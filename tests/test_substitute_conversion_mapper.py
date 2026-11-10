import re
import unittest
from cxone_repo_tools.convert.mapping import (
    ConversionMapper,
    SubstituteConversionMapper,
)
from cxone_repo_tools.exceptions import MappingException


def convert(mapper, source_url):
    return mapper.convert(
        "https://github.com", source_url, "acme", "https://ghe.example.com", "new-org"
    )


class SubstituteConversionMapperTestCase(unittest.TestCase):

    def test_is_a_conversion_mapper(self):
        self.assertIsInstance(
            SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}"),
            ConversionMapper,
        )

    def test_substitutes_path_after_org(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<repo>[^/]+?)(\.git)?$", "{repo}-migrated"
        )
        self.assertEqual(
            convert(mapper, "https://github.com/acme/widgets.git"),
            "https://ghe.example.com/new-org/widgets-migrated",
        )

    def test_substitution_can_restructure_path(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<group>[^/]+)/(?P<repo>[^/]+)$", "{group}-{repo}"
        )
        self.assertEqual(
            convert(mapper, "https://github.com/acme/platform/widgets"),
            "https://ghe.example.com/new-org/platform-widgets",
        )

    def test_substitution_can_add_path_segments(self):
        mapper = SubstituteConversionMapper(r"^(?P<repo>[^/]+)$", "migrated/{repo}")
        self.assertEqual(
            convert(mapper, "https://github.com/acme/widgets"),
            "https://ghe.example.com/new-org/migrated/widgets",
        )

    def test_regex_receives_only_path_after_org(self):
        mapper = SubstituteConversionMapper(r"^(?P<all>.*)$", "{all}")
        self.assertEqual(
            convert(mapper, "https://github.com/acme/sub/group/repo"),
            "https://ghe.example.com/new-org/sub/group/repo",
        )

    def test_path_not_matching_regex_raises(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<group>[^/]+)/(?P<repo>[^/]+)$", "{repo}"
        )
        with self.assertRaises(MappingException):
            convert(mapper, "https://github.com/acme/widgets")

    def test_url_ending_at_org_gives_dot_path(self):
        mapper = SubstituteConversionMapper(r"^(?P<repo>[^/]+)$", "{repo}")
        self.assertEqual(
            convert(mapper, "https://github.com/acme"),
            "https://ghe.example.com/new-org",
        )

    def test_base_url_and_org_still_validated(self):
        mapper = SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}")
        with self.assertRaises(MappingException):
            convert(mapper, "https://gitlab.com/acme/widgets")
        with self.assertRaises(MappingException):
            convert(mapper, "https://github.com/other/widgets")

    def test_invalid_regex_raises_on_init(self):
        with self.assertRaises(re.error):
            SubstituteConversionMapper(r"(?P<repo>", "{repo}")

    def test_invalid_substitution_raises_on_init(self):
        with self.assertRaises(ValueError):
            SubstituteConversionMapper(r"(?P<repo>.+)", "{repo")


if __name__ == "__main__":
    unittest.main()
