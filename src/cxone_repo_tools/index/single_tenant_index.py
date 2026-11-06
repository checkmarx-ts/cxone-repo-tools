from asyncio import Lock, gather
from typing import List, AsyncGenerator
from cxone_repo_tools.client import CxOneRepoToolsClient
from .scm_project_index import ScmProjectIndex
from cxone_api.low.code_repository_management import retrieve_scm_projects
from cxone_api.low.projects import retrieve_list_of_projects
from cxone_api.util import page_generator
from cxone_api.high.projects import ProjectRepoConfig
from cxone_repo_tools.consts import MAX_RECORD_COUNT, MAX_NAMES_IN_QUERY


class SingleTenantIndex(ScmProjectIndex):
    """An index of SCM-connected projects for a single-tenant Checkmarx One
    deployment.

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
        self.__indexing_lock = Lock()
        self.__project_data_generator_by_scm_index = {}

        self.__scm_project_data_index = {}

        self.__scm_project_name_index = None
        self.__scm_project_name_index_lock = Lock()

    async def __init_index(self):
        async with self.__indexing_lock:
            if self.__scm_project_name_index is not None:
                return

            self.__scm_project_name_index = {}

            await gather(
                *[
                    self.__index_projects_assigned_to_scm(id)
                    for id in await self._get_scm_ids()
                ]
            )

            # Make a generator for the project data to avoid
            # trying to load a lot of data in memory.

            # The name parameters may be many, so there needs
            # to be multiple generators.
            for scm_id in self.__scm_project_name_index.keys():
                generators = []

                names = self.__scm_project_name_index[scm_id].copy()

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

                self.__project_data_generator_by_scm_index[scm_id] = (
                    generators if len(generators) > 0 else None
                )

    async def __index_projects_assigned_to_scm(self, scm_id: int):
        async with self._semaphore:
            async for project in page_generator(
                retrieve_scm_projects,
                "projects",
                client=self._client,
                scmid=scm_id,
                limit=MAX_RECORD_COUNT,
            ):
                async with self.__scm_project_name_index_lock:
                    self.__scm_project_name_index.setdefault(scm_id, []).append(project)

    async def __load_projects_list(
        self, generator: AsyncGenerator
    ) -> List[ProjectRepoConfig]:
        async with self._semaphore:

            cfg_list = []
            async for project_json in generator:
                cfg_list.append(
                    await ProjectRepoConfig.from_project_json(
                        self._client, project_json
                    )
                )

            return cfg_list

    async def associated_projects(self, scm_id: int) -> List[ProjectRepoConfig]:
        """Retrieves the projects connected to an SCM.  The SCM project index
        is built on the first call, and each SCM's project configurations are
        loaded on the first request for that SCM and cached afterwards.

        :param scm_id: The ID of the SCM.
        :type scm_id: int

        :return: The repository configurations of the projects connected to
                 the SCM, or an empty list if the SCM has no connected
                 projects or `scm_id` is not a known SCM.
        :rtype: List[ProjectRepoConfig]
        """
        await self.__init_index()

        if self.__project_data_generator_by_scm_index.get(scm_id) is not None:
            async with self.__indexing_lock:
                if scm_id not in self.__scm_project_data_index.keys():
                    self.__scm_project_data_index[scm_id] = []
                    list_of_project_cfg_lists = await gather(
                        *[
                            self.__load_projects_list(gen)
                            for gen in self.__project_data_generator_by_scm_index[
                                scm_id
                            ]
                        ]
                    )

                    for cfg_list in list_of_project_cfg_lists:
                        for cfg in cfg_list:
                            self.__scm_project_data_index[scm_id].append(cfg)

        return self.__scm_project_data_index.get(scm_id, [])
