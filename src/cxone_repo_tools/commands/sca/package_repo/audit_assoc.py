import aiofiles, aiocsv, csv
from docopt import docopt
from tqdm.asyncio import tqdm
from typing import List
from cxone_api.util import page_generator
from cxone_api.low.sca.registry.configurations import retrieve_configurations
from cxone_api.low.projects import retrieve_list_of_projects
from cxone_api.high.sca.registry import PackageRepositoryConfiguration
from cxone_api.high.scan_configuration import ProjectScanConfiguration
from cxone_repo_tools.commands.base import Command
from .util import PACKAGE_MANAGERS
from cxone_repo_tools.convert import AbortedConversionException
from cxone_repo_tools.consts import MAX_RECORD_COUNT


class AuditAssocCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools audit-assoc (-h | --help | --version)
      cxone-repo-tools audit-assoc [--out EXPORT_FILE]

    Produce a summary CSV showing SCA private package repository configurations associated
    with each project.

    --out EXPORT_FILE             The name of the CSV export file. [default: ./assoc_audit.csv]
    """
    # fmt: on

    CMD_NAME = "audit-assoc"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            AuditAssocCommand.__doc__,
            [AuditAssocCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        await self.__populate_assigned_project_index()

        package_managers = [pm.value for pm in PACKAGE_MANAGERS]

        async with aiofiles.open(
            parsed_args["--out"], "wt", encoding="UTF-8"
        ) as csv_out:
            writer = aiocsv.AsyncDictWriter(
                csv_out,
                quoting=csv.QUOTE_ALL,
                fieldnames=["project_name", "project_id"]
                + package_managers
                + ["sca_file_filters"],
            )
            await writer.writeheader()

            async for project in tqdm(
                page_generator(
                    retrieve_list_of_projects,
                    "projects",
                    client=self.client,
                    limit=MAX_RECORD_COUNT,
                ),
                desc="Inspecting projects",
            ):
                project_id = project.get("id")

                counts = {pm: 0 for pm in package_managers}
                for cfg in self.__assigned_project_index.get(project_id, []):
                    counts[cfg.packageManager.value] += 1

                sca_filters = (
                    await ProjectScanConfiguration(
                        self.client, project_id
                    ).SCA.Exclusions.getValue()
                    or ""
                )

                await writer.writerow(
                    {"project_name": project.get("name"), "project_id": project_id}
                    | counts
                    | {"sca_file_filters": sca_filters}
                )

    async def __populate_assigned_project_index(self):
        self.__assigned_project_index = {}

        async for cfg_json in page_generator(
            retrieve_configurations,
            offset_param="PageNumber",
            offset_init_value=1,
            offset_is_by_count=False,
            client=self.client,
            PageSize=50,
        ):
            cfg = PackageRepositoryConfiguration.from_config_json(self.client, cfg_json)
            for pid in cfg.associated_projects:
                if pid not in self.__assigned_project_index.keys():
                    self.__assigned_project_index[pid] = [cfg]
                else:
                    self.__assigned_project_index[pid].append(cfg)

    @staticmethod
    def print_help():
        print(AuditAssocCommand.__doc__)
