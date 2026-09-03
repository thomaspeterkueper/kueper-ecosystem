import importlib.util
import json
import pathlib
import tempfile
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("merge_gate.py")
spec = importlib.util.spec_from_file_location("merge_gate", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

PROPOSED = "Status: proposed  \nDatum: 2026-08-29  \n"
ACCEPTED = "Status: accepted  \nDatum: 2026-08-29  \n"

SCHEMA_WITH_BW = json.dumps({
    "properties": {
        "id": {"pattern": "^EXT-(ECO|BW)-[0-9]{8}-[0-9]{3}$"},
        "source": {"enum": ["ECO", "BW"]},
        "target": {"enum": ["ECO", "BW"]},
        "affects": {"items": {"enum": ["ECO", "BW"]}},
    }
})
SCHEMA_WITHOUT_BW = json.dumps({
    "properties": {
        "id": {"pattern": "^EXT-ECO-[0-9]{8}-[0-9]{3}$"},
        "source": {"enum": ["ECO"]},
        "target": {"enum": ["ECO"]},
        "affects": {"items": {"enum": ["ECO"]}},
    }
})
REGISTRY_WITH_BW = json.dumps({
    "projects": [{"id": "ecosystem", "code": "ECO"}, {"id": "buecherwelten", "code": "BW", "enabled": False}]
})
REGISTRY_WITHOUT_BW = json.dumps({
    "projects": [{"id": "ecosystem", "code": "ECO"}]
})


def make_root(decisions=PROPOSED, schema=SCHEMA_WITH_BW, lint_bw=True,
              code_table_bw=True, registry=REGISTRY_WITH_BW):
    root = tempfile.mkdtemp()
    d = pathlib.Path(root)
    (d / "decisions").mkdir()
    (d / "schemas").mkdir()
    (d / "tools").mkdir()
    (d / "registry").mkdir()
    (d / "decisions" / "ECO-ARC-0030-2026-DE.md").write_text(decisions, encoding="utf-8")
    (d / "decisions" / "ECO-ARC-0031-2026-DE.md").write_text(decisions, encoding="utf-8")
    (d / "schemas" / "external-task.schema.json").write_text(schema, encoding="utf-8")
    (d / "tools" / "lint-external-tasks").mkdir()
    lint = 'CODES = {"ECO", "BW"}\n' if lint_bw else 'CODES = {"ECO"}\n'
    (d / "tools" / "lint-external-tasks" / "lint.py").write_text(lint, encoding="utf-8")
    (d / "decisions" / "ECO-ARC-0006-2026-DE.md").write_text(
        "| `ECO` | `kueper-ecosystem` |\n| `BW` | `buecherwelten` |\n" if code_table_bw
        else "| `ECO` | `kueper-ecosystem` |\n",
        encoding="utf-8",
    )
    (d / "registry" / "projects.json").write_text(registry, encoding="utf-8")
    return root


class MergeGateTests(unittest.TestCase):
    def test_blocked_while_decisions_proposed(self):
        root = make_root(decisions=PROPOSED)
        self.assertFalse(mod.decisions_accepted(root))
        self.assertTrue(mod.governed_bw_present(root))
        self.assertEqual(mod.main([root]), 1)

    def test_allowed_once_decisions_accepted(self):
        root = make_root(decisions=ACCEPTED)
        self.assertTrue(mod.decisions_accepted(root))
        self.assertTrue(mod.governed_bw_present(root))
        self.assertEqual(mod.main([root]), 0)

    def test_unrelated_branch_not_blocked(self):
        root = make_root(
            decisions=PROPOSED,
            schema=SCHEMA_WITHOUT_BW,
            lint_bw=False,
            code_table_bw=False,
            registry=REGISTRY_WITHOUT_BW,
        )
        self.assertFalse(mod.decisions_accepted(root))
        self.assertFalse(mod.governed_bw_present(root))
        self.assertEqual(mod.main([root]), 0)

    def test_missing_decision_file_counts_as_not_accepted(self):
        root = make_root(decisions=PROPOSED)
        pathlib.Path(root, "decisions", "ECO-ARC-0031-2026-DE.md").unlink()
        self.assertFalse(mod.decisions_accepted(root))
        self.assertEqual(mod.main([root]), 1)

    def test_registry_entry_alone_triggers_gate(self):
        # Nur der Registry-Eintrag (ohne Schema/Linter/Code-Tabelle) sperrt ebenfalls.
        root = make_root(
            decisions=PROPOSED,
            schema=SCHEMA_WITHOUT_BW,
            lint_bw=False,
            code_table_bw=False,
        )
        self.assertTrue(mod.governed_bw_present(root))
        self.assertEqual(mod.main([root]), 1)


if __name__ == "__main__":
    unittest.main()
