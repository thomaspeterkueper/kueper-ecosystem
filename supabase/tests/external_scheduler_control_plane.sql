-- Run after 20260829143000_external_scheduler_control_plane.sql.
-- This test intentionally does not enable cron jobs or require a GitHub token.

begin;

do $$
declare
  first_result jsonb;
  second_result jsonb;
  run_id uuid;
  token uuid;
begin
  first_result := public.kueper_acquire_scheduler_lease(
    'agent-worker-v7', null, 'manual', 600, 600
  );
  if coalesce((first_result->>'acquired')::boolean,false) is not true then
    raise exception 'expected first scheduler lease to be acquired: %', first_result;
  end if;

  run_id := (first_result->>'run_id')::uuid;
  token := (first_result->>'lease_token')::uuid;

  second_result := public.kueper_acquire_scheduler_lease(
    'agent-worker-v7', null, 'github_schedule', 600, 600
  );
  if coalesce((second_result->>'acquired')::boolean,true) is not false
     or second_result->>'reason' <> 'active_lease' then
    raise exception 'expected duplicate execution to be rejected by active lease: %', second_result;
  end if;

  if public.kueper_finish_scheduler_run(run_id, token, 'succeeded', 123456789, null) is not true then
    raise exception 'expected scheduler finish to succeed';
  end if;

  second_result := public.kueper_acquire_scheduler_lease(
    'agent-worker-v7', null, 'github_schedule', 600, 600
  );
  if coalesce((second_result->>'acquired')::boolean,true) is not false
     or second_result->>'reason' <> 'cooldown' then
    raise exception 'expected immediate duplicate execution to be rejected by cooldown: %', second_result;
  end if;

  if not exists(
    select 1 from public.kueper_scheduler_health()
    where worker_name='agent-worker-v7' and stale=false
  ) then
    raise exception 'scheduler health did not observe recent agent-worker execution';
  end if;
end
$$;

rollback;
