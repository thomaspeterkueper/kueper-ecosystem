from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("pr_review_agent_v06.py")
spec = importlib.util.spec_from_file_location("pr_review_agent_v06", MODULE_PATH)
assert spec and spec.loader
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


class FakeDB:
    def __init__(self, pending):
        self.pending = list(pending)
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        if name == "kueper_list_review_pending":
            return list(self.pending)
        return None


class ReviewerStaleSweepTests(unittest.TestCase):
    def setUp(self):
        self.original_state = reviewer.v05.pr_state
        self.original_terminal = reviewer.v05.v04._original_review_task
        self.original_live = reviewer.v05.resilient_review_pending_batch

    def tearDown(self):
        reviewer.v05.pr_state = self.original_state
        reviewer.v05.v04._original_review_task = self.original_terminal
        reviewer.v05.resilient_review_pending_batch = self.original_live

    def test_sweep_reconciles_closed_task_even_after_open_task(self):
        tasks = [
            {"id": "open-first", "pr_url": "https://github.com/o/r/pull/1"},
            {"id": "closed-later", "pr_url": "https://github.com/o/r/pull/2"},
        ]
        db = FakeDB(tasks)
        states = {tasks[0]["pr_url"]: "OPEN", tasks[1]["pr_url"]: "CLOSED"}
        reviewer.v05.pr_state = lambda url: states[url]
        reviewer.v05.v04._original_review_task = lambda task, _db: {
            "task": task["id"], "result": "terminal"
        }

        result = reviewer.reconcile_inactive_review_tasks(db, 50)

        self.assertEqual(result, [{"task": "closed-later", "result": "terminal"}])

    def test_sweep_continues_after_transient_state_lookup_error(self):
        tasks = [
            {"id": "lookup-error", "pr_url": "https://github.com/o/r/pull/1"},
            {"id": "merged-later", "pr_url": "https://github.com/o/r/pull/2"},
        ]
        db = FakeDB(tasks)

        def state(url):
            if url.endswith("/1"):
                raise RuntimeError("temporary github error")
            return "MERGED"

        reviewer.v05.pr_state = state
        reviewer.v05.v04._original_review_task = lambda task, _db: {
            "task": task["id"], "result": "terminal"
        }

        result = reviewer.reconcile_inactive_review_tasks(db, 50)

        self.assertEqual(result, [{"task": "merged-later", "result": "terminal"}])

    def test_cleanup_runs_before_provider_paused_live_batch(self):
        db = FakeDB([{"id": "closed", "pr_url": "https://github.com/o/r/pull/2"}])
        reviewer.v05.pr_state = lambda _url: "CLOSED"
        reviewer.v05.v04._original_review_task = lambda task, _db: {
            "task": task["id"], "result": "terminal"
        }
        reviewer.v05.resilient_review_pending_batch = lambda _db, _max: (
            [{"task": "open", "result": "provider-paused", "provider": "deepseek"}], 0
        )

        results, failures = reviewer.resilient_review_pending_batch(db, 3)

        self.assertEqual(failures, 0)
        self.assertEqual(results[0]["task"], "closed")
        self.assertEqual(results[1]["result"], "provider-paused")


if __name__ == "__main__":
    unittest.main()
