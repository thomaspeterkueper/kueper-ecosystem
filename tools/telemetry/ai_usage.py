#!/usr/bin/env python3
"""Service-role client for the KUEPER AI usage ledger.

Semantic work is claimed atomically before provider execution. A repeated semantic
request is deduplicated unless the previous attempt is explicitly retryable.
Provider payloads/prompts and provider secrets are deliberately out of scope.
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


def claim_attempt(*, source_system: str, trigger_type: str, reason: str, provider: str,
                  model: str, semantic_key: str, repository: str | None = None,
                  pr_number: int | None = None, research_id: str | None = None,
                  task_id: str | None = None, workflow_run_id: int | None = None,
                  commit_sha: str | None = None, retry_mode: str = "none",
                  retry_reason: str | None = None,
                  metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    result = rpc("kueper_claim_ai_usage_attempt", {
        "p_source_system": source_system,
        "p_trigger_type": trigger_type,
        "p_reason": reason,
        "p_provider_requested": provider,
        "p_model_requested": model,
        "p_semantic_key": semantic_key,
        "p_repository": repository,
        "p_pr_number": pr_number,
        "p_research_id": research_id,
        "p_task_id": task_id,
        "p_workflow_run_id": workflow_run_id,
        "p_commit_sha": commit_sha,
        "p_retry_mode": retry_mode,
        "p_retry_reason": retry_reason,
        "p_metadata": metadata or {},
    })
    if not isinstance(result, dict) or not result.get("id") or "execute_allowed" not in result:
        raise RuntimeError(f"AI usage attempt claim returned an invalid result: {result!r}")
    return result


def log_event(intent_id: str, event_type: str, *, provider: str | None = None,
              model: str | None = None, input_tokens: int | None = None,
              output_tokens: int | None = None, cached_input_tokens: int | None = None,
              estimated_cost_usd: float | None = None, actual_cost_usd: float | None = None,
              provider_request_id: str | None = None, workflow_run_id: int | None = None,
              error_code: str | None = None, error_message: str | None = None,
              failure_class: str | None = None,
              metadata: dict[str, Any] | None = None) -> Any:
    return rpc("kueper_log_ai_usage_event_v2", {
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
        "p_failure_class": failure_class,
        "p_metadata": metadata or {},
    })


def classify_failure(error_code: str | int | None, message: str | None) -> str:
    """Map provider/executor failures onto retry governance classes."""
    code = str(error_code or "").lower()
    text = f"{code} {message or ''}".lower()
    if "402" in text or "insufficient balance" in text or "billing" in text:
        return "provider-billing"
    if "401" in text or "403" in text or "unauthorized" in text or "forbidden" in text:
        return "auth"
    if "unknown model" in text or "invalid model" in text or "configuration" in text or "config" in code:
        return "configuration"
    if "429" in text or "rate limit" in text or "rate-limit" in text:
        return "rate-limit"
    if any(marker in text for marker in ("500", "502", "503", "504", "provider-5xx")):
        return "provider-5xx"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if any(marker in text for marker in ("connection reset", "connection refused", "network", "temporary failure")):
        return "network"
    return "domain"


def retry_request_from_env(*, automatic_default: bool = False) -> tuple[str, str | None]:
    explicit_mode = (os.environ.get("KUEPER_AI_RETRY_MODE") or "").strip().lower()
    reason = (os.environ.get("KUEPER_AI_RETRY_REASON") or "").strip() or None
    if explicit_mode:
        if explicit_mode not in {"none", "automatic", "manual"}:
            raise RuntimeError(f"Invalid KUEPER_AI_RETRY_MODE: {explicit_mode}")
        if explicit_mode == "manual" and not reason:
            raise RuntimeError("KUEPER_AI_RETRY_REASON is required for manual AI retries")
        return explicit_mode, reason
    return ("automatic", None) if automatic_default else ("none", None)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_claim = sub.add_parser("claim")
    p_claim.add_argument("--source-system", required=True)
    p_claim.add_argument("--trigger-type", required=True)
    p_claim.add_argument("--reason", required=True)
    p_claim.add_argument("--provider", default="deepseek")
    p_claim.add_argument("--model", required=True)
    p_claim.add_argument("--semantic-key", required=True)
    p_claim.add_argument("--repository")
    p_claim.add_argument("--pr-number", type=int)
    p_claim.add_argument("--research-id")
    p_claim.add_argument("--task-id")
    p_claim.add_argument("--workflow-run-id", type=int)
    p_claim.add_argument("--commit-sha")
    p_claim.add_argument("--retry-mode", choices=["none", "automatic", "manual"], default="none")
    p_claim.add_argument("--retry-reason")

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
    p_event.add_argument("--failure-class")

    args = parser.parse_args()
    if args.command == "claim":
        result = claim_attempt(
            source_system=args.source_system, trigger_type=args.trigger_type,
            reason=args.reason, provider=args.provider, model=args.model,
            semantic_key=args.semantic_key, repository=args.repository,
            pr_number=args.pr_number, research_id=args.research_id,
            task_id=args.task_id, workflow_run_id=args.workflow_run_id,
            commit_sha=args.commit_sha, retry_mode=args.retry_mode,
            retry_reason=args.retry_reason,
        )
        print(json.dumps(result))
        return 0

    result = log_event(
        args.intent_id, args.type, provider=args.provider, model=args.model,
        input_tokens=args.input_tokens, output_tokens=args.output_tokens,
        estimated_cost_usd=args.estimated_cost_usd, actual_cost_usd=args.actual_cost_usd,
        workflow_run_id=args.workflow_run_id, error_code=args.error_code,
        error_message=args.error_message, failure_class=args.failure_class,
    )
    print(json.dumps({"event_id": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
