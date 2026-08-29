# External Scheduler for Agent Worker and PR Review

## Purpose

GitHub Actions remains the executor, but Supabase becomes the primary scheduler for:

- `KUEPER Agent Worker V7`
- `KUEPER Automated PR Review`

The native GitHub `schedule` triggers remain in place as a fallback. A Supabase-backed execution lease and 10-minute cooldown prevent both trigger sources from doing the same expensive work twice.

## Components

- `ecosystem.scheduler_runs`: dispatch/start/finish heartbeat history
- `ecosystem.scheduler_leases`: one short-lived execution lease per worker
- `public.kueper_scheduler_dispatch(worker)`: allow-listed GitHub `workflow_dispatch`
- `public.kueper_acquire_scheduler_lease(...)`: fail-closed duplicate guard
- `public.kueper_finish_scheduler_run(...)`: terminal heartbeat and lease release
- `public.kueper_scheduler_health()`: compact stale-state query
- `public.kueper_enable_external_scheduler()`: explicit cron activation
- `public.kueper_disable_external_scheduler()`: immediate rollback of external cron jobs
- `tools/scheduler/run_guard.py`: GitHub-side RPC client, stdlib only

## Security boundary

The GitHub dispatch credential is never committed and never returned by an RPC. Store it in Supabase Vault under exactly:

`kueper_github_dispatch_token`

Use a credential dedicated to this scheduler. It only needs permission to dispatch Actions workflows in `thomaspeterkueper/kueper-ecosystem`; do not reuse a broader repository administration token.

## Activation

The migration is intentionally inert after installation: it creates the schema/functions but no cron jobs.

After the Vault secret exists, activate once with a service-role/admin SQL session:

```sql
select public.kueper_enable_external_scheduler();
```

Expected cron cadence:

- Agent Worker: `*/15 * * * *`
- PR Review: `7,22,37,52 * * * *`

## Verification

Query:

```sql
select * from public.kueper_scheduler_health();
```

Then confirm two successive intervals for each worker contain Supabase-originated runs that reach `started` and a terminal state. A GitHub-native schedule arriving during an active lease or within the cooldown should finish cheaply with a `skipped` scheduler run rather than invoke the agent/reviewer.

For detail:

```sql
select id, worker_name, source, status, dispatch_requested_at, started_at,
       finished_at, github_run_id, last_error
from ecosystem.scheduler_runs
order by created_at desc
limit 50;
```

## Rollback

Disable only the external cron source:

```sql
select public.kueper_disable_external_scheduler();
```

The GitHub-native schedule remains present in both workflow files, so disabling the Supabase scheduler does not remove the existing fallback.

## Failure modes

If Supabase cannot be reached from a GitHub run, the lease guard fails closed. This is intentional: the worker and reviewer already depend on Supabase for their task state, and running without the duplicate-control boundary could create unnecessary LLM/API cost.

If the Vault token is missing, activation fails before any cron jobs are installed. If a later GitHub dispatch request is rejected, `scheduler_runs` preserves the dispatch request and subsequent lack of `started_at` makes the missed execution visible instead of silently losing it.
