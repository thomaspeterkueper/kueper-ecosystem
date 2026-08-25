import unittest

from tools.review.direct_pr_intake import parse_pr_url


class DirectPrIntakeTests(unittest.TestCase):
    def test_parses_canonical_pr_url(self):
        self.assertEqual(
            parse_pr_url("https://github.com/thomaspeterkueper/kueper-ecosystem/pull/30"),
            ("thomaspeterkueper/kueper-ecosystem", 30),
        )

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/thomaspeterkueper/kueper-ecosystem/issues/30")


if __name__ == "__main__":
    unittest.main()
