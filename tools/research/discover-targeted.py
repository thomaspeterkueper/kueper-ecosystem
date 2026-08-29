#!/usr/bin/env python3
"""Run normal research discovery for one explicitly selected project.

This wrapper does not weaken discovery policy. It narrows the existing weighted
eligible-project set to one configured project and then calls discover.main().
Useful for manual or project-specific sweeps such as OTA evidence audits.
"""
from __future__ import annotations

import os

import discover as core


def main() -> int:
    project_id = os.environ.get("KUEPER_DISCOVERY_PROJECT_ID", "").strip()
    if not project_id:
        raise SystemExit("KUEPER_DISCOVERY_PROJECT_ID required")

    matches = [
        entry
        for entry in core.POLICY.get("eligible_projects", [])
        if entry.get("id") == project_id
    ]
    if len(matches) != 1:
        raise SystemExit(f"project is not uniquely eligible for research: {project_id}")

    # discover.main() remains the single implementation of novelty checks,
    # evidence-profile validation, source-path enforcement and queue writes.
    core.POLICY["eligible_projects"] = matches
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
