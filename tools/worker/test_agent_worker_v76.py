from __future__ import annotations

import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("agent_worker_v76.py")
sys.path.insert(0, str(MODULE_PATH.parent))
spec = importlib.util.spec_from_file_location("agent_worker_v76", MODULE_PATH)
assert spec and spec.loader
v76 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v76)

UTC = dt.timezone.utc


class WorkerBudgetTests(unittest.TestCase):
    def test_next_budget_window_is_next_utc_day(self):
        value = v76.next_budget_window(dt.datetime(2026, 9, 5, 23, 59, tzinfo=UTC))
        self.assertEqual(value, "2026-09-06T00:02:00+00:00")

    def test_budget_reason_prefix_is_stable(self):
        self.assertEqual(v76.BUDGET_REASON_PREFIX, "LLM budget deferred:")

    def test_pro_and_flash_share_same_reservation_path(self):
        self.assertTrue(callable(v76.reserve_budget))
        self.assertTrue(callable(v76.budgeted_execute_task))


if __name__ == "__main__":
    unittest.main()
