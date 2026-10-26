import asyncio, logging
from docopt import docopt
from tqdm.asyncio import tqdm
from typing import List
from cxone_api.high.sca.registry import PackageRepositoryConfiguration
from cxone_repo_tools.commands.base import Command
from .util import resolve_tag
from cxone_repo_tools.convert import (
    AbortedConversionException,
    InvalidRepositoryConfiguration,
)

_log = logging.getLogger(__name__)


class UndeployTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools undeploy-tag (-h | --help | --version)
      cxone-repo-tools undeploy-tag (--tag-id TAGID | --tag-name TAGNAME) [--confirm]

    Remove a configuration tag and every SCA private package repository configuration
    associated with it.  Deleting a configuration also removes it from every project
    it is assigned to.

    Without --confirm, the tag and the configurations that would be deleted are only
    listed.  With --confirm, the associated configurations are deleted first and then
    the tag is deleted.

    --tag-id TAGID                The ID of the tag to undeploy.

    --tag-name TAGNAME            The name of the tag to undeploy.  Tag names are not
                                  unique; if more than one tag has the name, the
                                  command fails and lists the matching tag ids.

    --confirm                     Delete the tag and its associated configurations.
                                  Without this flag nothing is deleted.
    """
    # fmt: on

    CMD_NAME = "undeploy-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            UndeployTagCommand.__doc__,
            [UndeployTagCommand.CMD_NAME] + cmdline_args,
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

        configs = await PackageRepositoryConfiguration.retrieve_tag_configurations(
            self.client, tag
        )

        if not parsed_args["--confirm"]:
            print(f"Tag that would be deleted (use --confirm to delete):")
            print(f"  {tag.name} ({tag.tagid})")
            print("Associated configurations that would be deleted:")
            for cfg in configs:
                print(f"  {cfg.name} ({cfg.configId}) [{cfg.packageManager.value}]")
            if len(configs) == 0:
                print("  NONE")
            return

        semaphore = asyncio.Semaphore(self.threads)
        failures = 0

        async def delete(cfg: PackageRepositoryConfiguration):
            nonlocal failures
            async with semaphore:
                if await cfg.delete():
                    _log.info(f"Deleted configuration {cfg.name} ({cfg.configId}).")
                else:
                    failures += 1
                    _log.error(
                        f"Failed to delete configuration {cfg.name} ({cfg.configId})."
                    )

        await tqdm.gather(
            *[delete(cfg) for cfg in configs], desc="Deleting configurations"
        )

        if failures > 0:
            _log.error(
                f"Tag {tag.name} ({tag.tagid}) was not deleted because {failures} "
                "associated configurations could not be deleted."
            )
            return

        if await tag.delete():
            _log.info(f"Deleted tag {tag.name} ({tag.tagid}).")
        else:
            _log.error(f"Failed to delete tag {tag.name} ({tag.tagid}).")

    @staticmethod
    def print_help():
        print(UndeployTagCommand.__doc__)
