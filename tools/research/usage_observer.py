#!/usr/bin/env python3
"""Attach KUEPER AI usage provenance to research executor calls."""
from __future__ import annotations

import os
from typing import Any, Callable

from tools.telemetry.ai_usage import log_event, log_intent


def _run_id() -> int | None:
    value = os.environ.get("GITHUB_RUN_ID", "")
    return int(value) if value.isdigit() else None


def install(core: Any, source_system: str) -> None:
    """Wrap core.execute once. Telemetry is fail-closed before provider execution."""
    original: Callable[..., dict[str, Any]] = core.execute
    if getattr(original, "_kueper_usage_observed", False):
        return

    def observed(token: str, item: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(item.get("id") or "unknown")
        provider = "deepseek"
        model = os.environ.get("ANTHROPIC_MODEL") or os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL") or "deepseek-v4-flash"
        source_revision = item.get("source_blob_sha") or item.get("source_ref") or item.get("created") or "unversioned"
        reason = str(item.get("question") or item.get("title") or item.get("why_now") or "Research evidence task")
        intent = log_intent(
            source_system=source_system,
            trigger_type=os.environ.get("GITHUB_EVENT_NAME") or "research",
            reason=reason,
            provider=provider,
            model=model,
            dedup_key=f"research:{research_id}:{source_revision}:{model}",
            repository=item.get("source_repository"),
            research_id=research_id,
            workflow_run_id=_run_id(),
            commit_sha=os.environ.get("GITHUB_SHA"),
            is_retry=bool(item.get("validated_at") or item.get("last_error")),
            metadata={
                "source_project": item.get("source_project"),
                "evidence_profile": item.get("evidence_profile"),
                "publication_route_hint": item.get("publication_route_hint"),
            },
        )
        intent_id = str(intent["id"])
        log_event(intent_id, "started", provider=provider, model=model, workflow_run_id=_run_id())
        try:
            result = original(token, item, payload)
        except Exception as exc:
            log_event(intent_id, "failed", provider=provider, model=model, workflow_run_id=_run_id(),
                      error_code="research-executor-error", error_message=str(exc))
            raise

        if result.get("result") == "candidate-pr":
            log_event(intent_id, "completed", provider=provider, model=model, workflow_run_id=_run_id(),
                      metadata={"candidate_pr": result.get("pr"), "evidence_score": result.get("evidence_score")})
        else:
            log_event(intent_id, "failed", provider=provider, model=model, workflow_run_id=_run_id(),
                      error_code=str(result.get("result") or "needs-review"), error_message=str(result.get("error") or "Research did not produce a candidate PR"))
        result["usage_intent"] = intent_id
        return result

    observed._kueper_usage_observed = True  # type: ignore[attr-defined]
    core.execute = observed
