#!/usr/bin/env python3
"""KUEPER PR reviewer v0.5 — stale-PR cleanup and provider outage resilience.

V0.4 added the research evidence gate but resolves the changed-file list before the
base reviewer can terminalize CLOSED/MERGED PRs. It also lets a provider billing or
availability outage turn the entire scheduled review workflow red every cycle.

V0.5 keeps all v0.4 review/evidence semantics and adds two operational guards:
- resolve PR state before the research changed-file guard, so inactive PR review
  tasks are reconciled without requiring a diff or model call;
- treat ``ProviderUnavailable`` as a control-plane provider pause, not a review
  defect. Persist the provider pause, leave the review task pending, stop the live
  review batch, and return success so the scheduler heartbeat reflects infrastructure
  truth instead of reporting repeated false review failures.

There is deliberately no synthetic model fallback here. The active provider policy
currently contains only DeepSeek, so pretending to fail over would violate the
configured routing contract.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import pr_review_agent_v04 as v04  # noqa: E402

base = v04.base


def pr_state(pr_url: str) -> str:
    """Return authoritative GitHub PR state without cloning the repository."""
    env = os.environ.copy()
    token = env.get("KUEPER_BOT_TOKEN") or env.get("GITHUB_TOKEN")
    if token:
        env["GH_TOKEN"] = token
    cp = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "state"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=False,
    )
    if cp.returncode != 0:
        raise base.worker.WorkerError(
            f"could not resolve PR state ({cp.returncode}): {(cp.stdout or '')[-2000:]}"
        )
    try:
        payload = json.loads(cp.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise base.worker.WorkerError("invalid JSON while resolving PR state") from exc
    state = str(payload.get("state") or "").strip().upper()
    if not state:
        raise base.worker.WorkerError("PR state response is empty")
    return state


def resilient_review_task(task: dict[str, Any], db: Any) -> dict[str, Any]:
    """Reconcile inactive PRs before v0.4 asks GitHub for changed paths."""
    pr_url = str(task.get("pr_url") or "").strip()
    if not pr_url:
        return v04.guarded_review_task(task, db)

    state = pr_state(pr_url)
    if state in {"CLOSED", "MERGED"}:
        # v04 captured the original v0.1 task reviewer before installing its
        # research guard. That reviewer already owns the canonical terminal RPC.
        return v04._original_review_task(task, db)
    if state != "OPEN":
        raise base.worker.WorkerError(f"unexpected PR state: {state}")
    return v04.guarded_review_task(task, db)


def _provider_available(db: Any) -> bool:
    value = db.rpc("kueper_provider_available", {"p_provider": "deepseek"})
    return bool(value)


def _pause_provider(db: Any, exc: base.worker.ProviderUnavailable) -> None:
    db.rpc(
        "kueper_pause_provider",
        {
            "p_provider": exc.provider,
            "p_reason": "billing-or-provider-unavailable",
            "p_error_code": exc.code,
            "p_error_message": exc.message[:2000],
            "p_pause_seconds": exc.pause_seconds,
        },
    )


def resilient_review_pending_batch(db: Any, max_reviews: int) -> tuple[list[dict[str, Any]], int]:
    """Review live PRs while keeping stale cleanup independent of model health."""
    limit = max(1, max_reviews)
    results: list[dict[str, Any]] = []
    failures = 0
    charged = 0
    seen: set[str] = set()

    while charged < limit:
        pending = db.rpc("kueper_list_review_pending", {"p_limit": limit - charged}) or []
        if isinstance(pending, dict):
            pending = [pending]
        candidates = [task for task in pending if str(task.get("id") or "") not in seen]
        if not candidates:
            break

        for task in candidates:
            task_id = str(task.get("id") or "")
            if task_id:
                seen.add(task_id)
            try:
                state = pr_state(str(task.get("pr_url") or "").strip())
                if state in {"CLOSED", "MERGED"}:
                    result = v04._original_review_task(task, db)
                    results.append(result)
                    continue
                if state != "OPEN":
                    raise base.worker.WorkerError(f"unexpected PR state: {state}")

                if not _provider_available(db):
                    print(
                        "::warning title=Review provider paused::DeepSeek is paused; live PR reviews remain queued",
                        flush=True,
                    )
                    results.append(
                        {
                            "task": task.get("id"),
                            "result": "provider-paused",
                            "provider": "deepseek",
                        }
                    )
                    return results, failures

                result = v04.guarded_review_task(task, db)
            except base.worker.ProviderUnavailable as exc:
                _pause_provider(db, exc)
                print(
                    f"::warning title=Review provider paused::{exc.provider} paused due to {exc.code}; live reviews remain queued",
                    flush=True,
                )
                results.append(
                    {
                        "task": task.get("id"),
                        "result": "provider-paused",
                        "provider": exc.provider,
                        "code": exc.code,
                    }
                )
                return results, failures
            except Exception as exc:
                failures += 1
                charged += 1
                print(
                    f"::error title=Automated PR review failed::{task.get('id')}: {str(exc)[:500]}",
                    flush=True,
                )
                result = {
                    "task": task.get("id"),
                    "result": "REVIEW_ERROR",
                    "error": str(exc),
                }
            else:
                if result.get("result") != "terminal":
                    charged += 1
            results.append(result)
            if charged >= limit:
                break

    return results, failures


# base.main resolves this global at runtime, so v0.5 can retain the established
# CLI, Supabase construction and report format while replacing only batch policy.
base.review_task = resilient_review_task
base.review_pending_batch = resilient_review_pending_batch


def main() -> int:
    return v04.main()


if __name__ == "__main__":
    raise SystemExit(main())
