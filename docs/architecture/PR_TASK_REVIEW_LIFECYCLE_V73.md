# KUEPER V7.3 — PR Task & Review Lifecycle

Status: implementation contract  
Date: 2026-08-24

## Problem

V7.2 treated successful PR creation as terminal task completion:

```text
Task -> implementation -> PR -> COMPLETED
```

That makes later review findings operationally invisible. A human or automated review can request changes, but there is no runnable task left to carry the PR through fix and re-review.

NOXIA PR #10 exposed the defect directly: implementation succeeded, the External Task was marked done, then two blocking findings were posted. Because the originating execution task was already terminal, no REVIEW_FIX work was generated.

## V7.3 lifecycle

Repository-changing tasks now use:

```text
PENDING
  -> CLAIMED
  -> RUNNING
  -> REVIEW_PENDING
       -> PASS -------------------------------> COMPLETED
       -> CHANGES_REQUIRED -> REVIEW_FIX
                              -> updated PR head
                              -> REVIEW_PENDING (same parent task)
                                   -> PASS ----> COMPLETED
                                   -> CHANGES_REQUIRED -> next REVIEW_FIX generation
```

`COMPLETED` means accepted implementation, not merely published implementation.

A task that produces no PR may still complete directly when its own task semantics are terminal (for example a bounded non-repository analysis). A REVIEW_FIX child task completes after it updates the existing PR branch; acceptance remains the responsibility of the parent task's next review generation.

## State plane

V7.3 adds task status `review_pending` and `ecosystem.pr_review_runs`.

Each review generation is unique by:

```text
(originating task id, PR head SHA)
```

Therefore an unchanged head cannot create repeated REVIEW_FIX tasks or repeated model spend.

A persisted review contains:

- task id;
- PR URL;
- exact head SHA;
- verdict (`PASS` or `CHANGES_REQUIRED`);
- provider/model;
- summary;
- structured findings;
- timestamp.

`PASS` can complete a task only when a PASS record exists for the exact supplied head SHA.

## Reviewer invariants

The reviewer validates:

1. task fulfillment;
2. architecture boundaries;
3. correctness and lifecycle/idempotency behavior;
4. test quality;
5. integration and boundary metadata;
6. security/governance;
7. cost/runtime semantics.

Structured output is schema-checked before persistence:

- `PASS` with a blocking finding is invalid;
- `CHANGES_REQUIRED` without a blocking finding is invalid;
- finding IDs must be stable and unique per review generation;
- severity/category/confidence are validated.

`REVIEW_ERROR` is never converted into PASS and is not persisted as a completed review generation, allowing a later retry.

## REVIEW_FIX semantics

A blocking review creates exactly one task with idempotency key:

```text
review-fix:<originating-task-id>:<review-head-sha>
```

The task payload carries:

- existing PR URL;
- reviewed head SHA;
- originating task id and payload;
- blocking structured findings.

The V7.3 worker checks out the existing PR head branch and pushes fixes to that branch. It MUST NOT create a second PR.

Before editing, it re-reads the current PR head. If the head no longer equals the reviewed SHA, the REVIEW_FIX generation is stale and is completed without writing; the reviewer will inspect the newer head instead.

## Auto-merge boundary

V7.3 has no auto-merge authority.

A PASS transitions task state to `completed`, but merging remains outside this agent version. Research-candidate auto-merge policies remain separate and do not grant implementation PR merge authority.

A blocked Ready/Merge transition is likewise no license for a default-branch write. When the connector cannot execute Ready/Merge, the PR stays open/draft and the technical blocker is recorded as review-/merge-blocked. Direct default-branch integration as a merge substitute — cherry-pick, re-committing the same changes on the base, or a Contents-API write — is forbidden and enforced fail-closed by `tools/worker/default_branch_guard.py` (decision guard, sandbox pre-push hook, post-run remote verification). See ECO-ARC-0031-2026-DE.

## Cost behavior

Initial implementation follows the normal task cost policy. Review is part of task completion and runs promptly. Review generations are head-SHA deduplicated to prevent repeated model cost. REVIEW_FIX is high priority for normal implementations and critical when the originating task is critical.

## Deployment order

The database contract must exist before the V7.3 worker/reviewer is activated.

1. Merge/deploy code only in a controlled window or temporarily disable the scheduled worker.
2. Apply `supabase/migrations/20260824093000_pr_review_lifecycle.sql` to the existing Ecosystem state-plane database.
3. Verify the new RPCs are callable by `service_role`.
4. Enable/run `agent-worker-v7.yml` using `agent_worker_v73.py`.
5. Enable/run `pr-review-agent.yml`.
6. Start with one bounded implementation task and verify:
   - PR creation yields `review_pending`, not `completed`;
   - one review generation is persisted for the current head;
   - CHANGES_REQUIRED yields exactly one REVIEW_FIX task;
   - REVIEW_FIX updates the same PR;
   - changed head is reviewed again;
   - only PASS on that new head yields `completed`.

Do not activate the V7.3 worker against a database that has not received the migration; failing closed is preferable to restoring premature completion semantics.

## Regression fixture

NOXIA PR #10 is the reference fixture. The two originally observed defect classes are:

- an unresolved condition being re-emitted merely because a cooldown elapsed instead of requiring `RESOLVED -> REGRESSION`;
- `estimated_effort` being dropped at the TaskCandidate -> Outbox boundary.

Both must be covered by deterministic tests in the NOXIA implementation and should be independently detectable by the reviewer from task + architecture + diff/test evidence.
