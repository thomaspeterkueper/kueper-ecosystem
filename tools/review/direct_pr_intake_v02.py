#!/usr/bin/env python3
"""Direct PR intake v0.2: exact-head observation for bounded review queues.

The v0.1 intake is preserved for task creation/routing. This wrapper additionally
records the currently observed open-PR head for every review_pending task, including
agent-originating tasks. That lets the queue suppress an already-reviewed exact
head after CHANGES_REQUIRED and automatically make the task eligible again when
GitHub discovery sees a new head.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import direct_pr_intake as v01  # noqa: E402

parse_pr_url = v01.parse_pr_url
load_repository_projects = v01.load_repository_projects
github_open_prs = v01.github_open_prs
SHA_RE = v01.SHA_RE


def note_head(db: Any, task: dict[str, Any], pr_url: str, repo: str, head_sha: str | None) -> dict[str, Any]:
    normalized_head = (head_sha or "").strip().lower()
    if not normalized_head:
        return task
    if not SHA_RE.match(normalized_head):
        raise ValueError("head_sha must be a full 40-character GitHub SHA")
    if str(task.get("status") or "") not in {"review_pending", "completed"}:
        return task
    observed = db.rpc("kueper_note_open_pr_head", {
        "p_task_id": task["id"],
        "p_pr_url": pr_url,
        "p_repository": repo,
        "p_head_sha": normalized_head,
    })
    if not isinstance(observed, dict):
        raise RuntimeError("kueper_note_open_pr_head returned no task")
    return observed


def intake(
    db: Any,
    pr_url: str,
    *,
    priority: str = "medium",
    repository_projects: dict[str, str] | None = None,
    head_sha: str | None = None,
) -> dict[str, Any]:
    repo, _ = parse_pr_url(pr_url)
    projects = repository_projects if repository_projects is not None else load_repository_projects()
    if repo not in projects:
        raise ValueError(f"repository is not enabled in registry: {repo}")

    normalized_head = (head_sha or "").strip().lower()
    if normalized_head and not SHA_RE.match(normalized_head):
        raise ValueError("head_sha must be a full 40-character GitHub SHA")

    existing = db.rpc("kueper_get_task_for_pr", {"p_pr_url": pr_url})
    if isinstance(existing, dict) and existing.get("id") and existing.get("status") == "review_pending":
        return note_head(db, existing, pr_url, repo, normalized_head or None)

    task = v01.intake(
        db,
        pr_url,
        priority=priority,
        repository_projects=projects,
        head_sha=normalized_head or None,
    )
    return note_head(db, task, pr_url, repo, normalized_head or None)


def discover(
    db: Any,
    token: str,
    *,
    repository_projects: dict[str, str] | None = None,
    fetch_open_prs: Callable[[str, str], list[dict[str, Any]]] = github_open_prs,
    max_prs: int = 50,
) -> list[dict[str, Any]]:
    projects = repository_projects if repository_projects is not None else load_repository_projects()
    results: list[dict[str, Any]] = []
    for repository in sorted(projects):
        for pr in fetch_open_prs(repository, token):
            if len(results) >= max_prs:
                return results
            html_url = str(pr.get("html_url") or "").strip()
            head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
            head_sha = str(head.get("sha") or "").strip().lower()
            if not html_url:
                continue
            task = intake(db, html_url, repository_projects=projects, head_sha=head_sha or None)
            results.append({
                "repository": repository,
                "pr_url": html_url,
                "head_sha": head_sha or None,
                "task_id": task.get("id"),
                "status": task.get("status"),
                "task_type": task.get("type"),
            })
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_url", nargs="?")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--max-prs", type=int, default=50)
    parser.add_argument("--priority", default="medium", choices=("low", "medium", "high", "critical"))
    args = parser.parse_args()
    if bool(args.pr_url) == bool(args.discover):
        parser.error("provide exactly one PR URL or --discover")
    for name in ("SUPABASE_URL", "SUPABASE_SECRET_KEY"):
        if not os.environ.get(name):
            raise SystemExit(f"missing required secret: {name}")
    db = v01.v71.PatchedSupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    if args.discover:
        token = os.environ.get("KUEPER_BOT_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("missing required secret: KUEPER_BOT_TOKEN or GITHUB_TOKEN")
        result: Any = discover(db, token, max_prs=max(1, args.max_prs))
    else:
        result = intake(db, args.pr_url, priority=args.priority)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
