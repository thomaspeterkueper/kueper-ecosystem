#!/usr/bin/env python3
"""Declarative fail-closed external-check gate for PR review completion.

Policies live in registry/merge-gates.json. Every required check must resolve on the
current PR head and be completed successfully. Missing, stale, pending, ambiguous, or
failed required checks block semantic review/completion.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "registry" / "merge-gates.json"
_SUCCESS_CONCLUSIONS = {"success", "neutral", "skipped"}


class MergeGateError(RuntimeError):
    pass


def load_policy(repository: str, path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any] | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    policies = data.get("policies")
    if not isinstance(policies, list):
        raise MergeGateError("merge gate registry has no policies array")
    matches = [p for p in policies if isinstance(p, dict) and p.get("repository") == repository]
    if len(matches) > 1:
        raise MergeGateError(f"multiple merge gate policies for {repository}")
    return matches[0] if matches else None


def evaluate(policy: dict[str, Any], head_sha: str, status_payload: dict[str, Any], check_payload: dict[str, Any]) -> dict[str, Any]:
    if policy.get("mode") != "fail-closed":
        raise MergeGateError("only fail-closed merge gate mode is supported")
    if str(status_payload.get("sha") or "").lower() != head_sha.lower():
        return {"allowed": False, "reason": "stale-status-head", "details": []}

    check_runs = check_payload.get("check_runs")
    statuses = status_payload.get("statuses")
    if not isinstance(check_runs, list) or not isinstance(statuses, list):
        return {"allowed": False, "reason": "unreadable-check-payload", "details": []}

    required = policy.get("required")
    if not isinstance(required, list) or not required:
        return {"allowed": False, "reason": "empty-required-check-policy", "details": []}

    details: list[dict[str, Any]] = []
    for requirement in required:
        if not isinstance(requirement, dict):
            return {"allowed": False, "reason": "invalid-required-check-policy", "details": details}
        req_id = str(requirement.get("id") or "unnamed")
        source = requirement.get("source")

        if source == "commit_status":
            context = str(requirement.get("context") or "")
            matches = [s for s in statuses if isinstance(s, dict) and str(s.get("context") or "") == context]
            if len(matches) != 1:
                details.append({"id": req_id, "state": "missing-or-ambiguous", "matches": len(matches)})
                return {"allowed": False, "reason": f"required-check-{req_id}-missing-or-ambiguous", "details": details}
            state = str(matches[0].get("state") or "").lower()
            details.append({"id": req_id, "state": state})
            if state != "success":
                return {"allowed": False, "reason": f"required-check-{req_id}-{state or 'unknown'}", "details": details}
            continue

        if source == "check_run":
            name = str(requirement.get("name") or "")
            matches = [r for r in check_runs if isinstance(r, dict) and str(r.get("name") or "") == name]
            if len(matches) != 1:
                details.append({"id": req_id, "state": "missing-or-ambiguous", "matches": len(matches)})
                return {"allowed": False, "reason": f"required-check-{req_id}-missing-or-ambiguous", "details": details}
            run = matches[0]
            run_head = str(run.get("head_sha") or "").lower()
            if run_head != head_sha.lower():
                details.append({"id": req_id, "state": "stale-head", "head_sha": run_head})
                return {"allowed": False, "reason": f"required-check-{req_id}-stale-head", "details": details}
            status = str(run.get("status") or "").lower()
            conclusion = str(run.get("conclusion") or "").lower()
            details.append({"id": req_id, "status": status, "conclusion": conclusion})
            if status != "completed":
                return {"allowed": False, "reason": f"required-check-{req_id}-incomplete", "details": details}
            if conclusion not in _SUCCESS_CONCLUSIONS:
                return {"allowed": False, "reason": f"required-check-{req_id}-{conclusion or 'unknown'}", "details": details}
            continue

        return {"allowed": False, "reason": f"required-check-{req_id}-unknown-source", "details": details}

    return {"allowed": True, "reason": "all-required-checks-green", "details": details}


def _run_json(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    token = env.get("KUEPER_BOT_TOKEN") or env.get("GITHUB_TOKEN")
    if token:
        env["GH_TOKEN"] = token
    cp = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, check=False)
    if cp.returncode != 0:
        raise MergeGateError(f"command failed ({cp.returncode}): {(cp.stdout or '')[-2000:]}")
    try:
        return json.loads(cp.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise MergeGateError("invalid JSON from GitHub") from exc


def evaluate_pr(repository: str, pr_url: str, policy_path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    policy = load_policy(repository, policy_path)
    if policy is None:
        return {"allowed": True, "reason": "no-required-check-policy", "details": [], "head_sha": None}

    meta = _run_json(["gh", "pr", "view", pr_url, "--json", "headRefOid,state"])
    if str(meta.get("state") or "").upper() != "OPEN":
        return {"allowed": False, "reason": "pr-not-open", "details": [], "head_sha": meta.get("headRefOid")}
    head_sha = str(meta.get("headRefOid") or "").strip()
    if not head_sha:
        return {"allowed": False, "reason": "missing-current-head", "details": [], "head_sha": None}

    status_payload = _run_json(["gh", "api", f"repos/{repository}/commits/{head_sha}/status"])
    check_payload = _run_json(["gh", "api", "-H", "Accept: application/vnd.github+json", f"repos/{repository}/commits/{head_sha}/check-runs"])
    result = evaluate(policy, head_sha, status_payload, check_payload)
    result["head_sha"] = head_sha
    return result
