#!/usr/bin/env python3
"""KUEPER V7.6 worker — route/availability/budget decisions happen before claim.

A task attempt is now consumed only after the selected model has an atomically reserved
LLM budget slot. Cost-window and provider deferrals update a still-pending task and do
not create task_runs or increment attempt_count.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker as worker  # noqa: E402
import agent_worker_v71 as v71  # noqa: E402
import agent_worker_v74 as v74  # noqa: E402
import agent_worker_v75 as v75  # noqa: E402

BUDGET_REASONS = {"daily-call-budget-exhausted", "daily-pro-budget-exhausted", "provider-budget-disabled"}


def next_utc_day() -> str:
    now = dt.datetime.now(dt.timezone.utc)
    return (now.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=1, minutes=2)).isoformat()


def claim_for_execution(db: Any, task: dict[str, Any], worker_id: str, decision: Any) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    response = db.rpc("kueper_claim_task_with_llm_budget", {
        "p_task_id": task["id"],
        "p_worker_id": worker_id,
        "p_provider": decision.provider,
        "p_model": decision.model,
        "p_reason": decision.reason,
        "p_lease_seconds": 600,
    }) or {}
    if response.get("claimed"):
        return response.get("task"), response.get("budget") or {}
    return None, response


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tasks", type=int, default=int(os.environ.get("KUEPER_MAX_TASKS", "1")))
    args = parser.parse_args()
    required = ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "DEEPSEEK_API_KEY", "KUEPER_BOT_TOKEN"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"missing required secrets: {', '.join(missing)}")

    worker.ProviderUnavailable.__str__ = v75._provider_unavailable_str
    worker.repo_task = v74.repo_task
    db = v71.PatchedSupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    worker_id = f"github:{os.environ.get('GITHUB_RUN_ID', 'local')}:{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
    results: list[dict[str, Any]] = []
    task_failures = 0
    db.rpc("kueper_recover_expired_leases", {})

    for _ in range(max(1, args.max_tasks)):
        candidate = db.rpc("kueper_peek_runnable_task", {"p_target_project": None, "p_types": None})
        if not candidate:
            break
        decision = worker.route(candidate)
        task_id = str(candidate["id"])

        if decision.provider == "deepseek" and not db.rpc("kueper_provider_available", {"p_provider": "deepseek"}):
            available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=6)).isoformat()
            db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": available_at, "p_reason": "Provider unavailable: deepseek / paused"})
            results.append({"task": task_id, "result": "provider-paused-unclaimed", "available_at": available_at})
            break

        if not decision.execute_now:
            db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": decision.available_at, "p_reason": decision.reason})
            results.append({"task": task_id, "result": "cost-deferred-unclaimed", "available_at": decision.available_at})
            continue

        task, budget = claim_for_execution(db, candidate, worker_id, decision)
        if not task:
            reason = str(budget.get("reason") or "claim-race")
            if reason in BUDGET_REASONS:
                available_at = next_utc_day()
                db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": available_at, "p_reason": f"LLM budget deferred: {reason}"})
                results.append({"task": task_id, "result": "budget-deferred-unclaimed", "reason": reason, "available_at": available_at})
                break
            results.append({"task": task_id, "result": "claim-race", "reason": reason})
            continue

        lease = str(task["lease_token"])
        db.rpc("kueper_start_task", {"p_task_id": task_id, "p_lease_token": lease})
        try:
            with worker.Heartbeat(db, task_id, lease):
                outcome = worker.execute_task(task, decision.model)
            if outcome.get("kind") == "park":
                db.rpc("kueper_park_task", {"p_task_id": task_id, "p_lease_token": lease, "p_reason": outcome["reason"], "p_requires_owner_decision": bool(outcome.get("requires_owner_decision"))})
                results.append({"task": task_id, "result": "parked", "reason": outcome["reason"]})
            elif outcome.get("pr_url"):
                db.rpc("kueper_submit_task_for_review", {"p_task_id": task_id, "p_lease_token": lease, "p_result": outcome, "p_provider": decision.provider, "p_model": decision.model, "p_input_tokens": outcome.get("input_tokens"), "p_output_tokens": outcome.get("output_tokens"), "p_cost_estimate_eur": None})
                results.append({"task": task_id, "result": "review_pending", "pr_url": outcome.get("pr_url"), "provider": decision.provider, "model": decision.model, "budget": budget})
            else:
                db.rpc("kueper_complete_task", {"p_task_id": task_id, "p_lease_token": lease, "p_result": outcome, "p_provider": decision.provider, "p_model": decision.model, "p_input_tokens": outcome.get("input_tokens"), "p_output_tokens": outcome.get("output_tokens"), "p_cost_estimate_eur": None})
                results.append({"task": task_id, "result": "completed", "provider": decision.provider, "model": decision.model, "budget": budget})
        except worker.ProviderUnavailable as exc:
            db.rpc("kueper_pause_provider", {"p_provider": exc.provider, "p_reason": "billing-or-provider-unavailable", "p_error_code": exc.code, "p_error_message": exc.message[:2000], "p_pause_seconds": exc.pause_seconds})
            available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=exc.pause_seconds)).isoformat()
            db.rpc("kueper_reschedule_provider_task", {"p_task_id": task_id, "p_lease_token": lease, "p_provider": exc.provider, "p_reason": str(exc), "p_available_at": available_at})
            results.append({"task": task_id, "result": "provider-paused", "provider": exc.provider, "available_at": available_at})
            break
        except Exception as exc:
            task_failures += 1
            try:
                db.rpc("kueper_fail_task", {"p_task_id": task_id, "p_lease_token": lease, "p_error": str(exc)[:4000], "p_retry_delay_seconds": 300})
            except Exception as fail_exc:
                print(f"ERROR could not record task failure: {fail_exc}", flush=True)
            print(f"::error title=Task execution failed::{task_id}: {str(exc)[:500]}", flush=True)
            results.append({"task": task_id, "result": "failed", "error": str(exc)})

    print(json.dumps({"worker": worker_id, "results": results}, ensure_ascii=False, indent=2))
    return 1 if task_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
