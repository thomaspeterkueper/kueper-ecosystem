#!/usr/bin/env python3
"""Cross-repository branch hygiene classifier.

Dry-run only. This tool never deletes refs. It classifies branches across the
trusted project registry plus explicitly configured metadata-only extras.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "projects.json"
POLICY = ROOT / "config" / "branch-hygiene.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repositories(registry: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    repos = {
        p["repository"]
        for p in registry.get("projects", [])
        if p.get("enabled") and p.get("provider") == "github" and p.get("repository")
    }
    repos.update(policy.get("extra_repositories", []))
    repos.difference_update(policy.get("excluded_repositories", []))
    return sorted(repos)


class GitHub:
    def __init__(self, token: str, api: str = "https://api.github.com") -> None:
        self.token = token
        self.api = api.rstrip("/")

    def get(self, path: str) -> Any:
        req = urllib.request.Request(
            f"{self.api}{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "kueper-branch-hygiene",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def paged(self, path: str, per_page: int = 100) -> list[Any]:
        out: list[Any] = []
        page = 1
        sep = "&" if "?" in path else "?"
        while True:
            batch = self.get(f"{path}{sep}per_page={per_page}&page={page}")
            if not isinstance(batch, list):
                raise RuntimeError(f"Expected list from {path}")
            out.extend(batch)
            if len(batch) < per_page:
                return out
            page += 1


def classify_branch(
    branch: str,
    branch_sha: str | None,
    default_branch: str,
    prs: list[dict[str, Any]],
    protected: bool,
    policy: dict[str, Any],
    repo: str,
) -> tuple[str, str]:
    if branch == default_branch:
        return "KEEP", "default branch"
    if protected:
        return "KEEP", "protected branch"

    own_head = [p for p in prs if p.get("head", {}).get("repo", {}).get("full_name") == repo]

    open_head = [p for p in own_head if p.get("state") == "open" and p.get("head", {}).get("ref") == branch]
    if open_head:
        return "KEEP", f"head of open PR #{open_head[0].get('number')}"

    open_base = [
        p for p in prs
        if p.get("state") == "open"
        and p.get("base", {}).get("repo", {}).get("full_name") == repo
        and p.get("base", {}).get("ref") == branch
    ]
    if open_base:
        return "KEEP", f"base of open/stacked PR #{open_base[0].get('number')}"

    branch_prs = [p for p in own_head if p.get("head", {}).get("ref") == branch]
    merged = [p for p in branch_prs if p.get("merged_at")]
    closed_unmerged = [p for p in branch_prs if p.get("state") == "closed" and not p.get("merged_at")]

    review_prefixes = tuple(policy.get("always_review_prefixes", ["research/"]))
    if branch.startswith(review_prefixes):
        if merged:
            return "REVIEW", f"research/special branch; merged PR #{merged[-1].get('number')} but follow-up state is not inferable"
        return "REVIEW", "research/special branch requires explicit lifecycle check"

    if closed_unmerged:
        unmerged_numbers = ",".join(str(p.get("number")) for p in closed_unmerged)
        if merged:
            merged_numbers = ",".join(str(p.get("number")) for p in merged)
            return "REVIEW", f"merged PR(s) #{merged_numbers} but closed-unmerged PR(s) #{unmerged_numbers}; deletion cannot be proven safe"
        return "REVIEW", f"closed but unmerged PR(s) #{unmerged_numbers}"

    if merged:
        normalized_branch_sha = (branch_sha or "").lower()
        exact = [
            p for p in merged
            if str(p.get("head", {}).get("sha") or "").lower() == normalized_branch_sha
        ]
        if exact and normalized_branch_sha:
            numbers = ",".join(str(p.get("number")) for p in exact)
            return "DELETE_CANDIDATE", f"current branch SHA exactly matches merged PR head for PR(s) #{numbers}; no open PR uses branch as head/base"
        merged_numbers = ",".join(str(p.get("number")) for p in merged)
        return "REVIEW", f"merged PR(s) #{merged_numbers}, but current branch SHA does not match a merged PR head; branch may have moved after merge"

    if branch.startswith(tuple(policy.get("ephemeral_prefixes", ["tmp-", "test/", "agent/", "ecosystem/task-"]))):
        return "REVIEW", "ephemeral-looking branch without a merged PR association"

    return "REVIEW", "no safely provable deletion condition"


def scan_repo(gh: GitHub, repo: str, policy: dict[str, Any]) -> dict[str, Any]:
    meta = gh.get(f"/repos/{repo}")
    default_branch = meta["default_branch"]
    branches = gh.paged(f"/repos/{repo}/branches")
    prs = gh.paged(f"/repos/{repo}/pulls?state=all")

    rows = []
    for item in branches:
        name = item["name"]
        branch_sha = item.get("commit", {}).get("sha")
        action, reason = classify_branch(name, branch_sha, default_branch, prs, bool(item.get("protected")), policy, repo)
        rows.append({
            "branch": name,
            "sha": branch_sha,
            "protected": bool(item.get("protected")),
            "action": action,
            "reason": reason,
        })
    counts = Counter(r["action"] for r in rows)
    return {
        "repository": repo,
        "default_branch": default_branch,
        "visibility": meta.get("visibility"),
        "branches": rows,
        "counts": dict(counts),
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# KUEPER Branch Hygiene — Dry Run",
        "",
        "> This report is classification only. No branch refs were deleted.",
        "",
    ]
    totals = Counter()
    for repo in report["repositories"]:
        totals.update(repo.get("counts", {}))
    lines += [
        f"Repositories scanned: **{len(report['repositories'])}** · KEEP **{totals['KEEP']}** · DELETE candidates **{totals['DELETE_CANDIDATE']}** · REVIEW **{totals['REVIEW']}** · errors **{len(report['errors'])}**",
        "",
    ]
    for repo in report["repositories"]:
        c = repo["counts"]
        lines += [
            f"## {repo['repository']}",
            "",
            f"Default: `{repo['default_branch']}` · KEEP {c.get('KEEP',0)} · DELETE candidates {c.get('DELETE_CANDIDATE',0)} · REVIEW {c.get('REVIEW',0)}",
            "",
            "| Action | Branch | SHA | Reason |",
            "|---|---|---|---|",
        ]
        order = {"DELETE_CANDIDATE": 0, "REVIEW": 1, "KEEP": 2}
        for row in sorted(repo["branches"], key=lambda r: (order[r["action"]], r["branch"])):
            lines.append(f"| {row['action']} | `{row['branch']}` | `{row.get('sha') or ''}` | {row['reason']} |")
        lines.append("")
    if report["errors"]:
        lines += ["## Errors", ""]
        for err in report["errors"]:
            lines.append(f"- `{err['repository']}`: {err['error']}")
    return "\n".join(lines) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", default="branch-hygiene-report.json")
    parser.add_argument("--output-md", default="branch-hygiene-report.md")
    parser.add_argument("--repo", action="append", help="Limit scan to one or more owner/repo values")
    args = parser.parse_args(argv)

    token = os.getenv("GH_TOKEN") or os.getenv("KUEPER_BOT_TOKEN")
    if not token:
        print("GH_TOKEN or KUEPER_BOT_TOKEN is required", file=sys.stderr)
        return 2

    registry = load_json(REGISTRY)
    policy = load_json(POLICY)
    repos = repositories(registry, policy)
    if args.repo:
        requested = set(args.repo)
        repos = [r for r in repos if r in requested]

    gh = GitHub(token)
    report: dict[str, Any] = {"schema_version": "1.1", "mode": "dry-run", "repositories": [], "errors": []}
    for repo in repos:
        try:
            report["repositories"].append(scan_repo(gh, repo, policy))
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, KeyError) as exc:
            report["errors"].append({"repository": repo, "error": str(exc)})

    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(markdown(report), encoding="utf-8")
    print(markdown(report))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
