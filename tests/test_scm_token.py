import os
import unittest
from unittest import mock
from cxone_repo_tools.commands.scm.scm_token import PAT_ENV, get_scm_token
from cxone_repo_tools.exceptions import AbortedConversionException


class GetScmTokenTestCase(unittest.TestCase):

    def env(self, value=None):
        """Patches the environment so PAT_ENV is set to value, or unset when
        value is None."""
        patcher = mock.patch.dict(
            os.environ, {PAT_ENV: value} if value is not None else {}
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        if value is None:
            os.environ.pop(PAT_ENV, None)

    def test_pat_env_is_cx_pat(self):
        self.assertEqual(PAT_ENV, "CX_PAT")

    def test_no_token_and_not_in_env_returns_none(self):
        self.env("from-env")
        self.assertIsNone(get_scm_token(None, False))

    def test_token_returned(self):
        self.env()
        self.assertEqual(get_scm_token("abc123", False), "abc123")

    def test_token_takes_precedence_over_env(self):
        self.env("from-env")
        self.assertEqual(get_scm_token("abc123", True), "abc123")

    def test_token_returned_when_in_env_and_env_unset(self):
        self.env()
        self.assertEqual(get_scm_token("abc123", True), "abc123")

    def test_env_value_returned_when_no_token(self):
        self.env("from-env")
        self.assertEqual(get_scm_token(None, True), "from-env")

    def test_env_unset_raises(self):
        self.env()
        with self.assertRaises(AbortedConversionException) as ctx:
            get_scm_token(None, True)
        self.assertIn(PAT_ENV, str(ctx.exception))

    def test_env_empty_raises(self):
        self.env("")
        with self.assertRaises(AbortedConversionException) as ctx:
            get_scm_token(None, True)
        self.assertIn(PAT_ENV, str(ctx.exception))

    def test_empty_token_raises(self):
        self.env()
        with self.assertRaises(AbortedConversionException) as ctx:
            get_scm_token("", False)
        self.assertIn("empty", str(ctx.exception))

    def test_empty_token_raises_even_when_env_set(self):
        self.env("from-env")
        with self.assertRaises(AbortedConversionException):
            get_scm_token("", True)


if __name__ == "__main__":
    unittest.main()
