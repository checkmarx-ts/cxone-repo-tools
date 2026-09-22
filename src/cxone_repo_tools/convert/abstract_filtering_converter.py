import re
from .batch_converter import BatchConverter
from cxone_api.high.projects import ProjectRepoConfig


class AbstractFilteringBatchConverter(BatchConverter):

    def __init__(self, regex: str, ignore_case: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__regex = re.compile(regex, re.IGNORECASE if ignore_case else re.NOFLAG)

    def matches(self, string: str) -> bool:
        return self.__regex.search(string)

    async def _include_in_batch(self, repo_cfg: ProjectRepoConfig) -> bool:
        raise NotImplementedError("_include_in_batch")
