#!/usr/bin/env python3
"""KUEPER V7.4 worker: V7.3 lifecycle plus privileged workflow pushes.

Normal repository mutations continue to use KUEPER_BOT_TOKEN. A commit that
changes `.github/workflows/*` is a privileged mutation class and is pushed only
with the dedicated KUEPER_WORKFLOW_TOKEN. If that credential is unavailable,
the task is parked rather than retried as a generic failure.

Every temporary repository clone also gets a fail-closed pre-push guard for its
default branch. GitHub write credentials are withheld from the coding-agent
process and are restored only by the worker for an approved PR-branch push.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_worker as worker  # noqa: E402
import agent_worker_v73 as v73  # noqa: E402
from direct_main_guard import assert_push_target, install_pre_push_guard  # noqa: E402
from git_credentials import PrivilegedCredentialMissing, select_push_token  # noqa: E402

_BASE_REPO_TASK = v73.repo_task


def _resolve_and_install_guard(cwd: Path, original_run) -> str:
    default_branch = original_run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=cwd
    ).stdout.strip().split("/", 1)[-1]
    install_pre_push_guard(Path(cwd), default_branch)
    return default_branch


def repo_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    repo = str(task.get("repository") or "").strip()
    original_run = worker.run
    guarded_roots: dict[str, str] = {}

    def credential_aware_run(cmd, *args, **kwargs):
        cwd = kwargs.get("cwd")
        if cwd is not None and isinstance(cmd, list) and cmd:
            root_key = str(Path(cwd))

            # The coding agent may edit and test locally, but it does not receive
            # GitHub mutation credentials. Even `git push --no-verify` therefore
            # cannot turn a blocked Ready/Merge operation into a direct write.
            if cmd[0] == "claude":
                if root_key not in guarded_roots:
                    guarded_roots[root_key] = _resolve_and_install_guard(Path(cwd), original_run)
                original_run(
                    ["git", "remote", "set-url", "origin", f"https://github.com/{repo}.git"],
                    cwd=cwd,
                )
                agent_env = dict(kwargs.get("env") or os.environ.copy())
                for secret_name in ("KUEPER_BOT_TOKEN", "KUEPER_WORKFLOW_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
                    agent_env.pop(secret_name, None)
                kwargs["env"] = agent_env

            if cmd[0] == "git":
                # Install before checkout/agent execution in REVIEW_FIX. Normal
                # V7.2 tasks also install the same hook after origin/HEAD lookup.
                if len(cmd) >= 2 and cmd[1] in {"checkout", "push"} and root_key not in guarded_roots:
                    guarded_roots[root_key] = _resolve_and_install_guard(Path(cwd), original_run)

                if len(cmd) >= 2 and cmd[1] == "push":
                    default_branch = guarded_roots[root_key]
                    for arg in cmd[2:]:
                        if isinstance(arg, str) and (":" in arg or arg in {default_branch, f"refs/heads/{default_branch}"}):
                            assert_push_target(default_branch, arg)

                    changed = original_run(
                        ["git", "show", "--name-only", "--format=", "HEAD"], cwd=cwd
                    ).stdout.splitlines()
                    push_token, _privileged = select_push_token(
                        changed,
                        bot_token=os.environ["KUEPER_BOT_TOKEN"],
                        workflow_token=os.environ.get("KUEPER_WORKFLOW_TOKEN"),
                    )
                    # Restore an authenticated origin only at the controlled
                    # worker push boundary, after the agent process has exited.
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
