import logging
from docopt import docopt, ParsedOptions
from typing import List
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.exceptions import (
    AbortedConversionException,
    ConversionException,
)
from cxone_repo_tools.connection import Connector
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.low.projects import update_specific_project_fields
from .scm_token import get_scm_token

_log = logging.getLogger(__name__)


class ConnectScmCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools connect-scm
                      --scm-id SCMID --project-id PROJECTID
                      --scm-org ORG
                      [--repo-name REPONAME]
                      [--project-name PROJNAME]
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

    --repo-name REPONAME          The repository name.  If not provided, the project's
                                  name is used as the repository name: the new name
                                  when --project-name is given, otherwise the current
                                  name.  If the repository is not found in the SCM, the
                                  connection will fail.

                                  The repo name should be the portion of the repo URL
                                  after the SCM URL and not include the .git extension.

    --project-name PROJNAME       The project name that will be set on the project before
                                  it is connected.  If it is the project's current name,
                                  the project is not renamed.  If the connection fails,
                                  the name change is not rolled back.

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

    async def __precheck(self, project_id: str) -> str:
        """Validates that the project is not already connected to an SCM.

        :param project_id: The ID of the project to connect.
        :type project_id: str

        :return: The project's current name.
        :rtype: str

        :raises ConversionException: The project is already connected to an
                                     SCM.
        """
        repo_cfg = await ProjectRepoConfig.from_project_id(self.client, project_id)

        if await repo_cfg.is_scm_imported:
            raise ConversionException.project_already_connected(
                project_id, repo_cfg.name
            )

        return repo_cfg.name

    async def __rename(self, project_id: str, project_name: str) -> None:
        """Sets the project's name with the PATCH project settings API.

        :param project_id: The ID of the project.
        :type project_id: str

        :param project_name: The name to set on the project.
        :type project_name: str

        :raises ConversionException: The project name was not changed.
        """
        if not (
            await update_specific_project_fields(
                self.client, project_id, name=project_name
            )
        ).ok:
            raise ConversionException.rename_failed(project_id, project_name)

        _log.info(f"Project {project_id} renamed to {project_name}.")

    async def execute(self, cmdline_args: List[str]):
        """Connects the project named by --project-id to the SCM named by
        --scm-id, after checking that it is not already connected and, with
        a --project-name that differs from the current name, renaming it.

        :param cmdline_args: The command's arguments, without the command name.
        :type cmdline_args: List[str]

        :raises AbortedConversionException: No Checkmarx One connection
                                            parameters were provided, or the
                                            SCM PAT option is provided but the
                                            PAT is missing or empty.
        :raises ConversionException: The project is already connected to an
                                     SCM, the rename failed, or the project
                                     was not connected to the SCM.
        """
        parsed_args = docopt(
            ConnectScmCommand.__doc__,
            [ConnectScmCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        scm_token = get_scm_token(parsed_args["--token"], parsed_args["--token-env"])

        project_id = parsed_args["--project-id"]
        project_name = parsed_args["--project-name"]

        current_name = await self.__precheck(project_id)

        if project_name is not None:
            if project_name == current_name:
                _log.info(
                    f"Project {project_id} is already named {project_name}; "
                    "the rename step is skipped."
                )
            else:
                await self.__rename(project_id, project_name)

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
