from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("pr_review_agent_v04.py")
spec = importlib.util.spec_from_file_location("pr_review_agent_v04", MODULE_PATH)
assert spec and spec.loader
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


class FakeDB:
    def __init__(self):
        self.calls = []

    def rpc(self, name, payload):
        self.calls.append((name, payload))
        return {"delegated": name}


class ResearchCandidateGateTests(unittest.TestCase):
    def test_candidate_only_requires_manual_gate(self):
        self.assertTrue(
            reviewer.research_candidate_only(
                [
                    "research/candidates/RES-A.md",
                    "research/candidates/RES-B.md",
                ]
            )
        )

    def test_mixed_pr_does_not_use_research_gate(self):
        self.assertFalse(
            reviewer.research_candidate_only(
                [
                    "research/candidates/RES-A.md",
                    "src/runtime.ts",
                ]
            )
        )

    def test_empty_file_list_is_not_candidate_only(self):
        self.assertFalse(reviewer.research_candidate_only([]))

    def test_completion_is_suppressed_for_research_candidate(self):
        db = FakeDB()
        proxy = reviewer.CompletionGuardDB(db, hold_completion=True)
        result = proxy.rpc(
            "kueper_complete_reviewed_task",
            {"p_task_id": "task-1", "p_head_sha": "a" * 40},
        )
        self.assertEqual(result["status"], "review_pending")
        self.assertTrue(proxy.completion_suppressed)
        self.assertEqual(db.calls, [])

    def test_other_rpc_is_delegated(self):
        db = FakeDB()
        proxy = reviewer.CompletionGuardDB(db, hold_completion=True)
        result = proxy.rpc("kueper_record_pr_review", {"x": 1})
        self.assertEqual(result, {"delegated": "kueper_record_pr_review"})
        self.assertEqual(db.calls, [("kueper_record_pr_review", {"x": 1})])

    def test_completion_is_delegated_for_normal_pr(self):
        db = FakeDB()
        proxy = reviewer.CompletionGuardDB(db, hold_completion=False)
        result = proxy.rpc(
            "kueper_complete_reviewed_task",
            {"p_task_id": "task-2", "p_head_sha": "b" * 40},
        )
        self.assertEqual(result, {"delegated": "kueper_complete_reviewed_task"})
        self.assertFalse(proxy.completion_suppressed)
        self.assertEqual(db.calls[0][0], "kueper_complete_reviewed_task")


if __name__ == "__main__":
    unittest.main()
