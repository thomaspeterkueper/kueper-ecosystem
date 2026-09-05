from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("pr_review_agent_v07.py")
sys.path.insert(0, str(MODULE_PATH.parent))
spec = importlib.util.spec_from_file_location("pr_review_agent_v07", MODULE_PATH)
assert spec and spec.loader
v07 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v07)


class ReviewModelPolicyTests(unittest.TestCase):
    def test_routine_pr_uses_flash(self):
        model, reason = v07.select_review_model(
            {"type": "IMPLEMENT_EXTERNAL_REQUIREMENT", "priority": "medium", "payload": {}},
            ["app/page.tsx", "README.md"],
        )
        self.assertEqual(model, "deepseek-v4-flash")
        self.assertIn("routine review", reason)

    def test_high_priority_pr_uses_pro(self):
        model, _ = v07.select_review_model(
            {"type": "IMPLEMENT_EXTERNAL_REQUIREMENT", "priority": "high", "payload": {}},
            ["app/page.tsx"],
        )
        self.assertEqual(model, "deepseek-v4-pro")

    def test_workflow_change_uses_pro(self):
        model, reason = v07.select_review_model(
            {"type": "CODE", "priority": "medium", "payload": {}},
            [".github/workflows/deploy.yml"],
        )
        self.assertEqual(model, "deepseek-v4-pro")
        self.assertIn("privileged/sensitive path", reason)

    def test_critical_scientific_gate_uses_pro(self):
        model, _ = v07.select_review_model(
            {
                "type": "PR_REVIEW",
                "priority": "medium",
                "payload": {},
                "blocked_reason": "Critical scientific/evidence review required",
            },
            ["docs/evidence.md"],
        )
        self.assertEqual(model, "deepseek-v4-pro")

    def test_explicit_deep_reasoning_uses_pro(self):
        model, _ = v07.select_review_model(
            {"type": "CODE", "priority": "medium", "payload": {"requires_deep_reasoning": True}},
            ["src/simple.py"],
        )
        self.assertEqual(model, "deepseek-v4-pro")

    def test_unknown_changed_paths_fail_safe_to_pro(self):
        model, _ = v07.select_review_model(
            {"type": "CODE", "priority": "medium", "payload": {}},
            ["__UNKNOWN_CHANGED_PATHS__"],
        )
        self.assertEqual(model, "deepseek-v4-pro")


if __name__ == "__main__":
    unittest.main()
