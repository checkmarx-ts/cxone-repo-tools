import asyncio, aiofiles, aiocsv, csv
from typing import List
from cxone_api import CxOneClient


class BaseExport:
    def __init__(self, client: CxOneClient, *, threads: int = 2):
        self.__client = client
        self.__threads = asyncio.Semaphore(threads)

    @property
    def _thread_semaphore(self) -> asyncio.Semaphore:
        return self.__threads

    @property
    def _client(self) -> CxOneClient:
        return self.__client

    async def _prep_for_export(self):
        raise NotImplementedError("_prep_for_export")

    async def export(self, export_csv_file: str) -> None:
        await self._prep_for_export()
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
