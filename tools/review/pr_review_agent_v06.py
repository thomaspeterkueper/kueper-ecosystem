#!/usr/bin/env python3
"""KUEPER PR reviewer v0.6 — provider-independent stale review reconciliation.

V0.5 made provider outages non-fatal, but a paused provider can still stop the live
batch before later CLOSED/MERGED PR tasks are reached. V0.6 performs a bounded stale
sweep first, independent of model availability, then delegates live review work to
v0.5 unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import pr_review_agent_v05 as v05  # noqa: E402

base = v05.base


def reconcile_inactive_review_tasks(db: Any, scan_limit: int = 50) -> list[dict[str, Any]]:
    pending = db.rpc("kueper_list_review_pending", {"p_limit": max(1, scan_limit)}) or []
    if isinstance(pending, dict):
        pending = [pending]

    reconciled: list[dict[str, Any]] = []
    for task in pending:
        pr_url = str(task.get("pr_url") or "").strip()
        if not pr_url:
            continue
        try:
            state = v05.pr_state(pr_url)
        except Exception as exc:
            # A transient GitHub lookup must not prevent other stale tasks from being
            # reconciled. Live review remains fail-closed in v0.5.
            print(
                f"::warning title=PR state lookup skipped::{task.get('id')}: {str(exc)[:300]}",
                flush=True,
            )
            continue
        if state in {"CLOSED", "MERGED"}:
            reconciled.append(v05.v04._original_review_task(task, db))
    return reconciled


def resilient_review_pending_batch(db: Any, max_reviews: int) -> tuple[list[dict[str, Any]], int]:
    cleanup = reconcile_inactive_review_tasks(db, scan_limit=max(50, max_reviews * 10))
    live_results, failures = v05.resilient_review_pending_batch(db, max_reviews)
    return cleanup + live_results, failures


# v0.5's main delegates to the base CLI, which resolves this global at runtime.
base.review_pending_batch = resilient_review_pending_batch


def main() -> int:
    return v05.main()


if __name__ == "__main__":
    raise SystemExit(main())
