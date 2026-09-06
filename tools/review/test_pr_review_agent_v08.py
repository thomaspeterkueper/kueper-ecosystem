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
