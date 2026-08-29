#!/usr/bin/env python3
"""Fail-closed guard for repository publication paths.

A PR/agent branch may be pushed, but an open/draft PR must never be replaced by
writing equivalent content directly to its default branch when Ready/Merge is
unavailable. This module is deliberately small so every worker publication path
can enforce the same invariant before a git push or API-backed content write.
"""
from __future__ import annotations


class DefaultBranchMutationBlocked(RuntimeError):
    pass


def assert_non_default_branch(target_branch: str, default_branch: str, *, context: str) -> None:
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
    """Reject a default-branch mutation used as a substitute for blocked PR lifecycle actions."""
    state = (pr_state or "").upper()
    if state == "OPEN" and not ready_or_merge_available and target_branch == default_branch:
        detail = "draft " if is_draft else ""
        raise DefaultBranchMutationBlocked(
            f"{context}: {detail}PR is open and Ready/Merge is unavailable; keep the PR open and record the blocker"
        )
    assert_non_default_branch(target_branch, default_branch, context=context)
