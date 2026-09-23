import asyncio, sys, traceback, urllib3
from docopt import docopt, DocoptExit, ParsedOptions
from typing import Dict, List, Coroutine
from . import AGENT
from .client import mt_endpoints, client_factory
from .export import ProjectAssignmentExport, ScmExport
from .convert import (
    ConversionException,
    BatchConverter,
    RecoverableConverter,
    NameFilterConverter,
    GroupFilterConverter,
)
from .connection import Disconnector, Connector
from cxone_api import CxOneClient


def make_engine_list(args: Dict) -> List[str]:
    engines = []

    if args.get("--sca"):
        engines.append("sca")
    if args.get("--kics"):
        engines.append("kics")
    if args.get("--2ms"):
        engines.append("2ms")
    if args.get("--apisec"):
        engines.append("apisec")
    if args.get("--sast"):
        engines.append("sast")
    if args.get("--ossf"):
        engines.append("ossf")
    if args.get("--container"):
        engines.append("container")
    if args.get("--aisc"):
        engines.append("aisc")

    return engines


def __batch_coro_factory(
    args: ParsedOptions, client: CxOneClient, threads: int
) -> Coroutine:
    if args["--recovery-only"]:
        return RecoverableConverter(client, args["--report"], threads=threads).convert()
    else:
        max_batches = args.get("--max-batches")
        if max_batches is None:
            max_batches = 0

        convert_args = [
            client,
            args["--source-id"],
            args["--target-id"],
            args["--report"],
            threads,
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


async def main():
    # fmt: off
    """Usage:
        cxone-repo-tools (-h | --help | --version)
        cxone-repo-tools (export-projects | export-scms)
                        --tenant TENANT [--threads THREADS]
                        (--api-key APIKEY | --api-key-env)
                        (--cxone-hostname FQDN | --cxone-region REGION)
                        [--retries RETRIES]
                        [-k] [--proxy-url PROXY_URL] [--out EXPORT_FILE]
        cxone-repo-tools convert-scms
                        --tenant TENANT [--threads THREADS]
                        (--api-key APIKEY | --api-key-env)
                        (--cxone-hostname FQDN | --cxone-region REGION)
                        [--retries RETRIES]
                        [-k] [--proxy-url PROXY_URL]
                        [--report REPORT_FILE]
                        [--max-batches MAXBATCH]
                        [--ignore-url-mismatch] [--skip-recovery]
                        [--project-id PROJECTID | --project-name-match REGEX | --project-group-match REGEX]
                        [--regex-ignore-case]
                        --target-id TARGETID --source-id SOURCEIDS...
        cxone-repo-tools convert-scms
                        --tenant TENANT [--threads THREADS]
                        (--api-key APIKEY | --api-key-env)
                        (--cxone-hostname FQDN | --cxone-region REGION)
                        [--retries RETRIES]
                        [-k] [--proxy-url PROXY_URL]
                        [--report REPORT_FILE]
                        --recovery-only
        cxone-repo-tools disconnect-scm
                        --tenant TENANT [--threads THREADS]
                        (--api-key APIKEY | --api-key-env)
                        (--cxone-hostname FQDN | --cxone-region REGION)
                        [--retries RETRIES]
                        [-k] [--proxy-url PROXY_URL]
                        (--scm-id SCMID | --project-id PROJECTID)
        cxone-repo-tools connect-scm
                        --tenant TENANT
                        (--api-key APIKEY | --api-key-env)
                        (--cxone-hostname FQDN | --cxone-region REGION)
                        [--retries RETRIES]
                        [-k] [--proxy-url PROXY_URL]
                        --scm-id SCMID --project-id PROJECTID
                        --scm-org ORG
                        [--repo-name REPONAME]
                        [--protected-branch BRANCH...]
                        [--sca][--kics][--2ms][--apisec]
                        [--sast][--sast-incremental][--ossf]
                        [--container][--aisc]
                        [--auto-sca-pr]
                        [--pr-decorations]
                        [--webhook]

    ## Common Options

    These options may be used by multiple operations as shown in the
    usage examples above.

    --tenant TENANT               Checkmarx One tenant

    --api-key APIKEY              Checkmarx One API Key

    --api-key-env                 Obtain the API Key from environment variable CX_API_KEY

    --cxone-hostname FQDN         The FQDN of the CxOne hostname for your instance
                                  (name only, not the https:// protocol prefix)

    --cxone-region REGION         The multi-tenant region: {MTREGION}

    --retries RETRIES             The number of retries to attempt with API failures. [default: 255]

    -k                            Turn off SSL verification

    --proxy-url PROXY_URL         URL to proxy server

    --project-id PROJECTID        For operations that support it, the ID of a single project
                                  that is the target of the operation.

    --scm-id SCMID                The ID of the SCM configuration used as the target of
                                  the operation.

    --threads THREADS             The number of concurrent threads. [default: 2]

    ## export-projects

    Exports a list of projects and their SCM assignment details.

    ## export-scms

    Exports a list of SCM connection details.

    ### Common Export Parameters

    --out EXPORT_FILE             The name of the CSV export file. [default: ./export.csv]


    ## convert-scms

    Converts all projects assigned to source SCMs to target SCM.

    --report REPORT_FILE          Path to conversion report CSV. [default: ./report.csv]

    --source-id SOURCEIDS...      Source SCM IDs to convert to using the target SCM. Repeat
                                  for multiple source SCMs.

    --max-batches MAXBATCH        Maximum number of batches to convert this run. All projects
                                  will be converted in random batches if not specified.

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

    ### Common Convert Parameters

    --target-id TARGETID          Target SCM ID

    ## disconnect-scm

    Disconnect a single project from an SCM or all projects connected to an SCM.

    WARNING: Batched conversion back to a connected SCM is not possible after
    a project has been disconnected!

    ## connect-scm

    Connects a manual scan project to an SCM.

    --scm-org ORG                 The organization name in the SCM containing the
                                  repository corresponding to the project.

    --repo-name REPONAME          The repository name.  If not provided, the name of the
                                  project will be used as the repository name.  If the
                                  repository is not found in the SCM, the connection
                                  will fail.

                                  The repo name should be the portion of the repo URL
                                  after the SCM URL and not include the .git extension.

    --protected-branch BRANCH...  Repeat with each branch name that is to be considered
                                  a protected branch.

    --sca                         Enable the SCA engine for initiated scans.

    --kics                        Enable the KICS engine for initiated scans.

    --2ms                         Enable the secret scanning engine for initiated scans.

    --apisec                      Enable the API security engine for initiated scans.

    --sast                        Enable the SAST engine for initiated scans.

    --sast-incremental            Initiated SAST scans are executed as incremental scans.

    --ossf                        Enable the OSSF scorecard for initiated scans.

    --container                   Enable the container scanning engine for initiated scans.

    --aisc                        Enable the AI supply chain engine for initiated scans.

    --auto-sca-pr                 Enable SCA automatic pull-requests.

    --pr-decorations              Enable pull-request decorations with scan summary results.

    --webhook                     Allow webhook events to initiate scans.

    """
    # fmt: on
    try:
        args = docopt(main.__doc__.replace("{MTREGION}", mt_endpoints()), version=AGENT)

        if bool(args["-k"]):
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        client = client_factory(
            args["--api-key"],
            args["--api-key-env"],
            args["--cxone-hostname"],
            args["--cxone-region"],
            args["--tenant"],
            args["--proxy-url"],
            not bool(args["-k"]),
            int(args["--retries"]),
        )

        threads = int(args["--threads"])

        if args["export-projects"]:
            await ProjectAssignmentExport(client, threads=threads).export(args["--out"])
        elif args["export-scms"]:
            await ScmExport(client, threads=threads).export(args["--out"])
        elif args["convert-scms"]:
            await __batch_coro_factory(args, client, threads)
        elif args["disconnect-scm"]:
            operator = None
            if args.get("--scm-id") is not None:
                operator = Disconnector.from_scm_id(
                    client, int(args.get("--scm-id")), threads=threads
                )
            elif args.get("--project-id") is not None:
                operator = Disconnector.from_project_id(
                    client, args.get("--project-id"), threads=threads
                )

            await operator.disconnect()

        elif args["connect-scm"]:
            await Connector.connect(
                client,
                int(args.get("--scm-id")),
                args.get("--project-id"),
                args.get("--scm-org"),
                make_engine_list(args),
                args.get("--sast-incremental"),
                args.get("--webhook"),
                args.get("--auto-sca-pr"),
                args.get("--pr-decorations"),
                repo_name=args.get("--repo-name"),
                protected_branches=args.get("--protected-branch"),
            )

        exit(0)
    except DocoptExit as bad_args:
        print("Incorrect arguments provided.", file=sys.stderr, flush=True)
        print(bad_args, file=sys.stderr, flush=True)
    except ConversionException as cex:
        print(cex, file=sys.stderr, flush=True)
    except Exception:
        print(traceback.format_exc(), file=sys.stderr, flush=True)

    exit(1)


def cli_entry():
    asyncio.run(main())


if __name__ == "__main__":
    cli_entry()
