import asyncio, aiocsv
from tqdm.asyncio import tqdm
from typing import List, Dict
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.high.access_mgmt.user_mgmt import Groups
from .scms import ScmExport


class ProjectAssignmentExport(ScmExport):
    """Exports the projects connected to each SCM to a CSV file, using the
    export's SCM project index to find the projects for each SCM."""

    def __init__(self, *args, **kwargs):
        """Initializes the export.  Arguments are passed to `ScmExport`.

        :param args: Positional arguments passed to `ScmExport`.
        :param kwargs: Keyword arguments passed to `ScmExport`.
        """
        super().__init__(*args, **kwargs)
        self.__groups = Groups(self._client)
        # aiocsv writers are not safe for concurrent writerow calls.
        self.__write_lock = asyncio.Lock()

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

    async def _generate_row(self, scm_id: int, repo_cfg: ProjectRepoConfig) -> Dict:
        """Generates the CSV row for a project connected to an SCM.

        :param scm_id: The ID of the SCM the project is connected to.
        :type scm_id: int

        :param repo_cfg: The project's repository configuration.
        :type repo_cfg: ProjectRepoConfig

        :return: The CSV row, keyed by field name.
        :rtype: Dict
        """
        row = await super()._generate_row(
            await (await self._index).get_scm_data(scm_id)
        )
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
        """Writes one row for each project connected to an SCM.

        :param scm_id: The ID of the SCM.
        :type scm_id: int

        :param writer: The CSV writer.
        :type writer: aiocsv.AsyncDictWriter
        """
        repo_cfgs = await (await self._index).associated_projects(scm_id)
        async with self._thread_semaphore:
            for repo_cfg in repo_cfgs:
                row = await self._generate_row(scm_id, repo_cfg)
                async with self.__write_lock:
                    await writer.writerow(row)

    async def _write_rows(self, writer: aiocsv.AsyncDictWriter) -> None:
        """Writes the rows for the projects connected to every SCM in the
        index.

        :param writer: The CSV writer.
        :type writer: aiocsv.AsyncDictWriter
        """
        await tqdm.gather(
            *[
                self.__write_rows_for_scm(scm_id, writer)
                for scm_id in await (await self._index).get_scm_ids()
            ],
            desc="Exporting data",
        )
