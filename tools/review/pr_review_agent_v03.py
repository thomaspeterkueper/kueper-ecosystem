#!/usr/bin/env python3
"""KUEPER PR reviewer v0.3 — stdin transport for large review prompts.

V0.2 fixed noisy JSON extraction but still inherited v0.1's Claude invocation,
which passed the full review prompt as a command-line argument. Large PR diffs
can exceed the operating system ARG_MAX limit before Claude starts. This wrapper
keeps v0.2 review parsing and lifecycle semantics, but routes only Claude prompt
payloads through stdin.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import pr_review_agent_v02 as v02  # noqa: E402

base = v02.base
_original_run = base.worker.run


def run_with_stdin(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = True):
    """Preserve worker.run semantics while moving Claude's prompt off argv.

    The base reviewer invokes Claude as:
      claude -p --dangerously-skip-permissions <PROMPT>

    For that exact shape, remove the final prompt argument and send it as stdin.
    Every other command is delegated unchanged to the original worker helper.
    """
    if (
        len(cmd) >= 4
        and cmd[0] == "claude"
        and cmd[1] == "-p"
        and "--dangerously-skip-permissions" in cmd
    ):
        prompt = cmd[-1]
        cli = cmd[:-1]
        cp = subprocess.run(
            cli,
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if check and cp.returncode != 0:
            raise base.worker.WorkerError(
                f"command failed ({cp.returncode}): {' '.join(cli)}\n{(cp.stdout or '')[-5000:]}"
            )
        return cp
    return _original_run(cmd, cwd=cwd, env=env, check=check)


# Patch only the subprocess transport boundary. V0.2's JSON extraction,
# validation, persistence, idempotency and no-auto-merge semantics remain intact.
base.worker.run = run_with_stdin


def main() -> int:
    return v02.main()


if __name__ == "__main__":
    raise SystemExit(main())
