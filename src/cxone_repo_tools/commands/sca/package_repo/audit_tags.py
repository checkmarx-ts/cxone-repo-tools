import aiofiles, aiocsv, csv
from docopt import docopt
from tqdm.asyncio import tqdm
from typing import List
from cxone_api.util import page_generator
from cxone_api.low.sca.registry.tags import retrieve_list_of_configurations_by_tag
from cxone_api.high.sca.registry import PackageRepositoryConfigurationTag
from cxone_repo_tools.commands.base import Command
from .util import PACKAGE_MANAGERS
from cxone_repo_tools.convert import AbortedConversionException


class AuditTagsCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools audit-tags (-h | --help | --version)
      cxone-repo-tools audit-tags [--out EXPORT_FILE]

    Produce a summary CSV showing the number of SCA private package repository
    configurations of each package manager type associated with each configuration tag.

    --out EXPORT_FILE             The name of the CSV export file. [default: ./tag_audit.csv]
    """
    # fmt: on

    CMD_NAME = "audit-tags"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            AuditTagsCommand.__doc__,
            [AuditTagsCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        package_managers = [pm.value for pm in PACKAGE_MANAGERS]

        async with aiofiles.open(
            parsed_args["--out"], "wt", encoding="UTF-8"
        ) as csv_out:
            writer = aiocsv.AsyncDictWriter(
                csv_out,
                quoting=csv.QUOTE_ALL,
                fieldnames=["tag_name", "tag_id"] + package_managers,
            )
            await writer.writeheader()

            async for tag_json in tqdm(
                page_generator(
                    retrieve_list_of_configurations_by_tag,
                    offset_param="PageNumber",
                    offset_init_value=1,
                    offset_is_by_count=False,
                    client=self.client,
                    PageSize=50,
                ),
                desc="Inspecting tags",
            ):
                tag = PackageRepositoryConfigurationTag.from_tag_json(
                    self.client, tag_json
                )

                counts = {pm: 0 for pm in package_managers}
                for cfg in tag.associated_configs:
                    counts[cfg.packageManager.value] += 1

                await writer.writerow(
                    {"tag_name": tag.name, "tag_id": tag.tagid} | counts
                )

    @staticmethod
    def print_help():
        print(AuditTagsCommand.__doc__)
