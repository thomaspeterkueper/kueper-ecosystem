#!/usr/bin/env python3
"""Omnizedenz and Mishkenaz: no mandatory strong-source gate (Thomas, 22.11.2026)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    policy = json.loads((ROOT / "research/policy.json").read_text(encoding="utf-8"))
    profiles = policy["evidence_profiles"]
    projects = {p["id"]: p for p in policy["eligible_projects"]}
    assert projects["omnizedenz"]["evidence_profile"] == "philosophy-own-system"
    assert projects["mishkenaz"]["evidence_profile"] == "conlang-scientific"
    assert projects["contracomology"]["evidence_profile"] == "philosophy-comparative"
    for name in ("philosophy-own-system", "conlang-scientific"):
        prof = profiles[name]
        assert prof["require_strong_source"] is False, name
        assert "own-system-text" in prof["strong_source_markers"], name
        assert prof.get("own_system_primary_source"), name
        assert prof["minimum_sources"] >= 3 and prof["minimum_urls"] >= 3, name
    assert profiles["conlang-scientific"]["require_claim_classification"] is True
    assert profiles["philosophy-comparative"]["require_strong_source"] is True
    print("own-system profile tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
