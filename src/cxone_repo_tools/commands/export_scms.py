from docopt import docopt
from typing import List
from .command import Command
from ..convert import AbortedConversionException
from ..export import ScmExport


class ExportScmsCommand(Command):
    # fmt: off
    """Usage:
    cxone-repo-tools export-scms (-h | --help | --version)
    cxone-repo-tools export-scms [--out EXPORT_FILE]

    --out EXPORT_FILE             The name of the CSV export file. [default: ./scm_export.csv]

    """
    # fmt: on

    CMD_NAME = "export-scms"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            ExportScmsCommand.__doc__,
            [ExportScmsCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        await ScmExport(self.client, threads=self.threads).export(parsed_args["--out"])

    @staticmethod
    def print_help():
        print(ExportScmsCommand.__doc__)
