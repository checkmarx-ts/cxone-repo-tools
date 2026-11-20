import unittest
from cxone_repo_tools.convert.mapping import ConversionMapper, DefaultConversionMapper
from cxone_repo_tools.exceptions import MappingException


class DefaultConversionMapperTestCase(unittest.TestCase):

    def setUp(self):
        self.mapper = DefaultConversionMapper()

    def convert(self, source_url, *, source_base="https://github.com", org="acme"):
        return self.mapper.convert_repo_url(
            source_base, source_url, org, "https://ghe.example.com", "new-org"
        )

    def test_replaces_base_url_and_org(self):
        self.assertEqual(
            self.convert("https://github.com/acme/widgets"),
            "https://ghe.example.com/new-org/widgets",
        )

    def test_keeps_rest_of_path(self):
        self.assertEqual(
            self.convert(
                "https://gitlab.com/acme/sub/group/repo.git",
                source_base="https://gitlab.com",
            ),
            "https://ghe.example.com/new-org/sub/group/repo.git",
        )

    def test_keeps_path_after_org_in_azure_layout(self):
        self.assertEqual(
            self.convert(
                "https://dev.azure.com/acme/Proj/_git/repo",
                source_base="https://dev.azure.com",
            ),
            "https://ghe.example.com/new-org/Proj/_git/repo",
        )

    def test_base_url_and_org_compared_without_case(self):
        self.assertEqual(
            self.convert("https://GitHub.com/ACME/widgets"),
            "https://ghe.example.com/new-org/widgets",
        )

    def test_trailing_slashes_on_base_urls_ignored(self):
        self.assertEqual(
            self.mapper.convert_repo_url(
                "https://github.com/",
                "https://github.com/acme/widgets",
                "acme",
                "https://ghe.example.com/",
                "new-org",
            ),
            "https://ghe.example.com/new-org/widgets",
        )

    def test_url_of_org_only(self):
        self.assertEqual(
            self.convert("https://github.com/acme"), "https://ghe.example.com/new-org"
        )

    def test_url_on_different_host_is_converted(self):
        self.assertEqual(
            self.convert("https://gitlab.com/acme/widgets"),
            "https://ghe.example.com/new-org/widgets",
        )

    def test_url_on_host_sharing_base_prefix_is_converted(self):
        self.assertEqual(
            self.convert("https://github.community/acme/widgets"),
            "https://ghe.example.com/new-org/widgets",
        )

    def test_url_equal_to_base_raises(self):
        with self.assertRaises(MappingException):
            self.convert("https://github.com")

    def test_url_in_different_org_raises(self):
        with self.assertRaises(MappingException) as ctx:
            self.convert("https://github.com/other/widgets")
        self.assertIn("not in organization [acme]", str(ctx.exception))

    def test_org_matching_only_a_prefix_of_segment_raises(self):
        with self.assertRaises(MappingException):
            self.convert("https://github.com/acme-labs/widgets")

    def test_url_with_different_scheme_is_converted(self):
        self.assertEqual(
            self.convert("http://github.com/acme/widgets"),
            "https://ghe.example.com/new-org/widgets",
        )

    def test_base_urls_with_paths(self):
        self.assertEqual(
            self.mapper.convert_repo_url(
                "https://scm.example.com/gitlab",
                "https://scm.example.com/GitLab/acme/widgets",
                "acme",
                "https://new.example.com/git/",
                "new-org",
            ),
            "https://new.example.com/git/new-org/widgets",
        )

    def test_url_outside_base_url_path_needs_org_as_first_segment(self):
        with self.assertRaises(MappingException) as ctx:
            self.mapper.convert_repo_url(
                "https://scm.example.com/gitlab",
                "https://scm.example.com/other/acme/widgets",
                "acme",
                "https://new.example.com",
                "new-org",
            )
        self.assertIn("not in organization [acme]", str(ctx.exception))

    def test_url_outside_base_url_path_with_org_first_is_converted(self):
        self.assertEqual(
            self.mapper.convert_repo_url(
                "https://scm.example.com/gitlab",
                "https://git.example.com/acme/widgets",
                "acme",
                "https://new.example.com",
                "new-org",
            ),
            "https://new.example.com/new-org/widgets",
        )

    def test_base_url_path_skipped_on_different_host(self):
        self.assertEqual(
            self.mapper.convert_repo_url(
                "https://scm.example.com/gitlab",
                "https://git.example.com/GitLab/acme/widgets",
                "acme",
                "https://new.example.com",
                "new-org",
            ),
            "https://new.example.com/new-org/widgets",
        )

    def test_query_and_fragment_kept(self):
        self.assertEqual(
            self.convert("https://github.com/acme/widgets?tab=readme#top"),
            "https://ghe.example.com/new-org/widgets?tab=readme#top",
        )


