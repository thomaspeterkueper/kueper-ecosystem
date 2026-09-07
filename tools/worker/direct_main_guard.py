#!/usr/bin/env python3
"""Fail closed against autonomous writes to a repository default branch."""
from __future__ import annotations

import stat
from pathlib import Path


class DefaultBranchMutationBlocked(RuntimeError):
    pass


def validate_push_lines(default_branch: str, lines: str) -> None:
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
    if not default_branch or default_branch in {"HEAD", ".", ".."}:
        raise ValueError("default branch must be resolved before installing push guard")
    hooks = repo_root / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-push"
    hook.write_text(hook_script(default_branch), encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return hook


def assert_push_target(default_branch: str, target: str) -> None:
    target = (target or "").strip()
    if not target:
        return
    remote_target = target.rsplit(":", 1)[-1]
    if remote_target in {default_branch, f"refs/heads/{default_branch}"}:
        raise DefaultBranchMutationBlocked(
            f"direct push to default branch {default_branch!r} is forbidden"
        )
