#!/usr/bin/env python3
"""Create idempotent review_pending tasks for directly-created PRs.

Repository routing comes from the trusted control-plane registry. The module can
also discover open PRs through GitHub's API so the base-branch review workflow
can ingest them without executing code from those PRs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

WORKER_DIR = Path(__file__).resolve().parents[1] / "worker"
sys.path.insert(0, str(WORKER_DIR))
import agent_worker_v71 as v71  # noqa: E402

PR_RE = re.compile(r"^https://github\.com/([^/]+/[^/]+)/pull/(\d+)$")
REGISTRY_PATH = Path(__file__).resolve().parents[2] / "registry" / "projects.json"
PROJECT_CODES = {
    "ecosystem": "ECO",
    "noxia": "NOXIA",
    "ssf": "SSF",
    "knowledge-graph": "KG",
}


def parse_pr_url(url: str) -> tuple[str, int]:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("expected https://github.com/OWNER/REPO/pull/NUMBER")
    return match.group(1), int(match.group(2))


def project_code(project_id: str) -> str:
    normalized = project_id.strip().lower()
    return PROJECT_CODES.get(normalized, normalized.upper().replace("-", "_"))


def load_repository_projects(path: Path = REGISTRY_PATH) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    projects: dict[str, str] = {}
    for project in data.get("projects", []):
        if not project.get("enabled", True) or project.get("provider") != "github":
            continue
        repository = str(project.get("repository") or "").strip()
        project_id = str(project.get("id") or "").strip()
        if repository and project_id:
            projects[repository] = project_code(project_id)
    return projects


def intake(
    db: v71.PatchedSupabaseRPC,
    pr_url: str,
    *,
    priority: str = "medium",
    repository_projects: dict[str, str] | None = None,
) -> dict[str, Any]:
    repo, number = parse_pr_url(pr_url)
    projects = repository_projects if repository_projects is not None else load_repository_projects()
    target_project = projects.get(repo)
    if not target_project:
        raise ValueError(f"repository is not enabled in registry: {repo}")

    existing = db.rpc("kueper_get_task_for_pr", {"p_pr_url": pr_url})
    if isinstance(existing, dict) and existing.get("id"):
        # Agent-created PRs already carry their originating task. Returning it
        # here prevents a second PR_REVIEW task from being introduced by the
        # registry scanner. A pending direct-intake task is recoverable below.
        if existing.get("type") != "PR_REVIEW" or existing.get("status") != "pending":
            return existing
        promoted = db.rpc("kueper_enqueue_direct_pr_review", {
            "p_task_id": existing["id"],
            "p_pr_url": pr_url,
            "p_repository": repo,
        })
        if not isinstance(promoted, dict):
            raise RuntimeError("kueper_enqueue_direct_pr_review returned no task")
        return promoted

    payload = {
        "pr_url": pr_url,
        "origin": "direct-pr-intake",
        "review_scope": "Review the current PR against its stated intent, repository governance and diff.",
    }
    created = db.rpc("kueper_create_task", {
        "p_type": "PR_REVIEW",
        "p_source_project": "ECO",
        "p_target_project": target_project,
        "p_payload": payload,
        "p_priority": priority,
        "p_parent_task_id": None,
        "p_dependencies": [],
        "p_idempotency_key": f"direct-pr-review:{repo}:{number}",
        "p_external_id": f"DIRECT-PR-{repo.replace('/', '-').upper()}-{number}",
        "p_available_at": None,
        "p_max_attempts": 3,
        "p_preferred_provider": None,
        "p_preferred_model": None,
        "p_repository": repo,
        "p_base_sha": None,
        "p_relevance_score": None,
        "p_evidence_score": None,
        "p_metadata": {"actor": "direct-pr-intake", "pr_number": number, "registry_project": target_project},
    })
    task_id = created.get("id") if isinstance(created, dict) else None
    if not task_id:
        raise RuntimeError("kueper_create_task returned no task id")

    promoted = db.rpc("kueper_enqueue_direct_pr_review", {
        "p_task_id": task_id,
        "p_pr_url": pr_url,
        "p_repository": repo,
    })
    if not isinstance(promoted, dict):
        raise RuntimeError("kueper_enqueue_direct_pr_review returned no task")
    return promoted


def github_open_prs(repository: str, token: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/pulls?state=open&per_page=100",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "kueper-direct-pr-intake",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub PR discovery failed for {repository}: HTTP {exc.code}") from exc
    if not isinstance(data, list):
        raise RuntimeError(f"GitHub PR discovery returned invalid payload for {repository}")
    return data


def discover(
    db: v71.PatchedSupabaseRPC,
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
            if not html_url:
                continue
            task = intake(db, html_url, repository_projects=projects)
            results.append({
                "repository": repository,
                "pr_url": html_url,
                "task_id": task.get("id"),
                "status": task.get("status"),
                "task_type": task.get("type"),
            })
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_url", nargs="?")
    parser.add_argument("--discover", action="store_true", help="scan enabled registry repositories for open PRs")
    parser.add_argument("--max-prs", type=int, default=50)
    parser.add_argument("--priority", default="medium", choices=("low", "medium", "high", "critical"))
    args = parser.parse_args()
    if bool(args.pr_url) == bool(args.discover):
        parser.error("provide exactly one PR URL or --discover")
    for name in ("SUPABASE_URL", "SUPABASE_SECRET_KEY"):
        if not os.environ.get(name):
            raise SystemExit(f"missing required secret: {name}")
    db = v71.PatchedSupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
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
