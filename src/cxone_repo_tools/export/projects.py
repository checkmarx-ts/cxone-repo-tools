import asyncio, aiocsv
from tqdm.asyncio import tqdm
from typing import List, Dict
from cxone_api.util import page_generator
from cxone_api.low.code_repository_management import retrieve_scm_projects
from cxone_api.low.projects import retrieve_list_of_projects
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.high.access_mgmt.user_mgmt import Groups
from .scms import ScmExport
from ..consts import MAX_RECORD_COUNT, MAX_NAMES_IN_QUERY


class ProjectAssignmentExport(ScmExport):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__project_data_generator_by_scm_index = {}
        self.__scm_project_name_index = {}
        self.__scm_project_name_index_lock = asyncio.Lock()
        self.__groups = Groups(self._client)

    @property
    def _field_names(self) -> List[str]:
        return super()._field_names + [
            "project_id",
            "project_name",
            "project_repo_id",
            "project_repo_url",
            "project_webhook_enabled",
            "project_pr_decoration_enabled",
            "project_sca_autopr_enabled",
            "project_primary_branch",
            "project_protected_branches",
            "project_scm_org",
            "project_scanners",
            "project_groups",
        ]

    async def __index_projects_assigned_to_scm(self, scm_id: int):
        async with self._thread_semaphore:
            async for project in page_generator(
                retrieve_scm_projects,
                "projects",
                client=self._client,
                scmid=scm_id,
                limit=MAX_RECORD_COUNT,
            ):
                async with self.__scm_project_name_index_lock:
                    if scm_id not in self.__scm_project_name_index.keys():
                        self.__scm_project_name_index[scm_id] = []

                    self.__scm_project_name_index[scm_id].append(project)

    async def __index_scm_projects(self):
        await asyncio.gather(
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

            if len(generators) > 0:
                self.__project_data_generator_by_scm_index[scm_id] = generators

    async def _prep_for_export(self):
        await super()._prep_for_export()
        await self.__index_scm_projects()

    async def _generate_row(self, scm_id: int, repo_cfg: ProjectRepoConfig) -> Dict:
        row = await super()._generate_row(await self._get_scm_data(scm_id))
        groups = ""
        if repo_cfg.groups is not None and len(repo_cfg.groups) > 0:
            group_list = []
            for gid in repo_cfg.groups:
                desc = await self.__groups.get_by_id(gid)
                group_list.append(str(desc.path))

            groups = "|".join(group_list)

        row.update(
            {
                "project_id": repo_cfg.id,
                "project_name": repo_cfg.name,
                "project_repo_id": await repo_cfg.repo_id,
                "project_repo_url": await repo_cfg.repo_url,
                "project_webhook_enabled": await repo_cfg.webhook_enabled,
                "project_pr_decoration_enabled": await repo_cfg.pr_decoration_enabled,
                "project_sca_autopr_enabled": await repo_cfg.sca_auto_pr_enabled,
                "project_primary_branch": await repo_cfg.primary_branch,
                "project_protected_branches": ",".join(
                    await repo_cfg.protected_branches
                ),
                "project_scm_org": await repo_cfg.scm_org,
                "project_scanners": await repo_cfg.get_enabled_scanners(
                    await repo_cfg.primary_branch
                ),
                "project_groups": groups,
            }
        )

        return row

    async def __write_rows_for_scm(self, scm_id: int, writer: aiocsv.AsyncDictWriter):
        async with self._thread_semaphore:
            for generator in self.__project_data_generator_by_scm_index[scm_id]:
                async for project_json in generator:
                    repo_cfg = await ProjectRepoConfig.from_project_json(
                        self._client, project_json
                    )
                    row = await self._generate_row(scm_id, repo_cfg)
                    await writer.writerow(row)

    async def _write_rows(self, writer: aiocsv.AsyncDictWriter) -> None:
        await tqdm.gather(
            *[
                self.__write_rows_for_scm(id, writer)
                for id in self.__project_data_generator_by_scm_index.keys()
            ],
            desc="Exporting data",
        )
