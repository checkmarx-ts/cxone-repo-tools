from __future__ import annotations
import uuid, asyncio, json, os
from pathlib import Path
from typing import List, Dict
from cxone_api.high.projects import ProjectRepoConfig


class ConversionBatch:
    __RECOVER_FILE_EXT = ".recovery.json"

    def __init__(
        self,
        target_org: str,
        target_scm_type: str,
        target_scm_url: str,
        target_scm_token: str | None,
    ):
        self.__target_scm_token = target_scm_token
        self.__target_org = target_org
        self.__target_scm_type = target_scm_type
        self.__target_scm_url = target_scm_url
        self.__disconnect_projects = []
        self.__enable_sast_incremental_projects = []
        self.__project_convert_data = {}
        self.__project_id_to_cur_name_map = {}
        self.__project_id_to_target_name_map = {}
        self.__batch_id = str(uuid.uuid4())
        self.__file_lock = asyncio.Lock()
        self.__state_lock = asyncio.Lock()
        self.__recovery_mode = False

    def to_dict(self) -> Dict:
        return {
            "batch_id": self.__batch_id,
            "target_org": self.__target_org,
            "target_scm_type": self.__target_scm_type,
            "target_scm_url": self.__target_scm_url,
            "disconnect": self.__disconnect_projects,
            "conversion": self.__project_convert_data,
            "id2name": self.__project_id_to_cur_name_map,
            "targetnames": self.__project_id_to_target_name_map,
            "sast_inc_enabled": self.__enable_sast_incremental_projects,
        }

    @staticmethod
    def from_dict(
        target_scm_token: str | None,
        *,
        target_org: str,
        target_scm_type: str,
        target_scm_url: str,
        batch_id: str,
        disconnect: List[str],
        conversion: Dict,
        id2name: Dict,
        targetnames: Dict,
        sast_inc_enabled: List[str],
    ) -> ConversionBatch:
        inst = ConversionBatch(
            target_org, target_scm_type, target_scm_url, target_scm_token
        )
        inst.__batch_id = batch_id
        inst.__disconnect_projects = disconnect
        inst.__project_convert_data = conversion
        inst.__project_id_to_cur_name_map = id2name
        inst.__project_id_to_target_name_map = targetnames
        inst.__enable_sast_incremental_projects = sast_inc_enabled
        return inst

    @staticmethod
    def load_recovery_batches(
        target_scm_token: str | None,
    ) -> List[ConversionBatch] | None:
        loaded = []

        for recover_file in Path(".").glob(f"*{ConversionBatch.__RECOVER_FILE_EXT}"):
            with open(recover_file, "rt") as json_file:
                loaded.append(
                    ConversionBatch.from_dict(target_scm_token, **json.load(json_file))
                )

        if len(loaded) == 0:
            return None
        else:
            return loaded

    @property
    def batch_id(self) -> str:
        return self.__batch_id

    @property
    def org(self) -> str:
        return self.__target_org

    @property
    def size(self) -> int:
        return len(self.__disconnect_projects)

    @property
    def disconnect_projects(self) -> List[str]:
        return self.__disconnect_projects

    @property
    def batch_projects(self) -> List[str]:
        return list(self.__project_id_to_cur_name_map.keys())

    def get_project_id(self, project_name: str) -> str | None:
        return self.__project_id_to_cur_name_map.get(project_name)

    def get_new_project_name(self, project_id: str) -> str | None:
        return self.__project_id_to_target_name_map.get(project_id)

    def as_api_payload(self):
        payload = {
            "projects": list(self.__project_convert_data.values()),
            "scmType": self.__target_scm_type,
            "scmOnPremUrl": self.__target_scm_url,
            "orgIdentity": self.__target_org,
        }

        if self.__target_scm_token is not None:
            payload["token"] = self.__target_scm_token

        return payload

    @property
    def __recover_file_name(self) -> str:
        return f"{self.batch_id}{ConversionBatch.__RECOVER_FILE_EXT}"

    async def __update_recover_file(self):
        async with self.__file_lock:
            recover_file = Path(self.__recover_file_name)

            with open(recover_file, "wt") as recover_file:
                json.dump(self.to_dict(), recover_file)

    async def __remove_recover_file(self):
        async with self.__file_lock:
            recover_file = Path(self.__recover_file_name)
            if recover_file.exists():
                os.remove(recover_file)

    async def begin_recovery_mode(self):
        async with self.__state_lock:
            self.__recovery_mode = True
            await self.__update_recover_file()

    def check_sast_incremental_enabled(self, project_id: str) -> bool:
        return project_id in self.__enable_sast_incremental_projects

    async def project_complete(self, project_id: str):
        async with self.__state_lock:
            if project_id in self.__disconnect_projects:
                self.__disconnect_projects.remove(project_id)

            if project_id in self.__project_id_to_cur_name_map.keys():
                del self.__project_id_to_cur_name_map[project_id]

            if project_id in self.__project_convert_data.keys():
                del self.__project_convert_data[project_id]

            if project_id in self.__enable_sast_incremental_projects:
                self.__enable_sast_incremental_projects.remove(project_id)

            if self.__recovery_mode:
                await self.__update_recover_file()
                if len(self.__project_convert_data) == 0:
                    self.__recovery_mode = False
                    await self.__remove_recover_file()

    async def add(
        self,
        repo_cfg: ProjectRepoConfig,
        target_repo_url: str,
        target_project_name: str | None,
    ):
        async with self.__state_lock:
            self.__disconnect_projects.append(repo_cfg.id)
            self.__project_id_to_cur_name_map[repo_cfg.name] = repo_cfg.id
            self.__project_id_to_target_name_map[repo_cfg.id] = target_project_name

            if await repo_cfg.sast_incremental_enabled:
                self.__enable_sast_incremental_projects.append(repo_cfg.id)

            self.__project_convert_data[repo_cfg.id] = {
                "cxProjectId": repo_cfg.id,
                "scmRepositoryUrl": target_repo_url,
                "protectedBranches": await repo_cfg.protected_branches,
                "types": await repo_cfg.get_enabled_scanners(
                    await repo_cfg.primary_branch
                ),
                "scaAutoPrEnabled": await repo_cfg.sca_auto_pr_enabled,
                "decoratePullRequests": await repo_cfg.pr_decoration_enabled,
                "webhookEnabled": await repo_cfg.webhook_enabled,
            }

            if self.__recovery_mode:
                await self.__update_recover_file()
