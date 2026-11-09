import re
from string import Formatter
from typing import List
from cxone_repo_tools.exceptions import MappingException


class StringByRegex:
    """Builds an output string from the values a regular expression extracts
    from an input string.

    The regular expression is searched for in the input string, so it matches
    anywhere unless it is anchored with ``^`` and ``$``.  The substitution
    specification is a Python format string: static text is copied as-is,
    ``{name}`` is replaced by the value extracted by the named group ``name``,
    and ``{{`` and ``}}`` produce literal braces.

    :param regex: The regular expression evaluated against the input string.
                  It defines the field extractions as named groups, for
                  example ``(?P<org>[^/]+)``.
    :type regex: str

    :param substitution: The specification of the output string.  Static text
                         is copied as-is, and dynamic elements reference the
                         regex's extracted values by name, for example
                         ``{org}``.
    :type substitution: str
    """

    def __init__(self, regex: str, substitution: str):
        """Initializes the converter, compiling the regex and finding the
        extracted values the substitution specification references.

        :param regex: The regular expression evaluated against the input
                      string.  It defines the field extractions as named
                      groups.
        :type regex: str

        :param substitution: The specification of the output string, built
                             from static text and dynamic elements that
                             reference the regex's extracted values by name.
        :type substitution: str

        :raises re.error: `regex` is not a valid regular expression.
        :raises ValueError: `substitution` is not a valid format string, for
                            example because a brace is not closed.
        """
        self.__pattern = re.compile(regex)
        self.__substitution = substitution
        self.__referenced = StringByRegex.__referenced_names(substitution)

    @staticmethod
    def __referenced_names(substitution: str) -> List[str]:
        """Finds the names of the extracted values a substitution
        specification references.

        :param substitution: The substitution specification.
        :type substitution: str

        :return: The referenced names, without duplicates, in the order they
                 first appear.
        :rtype: List[str]

        :raises ValueError: `substitution` is not a valid format string.
        """
        names = [
            field_name
            for _, field_name, _, _ in Formatter().parse(substitution)
            if field_name is not None
        ]
        return list(dict.fromkeys(names))

    def convert(self, input_string: str) -> str:
        """Builds the output string from the values the regex extracts from
        the input string.

        :param input_string: The string the regex is evaluated against.
        :type input_string: str

        :return: The substitution specification with each dynamic element
                 replaced by the extracted value it references.
        :rtype: str

        :raises MappingException: The input string does not yield every
                                  extracted value the substitution
                                  specification references, either because
                                  the regex does not match or because a
                                  referenced group did not participate in the
                                  match.
        """
        match = self.__pattern.search(input_string)
        extracted = {
            name: value
            for name, value in (match.groupdict() if match else {}).items()
            if value is not None
        }

        missing = [name for name in self.__referenced if name not in extracted]
        if len(missing) > 0:
            raise MappingException.missing_extracted_values(input_string, missing)

        return self.__substitution.format_map(extracted)
