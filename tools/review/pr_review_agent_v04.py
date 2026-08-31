#!/usr/bin/env python3
"""KUEPER PR reviewer v0.4 — hold research candidates after technical PASS.

The normal reviewer may complete ordinary implementation PR tasks after a persisted
PASS on the exact current head. Research evidence candidates are different: a
technically clean Markdown candidate can still contain source overreach, stale market
values, or incorrect scientific generalization.

V0.4 adds one narrow lifecycle guard around v0.3:
- inspect the current PR file list before review;
- when every changed path is below ``research/candidates/``, persist the normal
  technical review but replace completion with the server-side research evidence gate;
- leave the task ``review_pending`` and mark it as requiring an explicit evidence
  approval for the exact technical-PASS head;
- rely on ``kueper_list_review_pending`` exact-head deduplication to avoid reviewing
  the same persisted head again;
- when the PR head changes, direct-PR intake records the new head and the existing
  queue logic makes it reviewable again.

The matching Supabase RPCs make this fail closed even if another service later calls
``kueper_complete_reviewed_task`` directly: gated research tasks can complete only
after ``kueper_approve_research_candidate`` has approved the same head SHA.

No merge is performed here. The research candidate still requires explicit critical
scientific/evidence review before a human or trusted orchestrator approves and merges it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import pr_review_agent_v03 as v03  # noqa: E402

base = v03.v02.base
_original_review_task = base.review_task

RESEARCH_CANDIDATE_PREFIX = "research/candidates/"


def research_candidate_only(paths: list[str]) -> bool:
    """Return True only when the PR changes one or more research candidate files."""
    normalized = [str(path or "").strip() for path in paths if str(path or "").strip()]
    return bool(normalized) and all(path.startswith(RESEARCH_CANDIDATE_PREFIX) for path in normalized)


def pr_changed_paths(pr_url: str) -> list[str]:
    """Resolve the authoritative changed-file list for the current PR."""
    env = os.environ.copy()
    token = env.get("KUEPER_BOT_TOKEN") or env.get("GITHUB_TOKEN")
    if token:
        env["GH_TOKEN"] = token
    cp = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "files"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=False,
    )
    if cp.returncode != 0:
        raise base.worker.WorkerError(
            f"could not resolve PR file list ({cp.returncode}): {(cp.stdout or '')[-2000:]}"
        )
    try:
        payload = json.loads(cp.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise base.worker.WorkerError("invalid JSON while resolving PR file list") from exc
    files = payload.get("files")
    if not isinstance(files, list):
        raise base.worker.WorkerError("PR file list response has no files array")
    paths: list[str] = []
    for entry in files:
        if isinstance(entry, dict):
            path = str(entry.get("path") or "").strip()
            if path:
                paths.append(path)
    if not paths:
        raise base.worker.WorkerError("PR has no resolvable changed paths")
    return paths


class CompletionGuardDB:
    """Proxy Supabase RPC calls while routing research completion into the evidence gate."""

    def __init__(self, db: Any, *, hold_completion: bool):
        self._db = db
        self.hold_completion = hold_completion
        self.completion_suppressed = False

    def rpc(self, name: str, payload: dict[str, Any]):
        if self.hold_completion and name == "kueper_complete_reviewed_task":
            self.completion_suppressed = True
            return self._db.rpc(
                "kueper_mark_research_evidence_gate",
                {
                    "p_task_id": payload.get("p_task_id"),
                    "p_head_sha": payload.get("p_head_sha"),
                },
            )
        return self._db.rpc(name, payload)

    def __getattr__(self, name: str):
        return getattr(self._db, name)


def _post_research_gate_comment(pr_url: str, head_sha: str) -> None:
    env = os.environ.copy()
    token = env.get("KUEPER_BOT_TOKEN") or env.get("GITHUB_TOKEN")
    if token:
        env["GH_TOKEN"] = token
    body = (
        f"KUEPER research evidence gate: technical **PASS** recorded for `{head_sha[:12]}`, "
        "but this PR changes only `research/candidates/`. The server-side evidence gate is now "
        "active: the review task remains `review_pending`, requires explicit critical evidence "
        "approval for this exact head, and `kueper_complete_reviewed_task` will fail closed until "
        "that approval is recorded. The persisted exact-head review suppresses duplicate review "
        "runs; a changed head becomes reviewable again. No merge is authorized by this technical PASS."
    )
    cp = subprocess.run(
        ["gh", "pr", "comment", pr_url, "--body", body],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=False,
    )
    if cp.returncode != 0:
        raise base.worker.WorkerError(
            f"could not post research-gate comment ({cp.returncode}): {(cp.stdout or '')[-2000:]}"
        )


def guarded_review_task(task: dict[str, Any], db: Any) -> dict[str, Any]:
    pr_url = str(task.get("pr_url") or "").strip()
    if not pr_url:
        return _original_review_task(task, db)

    paths = pr_changed_paths(pr_url)
    hold = research_candidate_only(paths)
    proxy = CompletionGuardDB(db, hold_completion=hold)
    result = _original_review_task(task, proxy)

    if hold and result.get("result") == "PASS" and proxy.completion_suppressed:
        head_sha = str(result.get("head_sha") or "")
        _post_research_gate_comment(pr_url, head_sha)
        result = dict(result)
        result["research_manual_gate"] = True
        result["changed_paths"] = paths

    return result


# Patch the base module that owns main() so v0.3 keeps its stdin transport while
# dispatching individual tasks through the research lifecycle guard above.
base.review_task = guarded_review_task


def main() -> int:
    return v03.main()


if __name__ == "__main__":
    raise SystemExit(main())
