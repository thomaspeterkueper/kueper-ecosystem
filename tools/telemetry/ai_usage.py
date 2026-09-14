#!/usr/bin/env python3
"""Small service-role client for the KUEPER AI usage ledger.

No provider secret is stored here. The ledger records provenance, lifecycle, token
telemetry and costs around provider calls. Provider payloads/prompts are deliberately
out of scope.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from typing import Any


def _config() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY/SUPABASE_SERVICE_ROLE_KEY are required for AI usage telemetry")
    return url, key


def rpc(name: str, payload: dict[str, Any]) -> Any:
    url, key = _config()
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"{url}/rest/v1/rpc/{name}", data=body, method="POST")
    req.add_header("apikey", key)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI usage telemetry RPC {name} failed with HTTP {exc.code}: {detail[:1000]}") from exc


def log_intent(*, source_system: str, trigger_type: str, reason: str, provider: str,
               model: str, dedup_key: str, repository: str | None = None,
               pr_number: int | None = None, research_id: str | None = None,
               task_id: str | None = None, workflow_run_id: int | None = None,
               commit_sha: str | None = None, is_retry: bool = False,
               parent_intent_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    result = rpc("kueper_log_ai_usage_intent", {
        "p_source_system": source_system,
        "p_trigger_type": trigger_type,
        "p_reason": reason,
        "p_provider_requested": provider,
        "p_model_requested": model,
        "p_dedup_key": dedup_key,
        "p_repository": repository,
        "p_pr_number": pr_number,
        "p_research_id": research_id,
        "p_task_id": task_id,
        "p_workflow_run_id": workflow_run_id,
        "p_commit_sha": commit_sha,
        "p_is_retry": is_retry,
        "p_parent_intent_id": parent_intent_id,
        "p_metadata": metadata or {},
    })
    if not isinstance(result, dict) or not result.get("id"):
        raise RuntimeError(f"AI usage intent RPC returned an invalid result: {result!r}")
    return result


def log_event(intent_id: str, event_type: str, *, provider: str | None = None,
              model: str | None = None, input_tokens: int | None = None,
              output_tokens: int | None = None, cached_input_tokens: int | None = None,
              estimated_cost_usd: float | None = None, actual_cost_usd: float | None = None,
              provider_request_id: str | None = None, workflow_run_id: int | None = None,
              error_code: str | None = None, error_message: str | None = None,
              metadata: dict[str, Any] | None = None) -> Any:
    return rpc("kueper_log_ai_usage_event", {
        "p_intent_id": intent_id,
        "p_event_type": event_type,
        "p_provider": provider,
        "p_model": model,
        "p_input_tokens": input_tokens,
        "p_output_tokens": output_tokens,
        "p_cached_input_tokens": cached_input_tokens,
        "p_estimated_cost_usd": estimated_cost_usd,
        "p_actual_cost_usd": actual_cost_usd,
        "p_provider_request_id": provider_request_id,
        "p_workflow_run_id": workflow_run_id,
        "p_error_code": error_code,
        "p_error_message": error_message,
        "p_metadata": metadata or {},
    })


def _optional_int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_intent = sub.add_parser("intent")
    p_intent.add_argument("--source-system", required=True)
    p_intent.add_argument("--trigger-type", required=True)
    p_intent.add_argument("--reason", required=True)
    p_intent.add_argument("--provider", default="deepseek")
    p_intent.add_argument("--model", required=True)
    p_intent.add_argument("--dedup-key", required=True)
    p_intent.add_argument("--repository")
    p_intent.add_argument("--pr-number", type=int)
    p_intent.add_argument("--research-id")
    p_intent.add_argument("--task-id")
    p_intent.add_argument("--workflow-run-id", type=int)
    p_intent.add_argument("--commit-sha")
    p_intent.add_argument("--retry", action="store_true")

    p_event = sub.add_parser("event")
    p_event.add_argument("--intent-id", required=True)
    p_event.add_argument("--type", required=True, choices=["planned","started","completed","failed","skipped","blocked","deduped"])
    p_event.add_argument("--provider")
    p_event.add_argument("--model")
    p_event.add_argument("--input-tokens", type=int)
    p_event.add_argument("--output-tokens", type=int)
    p_event.add_argument("--estimated-cost-usd", type=float)
    p_event.add_argument("--actual-cost-usd", type=float)
    p_event.add_argument("--workflow-run-id", type=int)
    p_event.add_argument("--error-code")
    p_event.add_argument("--error-message")

    args = parser.parse_args()
    if args.command == "intent":
        result = log_intent(
            source_system=args.source_system, trigger_type=args.trigger_type,
            reason=args.reason, provider=args.provider, model=args.model,
            dedup_key=args.dedup_key, repository=args.repository,
            pr_number=args.pr_number, research_id=args.research_id,
            task_id=args.task_id, workflow_run_id=args.workflow_run_id,
            commit_sha=args.commit_sha, is_retry=args.retry,
        )
        print(json.dumps(result))
        return 0

    result = log_event(
        args.intent_id, args.type, provider=args.provider, model=args.model,
        input_tokens=args.input_tokens, output_tokens=args.output_tokens,
        estimated_cost_usd=args.estimated_cost_usd, actual_cost_usd=args.actual_cost_usd,
        workflow_run_id=args.workflow_run_id, error_code=args.error_code,
        error_message=args.error_message,
    )
    print(json.dumps({"event_id": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
