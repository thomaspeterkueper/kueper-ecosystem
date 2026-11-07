"""Offline regression tests for the read-only release evidence pilot."""
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "release_evidence", pathlib.Path(__file__).resolve().parents[1] / "tools/governance/release_evidence.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PR = {"number": 127, "head": {"sha": "newsha"}, "draft": False, "user": {"login": "author"}}

def fake_get(path):
    if "/reviews?" in path:
        return [
            {"id": 1, "user": {"login": "reviewer"}, "state": "APPROVED", "submitted_at": "2026-11-01T10:00:00Z", "commit_id": "oldsha"},
            {"id": 2, "user": {"login": "reviewer"}, "state": "COMMENTED", "submitted_at": "2026-11-02T10:00:00Z", "commit_id": "newsha"},
        ]
    if "/check-runs?" in path:
        return {"total_count": 1, "check_runs": [{"name": "build", "status": "completed", "conclusion": "success"}]}
    if "/status" in path:
        return {"state": "success", "statuses": [{"state": "success"}]}
    raise AssertionError(path)

class EvidenceTests(unittest.TestCase):
    @patch.object(module, "get", side_effect=fake_get)
    def test_comment_does_not_revalidate_stale_approval(self, _):
        result = module.inspect("owner/repo", PR)
        self.assertEqual(result["stale_approvals"], ["reviewer"])
        self.assertEqual(result["independent_approvals"], [])
        self.assertIn("no_current_head_independent_approval", result["blockers"])

    @patch.object(module, "get", side_effect=lambda path: (
        [{"id": 3, "user": {"login": "reviewer"}, "state": "APPROVED", "submitted_at": "2026-11-03T10:00:00Z", "commit_id": "newsha"}]
        if "/reviews?" in path else fake_get(path)
    ))
    def test_current_head_approval(self, _):
        result = module.inspect("owner/repo", PR)
        self.assertEqual(result["independent_approvals"], ["reviewer"])
        self.assertNotIn("no_current_head_independent_approval", result["blockers"])

    @patch.object(module, "get", side_effect=lambda path: (
        {"total_count": 1, "check_runs": [{"name": "build", "status": "completed", "conclusion": "failure"}]}
        if "/check-runs?" in path else fake_get(path)
    ))
    def test_failed_check_blocks(self, _):
        self.assertIn("failed_checks", module.inspect("owner/repo", PR)["blockers"])

    @patch.object(module, "get", side_effect=lambda path: (
        {"total_count": 2, "check_runs": [
            {"name": "build", "status": "completed", "conclusion": "stale"},
            {"name": "build", "status": "completed", "conclusion": "success"},
        ]}
        if "/check-runs?" in path else
        [{"id": 4, "user": {"login": "reviewer"}, "state": "APPROVED", "submitted_at": "2026-11-03T10:00:00Z", "commit_id": "newsha"}]
        if "/reviews?" in path else fake_get(path)
    ))
    def test_superseded_stale_check_run_does_not_block(self, _):
        result = module.inspect("owner/repo", PR)
        self.assertNotIn("non_successful_check_runs", result["blockers"])

    @patch.object(module, "get", side_effect=lambda path: (
        {"state": "success", "total_count": 55, "statuses": [{"state": "success"}] * 30}
        if "/status" in path else
        [{"id": 5, "user": {"login": "reviewer"}, "state": "APPROVED", "submitted_at": "2026-11-03T10:00:00Z", "commit_id": "newsha"}]
        if "/reviews?" in path else fake_get(path)
    ))
    def test_incomplete_commit_status_page_blocks(self, _):
        result = module.inspect("owner/repo", PR)
        self.assertIn("commit_statuses_pagination_incomplete", result["blockers"])

    def test_commit_status_request_uses_max_page_size(self):
        paths = []

        def recording_get(path):
            paths.append(path)
            return fake_get(path)

        with patch.object(module, "get", side_effect=recording_get):
            module.inspect("owner/repo", PR)
        self.assertTrue(any("/status?" in path and "per_page=100" in path for path in paths))

if __name__ == "__main__":
    unittest.main()
