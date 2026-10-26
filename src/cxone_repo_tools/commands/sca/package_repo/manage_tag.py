from docopt import docopt
from typing import List
from ...base import Command
from ....convert import AbortedConversionException


class ManageTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools manage-tag (-h | --help | --version)
      cxone-repo-tools manage-tag

    Manage SCA private package repository configurations associated with a private
    repository configuration tag.

    """
    # fmt: on

    CMD_NAME = "manage-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            ManageTagCommand.__doc__,
            [ManageTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        raise NotImplementedError(
            f"Command {ManageTagCommand.CMD_NAME} is not implemented."
        )

    @staticmethod
    def print_help():
        print(ManageTagCommand.__doc__)
