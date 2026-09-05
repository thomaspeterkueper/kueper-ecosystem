# 20260905065000 verification

Production migration name: `worker_preclaim_budget_and_telemetry`.

Expected smoke checks:

- `kueper_peek_runnable_task(null,null)` is read-only and may return null when no task is currently runnable.
- `kueper_control_room_operations()->'llm_budget'` exposes aggregate counters only.
- `kueper_claim_task_with_llm_budget` must be called only by `service_role`; budget reservation and attempt increment occur in one transaction.
- `kueper_defer_unclaimed_task` leaves `attempt_count` unchanged.
