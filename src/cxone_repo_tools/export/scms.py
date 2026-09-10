import asyncio, aiocsv
from typing import List, Dict
from cxone_api.util import json_on_ok
from cxone_api.low.code_repository_management import retrieve_list_of_scms
from .base import BaseExport


class ScmExport(BaseExport):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__scm_index = None
        self.__scm_index_lock = asyncio.Lock()

    async def _prep_for_export(self):
        await self.__index_scms()

    @property
    def _field_names(self) -> List[str]:
        return [
            "scm_id",
            "scm_type",
            "scm_base_url",
            "scm_instance_name",
            "scm_self_hosted",
        ]

    async def _get_scm_ids(self) -> List[int]:
        if self.__scm_index is None:
            await self.__index_scms()

        return list(self.__scm_index.keys())

    async def _get_scm_data(self, scm_id: int) -> Dict | None:
        if self.__scm_index is None:
            await self.__index_scms()

        return self.__scm_index.get(scm_id)

    async def __index_scms(self):
        async with self.__scm_index_lock:
            if self.__scm_index is not None:
                return
            else:
                self.__scm_index = {}

            for scm in json_on_ok(await retrieve_list_of_scms(self._client)):
                self.__scm_index[scm.get("id")] = scm

    async def _generate_row(self, scm_dict: Dict) -> Dict:
        return {
            "scm_id": scm_dict.get("id"),
            "scm_type": scm_dict.get("type"),
            "scm_base_url": scm_dict.get("repoBaseUrl"),
            "scm_instance_name": scm_dict.get("instanceName"),
            "scm_self_hosted": scm_dict.get("onPrem", False),
        }

    async def _write_rows(self, writer: aiocsv.AsyncDictWriter) -> None:
        for scm in self.__scm_index.values():
            await writer.writerow(await self._generate_row(scm))
