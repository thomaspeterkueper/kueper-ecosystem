#!/usr/bin/env python3
"""Fail-closed guard against agent writes to a repository default branch.

The guard is installed as a local Git pre-push hook inside every temporary
worker clone. It therefore also covers git commands started by the coding agent
itself, not only pushes issued through worker.run().
"""
from __future__ import annotations

import os
import stat
from pathlib import Path


class DefaultBranchMutationBlocked(RuntimeError):
    pass


def validate_push_lines(default_branch: str, lines: str) -> None:
    """Reject a pre-push stream that targets refs/heads/<default_branch>."""
    protected_ref = f"refs/heads/{default_branch}"
    for raw in lines.splitlines():
        fields = raw.split()
        if len(fields) >= 3 and fields[2] == protected_ref:
            raise DefaultBranchMutationBlocked(
                f"direct push to default branch {default_branch!r} is forbidden; publish/update a PR branch instead"
            )


def hook_script(default_branch: str) -> str:
    protected_ref = f"refs/heads/{default_branch}"
    return f'''#!/bin/sh
set -eu
protected_ref={protected_ref!r}
while read local_ref local_sha remote_ref remote_sha; do
  if [ "$remote_ref" = "$protected_ref" ]; then
    echo "KUEPER guard: direct push to default branch {default_branch} is forbidden; keep the PR open/blocked instead." >&2
    exit 41
  fi
done
exit 0
'''


def install_pre_push_guard(repo_root: Path, default_branch: str) -> Path:
    """Install the deterministic guard in a worker clone and return hook path."""
    if not default_branch or default_branch in {"HEAD", ".", ".."}:
        raise ValueError("default branch must be resolved before installing push guard")
    hooks = repo_root / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-push"
    hook.write_text(hook_script(default_branch), encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return hook


def assert_push_target(default_branch: str, target: str) -> None:
    """Second-line guard for worker-managed explicit refspecs."""
    target = (target or "").strip()
    if not target:
        return
    remote_target = target.rsplit(":", 1)[-1]
    if remote_target in {default_branch, f"refs/heads/{default_branch}"}:
        raise DefaultBranchMutationBlocked(
            f"direct push to default branch {default_branch!r} is forbidden"
        )
