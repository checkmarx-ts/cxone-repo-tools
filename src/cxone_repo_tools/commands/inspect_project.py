from docopt import docopt
from typing import List
from cxone_api.util import json_on_ok
from cxone_api.low.projects import retrieve_project_info
from cxone_api.high.sca.registry import PackageRepositoryConfiguration
from .inspect_base import AbstractInspectCommand
from ..convert import AbortedConversionException


class InspectProjectCommand(AbstractInspectCommand):
    # fmt: off
    """Usage:
      cxone-repo-tools inspect-project (-h | --help | --version)
      cxone-repo-tools inspect-project --project-id PROJECTID [--out EXPORT_FILE]

    Show the SCA private package repository configurations assigned to a project.

    --project-id PROJECTID        The ID of the project to inspect.

    --out EXPORT_FILE             The name of the output file.  Output is written to
                                  stdout if not provided.
    """
    # fmt: on

    CMD_NAME = "inspect-project"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            InspectProjectCommand.__doc__,
            [InspectProjectCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        project_id = parsed_args["--project-id"]

        project = json_on_ok(await retrieve_project_info(self.client, project_id))

        configs = await PackageRepositoryConfiguration.retrieve_project_configurations(
            self.client, project_id
        )

        await self._write_output(
            self._format_configurations(
                f"Configurations assigned to project: {project.get('name')} ({project_id})",
                configs,
            ),
            parsed_args["--out"],
        )

    @staticmethod
    def print_help():
        print(InspectProjectCommand.__doc__)
