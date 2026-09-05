#!/usr/bin/env python3
"""Fail-closed guard for repository publication paths (ECO-ARC-0031-2026-DE).

An open/draft PR must never be replaced by writing equivalent content directly
to the default branch when Ready/Merge is unavailable. Worker-driven agents run
with shell access inside the cloned repository, so enforcement is layered:

1. decision guard     — the worker refuses any publication target that equals
                        the default branch, before checkout and before push;
2. sandbox guard      — a pre-push hook installed in the cloned repository
                        rejects git pushes to the default branch from inside
                        the agent sandbox;
3. verification guard — after the agent run, the remote default branch ref is
                        compared against the pre-run SHA. A detected mutation
                        is reported as a governance violation and the task is
                        parked instead of continuing.

The module is deliberately dependency-free so repository-local automation can
reuse the same checks.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class DefaultBranchMutationBlocked(RuntimeError):
    """A publication path targeting the default branch was refused."""


class DefaultBranchMutationDetected(RuntimeError):
    """The remote default branch changed during an agent run (governance violation)."""


class DefaultBranchVerificationFailed(RuntimeError):
    """The default branch could not be verified after an agent run (fail closed)."""


def assert_non_default_branch(target_branch: str, default_branch: str, *, context: str) -> None:
    """Refuse any publication path whose target is the default branch."""
    target = (target_branch or "").strip()
    default = (default_branch or "").strip()
    if not target or not default:
        raise DefaultBranchMutationBlocked(f"{context}: branch identity is missing")
    if target == default:
        raise DefaultBranchMutationBlocked(
            f"{context}: refusing direct write to default branch {default!r}; publish through the PR head"
        )


def assert_no_merge_substitute(
    *,
    pr_state: str,
    is_draft: bool,
    ready_or_merge_available: bool,
    target_branch: str,
    default_branch: str,
    context: str,
) -> None:
    """Reject a default-branch mutation used as a substitute for blocked PR lifecycle actions.

    Fail-closed semantics: an open (draft) PR whose Ready/Merge transition is
    technically unavailable must stay open and unchanged; its content may never
    be integrated directly on the default branch. Updating the PR head branch
    stays allowed.
    """
    state = (pr_state or "").upper()
    if state == "OPEN" and not ready_or_merge_available and target_branch == default_branch:
        detail = "draft " if is_draft else ""
        raise DefaultBranchMutationBlocked(
            f"{context}: {detail}PR is open and Ready/Merge is unavailable; keep the PR open and record the blocker"
        )
    assert_non_default_branch(target_branch, default_branch, context=context)


def pre_push_hook_script() -> str:
    """Return the sandbox pre-push hook that refuses pushes to the default branch.

    The hook resolves the default branch from the clone's origin/HEAD and rejects
    every push whose remote ref targets it. Feature branches pass through.
    """
    return """#!/bin/sh
# KUEPER default-branch guard (fail-closed, ECO-ARC-0031-2026-DE).
# An open/draft PR must never be replaced by direct integration on the default
# branch. This hook refuses git pushes to the default branch from the agent
# sandbox; the worker additionally verifies the remote ref after the agent run.
set -u
default="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
if [ -z "$default" ]; then
  default="main"
fi
while read -r _local_ref _local_sha remote_ref _remote_sha; do
  [ -n "$remote_ref" ] || continue
  case "$remote_ref" in
    "refs/heads/$default" | "$default")
      echo "KUEPER guard: push to default branch '$default' is forbidden (fail-closed)." >&2
      echo "Do not integrate PR content directly on the default branch as a merge substitute." >&2
      exit 1
      ;;
  esac
done
exit 0
"""


def install_pre_push_hook(repo_root: Path) -> Path:
    """Install the sandbox pre-push hook into a cloned repository."""
    hook = Path(repo_root) / ".git" / "hooks" / "pre-push"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(pre_push_hook_script(), encoding="utf-8")
    hook.chmod(0o755)
    return hook


def initial_default_sha(run: Any, root: Path, default_branch: str) -> str:
    """Record the default-branch SHA of a fresh clone before the agent runs."""
    return run(["git", "rev-parse", f"refs/remotes/origin/{default_branch}"], cwd=root).stdout.strip()


def parse_ls_remote_sha(stdout: str) -> str:
    """Extract the SHA from `git ls-remote` output."""
    for line in (stdout or "").splitlines():
        fields = line.split()
        if len(fields) >= 2:
            return fields[0]
    raise DefaultBranchVerificationFailed("remote default branch ref returned no SHA")


def assert_remote_default_unchanged(
    run: Any, root: Path, default_branch: str, expected_sha: str, *, context: str
) -> None:
    """Verify the remote default branch still matches the pre-run SHA.

    Raises DefaultBranchMutationDetected when the ref moved (governance
    violation) and DefaultBranchVerificationFailed when the check itself cannot
    be completed (fail closed: nothing is pushed in either case).
    """
    result = run(
        ["git", "ls-remote", "--exit-code", "origin", f"refs/heads/{default_branch}"],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        raise DefaultBranchVerificationFailed(
            f"{context}: could not verify remote default branch {default_branch!r} (fail closed)"
        )
    remote_sha = parse_ls_remote_sha(result.stdout)
    if remote_sha != expected_sha:
        raise DefaultBranchMutationDetected(
            f"{context}: remote default branch {default_branch!r} moved from {expected_sha} to "
            f"{remote_sha} during the agent run; refusing to continue (ECO-ARC-0031)"
        )
