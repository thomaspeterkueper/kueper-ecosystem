from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker_v76 as v76


class FakeDB:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        return self.response


class WorkerV76Tests(unittest.TestCase):
    def test_claim_reserves_selected_model_before_returning_task(self):
        db = FakeDB({"claimed": True, "task": {"id": "abc", "lease_token": "lease"}, "budget": {"calls": 3}})
        decision = SimpleNamespace(provider="deepseek", model="deepseek-v4-flash", reason="Flash default")
        task, budget = v76.claim_for_execution(db, {"id": "abc"}, "worker-1", decision)
        self.assertEqual(task["lease_token"], "lease")
        self.assertEqual(budget["calls"], 3)
        self.assertEqual(db.calls[0][0], "kueper_claim_task_with_llm_budget")
        self.assertEqual(db.calls[0][1]["p_model"], "deepseek-v4-flash")

    def test_budget_denial_does_not_fabricate_claim(self):
        db = FakeDB({"claimed": False, "reason": "daily-pro-budget-exhausted", "pro_calls": 2})
        decision = SimpleNamespace(provider="deepseek", model="deepseek-v4-pro", reason="security task")
        task, detail = v76.claim_for_execution(db, {"id": "abc"}, "worker-1", decision)
        self.assertIsNone(task)
        self.assertEqual(detail["reason"], "daily-pro-budget-exhausted")
        self.assertIn(detail["reason"], v76.BUDGET_REASONS)

    def test_next_budget_window_is_future_utc_day(self):
        reset = dt.datetime.fromisoformat(v76.next_utc_day())
        self.assertIsNotNone(reset.tzinfo)
        self.assertGreater(reset, dt.datetime.now(dt.timezone.utc))
        self.assertEqual((reset.hour, reset.minute), (0, 2))


if __name__ == "__main__":
    unittest.main()
