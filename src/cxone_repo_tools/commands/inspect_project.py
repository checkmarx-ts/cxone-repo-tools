import aiofiles
from docopt import docopt
from typing import Dict, List
from cxone_api.high.sca.registry import (
    PackageRepositoryConfiguration,
    PackageManagerType,
)
from .command import Command
from ..convert import AbortedConversionException


class InspectProjectCommand(Command):
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

        configs = await PackageRepositoryConfiguration.retrieve_project_configurations(
            self.client, parsed_args["--project-id"]
        )

        await self.__output_configurations(configs, parsed_args["--out"])

    @staticmethod
    def __configuration_warnings(
        cfg: PackageRepositoryConfiguration,
        first_of_type: Dict[PackageManagerType, PackageRepositoryConfiguration],
    ) -> List[str]:
        warnings = []

        first = first_of_type.get(cfg.packageManager)
        if first is not None and first is not cfg:
            warnings.append(
                f"A {cfg.packageManager.value} configuration is already assigned to "
                f"the project: {first.name} ({first.configId}). Multiple configurations "
                "of the same package manager type produce undefined SCA scan results."
            )

        if len(cfg.associated_tags) > 1:
            warnings.append(
                f"The configuration is associated with {len(cfg.associated_tags)} tags. "
                "Multiple tags may make it difficult to manage updates to the configuration."
            )

        return warnings

    @staticmethod
    def __format_configuration(
        index: int,
        cfg: PackageRepositoryConfiguration,
        first_of_type: Dict[PackageManagerType, PackageRepositoryConfiguration],
    ) -> str:
        lines = [f"{index}. {cfg.name} ({cfg.configId}) [{cfg.packageManager.value}]"]

        lines.append("  Content:")
        lines.extend(f"    {line}" for line in (cfg.content or "").splitlines())

        lines.append("  Assigned Projects:")
        lines.extend(f"    {project_id}" for project_id in cfg.associated_projects)

        lines.append("  Tags:")
        lines.extend(f"    {tag.name} ({tag.tagid})" for tag in cfg.associated_tags)

        warnings = InspectProjectCommand.__configuration_warnings(cfg, first_of_type)
        if len(warnings) > 0:
            lines.append("  Warnings:")
            lines.extend(f"    {warning}" for warning in warnings)

        return "\n".join(lines)

    async def __output_configurations(
        self, configs: List[PackageRepositoryConfiguration], out_file: str | None
    ) -> None:
        first_of_type = {}
        for cfg in configs:
            first_of_type.setdefault(cfg.packageManager, cfg)

        text = "\n---\n".join(
            InspectProjectCommand.__format_configuration(index, cfg, first_of_type)
            for index, cfg in enumerate(configs, start=1)
        )
        if len(text) > 0:
            text += "\n"

        if out_file is not None and len(out_file) > 0:
            async with aiofiles.open(out_file, "wt", encoding="UTF-8") as out:
                await out.write(text)
        else:
            print(text, end="", flush=True)

        pass

    @staticmethod
    def print_help():
        print(InspectProjectCommand.__doc__)
