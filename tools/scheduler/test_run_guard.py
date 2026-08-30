import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("run_guard.py")
spec = importlib.util.spec_from_file_location("run_guard", MODULE_PATH)
run_guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(run_guard)


class SchedulerGuardTests(unittest.TestCase):
    def test_acquire_writes_positive_outputs(self):
        parser = run_guard.build_parser()
        args = parser.parse_args([
            "acquire", "--worker", "agent-worker-v7", "--source", "supabase",
            "--scheduler-run-id", "11111111-1111-1111-1111-111111111111"
        ])
        with tempfile.NamedTemporaryFile(delete=False) as output:
            output_path = output.name
        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": output_path}), patch.object(
                run_guard,
                "_rpc",
                return_value={
                    "acquired": True,
                    "run_id": "11111111-1111-1111-1111-111111111111",
                    "lease_token": "22222222-2222-2222-2222-222222222222",
                },
            ):
                self.assertEqual(run_guard.acquire(args), 0)
            text = Path(output_path).read_text(encoding="utf-8")
            self.assertIn("should_run=true", text)
            self.assertIn("scheduler_run_id=11111111-1111-1111-1111-111111111111", text)
            self.assertIn("lease_token=22222222-2222-2222-2222-222222222222", text)
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_acquire_writes_skip_outputs(self):
        parser = run_guard.build_parser()
        args = parser.parse_args(["acquire", "--worker", "pr-review-agent", "--source", "github_schedule"])
        with tempfile.NamedTemporaryFile(delete=False) as output:
            output_path = output.name
        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": output_path}), patch.object(
                run_guard,
                "_rpc",
                return_value={"acquired": False, "run_id": "33333333-3333-3333-3333-333333333333", "reason": "cooldown"},
            ):
                self.assertEqual(run_guard.acquire(args), 0)
            text = Path(output_path).read_text(encoding="utf-8")
            self.assertIn("should_run=false", text)
            self.assertIn("skip_reason=cooldown", text)
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_finish_maps_non_success_to_failed(self):
        parser = run_guard.build_parser()
        args = parser.parse_args([
            "finish", "--run-id", "11111111-1111-1111-1111-111111111111",
            "--lease-token", "22222222-2222-2222-2222-222222222222",
            "--status", "failure", "--github-run-id", "1234"
        ])
        with patch.object(run_guard, "_rpc", return_value=True) as rpc:
            self.assertEqual(run_guard.finish(args), 0)
        payload = rpc.call_args.args[1]
        self.assertEqual(payload["p_status"], "failed")
        self.assertEqual(payload["p_github_run_id"], 1234)


if __name__ == "__main__":
    unittest.main()
