#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge_gate  # noqa: E402

HEAD = "ee23d493a818214e4e534729da589c7b0b4b66a4"
POLICY = {
    "mode": "fail-closed",
    "required": [
        {"id": "vercel", "source": "commit_status", "context": "Vercel"},
        {"id": "supabase-preview", "source": "check_run", "name": "Supabase Preview"},
        {"id": "supabase-migrations", "source": "check_run", "name": "Supabase Preview"},
    ],
}


def status(state: str = "success", sha: str = HEAD):
    return {"sha": sha, "statuses": [{"context": "Vercel", "state": state}]}


def checks(conclusion: str = "success", sha: str = HEAD, include: bool = True, run_status: str = "completed"):
    runs = []
    if include:
        runs.append({"name": "Supabase Preview", "head_sha": sha, "status": run_status, "conclusion": conclusion})
    return {"check_runs": runs}


class MergeGateTests(unittest.TestCase):
    def test_regression_vercel_green_supabase_migration_failure_blocks(self):
        result = merge_gate.evaluate(POLICY, HEAD, status("success"), checks("failure"))
        self.assertFalse(result["allowed"])
        self.assertIn("supabase-preview-failure", result["reason"])

    def test_missing_required_check_blocks(self):
        result = merge_gate.evaluate(POLICY, HEAD, status(), checks(include=False))
        self.assertFalse(result["allowed"])
        self.assertIn("missing-or-ambiguous", result["reason"])

    def test_check_from_old_head_blocks(self):
        result = merge_gate.evaluate(POLICY, HEAD, status(), checks(sha="old-head"))
        self.assertFalse(result["allowed"])
        self.assertIn("stale-head", result["reason"])

    def test_incomplete_check_blocks(self):
        result = merge_gate.evaluate(POLICY, HEAD, status(), checks(conclusion="", run_status="in_progress"))
        self.assertFalse(result["allowed"])
        self.assertIn("incomplete", result["reason"])

    def test_failed_vercel_blocks(self):
        result = merge_gate.evaluate(POLICY, HEAD, status("failure"), checks())
        self.assertFalse(result["allowed"])
        self.assertIn("vercel-failure", result["reason"])

    def test_all_required_current_head_green_allows_review_to_continue(self):
        result = merge_gate.evaluate(POLICY, HEAD, status(), checks())
        self.assertTrue(result["allowed"])
        self.assertEqual(result["reason"], "all-required-checks-green")
        self.assertEqual([x["id"] for x in result["details"]], ["vercel", "supabase-preview", "supabase-migrations"])

    def test_status_payload_for_old_head_blocks(self):
        result = merge_gate.evaluate(POLICY, HEAD, status(sha="old-head"), checks())
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "stale-status-head")


if __name__ == "__main__":
    unittest.main()
