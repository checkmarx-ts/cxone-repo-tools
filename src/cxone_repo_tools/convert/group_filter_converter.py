from .abstract_filtering_converter import AbstractFilteringBatchConverter
from cxone_api.high.projects import ProjectRepoConfig
from cxone_api.high.access_mgmt.user_mgmt import Groups


class GroupFilterConverter(AbstractFilteringBatchConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__groups = Groups(self._client)

    async def _include_in_batch(self, repo_cfg: ProjectRepoConfig) -> bool:
        return True
