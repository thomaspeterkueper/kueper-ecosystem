#!/usr/bin/env python3
"""KUEPER V7 execution worker.

Claims a bounded number of tasks from Supabase, applies provider/cost routing,
executes repository work through Claude Code backed by DeepSeek, and reports the
lifecycle through the V6 RPC state machine.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from provider_router import route


class WorkerError(RuntimeError):
    pass


class SupabaseRPC:
    def __init__(self, url: str, secret: str):
        self.base = url.rstrip("/")
        self.secret = secret

    def rpc(self, name: str, payload: dict[str, Any]) -> Any:
        req = urllib.request.Request(
            f"{self.base}/rest/v1/rpc/{name}",
            data=json.dumps(payload).encode(),
            method="POST",
        )
        req.add_header("apikey", self.secret)
        req.add_header("Authorization", f"Bearer {self.secret}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise WorkerError(f"Supabase RPC {name} failed: HTTP {exc.code}: {body}") from exc


class Heartbeat:
    def __init__(self, db: SupabaseRPC, task_id: str, lease_token: str, interval: int = 240):
        self.db, self.task_id, self.lease_token = db, task_id, lease_token
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def __enter__(self):
        def loop() -> None:
            while not self.stop_event.wait(self.interval):
                try:
                    self.db.rpc("kueper_heartbeat_task", {
                        "p_task_id": self.task_id,
                        "p_lease_token": self.lease_token,
                        "p_extend_seconds": 600,
                    })
                except Exception as exc:
                    print(f"WARN heartbeat failed for {self.task_id}: {exc}", flush=True)
        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if check and cp.returncode != 0:
        raise WorkerError(f"command failed ({cp.returncode}): {' '.join(cmd)}\n{(cp.stdout or '')[-5000:]}")
    return cp


def deepseek_chat(task: dict[str, Any], model: str) -> dict[str, Any]:
    key = os.environ["DEEPSEEK_API_KEY"]
    prompt = (
        "You are a KUEPER Ecosystem project agent. Complete the task precisely. "
        "Do not invent facts. Return a concise structured result that states what was done, "
        "remaining uncertainty, and any concrete cross-project follow-up need.\n\n"
        f"TASK TYPE: {task.get('type')}\nTARGET: {task.get('target_project')}\n"
        f"PAYLOAD:\n{json.dumps(task.get('payload') or {}, ensure_ascii=False, indent=2)}"
    )
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    if model == "deepseek-v4-pro":
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "high"
    req = urllib.request.Request("https://api.deepseek.com/chat/completions",
                                 data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise WorkerError(f"DeepSeek HTTP {exc.code}: {exc.read().decode(errors='replace')}") from exc
    message = data["choices"][0]["message"].get("content", "")
    usage = data.get("usage") or {}
    return {
        "kind": "analysis",
        "content": message,
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
    }


def clone_url(repo: str, token: str) -> str:
    return f"https://x-access-token:{urllib.parse.quote(token, safe='')}@github.com/{repo}.git"


def repo_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    repo = str(task.get("repository") or "").strip()
    if not repo:
        raise WorkerError("repository task has no repository")
    token = os.environ["KUEPER_BOT_TOKEN"]
    with tempfile.TemporaryDirectory(prefix="kueper-v7-") as temp:
        root = Path(temp) / "repo"
        run(["git", "clone", "--quiet", clone_url(repo, token), str(root)])
        default_branch = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=root).stdout.strip().split("/", 1)[-1]
        current_sha = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
        expected_sha = task.get("base_sha")
        if expected_sha and current_sha != expected_sha:
            raise WorkerError(f"base SHA moved: expected {expected_sha}, current {current_sha}")

        branch = f"ecosystem/task-{task['id'][:8]}"
        run(["git", "checkout", "-b", branch], cwd=root)

        payload = json.dumps(task.get("payload") or {}, ensure_ascii=False, indent=2)
        prompt = f"""You are the autonomous project owner for {repo}.
Read the repository and AGENTS.md if present before editing.
Task type: {task.get('type')}
Task id: {task.get('id')}
Priority: {task.get('priority')}

Payload:
{payload}

