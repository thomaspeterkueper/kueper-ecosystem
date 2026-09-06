#!/usr/bin/env python3
"""KUEPER V7.3 worker.

Adds review lifecycle semantics:
- repository tasks that publish a new PR become review_pending, not completed;
- REVIEW_FIX tasks update the existing PR head instead of opening a second PR;
- stale REVIEW_FIX tasks are idempotently skipped when the PR head already moved.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker as worker  # noqa: E402
import agent_worker_v71 as v71  # noqa: E402
import agent_worker_v72 as v72  # noqa: E402
import default_branch_guard as branch_guard  # noqa: E402


def review_fix_repo_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    repo = str(task.get("repository") or "").strip()
    payload = task.get("payload") or {}
    pr_url = str(payload.get("pr_url") or "").strip()
    expected_head = str(payload.get("review_head_sha") or "").strip().lower()
    findings = payload.get("findings") or []
    if not repo or not pr_url or not expected_head or not isinstance(findings, list) or not findings:
        raise worker.WorkerError("REVIEW_FIX requires repository, pr_url, review_head_sha and non-empty findings")

    token = os.environ["KUEPER_BOT_TOKEN"]
    with tempfile.TemporaryDirectory(prefix="kueper-v73-review-fix-") as temp:
        root = Path(temp) / "repo"
        worker.run(["git", "clone", "--quiet", worker.clone_url(repo, token), str(root)])
        branch_guard.install_pre_push_hook(root)
        gh_env = os.environ.copy()
        gh_env["GH_TOKEN"] = token
        pr_meta_raw = worker.run([
            "gh", "pr", "view", pr_url, "--json", "headRefName,headRefOid,state,baseRefName"
        ], cwd=root, env=gh_env).stdout
        pr_meta = json.loads(pr_meta_raw)
        if pr_meta.get("state") != "OPEN":
            return {"kind": "completed", "summary": f"REVIEW_FIX obsolete: PR is {pr_meta.get('state')}"}

        current_head = str(pr_meta.get("headRefOid") or "").lower()
        head_branch = str(pr_meta.get("headRefName") or "").strip()
        base_ref = str(pr_meta.get("baseRefName") or "").strip()
        if not current_head or not head_branch:
            raise worker.WorkerError("could not resolve PR head")
        if not base_ref:
            raise worker.WorkerError("could not resolve PR base ref")
        if head_branch == base_ref:
            return {
                "kind": "park",
                "reason": f"REVIEW_FIX refuses to write: PR head branch {head_branch!r} equals its base branch; a fix there would be a direct default-branch write",
                "requires_owner_decision": True,
                "governance_violation": "default-branch-mutation",
            }
        initial_default_sha = branch_guard.initial_default_sha(worker.run, root, base_ref)
        if current_head != expected_head:
            return {
                "kind": "completed",
                "summary": "REVIEW_FIX obsolete because PR head already changed; reviewer must inspect new head",
                "expected_head": expected_head,
                "current_head": current_head,
            }

        worker.run(["git", "fetch", "origin", head_branch], cwd=root)
        worker.run(["git", "checkout", "-B", head_branch, f"origin/{head_branch}"], cwd=root)

        prompt = f"""You are the KUEPER REVIEW_FIX implementation agent for {repo}.
Update the EXISTING pull request {pr_url}. Do not open a new PR.
The review is anchored to head SHA {expected_head}.

Blocking findings:
{json.dumps(findings, ensure_ascii=False, indent=2)}

