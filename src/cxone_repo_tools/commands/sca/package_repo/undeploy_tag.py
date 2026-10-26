from docopt import docopt
from typing import List
from ...base import Command
from ....convert import AbortedConversionException


class UndeployTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools undeploy-tag (-h | --help | --version)
      cxone-repo-tools undeploy-tag

    Remove SCA private package repository configurations associated with a tag from
    selected projects.

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

        raise NotImplementedError(
            f"Command {UndeployTagCommand.CMD_NAME} is not implemented."
        )

    @staticmethod
    def print_help():
        print(UndeployTagCommand.__doc__)
