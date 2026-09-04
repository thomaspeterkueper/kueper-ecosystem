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
