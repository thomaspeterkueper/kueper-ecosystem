import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("ingest_external_tasks.py")
spec = importlib.util.spec_from_file_location("ingest_external_tasks", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class IngestExternalTasksTests(unittest.TestCase):
    def test_frontmatter_and_sections(self):
        text = """---
id: EXT-SSF-KG-20260821-001
status: open
source: SSF
target: KG
priority: high
---
# Example

## Anlass
Need canonical data.

## Gewünschte Änderung
Add the records.

## Erwartetes Ergebnis
KXF export exists.
"""
        fm = mod.frontmatter(text)
        self.assertEqual(fm["source"], "SSF")
        self.assertEqual(fm["target"], "KG")
        self.assertEqual(mod.section(text, "Gewünschte Änderung"), "Add the records.")
        self.assertEqual(mod.title(text), "Example")

    def test_legacy_heading_task(self):
        text = """# SSF-0001 — Magnetismus

## Herkunft
Solar Science Foundation

## Ziel
Create canonical KG records.

## KXF-Anforderung
Export eight learning modules.
"""
        self.assertEqual(mod.frontmatter(text), {})
        self.assertEqual(mod.section(text, "Herkunft"), "Solar Science Foundation")
        self.assertEqual(mod.section(text, "Ziel"), "Create canonical KG records.")

    def test_resolve_project_code_and_name(self):
        by_id = {
            "ssf": {"id": "ssf", "name": "Solar Science Foundation", "repository": "x/solarsciencefoundation"},
            "knowledge-graph": {"id": "knowledge-graph", "name": "KUEPER Knowledge Graph", "repository": "x/kueper-knowledge-graph"},
        }
        self.assertEqual(mod.resolve_project("SSF", "ecosystem", by_id), "ssf")
        self.assertEqual(mod.resolve_project("Solar Science Foundation", "ecosystem", by_id), "ssf")
        self.assertEqual(mod.resolve_project("KG", "ecosystem", by_id), "knowledge-graph")


if __name__ == "__main__":
    unittest.main()
