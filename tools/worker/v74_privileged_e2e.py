#!/usr/bin/env python3
"""Deterministic end-to-end harness for the V7.4 privileged push wrapper.

This deliberately bypasses Supabase and the model provider. It exercises the
production V7.4 repo_task wrapper around one fixed, harmless mutation on the
existing `test/workflow-credential-smoke` branch. The actual `git push` is made
through `worker.run`, so agent_worker_v74.py must detect the workflow-file
change and replace the origin credential with KUEPER_WORKFLOW_TOKEN.

It never targets main and refuses any target branch other than the dedicated
smoke branch.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Any

from tools.worker import agent_worker as worker
from tools.worker import agent_worker_v74 as v74

TARGET_BRANCH = "test/workflow-credential-smoke"
TARGET_PATH = Path(".github/workflows/_v74-e2e-target.yml")
MARKER = """name: V7.4 Privileged Credential E2E Target
on:
  workflow_dispatch:
jobs:
  noop:
    runs-on: ubuntu-latest
    steps:
      - run: echo \"v74 privileged credential e2e\"
"""


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"missing required environment variable: {name}")
    return value


def _fake_repo_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    del model
    repo = str(task["repository"])
    mode = str((task.get("payload") or {}).get("mode") or "apply")
    if mode not in {"apply", "cleanup"}:
        raise RuntimeError(f"unsupported mode: {mode}")

    bot_token = _require_env("KUEPER_BOT_TOKEN")
    with tempfile.TemporaryDirectory(prefix="kueper-v74-e2e-") as temp:
        root = Path(temp) / "repo"
        worker.run(["git", "clone", "--quiet", worker.clone_url(repo, bot_token), str(root)])
        worker.run(["git", "checkout", TARGET_BRANCH], cwd=root)

        path = root / TARGET_PATH
        if mode == "apply":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(MARKER, encoding="utf-8")
        elif path.exists():
            path.unlink()
        else:
            return {"kind": "completed", "summary": "cleanup already complete"}

        worker.run(["git", "config", "user.name", "KUEPER V7.4 E2E"], cwd=root)
        worker.run(["git", "config", "user.email", "v74-e2e@users.noreply.github.com"], cwd=root)
        worker.run(["git", "add", "-A"], cwd=root)
        status = worker.run(["git", "status", "--porcelain"], cwd=root).stdout.strip()
        if not status:
            return {"kind": "completed", "summary": "target already in requested state"}

        worker.run(["git", "commit", "-m", f"test: v74 privileged e2e {mode}"], cwd=root)
        changed = [
            p for p in worker.run(
                ["git", "show", "--name-only", "--format=", "HEAD"], cwd=root
            ).stdout.splitlines() if p.strip()
        ]
        if changed != [TARGET_PATH.as_posix()]:
            raise RuntimeError(f"safety guard: unexpected changed paths: {changed}")

        # This is the line under test. agent_worker_v74.repo_task temporarily
        # wraps worker.run and must switch origin to KUEPER_WORKFLOW_TOKEN before
        # this privileged workflow-file push is executed.
        worker.run(["git", "push", "--quiet", "origin", TARGET_BRANCH], cwd=root)
        sha = worker.run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
        return {
            "kind": "completed",
            "summary": f"V7.4 privileged {mode} push completed",
            "commit_sha": sha,
            "changed_paths": changed,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("apply", "cleanup"), default="apply")
    args = parser.parse_args()

    repo = _require_env("GITHUB_REPOSITORY")
    _require_env("KUEPER_BOT_TOKEN")
    _require_env("KUEPER_WORKFLOW_TOKEN")
    if repo != "thomaspeterkueper/kueper-ecosystem":
        raise SystemExit(f"safety guard: unexpected repository {repo}")

    original = v74._BASE_REPO_TASK
    v74._BASE_REPO_TASK = _fake_repo_task
    try:
        result = v74.repo_task(
            {
                "id": "00000000-v74-e2e-0000-000000000001",
                "repository": repo,
                "type": "V74_PRIVILEGED_CREDENTIAL_E2E",
                "payload": {"mode": args.mode},
            },
            "deterministic-no-provider",
        )
    finally:
        v74._BASE_REPO_TASK = original

    if result.get("kind") != "completed":
        raise SystemExit(f"unexpected V7.4 result: {result}")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
