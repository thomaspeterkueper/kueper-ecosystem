#!/usr/bin/env python3
"""KUEPER Ecosystem autonomous task loop v1.

Scans all enabled repositories in registry/projects.json for canonical open external
Tasks, executes at most N tasks per run in a fresh checkout of the target repo,
and publishes the result as a PR. Low-risk PRs can be queued for auto-merge.

Required environment:
  KUEPER_BOT_TOKEN      GitHub token with read/write access to registered repos
  OPENAI_API_KEY        API key used by Codex CLI

Optional:
  KUEPER_MAX_TASKS      default 3
  KUEPER_AUTO_MERGE     default true
  KUEPER_AGENT_CMD      default: codex exec --full-auto
  KUEPER_WORKDIR        default: /tmp/kueper-loop
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "projects.json"
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

REVIEW_ONLY_PREFIXES = (
    ".github/",
    "migrations/",
    "supabase/migrations/",
    "infra/",
    "terraform/",
    "auth/",
    "security/",
)
REVIEW_ONLY_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "vercel.json",
}


class LoopError(RuntimeError):
    pass


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    repository: str
    code: str
    enabled: bool


@dataclass(frozen=True)
class Task:
    project: Project
    path: str
    filename: str
    content: str
    id: str
    title: str
    status: str
    source: str
    target: str
    priority: str
    created: str


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None,
        check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    if check and cp.returncode != 0:
        raise LoopError(f"command failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stdout or ''}")
    return cp


def gh_request(token: str, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise LoopError(f"GitHub {method} {path}: HTTP {exc.code}: {payload}") from exc


def repo_info(token: str, repo: str) -> dict[str, Any]:
    return gh_request(token, "GET", f"/repos/{repo}")


def branch_head(token: str, repo: str, branch: str) -> str:
    ref = gh_request(token, "GET", f"/repos/{repo}/git/ref/heads/{urllib.parse.quote(branch, safe='')}")
    return ref["object"]["sha"]


def contents(token: str, repo: str, path: str, ref: str) -> Any:
    enc_path = "/".join(urllib.parse.quote(p, safe="") for p in path.split("/"))
    try:
        return gh_request(token, "GET", f"/repos/{repo}/contents/{enc_path}?ref={urllib.parse.quote(ref, safe='')}")
    except LoopError as exc:
        if "HTTP 404" in str(exc):
            return None
        raise


def decode_content(payload: dict[str, Any]) -> str:
    import base64
    return base64.b64decode(payload.get("content", "")).decode("utf-8")


def parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    return raw.strip("'\"")


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    out: dict[str, Any] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = parse_scalar(value)
    return out


def system_code_map() -> dict[str, str]:
    return {
        "ecosystem": "ECO", "knowledge-graph": "KG", "ssf": "SSF", "noxia": "NOXIA",
        "noxia-universe": "NXU", "mishkenaz": "MISH", "omnizedenz": "OMNI",
        "avi-modell": "AVI", "contracomology": "CONTRA", "kueper-archive-schema": "ARCH",
        "endia": "ENDIA", "zereya": "ZEREYA", "davaru": "DAVARU",
        "fluide-hermeneutik": "FLHERM", "resonanz-ethik": "RESETH",
        "kueper-com": "KUE", "ota": "OTA", "thomas-kueper-de": "TKD",
    }


def load_projects() -> list[Project]:
    with REGISTRY.open(encoding="utf-8") as f:
        reg = json.load(f)
    codes = system_code_map()
    projects: list[Project] = []
    for p in reg["projects"]:
        pid = p["id"]
        if pid not in codes:
            continue
        projects.append(Project(pid, p["name"], p["repository"], codes[pid], p.get("enabled", True)))
    return projects


def list_open_tasks(token: str, project: Project) -> list[Task]:
    if not project.enabled:
        return []
    info = repo_info(token, project.repository)
    branch = info["default_branch"]
    listing = contents(token, project.repository, "external-tasks/open", branch)
    if not isinstance(listing, list):
        return []
    tasks: list[Task] = []
    for item in listing:
        if item.get("type") != "file" or not item.get("name", "").endswith(".md"):
            continue
        payload = contents(token, project.repository, item["path"], branch)
        if not isinstance(payload, dict):
            continue
        text = decode_content(payload)
        fm = parse_frontmatter(text)
        if fm.get("status") != "open":
            continue
        if fm.get("target") != project.code:
            print(f"WARN {project.repository}:{item['path']} target={fm.get('target')} expected={project.code}")
            continue
        task_id = str(fm.get("id") or Path(item["name"]).stem)
        tasks.append(Task(
            project=project,
            path=item["path"],
            filename=item["name"],
            content=text,
            id=task_id,
            title=str(fm.get("title") or task_id),
            status="open",
            source=str(fm.get("source") or "UNKNOWN"),
            target=str(fm.get("target") or project.code),
            priority=str(fm.get("priority") or "medium").lower(),
            created=str(fm.get("created") or "9999-12-31"),
        ))
    return tasks


def task_sort_key(task: Task) -> tuple[int, str, str]:
    return (PRIORITY_ORDER.get(task.priority, PRIORITY_ORDER["medium"]), task.created, task.id)


def branch_name(task: Task) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", task.id.lower()).strip("-")
    return f"ecosystem/{slug}"[:120]


def existing_open_pr(token: str, repo: str, branch: str) -> dict[str, Any] | None:
    owner = repo.split("/", 1)[0]
    q = urllib.parse.urlencode({"state": "open", "head": f"{owner}:{branch}", "per_page": 5})
    prs = gh_request(token, "GET", f"/repos/{repo}/pulls?{q}")
    return prs[0] if prs else None


def build_prompt(task: Task, base_sha: str) -> str:
    return f"""You are the autonomous project owner for repository {task.project.repository}.

