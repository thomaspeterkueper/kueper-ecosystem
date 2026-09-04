from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("pr_review_agent_v05.py")
spec = importlib.util.spec_from_file_location("pr_review_agent_v05", MODULE_PATH)
assert spec and spec.loader
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


class FakeDB:
    def __init__(self, pending, provider_available=True):
        self.pending = list(pending)
        self.provider_available = provider_available
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        if name == "kueper_list_review_pending":
            return list(self.pending)
        if name == "kueper_provider_available":
            return self.provider_available
        if name == "kueper_pause_provider":
            return {"paused": True}
        return {"rpc": name}


class ReviewerResilienceTests(unittest.TestCase):
    def setUp(self):
        self.original_state = reviewer.pr_state
        self.original_terminal = reviewer.v04._original_review_task
        self.original_guarded = reviewer.v04.guarded_review_task

    def tearDown(self):
        reviewer.pr_state = self.original_state
        reviewer.v04._original_review_task = self.original_terminal
        reviewer.v04.guarded_review_task = self.original_guarded

    def test_closed_pr_is_terminalized_without_provider_check(self):
        task = {"id": "closed-1", "pr_url": "https://github.com/o/r/pull/1"}
        db = FakeDB([task], provider_available=False)
        reviewer.pr_state = lambda _url: "CLOSED"
        reviewer.v04._original_review_task = lambda current, _db: {
            "task": current["id"],
            "result": "terminal",
            "reason": "PR is CLOSED",
        }

        results, failures = reviewer.resilient_review_pending_batch(db, 1)

        self.assertEqual(failures, 0)
        self.assertEqual(results[0]["result"], "terminal")
        self.assertFalse(any(name == "kueper_provider_available" for name, _ in db.calls))

    def test_paused_provider_leaves_open_review_queued_without_failure(self):
        task = {"id": "open-1", "pr_url": "https://github.com/o/r/pull/2"}
        db = FakeDB([task], provider_available=False)
        reviewer.pr_state = lambda _url: "OPEN"

        results, failures = reviewer.resilient_review_pending_batch(db, 3)

        self.assertEqual(failures, 0)
        self.assertEqual(results, [{"task": "open-1", "result": "provider-paused", "provider": "deepseek"}])

    def test_provider_unavailable_is_persisted_as_pause_not_review_error(self):
        task = {"id": "open-2", "pr_url": "https://github.com/o/r/pull/3"}
        db = FakeDB([task], provider_available=True)
        reviewer.pr_state = lambda _url: "OPEN"

        def fail_provider(_task, _db):
            raise reviewer.base.worker.ProviderUnavailable(
                "deepseek",
                "billing-insufficient-balance",
                "402 balance exhausted",
                21600,
            )

        reviewer.v04.guarded_review_task = fail_provider

        results, failures = reviewer.resilient_review_pending_batch(db, 3)

        self.assertEqual(failures, 0)
        self.assertEqual(results[0]["result"], "provider-paused")
        pause_calls = [payload for name, payload in db.calls if name == "kueper_pause_provider"]
        self.assertEqual(len(pause_calls), 1)
        self.assertEqual(pause_calls[0]["p_error_code"], "billing-insufficient-balance")
        self.assertEqual(pause_calls[0]["p_pause_seconds"], 21600)

    def test_non_provider_exception_still_fails_closed(self):
        task = {"id": "open-3", "pr_url": "https://github.com/o/r/pull/4"}
        db = FakeDB([task], provider_available=True)
        reviewer.pr_state = lambda _url: "OPEN"

        def fail_review(_task, _db):
            raise RuntimeError("schema corruption")

        reviewer.v04.guarded_review_task = fail_review

        results, failures = reviewer.resilient_review_pending_batch(db, 1)

        self.assertEqual(failures, 1)
        self.assertEqual(results[0]["result"], "REVIEW_ERROR")


if __name__ == "__main__":
    unittest.main()
