#!/usr/bin/env python3
"""Execute explicitly selected queued research IDs.

This is a thin operational wrapper around execute.py. It does not weaken evidence
validation or canonicalization boundaries; it only controls which queued items are
selected for a manual/targeted run.

For OTA technical-object research, this wrapper also enforces the consumer boundary
before any external research starts: only externally researchable claim classes are
accepted and NOXIA balancing must be explicitly marked out of scope / non-mutating.
"""
from __future__ import annotations

import json
import os

import execute as core

TECH_OBJECT_CONTRACT = "ota-tech-object-v1"
TECH_OBJECT_RESEARCHABLE_CLASSES = {"R", "R-Anker", "H", "T"}


def validate_research_contract(item: dict) -> None:
    contract = item.get("research_contract")
    if contract != TECH_OBJECT_CONTRACT:
        return

    if item.get("source_project") != "ota":
        raise SystemExit(
            f"{item.get('id')}: {TECH_OBJECT_CONTRACT} requires source_project=ota"
        )
    if item.get("consumer_project") != "noxia":
        raise SystemExit(
            f"{item.get('id')}: {TECH_OBJECT_CONTRACT} requires consumer_project=noxia"
        )
    if not item.get("source_path") or not item.get("source_blob_sha"):
        raise SystemExit(
            f"{item.get('id')}: technical-object research requires pinned source_path + source_blob_sha"
        )

    classes = set(item.get("claim_classes") or [])
    if not classes or not classes.issubset(TECH_OBJECT_RESEARCHABLE_CLASSES):
        bad = sorted(classes - TECH_OBJECT_RESEARCHABLE_CLASSES)
        raise SystemExit(
            f"{item.get('id')}: technical-object research may only target "
            f"{sorted(TECH_OBJECT_RESEARCHABLE_CLASSES)}; invalid classes: {bad}"
        )

    impact = item.get("consumer_impact_policy") or {}
    if impact.get("auto_update_noxia") is not False:
        raise SystemExit(
            f"{item.get('id')}: technical-object contract requires auto_update_noxia=false"
        )
    if impact.get("balancing_is_out_of_scope") is not True:
        raise SystemExit(
            f"{item.get('id')}: technical-object contract requires balancing_is_out_of_scope=true"
        )
    if impact.get("flag_noxia_impact") is not True:
        raise SystemExit(
            f"{item.get('id')}: technical-object contract requires flag_noxia_impact=true"
        )


def main() -> int:
    token = os.environ.get("KUEPER_BOT_TOKEN")
    if not token:
        raise SystemExit("KUEPER_BOT_TOKEN required")

    requested = [
        value.strip()
        for value in os.environ.get("KUEPER_RESEARCH_IDS", "").split(",")
        if value.strip()
    ]
    if not requested:
        raise SystemExit("KUEPER_RESEARCH_IDS required (comma-separated research IDs)")

    queued = core.queue(token)
    by_id = {item["id"]: (item, payload) for item, payload in queued}
    missing = [research_id for research_id in requested if research_id not in by_id]
    if missing:
        raise SystemExit(f"requested research IDs are not queued: {', '.join(missing)}")

    results = []
    for research_id in requested:
        item, payload = by_id[research_id]
        validate_research_contract(item)
        results.append(core.execute(token, item, payload))

    print(
        json.dumps(
            {
                "selected": len(requested),
                "requested_ids": requested,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
