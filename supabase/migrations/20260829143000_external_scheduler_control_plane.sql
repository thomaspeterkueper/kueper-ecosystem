-- KUEPER external scheduler control plane
--
-- Purpose:
--   1. make Supabase the reliable scheduler for selected GitHub Actions workflows,
--   2. retain GitHub `schedule` as a fallback,
--   3. prevent duplicate expensive executions through a short execution lease/cooldown,
--   4. persist dispatch/start/finish heartbeats so missed intervals become observable.
--
-- Activation is deliberately fail-closed. This migration does NOT install cron jobs.
-- Call public.kueper_enable_external_scheduler() only after a GitHub token with the
-- minimal Actions workflow-dispatch permission has been stored in Supabase Vault as
-- `kueper_github_dispatch_token`.

create extension if not exists pgcrypto;
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron with schema extensions;
create schema if not exists ecosystem;

create table if not exists ecosystem.scheduler_runs (
  id uuid primary key default gen_random_uuid(),
  worker_name text not null check (worker_name in ('agent-worker-v7','pr-review-agent')),
  source text not null check (source in ('supabase','github_schedule','manual')),
  scheduled_for timestamptz not null default now(),
  status text not null default 'planned' check (status in ('planned','dispatch_requested','started','succeeded','failed','skipped')),
  request_id bigint,
  github_run_id bigint,
  lease_token uuid,
  dispatch_requested_at timestamptz,
  started_at timestamptz,
  finished_at timestamptz,
  last_error text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists scheduler_runs_worker_created_idx
  on ecosystem.scheduler_runs(worker_name, created_at desc);
create index if not exists scheduler_runs_status_created_idx
  on ecosystem.scheduler_runs(status, created_at desc);

create table if not exists ecosystem.scheduler_leases (
  worker_name text primary key check (worker_name in ('agent-worker-v7','pr-review-agent')),
  run_id uuid references ecosystem.scheduler_runs(id) on delete set null,
  lease_token uuid,
  lease_expires_at timestamptz,
  last_started_at timestamptz,
  last_finished_at timestamptz,
  updated_at timestamptz not null default now()
);

create or replace function ecosystem.kueper_scheduler_touch_updated_at()
returns trigger
language plpgsql
set search_path=ecosystem,pg_temp
as $$
begin
  new.updated_at := now();
  return new;
end
$$;

drop trigger if exists scheduler_runs_touch_updated_at on ecosystem.scheduler_runs;
create trigger scheduler_runs_touch_updated_at
before update on ecosystem.scheduler_runs
for each row execute function ecosystem.kueper_scheduler_touch_updated_at();

-- Acquire a lease before any expensive setup/LLM work. A recent successful or running
-- execution creates a cooldown window as well, so a GitHub-schedule fallback that
-- arrives shortly after the Supabase dispatch exits cheaply instead of doing duplicate work.
create or replace function public.kueper_acquire_scheduler_lease(
  p_worker_name text,
  p_run_id uuid default null,
  p_source text default 'manual',
  p_lease_seconds integer default 5400,
  p_cooldown_seconds integer default 600
) returns jsonb
language plpgsql
security definer
set search_path=ecosystem,public,pg_temp
as $$
declare
  v_run ecosystem.scheduler_runs;
  v_lease ecosystem.scheduler_leases;
  v_token uuid := gen_random_uuid();
  v_now timestamptz := now();
begin
  if p_worker_name not in ('agent-worker-v7','pr-review-agent') then
    raise exception 'unsupported scheduler worker: %', p_worker_name;
  end if;
  if p_source not in ('supabase','github_schedule','manual') then
    raise exception 'invalid scheduler source: %', p_source;
  end if;
  if p_lease_seconds < 60 or p_lease_seconds > 7200 then
    raise exception 'lease seconds out of range';
  end if;
  if p_cooldown_seconds < 0 or p_cooldown_seconds > 1800 then
    raise exception 'cooldown seconds out of range';
  end if;

  if p_run_id is not null then
    select * into v_run
      from ecosystem.scheduler_runs
      where id = p_run_id and worker_name = p_worker_name
      for update;
    if v_run.id is null then
      raise exception 'scheduler run not found for worker';
    end if;
  else
    insert into ecosystem.scheduler_runs(worker_name, source, scheduled_for, status)
    values (p_worker_name, p_source, v_now, 'planned')
    returning * into v_run;
  end if;

  insert into ecosystem.scheduler_leases(worker_name)
  values (p_worker_name)
  on conflict (worker_name) do nothing;

  select * into v_lease
    from ecosystem.scheduler_leases
    where worker_name = p_worker_name
    for update;

  if v_lease.lease_expires_at is not null and v_lease.lease_expires_at > v_now then
    update ecosystem.scheduler_runs
       set status='skipped', finished_at=v_now,
           last_error='active execution lease'
     where id=v_run.id;
    return jsonb_build_object('acquired',false,'run_id',v_run.id,'reason','active_lease');
  end if;

  if v_lease.last_finished_at is not null
     and v_lease.last_finished_at > v_now - make_interval(secs => p_cooldown_seconds) then
    update ecosystem.scheduler_runs
       set status='skipped', finished_at=v_now,
           last_error='recent execution cooldown'
     where id=v_run.id;
    return jsonb_build_object('acquired',false,'run_id',v_run.id,'reason','cooldown');
  end if;

  update ecosystem.scheduler_leases
     set run_id=v_run.id,
         lease_token=v_token,
         lease_expires_at=v_now + make_interval(secs => p_lease_seconds),
         last_started_at=v_now,
         updated_at=v_now
   where worker_name=p_worker_name;

  update ecosystem.scheduler_runs
     set status='started', started_at=coalesce(started_at,v_now), lease_token=v_token
   where id=v_run.id;

  return jsonb_build_object('acquired',true,'run_id',v_run.id,'lease_token',v_token);
end
$$;

create or replace function public.kueper_finish_scheduler_run(
  p_run_id uuid,
  p_lease_token uuid,
  p_status text,
  p_github_run_id bigint default null,
  p_error text default null
) returns boolean
language plpgsql
security definer
set search_path=ecosystem,public,pg_temp
as $$
declare
  v_worker text;
  v_now timestamptz := now();
begin
  if p_status not in ('succeeded','failed') then
    raise exception 'invalid terminal scheduler status';
  end if;

  select worker_name into v_worker
    from ecosystem.scheduler_runs
    where id=p_run_id and lease_token=p_lease_token
    for update;
  if v_worker is null then
    raise exception 'scheduler run lease invalid';
  end if;

  update ecosystem.scheduler_runs
     set status=p_status,
         finished_at=v_now,
         github_run_id=coalesce(p_github_run_id,github_run_id),
         last_error=p_error
   where id=p_run_id;

  update ecosystem.scheduler_leases
     set run_id=null,
         lease_token=null,
         lease_expires_at=null,
         last_finished_at=v_now,
         updated_at=v_now
   where worker_name=v_worker and lease_token=p_lease_token;

  return true;
end
$$;

-- Supabase-side dispatcher. The token is read only inside this SECURITY DEFINER
-- function from Vault and is never returned to callers or persisted in run rows.
create or replace function public.kueper_scheduler_dispatch(p_worker_name text)
returns uuid
language plpgsql
security definer
set search_path=ecosystem,public,extensions,vault,pg_temp
as $$
declare
  v_run_id uuid := gen_random_uuid();
  v_token text;
  v_workflow text;
  v_inputs jsonb;
  v_request_id bigint;
begin
  case p_worker_name
    when 'agent-worker-v7' then
      v_workflow := 'agent-worker-v7.yml';
      v_inputs := jsonb_build_object('max_tasks','3','scheduler_run_id',v_run_id::text);
    when 'pr-review-agent' then
      v_workflow := 'pr-review-agent.yml';
      v_inputs := jsonb_build_object('max_reviews','3','scheduler_run_id',v_run_id::text);
    else
      raise exception 'unsupported scheduler worker: %', p_worker_name;
  end case;

  select decrypted_secret into v_token
    from vault.decrypted_secrets
    where name='kueper_github_dispatch_token'
    limit 1;
  if coalesce(v_token,'')='' then
    raise exception 'Vault secret kueper_github_dispatch_token is not configured';
  end if;

  insert into ecosystem.scheduler_runs(id,worker_name,source,scheduled_for,status,dispatch_requested_at)
  values(v_run_id,p_worker_name,'supabase',now(),'dispatch_requested',now());

  select net.http_post(
    url := format('https://api.github.com/repos/thomaspeterkueper/kueper-ecosystem/actions/workflows/%s/dispatches',v_workflow),
    headers := jsonb_build_object(
      'Accept','application/vnd.github+json',
      'Authorization','Bearer ' || v_token,
      'X-GitHub-Api-Version','2022-11-28',
      'User-Agent','kueper-supabase-scheduler'
    ),
    body := jsonb_build_object('ref','main','inputs',v_inputs),
    timeout_milliseconds := 10000
  ) into v_request_id;

  update ecosystem.scheduler_runs set request_id=v_request_id where id=v_run_id;
  return v_run_id;
exception when others then
  if exists(select 1 from ecosystem.scheduler_runs where id=v_run_id) then
    update ecosystem.scheduler_runs
       set status='failed', finished_at=now(), last_error=sqlerrm
     where id=v_run_id;
  end if;
  raise;
end
$$;

-- Activation is explicit and idempotent. No background traffic begins until this is called.
create or replace function public.kueper_enable_external_scheduler()
returns jsonb
language plpgsql
security definer
set search_path=ecosystem,public,extensions,vault,cron,pg_temp
as $$
declare
  v_token text;
begin
  select decrypted_secret into v_token
    from vault.decrypted_secrets
    where name='kueper_github_dispatch_token'
    limit 1;
  if coalesce(v_token,'')='' then
    raise exception 'Vault secret kueper_github_dispatch_token is not configured';
  end if;

  perform cron.unschedule(jobid)
    from cron.job
    where jobname in ('kueper-external-agent-worker-v7','kueper-external-pr-review-agent');

  perform cron.schedule(
    'kueper-external-agent-worker-v7',
    '*/15 * * * *',
    $cron$select public.kueper_scheduler_dispatch('agent-worker-v7');$cron$
  );
  perform cron.schedule(
    'kueper-external-pr-review-agent',
    '7,22,37,52 * * * *',
    $cron$select public.kueper_scheduler_dispatch('pr-review-agent');$cron$
  );

  return jsonb_build_object('enabled',true,'agent_worker','*/15 * * * *','pr_review','7,22,37,52 * * * *');
end
$$;

create or replace function public.kueper_disable_external_scheduler()
returns jsonb
language plpgsql
security definer
set search_path=ecosystem,public,extensions,cron,pg_temp
as $$
begin
  perform cron.unschedule(jobid)
    from cron.job
    where jobname in ('kueper-external-agent-worker-v7','kueper-external-pr-review-agent');
  return jsonb_build_object('enabled',false);
end
$$;

create or replace function public.kueper_scheduler_health()
returns table(
  worker_name text,
  last_dispatch_at timestamptz,
  last_started_at timestamptz,
  last_finished_at timestamptz,
  last_status text,
  stale boolean
)
language sql
security definer
set search_path=ecosystem,public,pg_temp
as $$
  with workers(worker_name,max_age) as (
    values ('agent-worker-v7'::text, interval '25 minutes'),
           ('pr-review-agent'::text, interval '25 minutes')
  ), latest as (
    select distinct on (r.worker_name)
           r.worker_name,r.dispatch_requested_at,r.started_at,r.finished_at,r.status,r.created_at
      from ecosystem.scheduler_runs r
     order by r.worker_name,r.created_at desc
  )
  select w.worker_name,
         l.dispatch_requested_at,
         l.started_at,
         l.finished_at,
         l.status,
         (l.created_at is null or l.created_at < now()-w.max_age) as stale
    from workers w
    left join latest l using(worker_name)
   order by w.worker_name;
$$;

revoke all on function public.kueper_acquire_scheduler_lease(text,uuid,text,integer,integer) from public,anon,authenticated;
revoke all on function public.kueper_finish_scheduler_run(uuid,uuid,text,bigint,text) from public,anon,authenticated;
revoke all on function public.kueper_scheduler_dispatch(text) from public,anon,authenticated;
revoke all on function public.kueper_enable_external_scheduler() from public,anon,authenticated;
revoke all on function public.kueper_disable_external_scheduler() from public,anon,authenticated;
revoke all on function public.kueper_scheduler_health() from public,anon,authenticated;

grant execute on function public.kueper_acquire_scheduler_lease(text,uuid,text,integer,integer) to service_role;
grant execute on function public.kueper_finish_scheduler_run(uuid,uuid,text,bigint,text) to service_role;
grant execute on function public.kueper_scheduler_dispatch(text) to service_role;
grant execute on function public.kueper_enable_external_scheduler() to service_role;
grant execute on function public.kueper_disable_external_scheduler() to service_role;
grant execute on function public.kueper_scheduler_health() to service_role;
