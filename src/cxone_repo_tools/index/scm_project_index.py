from cxone_repo_tools.client import CxOneRepoToolsClient
from typing import List
from dotwiz import DotWiz
from asyncio import Semaphore, Lock
from cxone_api.util import json_on_ok
from cxone_api.low.code_repository_management import retrieve_list_of_scms
from cxone_api.high.projects import ProjectRepoConfig


class ScmProjectIndex:
    """Base class for an index of SCM-connected projects.  Subclasses must
    implement `associated_projects`.

    Use `ScmProjectIndexFactory.create_index` to obtain an instance.

    :param client: The client used to make Checkmarx One API calls.
    :type client: CxOneRepoToolsClient

    :param threads: The maximum number of concurrent API calls the index
                    makes.  Defaults to 2.
    :type threads: int, optional
    """

    def __init__(self, client: CxOneRepoToolsClient, *, threads: int = 2):
        self.__client = client
        self.__threads = Semaphore(threads)
        self.__scm_index = None
        self.__scm_index_lock = Lock()

    @property
    def _client(self) -> CxOneRepoToolsClient:
        """The client used to make Checkmarx One API calls.

        :rtype: CxOneRepoToolsClient
        """
        return self.__client

    @property
    def _semaphore(self) -> Semaphore:
        """The semaphore that bounds the number of concurrent API calls.

        :rtype: Semaphore
        """
        return self.__threads

    async def get_scm_data(self, scm_id: int) -> DotWiz | None:
        """Retrieves the data of an SCM configured in the tenant.  The SCM
        list is retrieved on the first call and cached afterwards.

        :param scm_id: The ID of the SCM.
        :type scm_id: int

        :return: The SCM's data, with its fields available as attributes, or
                 None if `scm_id` is not a known SCM.
        :rtype: DotWiz | None
        """
        await self.__index_scms()
        scm = self.__scm_index.get(scm_id)
        return DotWiz(scm) if scm is not None else None

    async def get_scm_ids(self) -> List[int]:
        """Retrieves the IDs of every SCM configured in the tenant.  The SCM
        list is retrieved on the first call and cached afterwards.

        :return: The SCM IDs.
        :rtype: List[int]
        """
        await self.__index_scms()
        return list(self.__scm_index.keys())

    async def __index_scms(self):
        async with self.__scm_index_lock:
            if self.__scm_index is not None:
                return
            else:
                self.__scm_index = {}

            for scm in json_on_ok(await retrieve_list_of_scms(self._client)):
                self.__scm_index[scm.get("id")] = scm

    async def associated_projects(self, scm_id: int) -> List[ProjectRepoConfig]:
        """Retrieves the projects connected to an SCM.

        :param scm_id: The ID of the SCM.
        :type scm_id: int

        :return: The repository configurations of the projects connected to
                 the SCM.
        :rtype: List[ProjectRepoConfig]

        :raises NotImplementedError: The subclass does not implement this
                                     method.
        """
        raise NotImplementedError(ScmProjectIndex.associated_projects.__name__)
