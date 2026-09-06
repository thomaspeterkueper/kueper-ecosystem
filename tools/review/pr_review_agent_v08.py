#!/usr/bin/env python3
"""KUEPER PR reviewer v0.8 — budget-aware batch admission.

V0.7 reserves budget per semantic review, but a failed semantic attempt can leave the
same review_pending task at the head of the queue. Subsequent scheduled runs then
reserve another daily slot for the same unchanged PR. V0.8 prevents that retry loop:

- one unchanged task/head is admitted at most once per UTC day;
- exhausted daily budget stops semantic batch work immediately;
- provider-independent stale PR reconciliation still runs before the budget guard.

A changed PR head is a new review candidate and may be admitted again the same day.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import pr_review_agent_v07 as v07  # noqa: E402

base = v07.base
v06 = v07.v06


def _task_head_sha(task: dict[str, Any]) -> str:
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    for key in ("head_sha", "pr_head_sha", "head"): 
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("head_sha", "base_sha"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def review_reason(task: dict[str, Any], model_reason: str) -> str:
    return f"{model_reason}; head={_task_head_sha(task)}"


def already_reserved_today(db: Any, task: dict[str, Any], reason: str) -> bool:
    result = db.rpc(
        "kueper_llm_invocation_reserved_today",
        {
            "p_provider": "deepseek",
            "p_source": "pr-review-agent",
            "p_task_id": task.get("id"),
            "p_reason": reason,
        },
    )
    return bool(result)


def cost_aware_review_task(task: dict[str, Any], db: Any) -> dict[str, Any]:
    pr_url = str(task.get("pr_url") or "").strip()
    paths = v07.changed_paths(pr_url) if pr_url else ["__UNKNOWN_CHANGED_PATHS__"]
    model, model_reason = v07.select_review_model(task, paths)
    reason = review_reason(task, model_reason)

    if already_reserved_today(db, task, reason):
        print(
            f"::notice title=Review retry deferred::{task.get('id')}: unchanged PR already consumed today's review slot",
            flush=True,
        )
        return {
            "task": task.get("id"),
            "result": "already-attempted-today",
            "provider": "deepseek",
            "model": model,
            "reason": "unchanged-review-already-reserved-today",
        }

    budget = v07.reserve_review_budget(db, task, model, reason)
    if not budget.get("allowed"):
        print(
            f"::notice title=Review budget deferred::{task.get('id')}: {budget.get('reason')} "
            f"({budget.get('calls', 0)}/{budget.get('max_daily_calls', '?')} calls, "
            f"{budget.get('pro_calls', 0)}/{budget.get('max_daily_pro_calls', '?')} Pro)",
            flush=True,
        )
        return {
            "task": task.get("id"),
            "result": "budget-deferred",
            "provider": "deepseek",
            "model": model,
            "reason": budget.get("reason"),
        }

    original_reserve = v07.reserve_review_budget
    v07.reserve_review_budget = lambda _db, _task, _model, _reason: {"allowed": True, "reason": "pre-reserved"}
    try:
        return v07.cost_aware_review_task(task, db)
    finally:
        v07.reserve_review_budget = original_reserve


def budget_aware_review_pending_batch(db: Any, max_reviews: int) -> tuple[list[dict[str, Any]], int]:
    cleanup = v06.reconcile_inactive_review_tasks(db, scan_limit=max(50, max_reviews * 10))
    pending = db.rpc("kueper_list_review_pending", {"p_limit": max(1, max_reviews * 4)}) or []
    if isinstance(pending, dict):
        pending = [pending]

    results: list[dict[str, Any]] = list(cleanup)
    failures = 0
    semantic_attempts = 0

    for task in pending:
        if semantic_attempts >= max(1, max_reviews):
            break
        pr_url = str(task.get("pr_url") or "").strip()
        if not pr_url:
            continue
        try:
            state = v06.v05.pr_state(pr_url)
            if state in {"CLOSED", "MERGED"}:
                continue  # already handled by stale sweep
            if state != "OPEN":
                continue
            if not v06.v05._provider_available(db):
                results.append({"task": task.get("id"), "result": "provider-paused", "provider": "deepseek"})
                break
            result = cost_aware_review_task(task, db)
        except base.worker.ProviderUnavailable as exc:
            v06.v05._pause_provider(db, exc)
            results.append({"task": task.get("id"), "result": "provider-paused", "provider": exc.provider, "code": exc.code})
            break
        except Exception as exc:
            failures += 1
            semantic_attempts += 1
            print(f"::error title=Automated PR review failed::{task.get('id')}: {str(exc)[:500]}", flush=True)
            results.append({"task": task.get("id"), "result": "REVIEW_ERROR", "error": str(exc)})
            continue

        results.append(result)
        outcome = str(result.get("result") or "")
        if outcome == "budget-deferred":
            break
        if outcome == "already-attempted-today":
            continue
        if outcome != "terminal":
            semantic_attempts += 1

    return results, failures


base.review_pending_batch = budget_aware_review_pending_batch


def main() -> int:
    return v07.main()


if __name__ == "__main__":
    raise SystemExit(main())
