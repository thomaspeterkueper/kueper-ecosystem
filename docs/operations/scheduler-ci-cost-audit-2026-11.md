# Scheduler and CI trigger cost audit (2026-11-13)

## Scope and evidence

This is a **read-only audit**, not a claim about the live Supabase scheduler. GitHub Actions currently cannot launch new jobs because the account has no available billed Actions budget. No job, billing setting, cron setting, lease or task has been changed in production by this document.

| Source | Current `main` / historical SQL | Draft proposal | Impact |
| --- | --- | --- | --- |
| `.github/workflows/agent-worker-v7.yml` | `*/15 * * * *` | `17 * * * *` (#135) | 4 to 1 native scheduled starts/hour |
| `.github/workflows/pr-review-agent.yml` | `7,22,37,52 * * * *` | `17 * * * *` (#135) | 4 to 1 native scheduled starts/hour |
| `.github/workflows/autonomous-loop.yml` | `7,22,37,52 * * * *` plus path-scoped push | `17 * * * *` plus push (#134) | 4 to 1 scheduled starts/hour; push remains immediate |
| `supabase/migrations/20260829143000_external_scheduler_control_plane.sql` | `kueper_enable_external_scheduler()` explicitly defines two *independent* pg_cron jobs with 15-minute cadence | **Not changed** | If enabled in the live DB, can still dispatch GitHub work every 15 minutes |

The same historical SQL defines `kueper_scheduler_health()` with a **25-minute** maximum age for both workers. An hourly cadence would cause false stale alerts if not adjusted. Do **not** edit historical applied migrations in place.

## Read-only live verification — correct control-plane database required

Before any schedule migration or cron mutation, identify the project actually hosting `ecosystem.scheduler_runs` and `ecosystem.scheduler_leases`. Connected Supabase projects may be unrelated; do not guess by name. With a database administrator's read-only session:

```sql
select jobid, jobname, schedule, active, command
from cron.job
where jobname in (
  'kueper-external-agent-worker-v7',
  'kueper-external-pr-review-agent'
)
order by jobname;
```

Avoid dumping decrypted Vault tokens. Check whether dispatch is actually happening, without exposing task payloads or credentials:

```sql
select worker_name, source, status, count(*) as runs
from ecosystem.scheduler_runs
where created_at >= now() - interval '24 hours'
group by worker_name, source, status
order by worker_name, source, status;
```

Inspect active scheduler job definitions and source-specific skips, then verify whether the external scheduler is needed at all. `kueper_acquire_scheduler_lease` already rejects active/cooldown duplicates, but rejected runs still consume GitHub startup time.

## Safe future changes — **not executed**

1. Decide which component owns the routine hourly dispatch (Supabase *or* GitHub). If Supabase is reliable, evaluate removing native GitHub cron triggers and retaining `workflow_dispatch`; only after a proven watchdog/recovery path exists. Otherwise ensure both cadences are hourly, offset to avoid accidental simultaneous dispatch, and keep lease acquisition.
2. Update existing live `cron.job` schedules only after checking their current values, preserving the job command, enabled status, name and invocation permissions. Supabase docs describe `cron.alter_job` for schedule updates. Use a new reviewed migration/operational change, not an edit of the previously applied 2026-08-29 migration.
3. Update `kueper_enable_external_scheduler()` re-enable behavior too, or reactivation can restore the old 15-minute cadence. Update `kueper_scheduler_health()` staleness threshold to reflect the chosen schedule plus dispatch jitter.
4. Test a single worker/reviewer dispatch end-to-end: `dispatch_requested -> started -> succeeded/failed`, run-id propagation, active-lease skips, cooldown skips, failure/recovery, jobs with time-delayed tasks and empty queue.
5. For the autonomous loop, preserve event-driven `push` handling; don't coarsely cancel running jobs because they may update a task bus.
6. Measure actual GitHub billed minutes and run counts for at least 24 hours after billing is restored. Lower cron frequency alone is not a measured cost reduction.

## Concurrency and safety classification

- **Safe to cancel on new PR commit:** read-only, PR-scoped validation only. Example: NOXIA earth parcel snapshot guard (#707), Ecosystem review-head-dedup tests (#137). Manual dispatch uses its own group.
- **Do not cancel merely because another trigger arrives:** worker tasks, reviewer decisions, research ingestion, migrations, external API writes, task-bus routing. Retain non-canceling concurrency and idempotency keys.
- **Different triggers can be complementary, not duplicates:** push changes to `.kueper/outbox/**` run immediate ingestion; the hourly cron is a fallback.
- **Any skipped GitHub job may still bill for its runner startup.** A true no-work dispatch reduction needs a pre-dispatch gate in the authoritative scheduler, not only a lease check inside Actions.

## Rollout gate

No production schedule changes before: (a) control-plane project identified, (b) live cron state read, (c) implementation tested locally/disposable DB and reviewed, (d) rollback documented, (e) billing block lifted sufficiently to run a controlled smoke test.
