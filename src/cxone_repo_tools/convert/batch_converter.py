import logging
from tqdm.asyncio import tqdm
from typing import List, AsyncGenerator
from cxone_repo_tools.exceptions import ConversionException
from cxone_repo_tools.client import CxOneRepoToolsClient
from cxone_api.util import page_generator
from cxone_api.low.code_repository_management import retrieve_scm_projects
from cxone_api.low.projects import retrieve_list_of_projects
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.high.misc import FeatureFlagInspector
from cxone_repo_tools.consts import MAX_RECORD_COUNT, DISCO_API_FLAG, MAX_NAMES_IN_QUERY
from cxone_repo_tools.index import ScmProjectIndexFactory
from .batch import ConversionBatch
from .mapping import ConversionMapper
from .recoverable_converter import RecoverableConverter

_log = logging.getLogger(__name__)


class BatchConverter(RecoverableConverter):

    __BATCH_SIZE = 15

    def __init__(
        self,
        client: CxOneRepoToolsClient,
        source_ids: List[int],
        target_id: int,
        target_org: str,
        mapper: ConversionMapper,
        scm_token: str | None,
        report_path: str,
        threads: int = 2,
    ):
        """Initializes the converter and creates the SCM project index that
        matches the deployment the client is connected to.

        :param client: The client used to make Checkmarx One API calls.
        :type client: CxOneRepoToolsClient

        :param source_ids: The IDs of the SCMs whose projects are converted.
        :type source_ids: List[int]

        :param target_id: The ID of the SCM the projects are converted to.
        :type target_id: int

        :param target_org: The name of the SCM target organization.
        :type target_org: str

        :param mapper: Maps source repository URLs to target repository URLs.
        :type mapper: ConversionMapper

        :param scm_token: The SCM PAT for SCMs that require a token for
                          conversion, or None if no token was provided.
        :type scm_token: str | None

        :param report_path: The path of the conversion report file.
        :type report_path: str

        :param threads: The maximum number of concurrent operations.
                        Defaults to 2.
        :type threads: int, optional
        """
        super().__init__(client, report_path, scm_token, threads)

        self.__source_ids = source_ids
        self.__target_org = target_org
        self.__target_id = target_id
        self.__mapper = mapper
        self.__index = ScmProjectIndexFactory.create_index(client, threads=threads)
        self.__conversion_cfgs = None

        self.__scm_data = {}

    async def __validate_conversion(self):
        """Validates that a conversion can run: the disconnect API feature
        flag is enabled, the source and target SCMs exist in the index, each
        source SCM type is compatible with the target SCM type, and, unless
        overridden, all the SCMs share a repository base URL.  The data of
        the source and target SCMs is retained for the conversion.

        :param override_url_mismatch: True to skip the check that the source
                                      and target SCMs share a repository base
                                      URL.
        :type override_url_mismatch: bool

        :raises ConversionException: The conversion cannot run.
        """
        flag_insp = await FeatureFlagInspector.create(self._client)

        if flag_insp[DISCO_API_FLAG] is None or not flag_insp[DISCO_API_FLAG].Status:
            raise ConversionException.disconnect_api_ff_not_enabled()

        source_map = {}
        target_id_found = False

        base_urls = {}

        for scm_id in await self.__index.get_scm_ids():
            scm = await self.__index.get_scm_data(scm_id)
            base_urls[scm_id] = scm.repoBaseUrl

            add = False
            if scm_id in self.__source_ids:
                source_map[scm_id] = scm.type
                add = True
            elif scm_id == self.__target_id:
                target_id_found = True
                add = True

            if add:
                self.__scm_data[scm_id] = scm

        if not target_id_found:
            raise ConversionException.target_scm_not_found(self.__target_id)

        missing_sources = [
            src for src in self.__source_ids if src not in source_map.keys()
        ]
        if len(missing_sources) > 0:
            raise ConversionException.source_scms_not_found(missing_sources)

    async def _include_in_batch(self, repo_cfg: ProjectRepoConfig) -> bool:
        return True

    async def __convert_projects(
        self,
        *,
        max_batches: int = 0,
    ):
        batches = []

        convert_count = 0

        cur_batches_by_org = {}

        for repo_cfg in self.__conversion_cfgs:
            if await self._include_in_batch(repo_cfg):
                if cur_batches_by_org.get(self.__target_org) is None or (
                    cur_batches_by_org.get(self.__target_org) is not None
                    and cur_batches_by_org[self.__target_org].size
                    >= BatchConverter.__BATCH_SIZE
                ):
                    cur_batches_by_org[self.__target_org] = ConversionBatch(
                        self._scm_token,
                        self.__target_org,
                        self.__scm_data[int(self.__target_id)].type,
                        self.__scm_data[int(self.__target_id)].repoBaseUrl,
                    )
                    batches.append(cur_batches_by_org[self.__target_org])

                target_repo_url = self.__mapper.convert(
                    self.__scm_data[await repo_cfg.scm_id].repoBaseUrl,
                    await repo_cfg.repo_url,
                    await repo_cfg.scm_org,
                    self.__scm_data[int(self.__target_id)].repoBaseUrl,
                    self.__target_org,
                )
                await cur_batches_by_org[self.__target_org].add(
                    repo_cfg, target_repo_url
                )
                convert_count += 1

        _log.info(
            f"{convert_count} projects found for conversion in {len(batches)} batches."
        )
        await self._process_batches(batches, "Converting", max_batches=max_batches)

    async def convert(
        self,
        *,
        max_batches: int = 0,
        project_id: str = None,
        skip_recovery: bool = False,
    ):
        # Delegate recovery of any in-progress conversions to the base class.
        if not skip_recovery:
            await super().convert()

        _log.info("Gathering projects...this may take a while.")
        if project_id is not None:
            cfg = ProjectRepoConfig.from_project_id(self._client, project_id)
            if self.__target_id == await cfg.scm_id:
                raise ConversionException.project_already_assigned(
                    project_id, cfg.name, await cfg.scm_id
                )
            if await cfg.scm_id not in self.__source_ids:
                raise ConversionException.project_not_connected_to_scms(
                    project_id, cfg.name, self.__source_ids
                )

            self.__conversion_cfgs = [cfg]
        else:
            self.__conversion_cfgs = []
            for source_id in self.__source_ids:
                self.__conversion_cfgs += await self.__index.associated_projects(
                    int(source_id)
                )

        await self.__validate_conversion()
        await self.__convert_projects(max_batches=max_batches)