class RecordingMapper(ConversionMapper):
    """Records the paths given to _map_repo_path and _map_project_name and
    returns fixed values."""

    def __init__(self, mapped: str, project_name: str | None = None):
        self.received = []
        self.mapped = mapped
        self.received_project = []
        self.project_name = project_name

    def _map_repo_path(self, path: str) -> str:
        self.received.append(path)
        return self.mapped

    def _map_project_name(self, path: str) -> str | None:
        self.received_project.append(path)
        return self.project_name


class ConversionMapperSubclassTestCase(unittest.TestCase):

    def test_conversion_mapper_is_abstract(self):
        with self.assertRaises(TypeError):
            ConversionMapper()

    def test_subclass_without_map_repo_path_is_abstract(self):
        class Incomplete(ConversionMapper):
            def _map_project_name(self, path):
                return None

        with self.assertRaises(TypeError):
            Incomplete()

    def test_subclass_without_map_project_name_is_abstract(self):
        class Incomplete(ConversionMapper):
            def _map_repo_path(self, path):
                return path

        with self.assertRaises(TypeError):
            Incomplete()

    def test_source_repo_path_is_path_after_org(self):
        self.assertEqual(
            DefaultConversionMapper()._source_repo_path(
                "https://github.com", "https://github.com/ACME/sub/repo.git", "acme"
            ),
            "sub/repo.git",
        )

    def test_source_repo_path_is_dot_when_url_ends_at_org(self):
        self.assertEqual(
            DefaultConversionMapper()._source_repo_path(
                "https://github.com", "https://github.com/acme", "acme"
            ),
            ".",
        )

    def test_source_repo_path_does_not_check_base_url(self):
        self.assertEqual(
            DefaultConversionMapper()._source_repo_path(
                "https://github.com", "https://gitlab.com/acme/repo", "acme"
            ),
            "repo",
        )

    def test_source_repo_path_validates_org(self):
        with self.assertRaises(MappingException):
            DefaultConversionMapper()._source_repo_path(
                "https://github.com", "https://github.com/other/repo", "acme"
            )

    def test_convert_project_passes_path_after_org_to_map_project_name(self):
        mapper = RecordingMapper("x", project_name="renamed")
        self.assertEqual(
            mapper.convert_project(
                "https://github.com", "https://github.com/acme/sub/repo.git", "acme"
            ),
            "renamed",
        )
        self.assertEqual(mapper.received_project, ["sub/repo.git"])

    def test_convert_project_returns_none_from_map_project_name(self):
        mapper = RecordingMapper("x", project_name=None)
        self.assertIsNone(
            mapper.convert_project(
                "https://github.com", "https://github.com/acme/widgets", "acme"
            )
        )

    def test_convert_project_validates_before_map_project_name(self):
        mapper = RecordingMapper("x", project_name="renamed")
        with self.assertRaises(MappingException):
            mapper.convert_project(
                "https://github.com", "https://github.com/other/widgets", "acme"
            )
        self.assertEqual(mapper.received_project, [])

    def test_default_map_project_name_returns_none(self):
        self.assertIsNone(DefaultConversionMapper()._map_project_name("repo"))

    def test_default_convert_project_returns_none(self):
        self.assertIsNone(
            DefaultConversionMapper().convert_project(
                "https://github.com", "https://github.com/acme/widgets", "acme"
            )
        )

    def test_default_mapper_is_a_conversion_mapper(self):
        self.assertIsInstance(DefaultConversionMapper(), ConversionMapper)

    def convert(self, mapper, source_url):
        return mapper.convert_repo_url(
            "https://github.com",
            source_url,
            "acme",
            "https://ghe.example.com",
            "new-org",
        )

    def test_default_map_repo_path_returns_path_unchanged(self):
        self.assertEqual(
            DefaultConversionMapper()._map_repo_path("sub/group/repo.git"),
            "sub/group/repo.git",
        )

    def test_map_repo_path_receives_path_after_org(self):
        mapper = RecordingMapper("x")
        self.convert(mapper, "https://github.com/acme/sub/group/repo.git")
        self.assertEqual(mapper.received, ["sub/group/repo.git"])

    def test_map_repo_path_receives_dot_when_url_ends_at_org(self):
        mapper = RecordingMapper(".")
        self.assertEqual(
            self.convert(mapper, "https://github.com/acme"),
            "https://ghe.example.com/new-org",
        )
        self.assertEqual(mapper.received, ["."])

    def test_mapped_path_follows_target_org(self):
        self.assertEqual(
            self.convert(
                RecordingMapper("renamed/repo"), "https://github.com/acme/widgets"
            ),
            "https://ghe.example.com/new-org/renamed/repo",
        )

    def test_mapped_path_with_leading_slash_stays_under_target_org(self):
        self.assertEqual(
            self.convert(RecordingMapper("/repo"), "https://github.com/acme/widgets"),
            "https://ghe.example.com/new-org/repo",
        )


if __name__ == "__main__":
    unittest.main()
