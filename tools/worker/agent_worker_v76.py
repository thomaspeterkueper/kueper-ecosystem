#!/usr/bin/env python3
"""KUEPER V7.6 worker — route/availability/budget decisions happen before claim.

A task attempt is now consumed only after the selected model has an atomically reserved
LLM budget slot. Cost-window and provider deferrals update a still-pending task and do
not create task_runs or increment attempt_count.

Every provider decision is also written to the central AI usage ledger before a paid
provider call can happen. Telemetry failure is fail-closed: no unaccounted AI call.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))
import agent_worker as worker  # noqa: E402
import agent_worker_v71 as v71  # noqa: E402
import agent_worker_v74 as v74  # noqa: E402
import agent_worker_v75 as v75  # noqa: E402
from tools.telemetry.ai_usage import log_event, log_intent  # noqa: E402

BUDGET_REASONS = {"daily-call-budget-exhausted", "daily-pro-budget-exhausted", "provider-budget-disabled"}


def next_utc_day() -> str:
    now = dt.datetime.now(dt.timezone.utc)
    return (now.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=1, minutes=2)).isoformat()


def workflow_run_id() -> int | None:
    value = os.environ.get("GITHUB_RUN_ID", "")
    return int(value) if value.isdigit() else None


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


def usage_intent(candidate: dict[str, Any], decision: Any) -> dict[str, Any]:
    task_id = str(candidate["id"])
    repository = candidate.get("repository")
    external_id = candidate.get("external_id")
    task_type = str(candidate.get("type") or "unknown")
    trigger = os.environ.get("GITHUB_EVENT_NAME") or "worker"
    dedup = f"agent-worker-v7:{task_id}:{decision.provider}:{decision.model}"
    return log_intent(
        source_system="agent-worker-v7",
        trigger_type=trigger,
        reason=f"{task_type}: {decision.reason}",
        provider=decision.provider,
        model=decision.model,
        dedup_key=dedup,
        repository=repository,
        task_id=task_id,
        workflow_run_id=workflow_run_id(),
        commit_sha=os.environ.get("GITHUB_SHA"),
        is_retry=int(candidate.get("attempt_count") or 0) > 0,
        metadata={"external_id": external_id, "task_type": task_type, "priority": candidate.get("priority")},
    )


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

        # Governance invariant: a provider decision must have a durable reason before
        # any availability/budget/claim/provider action can proceed.
        intent = usage_intent(candidate, decision)
        intent_id = str(intent["id"])

        if decision.provider == "deepseek" and not db.rpc("kueper_provider_available", {"p_provider": "deepseek"}):
            available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=6)).isoformat()
            log_event(intent_id, "blocked", provider=decision.provider, model=decision.model,
                      workflow_run_id=workflow_run_id(), error_code="provider-paused",
                      error_message="Provider unavailable: deepseek / paused")
            db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": available_at, "p_reason": "Provider unavailable: deepseek / paused"})
            results.append({"task": task_id, "result": "provider-paused-unclaimed", "available_at": available_at, "usage_intent": intent_id})
            break

        if not decision.execute_now:
            log_event(intent_id, "skipped", provider=decision.provider, model=decision.model,
                      workflow_run_id=workflow_run_id(), error_code="cost-window-deferred",
                      error_message=decision.reason)
            db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": decision.available_at, "p_reason": decision.reason})
            results.append({"task": task_id, "result": "cost-deferred-unclaimed", "available_at": decision.available_at, "usage_intent": intent_id})
            continue

        task, budget = claim_for_execution(db, candidate, worker_id, decision)
        if not task:
            reason = str(budget.get("reason") or "claim-race")
            if reason in BUDGET_REASONS:
                available_at = next_utc_day()
                log_event(intent_id, "blocked", provider=decision.provider, model=decision.model,
                          workflow_run_id=workflow_run_id(), error_code=reason,
                          error_message=f"LLM budget deferred: {reason}")
                db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": available_at, "p_reason": f"LLM budget deferred: {reason}"})
                results.append({"task": task_id, "result": "budget-deferred-unclaimed", "reason": reason, "available_at": available_at, "usage_intent": intent_id})
                break
            log_event(intent_id, "skipped", provider=decision.provider, model=decision.model,
                      workflow_run_id=workflow_run_id(), error_code=reason,
                      error_message="Task could not be claimed; provider was not called")
            results.append({"task": task_id, "result": "claim-race", "reason": reason, "usage_intent": intent_id})
            continue

        lease = str(task["lease_token"])
        db.rpc("kueper_start_task", {"p_task_id": task_id, "p_lease_token": lease})
        log_event(intent_id, "started", provider=decision.provider, model=decision.model,
                  workflow_run_id=workflow_run_id(), metadata={"budget": budget})
        try:
            with worker.Heartbeat(db, task_id, lease):
                outcome = worker.execute_task(task, decision.model)
            input_tokens = outcome.get("input_tokens")
            output_tokens = outcome.get("output_tokens")
            if outcome.get("kind") == "park":
                db.rpc("kueper_park_task", {"p_task_id": task_id, "p_lease_token": lease, "p_reason": outcome["reason"], "p_requires_owner_decision": bool(outcome.get("requires_owner_decision"))})
                log_event(intent_id, "completed", provider=decision.provider, model=decision.model,
                          input_tokens=input_tokens, output_tokens=output_tokens,
                          workflow_run_id=workflow_run_id(), metadata={"outcome": "parked"})
                results.append({"task": task_id, "result": "parked", "reason": outcome["reason"], "usage_intent": intent_id})
            elif outcome.get("pr_url"):
                db.rpc("kueper_submit_task_for_review", {"p_task_id": task_id, "p_lease_token": lease, "p_result": outcome, "p_provider": decision.provider, "p_model": decision.model, "p_input_tokens": input_tokens, "p_output_tokens": output_tokens, "p_cost_estimate_eur": None})
                log_event(intent_id, "completed", provider=decision.provider, model=decision.model,
                          input_tokens=input_tokens, output_tokens=output_tokens,
                          workflow_run_id=workflow_run_id(), metadata={"outcome": "review_pending", "pr_url": outcome.get("pr_url")})
                results.append({"task": task_id, "result": "review_pending", "pr_url": outcome.get("pr_url"), "provider": decision.provider, "model": decision.model, "budget": budget, "usage_intent": intent_id})
            else:
                db.rpc("kueper_complete_task", {"p_task_id": task_id, "p_lease_token": lease, "p_result": outcome, "p_provider": decision.provider, "p_model": decision.model, "p_input_tokens": input_tokens, "p_output_tokens": output_tokens, "p_cost_estimate_eur": None})
                log_event(intent_id, "completed", provider=decision.provider, model=decision.model,
                          input_tokens=input_tokens, output_tokens=output_tokens,
                          workflow_run_id=workflow_run_id(), metadata={"outcome": "completed"})
                results.append({"task": task_id, "result": "completed", "provider": decision.provider, "model": decision.model, "budget": budget, "usage_intent": intent_id})
        except worker.ProviderUnavailable as exc:
            log_event(intent_id, "failed", provider=exc.provider, model=decision.model,
                      workflow_run_id=workflow_run_id(), error_code=str(exc.code), error_message=exc.message)
            db.rpc("kueper_pause_provider", {"p_provider": exc.provider, "p_reason": "billing-or-provider-unavailable", "p_error_code": exc.code, "p_error_message": exc.message[:2000], "p_pause_seconds": exc.pause_seconds})
            available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=exc.pause_seconds)).isoformat()
            db.rpc("kueper_reschedule_provider_task", {"p_task_id": task_id, "p_lease_token": lease, "p_provider": exc.provider, "p_reason": str(exc), "p_available_at": available_at})
            results.append({"task": task_id, "result": "provider-paused", "provider": exc.provider, "available_at": available_at, "usage_intent": intent_id})
            break
        except Exception as exc:
            task_failures += 1
            try:
                log_event(intent_id, "failed", provider=decision.provider, model=decision.model,
                          workflow_run_id=workflow_run_id(), error_code="task-execution-error", error_message=str(exc))
                db.rpc("kueper_fail_task", {"p_task_id": task_id, "p_lease_token": lease, "p_error": str(exc)[:4000], "p_retry_delay_seconds": 300})
            except Exception as fail_exc:
                print(f"ERROR could not record task failure: {fail_exc}", flush=True)
            print(f"::error title=Task execution failed::{task_id}: {str(exc)[:500]}", flush=True)
            results.append({"task": task_id, "result": "failed", "error": str(exc), "usage_intent": intent_id})

    print(json.dumps({"worker": worker_id, "results": results}, ensure_ascii=False, indent=2))
    return 1 if task_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
