from asyncio import Lock, gather, create_task, Event
from typing import Dict, List, AsyncGenerator
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.low.code_repository_management import retrieve_scm_projects
from cxone_api.util import page_generator
from cxone_repo_tools.client import CxOneRepoToolsClient
from cxone_repo_tools.consts import MAX_RECORD_COUNT
from .scm_project_index import ScmProjectIndex


class UnifiedIndex(ScmProjectIndex):
    """An index of SCM-connected projects built from the projects the API
    returns as assigned to each SCM.  `ScmProjectIndexFactory` uses it for
    multi-tenant clients and for single-tenant deployments on CxOne 3.70.1 or
    later.

    The project IDs assigned to every SCM are indexed on first use.  The
    ProjectRepoConfig instances for an SCM's projects are loaded when that
    SCM is first requested and cached afterwards; the projects of SCMs that
    are never requested are not loaded.

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
        self.__indexing_entry_lock = Lock()
        self.__load_tasks = {}
        self.__load_events = {}

    async def __load_scm(self, scm_id: int, event: Event):
        await event.wait()

        async def __load_ProjectRepoConfig(pid: str):
            async with self._semaphore:
                return await ProjectRepoConfig.from_project_id(self._client, pid)

        loaded_list = await gather(
            *[__load_ProjectRepoConfig(pid) for pid in self.__projects_by_scm[scm_id]]
        )

        async with self.__indexing_entry_lock:
            self.__projects_by_scm[scm_id] = loaded_list

    async def __populate_index_for_scm(self, scm_id: int, list_gen: AsyncGenerator):
        async with self._semaphore:

            async for entry in list_gen:
                project_id = entry.get("cxProjectId")

                async with self.__indexing_entry_lock:
                    self.__projects_by_scm.setdefault(scm_id, []).append(project_id)

                    if scm_id not in self.__load_tasks.keys():
                        self.__load_events[scm_id] = Event()
                        self.__load_tasks[scm_id] = create_task(
                            self.__load_scm(scm_id, self.__load_events[scm_id])
                        )

    async def __init_index(self):
        """Builds the index of the project IDs assigned to each SCM.  The index
        is built once; later calls return immediately.

        :raises Exception: A cxone-async-api call made while building the
                           index failed.  The exception is propagated, the
                           partial index is discarded, and the next call
                           builds the index again.
        """
        async with self.__indexing_lock:
            if self.__projects_by_scm is not None:
                return

            self.__projects_by_scm = {}
            try:
                project_generators = [
                    (
                        scm_id,
                        page_generator(
                            retrieve_scm_projects,
                            "projects",
                            client=self._client,
                            limit=MAX_RECORD_COUNT,
                            scmid=scm_id,
                        ),
                    )
                    for scm_id in await self.get_scm_ids()
                ]

                await gather(
                    *[self.__populate_index_for_scm(*gen) for gen in project_generators]
                )
            except Exception:
                # Discard the partial index so the next call rebuilds it.
                for task in self.__load_tasks.values():
                    task.cancel()
                self.__load_tasks.clear()
                self.__load_events.clear()
                self.__projects_by_scm = None
                raise

    async def associated_projects(self, scm_id: int) -> List[ProjectRepoConfig]:
        """Retrieves the projects connected to an SCM.  The index of project
        IDs for every SCM is built on the first call.  The ProjectRepoConfig
        instances for `scm_id` are loaded on the first request for that SCM;
        later calls return the cached list.

        :param scm_id: The ID of the SCM.
        :type scm_id: int

        :return: The repository configurations of the projects connected to
                 the SCM, or an empty list if the SCM has no connected
                 projects or `scm_id` is not a known SCM.
        :rtype: List[ProjectRepoConfig]

        :raises Exception: A cxone-async-api call failed while building the
                           index or loading the SCM's projects.
        """
        await self.__init_index()

        # Lazy load the ProjectRepoConfig instances since a conversion may not
        # need to load all scm projects.
        async with self.__indexing_lock:
            if scm_id in self.__load_events.keys():
                self.__load_events[scm_id].set()
                await self.__load_tasks[scm_id]
                del self.__load_tasks[scm_id]
                del self.__load_events[scm_id]

        return self.__projects_by_scm.get(scm_id, [])
