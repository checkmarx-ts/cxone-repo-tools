from typing import List
from ..convert import BatchConverter
from cxone_api import CxOneClient
from cxone_api.util import json_on_ok
from cxone_api.low.repos_manager import get_scm_by_id
from cxone_api.low.projects import retrieve_project_info
from cxone_api.high.projects import ProjectRepoConfig


class Connector:

    @staticmethod
    async def connect(
        client: CxOneClient,
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
    ):

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

        await BatchConverter.convert_project_and_wait(client, payload)

        if sast_incremental:
            repo_cfg = await ProjectRepoConfig.from_project_id(client, project_id)
            await repo_cfg.update_repository_toggles(sastIncrementalScan=True)
