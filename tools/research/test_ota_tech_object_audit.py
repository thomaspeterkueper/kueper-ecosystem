#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit-ota-tech-objects.py")
spec = importlib.util.spec_from_file_location("ota_tech_audit", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

DOC = '''---
signature: "OTA-TEC-0099-2026-DE"
series: "TEC"
objectId: test-object
contexts:
  - noxia
mappings:
  noxia:
    objectId: test-object
    role: buildable
---
# Test
'''


def write_fixture(root: Path, queue_item: dict | None = None) -> Path:
    ota = root / "ota"
    docs = ota / "src" / "content" / "documents"
    docs.mkdir(parents=True)
    doc = docs / "OTA-TEC-0099-2026-DE.md"
    doc.write_text(DOC, encoding="utf-8")
    queue = root / "queue"
    queue.mkdir()
    if queue_item is not None:
        (queue / "RES-test.json").write_text(json.dumps(queue_item), encoding="utf-8")
    return ota


def safe_item(blob: str) -> dict:
    return {
        "id": "RES-test",
        "source_project": "ota",
        "source_path": "src/content/documents/OTA-TEC-0099-2026-DE.md",
        "source_blob_sha": blob,
        "research_contract": "ota-tech-object-v1",
        "object_id": "test-object",
        "consumer_project": "noxia",
        "claim_classes": ["R", "H"],
        "consumer_impact_policy": {
            "flag_noxia_impact": True,
            "auto_update_noxia": False,
            "balancing_is_out_of_scope": True,
        },
    }


def test_uncovered() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ota = write_fixture(root)
        report = mod.audit(ota, root / "queue")
        assert report["counts"] == {"uncovered": 1}
        assert not report["metadata_errors"]
        assert not report["contract_errors"]


def test_covered() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ota = write_fixture(root)
        doc = ota / "src" / "content" / "documents" / "OTA-TEC-0099-2026-DE.md"
        (root / "queue" / "RES-test.json").write_text(
            json.dumps(safe_item(mod.git_blob_sha(doc))), encoding="utf-8"
        )
        report = mod.audit(ota, root / "queue")
        assert report["counts"] == {"covered": 1}
        assert report["objects"][0]["current_research_ids"] == ["RES-test"]


def test_stale() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ota = write_fixture(root)
        (root / "queue" / "RES-test.json").write_text(
            json.dumps(safe_item("0" * 40)), encoding="utf-8"
        )
        report = mod.audit(ota, root / "queue")
        assert report["counts"] == {"stale": 1}


def test_unsafe_contract_is_reported() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ota = write_fixture(root)
        doc = ota / "src" / "content" / "documents" / "OTA-TEC-0099-2026-DE.md"
        item = safe_item(mod.git_blob_sha(doc))
        item["consumer_impact_policy"]["auto_update_noxia"] = True
        (root / "queue" / "RES-test.json").write_text(json.dumps(item), encoding="utf-8")
        report = mod.audit(ota, root / "queue")
        assert report["counts"] == {"stale": 1}
        assert any("auto_update_noxia must be false" in e for e in report["contract_errors"])


if __name__ == "__main__":
    test_uncovered()
    test_covered()
    test_stale()
    test_unsafe_contract_is_reported()
    print("ota tech object audit tests: ok")
