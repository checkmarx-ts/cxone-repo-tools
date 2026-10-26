import aiofiles, logging
from docopt import docopt
from tqdm.asyncio import tqdm
from typing import Dict, List
from cxone_api.high.sca.registry import (
    PackageRepositoryConfiguration,
    PackageRepositoryConfigurationTag,
    PackageManagerType,
)
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import (
    AbortedConversionException,
    InvalidRepositoryConfiguration,
)

_log = logging.getLogger(__name__)

# One option per supported package manager type, e.g. --nuget FILE.
_PM_OPTIONS = {pm: f"--{pm.value}" for pm in PackageManagerType}


class DeployTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools deploy-tag (-h | --help | --version)
      cxone-repo-tools deploy-tag --tag-name TAGNAME {USAGE_OPTIONS}

    Create a configuration tag and an SCA private package repository configuration for
    each package manager type provided.  Each configuration is created from the content
    of the given file and associated with the tag.  At least one package manager type
    must be provided.

    --tag-name TAGNAME            The name of the new tag.  The name must not already
                                  be in use by another tag.

{PM_OPTIONS}
    """
    # fmt: on

    __doc__ = __doc__.format(
        USAGE_OPTIONS=" ".join(f"[{opt} FILE]" for opt in _PM_OPTIONS.values()),
        PM_OPTIONS="\n\n".join(
            f"    {opt + ' FILE':<30}Path to the {pm.value} configuration content file."
            for pm, opt in _PM_OPTIONS.items()
        ),
    )

    CMD_NAME = "deploy-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            DeployTagCommand.__doc__,
            [DeployTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        tag_name = parsed_args["--tag-name"]

        content_files: Dict[PackageManagerType, str] = {
            pm: parsed_args[opt]
            for pm, opt in _PM_OPTIONS.items()
            if parsed_args[opt] is not None
        }

        if len(content_files) == 0:
            raise InvalidRepositoryConfiguration.no_package_manager_configs()

        existing = await PackageRepositoryConfigurationTag.retrieve_by_name(
            self.client, tag_name
        )
        if len(existing) > 0:
            raise InvalidRepositoryConfiguration.tag_name_exists(
                tag_name, [tag.tagid for tag in existing]
            )

        contents = {}
        for pm, path in content_files.items():
            async with aiofiles.open(path, "rt", encoding="UTF-8") as f:
                contents[pm] = await f.read()

        tag = await PackageRepositoryConfigurationTag.create_new(self.client, tag_name)
        _log.info(f"Created tag {tag.name} ({tag.tagid}).")

        for pm, content in tqdm(contents.items(), desc="Creating configurations"):
            cfg = await PackageRepositoryConfiguration.create_new(
                self.client, f"{tag_name}-{pm.value}", pm, content, tags=[tag]
            )
            _log.info(
                f"Created configuration {cfg.name} ({cfg.configId}) [{pm.value}] "
                f"associated with tag {tag.name} ({tag.tagid})."
            )

    @staticmethod
    def print_help():
        print(DeployTagCommand.__doc__)
