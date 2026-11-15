#!/usr/bin/env python3
"""Regression coverage for KUEPER Engineering ecosystem routing."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_engineering_is_a_canonical_followup_target() -> None:
    router = load_module(ROOT / "tools" / "loop" / "route_followups.py", "route_followups")
    by_id, by_code = router.registry()

    assert router.codes()["engineering"] == "ENG"
    assert by_id["engineering"]["repository"] == "thomaspeterkueper/kueper-engineering"
    assert by_code["ENG"]["id"] == "engineering"

    envelope = {
        "target": "ENG",
        "title": "Resolve engineering dependency",
        "reason": "A concrete technical dependency was found",
        "requested_change": "Define the engineering-owned technical contract",
        "expected_result": "A stable engineering result exists",
        "priority": "medium",
        "depth": 1,
    }
    assert router.validate(envelope, "NOXIA", by_code) == []


def test_worker_prompt_allows_eng_followups() -> None:
    worker = load_module(ROOT / "tools" / "worker" / "agent_worker_v72.py", "agent_worker_v72")
    assert "ENG" in {code.strip() for code in worker.TARGET_CODES.split(",")}


def test_affects_keeps_only_project_codes() -> None:
    router = load_module(ROOT / "tools" / "loop" / "route_followups.py", "route_followups")

    assert router.normalize_affects(["source-code", "target-code"], "NOXIA", "ENG") == ["NOXIA", "ENG"]
    assert router.normalize_affects(["docs/world/chronomap-erde/"], "NOXIA", "OTA") == ["NOXIA", "OTA"]
    assert router.normalize_affects(["kg", "ECO", "ENG"], "NOXIA", "ENG") == ["NOXIA", "ENG", "KG", "ECO"]
    assert router.normalize_affects(None, "KUE", "KG") == ["KUE", "KG"]

    envelope = {
        "title": "Resolve engineering dependency",
        "reason": "r",
        "requested_change": "c",
        "expected_result": "e",
        "affects": ["source-code", "target-code"],
    }
    text = router.markdown(envelope, "EXT-NOXIA-ENG-20261115-001", "NOXIA", "ENG", "abc", "2026-11-15")
    assert "affects: [NOXIA, ENG]" in text