Rules:
- Read repository governance and the originating task context available in the findings/payload.
- Fix every blocking finding with the smallest complete change.
- Preserve unrelated behavior and existing architecture boundaries.
- Run relevant deterministic tests, typecheck/lint/build where practical.
- Do not weaken or delete tests to obtain green output.
- Do not merge the PR and do not switch it to Ready.
- Never commit, push, cherry-pick, reconstruct, or use a Contents/API write on the PR base/default branch as a substitute for Ready or Merge; if a lifecycle operation is unavailable, leave the PR unchanged and surface the blocker.
- Do not modify other repositories.
- If a finding cannot be fixed without an owner/creative decision, leave the repository unchanged and print `KUEPER_PARK_OWNER: <reason>`.
- Finish with only intentional working-tree changes.
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
            raise worker.WorkerError(f"review-fix agent failed ({agent.returncode}): {output[-5000:]}")

        if "KUEPER_PARK_OWNER:" in output:
            reason = output.split("KUEPER_PARK_OWNER:", 1)[1].splitlines()[0].strip()
            return {"kind": "park", "reason": reason, "requires_owner_decision": True}

        try:
            branch_guard.assert_remote_default_unchanged(
                worker.run, root, base_ref, initial_default_sha,
                context="review-fix agent run",
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
            return {"kind": "park", "reason": "blocking review findings remain but REVIEW_FIX produced no change", "requires_owner_decision": False}

        worker.run(["git", "config", "user.name", "KUEPER Ecosystem Bot"], cwd=root)
        worker.run(["git", "config", "user.email", "ecosystem-bot@users.noreply.github.com"], cwd=root)
        worker.run(["git", "add", "-A"], cwd=root)
        worker.run(["git", "commit", "-m", f"fix(review): address findings for {expected_head[:8]}"], cwd=root)
        branch_guard.assert_non_default_branch(head_branch, base_ref, context="review-fix push")
        worker.run(["git", "push", "--quiet", "origin", f"HEAD:{head_branch}"], cwd=root)
        new_head = worker.run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
        return {
            "kind": "completed",
            "summary": "Blocking review findings addressed on existing PR head branch",
            "pr_url": None,
            "previous_head": expected_head,
            "new_head": new_head,
            "agent_output": output[-4000:],
        }


def repo_task(task: dict[str, Any], model: str) -> dict[str, Any]:
    if str(task.get("type") or "").upper() == "REVIEW_FIX":
        return review_fix_repo_task(task, model)
    return v72.repo_task(task, model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tasks", type=int, default=int(os.environ.get("KUEPER_MAX_TASKS", "3")))
    args = parser.parse_args()
    required = ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "DEEPSEEK_API_KEY", "KUEPER_BOT_TOKEN"]
    missing = [x for x in required if not os.environ.get(x)]
    if missing:
        raise SystemExit(f"missing required secrets: {', '.join(missing)}")

    db = v71.PatchedSupabaseRPC(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    worker.repo_task = repo_task
    worker_id = f"github:{os.environ.get('GITHUB_RUN_ID', 'local')}:{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
    results: list[dict[str, Any]] = []
    task_failures = 0
    db.rpc("kueper_recover_expired_leases", {})

    for _ in range(max(1, args.max_tasks)):
        task = db.rpc("kueper_claim_task", {"p_worker_id": worker_id, "p_lease_seconds": 600, "p_target_project": None, "p_types": None})
        if not task:
            break
        decision = worker.route(task)
        task_id, lease = str(task["id"]), str(task["lease_token"])

        if decision.provider == "deepseek" and not db.rpc("kueper_provider_available", {"p_provider": "deepseek"}):
            available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=6)).isoformat()
            db.rpc("kueper_reschedule_provider_task", {"p_task_id": task_id, "p_lease_token": lease, "p_provider": "deepseek", "p_reason": "provider paused", "p_available_at": available_at})
            results.append({"task": task_id, "result": "provider-paused", "provider": "deepseek", "available_at": available_at})
            break

        if not decision.execute_now:
            db.rpc("kueper_reschedule_task", {"p_task_id": task_id, "p_lease_token": lease, "p_available_at": decision.available_at, "p_reason": decision.reason})
            results.append({"task": task_id, "result": "rescheduled", "available_at": decision.available_at})
            continue

        db.rpc("kueper_start_task", {"p_task_id": task_id, "p_lease_token": lease})
        try:
            with worker.Heartbeat(db, task_id, lease):
                outcome = worker.execute_task(task, decision.model)

            if outcome.get("kind") == "park":
                db.rpc("kueper_park_task", {
                    "p_task_id": task_id,
                    "p_lease_token": lease,
                    "p_reason": outcome["reason"],
                    "p_requires_owner_decision": bool(outcome.get("requires_owner_decision")),
                })
                results.append({"task": task_id, "result": "parked", "reason": outcome["reason"]})
            elif outcome.get("pr_url"):
                db.rpc("kueper_submit_task_for_review", {
                    "p_task_id": task_id,
                    "p_lease_token": lease,
                    "p_result": outcome,
                    "p_provider": decision.provider,
                    "p_model": decision.model,
                    "p_input_tokens": outcome.get("input_tokens"),
                    "p_output_tokens": outcome.get("output_tokens"),
                    "p_cost_estimate_eur": None,
                })
                results.append({"task": task_id, "result": "review_pending", "pr_url": outcome.get("pr_url"), "provider": decision.provider, "model": decision.model})
            else:
                db.rpc("kueper_complete_task", {
                    "p_task_id": task_id,
                    "p_lease_token": lease,
                    "p_result": outcome,
                    "p_provider": decision.provider,
                    "p_model": decision.model,
                    "p_input_tokens": outcome.get("input_tokens"),
                    "p_output_tokens": outcome.get("output_tokens"),
                    "p_cost_estimate_eur": None,
                })
                results.append({"task": task_id, "result": "completed", "provider": decision.provider, "model": decision.model})
        except worker.ProviderUnavailable as exc:
            db.rpc("kueper_pause_provider", {"p_provider": exc.provider, "p_reason": "billing-or-provider-unavailable", "p_error_code": exc.code, "p_error_message": exc.message[:2000], "p_pause_seconds": exc.pause_seconds})
            available_at = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=exc.pause_seconds)).isoformat()
            db.rpc("kueper_reschedule_provider_task", {"p_task_id": task_id, "p_lease_token": lease, "p_provider": exc.provider, "p_reason": str(exc), "p_available_at": available_at})
            results.append({"task": task_id, "result": "provider-paused", "provider": exc.provider, "available_at": available_at})
            break
        except Exception as exc:
            task_failures += 1
            try:
                db.rpc("kueper_fail_task", {"p_task_id": task_id, "p_lease_token": lease, "p_error": str(exc)[:4000], "p_retry_delay_seconds": 300})
            except Exception as fail_exc:
                print(f"ERROR could not record task failure: {fail_exc}", flush=True)
            print(f"::error title=Task execution failed::{task_id}: {str(exc)[:500]}", flush=True)
            results.append({"task": task_id, "result": "failed", "error": str(exc)})

    print(json.dumps({"worker": worker_id, "results": results}, ensure_ascii=False, indent=2))
    return 1 if task_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
