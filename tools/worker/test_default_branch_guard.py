import tempfile
import unittest
from pathlib import Path

from tools.worker.default_branch_guard import (
    DefaultBranchMutationBlocked,
    DefaultBranchMutationDetected,
    DefaultBranchVerificationFailed,
    assert_no_merge_substitute,
    assert_non_default_branch,
    assert_remote_default_unchanged,
    install_pre_push_hook,
    parse_ls_remote_sha,
    pre_push_hook_script,
)


class FakeResult:
    def __init__(self, returncode: int = 0, stdout: str = ""):
        self.returncode = returncode
        self.stdout = stdout


class DefaultBranchGuardTests(unittest.TestCase):
    def test_agent_branch_is_allowed(self):
        assert_non_default_branch("ecosystem/task-12345678", "main", context="publish")

    def test_default_branch_write_is_blocked(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_non_default_branch("main", "main", context="publish")

    def test_missing_branch_identity_is_blocked(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_non_default_branch("", "main", context="publish")

    def test_draft_pr_ready_unavailable_cannot_fall_back_to_main(self):
        with self.assertRaisesRegex(DefaultBranchMutationBlocked, "keep the PR open"):
            assert_no_merge_substitute(
                pr_state="OPEN",
                is_draft=True,
                ready_or_merge_available=False,
                target_branch="main",
                default_branch="main",
                context="review lifecycle",
            )

    def test_open_non_draft_pr_ready_unavailable_cannot_fall_back_to_main(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_no_merge_substitute(
                pr_state="OPEN",
                is_draft=False,
                ready_or_merge_available=False,
                target_branch="main",
                default_branch="main",
                context="review lifecycle",
            )

    def test_ready_available_still_does_not_allow_default_branch_write(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_no_merge_substitute(
                pr_state="OPEN",
                is_draft=False,
                ready_or_merge_available=True,
                target_branch="main",
                default_branch="main",
                context="review lifecycle",
            )

    def test_blocked_ready_still_allows_pr_head_update(self):
        assert_no_merge_substitute(
            pr_state="OPEN",
            is_draft=True,
            ready_or_merge_available=False,
            target_branch="ecosystem/task-12345678",
            default_branch="main",
            context="review lifecycle",
        )


class PrePushHookTests(unittest.TestCase):
    def test_hook_script_refuses_default_branch(self):
        script = pre_push_hook_script()
        self.assertIn("refs/heads/$default", script)
        self.assertIn("exit 1", script)
        self.assertIn("symbolic-ref", script)
        self.assertIn("fail-closed", script)

    def test_install_pre_push_hook_writes_executable_hook(self):
        with tempfile.TemporaryDirectory(prefix="kueper-guard-test-") as temp:
            root = Path(temp) / "repo"
            (root / ".git" / "hooks").mkdir(parents=True)
            hook = install_pre_push_hook(root)
            self.assertTrue(hook.is_file())
            self.assertEqual(hook.read_text(encoding="utf-8"), pre_push_hook_script())
            self.assertTrue(hook.stat().st_mode & 0o100)


class RemoteVerificationTests(unittest.TestCase):
    def test_parse_ls_remote_sha(self):
        self.assertEqual(parse_ls_remote_sha("abc123\trefs/heads/main\n"), "abc123")

    def test_parse_ls_remote_sha_missing_raises(self):
        with self.assertRaises(DefaultBranchVerificationFailed):
            parse_ls_remote_sha("")

    def test_unchanged_default_branch_passes(self):
        def run(cmd, *, cwd=None, check=True):
            return FakeResult(stdout="abc123\trefs/heads/main\n")

        assert_remote_default_unchanged(
            run, Path("."), "main", "abc123", context="agent run"
        )

    def test_default_branch_mutation_is_detected(self):
        def run(cmd, *, cwd=None, check=True):
            return FakeResult(stdout="def456\trefs/heads/main\n")

        with self.assertRaisesRegex(DefaultBranchMutationDetected, "moved from abc123"):
            assert_remote_default_unchanged(
                run, Path("."), "main", "abc123", context="agent run"
            )

    def test_unverifiable_default_branch_fails_closed(self):
        def run(cmd, *, cwd=None, check=True):
            return FakeResult(returncode=128, stdout="fatal: could not read remote\n")

        with self.assertRaises(DefaultBranchVerificationFailed):
            assert_remote_default_unchanged(
                run, Path("."), "main", "abc123", context="agent run"
            )


if __name__ == "__main__":
    unittest.main()
