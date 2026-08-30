#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.worker.direct_main_guard import (
    DefaultBranchMutationBlocked,
    assert_push_target,
    install_pre_push_guard,
    validate_push_lines,
)


class DirectMainGuardTests(unittest.TestCase):
    def test_pre_push_payload_rejects_default_branch(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            validate_push_lines(
                "main",
                "refs/heads/review-fix abc refs/heads/main 000\n",
            )

    def test_pre_push_payload_allows_pr_branch(self):
        validate_push_lines(
            "main",
            "refs/heads/task abc refs/heads/ecosystem/task-123 000\n",
        )

    def test_explicit_refspec_rejects_default_branch(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_push_target("main", "HEAD:main")
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_push_target("main", "HEAD:refs/heads/main")
        assert_push_target("main", "HEAD:review/fix-123")

    def test_installed_hook_blocks_agent_style_push_to_main(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            hook = install_pre_push_guard(root, "main")
            blocked = subprocess.run(
                [str(hook), "origin", "unused"],
                input="refs/heads/work abc refs/heads/main 000\n",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(blocked.returncode, 41)
            self.assertIn("direct push to default branch main is forbidden", blocked.stderr)

    def test_draft_ready_failure_contract_is_fail_closed(self):
        """A failed Ready/Merge step cannot be replaced by a push to default."""
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_push_target("main", "HEAD:main")


if __name__ == "__main__":
    unittest.main()
