#!/usr/bin/env python3
"""KUEPER V7.6 worker: shared daily LLM invocation budget.

V7.5 keeps provider blockers compact. V7.6 adds a conservative pre-invocation
reservation against the shared DeepSeek daily budget. Budget exhaustion reschedules
the task to the next UTC day instead of consuming an attempt or completing it.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_worker as worker  # noqa: E402
import agent_worker_v73 as v73  # noqa: E402
import agent_worker_v75 as v75  # noqa: E402

ORIGINAL_EXECUTE_TASK = worker.execute_task
ORIGINAL_RPC_CLASS = v73.v71.PatchedSupabaseRPC
BUDGET_REASON_PREFIX = "LLM budget deferred:"


def next_budget_window(now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    now = now.astimezone(dt.timezone.utc)
    tomorrow = (now + dt.timedelta(days=1)).date()
    return dt.datetime.combine(tomorrow, dt.time(0, 2), tzinfo=dt.timezone.utc).isoformat()


def reserve_budget(task: dict[str, Any], model: str) -> dict[str, Any]:
    db = worker.SupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    result = db.rpc(
        "kueper_reserve_llm_invocation",
        {
            "p_provider": "deepseek",
            "p_model": model,
            "p_source": "agent-worker-v7",
            "p_task_id": task.get("id"),
            "p_reason": str(task.get("type") or "task"),
        },
    )
    return result if isinstance(result, dict) else {"allowed": bool(result), "reason": "unknown"}


def budgeted_execute_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    budget = reserve_budget(task, model)
    if budget.get("allowed"):
        return ORIGINAL_EXECUTE_TASK(task, model)

    available_at = next_budget_window()
    reason = (
        f"{BUDGET_REASON_PREFIX} {budget.get('reason')} until {available_at} "
        f"({budget.get('calls', 0)}/{budget.get('max_daily_calls', '?')} calls, "
        f"{budget.get('pro_calls', 0)}/{budget.get('max_daily_pro_calls', '?')} Pro)"
    )
    print(f"::notice title=LLM budget deferred::{task.get('id')}: {reason}", flush=True)
    return {
        "kind": "park",
        "reason": reason,
        "requires_owner_decision": False,
        "budget_deferred_until": available_at,
    }


class BudgetAwareRPC(ORIGINAL_RPC_CLASS):
    def rpc(self, name: str, payload: dict[str, Any]) -> Any:
        if name == "kueper_park_task":
            reason = str(payload.get("p_reason") or "")
            if reason.startswith(BUDGET_REASON_PREFIX):
                marker = " until "
                available_at = next_budget_window()
                if marker in reason:
                    candidate = reason.split(marker, 1)[1].split(" ", 1)[0].strip()
                    if candidate:
                        available_at = candidate
                return super().rpc(
                    "kueper_reschedule_task",
                    {
                        "p_task_id": payload.get("p_task_id"),
                        "p_lease_token": payload.get("p_lease_token"),
                        "p_available_at": available_at,
                        "p_reason": reason,
                    },
                )
        return super().rpc(name, payload)


def main() -> int:
    worker.execute_task = budgeted_execute_task
    v73.v71.PatchedSupabaseRPC = BudgetAwareRPC
    try:
        return v75.main()
    finally:
        worker.execute_task = ORIGINAL_EXECUTE_TASK
        v73.v71.PatchedSupabaseRPC = ORIGINAL_RPC_CLASS


if __name__ == "__main__":
    raise SystemExit(main())
