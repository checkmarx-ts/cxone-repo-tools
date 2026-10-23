from docopt import docopt
from typing import List
from .command import Command
from ..convert import AbortedConversionException


class AuditAssocCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools audit-assoc (-h | --help | --version)
      cxone-repo-tools audit-assoc

    Produce a CSV showing SCA private package repository configurations associated
    with each project.

    """
    # fmt: on

    CMD_NAME = "audit-assoc"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            AuditAssocCommand.__doc__,
            [AuditAssocCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        raise NotImplementedError(
            f"Command {AuditAssocCommand.CMD_NAME} is not implemented."
        )

    @staticmethod
    def print_help():
        print(AuditAssocCommand.__doc__)
