from asyncio import Lock, gather
from typing import Dict, List, Tuple
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.low.projects import retrieve_list_of_projects
from cxone_api.util import page_generator
from cxone_repo_tools.client import CxOneRepoToolsClient
from cxone_repo_tools.consts import MAX_RECORD_COUNT
from .scm_project_index import ScmProjectIndex


class UnifiedIndex(ScmProjectIndex):
    """An index of SCM-connected projects for multi-tenant Checkmarx One
    regions and for single-tenant deployments on CxOne 3.70.1 or later, which
    have the unified project APIs.

    Every project in the tenant is retrieved and grouped by the SCM ID of its
    repository configuration.  Projects without an SCM ID are not indexed.

    :param client: The client used to make Checkmarx One API calls.
    :type client: CxOneRepoToolsClient

    :param threads: The maximum number of concurrent API calls the index
                    makes.  Defaults to 2.
    :type threads: int, optional
    """

    def __init__(self, client: CxOneRepoToolsClient, *, threads: int = 2):
        """Initializes the index.

        :param client: The client used to make Checkmarx One API calls.
        :type client: CxOneRepoToolsClient

        :param threads: The maximum number of concurrent API calls the index
                        makes.  Defaults to 2.
        :type threads: int, optional
        """
        super().__init__(client, threads=threads)
        self.__projects_by_scm: Dict[int, List[ProjectRepoConfig]] | None = None
        self.__indexing_lock = Lock()

    async def __resolve_scm_id(
        self, cfg: ProjectRepoConfig
    ) -> Tuple[int | None, ProjectRepoConfig]:
        """Resolves the SCM ID of a project's repository configuration.

        :param cfg: The project's repository configuration.
        :type cfg: ProjectRepoConfig

        :return: The SCM ID, or None if the project is not connected to an SCM
                 or its SCM credentials have expired, paired with `cfg`.
        :rtype: Tuple[int | None, ProjectRepoConfig]
        """
        async with self._semaphore:
            return await cfg.scm_id, cfg

    async def __init_index(self):
        """Builds the SCM-to-projects index by iterating every project in the
        tenant, discarding projects with an SCM ID of None.  The index is built
        once; later calls return immediately.  If building fails, no index is
        stored and the next call tries again.
        """
        async with self.__indexing_lock:
            if self.__projects_by_scm is not None:
                return

            cfgs = [
                await ProjectRepoConfig.from_project_json(self._client, project_json)
                async for project_json in page_generator(
                    retrieve_list_of_projects,
                    "projects",
                    client=self._client,
                    limit=MAX_RECORD_COUNT,
                )
            ]

            index = {}
            for scm_id, cfg in await gather(
                *[self.__resolve_scm_id(cfg) for cfg in cfgs]
            ):
                if scm_id is not None:
                    index.setdefault(scm_id, []).append(cfg)

            self.__projects_by_scm = index

    async def associated_projects(self, scm_id: int) -> List[ProjectRepoConfig]:
        """Retrieves the projects connected to an SCM.  Every project in the
        tenant is retrieved and indexed on the first call; later calls are
        answered from the index.

        :param scm_id: The ID of the SCM.
        :type scm_id: int

        :return: The repository configurations of the projects connected to
                 the SCM, or an empty list if the SCM has no connected
                 projects or `scm_id` is not a known SCM.
        :rtype: List[ProjectRepoConfig]
        """
        await self.__init_index()
        return self.__projects_by_scm.get(scm_id, [])
