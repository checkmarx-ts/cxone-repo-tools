from .conversion_mapper import ConversionMapper


class DefaultConversionMapper(ConversionMapper):
    """A conversion mapper that assumes the target SCM organizes repositories
    the same way as the source SCM: the source base URL is replaced by the
    target base URL, the organization path segment that follows the base URL
    is replaced by the target organization, and the rest of the path is kept
    unchanged.  The project name is not changed.

    For example, with a source base URL of ``https://github.com`` and a
    target base URL of ``https://github.example.com``,
    ``https://github.com/acme/widgets`` in organization ``acme`` maps to
    ``https://github.example.com/new-org/widgets`` in organization
    ``new-org``.
    """

    def _map_repo_path(self, path: str) -> str:
        """Returns the path that follows the source organization unchanged.

        :param path: The relative POSIX path that follows the source
                     organization, for example ``sub/group/repo.git``.  It is
                     ``.`` when the source URL ends at the organization.
        :type path: str

        :return: `path`, unchanged.
        :rtype: str
        """
        return path

    def _map_project_name(self, path: str) -> str | None:
        """Returns None, because the default mapping does not change the
        project name.

        :param path: The relative POSIX path that follows the source
                     organization.
        :type path: str

        :return: None.
        :rtype: str | None
        """
        return None
