# LLM Budget Control

The Control Plane treats semantic model calls as a bounded resource.

## Invariants

1. Routing happens before task claim.
2. Provider/cost-window deferral does not increment `attempt_count` and does not create a `task_runs` row.
3. An executable task is claimed only in the same database transaction that reserves its LLM invocation slot.
4. Budget exhaustion leaves the task `pending` and moves `available_at` to the next UTC budget window.
5. A concurrent worker that wins the task row causes the loser to receive `task-no-longer-runnable`; no invocation is reserved for the loser.
6. The private invocation ledger is not exposed through PostgREST tables. The Control Room receives only aggregate daily counters through `kueper_control_room_operations()`.

Current DeepSeek policy: 12 calls per UTC day, at most 2 Pro calls. These are operational guardrails, not provider pricing assumptions.
