from __future__ import annotations

import importlib.util
import unittest
from unittest import mock
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("pr_review_agent.py")
spec = importlib.util.spec_from_file_location("pr_review_agent", MODULE_PATH)
assert spec and spec.loader
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


class ReviewValidationTests(unittest.TestCase):
    def finding(self, *, blocking: bool = True):
        return {
            "finding_id": "correctness:stable-1",
            "severity": "high",
            "category": "CORRECTNESS",
            "path": "lib/example.ts",
            "line": 10,
            "issue": "state may duplicate work",
            "expected": "one idempotent transition",
            "evidence": ["diff:lib/example.ts"],
            "confidence": 0.98,
            "blocking": blocking,
        }

    def test_pass_without_blockers(self):
        got = reviewer.validate_review({"verdict": "PASS", "summary": "ok", "findings": []})
        self.assertEqual(got["verdict"], "PASS")

    def test_pass_rejects_blocking_finding(self):
        with self.assertRaises(reviewer.worker.WorkerError):
            reviewer.validate_review({"verdict": "PASS", "summary": "bad", "findings": [self.finding()]})

    def test_changes_required_needs_blocker(self):
        with self.assertRaises(reviewer.worker.WorkerError):
            reviewer.validate_review({"verdict": "CHANGES_REQUIRED", "summary": "bad", "findings": [self.finding(blocking=False)]})

    def test_duplicate_finding_id_rejected(self):
        f = self.finding()
        with self.assertRaises(reviewer.worker.WorkerError):
            reviewer.validate_review({"verdict": "CHANGES_REQUIRED", "summary": "bad", "findings": [f, dict(f)]})

    def test_json_extraction_accepts_wrapped_object(self):
        got = reviewer.extract_json('result follows\n{"verdict":"PASS","summary":"ok","findings":[]}\nend')
        self.assertEqual(got["verdict"], "PASS")


class ReviewQueueCleanupTests(unittest.TestCase):
    class FakeDb:
        def __init__(self):
            self.queue_calls = 0

        def rpc(self, name, payload):
            if name != "kueper_list_review_pending":
                raise AssertionError(f"unexpected RPC: {name}")
            self.queue_calls += 1
            if self.queue_calls == 1:
                return [{"id": "closed-1"}, {"id": "merged-2"}, {"id": "closed-3"}]
            if self.queue_calls == 2:
                return [{"id": "live-4"}, {"id": "live-5"}, {"id": "live-6"}]
            return []

    def test_terminal_prs_do_not_consume_bounded_review_slots(self):
        db = self.FakeDb()

        def fake_review(task, _db):
            if task["id"].startswith(("closed", "merged")):
                return {"task": task["id"], "result": "terminal"}
            return {"task": task["id"], "result": "PASS"}

        with mock.patch.object(reviewer, "review_task", side_effect=fake_review):
            results, failures = reviewer.review_pending_batch(db, 3)

        self.assertEqual(failures, 0)
        self.assertEqual(db.queue_calls, 2)
        self.assertEqual([r["result"] for r in results], [
            "terminal", "terminal", "terminal", "PASS", "PASS", "PASS",
        ])

    def test_review_error_consumes_slot_and_cannot_loop_forever(self):
        db = self.FakeDb()
        with mock.patch.object(reviewer, "review_task", side_effect=RuntimeError("boom")):
            results, failures = reviewer.review_pending_batch(db, 2)
        self.assertEqual(failures, 2)
        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()
