import asyncio, aiofiles, aiocsv, csv
from pathlib import Path
from tqdm.asyncio import tqdm
from typing import List, Dict
from .exceptions import ConversionException
from cxone_api import CxOneClient
from cxone_api.util import json_on_ok
from cxone_api.low.code_repository_management import disconnect_project_from_scm
from cxone_api.low.code_repository_project_conversion import (
    convert_a_project,
    retrieve_conversion_status,
)
from cxone_api.high.projects import ProjectRepoConfig
from .batch import ConversionBatch


class RecoverableConverter:
    """Resumes and completes any conversions left in-progress by a previous,
    interrupted run.  This is the subset of conversion behavior that does
    not require validated source/target SCMs, since recovery batches were
    already validated before they were persisted to disk.
    """

    def __init__(
        self,
        client: CxOneClient,
        report_path: str,
        threads: int = 2,
    ):
        self._client = client
        self._threads = asyncio.Semaphore(threads)

        # Trying to do more than one conversion at a time gets an error
        # from the server side.
        self._conversion_threads = asyncio.Semaphore(1)

        self._report = report_path

    async def _enable_repo_incremental(self, project_id: str) -> bool:

        repo_cfg = await ProjectRepoConfig.from_project_id(self._client, project_id)

        return await repo_cfg.update_repository_toggles(sastIncrementalScan=True)

    @staticmethod
    async def convert_project_and_wait(client: CxOneClient, payload: Dict) -> Dict:

        convert_response = json_on_ok(await convert_a_project(client, payload))
        process_id = convert_response.get("processId")

        print(f"\nProcess Id: {process_id} : {convert_response.get('message')}")

        while True:
            status = json_on_ok(await retrieve_conversion_status(client, process_id))

            if status.get("migrationStatus") != "IN_PROGRESS":
                print(
                    f"\nProcess {process_id} complete: {status.get('migrationStatus')} {status.get('summary')}"
                )
                return status
            else:
                print(f"\nWaiting for migration processId {process_id} to finish.")
                await asyncio.sleep(2.5)

    async def __process_single_batch(
        self, batch: ConversionBatch, writer: aiocsv.AsyncWriter
    ):
        async with self._conversion_threads:

            await batch.begin_recovery_mode()

            for id in batch.disconnect_projects:
                await disconnect_project_from_scm(self._client, id)

            status = await self.convert_project_and_wait(
                self._client, batch.as_api_payload()
            )

            for converted in status.get("successfulProjectsList", []):

                project_id = batch.get_project_id(converted)

                if batch.check_sast_incremental_enabled(project_id):
                    try:
                        assert await self._enable_repo_incremental(project_id)
                    except Exception:
                        raise ConversionException.failure_enable_sast_incrementals(
                            converted
                        )

                await writer.writerow(
                    [batch.get_project_id(converted), converted, "SUCCESS"]
                )
                await batch.project_complete(project_id)

            if batch.size > 0:
                for failed in batch.batch_projects:
                    await writer.writerow(
                        [batch.get_project_id(failed), failed, "FAILED"]
                    )

    async def _process_batches(
        self,
        batches: List[List[ConversionBatch]],
        batch_desc: str,
        *,
        max_batches: int = 0,
    ):
        header = True
        if Path(self._report).exists():
            header = False

        async with aiofiles.open(self._report, "at", encoding="UTF-8") as csv_out:
            writer = aiocsv.AsyncWriter(csv_out, quoting=csv.QUOTE_ALL)

            if header:
                await writer.writerow(["ProjectId", "ProjectName", "Status"])

            tasks = []
            batch_count = 0
            for scm_batches in batches:
                for org_batch in scm_batches:
                    if max_batches == 0 or batch_count < max_batches:
                        tasks.append(self.__process_single_batch(org_batch, writer))
                    batch_count += 1

            await tqdm.gather(*tasks, desc=batch_desc)

    async def _recover(self):
        # Recovery means validation has already happened for those
        # conversions being recovered.  Assuming the CxOne credentials
        # are valid, resume conversions for recovery batches.
        recovery_batches = ConversionBatch.load_recovery_batches()
        if recovery_batches is not None:
            batches = [[batch] for batch in recovery_batches]
            await self._process_batches(batches, "Recovering")

    async def convert(self):
        await self._recover()
