from __future__ import annotations
from typing import List
from cxone_repo_tools.consts import DISCO_API_FLAG


class ConversionException(Exception):

    @staticmethod
    def conversion_request_failed(status_code: int | None) -> ConversionException:
        """Creates the exception raised when the project conversion API request
        fails after all retries.

        :param status_code: The HTTP status of the last response, or None if no
                            response was received.
        :type status_code: int | None

        :rtype: ConversionException
        """
        return ConversionException(
            "The project conversion request failed "
            f"(HTTP status {status_code if status_code is not None else 'none'})."
        )

    @staticmethod
    def connection_failed(project_id: str, scm_id: int) -> ConversionException:
        """Creates the exception raised when a project could not be connected
        to an SCM.

        :param project_id: The ID of the project.
        :type project_id: str

        :param scm_id: The ID of the SCM.
        :type scm_id: int

        :rtype: ConversionException
        """
        return ConversionException(
            f"Project {project_id} was not connected to SCM {scm_id}."
        )

    @staticmethod
    def target_scm_not_found(scm_id: int) -> ConversionException:
        return ConversionException(f"Target SCM ID {scm_id} not found")

    @staticmethod
    def source_scms_not_found(scm_ids: List[int]) -> ConversionException:
        return ConversionException(f"Source SCM IDs {scm_ids} not found")

    @staticmethod
    def disconnect_api_ff_not_enabled():
        return ConversionException(
            f"Feature flag {DISCO_API_FLAG} is not enabled on this tenant."
        )

    @staticmethod
    def failure_enable_sast_incrementals(project_name: str):
        return ConversionException(
            f"Failed to enable SAST incremental scans for project {project_name}"
        )

    @staticmethod
    def project_already_assigned(
        project_id: str, project_name: str, assigned_scm_id: str
    ):
        return ConversionException(
            f"Project {project_name} ({project_id}) is already assigned to scm {assigned_scm_id}"
        )

    @staticmethod
    def project_not_connected_to_scms(
        project_id: str, project_name: str, source_ids: List[str]
    ):
        return ConversionException(
            f"Project {project_name} ({project_id}) is not connected to scms {','.join(source_ids)}"
        )

    @staticmethod
    def rename_failed(project_id: str, project_target_name: str):
        return ConversionException(
            f"Attempt to rename project {project_id} to {project_target_name} failed."
        )

    @staticmethod
    def disconnect_failed(project_id: str):
        return ConversionException(
            f"Failed to disconnect project {project_id} from an SCM."
        )


class AbortedConversionException(Exception):

    @staticmethod
    def no_client() -> AbortedConversionException:
        return AbortedConversionException(
            "Checkmarx One connection parameters were not provided."
        )

    @staticmethod
    def missing_secret_env(env_var: str, label: str) -> AbortedConversionException:
        return AbortedConversionException(
            f"{label} was not found in environment variable {env_var}."
        )

    @staticmethod
    def empty_secret(label: str) -> AbortedConversionException:
        return AbortedConversionException(f"{label} was provided but is empty.")


class InvalidRepositoryConfiguration(Exception):

    @staticmethod
    def ambiguous_tag_name(
        tag_name: str, tag_ids: List[str]
    ) -> InvalidRepositoryConfiguration:
        found = "\n".join(f"  {tag_name} ({tag_id})" for tag_id in tag_ids)
        return InvalidRepositoryConfiguration(
            f"More than one tag is named {tag_name}:\n{found}\n"
            "Use --tag-id to specify the intended tag."
        )

    @staticmethod
    def tag_not_found(tag_name: str) -> InvalidRepositoryConfiguration:
        return InvalidRepositoryConfiguration(f"No tag found with name: {tag_name}")

    @staticmethod
    def tag_name_exists(
        tag_name: str, tag_ids: List[str]
    ) -> InvalidRepositoryConfiguration:
        found = "\n".join(f"  {tag_name} ({tag_id})" for tag_id in tag_ids)
        return InvalidRepositoryConfiguration(
            f"A tag named {tag_name} already exists:\n{found}\n"
            "Choose a tag name that is not in use."
        )

    @staticmethod
    def empty_tag(tag_name: str, tag_id: str) -> InvalidRepositoryConfiguration:
        return InvalidRepositoryConfiguration(
            f"Tag {tag_name} ({tag_id}) has no configurations to associate."
        )

    @staticmethod
    def config_not_retrieved(
        config_id: str, reason: str
    ) -> InvalidRepositoryConfiguration:
        """Creates the exception raised when a configuration cannot be
        retrieved, for example because no configuration has the ID.

        :param config_id: The ID of the configuration.
        :type config_id: str

        :param reason: The reason the retrieval failed.
        :type reason: str

        :rtype: InvalidRepositoryConfiguration
        """
        return InvalidRepositoryConfiguration(
            f"Configuration {config_id} could not be retrieved: {reason}"
        )

    @staticmethod
    def no_package_manager_configs() -> InvalidRepositoryConfiguration:
        return InvalidRepositoryConfiguration(
            "At least one package manager configuration file must be provided."
        )

    @staticmethod
    def duplicate_type_in_tag(
        tag_name: str, tag_id: str, package_manager: str, config_ids: List[str]
    ) -> InvalidRepositoryConfiguration:
        return InvalidRepositoryConfiguration(
            f"Tag {tag_name} ({tag_id}) has more than one {package_manager} "
            f"configuration: {', '.join(config_ids)}. Resolve the duplicate before "
            "updating the tag."
        )


class MappingException(Exception):
    """Raised when a value cannot be mapped during a conversion."""

    @staticmethod
    def missing_extracted_values(
        input_string: str, missing: List[str]
    ) -> MappingException:
        """Creates the exception raised when an input string does not yield
        every extracted value that a substitution specification references.

        :param input_string: The input string the regex was evaluated against.
        :type input_string: str

        :param missing: The names of the referenced values that were not
                        extracted.
        :type missing: List[str]

        :rtype: MappingException
        """
        return MappingException(
            f"Input [{input_string}] did not yield the extracted values: "
            f"{', '.join(missing)}"
        )

    @staticmethod
    def url_not_under_base(url: str, base_url: str) -> MappingException:
        """Creates the exception raised when a repository URL is not under the
        expected base URL.

        :param url: The repository URL.
        :type url: str

        :param base_url: The base URL the repository URL was expected to be
                         under.
        :type base_url: str

        :rtype: MappingException
        """
        return MappingException(
            f"Repository URL [{url}] is not under base URL [{base_url}]"
        )

    @staticmethod
    def org_not_in_url(url: str, org: str) -> MappingException:
        """Creates the exception raised when the path segment after the base
        URL of a repository URL is not the expected organization.

        :param url: The repository URL.
        :type url: str

        :param org: The organization expected after the base URL.
        :type org: str

        :rtype: MappingException
        """
        return MappingException(
            f"Repository URL [{url}] is not in organization [{org}]"
        )
