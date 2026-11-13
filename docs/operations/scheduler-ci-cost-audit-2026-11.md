# Scheduler and CI trigger cost audit (2026-11-13)

## Scope and evidence

This originally began as a **read-only audit**. The live scheduler was subsequently identified and adjusted as documented in the remediation section below. GitHub Actions currently cannot launch new jobs because the account has no available billed Actions budget. No job, billing setting, cron setting, lease or task has been changed in production by this document.

| Source | Current `main` / historical SQL | Draft proposal | Impact |
| --- | --- | --- | --- |
| `.github/workflows/agent-worker-v7.yml` | `*/15 * * * *` | `17 * * * *` (#135) | 4 to 1 native scheduled starts/hour |
| `.github/workflows/pr-review-agent.yml` | `7,22,37,52 * * * *` | `17 * * * *` (#135) | 4 to 1 native scheduled starts/hour |
| `.github/workflows/autonomous-loop.yml` | `7,22,37,52 * * * *` plus path-scoped push | `17 * * * *` plus push (#134) | 4 to 1 scheduled starts/hour; push remains immediate |
| `supabase/migrations/20260829143000_external_scheduler_control_plane.sql` | `kueper_enable_external_scheduler()` explicitly defines two *independent* pg_cron jobs with 15-minute cadence | **Not changed** | If enabled in the live DB, can still dispatch GitHub work every 15 minutes |

The same historical SQL defines `kueper_scheduler_health()` with a **25-minute** maximum age for both workers. An hourly cadence would cause false stale alerts if not adjusted. Do **not** edit historical applied migrations in place.

## Live control-plane remediation — 2026-11-13

**Database identified:** Supabase project `kueper-knowledge-graph` (the connected project containing `ecosystem.scheduler_runs`, `ecosystem.scheduler_leases` and the named `cron.job` entries). Other connected projects NOXIA/SSF do not contain these tables.

Verified before change:
- `kueper-external-agent-worker-v7`: `*/15 * * * *`, active, command `select public.kueper_scheduler_dispatch('agent-worker-v7');`
- `kueper-external-pr-review-agent`: `7,22,37,52 * * * *`, active, command `select public.kueper_scheduler_dispatch('pr-review-agent');`
- In the previous 48h, each Cron job recorded 192 succeeded *pg_cron invocations* (not proof of successful paid GitHub execution).
- The live `kueper_scheduler_health()` used a 25-minute stale tolerance.

**Applied in one guarded transaction, and verified read-back:**
1. `cron.alter_job` changed Agent Worker to `5 * * * *` and reviewer to `35 * * * *`. Job name, active state and dispatch command unchanged.
2. `public.kueper_scheduler_health()` now tolerates 85 minutes between observed scheduler events, preventing false stale classification due solely to the new hourly interval.
3. `public.kueper_enable_external_scheduler()` now recreates the same hourly schedules upon explicit re-enable (instead of silently restoring 15-minute runs).
4. Read-back verified both jobs active and hourly, both function definitions updated and current health rows `stale=false`.

No task queue, provider budget, Billing configuration, secrets or GitHub main branch changed. The operations change **was made live** in the connected control-plane DB; it is not merely a proposal. The prior migration file is retained as historical record and must not be rewritten.

**Caveats:** The separate native GitHub fallback `schedule` entries on `main` remain at their prior cadence until Draft PR #135 merges; current GitHub Actions billing block may prevent those jobs from running. Reduced Cron cadence reduces scheduled invocations but requires measured GitHub runner consumption to quantify money saved.

**Rollback if operationally required:** after verifying the original job identities and their exact commands, set Worker schedule back to `*/15 * * * *` and reviewer schedule back to `7,22,37,52 * * * *` with `cron.alter_job`; adjust health tolerance and the re-enable function together. Do not roll back the two schedules alone, as re-enable/health would become inconsistent.

**Follow-up:** Check the next hourly `cron.job_run_details` and `ecosystem.scheduler_runs` entries; compare expected dispatch records and no duplicate task execution. Record the changes as a forward-only schema/ops migration after review instead of retroactively editing the applied migration.

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