External task: {task.id} — {task.title}
Base commit verified before execution: {base_sha}

MANDATORY LOOP
1. Read the repository before changing anything. Read AGENTS.md if present.
2. Re-evaluate whether the request is still sensible against the current repository state.
3. If it is clear, consistent, and locally owned by this repository, implement the smallest complete solution.
4. Run the repository's relevant tests/build/lint checks. Fix failures caused by your change.
5. Update the task file as part of the same change:
   - on successful completion: move it from external-tasks/open/ to external-tasks/done/ and set frontmatter status: done;
   - if a material question, contradiction, unsafe assumption, missing external decision, or unresolved dependency prevents correct implementation: move it to external-tasks/parked/, set status: parked, and add a section '## Rückfrage' stating exactly what must be decided. Do not guess.
6. If your work discovers a need owned by another KUEPER repository, document the required follow-up in the current task's Hinweise; the ecosystem control plane will route it in a later loop version.
7. Do not modify another repository from this checkout. Do not expose or invent secrets. Do not weaken tests merely to obtain green status.
8. Finish with a clean working tree except for intentional changes.

The task document follows below:

{task.content}
"""


def changed_files(repo_dir: Path) -> list[str]:
    out = run(["git", "status", "--porcelain"], cwd=repo_dir).stdout or ""
    files: list[str] = []
    for line in out.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            files.append(path)
    return files


def requires_review(paths: list[str], task: Task) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if task.priority == "critical":
        reasons.append("critical-priority")
    for p in paths:
        if p in REVIEW_ONLY_FILES or any(p.startswith(prefix) for prefix in REVIEW_ONLY_PREFIXES):
            reasons.append(p)
    return bool(reasons), sorted(set(reasons))


def authenticated_clone_url(repo: str, token: str) -> str:
    return f"https://x-access-token:{urllib.parse.quote(token, safe='')}@github.com/{repo}.git"


def process_task(token: str, task: Task, agent_cmd: str, work_root: Path, auto_merge: bool) -> dict[str, Any]:
    info = repo_info(token, task.project.repository)
    default_branch = info["default_branch"]
    observed_sha = branch_head(token, task.project.repository, default_branch)
    bname = branch_name(task)

    existing = existing_open_pr(token, task.project.repository, bname)
    if existing:
        return {"task": task.id, "result": "already-in-progress", "pr": existing.get("html_url")}

    run_dir = Path(tempfile.mkdtemp(prefix=f"{task.project.id}-", dir=str(work_root)))
    try:
        clone_url = authenticated_clone_url(task.project.repository, token)
        run(["git", "clone", "--quiet", "--branch", default_branch, "--single-branch", clone_url, str(run_dir)], capture=True)
        local_sha = run(["git", "rev-parse", "HEAD"], cwd=run_dir).stdout.strip()

        current_sha = branch_head(token, task.project.repository, default_branch)
        if local_sha != observed_sha or current_sha != observed_sha:
            return {"task": task.id, "result": "rescan-and-replan", "observed": observed_sha, "current": current_sha}

        run(["git", "checkout", "-b", bname], cwd=run_dir)
        env = os.environ.copy()
        prompt = build_prompt(task, observed_sha)
        cmd = shlex.split(agent_cmd) + [prompt]
        agent = run(cmd, cwd=run_dir, env=env, check=False)
        if agent.returncode != 0:
            return {"task": task.id, "result": "agent-failed", "exit": agent.returncode,
                    "output_tail": (agent.stdout or "")[-4000:]}

        paths = changed_files(run_dir)
        if not paths:
            return {"task": task.id, "result": "no-change"}

        forbidden = [p for p in paths if p == ".env" or p.startswith(".env.") or "credentials" in p.lower()]
        if forbidden:
            return {"task": task.id, "result": "blocked-sensitive-files", "files": forbidden}

        run(["git", "config", "user.name", "KUEPER Ecosystem Bot"], cwd=run_dir)
        run(["git", "config", "user.email", "ecosystem-bot@users.noreply.github.com"], cwd=run_dir)
        run(["git", "add", "-A"], cwd=run_dir)
        run(["git", "commit", "-m", f"chore(loop): execute {task.id}"], cwd=run_dir)
        run(["git", "push", "--quiet", "origin", bname], cwd=run_dir)

        pr_body = (
            f"Autonomously executed external task `{task.id}` from `{task.source}`.\n\n"
            f"Base HEAD verified immediately before execution: `{observed_sha}`.\n\n"
            "The task remains reviewable through this PR; its lifecycle file is moved to `done/` or `parked/` only in this branch."
        )
        pr = gh_request(token, "POST", f"/repos/{task.project.repository}/pulls", {
            "title": f"[Loop] {task.id}: {task.title}",
            "head": bname,
            "base": default_branch,
            "body": pr_body,
            "draft": False,
        })
        pr_url = pr["html_url"]
        review_only, reasons = requires_review(paths, task)

        merge_result = "review-required"
        if auto_merge and not review_only:
            gh_env = os.environ.copy()
            gh_env["GH_TOKEN"] = token
            cp = run(["gh", "pr", "merge", pr_url, "--auto", "--squash", "--delete-branch"],
                     cwd=run_dir, env=gh_env, check=False)
            merge_result = "auto-merge-queued" if cp.returncode == 0 else "auto-merge-unavailable"

        return {
            "task": task.id,
            "result": "pr-created",
            "pr": pr_url,
            "merge": merge_result,
            "review_reasons": reasons,
            "changed_files": paths,
        }
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def main() -> int:
    token = os.environ.get("KUEPER_BOT_TOKEN")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not token:
        print("KUEPER_BOT_TOKEN is required", file=sys.stderr)
        return 2
    if not api_key:
        print("OPENAI_API_KEY is required", file=sys.stderr)
        return 2

    max_tasks = max(1, int(os.environ.get("KUEPER_MAX_TASKS", "3")))
    auto_merge = os.environ.get("KUEPER_AUTO_MERGE", "true").lower() in {"1", "true", "yes", "on"}
    agent_cmd = os.environ.get("KUEPER_AGENT_CMD", "codex exec --full-auto")
    work_root = Path(os.environ.get("KUEPER_WORKDIR", "/tmp/kueper-ecosystem-loop"))
    work_root.mkdir(parents=True, exist_ok=True)

    all_tasks: list[Task] = []
    for project in load_projects():
        try:
            all_tasks.extend(list_open_tasks(token, project))
        except Exception as exc:
            print(f"ERROR scan {project.repository}: {exc}", file=sys.stderr)

    all_tasks.sort(key=task_sort_key)
    selected = all_tasks[:max_tasks]
    results = []
    for task in selected:
        try:
            results.append(process_task(token, task, agent_cmd, work_root, auto_merge))
        except Exception as exc:
            results.append({"task": task.id, "result": "error", "error": str(exc)})

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "open_tasks_seen": len(all_tasks),
        "tasks_selected": len(selected),
        "results": results,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not any(r.get("result") == "error" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
