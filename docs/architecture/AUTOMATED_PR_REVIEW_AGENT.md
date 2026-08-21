# KUEPER Automated PR Review Agent

Status: architecture draft

## Purpose

The Review Agent closes the implementation loop by independently reviewing agent-generated pull requests against the originating task, repository governance, architecture contracts and test evidence.

```text
Task -> Implementation Agent -> PR -> Review Agent
                              -> PASS
                              -> CHANGES_REQUIRED -> REVIEW_FIX -> updated PR -> re-review
```

The reviewer must be logically separate from the implementation run. Where provider/model availability permits, prefer a different model family or at minimum a distinct reviewer prompt/context to reduce correlated failure modes.

## Inputs

- originating task/request and acceptance criteria;
- PR metadata and complete changed-file diff;
- repository AGENTS/governance/source-of-truth rules;
- referenced Ecosystem architecture contracts;
- test/lint/typecheck/build results where available;
- prior structured review findings and their resolution state.

The reviewer MUST NOT infer acceptance criteria solely from the PR description.

## Review dimensions

V0.1 evaluates at least:

1. `TASK_FULFILLMENT`: requested behavior and expected result are actually implemented.
2. `ARCHITECTURE`: boundaries, ownership and referenced contracts are respected.
3. `CORRECTNESS`: logic defects, lifecycle/idempotency/concurrency/state errors and unsafe assumptions.
4. `TEST_QUALITY`: important acceptance and regression behavior is tested, not merely happy paths.
5. `INTEGRATION`: metadata/contracts survive boundaries and existing interfaces are not silently broken.
6. `SECURITY_GOVERNANCE`: no prohibited writes, secret exposure, authority escalation, auto-merge or source-of-truth violation.
7. `COST_RUNTIME`: provider/model/cost-policy metadata and bounded-loop behavior are preserved where relevant.

## Structured finding

```json
{
  "finding_id": "stable-fingerprint",
  "severity": "high",
  "category": "CORRECTNESS",
  "path": "lib/example.ts",
  "line": 123,
  "issue": "same unresolved condition may emit a second task after cooldown",
  "expected": "re-emission only after resolved -> regression",
  "evidence": ["task:...", "diff:...", "test:..."],
  "confidence": 0.98,
  "blocking": true
}
```

Fingerprints are based on the underlying issue, not generated wording.

## Verdict

- `PASS`: no blocking findings; non-blocking comments may remain.
- `CHANGES_REQUIRED`: one or more blocking findings.
- `REVIEW_ERROR`: review could not be completed reliably; park/retry, never interpret as PASS.

V0.1 does not auto-merge.

## Review-fix loop

For `CHANGES_REQUIRED`:

1. persist findings and review run identity;
2. publish a concise PR review/comment plus machine-readable artifact/state;
3. create or update one idempotent `REVIEW_FIX` task keyed by repository + PR + review generation;
4. provide the implementation/fix agent the task, current PR head and unresolved findings;
5. after new commits, re-run review;
6. mark findings resolved only when the new diff/state actually removes the condition.

The same unchanged PR head must not generate repeated REVIEW_FIX tasks.

## Independence and self-review

A review run records `implementation_provider/model/run` and `review_provider/model/run`. Policy should prefer independent review. If only the same model is available, the system may review with isolated context and a dedicated adversarial/checklist prompt, but must record that independence is reduced.

## Human boundary

V0.1 may comment, approve conceptually in machine state and request fixes, but it MUST NOT merge PRs. Human review remains possible at every stage. Later auto-merge may be introduced only for explicitly low-risk task classes with required checks and repository opt-in.

## Cost-aware scheduling

Review of a newly completed implementation is part of task completion and should normally run promptly. Large semantic/full-repository review can use `prefer_off_peak`, but blocking correctness/security review must not be deferred merely for cost savings. Re-review should focus on the changed head plus unresolved findings where safe.

## V0.1 implementation target

1. trigger/discover agent-generated PRs tied to KUEPER tasks;
2. resolve originating task and acceptance criteria;
3. load repository governance and referenced architecture documents;
4. collect full diff and available check results;
5. invoke a configurable review provider/model independently from the implementation provider where possible;
6. require structured JSON findings and verdict validated against a schema;
7. persist review runs/findings with stable fingerprints and PR head SHA;
8. post a concise GitHub PR comment/review;
9. create one idempotent REVIEW_FIX task for blocking findings;
10. re-review on a changed PR head and track resolved/unresolved findings;
11. deterministic tests for PASS, CHANGES_REQUIRED, unchanged-head deduplication and REVIEW_ERROR;
12. no auto-merge.

The first acceptance fixture should model the NOXIA observation-producer class of defect: a lifecycle/idempotency error and dropped `estimated_effort` boundary metadata must be detectable from task + architecture + diff/test context.
