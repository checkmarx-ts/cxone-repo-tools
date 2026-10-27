import logging
from docopt import docopt
from typing import List
from cxone_api.high.sca.registry import (
    PackageRepositoryConfiguration,
    ProjectPrivateRepoTagAssignment,
)
from cxone_api.high.sca.registry.exceptions import DuplicatePackageManagerException
from cxone_api.high.exceptions import NameNotFoundException
from cxone_repo_tools.commands.base import Command
from cxone_repo_tools.convert import (
    AbortedConversionException,
    InvalidRepositoryConfiguration,
)
from .util import (
    resolve_tag,
    collect_project_exclusions,
    add_project_sca_exclusions,
)

_log = logging.getLogger(__name__)


class AssocTagCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools assoc-tag (-h | --help | --version)
      cxone-repo-tools assoc-tag (--tag-id TAGID | --tag-name TAGNAME)
                  (--project-name-match REGEX | --project-tag KEY | --project-group PATH)
                  [--skip-settings-update]

    Associate the SCA private package repository configurations in a tag with the
    selected projects.  Projects that already have a configuration of the same package
    manager type are skipped and reported.  Exactly one project filter is required.

    --tag-id TAGID                The ID of the tag whose configurations are associated.

    --tag-name TAGNAME            The name of the tag whose configurations are associated.
                                  Tag names are not unique; if no tag or more than one tag
                                  has the name, the command fails.

    --project-name-match REGEX    Select projects with names matching the regular
                                  expression.

    --project-tag KEY             Select projects that have a project tag with the key.

    --project-group PATH          Select projects assigned to the group with the full
                                  path (e.g. /parent/child).

    --skip-settings-update        Do not update project settings after the tag's
                                  configurations are associated with the projects.
                                  By default, the SCA file exclusions of every project
                                  associated with the tag's configurations are updated
                                  to exclude each package manager's configuration file
                                  so a file in the repository cannot override the
                                  deployed configuration.
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

        skip_settings_update = bool(parsed_args["--skip-settings-update"])

        tag = await resolve_tag(
            self.client, parsed_args["--tag-id"], parsed_args["--tag-name"]
        )

        if tag is None:
            raise InvalidRepositoryConfiguration.tag_not_found(
                parsed_args["--tag-name"]
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

        configs = await PackageRepositoryConfiguration.retrieve_tag_configurations(
            self.client, tag
        )

        if skip_settings_update:
            files = ", ".join(cfg.packageManager.config_file_name for cfg in configs)
            _log.warning(
                "Project settings were not updated. A package manager configuration "
                f"file in a project's repository ({files}) will override the deployed "
                "configuration if the file exists."
            )
            return

        await add_project_sca_exclusions(
            self.client, await collect_project_exclusions(configs), self.threads
        )

    @staticmethod
    def print_help():
        print(AssocTagCommand.__doc__)
