#!/usr/bin/env python3
"""Deterministic validation for the OTA evidence/KUE-SCI routing pilot."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads((ROOT / "research/policy.json").read_text(encoding="utf-8"))
PILOT = json.loads((ROOT / "research/pilots/ota-evidence-2026-08-28.json").read_text(encoding="utf-8"))

EXTERNAL_CLASSES = {"R", "T", "H", "S", "R-Anker", "OFFEN"}


def external_research_required(case: dict) -> bool:
    classes = set(case.get("preclassified_claim_classes") or [])
    anchor = bool(case.get("real_world_anchor"))
    if classes and classes <= {"F", "W"} and not anchor:
        return False
    return anchor or bool(classes & EXTERNAL_CLASSES)


def main() -> int:
    assert POLICY.get("auto_canonicalize") is False
    assert PILOT["safety"]["auto_publish"] is False
    assert PILOT["safety"]["auto_canonicalize"] is False

    routes = POLICY["publication_routing"]
    sci = routes["real_scientific_epaper"]
    assert sci["repository"] == "thomaspeterkueper/kueper.com"
    assert sci["path"] == "src/content/kue/sci"
    assert sci["namespace"] == "KUE-SCI"
    assert sci["auto_publish"] is False

    ota_profile = POLICY["evidence_profiles"]["ota-archive-evidence"]
    allowed_classes = set(ota_profile["claim_classes"])
    allowed_routes = set(ota_profile["allowed_publication_routes"])

    expected = {
        "OTA-PILOT-SCI-0037": True,
        "OTA-PILOT-FND-0030": True,
        "OTA-PILOT-BIO-0026": False,
    }
    observed = {}

    for case in PILOT["cases"]:
        classes = set(case.get("preclassified_claim_classes") or [])
        assert classes, f"{case['id']}: missing pre-research claim classification"
        assert classes <= allowed_classes, f"{case['id']}: invalid claim class"
        assert case["publication_route_hint"] in allowed_routes
        decision = external_research_required(case)
        observed[case["id"]] = decision
        assert decision is expected[case["id"]], f"{case['id']}: unexpected external research decision"

    assert observed["OTA-PILOT-BIO-0026"] is False
    print(json.dumps({
        "pilot": PILOT["pilot_id"],
        "ok": True,
        "external_research_required": observed,
        "real_scientific_epaper": {
            "repository": sci["repository"],
            "path": sci["path"],
            "namespace": sci["namespace"],
        },
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
