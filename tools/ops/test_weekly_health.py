"""Tests für die Auswertelogik von weekly_health.py – ohne Netzaufrufe."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import weekly_health as wh  # noqa: E402

NOW = datetime(2026, 11, 16, 6, 0, tzinfo=timezone.utc)


def run(name, created, conclusion, status="completed"):
    return {"name": name, "created_at": created, "conclusion": conclusion, "status": status}


class WorkflowTests(unittest.TestCase):
    def test_rate_ignores_cancelled_and_running(self):
        stats = wh.workflow_stats([
            run("CI", "2026-11-10T00:00:00Z", "success"),
            run("CI", "2026-11-11T00:00:00Z", "failure"),
            run("CI", "2026-11-12T00:00:00Z", "cancelled"),
            run("CI", "2026-11-13T00:00:00Z", None, status="in_progress"),
        ], NOW)
        self.assertEqual(stats["CI"]["runs"], 2)
        self.assertEqual(stats["CI"]["rate"], 0.5)

    def test_longest_red_phase_closed_by_success(self):
        stats = wh.workflow_stats([
            run("CI", "2026-11-10T00:00:00Z", "failure"),
            run("CI", "2026-11-10T06:00:00Z", "failure"),
            run("CI", "2026-11-10T12:00:00Z", "success"),
        ], NOW)
        self.assertEqual(stats["CI"]["longest_red_hours"], 12.0)
        self.assertFalse(stats["CI"]["red_now"])

    def test_open_red_phase_runs_until_now(self):
        stats = wh.workflow_stats([
            run("CI", "2026-11-15T06:00:00Z", "success"),
            run("CI", "2026-11-16T00:00:00Z", "startup_failure"),
        ], NOW)
        self.assertEqual(stats["CI"]["longest_red_hours"], 6.0)
        self.assertTrue(stats["CI"]["red_now"])


class AgeTests(unittest.TestCase):
    def test_pr_buckets(self):
        result = wh.pr_age_buckets([
            {"created_at": "2026-11-15T00:00:00Z"},
            {"created_at": "2026-11-01T00:00:00Z"},
            {"created_at": "2026-09-30T00:00:00Z"},
        ], NOW)
        self.assertEqual(result["buckets"], {"0-7": 1, "8-30": 1, ">30": 1})
        self.assertEqual(result["oldest"], "2026-09-30")

    def test_task_buckets_from_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name, created in (("A", "2026-11-14"), ("B", "2026-09-01"), ("C", None)):
                path = os.path.join(tmp, f"{name}.md")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("---\nid: X\n" + (f"created: {created}\n" if created else "") + "---\n")
                paths.append(path)
            result = wh.task_age_buckets(paths, NOW)
        self.assertEqual(result["buckets"]["0-7"], 1)
        self.assertEqual(result["buckets"][">30"], 1)
        self.assertEqual(result["unknown"], 1)
        self.assertEqual(result["over_limit"], ["B"])


class QueueTests(unittest.TestCase):
    def test_failure_reason_skips_agent_noise(self):
        item = {"last_error": "agent-with-exa: falling back to the existing research agent without Exa\n"
                              "\"deepseek-v4-flash\" isn't described by this version's model catalog\n"
                              "API Error: 402 Insufficient Balance\n"}
        self.assertEqual(wh.failure_reason(item), "API Error: 402 Insufficient Balance")

    def test_failure_reason_normalises_ids(self):
        item = {"validation_summary": "queued item RES-20260823-7E477B58 requires source_path"}
        self.assertEqual(wh.failure_reason(item), "queued item RES-… requires source_path")
        self.assertIsNone(wh.failure_reason({}))

    def test_queue_stats(self):
        items = [
            {"status": "needs-review", "evidence_profile": "philosophy-comparative", "created": "2026-11-12",
             "validation_summary": "candidate lacks a strong source type marker"},
            {"status": "needs-review", "evidence_profile": "philosophy-comparative", "created": "2026-11-11",
             "validation_summary": "candidate lacks a strong source type marker"},
            {"status": "candidate-pr", "evidence_profile": "philosophy-comparative", "created": "2026-11-03"},
            {"status": "queued", "created": "2026-07-01"},
        ]
        stats = wh.queue_stats(items, NOW)
        self.assertEqual(stats["status"]["needs-review"], 2)
        self.assertEqual(stats["top_reasons"][0], {"reason": "candidate lacks a strong source type marker", "count": 2})
        self.assertEqual(stats["needs_review_by_profile"]["philosophy-comparative"]["share"], 0.667)
        self.assertEqual(stats["newest_entry"], "2026-11-12")
        self.assertNotIn("2026-W27", stats["created_per_week"])  # älter als 8 Wochen


class FindingTests(unittest.TestCase):
    def snapshot(self):
        return {
            "generated_at": "2026-11-16T06:00:00+00:00",
            "repos": {"o/r": {
                "workflows": {
                    "Rot": {"runs": 10, "success": 5, "rate": 0.5, "longest_red_hours": 30.0, "red_now": True},
                    "Wenig": {"runs": 2, "success": 0, "rate": 0.0, "longest_red_hours": 1.0, "red_now": True},
                    "Grün": {"runs": 10, "success": 9, "rate": 0.9, "longest_red_hours": 1.0, "red_now": False},
                },
                "summary": {"runs": 22, "success": 14, "rate": 0.636},
                "pull_requests": {"buckets": {"0-7": 1, "8-30": 0, ">30": 4}, "total": 5, "oldest": "2026-09-01"},
                "branches": 120,
            }},
            "external_tasks": {"buckets": {"0-7": 0, "8-30": 0, ">30": 1}, "unknown": 0, "total": 1,
                               "over_limit": ["EXT-X"]},
            "research_queue": {"total": 3, "status": {"needs-review": 3}, "top_reasons": [],
                               "created_per_week": {}, "newest_entry": "2026-11-12",
                               "needs_review_by_profile": {
                                   "p": {"items": 5, "needs_review": 3, "share": 0.6},
                                   "klein": {"items": 2, "needs_review": 2, "share": 1.0}}},
        }

    def test_thresholds(self):
        found = wh.findings(self.snapshot())
        kinds = [f["kind"] for f in found]
        self.assertEqual(sorted(kinds), ["pr", "profile", "tasks", "workflow"])
        self.assertTrue(any("Rot" in f["text"] for f in found))
        self.assertFalse(any("Wenig" in f["text"] or "klein" in f["text"] for f in found))
        self.assertEqual(found[0]["kind"], "workflow")  # rot und derzeit rot → am schwersten

    def test_markdown_with_previous_and_max_three_suggestions(self):
        snap = self.snapshot()
        snap["findings"] = wh.findings(snap)
        previous = json.loads(json.dumps(snap))
        previous["generated_at"] = "2026-11-09T06:00:00+00:00"
        previous["repos"]["o/r"]["branches"] = 100
        md = wh.render_markdown(snap, previous)
        self.assertIn("dem Bericht vom 2026-11-09", md)
        self.assertIn("120 ↑", md)
        section = md.split("## Was als Nächstes dran ist")[1].split("##")[0]
        self.assertEqual(sum(1 for ln in section.splitlines() if ln[:2] in ("1.", "2.", "3.", "4.")), 3)
        self.assertIn("Task-Bus", md)

    def test_markdown_without_github(self):
        snap = self.snapshot()
        snap["repos"] = {}
        snap["github_note"] = "kein Token"
        snap["findings"] = wh.findings(snap)
        md = wh.render_markdown(snap, None)
        self.assertIn("Nicht erhoben: kein Token", md)
        self.assertIn("noch keine vorhanden", md)

    def test_arrow(self):
        self.assertEqual(wh.arrow(2, 1), " ↑")
        self.assertEqual(wh.arrow(1, 2), " ↓")
        self.assertEqual(wh.arrow(1, 1), " →")
        self.assertEqual(wh.arrow(1, None), "")


class MainTests(unittest.TestCase):
    def test_offline_run_writes_report_and_maintains_alert(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "registry"))
            os.makedirs(os.path.join(root, "external-tasks", "open"))
            os.makedirs(os.path.join(root, "research", "queue"))
            with open(os.path.join(root, "registry", "projects.json"), "w") as fh:
                json.dump({"projects": [{"repository": "o/r", "enabled": True}]}, fh)
            with open(os.path.join(root, "external-tasks", "open", "EXT-A.md"), "w") as fh:
                fh.write("---\ncreated: 2026-01-01\n---\n")
            md = os.path.join(root, "status", "h.md")
            js = os.path.join(root, "status", "h.json")
            alert = os.path.join(root, "external-tasks", "open", "ECO-OPS-health-alert.md")
            args = ["--root", root, "--out-md", md, "--out-json", js, "--alert-file", alert, "--no-github"]
            self.assertEqual(wh.main(args), 0)
            self.assertTrue(os.path.exists(alert))
            with open(alert, encoding="utf-8") as fh:
                self.assertIn("id: ECO-OPS-health-alert", fh.read())
            os.remove(os.path.join(root, "external-tasks", "open", "EXT-A.md"))
            self.assertEqual(wh.main(args), 0)
            self.assertFalse(os.path.exists(alert))
            with open(md, encoding="utf-8") as fh:
                self.assertIn("Pfeile vergleichen mit dem Bericht vom", fh.read())


if __name__ == "__main__":
    unittest.main()
