import asyncio, logging
from docopt import docopt
from tqdm.asyncio import tqdm
from typing import List
from cxone_api.util import page_generator
from cxone_api.low.sca.registry.configurations import retrieve_configurations
from cxone_api.low.sca.registry.tags import retrieve_list_of_configurations_by_tag
from cxone_api.high.sca.registry import (
    PackageRepositoryConfiguration,
    PackageRepositoryConfigurationTag,
)
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import AbortedConversionException

_log = logging.getLogger(__name__)


class PruneRepoConfigsCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools prune-repo-configs (--tags | --configs) [--confirm]

    Delete unused SCA private package repository configuration tags or configurations.
    Without --confirm, the tags or configurations that would be deleted are only listed.

    --tags                        Delete tags that have no associated configurations.

    --configs                     Delete configurations that are not associated with any
                                  project.

    --confirm                     Perform the deletions.  Without this flag nothing
                                  is deleted.
    """
    # fmt: on

    CMD_NAME = "prune-repo-configs"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            PruneRepoConfigsCommand.__doc__,
            [PruneRepoConfigsCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        confirm = bool(parsed_args["--confirm"])

        if parsed_args["--tags"]:
            await self.__prune_tags(confirm)
        else:
            await self.__prune_configurations(confirm)

    async def __prune_tags(self, confirm: bool):
        unused = []

        async for tag_json in tqdm(
            page_generator(
                retrieve_list_of_configurations_by_tag,
                offset_param="PageNumber",
                offset_init_value=1,
                offset_is_by_count=False,
                client=self.client,
                PageSize=50,
            ),
            desc="Inspecting tags",
        ):
            tag = PackageRepositoryConfigurationTag.from_tag_json(self.client, tag_json)
            if len(tag.associated_configs) == 0:
                unused.append(tag)

        _log.info(f"Found {len(unused)} tags with no associated configurations.")

        if not confirm:
            print("Tags that would be deleted (use --confirm to delete):")
            for tag in unused:
                print(f"  {tag.name} ({tag.tagid})")
            return

        semaphore = asyncio.Semaphore(self.threads)

        async def delete(tag: PackageRepositoryConfigurationTag):
            async with semaphore:
                if await tag.delete():
                    _log.info(f"Deleted tag {tag.name} ({tag.tagid}).")
                else:
                    _log.error(f"Failed to delete tag {tag.name} ({tag.tagid}).")

        await tqdm.gather(*[delete(tag) for tag in unused], desc="Deleting tags")

    async def __prune_configurations(self, confirm: bool):
        unused = []

        async for cfg_json in tqdm(
            page_generator(
                retrieve_configurations,
                offset_param="PageNumber",
                offset_init_value=1,
                offset_is_by_count=False,
                client=self.client,
                PageSize=50,
            ),
            desc="Inspecting configurations",
        ):
            cfg = PackageRepositoryConfiguration.from_config_json(self.client, cfg_json)
            if len(cfg.associated_projects) == 0:
                unused.append(cfg)

        _log.info(
            f"Found {len(unused)} configurations not associated with any project."
        )

        if not confirm:
            print("Configurations that would be deleted (use --confirm to delete):")
            for cfg in unused:
                print(f"  {cfg.name} ({cfg.configId}) [{cfg.packageManager.value}]")
            return

        semaphore = asyncio.Semaphore(self.threads)

        async def delete(cfg: PackageRepositoryConfiguration):
            async with semaphore:
                if await cfg.delete():
                    _log.info(f"Deleted configuration {cfg.name} ({cfg.configId}).")
                else:
                    _log.error(
                        f"Failed to delete configuration {cfg.name} ({cfg.configId})."
                    )

        await tqdm.gather(
            *[delete(cfg) for cfg in unused], desc="Deleting configurations"
        )

    @staticmethod
    def print_help():
        print(PruneRepoConfigsCommand.__doc__)
