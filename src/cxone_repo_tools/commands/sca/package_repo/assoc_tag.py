import logging
from docopt import docopt
from typing import List
from cxone_api.high.sca.registry import (
    PackageRepositoryConfigurationTag,
    ProjectPrivateRepoTagAssignment,
)
from cxone_api.high.sca.registry.exceptions import DuplicatePackageManagerException
from cxone_api.high.exceptions import NameNotFoundException
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import (
    AbortedConversionException,
    InvalidRepositoryConfiguration,
)

_log = logging.getLogger(__name__)


class AssocTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools assoc-tag (-h | --help | --version)
      cxone-repo-tools assoc-tag --tag-id TAGID
                  (--project-name-match REGEX | --project-tag KEY | --project-group PATH)

    Associate the SCA private package repository configurations in a tag with the
    selected projects.  Projects that already have a configuration of the same package
    manager type are skipped and reported.  Exactly one project filter is required.

    --tag-id TAGID                The ID of the tag whose configurations are associated.

    --project-name-match REGEX    Select projects with names matching the regular
                                  expression.

    --project-tag KEY             Select projects that have a project tag with the key.

    --project-group PATH          Select projects assigned to the group with the full
                                  path (e.g. /parent/child).
    """
    # fmt: on

    CMD_NAME = "assoc-tag"

    async def execute(self, cmdline_args: List[str]):
        parsed_args = docopt(
            AssocTagCommand.__doc__,
            [AssocTagCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        tag = await PackageRepositoryConfigurationTag.retrieve_by_id(
            self.client, parsed_args["--tag-id"]
        )

        if len(tag.associated_configs) == 0:
            raise InvalidRepositoryConfiguration.empty_tag(tag.name, tag.tagid)

        if parsed_args["--project-tag"] is not None:
            assignment = ProjectPrivateRepoTagAssignment.by_project_tag(
                self.client, parsed_args["--project-tag"], tag
            )
        elif parsed_args["--project-group"] is not None:
            assignment = ProjectPrivateRepoTagAssignment.by_group_path(
                self.client, parsed_args["--project-group"], tag
            )
        else:
            assignment = ProjectPrivateRepoTagAssignment.by_project_name_match(
                self.client, parsed_args["--project-name-match"], tag
            )

        try:
            results = await assignment.execute_assignment(
                concurrent_threads=self.threads
            )
        except DuplicatePackageManagerException as ex:
            raise InvalidRepositoryConfiguration(str(ex))
        except NameNotFoundException:
            raise InvalidRepositoryConfiguration(
                f"No group found with path: {parsed_args['--project-group']}"
            )

        for assignee in results.assignees:
            _log.info(
                f"Assigned tag {tag.name} ({tag.tagid}) configurations to project "
                f"{assignee.projectName} ({assignee.projectId})."
            )

        for ex in results.exceptions:
            _log.warning(f"Project skipped: {ex}")

        _log.info(
            f"Tag {tag.name} ({tag.tagid}): {len(results.assignees)} projects assigned, "
            f"{len(results.exceptions)} projects skipped, "
            f"{'success' if results.assignment_success else 'FAILED'}."
        )

        if not results.assignment_success:
            raise InvalidRepositoryConfiguration(
                f"Assignment of tag {tag.name} ({tag.tagid}) configurations failed "
                "for one or more projects."
            )

    @staticmethod
    def print_help():
        print(AssocTagCommand.__doc__)
