import unittest
from cxone_repo_tools.convert.mapping import StringByRegex
from cxone_repo_tools.exceptions import MappingException

REPO_URL_REGEX = r"^https://(?P<host>[^/]+)/(?P<org>[^/]+)/(?P<repo>[^/]+)$"


class StringByRegexTestCase(unittest.TestCase):

    def test_builds_output_from_extracted_values(self):
        converter = StringByRegex(REPO_URL_REGEX, "git@{host}:{org}/{repo}.git")
        self.assertEqual(
            converter.convert("https://github.com/acme/widgets"),
            "git@github.com:acme/widgets.git",
        )

    def test_value_referenced_more_than_once(self):
        converter = StringByRegex(REPO_URL_REGEX, "{org}/{repo}-{org}")
        self.assertEqual(
            converter.convert("https://github.com/acme/widgets"),
            "acme/widgets-acme",
        )

    def test_unreferenced_extracted_values_are_ignored(self):
        converter = StringByRegex(REPO_URL_REGEX, "{repo}")
        self.assertEqual(
            converter.convert("https://github.com/acme/widgets"), "widgets"
        )

    def test_static_only_substitution_needs_no_extracted_values(self):
        converter = StringByRegex(REPO_URL_REGEX, "static-value")
        self.assertEqual(converter.convert("does not match"), "static-value")

    def test_converter_is_reusable_across_inputs(self):
        converter = StringByRegex(REPO_URL_REGEX, "{org}/{repo}")
        self.assertEqual(converter.convert("https://github.com/acme/one"), "acme/one")
        self.assertEqual(converter.convert("https://gitlab.com/other/two"), "other/two")

    def test_input_that_does_not_match_raises(self):
        converter = StringByRegex(REPO_URL_REGEX, "{org}/{repo}")
        with self.assertRaises(MappingException):
            converter.convert("not a repository url")

    def test_referenced_value_not_extracted_raises(self):
        converter = StringByRegex(r"^(?P<org>[^/]+)(/(?P<repo>.+))?$", "{org}/{repo}")
        with self.assertRaises(MappingException) as ctx:
            converter.convert("acme")
        self.assertIn("repo", str(ctx.exception))

    def test_referenced_value_not_in_regex_raises(self):
        converter = StringByRegex(REPO_URL_REGEX, "{org}/{repo}@{branch}")
        with self.assertRaises(MappingException) as ctx:
            converter.convert("https://github.com/acme/widgets")
        self.assertIn("branch", str(ctx.exception))

    def test_unreferenced_value_not_extracted_is_allowed(self):
        converter = StringByRegex(r"^(?P<org>[^/]+)(/(?P<repo>.+))?$", "{org}")
        self.assertEqual(converter.convert("acme"), "acme")


if __name__ == "__main__":
    unittest.main()
