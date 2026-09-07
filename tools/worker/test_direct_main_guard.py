#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
    def test_default_branch_is_blocked(self):
        with self.assertRaises(DefaultBranchMutationBlocked):
            validate_push_lines("main", "refs/heads/work abc refs/heads/main 000\n")
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_push_target("main", "HEAD:main")
        with self.assertRaises(DefaultBranchMutationBlocked):
            assert_push_target("main", "HEAD:refs/heads/main")

    def test_pr_branch_is_allowed(self):
        validate_push_lines("main", "refs/heads/work abc refs/heads/review/fix 000\n")
        assert_push_target("main", "HEAD:review/fix")

    def test_installed_hook_rejects_default_branch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            hook = install_pre_push_guard(root, "main")
            result = subprocess.run(
                [str(hook), "origin", "unused"],
                input="refs/heads/work abc refs/heads/main 000\n",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 41)

    def test_v74_withholds_write_credentials_from_agent(self):
        calls = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            (root / ".git" / "hooks").mkdir(parents=True)

            def fake_run(cmd, *args, **kwargs):
                calls.append((list(cmd), dict(kwargs)))
                if cmd[:4] == ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]:
                    return subprocess.CompletedProcess(cmd, 0, "origin/main\n")
                if cmd[:3] == ["git", "show", "--name-only"]:
                    return subprocess.CompletedProcess(cmd, 0, "README.md\n")
                return subprocess.CompletedProcess(cmd, 0, "")

            def base_task(task, model):
                env = {
                    "DEEPSEEK_API_KEY": "deepseek",
                    "KUEPER_BOT_TOKEN": "bot",
                    "KUEPER_WORKFLOW_TOKEN": "workflow",
                    "GH_TOKEN": "gh",
                    "GITHUB_TOKEN": "github",
                }
                worker.run(["claude", "-p", "task"], cwd=root, env=env, check=False)
                with self.assertRaises(DefaultBranchMutationBlocked):
                    worker.run(["git", "push", "--no-verify", "origin", "HEAD:main"], cwd=root)
                return {"kind": "completed", "summary": "ok"}

            original_run = worker.run
            original_base = v74._BASE_REPO_TASK
            worker.run = fake_run
            v74._BASE_REPO_TASK = base_task
            try:
                with unittest.mock.patch.dict(os.environ, {"KUEPER_BOT_TOKEN": "bot", "KUEPER_WORKFLOW_TOKEN": "workflow"}):
                    result = v74.repo_task({"repository": "acme/repo"}, "deepseek-v4-flash")
            finally:
                worker.run = original_run
                v74._BASE_REPO_TASK = original_base

        self.assertEqual(result["summary"], "ok")
        claude_env = [kwargs["env"] for cmd, kwargs in calls if cmd and cmd[0] == "claude"][0]
        for name in ("KUEPER_BOT_TOKEN", "KUEPER_WORKFLOW_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
            self.assertNotIn(name, claude_env)
        self.assertEqual(claude_env["DEEPSEEK_API_KEY"], "deepseek")


if __name__ == "__main__":
    unittest.main()
