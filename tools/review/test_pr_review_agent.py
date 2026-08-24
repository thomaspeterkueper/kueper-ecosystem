from __future__ import annotations

import importlib.util
import unittest
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


if __name__ == "__main__":
    unittest.main()