Rules:
- Re-evaluate the task against the current repository before changing anything.
- Implement the smallest complete solution owned by this repository.
- Run relevant tests/build/lint and repair failures caused by your changes.
- Never expose secrets or weaken tests.
- Do not edit other repositories.
- If blocked by a genuine owner/creative decision, leave the repo unchanged and print `KUEPER_PARK_OWNER: <reason>`.
- If blocked by a temporary internal dependency, leave the repo unchanged and print `KUEPER_PARK: <reason>`.
- Finish with only intentional working-tree changes.
"""
        env = os.environ.copy()
        env.update({
            "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
            "ANTHROPIC_AUTH_TOKEN": os.environ["DEEPSEEK_API_KEY"],
            "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]" if model == "deepseek-v4-pro" else "deepseek-v4-flash",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1m]",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
            "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
            "CLAUDE_CODE_EFFORT_LEVEL": "max",
        })
        agent = run(["claude", "-p", "--dangerously-skip-permissions", prompt], cwd=root, env=env, check=False)
        output = agent.stdout or ""
        if agent.returncode != 0:
            raise WorkerError(f"agent failed ({agent.returncode}): {output[-5000:]}")
        for marker, owner in (("KUEPER_PARK_OWNER:", True), ("KUEPER_PARK:", False)):
            if marker in output:
                reason = output.split(marker, 1)[1].splitlines()[0].strip()
                return {"kind": "park", "reason": reason, "requires_owner_decision": owner}

        status = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root).stdout.strip()
        if not status:
            return {"kind": "completed", "summary": "Agent found no repository change necessary", "agent_output": output[-4000:]}

        run(["git", "config", "user.name", "KUEPER Ecosystem Bot"], cwd=root)
        run(["git", "config", "user.email", "ecosystem-bot@users.noreply.github.com"], cwd=root)
        run(["git", "add", "-A"], cwd=root)
        run(["git", "commit", "-m", f"chore(agent): execute task {task['id'][:8]}"], cwd=root)
        run(["git", "push", "--quiet", "origin", branch], cwd=root)
        gh_env = env.copy(); gh_env["GH_TOKEN"] = token
        pr = run(["gh", "pr", "create", "--repo", repo, "--base", default_branch, "--head", branch,
                  "--title", f"[Agent] {task.get('type')}: {task['id'][:8]}",
                  "--body", f"Autonomous KUEPER V7 task `{task['id']}`. Provider: DeepSeek / {model}."],
                 cwd=root, env=gh_env).stdout.strip()
        return {"kind": "completed", "summary": "Repository changes published as PR", "pr_url": pr, "agent_output": output[-4000:]}


def execute_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    if task.get("repository"):
        return repo_task(task, model)
    return deepseek_chat(task, model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tasks", type=int, default=int(os.environ.get("KUEPER_MAX_TASKS", "3")))
    args = parser.parse_args()
    required = ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "DEEPSEEK_API_KEY", "KUEPER_BOT_TOKEN"]
    missing = [x for x in required if not os.environ.get(x)]
    if missing:
        raise SystemExit(f"missing required secrets: {', '.join(missing)}")

    db = SupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    worker_id = f"github:{os.environ.get('GITHUB_RUN_ID', 'local')}:{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
    results: list[dict[str, Any]] = []

    db.rpc("kueper_recover_expired_leases", {})
    for _ in range(max(1, args.max_tasks)):
        task = db.rpc("kueper_claim_task", {
            "p_worker_id": worker_id,
            "p_lease_seconds": 600,
            "p_target_project": None,
            "p_types": None,
        })
        if not task:
            break
        decision = route(task)
        task_id, lease = str(task["id"]), str(task["lease_token"])
        if not decision.execute_now:
            db.rpc("kueper_reschedule_task", {
                "p_task_id": task_id,
                "p_lease_token": lease,
                "p_available_at": decision.available_at,
                "p_reason": decision.reason,
            })
            results.append({"task": task_id, "result": "rescheduled", "available_at": decision.available_at})
            continue

        db.rpc("kueper_start_task", {"p_task_id": task_id, "p_lease_token": lease})
        try:
            with Heartbeat(db, task_id, lease):
                outcome = execute_task(task, decision.model)
            if outcome.get("kind") == "park":
                db.rpc("kueper_park_task", {
                    "p_task_id": task_id,
                    "p_lease_token": lease,
                    "p_reason": outcome["reason"],
                    "p_requires_owner_decision": bool(outcome.get("requires_owner_decision")),
                })
                results.append({"task": task_id, "result": "parked", "reason": outcome["reason"]})
            else:
                db.rpc("kueper_complete_task", {
                    "p_task_id": task_id,
                    "p_lease_token": lease,
                    "p_result": outcome,
                    "p_provider": decision.provider,
                    "p_model": decision.model,
                    "p_input_tokens": outcome.get("input_tokens"),
                    "p_output_tokens": outcome.get("output_tokens"),
                    "p_cost_estimate_eur": None,
                })
                results.append({"task": task_id, "result": "completed", "provider": decision.provider, "model": decision.model})
        except Exception as exc:
            try:
                db.rpc("kueper_fail_task", {
                    "p_task_id": task_id,
                    "p_lease_token": lease,
                    "p_error": str(exc)[:4000],
                    "p_retry_delay_seconds": 300,
                })
            except Exception as fail_exc:
                print(f"ERROR could not record task failure: {fail_exc}", flush=True)
            results.append({"task": task_id, "result": "failed", "error": str(exc)})

    print(json.dumps({"worker": worker_id, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
