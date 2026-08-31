#!/usr/bin/env python3
"""KUEPER automated PR reviewer v0.1.

Scans review_pending tasks, reviews each unseen PR head, persists the review,
creates one idempotent REVIEW_FIX task for blocking findings, and completes the
originating task only after a persisted PASS on the current head.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

WORKER_DIR = Path(__file__).resolve().parents[1] / "worker"
sys.path.insert(0, str(WORKER_DIR))
import agent_worker as worker  # noqa: E402
import agent_worker_v71 as v71  # noqa: E402

REVIEW_CATEGORIES = {
    "TASK_FULFILLMENT",
    "ARCHITECTURE",
    "CORRECTNESS",
    "TEST_QUALITY",
    "INTEGRATION",
    "SECURITY_GOVERNANCE",
    "COST_RUNTIME",
}
SEVERITIES = {"low", "medium", "high", "critical"}


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise worker.WorkerError("reviewer returned no JSON object")
    return json.loads(match.group(0))


def validate_review(data: dict[str, Any]) -> dict[str, Any]:
    verdict = data.get("verdict")
    if verdict not in {"PASS", "CHANGES_REQUIRED"}:
        raise worker.WorkerError(f"invalid review verdict: {verdict}")
    findings = data.get("findings")
    if not isinstance(findings, list):
        raise worker.WorkerError("review findings must be an array")

    seen_ids: set[str] = set()
    blocking = 0
    normalized: list[dict[str, Any]] = []
    for raw in findings:
        if not isinstance(raw, dict):
            raise worker.WorkerError("each review finding must be an object")
        finding_id = str(raw.get("finding_id") or "").strip()
        if not finding_id or finding_id in seen_ids:
            raise worker.WorkerError("finding_id must be stable, non-empty and unique")
        seen_ids.add(finding_id)
        severity = str(raw.get("severity") or "").lower()
        category = str(raw.get("category") or "")
        confidence = float(raw.get("confidence", 0))
        is_blocking = bool(raw.get("blocking"))
        if severity not in SEVERITIES:
            raise worker.WorkerError(f"invalid severity for {finding_id}: {severity}")
        if category not in REVIEW_CATEGORIES:
            raise worker.WorkerError(f"invalid category for {finding_id}: {category}")
        if confidence < 0 or confidence > 1:
            raise worker.WorkerError(f"invalid confidence for {finding_id}")
        if is_blocking:
            blocking += 1
        normalized.append({
            "finding_id": finding_id,
            "severity": severity,
            "category": category,
            "path": raw.get("path"),
            "line": raw.get("line"),
            "issue": str(raw.get("issue") or "").strip(),
            "expected": str(raw.get("expected") or "").strip(),
            "evidence": raw.get("evidence") if isinstance(raw.get("evidence"), list) else [],
            "confidence": confidence,
            "blocking": is_blocking,
        })

    if verdict == "PASS" and blocking:
        raise worker.WorkerError("PASS review contains blocking findings")
    if verdict == "CHANGES_REQUIRED" and not blocking:
        raise worker.WorkerError("CHANGES_REQUIRED review contains no blocking finding")

    return {
        "verdict": verdict,
        "summary": str(data.get("summary") or "").strip(),
        "findings": normalized,
    }


def gh_json(root: Path, env: dict[str, str], *args: str) -> dict[str, Any]:
    raw = worker.run(["gh", *args], cwd=root, env=env).stdout
    return json.loads(raw)


def review_task(task: dict[str, Any], db: v71.PatchedSupabaseRPC) -> dict[str, Any]:
    repo = str(task.get("repository") or "").strip()
    pr_url = str(task.get("pr_url") or "").strip()
    task_id = str(task.get("id") or "")
    if not repo or not pr_url or not task_id:
        raise worker.WorkerError("review_pending task lacks repository/pr_url/id")

    token = os.environ["KUEPER_BOT_TOKEN"]
    with tempfile.TemporaryDirectory(prefix="kueper-review-") as temp:
        root = Path(temp) / "repo"
        worker.run(["git", "clone", "--quiet", worker.clone_url(repo, token), str(root)])
        gh_env = os.environ.copy()
        gh_env["GH_TOKEN"] = token
        meta = gh_json(root, gh_env, "pr", "view", pr_url, "--json", "state,headRefName,headRefOid,baseRefName,title")
        if meta.get("state") != "OPEN":
            state = str(meta.get("state") or "UNKNOWN").upper()
            if state not in {"CLOSED", "MERGED"}:
                raise worker.WorkerError(f"unexpected PR state: {state}")
            db.rpc("kueper_close_inactive_pr_review_task", {
                "p_task_id": task_id,
                "p_pr_url": pr_url,
                "p_pr_state": state,
            })
            return {"task": task_id, "result": "terminal", "reason": f"PR is {state}"}

        head_sha = str(meta.get("headRefOid") or "").strip().lower()
        head_branch = str(meta.get("headRefName") or "").strip()
        if not head_sha or not head_branch:
            raise worker.WorkerError("could not resolve current PR head")

        previous = db.rpc("kueper_get_pr_review", {"p_task_id": task_id, "p_head_sha": head_sha})
        if previous:
            return {"task": task_id, "result": "deduplicated", "head_sha": head_sha, "verdict": previous.get("verdict")}

        worker.run(["git", "fetch", "origin", head_branch], cwd=root)
        worker.run(["git", "checkout", "--detach", head_sha], cwd=root)
        diff = worker.run(["gh", "pr", "diff", pr_url], cwd=root, env=gh_env).stdout
        if len(diff) > 180_000:
            diff = diff[:180_000] + "\n\n[DIFF TRUNCATED BY REVIEWER BOUND]"

        governance: list[str] = []
        for name in ("AGENTS.md", "README.md"):
            path = root / name
            if path.exists() and path.is_file():
                governance.append(f"## {name}\n{path.read_text(errors='replace')[:20_000]}")

        task_payload = task.get("payload") or {}
        implementation_provider = task.get("agent_provider")
        implementation_model = task.get("agent_model")
        review_model = "deepseek-v4-pro"
        prompt = f"""You are the independent KUEPER Automated PR Review Agent.
