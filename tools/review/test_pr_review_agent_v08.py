from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("pr_review_agent_v08.py")
sys.path.insert(0, str(MODULE_PATH.parent))
spec = importlib.util.spec_from_file_location("pr_review_agent_v08", MODULE_PATH)
assert spec and spec.loader
v08 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v08)


class FakeDB:
    def __init__(self, reserved=False):
        self.reserved = reserved
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        if name == "kueper_llm_invocation_reserved_today":
            return self.reserved
        raise AssertionError(name)


class ReviewBudgetDedupTests(unittest.TestCase):
    def test_reason_contains_head_sha(self):
        task = {"payload": {"head_sha": "abc123"}}
        self.assertEqual(v08.review_reason(task, "routine review"), "routine review; head=abc123")

    def test_changed_head_changes_dedup_key(self):
        a = v08.review_reason({"payload": {"head_sha": "aaa"}}, "routine review")
        b = v08.review_reason({"payload": {"head_sha": "bbb"}}, "routine review")
        self.assertNotEqual(a, b)

    def test_live_head_replaces_stale_task_head_before_dedup(self):
        from unittest.mock import patch
        task = {
            "id": "11111111-1111-1111-1111-111111111111",
            "repository": "owner/repo",
            "pr_url": "https://github.com/owner/repo/pull/1",
            "payload": {"head_sha": "stale"},
        }
        db = FakeDB(reserved=True)
        with patch.object(v08, "required_ci_gate", return_value={
            "allowed": True, "reason": "all-required-checks-green",
            "head_sha": "fresh", "details": [],
        }), patch.object(v08.v07, "changed_paths", return_value=["README.md"]), patch.object(
            v08.v07, "select_review_model", return_value=("deepseek-v4-flash", "routine")
        ):
            result = v08.cost_aware_review_task(task, db)
        self.assertEqual(result["result"], "already-attempted-today")
        self.assertIn("head=fresh", db.calls[0][1]["p_reason"])
        self.assertEqual(task["payload"]["head_sha"], "stale")

    def test_no_policy_fetches_current_head_from_github(self):
        from unittest.mock import patch
        task = {"pr_url": "https://github.com/owner/repo/pull/1"}
        gate = {"allowed": True, "reason": "no-required-check-policy", "head_sha": None}
        with patch.object(v08.merge_gate, "_run_json", return_value={
            "headRefOid": "current-head", "state": "OPEN"
        }) as gh:
            self.assertEqual(v08.current_pr_head(task, gate), "current-head")
        gh.assert_called_once()

    def test_closed_pr_cannot_supply_head(self):
        from unittest.mock import patch
        with patch.object(v08.merge_gate, "_run_json", return_value={
            "headRefOid": "old-head", "state": "MERGED"
        }):
            self.assertIsNone(v08.current_pr_head({"pr_url": "https://github.com/owner/repo/pull/1"}, {}))

    def test_missing_live_head_does_not_reserve_budget(self):
        from unittest.mock import patch
        task = {"id": "t", "repository": "owner/repo", "pr_url": "https://github.com/owner/repo/pull/1"}
        db = FakeDB()
        with patch.object(v08, "required_ci_gate", return_value={
            "allowed": True, "reason": "no-required-check-policy", "head_sha": None, "details": [],
        }), patch.object(v08.v07, "changed_paths", return_value=[]), patch.object(
            v08.v07, "select_review_model", return_value=("deepseek-v4-flash", "routine")
        ):
            result = v08.cost_aware_review_task(task, db)
        self.assertEqual(result["result"], "ci-gate-blocked")
        self.assertEqual(result["reason"], "missing-current-head")
        self.assertEqual(db.calls, [])

    def test_daily_lookup_is_task_and_reason_scoped(self):
        db = FakeDB(reserved=True)
        task = {"id": "11111111-1111-1111-1111-111111111111"}
        self.assertTrue(v08.already_reserved_today(db, task, "routine; head=abc"))
        name, payload = db.calls[0]
        self.assertEqual(name, "kueper_llm_invocation_reserved_today")
        self.assertEqual(payload["p_task_id"], task["id"])
        self.assertEqual(payload["p_reason"], "routine; head=abc")


if __name__ == "__main__":
    unittest.main()
