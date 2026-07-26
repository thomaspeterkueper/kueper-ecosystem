-- KUEPER V7 — provider circuit breaker / availability state.

create table if not exists ecosystem.provider_state (
  provider text primary key,
  status text not null default 'available' check (status in ('available','degraded','paused')),
  pause_reason text,
  paused_until timestamptz,
  last_error_code text,
  last_error_message text,
  updated_at timestamptz not null default now()
);

create or replace function public.kueper_pause_provider(
  p_provider text,
  p_reason text,
  p_error_code text default null,
  p_error_message text default null,
  p_pause_seconds integer default 21600
)
returns ecosystem.provider_state
language plpgsql
security definer
set search_path = public, ecosystem
as $$
declare r ecosystem.provider_state;
begin
  insert into ecosystem.provider_state(provider,status,pause_reason,paused_until,last_error_code,last_error_message,updated_at)
  values(trim(lower(p_provider)),'paused',p_reason,now()+make_interval(secs=>greatest(p_pause_seconds,60)),p_error_code,p_error_message,now())
  on conflict(provider) do update set
    status='paused',
    pause_reason=excluded.pause_reason,
    paused_until=excluded.paused_until,
    last_error_code=excluded.last_error_code,
    last_error_message=excluded.last_error_message,
    updated_at=now()
  returning * into r;
  return r;
end;
$$;

create or replace function public.kueper_provider_available(p_provider text)
returns boolean
language plpgsql
security definer
set search_path = public, ecosystem
as $$
declare r ecosystem.provider_state;
begin
  select * into r from ecosystem.provider_state where provider=trim(lower(p_provider));
  if r.provider is null then return true; end if;
  if r.status <> 'paused' then return true; end if;
  if r.paused_until is not null and r.paused_until <= now() then
    update ecosystem.provider_state
      set status='available', pause_reason=null, paused_until=null, updated_at=now()
      where provider=r.provider;
    return true;
  end if;
  return false;
end;
$$;

create or replace function public.kueper_reschedule_provider_task(
  p_task_id uuid,
  p_lease_token uuid,
  p_provider text,
  p_reason text,
  p_available_at timestamptz
)
returns ecosystem.tasks
language plpgsql
security definer
set search_path = public, ecosystem
as $$
declare r ecosystem.tasks;
begin
  update ecosystem.tasks
  set status='pending',
      available_at=greatest(p_available_at, now()),
      blocked_reason=p_reason,
      lease_owner=null,
      lease_token=null,
      lease_expires_at=null,
      attempt_count=greatest(attempt_count-1,0),
      last_error=null
  where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token
  returning * into r;
  if r.id is null then raise exception 'task lease invalid'; end if;

  delete from ecosystem.task_runs where task_id=r.id and attempt=r.attempt_count+1 and status='running';
  insert into ecosystem.task_events(task_id,event_type,actor,from_status,to_status,data)
  values(r.id,'task.provider.paused','worker','running','pending',jsonb_build_object('provider',p_provider,'reason',p_reason,'available_at',r.available_at));
  return r;
end;
$$;

revoke all on table ecosystem.provider_state from public, anon, authenticated;
grant select,insert,update on ecosystem.provider_state to service_role;
revoke all on function public.kueper_pause_provider(text,text,text,text,integer) from public, anon, authenticated;
revoke all on function public.kueper_provider_available(text) from public, anon, authenticated;
revoke all on function public.kueper_reschedule_provider_task(uuid,uuid,text,text,timestamptz) from public, anon, authenticated;
grant execute on function public.kueper_pause_provider(text,text,text,text,integer) to service_role;
grant execute on function public.kueper_provider_available(text) to service_role;
grant execute on function public.kueper_reschedule_provider_task(uuid,uuid,text,text,timestamptz) to service_role;
