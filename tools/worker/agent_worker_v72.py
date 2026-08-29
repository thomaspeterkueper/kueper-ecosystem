#!/usr/bin/env python3
"""KUEPER V7.2 worker: V7.1 safety plus structured cross-project follow-up outbox."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker as worker  # noqa: E402
import agent_worker_v71 as v71  # noqa: E402
import default_branch_guard as branch_guard  # noqa: E402

TARGET_CODES = "ECO, KG, SSF, NOXIA, NXU, MISH, OMNI, AVI, CONTRA, ARCH, ENDIA, ZEREYA, DAVARU, FLHERM, RESETH, KUE, OTA, TKD"


def repo_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    repo = str(task.get("repository") or "").strip()
    if not repo:
        raise worker.WorkerError("repository task has no repository")
    token = os.environ["KUEPER_BOT_TOKEN"]
    with tempfile.TemporaryDirectory(prefix="kueper-v72-") as temp:
        root = Path(temp) / "repo"
        worker.run(["git", "clone", "--quiet", worker.clone_url(repo, token), str(root)])
        default_branch = worker.run(
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=root
        ).stdout.strip().split("/", 1)[-1]
        branch_guard.install_pre_push_hook(root)
        initial_default_sha = branch_guard.initial_default_sha(worker.run, root, default_branch)
        current_sha = worker.run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
        expected_sha = task.get("base_sha")
        if expected_sha and current_sha != expected_sha:
            raise worker.WorkerError(f"base SHA moved: expected {expected_sha}, current {current_sha}")

        branch = f"ecosystem/task-{task['id'][:8]}"
        branch_guard.assert_non_default_branch(branch, default_branch, context="repository task publication")
        worker.run(["git", "checkout", "-b", branch], cwd=root)
        payload = json.dumps(task.get("payload") or {}, ensure_ascii=False, indent=2)
        depth = int(task.get("depth") or 0)
        next_depth = depth + 1
        prompt = f"""You are the autonomous project owner for {repo}.
Read the repository and AGENTS.md if present before editing.
Task type: {task.get('type')}
Task id: {task.get('id')}
Priority: {task.get('priority')}
Task depth: {depth}

Payload:
{payload}

Rules:
- Re-evaluate the task against the current repository before changing anything.
- Implement the smallest complete solution owned by this repository.
- Run relevant tests/build/lint and repair failures caused by your changes.
- Never expose secrets or weaken tests.
- Do not edit other repositories.
- Never commit, push, cherry-pick, reconstruct, or use a Contents/API write on the default branch as a substitute for a PR, Ready transition, review, or merge.
- If a PR lifecycle operation is unavailable, leave the PR/head branch intact and surface the blocker; do not integrate equivalent content directly to the default branch.
- If blocked by a genuine owner/creative decision, leave the repo unchanged and print `KUEPER_PARK_OWNER: <reason>`.
- If blocked by a temporary internal dependency, leave the repo unchanged and print `KUEPER_PARK: <reason>`.
- Finish with only intentional working-tree changes.

Cross-project follow-ups:
- Only when this task reveals a CONCRETE, NECESSARY dependency owned by another repository for the same goal, create a JSON envelope under `.kueper/outbox/`.
- Do not create speculative ideas, nice-to-have work, or unrelated improvements as follow-ups.
- Do not edit the target repository yourself; the ecosystem loop will route and queue it.
- Allowed target codes: {TARGET_CODES}.
- Maximum routing depth is 3. Current next depth is {next_depth}; if that exceeds 3, do not emit another follow-up and park if the dependency blocks completion.
- Each envelope must be valid JSON with exactly the useful fields below:
  {{
    "target": "KG",
    "title": "Short concrete title",
    "reason": "Why this became necessary from the current task",
    "requested_change": "Smallest complete change owned by the target repository",
    "expected_result": "Observable completion criterion",
    "priority": "low|medium|high|critical",
    "parent_task": "{task.get('id')}",
    "depth": {next_depth},
    "affects": ["source-code", "target-code"]
  }}
- One dependency per envelope. Use stable descriptive filenames. If no necessary cross-project dependency exists, create no outbox file.
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
        agent = worker.run(["claude", "-p", "--dangerously-skip-permissions", prompt], cwd=root, env=env, check=False)
        output = agent.stdout or ""
        if agent.returncode != 0:
            lower = output.lower()
            if "insufficient balance" in lower or "http 402" in lower:
                raise worker.ProviderUnavailable("deepseek", "billing-insufficient-balance", output[-2000:], 21600)
            if "429" in lower or "rate limit" in lower:
                raise worker.ProviderUnavailable("deepseek", "rate-limit", output[-2000:], 1800)
            raise worker.WorkerError(f"agent failed ({agent.returncode}): {output[-5000:]}")

        for marker, owner in (("KUEPER_PARK_OWNER:", True), ("KUEPER_PARK:", False)):
            if marker in output:
                reason = output.split(marker, 1)[1].splitlines()[0].strip()
                return {"kind": "park", "reason": reason, "requires_owner_decision": owner}

        try:
            branch_guard.assert_remote_default_unchanged(
                worker.run, root, default_branch, initial_default_sha,
                context=f"task {task['id'][:8]} agent run",
            )
        except branch_guard.DefaultBranchMutationDetected as exc:
            return {
                "kind": "park",
                "reason": str(exc),
                "requires_owner_decision": True,
                "governance_violation": "default-branch-mutation",
            }
        except branch_guard.DefaultBranchVerificationFailed as exc:
            return {"kind": "park", "reason": str(exc), "requires_owner_decision": False}

        status = worker.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root).stdout.strip()
        if not status:
            return {"kind": "completed", "summary": "Agent found no repository change necessary", "agent_output": output[-4000:]}

        worker.run(["git", "config", "user.name", "KUEPER Ecosystem Bot"], cwd=root)
        worker.run(["git", "config", "user.email", "ecosystem-bot@users.noreply.github.com"], cwd=root)
        worker.run(["git", "add", "-A"], cwd=root)
        worker.run(["git", "commit", "-m", f"chore(agent): execute task {task['id'][:8]}"], cwd=root)
        branch_guard.assert_non_default_branch(branch, default_branch, context="repository task push")
        worker.run(["git", "push", "--quiet", "origin", branch], cwd=root)
        gh_env = env.copy()
        gh_env["GH_TOKEN"] = token
        pr = worker.run([
            "gh", "pr", "create", "--repo", repo, "--base", default_branch, "--head", branch,
            "--title", f"[Agent] {task.get('type')}: {task['id'][:8]}",
            "--body", f"Autonomous KUEPER V7.2 task `{task['id']}`. Provider: DeepSeek / {model}.",
        ], cwd=root, env=gh_env).stdout.strip()
        outbox_files = [x.strip() for x in worker.run(
            ["git", "show", "--name-only", "--format=", "HEAD"], cwd=root
        ).stdout.splitlines() if x.strip().startswith(".kueper/outbox/")]
        return {
            "kind": "completed",
            "summary": "Repository changes published as PR",
            "pr_url": pr,
            "followup_envelopes": outbox_files,
            "agent_output": output[-4000:],
        }


def main() -> int:
    worker.SupabaseRPC = v71.PatchedSupabaseRPC
    worker.repo_task = repo_task
    return worker.main()


if __name__ == "__main__":
    raise SystemExit(main())
