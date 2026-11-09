import logging
from docopt import docopt
from typing import List
from cxone_api.exceptions import ResponseException
from cxone_api.high.sca.registry import PackageRepositoryConfiguration
from cxone_repo_tools.commands.base import Command
from .util import collect_project_exclusions, remove_project_sca_exclusions
from cxone_repo_tools.exceptions import (
    AbortedConversionException,
    InvalidRepositoryConfiguration,
)

_log = logging.getLogger(__name__)


class DeleteConfigCommand(Command):
    # fmt: off
    """Usage:
      cxone-repo-tools delete-config --config-id CONFIGID
                  [(--confirm [--skip-settings-update])]

    Delete a single SCA private package repository configuration.  The configuration's
    associations with projects and tags are removed automatically when it is deleted;
    they do not need to be removed first.  A tag that contained the configuration no
    longer has a configuration for its package manager type.

    Without --confirm, the configuration and the tags and projects it is associated with
    are only listed.  With --confirm, the SCA file exclusion for the configuration file is
    removed from every project associated with the configuration, and then the
    configuration is deleted.

    --config-id CONFIGID          The ID of the configuration to delete.

    --confirm                     Delete the configuration.  Without this flag nothing
                                  is deleted.

    --skip-settings-update        Do not remove the configuration file exclusion from
                                  the SCA file exclusions of the associated projects.
    """
    # fmt: on

    CMD_NAME = "delete-config"

    async def execute(self, cmdline_args: List[str]):
        """Lists, or with --confirm deletes, the configuration named by
        --config-id.

        :param cmdline_args: The command's arguments, without the command name.
        :type cmdline_args: List[str]

        :raises AbortedConversionException: No Checkmarx One connection
                                            parameters were provided.
        :raises InvalidRepositoryConfiguration: The configuration could not be
                                                retrieved.
        """
        parsed_args = docopt(
            DeleteConfigCommand.__doc__,
            [DeleteConfigCommand.CMD_NAME] + cmdline_args,
            version=self.version,
        )

        if self.client is None:
            raise AbortedConversionException.no_client()

        config_id = parsed_args["--config-id"]

        # cxone-async-api exceptions derive from BaseException, so __main__
        # would not report this one cleanly.
        try:
            cfg = await PackageRepositoryConfiguration.retrieve_by_configid(
                self.client, config_id
            )
        except ResponseException as ex:
            raise InvalidRepositoryConfiguration.config_not_retrieved(
                config_id, str(ex)
            ) from ex

        # Also refreshes the configuration's project and tag associations.
        project_exclusions = await collect_project_exclusions([cfg])

        if not parsed_args["--confirm"]:
            print("Configuration that would be deleted (use --confirm to delete):")
            print(f"  {cfg.name} ({cfg.configId}) [{cfg.packageManager.value}]")
            print("Tags the configuration would be removed from:")
            for tag in cfg.associated_tags:
                print(f"  {tag.name} ({tag.tagid})")
            if len(cfg.associated_tags) == 0:
                print("  NONE")
            print(
                "Projects the configuration would be removed from: "
                f"{len(cfg.associated_projects)}"
            )
            return

        if parsed_args["--skip-settings-update"]:
            _log.warning(
                "Project settings were not updated. The SCA exclusion for "
                f"{cfg.packageManager.config_file_name} remains in "
                f"{len(project_exclusions)} projects and will continue to exclude "
                "that file from SCA scans."
            )
        else:
            await remove_project_sca_exclusions(
                self.client, project_exclusions, self.threads
            )

        if await cfg.delete():
            _log.info(f"Deleted configuration {cfg.name} ({cfg.configId}).")
        else:
            _log.error(f"Failed to delete configuration {cfg.name} ({cfg.configId}).")

    @staticmethod
    def print_help():
        """Prints the command's help."""
        print(DeleteConfigCommand.__doc__)
