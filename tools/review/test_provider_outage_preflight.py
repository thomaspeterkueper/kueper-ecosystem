import unittest

from tools.review.provider_outage_preflight import classify_provider_outage_preflight


class ProviderOutagePreflightTests(unittest.TestCase):
    def test_never_passes_normal_pr(self):
        result = classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="abc123",
            pr_state="OPEN",
            changed_paths=["src/app.ts"],
        )
        self.assertEqual(result.disposition, "DEFERRED")
        self.assertIn("provider-unavailable-independent-review-required", result.reasons)

    def test_sensitive_path_is_deferred_not_passed(self):
        result = classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="abc123",
            pr_state="OPEN",
            changed_paths=[".github/workflows/x.yml"],
        )
        self.assertEqual(result.disposition, "DEFERRED")
        self.assertIn("sensitive-paths-require-independent-review", result.reasons)

    def test_changed_head_blocks(self):
        result = classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="def456",
            pr_state="OPEN",
            changed_paths=["src/app.ts"],
        )
        self.assertEqual(result.disposition, "BLOCKED")
        self.assertIn("head-sha-mismatch", result.reasons)

    def test_closed_pr_blocks(self):
        result = classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="abc123",
            pr_state="MERGED",
            changed_paths=["src/app.ts"],
        )
        self.assertEqual(result.disposition, "BLOCKED")
        self.assertIn("pr-not-open:MERGED", result.reasons)


if __name__ == "__main__":
    unittest.main()
