#!/usr/bin/env python3
"""Deterministic provider-outage preflight for pending PR reviews.

This module is intentionally NOT wired into the production reviewer. It can
classify obvious fail-closed conditions while an LLM reviewer is unavailable,
but it can never emit PASS and can never complete a review task.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

SENSITIVE_PREFIXES = (
    ".github/workflows/",
    "supabase/migrations/",
    "migrations/",
    "security/",
    "governance/",
    "decisions/",
    "research/candidates/",
)


@dataclass(frozen=True)
class PreflightResult:
    disposition: str
    reasons: tuple[str, ...]
    changed_paths: tuple[str, ...]


def normalize_paths(paths: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for raw in paths:
        value = str(raw or "").strip().replace("\\", "/")
        if not value:
            continue
        normalized.append(PurePosixPath(value).as_posix())
    return tuple(sorted(set(normalized)))


def classify_provider_outage_preflight(
    *,
    expected_head_sha: str,
    current_head_sha: str,
    pr_state: str,
    changed_paths: Iterable[str],
) -> PreflightResult:
    """Return a deterministic DEFERRED_PROVIDER_UNAVAILABLE/BLOCKED result, never PASS.

    BLOCKED means the task should not even be presented as reviewable because
    immutable transport/state assumptions are violated.
    DEFERRED_PROVIDER_UNAVAILABLE means the PR is structurally reviewable but
    still requires the normal independent reviewer.
    """
    paths = normalize_paths(changed_paths)
    reasons: list[str] = []

    expected = expected_head_sha.strip().lower()
    current = current_head_sha.strip().lower()
    state = pr_state.strip().upper()

    if state != "OPEN":
        reasons.append(f"pr-not-open:{state or 'UNKNOWN'}")
    if not expected or not current or expected != current:
        reasons.append("head-sha-mismatch")
    if not paths:
        reasons.append("no-changed-paths")

    if reasons:
        return PreflightResult("BLOCKED", tuple(reasons), paths)

    sensitive = [p for p in paths if p.startswith(SENSITIVE_PREFIXES)]
    if sensitive:
        reasons.append("sensitive-paths-require-independent-review")
    else:
        reasons.append("provider-unavailable-independent-review-required")

    return PreflightResult("DEFERRED_PROVIDER_UNAVAILABLE", tuple(reasons), paths)
