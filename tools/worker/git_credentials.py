"""Credential selection for repository pushes.

Workflow-file changes are a privileged mutation class and must use a
separate credential from the normal KUEPER bot token.
"""
from __future__ import annotations

from collections.abc import Iterable

WORKFLOW_PREFIX = ".github/workflows/"


class PrivilegedCredentialMissing(RuntimeError):
    """Raised when a privileged workflow mutation has no dedicated token."""


def is_privileged_workflow_change(paths: Iterable[str]) -> bool:
    return any(str(path).replace("\\", "/").startswith(WORKFLOW_PREFIX) for path in paths)


def select_push_token(
    paths: Iterable[str],
    *,
    bot_token: str,
    workflow_token: str | None,
) -> tuple[str, bool]:
    privileged = is_privileged_workflow_change(paths)
    if not privileged:
        return bot_token, False
    if not workflow_token:
        raise PrivilegedCredentialMissing(
            "privileged workflow change requires KUEPER_WORKFLOW_TOKEN"
        )
    return workflow_token, True
