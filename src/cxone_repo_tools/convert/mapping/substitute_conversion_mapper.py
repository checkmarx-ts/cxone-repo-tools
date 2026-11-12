from .conversion_mapper import ConversionMapper
from .string_by_regex import StringByRegex


class SubstituteConversionMapper(ConversionMapper):
    """A conversion mapper that builds the path following the target
    organization, and optionally the project name, by applying a regex
    extraction and substitution specifications to the path following the
    source organization.

    The base URL and organization are mapped by
    `ConversionMapper.convert_repo_url`.  The path following the source
    organization, for example ``sub/group/repo.git``, is the input string of a
    `StringByRegex`, and its output is the path following the target
    organization.  When the source URL ends at the organization, the input
    string is ``.``.  When a project substitution specification is given, a
    second `StringByRegex` with the same regex builds the project name from
    the same input string.

    :param regex: The regular expression evaluated against the path following
                  the source organization.  It defines the field extractions
                  as named groups, for example ``(?P<repo>[^/]+)``.
    :type regex: str

    :param repo_substitution: The specification of the path following the
                              target organization.  Static text is copied
                              as-is, and dynamic elements reference the
                              regex's extracted values by name, for example
                              ``{repo}``.
    :type repo_substitution: str

    :param project_substitution: The specification of the project name after
                                 conversion, in the same form as
                                 `repo_substitution`, or None to leave the
                                 project name unchanged.
    :type project_substitution: str | None
    """

    def __init__(
        self,
        regex: str,
        repo_substitution: str,
        project_substitution: str | None,
    ):
        """Initializes the mapper and its internal `StringByRegex` instances.

        :param regex: The regular expression evaluated against the path
                      following the source organization.
        :type regex: str

        :param repo_substitution: The specification of the path following the
                                  target organization.
        :type repo_substitution: str

        :param project_substitution: The specification of the project name
                                     after conversion, or None to leave the
                                     project name unchanged.
        :type project_substitution: str | None

        :raises re.error: `regex` is not a valid regular expression.
        :raises ValueError: `repo_substitution` or `project_substitution` is
                            not a valid format string.
        """
        super().__init__()
        self.__path_converter = StringByRegex(regex, repo_substitution)
        self.__project_converter = (
            StringByRegex(regex, project_substitution)
            if project_substitution is not None
            else None
        )

    def _map_repo_path(self, path: str) -> str:
        """Maps the path following the source organization with the internal
        `StringByRegex`.

        :param path: The relative POSIX path following the source
                     organization.
        :type path: str

        :return: The relative POSIX path following the target organization.
        :rtype: str

        :raises MappingException: The path does not yield every extracted
                                  value the substitution specification
                                  references.
        """
        return self.__path_converter.convert(path)

    def _map_project_name(self, path: str) -> str | None:
        """Maps the path following the source organization to the project
        name with the project `StringByRegex`.

        :param path: The relative POSIX path following the source
                     organization.
        :type path: str

        :return: The project name after conversion, or None if no project
                 substitution specification was given.
        :rtype: str | None

        :raises MappingException: The path does not yield every extracted
                                  value the project substitution
                                  specification references.
        """
        if self.__project_converter is None:
            return None

        return self.__project_converter.convert(path)
