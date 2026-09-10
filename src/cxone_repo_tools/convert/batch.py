from __future__ import annotations
import uuid, asyncio, json, os
from pathlib import Path
from typing import List, Dict
from cxone_api.high.projects import ProjectRepoConfig


class ConversionBatch:
    __RECOVER_FILE_EXT = ".recovery.json"

    def __init__(self, org: str, scm_type: str, scm_url: str):
        self.__org = org
        self.__scm_type = scm_type
        self.__scm_url = scm_url
        self.__disconnect_projects = []
        self.__enable_sast_incremental_projects = []
        self.__project_convert_data = {}
        self.__project_id_to_name_map = {}
        self.__batch_id = str(uuid.uuid4())
        self.__file_lock = asyncio.Lock()
        self.__state_lock = asyncio.Lock()
        self.__recovery_mode = False

    def to_dict(self) -> Dict:
        return {
            "batch_id": self.__batch_id,
            "org": self.__org,
            "scm_type": self.__scm_type,
            "scm_url": self.__scm_url,
            "disconnect": self.__disconnect_projects,
            "conversion": self.__project_convert_data,
            "id2name": self.__project_id_to_name_map,
            "sast_inc_enabled": self.__enable_sast_incremental_projects,
        }

    @staticmethod
    def from_dict(
        *,
        org: str,
        scm_type: str,
        scm_url: str,
        batch_id: str,
        disconnect: List[str],
        conversion: Dict,
        id2name: Dict,
        sast_inc_enabled: List[str],
    ) -> ConversionBatch:
        inst = ConversionBatch(org, scm_type, scm_url)
        inst.__batch_id = batch_id
        inst.__disconnect_projects = disconnect
        inst.__project_convert_data = conversion
        inst.__project_id_to_name_map = id2name
        inst.__enable_sast_incremental_projects = sast_inc_enabled
        return inst

    @staticmethod
    def load_recovery_batches() -> List[ConversionBatch] | None:
        loaded = []

        for recover_file in Path(".").glob(f"*{ConversionBatch.__RECOVER_FILE_EXT}"):
            with open(recover_file, "rt") as json_file:
                loaded.append(ConversionBatch.from_dict(**json.load(json_file)))

        if len(loaded) == 0:
            return None
        else:
            return loaded

    @property
    def batch_id(self) -> str:
        return self.__batch_id

    @property
    def org(self) -> str:
        return self.__org

    @property
    def size(self) -> int:
        return len(self.__disconnect_projects)

    @property
    def disconnect_projects(self) -> List[str]:
        return self.__disconnect_projects

    @property
    def batch_projects(self) -> List[str]:
        return list(self.__project_id_to_name_map.keys())

    def get_project_id(self, project_name: str) -> str | None:
        return self.__project_id_to_name_map.get(project_name)

    def as_api_payload(self):
        return {
            "projects": list(self.__project_convert_data.values()),
            "scmType": self.__scm_type,
            "scmOnPremUrl": self.__scm_url,
            "orgIdentity": self.__org,
        }

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

            if project_id in self.__project_id_to_name_map.keys():
                del self.__project_id_to_name_map[project_id]

            if project_id in self.__project_convert_data.keys():
                del self.__project_convert_data[project_id]

            if project_id in self.__enable_sast_incremental_projects:
                self.__enable_sast_incremental_projects.remove(project_id)

            if self.__recovery_mode:
                await self.__update_recover_file()
                if len(self.__project_convert_data) == 0:
                    self.__recovery_mode = False
                    await self.__remove_recover_file()

    async def add(self, repo_cfg: ProjectRepoConfig):
        async with self.__state_lock:
            self.__disconnect_projects.append(repo_cfg.id)
            self.__project_id_to_name_map[repo_cfg.name] = repo_cfg.id

            if await repo_cfg.sast_incremental_enabled:
                self.__enable_sast_incremental_projects.append(repo_cfg.id)

            self.__project_convert_data[repo_cfg.id] = {
                "cxProjectId": repo_cfg.id,
                "scmRepositoryUrl": await repo_cfg.repo_url,
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
