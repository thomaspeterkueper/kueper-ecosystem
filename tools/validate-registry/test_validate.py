from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("registry_validate", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "project-registry.schema.json"
REGISTRY_PATH = REPO_ROOT / "registry" / "projects.json"

COLLECT_PATH = REPO_ROOT / "tools" / "collector" / "collect.py"
COLLECT_SPEC = importlib.util.spec_from_file_location("collect", COLLECT_PATH)
assert COLLECT_SPEC and COLLECT_SPEC.loader
COLLECT = importlib.util.module_from_spec(COLLECT_SPEC)
COLLECT_SPEC.loader.exec_module(COLLECT)


def registry_with(projects):
    return {
        "$schema": "../schemas/project-registry.schema.json",
        "schema_version": "1.0.0",
        "updated_at": "2026-08-31",
        "projects": projects,
    }


def standard_project(**overrides):
    project = {
        "id": "example",
        "name": "Example",
        "repository": "owner/example",
        "provider": "github",
        "enabled": True,
        "role": "application",
        "version_source": {
            "strategy": "first-existing",
            "candidates": [{"type": "package-json", "path": "package.json"}],
        },
        "governance": {"required_paths": ["README.md"]},
    }
    project.update(overrides)
    return project


def private_source(**overrides):
    project = standard_project(
        repository_class="private-manuscript-source",
        data_sensitivity="confidential-authoring",
        permissions={
            "ingest": True,
            "derived_analysis": True,
            "canonization": False,
            "public_export": False,
            "cross_repository_routing": False,
        },
    )
    project.update(overrides)
    return project


def private_permissions(**changes):
    perms = private_source()["permissions"]
    perms.update(changes)
    return perms


class ProjectRegistrySchemaTests(unittest.TestCase):
    def errors(self, projects):
        return VALIDATE.validate_document(registry_with(projects), SCHEMA_PATH)

    def mentions(self, errors, needle):
        return any(needle in f"{path}: {msg}" for path, msg in errors)

    def test_compliant_standard_project(self):
        self.assertEqual(self.errors([standard_project()]), [])

    def test_compliant_private_manuscript_source(self):
        self.assertEqual(self.errors([private_source()]), [])

    def test_private_source_rejects_public_export(self):
        errors = self.errors([private_source(permissions=private_permissions(public_export=True))])
        self.assertTrue(self.mentions(errors, "public_export"), errors)

    def test_private_source_rejects_canonization(self):
        errors = self.errors([private_source(permissions=private_permissions(canonization=True))])
        self.assertTrue(self.mentions(errors, "canonization"), errors)

    def test_private_source_rejects_cross_repository_routing(self):
        errors = self.errors(
            [private_source(permissions=private_permissions(cross_repository_routing=True))]
        )
        self.assertTrue(self.mentions(errors, "cross_repository_routing"), errors)

    def test_private_source_requires_permissions(self):
        project = private_source()
        del project["permissions"]
        errors = self.errors([project])
        self.assertTrue(self.mentions(errors, "permissions"), errors)

    def test_private_source_requires_data_sensitivity(self):
        project = private_source()
        del project["data_sensitivity"]
        errors = self.errors([project])
        self.assertTrue(self.mentions(errors, "data_sensitivity"), errors)

    def test_private_source_rejects_public_sensitivity(self):
        errors = self.errors([private_source(data_sensitivity="public")])
        self.assertTrue(self.mentions(errors, "confidential-authoring"), errors)

    def test_existing_registry_entries_remain_valid(self):
        # Rueckwaertskompatibilitaet: alle bestehenden 1.0.0-Eintraege (ohne die
        # neuen 1.1-Felder) muessen weiterhin gueltig sein. Deckt auch ab, dass
        # das $schema-Metafeld des Dokuments vom Schema akzeptiert wird.
        self.assertEqual(VALIDATE.validate_file(REGISTRY_PATH, SCHEMA_PATH), [])


class CollectorRegistryValidationTests(unittest.TestCase):
    def test_collector_accepts_current_registry(self):
        # Muss ohne GH_TOKEN laufen: Validierung geschieht vor dem Token-Check.
        COLLECT._validate_registry()

    def test_collector_stops_on_invalid_registry(self):
        invalid = registry_with(
            [private_source(permissions=private_permissions(public_export=True))]
        )
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            import json as _json

            _json.dump(invalid, f)
            tmp_path = f.name
        try:
            old_path = COLLECT.REG_PATH
            COLLECT.REG_PATH = tmp_path
            try:
                with self.assertRaises(SystemExit) as cm:
                    COLLECT._validate_registry()
                self.assertEqual(cm.exception.code, 1)
            finally:
                COLLECT.REG_PATH = old_path
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
