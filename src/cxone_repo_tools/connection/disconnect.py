from __future__ import annotations
import asyncio
from tqdm.asyncio import tqdm
from typing import AsyncGenerator, List
from cxone_api import CxOneClient
from cxone_api.util import page_generator
from cxone_api.low.code_repository_management import (
    retrieve_scm_projects,
    disconnect_project_from_scm,
)
from cxone_api.low.projects import retrieve_list_of_projects
from ..consts import MAX_RECORD_COUNT, MAX_NAMES_IN_QUERY


class Disconnector:

    def __init__(self, client: CxOneClient, threads: int = 2):
        self.__client = client
        self.__task = None
        self.__threads = asyncio.Semaphore(threads)

    async def __compile_project_ids(self, generator: AsyncGenerator) -> List[str]:
        async with self.__threads:
            pids = []

            async for p_data in generator:
                pids.append(p_data.get("id"))

            return pids

    async def __disconnect_scm(self, scm_id: int):
        names = []
        async for name in page_generator(
            retrieve_scm_projects,
            "projects",
            client=self.__client,
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
                    client=self.__client,
                    limit=MAX_RECORD_COUNT,
                    names=names[:MAX_NAMES_IN_QUERY],
                )
            )

            del names[:MAX_NAMES_IN_QUERY]

        task_out = await tqdm.gather(
            *[self.__compile_project_ids(gen) for gen in generators],
            desc="Gathering data",
        )

        pids = [id for task_list in task_out for id in task_list]

        await tqdm.gather(
            *[self.__disconnect_project(pid) for pid in pids], desc="Disconnecting"
        )

    async def __disconnect_project(self, project_id: str):
        async with self.__threads:
            await disconnect_project_from_scm(self.__client, project_id)

    @staticmethod
    def from_scm_id(client: CxOneClient, scm_id: int, **kwargs) -> Disconnector:
        inst = Disconnector(client, **kwargs)
        inst.__task = inst.__disconnect_scm(scm_id)
        return inst

    @staticmethod
    def from_project_id(client: CxOneClient, project_id: str, **kwargs) -> Disconnector:
        inst = Disconnector(client, **kwargs)
        inst.__task = inst.__disconnect_project(project_id)
        return inst

    async def disconnect(self):
        await self.__task
