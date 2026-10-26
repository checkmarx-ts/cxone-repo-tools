from docopt import docopt
from typing import List
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import AbortedConversionException


class DeployTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools deploy-tag (-h | --help | --version)
      cxone-repo-tools deploy-tag

    Deploy SCA private package repository configurations associated with a tag to
    selected projects.

    """
    # fmt: on

    CMD_NAME = "deploy-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            DeployTagCommand.__doc__,
            [DeployTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        raise NotImplementedError(
            f"Command {DeployTagCommand.CMD_NAME} is not implemented."
        )

    @staticmethod
    def print_help():
        print(DeployTagCommand.__doc__)
