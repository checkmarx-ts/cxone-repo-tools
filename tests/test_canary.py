import unittest


class CanaryTestCase(unittest.TestCase):
    """Trivial sanity check that the test suite is discovered and runs."""

    def test_canary(self):
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
