#!/usr/bin/env python3
"""KUEPER PR reviewer v0.7 — Flash-first semantic review with evidence-based Pro escalation.

All provider-independent reconciliation from v0.6 remains intact. Live semantic
review defaults to DeepSeek Flash. Pro is reserved for explicit high-risk evidence:
critical/high task priority, critical scientific/evidence gates, security tasks, or
changes touching privileged workflow/migration/security surfaces. Every semantic
review must also reserve a slot from the shared daily LLM invocation budget.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import pr_review_agent_v06 as v06  # noqa: E402

base = v06.base
worker = base.worker
ORIGINAL_GUARDED_REVIEW_TASK = v06.v05.v04.guarded_review_task

PRO_PATH_PREFIXES = (
    ".github/workflows/",
    "supabase/migrations/",
    "migrations/",
    "security/",
)
PRO_PATH_NAMES = {"rls.sql", "policies.sql", "schema.sql"}


def changed_paths(pr_url: str) -> list[str]:
    env = os.environ.copy()
    token = env.get("KUEPER_BOT_TOKEN") or env.get("GITHUB_TOKEN")
    if token:
        env["GH_TOKEN"] = token
    cp = subprocess.run(
        ["gh", "pr", "diff", pr_url, "--name-only"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=False,
    )
    if cp.returncode != 0:
        return ["__UNKNOWN_CHANGED_PATHS__"]
    return [line.strip() for line in (cp.stdout or "").splitlines() if line.strip()]


def select_review_model(task: dict[str, Any], paths: list[str]) -> tuple[str, str]:
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    priority = str(task.get("priority") or "medium").lower()
    task_type = str(task.get("type") or "").upper()
    blocker = str(task.get("blocked_reason") or "").lower()

    if bool(payload.get("requires_deep_reasoning")):
        return "deepseek-v4-pro", "explicit deep-reasoning request"
    if priority in {"high", "critical"}:
        return "deepseek-v4-pro", f"{priority}-priority review"
    if task_type == "SECURITY":
        return "deepseek-v4-pro", "security task"
    if "critical scientific/evidence review" in blocker:
        return "deepseek-v4-pro", "critical scientific/evidence gate"
    if "__UNKNOWN_CHANGED_PATHS__" in paths:
        return "deepseek-v4-pro", "changed-path inspection unavailable"

    for path in paths:
        normalized = path.strip().lower()
        if normalized.startswith(PRO_PATH_PREFIXES) or Path(normalized).name in PRO_PATH_NAMES:
            return "deepseek-v4-pro", f"privileged/sensitive path: {path}"

    return "deepseek-v4-flash", "routine review; no Pro escalation evidence"


class ModelAwareDB:
    def __init__(self, inner: Any, model: str):
        self.inner = inner
        self.model = model

    def rpc(self, name: str, payload: dict[str, Any]) -> Any:
        if name == "kueper_record_pr_review":
            payload = dict(payload)
            payload["p_model"] = self.model
        return self.inner.rpc(name, payload)


def reserve_review_budget(db: Any, task: dict[str, Any], model: str, reason: str) -> dict[str, Any]:
    result = db.rpc(
        "kueper_reserve_llm_invocation",
        {
            "p_provider": "deepseek",
            "p_model": model,
            "p_source": "pr-review-agent",
            "p_task_id": task.get("id"),
            "p_reason": reason,
        },
    )
    return result if isinstance(result, dict) else {"allowed": bool(result), "reason": "unknown"}


def cost_aware_review_task(task: dict[str, Any], db: Any) -> dict[str, Any]:
    pr_url = str(task.get("pr_url") or "").strip()
    paths = changed_paths(pr_url) if pr_url else ["__UNKNOWN_CHANGED_PATHS__"]
    model, reason = select_review_model(task, paths)

    budget = reserve_review_budget(db, task, model, reason)
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

    original_run = worker.run

    def model_aware_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd and cmd[0] == "claude":
            cmd = list(cmd)
            if len(cmd) >= 4 and isinstance(cmd[-1], str):
                cmd[-1] = cmd[-1].replace(
                    "Review provider/model: DeepSeek/deepseek-v4-pro",
                    f"Review provider/model: DeepSeek/{model}",
                )
            env = dict(kwargs.get("env") or os.environ.copy())
            actual_model = "deepseek-v4-pro[1m]" if model == "deepseek-v4-pro" else "deepseek-v4-flash"
            env["ANTHROPIC_MODEL"] = actual_model
            env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = actual_model
            env["CLAUDE_CODE_EFFORT_LEVEL"] = "max" if model == "deepseek-v4-pro" else "high"
            kwargs["env"] = env
            print(f"Review model route: {model} ({reason})", flush=True)
        return original_run(cmd, *args, **kwargs)

    worker.run = model_aware_run
    try:
        return ORIGINAL_GUARDED_REVIEW_TASK(task, ModelAwareDB(db, model))
    finally:
        worker.run = original_run


def cost_aware_review_pending_batch(db: Any, max_reviews: int) -> tuple[list[dict[str, Any]], int]:
    cleanup = v06.reconcile_inactive_review_tasks(db, scan_limit=max(50, max_reviews * 10))
    original_guarded = v06.v05.v04.guarded_review_task
    v06.v05.v04.guarded_review_task = cost_aware_review_task
    try:
        live, failures = v06.v05.resilient_review_pending_batch(db, max_reviews)
    finally:
        v06.v05.v04.guarded_review_task = original_guarded
    return cleanup + live, failures


base.review_pending_batch = cost_aware_review_pending_batch


def main() -> int:
    return v06.main()


if __name__ == "__main__":
    raise SystemExit(main())
