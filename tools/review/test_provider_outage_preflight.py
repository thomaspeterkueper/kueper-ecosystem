from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("provider_outage_preflight.py")
spec = importlib.util.spec_from_file_location("provider_outage_preflight", MODULE_PATH)
assert spec and spec.loader
preflight = importlib.util.module_from_spec(spec)
# Register before exec so the module-level @dataclass can resolve its own module.
sys.modules[spec.name] = preflight
spec.loader.exec_module(preflight)


class ProviderOutagePreflightTests(unittest.TestCase):
    def test_never_passes_normal_pr(self):
        result = preflight.classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="abc123",
            pr_state="OPEN",
            changed_paths=["src/app.ts"],
        )
        self.assertEqual(result.disposition, "DEFERRED_PROVIDER_UNAVAILABLE")
        self.assertIn("provider-unavailable-independent-review-required", result.reasons)

    def test_sensitive_path_is_deferred_not_passed(self):
        result = preflight.classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="abc123",
            pr_state="OPEN",
            changed_paths=[".github/workflows/x.yml"],
        )
        self.assertEqual(result.disposition, "DEFERRED_PROVIDER_UNAVAILABLE")
        self.assertIn("sensitive-paths-require-independent-review", result.reasons)

    def test_changed_head_blocks(self):
        result = preflight.classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="def456",
            pr_state="OPEN",
            changed_paths=["src/app.ts"],
        )
        self.assertEqual(result.disposition, "BLOCKED")
        self.assertIn("head-sha-mismatch", result.reasons)

    def test_closed_pr_blocks(self):
        result = preflight.classify_provider_outage_preflight(
            expected_head_sha="abc123",
            current_head_sha="abc123",
            pr_state="MERGED",
            changed_paths=["src/app.ts"],
        )
        self.assertEqual(result.disposition, "BLOCKED")
        self.assertIn("pr-not-open:MERGED", result.reasons)


if __name__ == "__main__":
    unittest.main()
