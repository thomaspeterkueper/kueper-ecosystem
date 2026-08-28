#!/usr/bin/env python3
"""Execute explicitly selected queued research IDs.

This is a thin operational wrapper around execute.py. It does not weaken evidence
validation or canonicalization boundaries; it only controls which queued items are
selected for a manual/targeted run.
"""
from __future__ import annotations

import json
import os

import execute as core


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
