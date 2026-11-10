from .conversion_mapper import ConversionMapper
from .string_by_regex import StringByRegex


class SubstituteConversionMapper(ConversionMapper):
    """A conversion mapper that builds the path following the target
    organization by applying a regex extraction and a substitution
    specification to the path following the source organization.

    The base URL and organization are mapped by `ConversionMapper.convert`.
    The path following the source organization, for example
    ``sub/group/repo.git``, is the input string of a `StringByRegex`, and its
    output is the path following the target organization.  When the source
    URL ends at the organization, the input string is ``.``.

    :param regex: The regular expression evaluated against the path following
                  the source organization.  It defines the field extractions
                  as named groups, for example ``(?P<repo>[^/]+)``.
    :type regex: str

    :param substitution: The specification of the path following the target
                         organization.  Static text is copied as-is, and
                         dynamic elements reference the regex's extracted
                         values by name, for example ``{repo}``.
    :type substitution: str
    """

    def __init__(self, regex: str, substitution: str):
        """Initializes the mapper and its internal `StringByRegex`.

        :param regex: The regular expression evaluated against the path
                      following the source organization.
        :type regex: str

        :param substitution: The specification of the path following the
                             target organization.
        :type substitution: str

        :raises re.error: `regex` is not a valid regular expression.
        :raises ValueError: `substitution` is not a valid format string.
        """
        super().__init__()
        self.__path_converter = StringByRegex(regex, substitution)

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
