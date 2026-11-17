import re
import unittest
from cxone_repo_tools.convert.mapping import (
    ConversionMapper,
    SubstituteConversionMapper,
)
from cxone_repo_tools.exceptions import MappingException


def convert(mapper, source_url):
    return mapper.convert_repo_url(
        "https://github.com", source_url, "acme", "https://ghe.example.com", "new-org"
    )


class SubstituteConversionMapperTestCase(unittest.TestCase):

    def test_is_a_conversion_mapper(self):
        self.assertIsInstance(
            SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}", None),
            ConversionMapper,
        )

    def test_substitutes_path_after_org(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<repo>[^/]+?)(\.git)?$", "{repo}-migrated", None
        )
        self.assertEqual(
            convert(mapper, "https://github.com/acme/widgets.git"),
            "https://ghe.example.com/new-org/widgets-migrated",
        )

    def test_substitution_can_restructure_path(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<group>[^/]+)/(?P<repo>[^/]+)$", "{group}-{repo}", None
        )
        self.assertEqual(
            convert(mapper, "https://github.com/acme/platform/widgets"),
            "https://ghe.example.com/new-org/platform-widgets",
        )

    def test_substitution_can_add_path_segments(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<repo>[^/]+)$", "migrated/{repo}", None
        )
        self.assertEqual(
            convert(mapper, "https://github.com/acme/widgets"),
            "https://ghe.example.com/new-org/migrated/widgets",
        )

    def test_regex_receives_only_path_after_org(self):
        mapper = SubstituteConversionMapper(r"^(?P<all>.*)$", "{all}", None)
        self.assertEqual(
            convert(mapper, "https://github.com/acme/sub/group/repo"),
            "https://ghe.example.com/new-org/sub/group/repo",
        )

    def test_path_not_matching_regex_raises(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<group>[^/]+)/(?P<repo>[^/]+)$", "{repo}", None
        )
        with self.assertRaises(MappingException):
            convert(mapper, "https://github.com/acme/widgets")

    def test_url_ending_at_org_gives_dot_path(self):
        mapper = SubstituteConversionMapper(r"^(?P<repo>[^/]+)$", "{repo}", None)
        self.assertEqual(
            convert(mapper, "https://github.com/acme"),
            "https://ghe.example.com/new-org",
        )

    def test_org_still_validated(self):
        mapper = SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}", None)
        with self.assertRaises(MappingException):
            convert(mapper, "https://github.com/other/widgets")

    def test_base_url_not_checked(self):
        mapper = SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}", None)
        self.assertEqual(
            convert(mapper, "https://gitlab.com/acme/widgets"),
            "https://ghe.example.com/new-org/widgets",
        )

    def test_convert_project_with_none_project_substitution_returns_none(self):
        mapper = SubstituteConversionMapper(
            r"(?P<repo>.+)", repo_substitution="{repo}", project_substitution=None
        )
        self.assertIsNone(
            mapper.convert_project(
                "https://github.com", "https://github.com/acme/widgets", "acme"
            )
        )

    def test_convert_project_builds_name_from_path_after_org(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<group>[^/]+)/(?P<repo>[^/]+?)(\.git)?$",
            repo_substitution="{repo}",
            project_substitution="{group}-{repo}",
        )
        self.assertEqual(
            mapper.convert_project(
                "https://github.com",
                "https://github.com/acme/platform/widgets.git",
                "acme",
            ),
            "platform-widgets",
        )

    def test_repo_and_project_substitutions_are_independent(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<repo>[^/]+)$",
            repo_substitution="migrated/{repo}",
            project_substitution="proj-{repo}",
        )
        source = ("https://github.com", "https://github.com/acme/widgets", "acme")
        self.assertEqual(
            mapper.convert_repo_url(*source, "https://ghe.example.com", "new-org"),
            "https://ghe.example.com/new-org/migrated/widgets",
        )
        self.assertEqual(mapper.convert_project(*source), "proj-widgets")

    def test_convert_project_path_not_yielding_values_raises(self):
        mapper = SubstituteConversionMapper(
            r"^(?P<repo>[^/]+)$", "{repo}", "{repo}-{branch}"
        )
        with self.assertRaises(MappingException) as ctx:
            mapper.convert_project(
                "https://github.com", "https://github.com/acme/widgets", "acme"
            )
        self.assertIn("branch", str(ctx.exception))

    def test_convert_project_validates_org(self):
        mapper = SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}", "{repo}")
        with self.assertRaises(MappingException):
            mapper.convert_project(
                "https://github.com", "https://github.com/other/widgets", "acme"
            )

    def test_convert_project_does_not_check_base_url(self):
        mapper = SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}", "{repo}")
        self.assertEqual(
            mapper.convert_project(
                "https://github.com", "https://gitlab.com/acme/widgets", "acme"
            ),
            "widgets",
        )

    def test_project_substitution_is_required(self):
        with self.assertRaises(TypeError):
            SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}")

    def test_invalid_project_substitution_raises_on_init(self):
        with self.assertRaises(ValueError):
            SubstituteConversionMapper(r"(?P<repo>.+)", "{repo}", "{repo")

    def test_invalid_regex_raises_on_init(self):
        with self.assertRaises(re.error):
            SubstituteConversionMapper(r"(?P<repo>", "{repo}", None)

    def test_invalid_substitution_raises_on_init(self):
        with self.assertRaises(ValueError):
            SubstituteConversionMapper(r"(?P<repo>.+)", "{repo", None)


if __name__ == "__main__":
    unittest.main()
