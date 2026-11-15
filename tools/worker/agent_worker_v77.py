#!/usr/bin/env python3
"""KUEPER V7.7 worker – V7.6 plus a provider fallback chain over the Vercel AI Gateway.

Decision Thomas, 2026-11-14 (ECO-OPS-20261028-llm-fallback): when DeepSeek is paused,
out of budget or fails with 402/429/503, the task runs on the next model of
`fallback_chain` in config/provider-policy.json instead of waiting for hours.

Invariants kept from V7.6:
- Routing and cost-window deferral happen before claim; deferral consumes no attempt.
- Every model actually used reserves its own LLM budget slot (claim for the first,
  kueper_reserve_llm_invocation for fallbacks after a mid-run provider failure).
- Only when the whole chain is exhausted is the task deferred/rescheduled as before.
Each result records provider, model and fallback_depth.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker as worker  # noqa: E402
import agent_worker_v71 as v71  # noqa: E402
import agent_worker_v74 as v74  # noqa: E402
import agent_worker_v75 as v75  # noqa: E402
import agent_worker_v76 as v76  # noqa: E402
from provider_router import fallback_chain, load_policy  # noqa: E402

SOURCE = "agent-worker-v7"
GATEWAY_PROVIDERS = {"gateway", "gateway-heavy"}
_ACTIVE: dict[str, str | None] = {"provider": None, "model": None}


def gateway_enabled() -> bool:
    return bool(os.environ.get("AI_GATEWAY_API_KEY"))


def candidates_for(task: dict[str, Any], decision: Any, policy: dict[str, Any] | None = None) -> list[tuple[str, str]]:
    first = [(decision.provider, decision.model)]
    if not gateway_enabled():
        return first
    return first + fallback_chain(task, decision, policy)


# --- gateway execution -------------------------------------------------------------------

def _gateway_urls(policy: dict[str, Any] | None = None) -> tuple[str, str]:
    cfg = (policy or load_policy()).get("gateway") or {}
    return (
        str(cfg.get("openai_base_url") or "https://ai-gateway.vercel.sh/v1"),
        str(cfg.get("anthropic_base_url") or "https://ai-gateway.vercel.sh"),
    )


def classify_http_error(provider: str, code: int, message: str) -> Exception:
    lower = message.lower()
    if code == 402 or "insufficient" in lower or ("credit" in lower and "balance" in lower):
        return worker.ProviderUnavailable(provider, "billing-insufficient-balance", message, 21600)
    if code in {429, 503}:
        return worker.ProviderUnavailable(provider, f"http-{code}", message, 1800)
    return worker.WorkerError(f"{provider} HTTP {code}: {message[:2000]}")


def gateway_chat(task: dict[str, Any], provider: str, model: str) -> dict[str, Any]:
    openai_url, _ = _gateway_urls()
    prompt = (
        "You are a KUEPER Ecosystem project agent. Complete the task precisely. Do not invent facts. "
        "Return a concise structured result that states what was done, remaining uncertainty, and any concrete cross-project follow-up need.\n\n"
        f"TASK TYPE: {task.get('type')}\nTARGET: {task.get('target_project')}\nPAYLOAD:\n"
        f"{json.dumps(task.get('payload') or {}, ensure_ascii=False, indent=2)}"
    )
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    req = urllib.request.Request(f"{openai_url}/chat/completions", data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {os.environ['AI_GATEWAY_API_KEY']}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise classify_http_error(provider, exc.code, exc.read().decode(errors="replace")) from exc
    usage = data.get("usage") or {}
    return {
        "kind": "analysis",
        "content": data["choices"][0]["message"].get("content", ""),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
    }


def gateway_agent_env(env: dict[str, str], model: str) -> dict[str, str]:
    """Point Claude Code at the AI Gateway (Anthropic-compatible endpoint) with the fallback model."""
    _, anthropic_url = _gateway_urls()
    env = dict(env)
    env.update({
        "ANTHROPIC_BASE_URL": anthropic_url,
        "ANTHROPIC_AUTH_TOKEN": os.environ["AI_GATEWAY_API_KEY"],
        "ANTHROPIC_MODEL": model,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
        "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
        "CLAUDE_CODE_SUBAGENT_MODEL": model,
    })
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def _install_gateway_run_hook() -> None:
    """Wrap worker.run once: while a gateway provider is active, Claude Code talks to the gateway."""
    if getattr(worker.run, "_kueper_gateway_hook", False):
        return
    inner = worker.run

    def run(cmd, *args, **kwargs):
        provider, model = _ACTIVE["provider"], _ACTIVE["model"]
        if provider in GATEWAY_PROVIDERS and isinstance(cmd, list) and cmd and cmd[0] == "claude":
            kwargs["env"] = gateway_agent_env(dict(kwargs.get("env") or os.environ.copy()), str(model))
        return inner(cmd, *args, **kwargs)

    run._kueper_gateway_hook = True  # type: ignore[attr-defined]
    worker.run = run


@contextlib.contextmanager
def active_provider(provider: str, model: str) -> Iterator[None]:
    previous = dict(_ACTIVE)
    _ACTIVE.update(provider=provider, model=model)
    try:
        yield
    finally:
        _ACTIVE.update(previous)


def execute(task: dict[str, Any], provider: str, model: str) -> dict[str, Any]:
    if provider not in GATEWAY_PROVIDERS:
        return worker.execute_task(task, model)
    with active_provider(provider, model):
        try:
            if task.get("repository"):
                return worker.repo_task(task, model)
            return gateway_chat(task, provider, model)
        except worker.ProviderUnavailable as exc:
            # Older layers label agent failures as "deepseek"; attribute them to the gateway tier.
            if exc.provider != provider:
                raise worker.ProviderUnavailable(provider, exc.code, exc.message, exc.pause_seconds) from exc
            raise


# --- orchestration -----------------------------------------------------------------------

def run_chain(
    db: Any,
    task: dict[str, Any],
    lease: str,
    chain: list[tuple[str, str]],
    reason: str,
    executor: Callable[[dict[str, Any], str, str], dict[str, Any]] = execute,
    start_depth: int = 0,
) -> tuple[dict[str, Any] | None, str, str, int, Exception | None]:
    """Execute along the chain. chain[start_depth] already holds a budget reservation (from claim).

    Returns (outcome, provider, model, depth, last_provider_error). outcome is None when the
    whole chain is exhausted.
    """
    last_error: Exception | None = None
    task_id = str(task["id"])
    for depth in range(start_depth, len(chain)):
        provider, model = chain[depth]
        if depth > start_depth:
            if not db.rpc("kueper_provider_available", {"p_provider": provider}):
                continue
            reservation = db.rpc("kueper_reserve_llm_invocation", {
                "p_provider": provider, "p_model": model, "p_source": SOURCE,
                "p_task_id": task_id, "p_reason": f"fallback depth {depth}: {reason}"[:500],
            }) or {}
            if not reservation.get("allowed"):
                continue
            print(f"::notice title=LLM fallback::task {task_id} continues on {provider}/{model} (depth {depth})", flush=True)
        try:
            with worker.Heartbeat(db, task_id, lease):
                outcome = executor(task, provider, model)
            return outcome, provider, model, depth, last_error
        except worker.ProviderUnavailable as exc:
            last_error = exc
            db.rpc("kueper_pause_provider", {
                "p_provider": exc.provider, "p_reason": "billing-or-provider-unavailable",
                "p_error_code": exc.code, "p_error_message": exc.message[:2000],
                "p_pause_seconds": exc.pause_seconds,
            })
    return None, chain[-1][0], chain[-1][1], len(chain) - 1, last_error


def claim_along_chain(
    db: Any, candidate: dict[str, Any], worker_id: str, decision: Any, chain: list[tuple[str, str]]
) -> tuple[dict[str, Any] | None, dict[str, Any], int]:
    """Claim with the first available provider whose budget allows it. Returns (task, info, depth)."""
    info: dict[str, Any] = {"reason": "provider-paused"}
    for depth, (provider, model) in enumerate(chain):
        if not db.rpc("kueper_provider_available", {"p_provider": provider}):
            info = {"reason": "provider-paused", "provider": provider}
            continue
        attempt = SimpleNamespace(provider=provider, model=model, reason=decision.reason)
        task, detail = v76.claim_for_execution(db, candidate, worker_id, attempt)
        if task:
            return task, {**detail, "provider": provider, "model": model}, depth
        info = detail
        if str(detail.get("reason")) not in v76.BUDGET_REASONS:
            return None, detail, depth  # claim race or non-runnable: do not try other providers
    return None, info, len(chain) - 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tasks", type=int, default=int(os.environ.get("KUEPER_MAX_TASKS", "1")))
    args = parser.parse_args()
    required = ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "DEEPSEEK_API_KEY", "KUEPER_BOT_TOKEN"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"missing required secrets: {', '.join(missing)}")
    if not gateway_enabled():
        print("::warning title=LLM fallback disabled::AI_GATEWAY_API_KEY missing; running without fallback chain", flush=True)

    worker.ProviderUnavailable.__str__ = v75._provider_unavailable_str
    worker.repo_task = v74.repo_task
    _install_gateway_run_hook()
    policy = load_policy()
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

        if not decision.execute_now:
            db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": decision.available_at, "p_reason": decision.reason})
            results.append({"task": task_id, "result": "cost-deferred-unclaimed", "available_at": decision.available_at})
            continue

        chain = candidates_for(candidate, decision, policy)
        task, info, depth = claim_along_chain(db, candidate, worker_id, decision, chain)
        if not task:
            reason = str(info.get("reason") or "claim-race")
            if reason == "provider-paused":
                available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=6)).isoformat()
                db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": available_at, "p_reason": "Provider unavailable: whole fallback chain paused"})
                results.append({"task": task_id, "result": "provider-paused-unclaimed", "available_at": available_at})
                break
            if reason in v76.BUDGET_REASONS:
                available_at = v76.next_utc_day()
                db.rpc("kueper_defer_unclaimed_task", {"p_task_id": task_id, "p_available_at": available_at, "p_reason": f"LLM budget deferred: {reason}"})
                results.append({"task": task_id, "result": "budget-deferred-unclaimed", "reason": reason, "available_at": available_at})
                break
            results.append({"task": task_id, "result": "claim-race", "reason": reason})
            continue

        lease = str(task["lease_token"])
        db.rpc("kueper_start_task", {"p_task_id": task_id, "p_lease_token": lease})
        try:
            outcome, provider, model, used_depth, provider_error = run_chain(db, task, lease, chain, decision.reason, start_depth=depth)
            if outcome is None:
                exc = provider_error
                pause = getattr(exc, "pause_seconds", 1800)
                available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=pause)).isoformat()
                db.rpc("kueper_reschedule_provider_task", {"p_task_id": task_id, "p_lease_token": lease, "p_provider": getattr(exc, "provider", provider), "p_reason": str(exc), "p_available_at": available_at})
                results.append({"task": task_id, "result": "provider-paused", "provider": getattr(exc, "provider", provider), "available_at": available_at, "fallback_depth": used_depth})
                break
            outcome = {**outcome, "provider": provider, "model": model, "fallback_depth": used_depth}
            meta = {"provider": provider, "model": model, "fallback_depth": used_depth}
            if outcome.get("kind") == "park":
                db.rpc("kueper_park_task", {"p_task_id": task_id, "p_lease_token": lease, "p_reason": outcome["reason"], "p_requires_owner_decision": bool(outcome.get("requires_owner_decision"))})
                results.append({"task": task_id, "result": "parked", "reason": outcome["reason"], **meta})
            elif outcome.get("pr_url"):
                db.rpc("kueper_submit_task_for_review", {"p_task_id": task_id, "p_lease_token": lease, "p_result": outcome, "p_provider": provider, "p_model": model, "p_input_tokens": outcome.get("input_tokens"), "p_output_tokens": outcome.get("output_tokens"), "p_cost_estimate_eur": None})
                results.append({"task": task_id, "result": "review_pending", "pr_url": outcome.get("pr_url"), **meta})
            else:
                db.rpc("kueper_complete_task", {"p_task_id": task_id, "p_lease_token": lease, "p_result": outcome, "p_provider": provider, "p_model": model, "p_input_tokens": outcome.get("input_tokens"), "p_output_tokens": outcome.get("output_tokens"), "p_cost_estimate_eur": None})
                results.append({"task": task_id, "result": "completed", **meta})
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
