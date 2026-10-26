from docopt import docopt
from typing import List
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import AbortedConversionException


class UpdateTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools update-tag (-h | --help | --version)
      cxone-repo-tools update-tag

    Update the SCA private package repository configurations associated with a private
    repository configuration tag.

    """
    # fmt: on

    CMD_NAME = "update-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            UpdateTagCommand.__doc__,
            [UpdateTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        raise NotImplementedError(
            f"Command {UpdateTagCommand.CMD_NAME} is not implemented."
        )

    @staticmethod
    def print_help():
        print(UpdateTagCommand.__doc__)
