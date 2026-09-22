from tqdm.asyncio import tqdm
from typing import List, AsyncGenerator
from .exceptions import ConversionException
from cxone_api import CxOneClient
from cxone_api.util import json_on_ok, page_generator
from cxone_api.low.code_repository_management import (
    retrieve_list_of_scms,
    retrieve_scm_projects,
)
from cxone_api.low.projects import retrieve_list_of_projects
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.high.misc import FeatureFlagInspector
from ..consts import MAX_RECORD_COUNT, DISCO_API_FLAG, MAX_NAMES_IN_QUERY
from .batch import ConversionBatch
from .recoverable_converter import RecoverableConverter

class BatchConverter(RecoverableConverter):

    __BATCH_SIZE = 15

    def __init__(
        self,
        client: CxOneClient,
        source_ids: List[int],
        target_id: int,
        report_path: str,
        threads: int = 2,
    ):
        super().__init__(client, report_path, threads)

        self.__source_ids = source_ids
        self.__target_id = target_id

        self.__scm_data = {}

    async def __validate_conversion(self, override_url_mismatch: bool):
        flag_insp = await FeatureFlagInspector.create(self._client)

        if flag_insp[DISCO_API_FLAG] is None or not flag_insp[DISCO_API_FLAG].Status:
            raise ConversionException.disconnect_api_ff_not_enabled()

        source_map = {}
        target_id_found = False
        target_type = None

        base_urls = {}

        for scm in json_on_ok(await retrieve_list_of_scms(self._client)):
            base_urls[int(scm.get("id"))] = scm.get("repoBaseUrl")

            add = False
            id = str(scm.get("id"))
            if id in self.__source_ids:
                source_map[id] = scm.get("type")
                add = True
            elif id == self.__target_id:
                target_id_found = True
                target_type = scm.get("type")
                add = True

            if add:
                self.__scm_data[scm.get("id")] = scm

        if not target_id_found:
            raise ConversionException.target_scm_not_found(self.__target_id)

        missing_sources = [
            src for src in self.__source_ids if src not in source_map.keys()
        ]
        if len(missing_sources) > 0:
            raise ConversionException.source_scms_not_found(missing_sources)

        for source_id in source_map.keys():
            if source_map[source_id] not in BatchConverter.__COMPATIBLE_MAP.get(
                target_type, []
            ):
                raise ConversionException.incompatible(
                    source_id, source_map[source_id], self.__target_id, target_type
                )

        if not override_url_mismatch:
            repo_base_urls = set(
                [scm_data.get("repoBaseUrl") for scm_data in self.__scm_data.values()]
            )
            if len(repo_base_urls) > 1:
                raise ConversionException.scm_base_urls_different(repo_base_urls)

    async def __get_single_project_generators(self, single_project: str):
        return [
            page_generator(
                retrieve_list_of_projects,
                "projects",
                client=self._client,
                ids=[single_project],
            )
        ]

    async def __get_scm_project_name_generators(self, scm_id: int):
        names = []
        async for name in page_generator(
            retrieve_scm_projects,
            "projects",
            client=self._client,
            scmid=scm_id,
            limit=MAX_RECORD_COUNT,
        ):
            names.append(name)

        generators = []

        while len(names) > 0:
            generators.append(
                page_generator(
                    retrieve_list_of_projects,
                    "projects",
                    client=self._client,
                    limit=MAX_RECORD_COUNT,
                    names=names[:MAX_NAMES_IN_QUERY],
                )
            )

            del names[:MAX_NAMES_IN_QUERY]

        return generators

    async def __get_scm_project_generators(
        self, scm_id: int, *, single_project: str = None
    ) -> List[AsyncGenerator]:
        async with self._threads:
            if single_project is not None:
                return await self.__get_single_project_generators(single_project)
            else:
                return await self.__get_scm_project_name_generators(scm_id)

    async def _include_in_batch(self, repo_cfg : ProjectRepoConfig) -> bool:
        return True

    async def __get_conversion_batches(
        self,
        project_data_gen: AsyncGenerator,
    ) -> List[ConversionBatch]:
        batches = []

        cur_batches_by_org = {}

        async with self._threads:
            async for project_data in project_data_gen:
                repo_cfg = await ProjectRepoConfig.from_project_json(
                    self._client, project_data
                )

                if await self._include_in_batch(repo_cfg):
                  repo_org = await repo_cfg.scm_org

                  if cur_batches_by_org.get(repo_org) is None or (
                      cur_batches_by_org.get(repo_org) is not None
                      and cur_batches_by_org[repo_org].size >= BatchConverter.__BATCH_SIZE
                  ):
                      cur_batches_by_org[repo_org] = ConversionBatch(
                          repo_org,
                          self.__scm_data[int(self.__target_id)].get("type"),
                          self.__scm_data[int(self.__target_id)].get("repoBaseUrl"),
                      )
                      batches.append(cur_batches_by_org[repo_org])

                  await cur_batches_by_org[repo_org].add(repo_cfg)

        return batches

    async def __convert_projects(
        self,
        *,
        max_batches: int = 0,
        project_id: str = None,
    ):
        data_gen_lists = await tqdm.gather(
            *[
                self.__get_scm_project_generators(id, single_project=project_id)
                for id in self.__scm_data.keys()
                if id != int(self.__target_id)
            ],
            desc="Gathering projects",
        )

        # unpack list of lists
        project_data_generators = [
            generator for gen_list in data_gen_lists for generator in gen_list
        ]

        batches = await tqdm.gather(
            *[self.__get_conversion_batches(gen) for gen in project_data_generators],
            desc="Batching conversions",
        )

        await self._process_batches(batches, "Converting", max_batches=max_batches)

    async def convert(
        self,
        *,
        max_batches: int = 0,
        project_id: str = None,
        override_url_mismatch: bool = False,
        skip_recovery: bool = False,
    ):
        # Delegate recovery of any in-progress conversions to the base class.
        if not skip_recovery:
            await super().convert()

        await self.__validate_conversion(override_url_mismatch)
        await self.__convert_projects(max_batches=max_batches, project_id=project_id)

    __COMPATIBLE_MAP = {
        "github": ["github", "githubApp"],
        "githubApp": ["github", "githubApp"],
        "azure": ["azure"],
        "gitlab": ["gitlab"],
        "bitbucket": ["bitbucket"],
    }
