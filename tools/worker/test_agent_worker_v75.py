from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("agent_worker_v75.py")
sys.path.insert(0, str(MODULE_PATH.parent))
spec = importlib.util.spec_from_file_location("agent_worker_v75", MODULE_PATH)
assert spec and spec.loader
worker_v75 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker_v75)


class CanonicalProviderReasonTests(unittest.TestCase):
    def test_reason_omits_provider_diagnostic_body(self):
        exc = worker_v75.worker.ProviderUnavailable(
            "deepseek",
            "billing-insufficient-balance",
            "very long provider output that must remain diagnostic-only",
            21600,
        )

        self.assertEqual(
            worker_v75.canonical_provider_reason(exc),
            "Provider unavailable: deepseek / billing-insufficient-balance",
        )
        self.assertNotIn("very long", worker_v75.canonical_provider_reason(exc))
        self.assertEqual(exc.message, "very long provider output that must remain diagnostic-only")

    def test_string_override_keeps_machine_readable_provider_and_code(self):
        exc = worker_v75.worker.ProviderUnavailable("deepseek", "rate-limit", "429 detail", 1800)
        self.assertEqual(worker_v75._provider_unavailable_str(exc), "Provider unavailable: deepseek / rate-limit")


if __name__ == "__main__":
    unittest.main()
