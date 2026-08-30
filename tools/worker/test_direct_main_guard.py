#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Worker modules import their siblings as top-level modules (agent_worker,
# direct_main_guard) after inserting tools/worker into sys.path. The tests must
# resolve the same module objects so exception classes stay identical.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_worker as worker  # noqa: E402
import agent_worker_v74 as v74  # noqa: E402
from direct_main_guard import (  # noqa: E402
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

    def _drive_v74_repo_task(self, repo: str, base_task) -> tuple[dict, list]:
        """Run v74.repo_task with a stubbed base task and a recording worker.run.

        The V7.4 wrapper installs its guard and credential handling around every
        command the base task issues, so the returned call log exposes exactly
        what the coding agent would receive.
        """
        calls: list[tuple[list[str], dict]] = []

        def recording_run(cmd, *args, **kwargs):
            calls.append((list(cmd), dict(kwargs)))
            if cmd[:4] == ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]:
                return subprocess.CompletedProcess(cmd, 0, "origin/main\n")
            if cmd[:3] == ["git", "show", "--name-only", "--format="]:
                return subprocess.CompletedProcess(
                    cmd, 0, "tools/worker/test_direct_main_guard.py\n"
                )
            return subprocess.CompletedProcess(cmd, 0, "")

        original_run = worker.run
        original_base = v74._BASE_REPO_TASK
        worker.run = recording_run
        v74._BASE_REPO_TASK = base_task
        try:
            result = v74.repo_task({"repository": repo, "type": "REVIEW_FIX"}, "deepseek-v4-flash")
        finally:
            worker.run = original_run
            v74._BASE_REPO_TASK = original_base
        return result, calls

    def test_agent_claude_run_withholds_github_credentials_and_resets_origin(self):
        """credential_aware_run strips GitHub mutation tokens from the coding
        agent env and resets origin to an unauthenticated URL before claude."""
        repo = "acme/kueper-ecosystem"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()

            def base_task(task, model):
                agent_env = {
                    "PATH": "/usr/bin",
                    "DEEPSEEK_API_KEY": "test-deepseek",
                    "KUEPER_BOT_TOKEN": "bot",
                    "KUEPER_WORKFLOW_TOKEN": "wf",
                    "GH_TOKEN": "gh",
                    "GITHUB_TOKEN": "ght",
                }
                worker.run(
                    ["claude", "-p", "--dangerously-skip-permissions", "implement task"],
                    cwd=root,
                    env=agent_env,
                    check=False,
                )
                return {"kind": "completed", "summary": "ok"}

            _, calls = self._drive_v74_repo_task(repo, base_task)
            hook_installed = (root / ".git" / "hooks" / "pre-push").is_file()

        claude_calls = [kwargs for cmd, kwargs in calls if cmd[:1] == ["claude"]]
        self.assertEqual(len(claude_calls), 1)
        agent_env = claude_calls[0]["env"]
        for secret in ("KUEPER_BOT_TOKEN", "KUEPER_WORKFLOW_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
            self.assertNotIn(secret, agent_env)
        self.assertEqual(agent_env["PATH"], "/usr/bin")
        self.assertEqual(agent_env["DEEPSEEK_API_KEY"], "test-deepseek")
        self.assertEqual(claude_calls[0]["cwd"], root)
        self.assertIn(
            ["git", "remote", "set-url", "origin", f"https://github.com/{repo}.git"],
            [cmd for cmd, _ in calls],
        )
        self.assertTrue(hook_installed)

    def test_draft_ready_failure_cannot_be_replaced_by_default_branch_write(self):
        """Draft-PR + Ready/Merge unavailable => no default-branch content mutation.

        The worker path itself (v74.credential_aware_run) is fail closed: the
        coding agent receives no GitHub credentials, origin stays unauthenticated,
        and every push to refs/heads/main is rejected before it reaches the
        underlying runner. Only the PR-head update remains writable.
        """
        repo = "acme/kueper-ecosystem"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()

            def base_task(task, model):
                # REVIEW_FIX flow: check out the existing PR head branch first.
                worker.run(
                    ["git", "checkout", "-B", "review/fix-123", "origin/review/fix-123"],
                    cwd=root,
                )
                # Coding agent run carrying the worker's environment (tokens present).
                agent_env = {
                    "PATH": "/usr/bin",
                    "DEEPSEEK_API_KEY": "test-deepseek",
                    "KUEPER_BOT_TOKEN": "test-bot-token",
                    "KUEPER_WORKFLOW_TOKEN": "test-workflow-token",
                    "GH_TOKEN": "test-gh-token",
                    "GITHUB_TOKEN": "test-github-token",
                }
                worker.run(
                    ["claude", "-p", "--dangerously-skip-permissions", "apply review fixes"],
                    cwd=root,
                    env=agent_env,
                    check=False,
                )
                # Ready/Merge is unavailable (draft PR stays open): every default-branch
                # merge substitute must be rejected on the worker path itself.
                for refspec in ("HEAD:main", "HEAD:refs/heads/main", "main", "refs/heads/main"):
                    with self.assertRaises(DefaultBranchMutationBlocked):
                        worker.run(["git", "push", "origin", refspec], cwd=root)
                # --no-verify bypasses the pre-push hook but not the wrapper check.
                with self.assertRaises(DefaultBranchMutationBlocked):
                    worker.run(["git", "push", "--no-verify", "origin", "HEAD:main"], cwd=root)
                # The intended PR-head update stays writable.
                worker.run(["git", "push", "--quiet", "origin", "HEAD:review/fix-123"], cwd=root)
                return {"kind": "completed", "summary": "simulated review fix"}

            with mock.patch.dict(
                os.environ,
                {"KUEPER_BOT_TOKEN": "test-bot-token", "KUEPER_WORKFLOW_TOKEN": "test-workflow-token"},
            ):
                result, calls = self._drive_v74_repo_task(repo, base_task)
                hook_installed = (root / ".git" / "hooks" / "pre-push").is_file()

        self.assertEqual(result["summary"], "simulated review fix")

        # The coding agent process received no GitHub mutation credentials,
        # while non-credential environment entries were preserved.
        claude_calls = [kwargs for cmd, kwargs in calls if cmd[:1] == ["claude"]]
        self.assertEqual(len(claude_calls), 1)
        for secret in ("KUEPER_BOT_TOKEN", "KUEPER_WORKFLOW_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
            self.assertNotIn(secret, claude_calls[0]["env"])
        self.assertEqual(claude_calls[0]["env"]["DEEPSEEK_API_KEY"], "test-deepseek")

        # Origin was reset to the unauthenticated URL before the agent ran.
        self.assertIn(
            ["git", "remote", "set-url", "origin", f"https://github.com/{repo}.git"],
            [cmd for cmd, _ in calls],
        )
        # The fail-closed pre-push guard is installed in the worker clone.
        self.assertTrue(hook_installed)

        # Default-branch pushes never reached the underlying runner; only the
        # PR-head push was executed, after the worker restored the authenticated
        # origin at the controlled push boundary.
        pushed = [cmd for cmd, _ in calls if len(cmd) >= 4 and cmd[:2] == ["git", "push"]]
        self.assertEqual(pushed, [["git", "push", "--quiet", "origin", "HEAD:review/fix-123"]])
        restored = [
            cmd
            for cmd, _ in calls
            if cmd[:4] == ["git", "remote", "set-url", "origin"]
            and cmd[4].startswith("https://x-access-token:")
        ]
        self.assertEqual(
            restored,
            [["git", "remote", "set-url", "origin", "https://x-access-token:test-bot-token@github.com/acme/kueper-ecosystem.git"]],
        )
        self.assertIn(["git", "show", "--name-only", "--format=", "HEAD"], [cmd for cmd, _ in calls])


if __name__ == "__main__":
    unittest.main()
