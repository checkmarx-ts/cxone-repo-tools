from .abstract_filtering_converter import AbstractFilteringBatchConverter
from cxone_api.high.projects import ProjectRepoConfig


class NameFilterConverter(AbstractFilteringBatchConverter):
    async def _include_in_batch(self, repo_cfg: ProjectRepoConfig) -> bool:
        return self.matches(repo_cfg.name)
