import importlib.util
import datetime as dt
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("check_health.py")
spec = importlib.util.spec_from_file_location("check_health", MODULE_PATH)
check_health = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(check_health)

NOW = dt.datetime(2026, 8, 29, 16, 19, 0, tzinfo=dt.timezone.utc)


def iso(minute: int, hour: int = 16) -> str:
    return dt.datetime(2026, 8, 29, hour, minute, 0, tzinfo=dt.timezone.utc).isoformat()


def run(created_at: str, event: str = "workflow_dispatch", status: str = "completed", conclusion: str = "success"):
    return {"created_at": created_at, "event": event, "status": status, "conclusion": conclusion}


class SlotComputationTests(unittest.TestCase):
    def test_quarter_hour_slots(self):
        slots = check_health.recent_slots(set(range(0, 60, 15)), NOW, 4)
        self.assertEqual(
            [slot.strftime("%H:%M") for slot in slots], ["16:15", "16:00", "15:45", "15:30"]
        )

    def test_review_slots(self):
        slots = check_health.recent_slots({7, 22, 37, 52}, NOW, 4)
        self.assertEqual(
            [slot.strftime("%H:%M") for slot in slots], ["16:07", "15:52", "15:37", "15:22"]
        )

    def test_skips_future_slots(self):
        now = dt.datetime(2026, 8, 29, 16, 2, 0, tzinfo=dt.timezone.utc)
        slots = check_health.recent_slots(set(range(0, 60, 15)), now, 4)
        self.assertEqual(
            [slot.strftime("%H:%M") for slot in slots], ["16:00", "15:45", "15:30", "15:15"]
        )


class GithubWorkerEvaluationTests(unittest.TestCase):
    def test_healthy_when_recent_slots_covered(self):
        runs = [
            run(iso(15)),  # covers 16:15 slot
            run(iso(0)),
            run(iso(45, hour=15)),
            run(iso(30, hour=15)),
        ]
        result = check_health.evaluate_github_worker("agent-worker-v7", runs, NOW)
        self.assertEqual(result["verdict"], "healthy")
        self.assertEqual(result["slots_covered"], 4)
        self.assertEqual(result["consecutive_slots_covered"], 4)

    def test_stale_when_no_runs(self):
        result = check_health.evaluate_github_worker("agent-worker-v7", [], NOW)
        self.assertEqual(result["verdict"], "stale")
        self.assertEqual(result["slots_covered"], 0)
        self.assertIsNone(result["latest_run_at"])

    def test_stale_when_runs_too_old(self):
        old = dt.datetime(2026, 8, 29, 13, 0, 0, tzinfo=dt.timezone.utc).isoformat()
        result = check_health.evaluate_github_worker("agent-worker-v7", [run(old)], NOW)
        self.assertEqual(result["verdict"], "stale")

    def test_cancelled_run_still_covers_slot(self):
        # A cancelled run proves the trigger source fired for that slot.
        runs = [run(iso(15), status="completed", conclusion="cancelled"), run(iso(0))]
        result = check_health.evaluate_github_worker("agent-worker-v7", runs, NOW)
        self.assertEqual(result["verdict"], "healthy")
        self.assertEqual(result["slots_covered"], 2)

    def test_two_consecutive_slots_but_stale_latest(self):
        # Only old slots covered: newest covered slot is 15:45, gap to now too large.
        runs = [run(iso(45, hour=15)), run(iso(30, hour=15))]
        result = check_health.evaluate_github_worker("agent-worker-v7", runs, NOW)
        self.assertEqual(result["verdict"], "stale")
        self.assertEqual(result["slots_covered"], 2)
        self.assertEqual(result["consecutive_slots_covered"], 0)

    def test_late_schedule_run_within_slot_window(self):
        # GitHub fired the 16:00 */15 cron six minutes late; still inside
        # [16:00, 16:15) and therefore covers that slot.
        runs = [run(iso(15), event="workflow_dispatch"), run(iso(6), event="schedule")]
        result = check_health.evaluate_github_worker("agent-worker-v7", runs, NOW)
        self.assertEqual(result["verdict"], "healthy")
        self.assertEqual(result["last_schedule_run_at"], iso(6))

    def test_review_worker_slots(self):
        runs = [run(iso(7)), run(iso(52, hour=15)), run(iso(37, hour=15))]
        result = check_health.evaluate_github_worker("pr-review-agent", runs, NOW)
        self.assertEqual(result["verdict"], "healthy")
        self.assertEqual(result["slots_covered"], 3)


class SupabaseEvaluationTests(unittest.TestCase):
    def test_healthy_rows(self):
        with patch.object(
            check_health,
            "_rpc",
            return_value=[
                {"worker_name": "agent-worker-v7", "stale": False, "last_status": "succeeded"},
                {"worker_name": "pr-review-agent", "stale": False, "last_status": "succeeded"},
            ],
        ):
            results = check_health.evaluate_supabase_workers(["agent-worker-v7", "pr-review-agent"])
        self.assertTrue(all(r["verdict"] == "healthy" for r in results))

    def test_stale_row(self):
        with patch.object(
            check_health,
            "_rpc",
            return_value=[{"worker_name": "agent-worker-v7", "stale": True, "last_status": "failed"}],
        ):
            results = check_health.evaluate_supabase_workers(["agent-worker-v7", "pr-review-agent"])
        by_worker = {r["worker"]: r for r in results}
        self.assertEqual(by_worker["agent-worker-v7"]["verdict"], "stale")
        self.assertEqual(by_worker["pr-review-agent"]["verdict"], "stale")

    def test_missing_row_is_stale(self):
        with patch.object(check_health, "_rpc", return_value=[]):
            results = check_health.evaluate_supabase_workers(["agent-worker-v7"])
        self.assertEqual(results[0]["verdict"], "stale")


class MainFlowTests(unittest.TestCase):
    def test_github_backend_healthy_exit_zero(self):
        runs = [run(iso(15)), run(iso(0)), run(iso(45, hour=15))]
        argv = ["--backend", "github", "--worker", "agent-worker-v7", "--json"]
        with patch.object(check_health, "fetch_github_runs", return_value=runs), patch(
            "sys.argv", ["check_health.py", *argv]
        ), patch.dict(os.environ, {}, clear=True), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code = check_health.main()
        payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["verdict"], "healthy")
        self.assertEqual(payload["workers"][0]["worker"], "agent-worker-v7")

    def test_github_backend_stale_exit_one(self):
        with patch.object(check_health, "fetch_github_runs", return_value=[]), patch(
            "sys.argv", ["check_health.py", "--backend", "github", "--worker", "agent-worker-v7"]
        ), patch.dict(os.environ, {}, clear=True), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code = check_health.main()
        self.assertEqual(code, 1)
        self.assertIn("verdict: stale", stdout.getvalue())

    def test_transport_error_fails_closed(self):
        def boom(*args, **kwargs):
            raise RuntimeError("api unreachable")

        with patch.object(check_health, "fetch_github_runs", side_effect=boom), patch(
            "sys.argv", ["check_health.py", "--backend", "github", "--worker", "agent-worker-v7"]
        ), patch.dict(os.environ, {}, clear=True), patch("sys.stderr"):
            code = check_health.main()
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
