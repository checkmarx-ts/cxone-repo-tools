import asyncio, aiofiles, aiocsv, csv, logging
from pathlib import Path
from tqdm.asyncio import tqdm
from typing import List, Dict
from cxone_repo_tools.exceptions import ConversionException
from cxone_repo_tools.client import CxOneRepoToolsClient
from cxone_api.util import json_on_ok
from cxone_api.low.projects import update_specific_project_fields
from cxone_api.low.code_repository_management import disconnect_project_from_scm
from cxone_api.low.code_repository_project_conversion import (
    convert_a_project,
    retrieve_conversion_status,
)

_log = logging.getLogger(__name__)
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
        client: CxOneRepoToolsClient,
        report_path: str,
        scm_token: str | None,
        threads: int = 2,
    ):
        """Initializes the converter.

        :param client: The client used to make Checkmarx One API calls.
        :type client: CxOneRepoToolsClient

        :param report_path: The path of the conversion report file.
        :type report_path: str

        :param scm_token: The SCM PAT for SCMs that require a token for
                          conversion, or None if no token was provided.
        :type scm_token: str | None

        :param threads: The maximum number of concurrent operations.
                        Defaults to 2.
        :type threads: int, optional
        """
        self._client = client
        self._threads = asyncio.Semaphore(threads)

        # Trying to do more than one conversion at a time gets an error
        # from the server side.
        self._conversion_threads = asyncio.Semaphore(1)

        self._report = report_path
        self.__scm_token = scm_token

    @property
    def _scm_token(self) -> str | None:
        """The SCM PAT for SCMs that require a token for conversion, or None
        if no token was provided.

        :rtype: str | None
        """
        return self.__scm_token

    async def _enable_repo_incremental(self, project_id: str) -> bool:

        repo_cfg = await ProjectRepoConfig.from_project_id(self._client, project_id)

        return await repo_cfg.update_repository_toggles(sastIncrementalScan=True)

    @staticmethod
    async def convert_project_and_wait(
        client: CxOneRepoToolsClient, payload: Dict
    ) -> Dict:

        convert_response = json_on_ok(await convert_a_project(client, payload))
        process_id = convert_response.get("processId")

        _log.info(f"Process Id: {process_id} : {convert_response.get('message')}")

        while True:
            status = json_on_ok(await retrieve_conversion_status(client, process_id))

            if status.get("migrationStatus") != "IN_PROGRESS":
                _log.info(
                    f"Process {process_id} complete: {status.get('migrationStatus')} {status.get('summary')}"
                )
                return status
            else:
                _log.debug(f"Waiting for migration processId {process_id} to finish.")
                await asyncio.sleep(2.5)

    async def __process_single_batch(
        self, batch: ConversionBatch, writer: aiocsv.AsyncWriter
    ):
        async with self._conversion_threads:

            await batch.begin_recovery_mode()

            for id in batch.disconnect_projects:
                if not (await disconnect_project_from_scm(self._client, id)).ok:
                    raise ConversionException.disconnect_failed(id)

                # MUST rename the project when it is disconnected.  The API
                # will reject a name change for an SCM connected project.
                target_name = batch.get_new_project_name(id)
                if target_name is not None:
                    if not (
                        await update_specific_project_fields(
                            self._client, id, name=target_name
                        )
                    ).ok:
                        # Previous failure may have named the project correctly but the API
                        # will return an error trying to name it to an "existing project name"
                        cfg = await ProjectRepoConfig.from_project_id(self._client, id)
                        if cfg.name != target_name:
                            raise ConversionException.rename_failed(id, target_name)

            status = await RecoverableConverter.convert_project_and_wait(
                self._client, batch.as_api_payload()
            )

            conversion_failures = {}
            # Response payload successfully converted project names will
            # not likely match the actual project name, so all projects
            # need to be checked if they are connected.
            if status.get("migrationStatus") in ["OK", "PARTIAL"]:
                for id in batch.disconnect_projects:
                    repo_cfg = await ProjectRepoConfig.from_project_id(self._client, id)
                    if await repo_cfg.is_scm_imported:
                        if batch.check_sast_incremental_enabled(id):
                            try:
                                assert await self._enable_repo_incremental(id)
                            except (Exception, BaseException) as ex:
                                _log.warning(
                                    f"Enabling SAST incremental scans for {repo_cfg.name} failed: {ex}",
                                    exc_info=True,
                                )
                                raise ConversionException.failure_enable_sast_incrementals(
                                    repo_cfg.name
                                )

                        await writer.writerow([id, repo_cfg.name, "SUCCESS"])
                        await batch.project_complete(id)
                    else:
                        conversion_failures[id] = repo_cfg

            if batch.size > 0:
                for id in batch.disconnect_projects:
                    failed_cfg = conversion_failures.get(id)

                    if failed_cfg is None:
                        failed_cfg = await ProjectRepoConfig.from_project_id(
                            self._client, id
                        )

                    await writer.writerow([failed_cfg.id, failed_cfg.name, "FAILED"])

    async def _process_batches(
        self,
        batches: List[ConversionBatch],
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
            for org_batch in batches:
                if max_batches == 0 or batch_count < max_batches:
                    tasks.append(self.__process_single_batch(org_batch, writer))
                batch_count += 1

            await tqdm.gather(*tasks, desc=batch_desc)

    async def _recover(self):
        # Recovery means validation has already happened for those
        # conversions being recovered.  Assuming the CxOne credentials
        # are valid, resume conversions for recovery batches.
        recovery_batches = ConversionBatch.load_recovery_batches(self._scm_token)
        if recovery_batches is not None:
            await self._process_batches(recovery_batches, "Recovering")

    async def convert(self):
        await self._recover()
