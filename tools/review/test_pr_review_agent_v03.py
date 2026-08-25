from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("pr_review_agent_v03.py")
spec = importlib.util.spec_from_file_location("pr_review_agent_v03", MODULE_PATH)
assert spec and spec.loader
reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviewer)


class ReviewStdinTransportTests(unittest.TestCase):
    def test_large_prompt_is_sent_via_stdin_not_argv(self):
        prompt = "X" * 500_000
        completed = subprocess.CompletedProcess(
            args=["claude", "-p", "--dangerously-skip-permissions"],
            returncode=0,
            stdout='{"verdict":"PASS","summary":"ok","findings":[]}',
        )
        with mock.patch.object(reviewer.subprocess, "run", return_value=completed) as run:
            got = reviewer.run_with_stdin(
                ["claude", "-p", "--dangerously-skip-permissions", prompt],
                cwd=Path("/tmp"),
                env={"EXAMPLE": "1"},
                check=False,
            )

        self.assertEqual(got.returncode, 0)
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["claude", "-p", "--dangerously-skip-permissions"])
        self.assertNotIn(prompt, args[0])
        self.assertEqual(kwargs["input"], prompt)
        self.assertTrue(kwargs["text"])
        self.assertEqual(kwargs["stderr"], subprocess.STDOUT)

    def test_failed_claude_call_preserves_worker_error_semantics(self):
        prompt = "review me"
        completed = subprocess.CompletedProcess(
            args=["claude", "-p", "--dangerously-skip-permissions"],
            returncode=7,
            stdout="provider failed",
        )
        with mock.patch.object(reviewer.subprocess, "run", return_value=completed):
            with self.assertRaises(reviewer.base.worker.WorkerError):
                reviewer.run_with_stdin(
                    ["claude", "-p", "--dangerously-skip-permissions", prompt],
                    check=True,
                )


if __name__ == "__main__":
    unittest.main()
