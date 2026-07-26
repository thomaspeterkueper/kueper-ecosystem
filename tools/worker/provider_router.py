#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "provider-policy.json"

@dataclass(frozen=True)
class RouteDecision:
    provider: str
    model: str
    execute_now: bool
    available_at: str | None
    reason: str
    price_multiplier: float


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


def route(task: dict[str, Any], now: dt.datetime | None = None, policy: dict[str, Any] | None = None) -> RouteDecision:
    policy = policy or load_policy()
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    now = now.astimezone(dt.timezone.utc)

    task_type = str(task.get("type") or "").upper()
    priority = str(task.get("priority") or "medium").lower()
    task_policy = policy.get("task_classes", {}).get(task_type, {"cost_sensitive": False, "complexity": "medium"})

    provider = str(task.get("preferred_provider") or "deepseek")
    provider_policy = policy.get("providers", {}).get(provider, {})
    if not provider_policy.get("enabled", False):
        raise RuntimeError(f"provider disabled or unknown: {provider}")

    complexity = task_policy.get("complexity", "medium")
    model = str(task.get("preferred_model") or (
        provider_policy.get("complex_model") if complexity == "high" else provider_policy.get("default_model")
    ))

    windows = provider_policy.get("peak_windows", [])
    in_peak = any(_in_window(now, w) for w in windows)
    multiplier = float(provider_policy.get("peak_multiplier", 1.0)) if in_peak else 1.0
    cost_sensitive = bool(task_policy.get("cost_sensitive", False))
    defer_priorities = set(provider_policy.get("defer_during_peak", []))
    never_defer = set(provider_policy.get("never_defer", []))

    if in_peak and cost_sensitive and priority in defer_priorities and priority not in never_defer:
        resume = _end_of_current_peak(now, windows)
        return RouteDecision(provider, model, False, resume.isoformat() if resume else None,
                             "cost-sensitive task deferred until provider peak window ends", multiplier)

    reason = "policy route"
    if in_peak:
        reason += "; peak accepted because task is urgent or not cost-sensitive"
    return RouteDecision(provider, model, True, None, reason, multiplier)
