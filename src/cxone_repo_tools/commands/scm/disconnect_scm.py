from docopt import docopt
from typing import List
from ..base import Command
from ...convert import AbortedConversionException
from ...connection import Disconnector


class DisconnectScmCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools disconnect-scm (-h | --help | --version)
      cxone-repo-tools disconnect-scm (--scm-id SCMID | --project-id PROJECTID)

    Disconnect a single project from an SCM or all projects connected to an SCM.

    WARNING: Batched conversion back to a connected SCM is not possible after
    a project has been disconnected!

    --scm-id SCMID                The ID of the SCM configuration.  All projects connected
                                  to the SCM will be disconnected.

    --project-id PROJECTID        The ID of a single project to disconnect from its SCM.

    """
    # fmt: on

    CMD_NAME = "disconnect-scm"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            DisconnectScmCommand.__doc__,
            [DisconnectScmCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        if parsed_args.get("--scm-id") is not None:
            operator = Disconnector.from_scm_id(
                self.client, int(parsed_args["--scm-id"]), threads=self.threads
            )
        else:
            operator = Disconnector.from_project_id(
                self.client, parsed_args["--project-id"], threads=self.threads
            )

        await operator.disconnect()

    @staticmethod
    def print_help():
        print(DisconnectScmCommand.__doc__)
