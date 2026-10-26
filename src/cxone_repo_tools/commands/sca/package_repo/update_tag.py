import aiofiles, logging
from docopt import docopt
from tqdm.asyncio import tqdm
from typing import List
from cxone_api.high.sca.registry import PackageRepositoryConfiguration
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import (
    AbortedConversionException,
    InvalidRepositoryConfiguration,
)
from .util import resolve_tag, pm_usage_options, pm_option_docs, pm_content_files

_log = logging.getLogger(__name__)


class UpdateTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools update-tag (-h | --help | --version)
      cxone-repo-tools update-tag (--tag-id TAGID | --tag-name TAGNAME) {USAGE_OPTIONS}

    Update the content of the SCA private package repository configurations associated
    with a tag.  For each package manager type provided, the configuration of that type
    associated with the tag is updated with the content of the given file.  Configurations
    of other package manager types are not changed.  At least one package manager type
    must be provided.

    --tag-id TAGID                The ID of the tag to update.

    --tag-name TAGNAME            The name of the tag to update.  Tag names are not
                                  unique; if more than one tag has the name, the
                                  command fails and lists the matching tag ids.

{PM_OPTIONS}
    """
    # fmt: on

    __doc__ = __doc__.format(
        USAGE_OPTIONS=pm_usage_options(), PM_OPTIONS=pm_option_docs()
    )

    CMD_NAME = "update-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            UpdateTagCommand.__doc__,
            [UpdateTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        content_files = pm_content_files(parsed_args)

        if len(content_files) == 0:
            raise InvalidRepositoryConfiguration.no_package_manager_configs()

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

        # Validate every requested type before changing anything.
        targets = {}
        for pm in content_files.keys():
            matches = [cfg for cfg in configs if cfg.packageManager == pm]
            if len(matches) == 0:
                raise InvalidRepositoryConfiguration.no_configuration_of_type(
                    tag.name, tag.tagid, pm.value
                )
            if len(matches) > 1:
                raise InvalidRepositoryConfiguration.duplicate_type_in_tag(
                    tag.name, tag.tagid, pm.value, [cfg.configId for cfg in matches]
                )
            targets[pm] = matches[0]

        contents = {}
        for pm, path in content_files.items():
            async with aiofiles.open(path, "rt", encoding="UTF-8") as f:
                contents[pm] = await f.read()

        for pm, cfg in tqdm(targets.items(), desc="Updating configurations"):
            if await cfg.update_content(contents[pm]):
                _log.info(
                    f"Updated configuration {cfg.name} ({cfg.configId}) [{pm.value}] "
                    f"in tag {tag.name} ({tag.tagid})."
                )
            else:
                _log.error(
                    f"Failed to update configuration {cfg.name} ({cfg.configId}) "
                    f"[{pm.value}]."
                )

    @staticmethod
    def print_help():
        print(UpdateTagCommand.__doc__)
