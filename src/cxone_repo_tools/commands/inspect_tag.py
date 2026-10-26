from docopt import docopt
from typing import List
from cxone_api.high.sca.registry import (
    PackageRepositoryConfiguration,
    PackageRepositoryConfigurationTag,
)
from .inspect_base import AbstractInspectCommand
from ..convert import AbortedConversionException, InvalidRepositoryConfiguration


class InspectTagCommand(AbstractInspectCommand):
    # fmt: off
    """Usage:
      cxone-repo-tools inspect-tag (-h | --help | --version)
      cxone-repo-tools inspect-tag (--tag-id TAGID | --tag-name TAGNAME) [--out EXPORT_FILE]

    Show the SCA private package repository configurations associated with a
    configuration tag.

    --tag-id TAGID                The ID of the tag to inspect.

    --tag-name TAGNAME            The name of the tag to inspect.  Tag names are not
                                  unique; every tag with the name is inspected.

    --out EXPORT_FILE             The name of the output file.  Output is written to
                                  stdout if not provided.
    """
    # fmt: on

    CMD_NAME = "inspect-tag"

    _DUPLICATE_SUBJECT = "the tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            InspectTagCommand.__doc__,
            [InspectTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        if parsed_args["--tag-id"] is not None:
            tags = [
                await PackageRepositoryConfigurationTag.retrieve_by_id(
                    self.client, parsed_args["--tag-id"]
                )
            ]
        else:
            tags = await PackageRepositoryConfigurationTag.retrieve_by_name(
                self.client, parsed_args["--tag-name"]
            )

        if len(tags) > 1:
            raise InvalidRepositoryConfiguration.ambiguous_tag_name(
                parsed_args["--tag-name"], [tag.tagid for tag in tags]
            )

        if len(tags) == 0:
            text = f"No tag found with name: {parsed_args['--tag-name']}\n"
        else:
            sections = []
            for tag in tags:
                configs = (
                    await PackageRepositoryConfiguration.retrieve_tag_configurations(
                        self.client, tag
                    )
                )
                sections.append(
                    self._format_configurations(
                        f"Configurations associated with tag: {tag.name} ({tag.tagid})",
                        configs,
                    )
                )
            text = "\n".join(sections)

        await self._write_output(text, parsed_args["--out"])

    @staticmethod
    def print_help():
        print(InspectTagCommand.__doc__)