Review the current pull request against the ORIGINATING TASK, repository governance,
and the full diff. Be adversarial and concrete. Do not implement fixes.

Originating task id: {task_id}
Task type: {task.get('type')}
Priority: {task.get('priority')}
Repository: {repo}
PR: {pr_url}
PR title: {meta.get('title')}
Current head SHA: {head_sha}
Implementation provider/model: {implementation_provider}/{implementation_model}
Review provider/model: DeepSeek/{review_model} (isolated reviewer context; same provider family if no independent provider is configured)

Originating payload / acceptance criteria:
{json.dumps(task_payload, ensure_ascii=False, indent=2)}

Repository governance/context:
{chr(10).join(governance)}

Complete PR diff (bounded only if exceptionally large):
{diff}

Review dimensions:
- TASK_FULFILLMENT
- ARCHITECTURE
- CORRECTNESS
- TEST_QUALITY
- INTEGRATION
- SECURITY_GOVERNANCE
- COST_RUNTIME

Important lifecycle checks include idempotency, state transitions, boundary metadata,
head-SHA correctness and whether tests actually prove the requested behavior.

Return ONLY valid JSON with exactly this top-level shape:
{{
  "verdict": "PASS" | "CHANGES_REQUIRED",
  "summary": "concise review summary",
  "findings": [
    {{
      "finding_id": "stable-semantic-fingerprint",
      "severity": "low|medium|high|critical",
      "category": "TASK_FULFILLMENT|ARCHITECTURE|CORRECTNESS|TEST_QUALITY|INTEGRATION|SECURITY_GOVERNANCE|COST_RUNTIME",
      "path": "path/or/null",
      "line": 123,
      "issue": "specific defect",
      "expected": "required behavior",
      "evidence": ["task:...", "diff:...", "test:..."],
      "confidence": 0.0,
      "blocking": true
    }}
  ]
}}
PASS is allowed only when there are no blocking findings. Do not invent findings merely to avoid PASS.
"""
        env = os.environ.copy()
        env.update({
            "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
            "ANTHROPIC_AUTH_TOKEN": os.environ["DEEPSEEK_API_KEY"],
            "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1m]",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
            "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
            "CLAUDE_CODE_EFFORT_LEVEL": "max",
        })
        cp = worker.run(["claude", "-p", "--dangerously-skip-permissions", prompt], cwd=root, env=env, check=False)
        if cp.returncode != 0:
            lower = (cp.stdout or "").lower()
            if "insufficient balance" in lower or "http 402" in lower:
                raise worker.ProviderUnavailable("deepseek", "billing-insufficient-balance", (cp.stdout or "")[-2000:], 21600)
            raise worker.WorkerError(f"review invocation failed ({cp.returncode}): {(cp.stdout or '')[-4000:]}")

        review = validate_review(extract_json(cp.stdout or ""))
        persisted = db.rpc("kueper_record_pr_review", {
            "p_task_id": task_id,
            "p_pr_url": pr_url,
            "p_head_sha": head_sha,
            "p_verdict": review["verdict"],
            "p_provider": "deepseek",
            "p_model": review_model,
            "p_summary": review["summary"],
            "p_findings": review["findings"],
        })

        if review["verdict"] == "PASS":
            db.rpc("kueper_complete_reviewed_task", {"p_task_id": task_id, "p_head_sha": head_sha})
            body = f"KUEPER automated review: **PASS** for `{head_sha[:12]}`.\n\n{review['summary']}\n\nNo auto-merge performed."
            worker.run(["gh", "pr", "comment", pr_url, "--body", body], cwd=root, env=gh_env)
            return {"task": task_id, "result": "PASS", "head_sha": head_sha, "review_id": persisted.get("id") if isinstance(persisted, dict) else None}

        blocking_findings = [f for f in review["findings"] if f["blocking"]]
        fix_payload = {
            "pr_url": pr_url,
            "review_head_sha": head_sha,
            "originating_task_id": task_id,
            "originating_task_payload": task_payload,
            "findings": blocking_findings,
        }
        fix = db.rpc("kueper_create_task", {
            "p_type": "REVIEW_FIX",
            "p_source_project": "ECO",
            "p_target_project": str(task.get("target_project") or "ECO"),
            "p_payload": fix_payload,
            "p_priority": "high" if str(task.get("priority")) != "critical" else "critical",
            "p_parent_task_id": task_id,
            "p_dependencies": [],
            "p_idempotency_key": f"review-fix:{task_id}:{head_sha}",
            "p_external_id": None,
            "p_available_at": None,
            "p_max_attempts": 3,
            "p_preferred_provider": None,
            "p_preferred_model": None,
            "p_repository": repo,
            "p_base_sha": None,
            "p_relevance_score": None,
            "p_evidence_score": None,
            "p_metadata": {"actor": "automated-pr-review-agent", "review_head_sha": head_sha},
        })
        lines = [f"KUEPER automated review: **CHANGES_REQUIRED** for `{head_sha[:12]}`.", "", review["summary"], "", "Blocking findings:"]
        for finding in blocking_findings:
            location = finding.get("path") or "(cross-cutting)"
            if finding.get("line"):
                location += f":{finding['line']}"
            lines.append(f"- **{finding['severity'].upper()} {finding['category']}** `{finding['finding_id']}` — {location}: {finding['issue']}")
        lines.extend(["", "One idempotent REVIEW_FIX task has been queued. No auto-merge performed."])
        worker.run(["gh", "pr", "comment", pr_url, "--body", "\n".join(lines)], cwd=root, env=gh_env)
        return {"task": task_id, "result": "CHANGES_REQUIRED", "head_sha": head_sha, "fix_task": fix.get("id") if isinstance(fix, dict) else None, "blocking": len(blocking_findings)}


def review_pending_batch(
    db: v71.PatchedSupabaseRPC,
    max_reviews: int,
) -> tuple[list[dict[str, Any]], int]:
    """Process a bounded number of live PRs without charging terminal cleanup.

    GitHub state is authoritative for whether a PR can still be reviewed. A
    CLOSED/MERGED task is terminalized by ``review_task`` and does not consume
    one of the bounded live-review slots. The queue is then fetched again so a
    stale prefix cannot starve eligible work behind it.
    """
    limit = max(1, max_reviews)
    results: list[dict[str, Any]] = []
    failures = 0
    charged = 0
    seen: set[str] = set()

    while charged < limit:
        pending = db.rpc("kueper_list_review_pending", {"p_limit": limit - charged}) or []
        if isinstance(pending, dict):
            pending = [pending]
        candidates = [task for task in pending if str(task.get("id") or "") not in seen]
        if not candidates:
            break

        for task in candidates:
            task_id = str(task.get("id") or "")
            if task_id:
                seen.add(task_id)
            try:
                result = review_task(task, db)
            except Exception as exc:
                failures += 1
                charged += 1
                print(f"::error title=Automated PR review failed::{task.get('id')}: {str(exc)[:500]}", flush=True)
                result = {"task": task.get("id"), "result": "REVIEW_ERROR", "error": str(exc)}
            else:
                if result.get("result") != "terminal":
                    charged += 1
            results.append(result)
            if charged >= limit:
                break

    return results, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-reviews", type=int, default=int(os.environ.get("KUEPER_MAX_REVIEWS", "3")))
    args = parser.parse_args()
    required = ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "DEEPSEEK_API_KEY", "KUEPER_BOT_TOKEN"]
    missing = [x for x in required if not os.environ.get(x)]
    if missing:
        raise SystemExit(f"missing required secrets: {', '.join(missing)}")

    db = v71.PatchedSupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    results, failures = review_pending_batch(db, args.max_reviews)
    print(json.dumps({"reviewer": "KUEPER_PR_REVIEW_V0_1", "results": results}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
