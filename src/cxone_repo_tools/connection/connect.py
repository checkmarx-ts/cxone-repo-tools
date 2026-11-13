from typing import List
from cxone_repo_tools.convert import BatchConverter
from cxone_repo_tools.client import CxOneRepoToolsClient
from cxone_api.util import json_on_ok
from cxone_api.low.repos_manager import get_scm_by_id
from cxone_api.low.projects import retrieve_project_info
from cxone_api.high.projects import ProjectRepoConfig


class Connector:

    @staticmethod
    async def connect(
        client: CxOneRepoToolsClient,
        scm_id: int,
        project_id: str,
        org: str,
        engines: List[str],
        sast_incremental: bool,
        webhook: bool,
        auto_pr: bool,
        pr_decorate: bool,
        *,
        repo_name: str = None,
        protected_branches: List[str] = [],
        token: str | None = None,
    ):
        """Connects a manual project to an SCM with the conversion API.

        :param client: The client used to make Checkmarx One API calls.
        :type client: CxOneRepoToolsClient

        :param scm_id: The ID of the SCM the project is connected to.
        :type scm_id: int

        :param project_id: The ID of the project to connect.
        :type project_id: str

        :param org: The organization in the SCM that contains the repository.
        :type org: str

        :param engines: The scan engines enabled for initiated scans.
        :type engines: List[str]

        :param sast_incremental: True to run initiated SAST scans as
                                 incremental scans.
        :type sast_incremental: bool

        :param webhook: True to allow webhook events to initiate scans.
        :type webhook: bool

        :param auto_pr: True to enable SCA automatic pull-requests.
        :type auto_pr: bool

        :param pr_decorate: True to enable pull-request decorations.
        :type pr_decorate: bool

        :param repo_name: The repository path after the SCM's repository base
                          URL.  Defaults to the project name.
        :type repo_name: str, optional

        :param protected_branches: The protected branch names.  Defaults to
                                   no protected branches.
        :type protected_branches: List[str], optional

        :param token: The SCM PAT for SCMs that require a token for
                      connection.  It is added to the API payload only when
                      it is not None.  Defaults to None.
        :type token: str | None, optional

        :raises ResponseException: A Checkmarx One API call failed.
        """

        scm_data = json_on_ok(await get_scm_by_id(client, scm_id))
        project_name = json_on_ok(await retrieve_project_info(client, project_id)).get(
            "name"
        )

        if repo_name is None:
            repo_name = project_name

        repo_base_url = scm_data.get("repoBaseUrl")

        payload = {
            "scmType": scm_data.get("type"),
            "scmOnPremUrl": repo_base_url,
            "orgIdentity": org,
            "projects": [
                {
                    "cxProjectId": project_id,
                    "scmRepositoryUrl": repo_base_url.rstrip("/")
                    + "/"
                    + repo_name.lstrip("/").rstrip("/"),
                    "protectedBranches": protected_branches,
                    "types": engines,
                    "scaAutoPrEnabled": auto_pr,
                    "decoratePullRequests": pr_decorate,
                    "webhookEnabled": webhook,
                }
            ],
        }

        if token is not None:
            payload["token"] = token

        await BatchConverter.convert_project_and_wait(client, payload)

        if sast_incremental:
            repo_cfg = await ProjectRepoConfig.from_project_id(client, project_id)
            await repo_cfg.update_repository_toggles(sastIncrementalScan=True)
