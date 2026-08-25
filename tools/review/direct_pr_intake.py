#!/usr/bin/env python3
"""Create an idempotent review_pending task for a directly-created PR.

This closes the gap where PRs not created by the worker never enter the
Automated PR Review lifecycle. It deliberately does not merge, approve, or
change canon; it only creates the review work item.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

WORKER_DIR = Path(__file__).resolve().parents[1] / "worker"
sys.path.insert(0, str(WORKER_DIR))
import agent_worker_v71 as v71  # noqa: E402

PR_RE = re.compile(r"^https://github\.com/([^/]+/[^/]+)/pull/(\d+)$")


def parse_pr_url(url: str) -> tuple[str, int]:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("expected https://github.com/OWNER/REPO/pull/NUMBER")
    return match.group(1), int(match.group(2))


def intake(db: v71.PatchedSupabaseRPC, pr_url: str, *, priority: str = "normal") -> dict[str, Any]:
    repo, number = parse_pr_url(pr_url)
    payload = {
        "pr_url": pr_url,
        "origin": "direct-pr-intake",
        "review_scope": "Review the current PR against its stated intent, repository governance and diff.",
    }
    created = db.rpc("kueper_create_task", {
        "p_type": "PR_REVIEW",
        "p_source_project": "ECO",
        "p_target_project": "ECO",
        "p_payload": payload,
        "p_priority": priority,
        "p_parent_task_id": None,
        "p_dependencies": [],
        "p_idempotency_key": f"direct-pr-review:{repo}:{number}",
        "p_external_id": f"DIRECT-PR-{repo.replace('/', '-').upper()}-{number}",
        "p_available_at": None,
        "p_max_attempts": 3,
        "p_preferred_provider": None,
        "p_preferred_model": None,
        "p_repository": repo,
        "p_base_sha": None,
        "p_relevance_score": None,
        "p_evidence_score": None,
        "p_metadata": {"actor": "direct-pr-intake", "pr_number": number},
    })
    task_id = created.get("id") if isinstance(created, dict) else None
    if not task_id:
        raise RuntimeError("kueper_create_task returned no task id")
    # Existing review RPCs operate only on review_pending tasks. Promote the
    # newly-created intake task using the narrow lifecycle RPC installed with V7.3.
    promoted = db.rpc("kueper_mark_task_review_pending", {
        "p_task_id": task_id,
        "p_pr_url": pr_url,
    })
    return promoted if isinstance(promoted, dict) else {"id": task_id, "status": "review_pending", "pr_url": pr_url}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_url")
    parser.add_argument("--priority", default="normal", choices=("low", "normal", "high", "critical"))
    args = parser.parse_args()
    for name in ("SUPABASE_URL", "SUPABASE_SECRET_KEY"):
        if not os.environ.get(name):
            raise SystemExit(f"missing required secret: {name}")
    db = v71.PatchedSupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    print(json.dumps(intake(db, args.pr_url, priority=args.priority), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
