import asyncio, aiofiles, aiocsv, csv
from typing import List
from cxone_repo_tools.client import CxOneRepoToolsClient
from cxone_repo_tools.index import ScmProjectIndex, ScmProjectIndexFactory


class BaseExport:
    """Base class for exports that write SCM data to a CSV file.

    :param client: The client used to make Checkmarx One API calls.
    :type client: CxOneRepoToolsClient

    :param threads: The maximum number of concurrent operations.  Defaults
                    to 2.
    :type threads: int, optional
    """

    def __init__(self, client: CxOneRepoToolsClient, *, threads: int = 2):
        """Initializes the export.  The SCM project index that matches the
        deployment the client is connected to is created on first use.

        :param client: The client used to make Checkmarx One API calls.
        :type client: CxOneRepoToolsClient

        :param threads: The maximum number of concurrent operations.
                        Defaults to 2.
        :type threads: int, optional
        """
        self.__client = client
        self.__threads = asyncio.Semaphore(threads)
        self.__index_threads = threads
        self.__index_instance: ScmProjectIndex | None = None
        self.__index_lock = asyncio.Lock()

    @property
    def _thread_semaphore(self) -> asyncio.Semaphore:
        return self.__threads

    @property
    def _client(self) -> CxOneRepoToolsClient:
        return self.__client

    @property
    async def __index(self) -> ScmProjectIndex:
        """The SCM project index for the deployment the client is connected to.
        It is created with `ScmProjectIndexFactory.create_index` the first time
        it is accessed and reused afterwards.

        :rtype: ScmProjectIndex

        :raises ResponseException: The index could not be created.
        """
        async with self.__index_lock:
            if self.__index_instance is None:
                self.__index_instance = await ScmProjectIndexFactory.create_index(
                    self.__client, threads=self.__index_threads
                )
        return self.__index_instance

    @property
    async def _index(self) -> ScmProjectIndex:
        """The index of SCMs and the projects connected to them, created on
        first use.  Subclasses use ``(await self._index)``.

        :rtype: ScmProjectIndex

        :raises ResponseException: The index could not be created.
        """
        return await self.__index

    async def export(self, export_csv_file: str) -> None:
        await self.__write_csv(export_csv_file)

    @property
    def _field_names(self) -> List[str]:
        raise NotImplementedError("_field_names")

    async def _write_rows(self, writer: aiocsv.AsyncDictWriter) -> None:
        raise NotImplementedError("_write_rows")

    async def __write_csv(self, csv_path: str):
        async with aiofiles.open(csv_path, "wt", encoding="UTF-8") as csv_out:
            writer = aiocsv.AsyncDictWriter(
                csv_out, quoting=csv.QUOTE_ALL, fieldnames=self._field_names
            )
            await writer.writeheader()
            await self._write_rows(writer)
