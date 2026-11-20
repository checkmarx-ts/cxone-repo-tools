from docopt import docopt, ParsedOptions
from typing import List, Coroutine
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.exceptions import AbortedConversionException
from cxone_repo_tools.convert import (
    BatchConverter,
    RecoverableConverter,
    NameFilterConverter,
    GroupFilterConverter,
)
from .scm_token import get_scm_token
from cxone_repo_tools.convert.mapping import (
    DefaultConversionMapper,
    SubstituteConversionMapper,
)


class ConvertScmsCommand(Command):
    # fmt: off
    """Usage:
        cxone-repo-tools convert-scms
                        [--report REPORT_FILE]
                        [--max-batches MAXBATCH]
                        [--skip-recovery]
                        [--project-id PROJECTID | --project-name-match REGEX | --project-group-match REGEX]
                        [--regex-ignore-case]
                        [(--map-fields FIELDREGEX --map-target-repo REPOSPEC
                          [--map-target-project PRJSPEC])]
                        [--token TOKEN | --token-env]
                        --target-id TARGETID --target-org ORGNAME
                        --source-id SOURCEIDS...
        cxone-repo-tools convert-scms
                        [--token TOKEN | --token-env]
                        [--report REPORT_FILE]
                        --recovery-only

    Converts all projects assigned to source SCMs to target SCM.

    --report REPORT_FILE          Path to conversion report CSV. [default: ./convert_report.csv]

    --source-id SOURCEIDS...      Source SCM IDs of projects to convert to using the
                                  target SCM. Repeat for multiple source SCMs.

    --target-id TARGETID          Target SCM ID where the project will be assigned
                                  after conversion.

    --target-org ORGNAME          The name of the target organization in the target SCM.

    --map-fields FIELDREGEX       The field extraction regular expression (e.g. (?P<field>[^/]+))
                                  used to extract fields from the portion of the source
                                  project's repository URL (portion of the repository URL
                                  after the "http://<baseurl>/<org>/" prefix) to obtain fields
                                  used in the REPOSPEC and PRJSPEC.
    
    --map-target-repo REPOSPEC    The substitution specification for mapping portions of the
                                  source repository URL to the target repository URL.  Static
                                  text can surround extracted variables surrounded by curly
                                  brackets (e.g. "static-prefix/{field1}/{field2}/static-suffix").
                                  If a substitution spec is not provided, the source repository
                                  sub-path after the organization is used by default.

    --map-target-project PRJSPEC  The substitution specification for the project name after
                                  conversion, built from static text and the fields extracted
                                  by --map-fields (e.g. "{field1}-{field2}").  Can only be used
                                  with --map-fields.  If not provided, the project name is not
                                  changed by the conversion.

    --max-batches MAXBATCH        Maximum number of batches of 15 projects to convert this
                                  run. All projects will be converted in random batches
                                  if not specified.

    --recovery-only               Only resume and complete any conversions left in-progress
                                  from a previous, interrupted run, then exit.

    --skip-recovery               Don't perform recovery this run if recovery
                                  files are found.
    
    --project-id PROJECTID        A project id of a single project to convert.
    
    --project-name-match REGEX    Converts projects with names matching the provided
                                  regular expression.
    
    --project-group-match REGEX   Converts projects assigned to at least one group
                                  whose path matches the provided regular expression.

    --regex-ignore-case           Use case-insensitive regular expression matching.

    --token TOKEN                 An SCM PAT for SCMs that require a token for conversion.

    --token-env                   Retrieves the SCM PAT from the environment variable CX_PAT.

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
        """Creates the conversion coroutine for the parsed command line.

        :param args: The parsed command line options.
        :type args: ParsedOptions

        :return: The coroutine that performs the recovery or the conversion.
        :rtype: Coroutine

        :raises re.error: --map-fields is not a valid regular expression.
        :raises ValueError: --map-target-repo is not a valid substitution
                            specification.
        :raises AbortedConversionException: The SCM PAT option is provided but
                                            the PAT is missing or empty.
        """
        scm_token = get_scm_token(args["--token"], args["--token-env"])

        if args["--recovery-only"]:
            return RecoverableConverter(
                self.client, args["--report"], scm_token, threads=self.threads
            ).convert()
        else:
            if args["--map-fields"] is not None:
                mapper = SubstituteConversionMapper(
                    args["--map-fields"],
                    args["--map-target-repo"],
                    args["--map-target-project"],
                )
            else:
                mapper = DefaultConversionMapper()

            max_batches = args.get("--max-batches")
            if max_batches is None:
                max_batches = 0

            convert_args = [
                self.client,
                [int(x) for x in args["--source-id"]],
                int(args["--target-id"]),
                args["--target-org"],
                mapper,
                scm_token,
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
                skip_recovery=args["--skip-recovery"],
            )

    @staticmethod
    def print_help():
        print(ConvertScmsCommand.__doc__)
