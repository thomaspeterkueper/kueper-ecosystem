#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "provider-policy.json"
VALID_COST_POLICIES = {"immediate", "normal", "prefer_off_peak", "off_peak_only"}

@dataclass(frozen=True)
class RouteDecision:
    provider: str
    model: str
    execute_now: bool
    available_at: str | None
    reason: str
    price_multiplier: float
    cost_policy: str


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _minutes(value: str) -> int:
    h, m = (int(x) for x in value.split(":", 1))
    return h * 60 + m


def _in_window(now: dt.datetime, window: dict[str, str]) -> bool:
    current = now.hour * 60 + now.minute
    start, end = _minutes(window["start"]), _minutes(window["end"])
    return start <= current < end if start < end else current >= start or current < end


def _end_of_current_peak(now: dt.datetime, windows: list[dict[str, str]]) -> dt.datetime | None:
    for window in windows:
        if not _in_window(now, window):
            continue
        end_min = _minutes(window["end"])
        candidate = now.replace(hour=end_min // 60, minute=end_min % 60, second=0, microsecond=0)
        if candidate <= now:
            candidate += dt.timedelta(days=1)
        return candidate + dt.timedelta(minutes=2)
    return None


def _payload(task: dict[str, Any]) -> dict[str, Any]:
    value = task.get("payload")
    return value if isinstance(value, dict) else {}


def _cost_policy(task: dict[str, Any], task_policy: dict[str, Any]) -> str:
    payload = _payload(task)
    explicit = str(task.get("cost_policy") or payload.get("cost_policy") or "").strip().lower()
    if explicit:
        if explicit not in VALID_COST_POLICIES:
            raise RuntimeError(f"invalid cost_policy: {explicit}")
        return explicit
    if bool(task_policy.get("cost_sensitive", False)):
        return "prefer_off_peak"
    return "normal"


def _complexity(task: dict[str, Any], task_policy: dict[str, Any]) -> str:
    payload = _payload(task)
    value = str(task.get("estimated_effort") or payload.get("estimated_effort") or task_policy.get("complexity", "medium")).lower()
    return value if value in {"low", "medium", "high"} else "medium"


def _explicit_deep_reasoning(task: dict[str, Any], policy: dict[str, Any]) -> bool:
    payload = _payload(task)
    flag = str(policy.get("routing", {}).get("explicit_deep_reasoning_flag") or "requires_deep_reasoning")
    return bool(task.get(flag) or payload.get(flag))


def _select_model(task: dict[str, Any], task_policy: dict[str, Any], provider_policy: dict[str, Any], policy: dict[str, Any]) -> tuple[str, str]:
    preferred = str(task.get("preferred_model") or "").strip()
    if preferred:
        return preferred, "explicit preferred_model"

    default_model = str(provider_policy.get("default_model") or "")
    complex_model = str(provider_policy.get("complex_model") or default_model)
    allow_pro = bool(task_policy.get("allow_pro", False))
    complexity = _complexity(task, task_policy)
    explicit_deep = _explicit_deep_reasoning(task, policy)
    priority = str(task.get("priority") or "medium").lower()
    task_type = str(task.get("type") or "").upper()

    # Pro is an escalation tier. High estimated effort alone is not enough for ordinary
    # implementation work: callers must either explicitly request deep reasoning, or the
    # task must belong to a narrow intrinsically high-reasoning class.
    intrinsic_pro = task_type in {"LONG_SIMULATION_ANALYSIS", "SECURITY"} and priority in {"high", "critical"}
    research_pro = task_type == "RESEARCH" and priority in {"high", "critical"}
    if allow_pro and (explicit_deep or intrinsic_pro or research_pro):
        reason = "explicit deep-reasoning escalation" if explicit_deep else "high-risk task-class escalation"
        return complex_model, reason

    return default_model, f"Flash default; complexity={complexity} without Pro escalation evidence"


def route(task: dict[str, Any], now: dt.datetime | None = None, policy: dict[str, Any] | None = None) -> RouteDecision:
    policy = policy or load_policy()
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    now = now.astimezone(dt.timezone.utc)

    task_type = str(task.get("type") or "").upper()
    priority = str(task.get("priority") or "medium").lower()
    task_policy = policy.get("task_classes", {}).get(task_type, {"cost_sensitive": True, "complexity": "medium", "allow_pro": False})
    cost_policy = _cost_policy(task, task_policy)

    provider = str(task.get("preferred_provider") or "deepseek")
    provider_policy = policy.get("providers", {}).get(provider, {})
    if not provider_policy.get("enabled", False):
        raise RuntimeError(f"provider disabled or unknown: {provider}")

    model, model_reason = _select_model(task, task_policy, provider_policy, policy)

    windows = provider_policy.get("peak_windows", [])
    in_peak = any(_in_window(now, w) for w in windows)
    multiplier = float(provider_policy.get("peak_multiplier", 1.0)) if in_peak else 1.0
    defer_priorities = set(provider_policy.get("defer_during_peak", []))
    never_defer = set(provider_policy.get("never_defer", []))

    urgent = priority in never_defer or cost_policy == "immediate"
    wants_off_peak = cost_policy in {"prefer_off_peak", "off_peak_only"}
    should_defer = in_peak and wants_off_peak and not urgent and (
        cost_policy == "off_peak_only" or priority in defer_priorities
    )

    if should_defer:
        resume = _end_of_current_peak(now, windows)
        return RouteDecision(
            provider,
            model,
            False,
            resume.isoformat() if resume else None,
            f"{model_reason}; cost-aware scheduling deferred task until provider peak window ends",
            multiplier,
            cost_policy,
        )

    reason = model_reason
    if in_peak and urgent:
        reason += "; peak accepted because task is urgent/immediate"
    elif in_peak and not wants_off_peak:
        reason += "; peak accepted because task does not request off-peak execution"
    elif not in_peak and wants_off_peak:
        reason += "; preferred off-peak window available"
    return RouteDecision(provider, model, True, None, reason, multiplier, cost_policy)
