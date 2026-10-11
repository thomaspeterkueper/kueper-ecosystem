import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("sweep.py")
spec = importlib.util.spec_from_file_location("governance_sweep", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
# dataclasses resolves cls.__module__ via sys.modules during exec_module.
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

TASK_TEMPLATE = """---
id: {tid}
title: Beispielaufgabe
status: open
source: {source}
target: {target}
created: 2026-09-25
requested_by: T.P.K.
priority: low
affects: [ECO]
---

# {tid} — Beispielaufgabe

## Anlass

Beispiel.
"""


def task(tid, source, target):
    return TASK_TEMPLATE.format(tid=tid, source=source, target=target)


class StubGitHub:
    """Minimal GitHub stand-in: one repository with a fixed file listing."""

    def __init__(self, files):
        self.files = files
        self.requested = []

    def get(self, path):
        return 200, {"default_branch": "main"}

    def contents(self, repo, path, ref):
        if path == "external-tasks/open":
            return [{"name": name, "path": f"external-tasks/open/{name}"} for name in self.files]
        return None

    def text(self, repo, path, ref):
        return self.files.get(path.split("/")[-1])


REGISTRY = {
    "projects": [
        {
            "id": "ecosystem",
            "repository": "thomaspeterkueper/kueper-ecosystem",
            "enabled": True,
            "provider": "github",
        },
    ],
}


class EcoAddressedTaskTests(unittest.TestCase):
    def sweep(self, files):
        result = mod.SweepResult(generated_at="test")
        mod.check_repositories(result, REGISTRY, StubGitHub(files))
        return result.findings

    def test_cross_project_task_addressed_to_eco_is_reported(self):
        name = "EXT-KUE-ECO-20260924-001.md"
        findings = self.sweep({name: task("EXT-KUE-ECO-20260924-001", "KUE", "ECO")})
        self.assertEqual([f.category for f in findings], ["task_addressed_to_eco"])
        self.assertIn(name, findings[0].message)

    def test_self_addressed_escalation_task_is_not_reported(self):
        # EXT-ECO-ECO-<date>-001 files are the sweep's own escalation artifacts;
        # reporting them escalated the previous run's escalation every day.
        findings = self.sweep(
            {"EXT-ECO-ECO-20260925-001.md": task("EXT-ECO-ECO-20260925-001", "ECO", "ECO")}
        )
        self.assertEqual(findings, [])

    def test_task_addressed_elsewhere_is_not_reported(self):
        findings = self.sweep(
            {"EXT-ECO-KG-20260920-001.md": task("EXT-ECO-KG-20260920-001", "ECO", "KG")}
        )
        self.assertEqual(findings, [])

    def test_mixed_listing_keeps_only_cross_project_task(self):
        files = {
            "EXT-ECO-ECO-20260925-001.md": task("EXT-ECO-ECO-20260925-001", "ECO", "ECO"),
            "EXT-ECO-ECO-20260926-001.md": task("EXT-ECO-ECO-20260926-001", "ECO", "ECO"),
            "EXT-ENG-ECO-20261002-kueper-products-bootstrap.md": task(
                "EXT-ENG-ECO-20261002-001", "ENG", "ECO"
            ),
        }
        findings = self.sweep(files)
        self.assertEqual(len(findings), 1)
        self.assertIn("EXT-ENG-ECO-20261002-kueper-products-bootstrap.md", findings[0].message)


class IsEcoAddressedTaskTests(unittest.TestCase):
    def test_target_eco_other_source(self):
        self.assertTrue(mod.is_eco_addressed_task(task("EXT-NXU-ECO-20260921-001", "NXU", "ECO")))

    def test_self_addressed_is_excluded(self):
        self.assertFalse(mod.is_eco_addressed_task(task("EXT-ECO-ECO-20260925-001", "ECO", "ECO")))

    def test_other_target_is_excluded(self):
        self.assertFalse(mod.is_eco_addressed_task(task("EXT-ECO-KG-20260920-001", "ECO", "KG")))

    def test_missing_target_is_excluded(self):
        self.assertFalse(mod.is_eco_addressed_task("# Not a task file\n"))


if __name__ == "__main__":
    unittest.main()
