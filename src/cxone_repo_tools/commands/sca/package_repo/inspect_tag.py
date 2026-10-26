from docopt import docopt
from typing import List
from cxone_api.high.sca.registry import PackageRepositoryConfiguration
from ...base import AbstractInspectCommand
from .util import resolve_tag
from ....convert import AbortedConversionException


class InspectTagCommand(AbstractInspectCommand):
    # fmt: off
    """Usage:
      cxone-repo-tools inspect-tag (-h | --help | --version)
      cxone-repo-tools inspect-tag (--tag-id TAGID | --tag-name TAGNAME) [--out EXPORT_FILE]

    Show the SCA private package repository configurations associated with a
    configuration tag.

    --tag-id TAGID                The ID of the tag to inspect.

    --tag-name TAGNAME            The name of the tag to inspect.  Tag names are not
                                  unique; if more than one tag has the name, the
                                  command fails and lists the matching tag ids.

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

        tag = await resolve_tag(
            self.client, parsed_args["--tag-id"], parsed_args["--tag-name"]
        )

        if tag is None:
            text = f"No tag found with name: {parsed_args['--tag-name']}\n"
        else:
            configs = await PackageRepositoryConfiguration.retrieve_tag_configurations(
                self.client, tag
            )
            text = self._format_configurations(
                f"Configurations associated with tag: {tag.name} ({tag.tagid})",
                configs,
            )

        await self._write_output(text, parsed_args["--out"])

    @staticmethod
    def print_help():
        print(InspectTagCommand.__doc__)
