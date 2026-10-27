import asyncio, logging
from docopt import docopt
from tqdm.asyncio import tqdm
from typing import List
from cxone_api.high.sca.registry import PackageRepositoryConfiguration
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import (
    AbortedConversionException,
    InvalidRepositoryConfiguration,
)
from .util import (
    resolve_tag,
    config_file_exclusion,
    remove_project_sca_exclusions,
)

_log = logging.getLogger(__name__)


class DisassocTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools disassoc-tag (-h | --help | --version)
      cxone-repo-tools disassoc-tag (--tag-id TAGID | --tag-name TAGNAME) --project-id PROJECTID
                  [--confirm] [--skip-settings-update]

    Disassociate the SCA private package repository configurations of a tag from a
    single project.  The configurations and the tag are not changed.

    Without --confirm, the configurations that would be disassociated are only listed.
    With --confirm, the SCA file exclusions for the configuration files are removed from
    the project's settings and then the configurations are disassociated from the project.

    --tag-id TAGID                The ID of the tag whose configurations are disassociated.

    --tag-name TAGNAME            The name of the tag whose configurations are disassociated.
                                  Tag names are not unique; if no tag or more than one tag
                                  has the name, the command fails.

    --project-id PROJECTID        The ID of the project to disassociate the configurations
                                  from.

    --confirm                     Perform the disassociation.  Without this flag nothing
                                  is changed.

    --skip-settings-update        Do not remove the configuration file exclusions from
                                  the project's SCA file exclusions.
    """
    # fmt: on

    CMD_NAME = "disassoc-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            DisassocTagCommand.__doc__,
            [DisassocTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        tag = await resolve_tag(
            self.client, parsed_args["--tag-id"], parsed_args["--tag-name"]
        )

        if tag is None:
            raise InvalidRepositoryConfiguration.tag_not_found(
                parsed_args["--tag-name"]
            )

        project_id = parsed_args["--project-id"]

        configs = await PackageRepositoryConfiguration.retrieve_tag_configurations(
            self.client, tag
        )

        if not parsed_args["--confirm"]:
            print(
                f"Configurations of tag {tag.name} ({tag.tagid}) that would be "
                f"disassociated from project {project_id} (use --confirm to disassociate):"
            )
            for cfg in configs:
                print(f"  {cfg.name} ({cfg.configId}) [{cfg.packageManager.value}]")
            if len(configs) == 0:
                print("  NONE")
            return

        exclusions = {config_file_exclusion(cfg.packageManager) for cfg in configs}

        if parsed_args["--skip-settings-update"]:
            files = ", ".join(
                sorted({cfg.packageManager.config_file_name for cfg in configs})
            )
            _log.warning(
                f"Project settings were not updated. The SCA exclusions for {files} "
                f"remain in project {project_id} and will continue to exclude those "
                "files from SCA scans."
            )
        elif len(exclusions) > 0:
            await remove_project_sca_exclusions(
                self.client, {project_id: exclusions}, self.threads
            )

        semaphore = asyncio.Semaphore(self.threads)

        async def disassociate(cfg: PackageRepositoryConfiguration):
            async with semaphore:
                if await cfg.disassociate_from_project(project_id):
                    _log.info(
                        f"Disassociated configuration {cfg.name} ({cfg.configId}) "
                        f"[{cfg.packageManager.value}] from project {project_id}."
                    )
                else:
                    _log.error(
                        f"Failed to disassociate configuration {cfg.name} "
                        f"({cfg.configId}) from project {project_id}."
                    )

        await tqdm.gather(
            *[disassociate(cfg) for cfg in configs],
            desc="Disassociating configurations",
        )

    @staticmethod
    def print_help():
        print(DisassocTagCommand.__doc__)
