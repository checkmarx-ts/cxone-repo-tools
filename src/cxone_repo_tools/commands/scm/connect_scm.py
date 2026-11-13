import logging
from docopt import docopt, ParsedOptions
from typing import List
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.exceptions import (
    AbortedConversionException,
    ConversionException,
)
from cxone_repo_tools.connection import Connector
from .scm_token import get_scm_token

_log = logging.getLogger(__name__)


class ConnectScmCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools connect-scm
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
                      [--token TOKEN | --token-env]

    Connects a manual scan project to an SCM.

    --scm-id SCMID                The ID of the SCM configuration the project will be
                                  connected to.

    --project-id PROJECTID        The ID of the project to connect to the SCM.

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

    --token TOKEN                 An SCM PAT for SCMs that require a token for connection.

    --token-env                   Retrieves the SCM PAT from the environment variable CX_PAT.

    """
    # fmt: on

    CMD_NAME = "connect-scm"

    __ENGINE_FLAGS = {
        "--sca": "sca",
        "--kics": "kics",
        "--2ms": "2ms",
        "--apisec": "apisec",
        "--sast": "sast",
        "--ossf": "ossf",
        "--container": "container",
        "--aisc": "aisc",
    }

    @staticmethod
    def __make_engine_list(args: ParsedOptions) -> List[str]:
        return [
            engine
            for flag, engine in ConnectScmCommand.__ENGINE_FLAGS.items()
            if args.get(flag)
        ]

    async def execute(self, cmdline_args: List[str]):
        """Connects the project named by --project-id to the SCM named by
        --scm-id.

        :param cmdline_args: The command's arguments, without the command name.
        :type cmdline_args: List[str]

        :raises AbortedConversionException: No Checkmarx One connection
                                            parameters were provided, or the
                                            SCM PAT option is provided but the
                                            PAT is missing or empty.
        :raises ConversionException: The project was not connected to the SCM.
        """
        parsed_args = docopt(
            ConnectScmCommand.__doc__,
            [ConnectScmCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        scm_token = get_scm_token(parsed_args["--token"], parsed_args["--token-env"])

        connected = await Connector.connect(
            self.client,
            int(parsed_args["--scm-id"]),
            parsed_args["--project-id"],
            parsed_args["--scm-org"],
            ConnectScmCommand.__make_engine_list(parsed_args),
            parsed_args["--sast-incremental"],
            parsed_args["--webhook"],
            parsed_args["--auto-sca-pr"],
            parsed_args["--pr-decorations"],
            repo_name=parsed_args.get("--repo-name"),
            protected_branches=parsed_args.get("--protected-branch"),
            token=scm_token,
        )

        if not connected:
            raise ConversionException.connection_failed(
                parsed_args["--project-id"], parsed_args["--scm-id"]
            )

        _log.info(
            f"Project {parsed_args['--project-id']} connected to SCM "
            f"{parsed_args['--scm-id']}."
        )

    @staticmethod
    def print_help():
        print(ConnectScmCommand.__doc__)
