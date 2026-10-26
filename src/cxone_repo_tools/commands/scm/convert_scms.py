from docopt import docopt, ParsedOptions
from typing import List, Coroutine
from cxone_api import CxOneClient
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import (
    AbortedConversionException,
    BatchConverter,
    RecoverableConverter,
    NameFilterConverter,
    GroupFilterConverter,
)


class ConvertScmsCommand(Command):
    # fmt: off
    """Usage:
        cxone-repo-tools convert-scms (-h | --help | --version)
        cxone-repo-tools convert-scms
                        [--report REPORT_FILE]
                        [--max-batches MAXBATCH]
                        [--ignore-url-mismatch]
                        [--skip-recovery]
                        [--project-id PROJECTID | --project-name-match REGEX | --project-group-match REGEX]
                        [--regex-ignore-case]
                        --target-id TARGETID --source-id SOURCEIDS...
        cxone-repo-tools convert-scms
                        [--report REPORT_FILE]
                        --recovery-only

    Converts all projects assigned to source SCMs to target SCM.

    --report REPORT_FILE          Path to conversion report CSV. [default: ./convert_report.csv]

    --source-id SOURCEIDS...      Source SCM IDs of projects to convert to using the
                                  target SCM. Repeat for multiple source SCMs.

    --target-id TARGETID          Target SCM ID where the project will be assigned
                                  after conversion.

    --max-batches MAXBATCH        Maximum number of batches of 15 projects to convert this
                                  run. All projects will be converted in random batches
                                  if not specified.

    --recovery-only               Only resume and complete any conversions left in-progress
                                  from a previous, interrupted run, then exit.

    --ignore-url-mismatch         Ignore mismatches of repository base URLs.

    --skip-recovery               Don't perform recovery this run if recovery
                                  files are found.

    --project-name-match REGEX    Converts projects with names matching the provided
                                  regular expression.
    
    --project-group-match REGEX   Converts projects assigned to at least one group
                                  whose path matches the provided regular expression.

    --regex-ignore-case           Use case-insensitive regular expression matching.

    """
    # fmt: on

    CMD_NAME = "convert-scms"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            ConvertScmsCommand.__doc__,
            [ConvertScmsCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        await self.__batch_coro_factory(parsed_args)

    def __batch_coro_factory(self, args: ParsedOptions) -> Coroutine:
        if args["--recovery-only"]:
            return RecoverableConverter(
                self.client, args["--report"], threads=self.threads
            ).convert()
        else:
            max_batches = args.get("--max-batches")
            if max_batches is None:
                max_batches = 0

            convert_args = [
                self.client,
                args["--source-id"],
                args["--target-id"],
                args["--report"],
                self.threads,
            ]

            regex_ignore_case = args["--regex-ignore-case"]
            regex = None

            converter_inst = BatchConverter

            if args.get("--project-name-match") is not None:
                regex = args.get("--project-name-match")
                converter_inst = NameFilterConverter
            elif args.get("--project-group-match") is not None:
                regex = args.get("--project-group-match")
                converter_inst = GroupFilterConverter

            if regex is not None:
                convert_args = [regex, regex_ignore_case] + convert_args

            return converter_inst(*convert_args).convert(
                max_batches=int(max_batches),
                project_id=args.get("--project-id"),
                override_url_mismatch=args["--ignore-url-mismatch"],
                skip_recovery=args["--skip-recovery"],
            )

    @staticmethod
    def print_help():
        print(ConvertScmsCommand.__doc__)
