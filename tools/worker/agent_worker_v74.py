#!/usr/bin/env python3
"""KUEPER V7.4 worker: V7.3 lifecycle plus privileged workflow pushes.

Normal repository mutations continue to use KUEPER_BOT_TOKEN. A commit that
changes `.github/workflows/*` is a privileged mutation class and is pushed only
with the dedicated KUEPER_WORKFLOW_TOKEN. If that credential is unavailable,
the task is parked rather than retried as a generic failure.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_worker as worker  # noqa: E402
import agent_worker_v73 as v73  # noqa: E402
from git_credentials import PrivilegedCredentialMissing, select_push_token  # noqa: E402

_BASE_REPO_TASK = v73.repo_task


def repo_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    repo = str(task.get("repository") or "").strip()
    original_run = worker.run

    def credential_aware_run(cmd, *args, **kwargs):
        if (
            isinstance(cmd, list)
            and len(cmd) >= 2
            and cmd[0] == "git"
            and cmd[1] == "push"
            and kwargs.get("cwd") is not None
        ):
            cwd = kwargs["cwd"]
            changed = original_run(
                ["git", "show", "--name-only", "--format=", "HEAD"], cwd=cwd
            ).stdout.splitlines()
            push_token, privileged = select_push_token(
                changed,
                bot_token=os.environ["KUEPER_BOT_TOKEN"],
                workflow_token=os.environ.get("KUEPER_WORKFLOW_TOKEN"),
            )
            if privileged:
                original_run(
                    ["git", "remote", "set-url", "origin", worker.clone_url(repo, push_token)],
                    cwd=cwd,
                )
        return original_run(cmd, *args, **kwargs)

    worker.run = credential_aware_run
    try:
        return _BASE_REPO_TASK(task, model)
    except PrivilegedCredentialMissing as exc:
        return {
            "kind": "park",
            "reason": str(exc),
            "requires_owner_decision": False,
            "privileged_mutation": "github-workflow",
        }
    finally:
        worker.run = original_run


def main() -> int:
    v73.repo_task = repo_task
    return v73.main()


if __name__ == "__main__":
    raise SystemExit(main())
