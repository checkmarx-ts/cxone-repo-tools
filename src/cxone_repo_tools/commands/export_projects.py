from docopt import docopt
from typing import List
from .command import Command
from ..convert import AbortedConversionException
from ..export import ProjectAssignmentExport

class ExportProjectsCommand(Command):
  # fmt: off
  """Usage:
  cxone-repo-tools export-projects (-h | --help | --version)
  cxone-repo-tools export-projects [--out EXPORT_FILE]

  --out EXPORT_FILE             The name of the CSV export file. [default: ./project_export.csv]

  """
  # fmt: on

  CMD_NAME = "export-projects"
  
  async def execute(self, cmdline_args : List[str]):
    parsed_args = docopt(ExportProjectsCommand.__doc__, [ExportProjectsCommand.CMD_NAME] + cmdline_args, version=self.version)

    if self.client is None:
      raise AbortedConversionException.no_client()

    await ProjectAssignmentExport(self.client, threads=self.threads).export(parsed_args["--out"])

  @staticmethod
  def print_help():
    print(ExportProjectsCommand.__doc__)
