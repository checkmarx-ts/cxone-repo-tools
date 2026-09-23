from .abstract_filtering_converter import AbstractFilteringBatchConverter
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.high.access_mgmt.user_mgmt import Groups


class GroupFilterConverter(AbstractFilteringBatchConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__groups = Groups(self._client)

    async def _include_in_batch(self, repo_cfg: ProjectRepoConfig) -> bool:
        for gid in repo_cfg.groups:
            if self.matches(str((await self.__groups.get_by_id(gid)).path)):
                return True

        return False
