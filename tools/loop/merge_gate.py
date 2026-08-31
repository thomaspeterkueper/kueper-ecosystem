#!/usr/bin/env python3
"""KUEPER fail-closed external-check merge gate for the autonomous loop.

The V2 loop may enable GitHub auto-merge on a PR only when the target
repository's registry entry declares a ``merge_gate`` policy and every
required external check has a completed, successful result for the exact
current PR head SHA.

Fail-closed semantics — a green verdict is never derived from absent data:

- no ``merge_gate`` policy declared        -> blocked (mode ``missing``);
- explicit ``mode: "off"``                 -> allowed without checks (owner opt-out);
- invalid policy or unknown check id       -> blocked;
- required check without a result for the
  current head (including results that
  belong to an older head)                 -> blocked (``missing``);
- failed/error/neutral/skipped/cancelled
  result or completed run without a
  success conclusion                       -> blocked (``failed``);
- pending/in-progress result               -> blocked (``incomplete``);
- truncated check evidence                 -> blocked (``truncated``);
- evidence collection failure              -> blocked.

Canonical policy structure: ``schemas/project-registry.schema.json#merge_gate``.
Reference: ``docs/architecture/EXTERNAL_CHECK_MERGE_GATE.md``.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

API = "https://api.github.com"
MAX_CHECK_PAGES = 5

# Known check kinds map to default GitHub matchers. String entries in a
# registry ``merge_gate.required`` list resolve through this table; custom
# check descriptors may be declared as objects with id/source/name/match.
KNOWN_CHECKS: dict[str, dict[str, str]] = {
    "vercel": {"id": "vercel", "source": "any", "name": "vercel", "match": "contains"},
    "supabase-preview": {
        "id": "supabase-preview",
        "source": "check-run",
        "name": "preview branch",
        "match": "contains",
        "app_slug": "supabase",
    },
    "supabase-migrations": {
        "id": "supabase-migrations",
        "source": "check-run",
        "name": "migrations",
        "match": "contains",
        "app_slug": "supabase",
    },
}

FAILING_CONCLUSIONS = {
    "failure", "error", "cancelled", "timed_out", "action_required",
    "neutral", "skipped", "stale", "startup_failure",
}
INCOMPLETE_STATUSES = {"queued", "in_progress", "pending", "requested", "waiting"}
VALID_SOURCES = {"check-run", "status", "any"}
VALID_MATCH = {"contains", "exact", "prefix"}


def normalize_descriptor(raw: Any) -> dict[str, str] | None:
    """Resolve a required-check entry to a canonical matcher, or None if unknown."""
    if isinstance(raw, str):
        desc = KNOWN_CHECKS.get(raw.strip().lower())
        return dict(desc) if desc else None
    if isinstance(raw, dict):
        rid = str(raw.get("id") or "").strip()
        name = str(raw.get("name") or "").strip()
        source = str(raw.get("source") or "check-run").strip().lower()
        match = str(raw.get("match") or "contains").strip().lower()
        if not rid or not name or source not in VALID_SOURCES or match not in VALID_MATCH:
            return None
        desc = {"id": rid, "source": source, "name": name, "match": match}
        if raw.get("app_slug"):
            desc["app_slug"] = str(raw["app_slug"]).strip()
        return desc
    return None


def normalize_policy(project: Any) -> dict[str, Any] | None:
    """Extract the merge_gate policy from a registry project (dict or dataclass).

    Returns None when no policy is declared (fail-closed default) and raises
    ValueError for a declared but invalid policy — both must never allow a merge.
    """
    if isinstance(project, dict):
        mg = project.get("merge_gate")
    else:
        mg = getattr(project, "merge_gate", None)
    if mg is None:
        return None
    mode = str(mg.get("mode") or "").strip().lower()
    if mode == "off":
        return {"mode": "off"}
    if mode != "fail-closed":
        raise ValueError(f"invalid merge_gate mode {mode!r}")
    required = mg.get("required")
    if not isinstance(required, list) or not required:
        raise ValueError("merge_gate mode fail-closed requires a non-empty required list")
    return {"mode": "fail-closed", "required": required}


def _decision(allowed: bool, mode: str, checks: list[dict[str, str]], reasons: list[str]) -> dict[str, Any]:
    return {
        "allowed": bool(allowed),
        "mode": mode,
        "blocking_reasons": [str(r) for r in reasons],
        "checks": checks,
    }


def _match(name: str, pattern: str, mode: str) -> bool:
    name = str(name or "").lower()
    pattern = str(pattern or "").lower()
    if mode == "exact":
        return name == pattern
    if mode == "prefix":
        return name.startswith(pattern)
    return pattern in name


def _evaluate_check(desc: dict[str, str], evidence: dict[str, Any], head_sha: str) -> dict[str, str]:
    source = desc.get("source")
    run_matches: list[dict[str, Any]] = []
    status_matches: list[dict[str, Any]] = []
    if source in {"check-run", "any"}:
        run_matches = [
            r for r in evidence.get("check_runs") or []
            if str(r.get("head_sha") or "").lower() == head_sha
            and _match(r.get("name") or "", desc["name"], desc.get("match", "contains"))
            and (not desc.get("app_slug") or str(r.get("app_slug") or "").lower() == desc["app_slug"].lower())
        ]
    if source in {"status", "any"}:
        status_matches = [
            s for s in evidence.get("statuses") or []
            if str(s.get("head_sha") or "").lower() == head_sha
            and _match(s.get("context") or "", desc["name"], desc.get("match", "contains"))
        ]
    matches = run_matches + status_matches
    if not matches:
        return {"id": desc["id"], "state": "missing", "detail": f"no result for head {head_sha[:8]}"}

    failed: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    for m in run_matches:
        conclusion = m.get("conclusion")
        status = str(m.get("status") or "")
        if status in INCOMPLETE_STATUSES or (conclusion is None and status != "completed"):
            incomplete.append(m)
        elif conclusion != "success":
            failed.append(m)
    for m in status_matches:
        state = str(m.get("state") or "")
        if state == "pending":
            incomplete.append(m)
        elif state != "success":
            failed.append(m)

    if failed:
        detail = "; ".join(sorted({
            f"{m.get('name') or m.get('context')}: {m.get('conclusion') or m.get('state')}" for m in failed
        }))
        return {"id": desc["id"], "state": "failed", "detail": detail}
    if incomplete:
        detail = "; ".join(sorted({
            f"{m.get('name') or m.get('context')}: {m.get('status') or m.get('state')}" for m in incomplete
        }))
        return {"id": desc["id"], "state": "incomplete", "detail": detail}
    return {"id": desc["id"], "state": "success", "detail": f"{len(matches)} matching result(s) for head {head_sha[:8]}"}


def evaluate(policy: dict[str, Any] | None, evidence: dict[str, Any], head_sha: str) -> dict[str, Any]:
    """Deterministically evaluate a merge gate policy against collected evidence.

    ``evidence`` is the shape produced by :func:`collect_evidence`. Only
    results whose ``head_sha`` equals ``head_sha`` count; results for older
    heads are ignored and therefore surface as ``missing``. No network access.
    """
    head_sha = str(head_sha or "").strip().lower()
    if policy is None:
        return _decision(False, "missing", [], [
            "repository declares no merge_gate policy; auto-merge requires an explicit policy"
        ])
    mode = policy.get("mode")
    if mode == "off":
        return _decision(True, "off", [], [])
    if mode != "fail-closed":
        return _decision(False, "invalid", [], [f"invalid merge_gate mode {mode!r}"])
    if not head_sha:
        return _decision(False, mode, [], ["PR head SHA unavailable"])
    if str(evidence.get("head_sha") or "").strip().lower() != head_sha:
        return _decision(False, mode, [], [
            f"check evidence belongs to head {evidence.get('head_sha')} instead of {head_sha}"
        ])
    if evidence.get("truncated"):
        return _decision(False, mode, [], ["check evidence incomplete (truncated API pages)"])

    required = policy.get("required")
    if not isinstance(required, list) or not required:
        return _decision(False, mode, [], ["policy declares no required checks"])

    checks: list[dict[str, str]] = []
    reasons: list[str] = []
    for raw in required:
        desc = normalize_descriptor(raw)
        if desc is None:
            checks.append({"id": str(raw), "state": "unknown", "detail": "unknown required check id"})
            reasons.append(f"required check {raw!r} cannot be evaluated")
            continue
        result = _evaluate_check(desc, evidence, head_sha)
        checks.append(result)
        if result["state"] != "success":
            reasons.append(f"required check {result['id']!r} is {result['state']}: {result['detail']}")
    return _decision(not reasons, mode, checks, reasons)


def gh_json(token: str, path: str) -> Any:
    """GET a GitHub API path; returns parsed JSON or None for 404."""
    req = urllib.request.Request(API + path)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"GitHub GET {path}: HTTP {exc.code}") from exc


def collect_evidence(token: str, repo: str, head_sha: str) -> dict[str, Any]:
    """Collect check runs and commit statuses for exactly one head SHA."""
    evidence: dict[str, Any] = {"head_sha": head_sha, "check_runs": [], "statuses": [], "truncated": False}
    collected = 0
    total: int | None = None
    for page in range(1, MAX_CHECK_PAGES + 1):
        data = gh_json(token, f"/repos/{repo}/commits/{head_sha}/check-runs?per_page=100&page={page}")
        if data is None:
            break
        for item in data.get("check_runs") or []:
            app = item.get("app") or {}
            evidence["check_runs"].append({
                "name": str(item.get("name") or ""),
                "conclusion": str(item.get("conclusion") or "") or None,
                "status": str(item.get("status") or ""),
                "app_slug": str(app.get("slug") or ""),
                "head_sha": str(item.get("head_sha") or ""),
            })
            collected += 1
        total = data.get("total_count")
        if total is None or collected >= total:
            break
    if total is not None and collected < total:
        evidence["truncated"] = True

    status_data = gh_json(token, f"/repos/{repo}/commits/{head_sha}/status")
    for item in (status_data or {}).get("statuses") or []:
        evidence["statuses"].append({
            "context": str(item.get("context") or ""),
            "state": str(item.get("state") or ""),
            "head_sha": head_sha,
        })
    return evidence


def gate_decision(token: str, project: Any, repo: str, head_sha: str) -> dict[str, Any]:
    """End-to-end merge gate decision for one PR head (network + policy + evaluate).

    Never raises for policy or evidence problems: every failure mode returns a
    blocked decision, so callers can rely on ``allowed`` being meaningful.
    """
    try:
        policy = normalize_policy(project)
    except ValueError as exc:
        return _decision(False, "invalid", [], [f"invalid merge_gate policy: {exc}"])
    if policy is None:
        return _decision(False, "missing", [], [
            "repository declares no merge_gate policy; auto-merge requires an explicit policy"
        ])
    if policy.get("mode") == "off":
        return _decision(True, "off", [], [])
    try:
        evidence = collect_evidence(token, repo, head_sha)
    except Exception as exc:
        return _decision(False, policy.get("mode"), [], [f"merge gate evidence collection failed: {exc}"])
    return evaluate(policy, evidence, head_sha)
