#!/usr/bin/env python3
"""KUEPER Ecosystem Loop v0.1.

Read-only orchestration foundation:
- scan registered repositories for open external tasks
- normalize/sort a queue
- record observed target HEAD SHA
- preflight one queue item immediately before execution

Requires GH_TOKEN. Does not mutate target repositories.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "projects.json"
POLICY = ROOT / "registry" / "loop-policy.json"
API = "https://api.github.com"

FIELD_PATTERNS = {
    "status": re.compile(r"^Status:\s*(.+?)\s*$", re.I | re.M),
    "source_repository": re.compile(r"^Source Repository:\s*`?([^`\n]+)`?\s*$", re.I | re.M),
    "target_repository": re.compile(r"^Target Repository:\s*`?([^`\n]+)`?\s*$", re.I | re.M),
    "created": re.compile(r"^Created:\s*(\d{4}-\d{2}-\d{2})\s*$", re.I | re.M),
    "requested_by": re.compile(r"^Requested by:\s*(.+?)\s*$", re.I | re.M),
    "execution_class": re.compile(r"^Execution Class:\s*([ABC])\s*$", re.I | re.M),
}

CLASS_ORDER = {"A": 0, "B": 1, "C": 2}


def token() -> str:
    value = os.environ.get("GH_TOKEN")
    if not value:
        raise SystemExit("GH_TOKEN nicht gesetzt.")
    return value


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def gh(path: str, gh_token: str) -> tuple[int, Any]:
    req = urllib.request.Request(API + path)
    req.add_header("Authorization", f"Bearer {gh_token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except urllib.error.URLError:
        return 0, None


def repo_state(repository: str, gh_token: str) -> dict[str, Any]:
    status, data = gh(f"/repos/{repository}", gh_token)
    if status != 200 or not isinstance(data, dict):
        return {"state": "unreachable", "http_status": status}

    branch = data.get("default_branch")
    encoded_branch = urllib.parse.quote(str(branch), safe="")
    ref_status, ref = gh(f"/repos/{repository}/git/ref/heads/{encoded_branch}", gh_token)
    sha = None
    if ref_status == 200 and isinstance(ref, dict):
        sha = (ref.get("object") or {}).get("sha")

    return {
        "state": "ok" if sha else "unknown_head",
        "default_branch": branch,
        "head_sha": sha,
        "pushed_at": data.get("pushed_at"),
    }


def fetch_text(download_url: str, gh_token: str) -> str | None:
    req = urllib.request.Request(download_url)
    req.add_header("Authorization", f"Bearer {gh_token}")
    req.add_header("Accept", "application/vnd.github.raw+json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except (urllib.error.HTTPError, urllib.error.URLError, UnicodeDecodeError):
        return None


def parse_task(text: str, filename: str, default_class: str) -> dict[str, Any]:
    result: dict[str, Any] = {"filename": filename}
    for key, pattern in FIELD_PATTERNS.items():
        match = pattern.search(text)
        result[key] = match.group(1).strip() if match else None
    result["execution_class"] = (result.get("execution_class") or default_class).upper()
    result["title"] = next(
        (line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")),
        filename,
    )
    return result


def scan() -> dict[str, Any]:
    gh_token = token()
    registry = load_json(REGISTRY)
    policy = load_json(POLICY)
    default_class = policy.get("scan", {}).get("default_execution_class", "C")
    include_disabled = policy.get("scan", {}).get("include_disabled_projects", False)
    pilot_projects = set(policy.get("pilot_projects", []))

    items: list[dict[str, Any]] = []
    project_states: dict[str, Any] = {}

    for project in registry.get("projects", []):
        if not include_disabled and not project.get("enabled", True):
            continue

        project_id = project["id"]
        repository = project["repository"]
        state = repo_state(repository, gh_token)
        project_states[project_id] = {"repository": repository, **state}
        branch = state.get("default_branch")
        if not branch:
            continue

        encoded_branch = urllib.parse.quote(str(branch), safe="")
        status, listing = gh(
            f"/repos/{repository}/contents/external-tasks/open?ref={encoded_branch}", gh_token
        )
        if status != 200 or not isinstance(listing, list):
            continue

        for entry in listing:
            if not isinstance(entry, dict) or not str(entry.get("name", "")).endswith(".md"):
                continue
            download_url = entry.get("download_url")
            if not download_url:
                continue
            text = fetch_text(download_url, gh_token)
            if text is None:
                continue
            item = parse_task(text, entry["name"], default_class)
            item.update(
                {
                    "project_id": project_id,
                    "repository": repository,
                    "path": entry.get("path"),
                    "pilot": project_id in pilot_projects,
                    "observed_default_branch": branch,
                    "observed_head_sha": state.get("head_sha"),
                    "observed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                }
            )
            items.append(item)

    items.sort(key=lambda item: (
        0 if item.get("pilot") else 1,
        CLASS_ORDER.get(item.get("execution_class", "C"), 9),
        item.get("created") or "9999-12-31",
        item.get("filename") or "",
    ))

    return {
        "schema_version": "1.0.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "mode": policy.get("mode", "pilot"),
        "execution_enabled": bool(policy.get("execution", {}).get("enabled", False)),
        "summary": {
            "projects_checked": len(project_states),
            "open_tasks": len(items),
            "pilot_tasks": sum(1 for item in items if item.get("pilot")),
            "by_execution_class": {
                cls: sum(1 for item in items if item.get("execution_class") == cls)
                for cls in ("A", "B", "C")
            },
        },
        "projects": project_states,
        "queue": items,
    }


def preflight(queue_path: Path, index: int) -> dict[str, Any]:
    gh_token = token()
    payload = load_json(queue_path)
    queue = payload.get("queue", [])
    if index < 0 or index >= len(queue):
        raise SystemExit(f"Queue-Index {index} existiert nicht.")

    item = queue[index]
    current = repo_state(item["repository"], gh_token)
    observed = item.get("observed_head_sha")
    current_sha = current.get("head_sha")
    fresh = bool(observed and current_sha and observed == current_sha)

    return {
        "task": item.get("filename"),
        "repository": item.get("repository"),
        "observed_head_sha": observed,
        "current_head_sha": current_sha,
        "fresh": fresh,
        "action": "eligible_for_dispatch" if fresh else "rescan_and_replan",
        "checked_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="KUEPER Ecosystem Loop")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_parser = sub.add_parser("scan", help="Scan open External Tasks and emit queue JSON")
    scan_parser.add_argument("--output", type=Path)

    preflight_parser = sub.add_parser("preflight", help="Re-check target HEAD before dispatch")
    preflight_parser.add_argument("--queue", type=Path, required=True)
    preflight_parser.add_argument("--index", type=int, default=0)

    args = parser.parse_args()
    if args.command == "scan":
        result = scan()
        rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    else:
        result = preflight(args.queue, args.index)
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        if not result["fresh"]:
            raise SystemExit(3)


if __name__ == "__main__":
    main()
