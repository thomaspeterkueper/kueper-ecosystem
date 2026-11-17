#!/usr/bin/env python3
"""Tests for per-gap evidence profile overrides in discovery (standards-technical)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("discover", ROOT / "tools/research/discover.py")
assert SPEC and SPEC.loader
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)


def main() -> int:
    profiles = D.POLICY["evidence_profiles"]
    std = profiles["standards-technical"]
    assert "standard" in std["strong_source_markers"] and std["require_strong_source"] is True
    assert D.override_options(profiles["science"]) == ["standards-technical"]
    assert D.override_options(profiles["ota-archive-evidence"]) == []
    assert D.gap_profile({"evidence_profile_override": "standards-technical"}, "science", profiles["science"])[0] == "standards-technical"
    assert D.gap_profile({"evidence_profile_override": "standards-technical"}, "ota-archive-evidence", profiles["ota-archive-evidence"])[0] == "ota-archive-evidence"
    assert D.gap_profile({"evidence_profile_override": "general"}, "science", profiles["science"])[0] == "science"
    assert D.gap_profile({}, "science", profiles["science"])[0] == "science"
    assert "evidence_profile_override" in D.prompt({"id": "products", "repository": "x"}, ["en"], "science", profiles["science"], [])
    print("profile override tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
