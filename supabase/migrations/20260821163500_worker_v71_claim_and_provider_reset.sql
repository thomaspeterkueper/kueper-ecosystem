-- KUEPER V7.1 — robust task claim serialization and explicit provider recovery.

create or replace function public.kueper_claim_task_v7(
  p_worker_id text,
  p_lease_seconds integer default 600,
  p_target_project text default null,
  p_types text[] default null
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  picked ecosystem.tasks;
  new_token uuid := gen_random_uuid();
begin
  if p_worker_id is null or length(trim(p_worker_id)) = 0 then
    raise exception 'worker id is required';
  end if;
  if p_lease_seconds < 30 or p_lease_seconds > 3600 then
    raise exception 'lease seconds must be between 30 and 3600';
  end if;

  select t.* into picked
  from ecosystem.tasks t
  where t.status = 'pending'
    and t.available_at <= now()
    and t.attempt_count < t.max_attempts
    and (p_target_project is null or t.target_project = p_target_project)
    and (p_types is null or t.type = any(p_types))
    and not exists (
      select 1
      from ecosystem.task_dependencies d
      join ecosystem.tasks dep on dep.id = d.depends_on_task_id
      where d.task_id = t.id and dep.status <> 'completed'
    )
  order by
    case t.priority when 'critical' then 0 when 'high' then 1 when 'medium' then 2 else 3 end,
    t.available_at,
    t.created_at
  for update skip locked
  limit 1;

  if picked.id is null then
    return null;
  end if;

  update ecosystem.tasks
  set status = 'claimed',
      claimed_at = now(),
      lease_owner = p_worker_id,
      lease_token = new_token,
      lease_expires_at = now() + make_interval(secs => p_lease_seconds),
      attempt_count = attempt_count + 1,
      last_error = null
  where id = picked.id
  returning * into picked;

  if picked.lease_token is null then
    raise exception 'claim invariant violated: lease token missing for task %', picked.id;
  end if;

  insert into ecosystem.task_runs(task_id, attempt, worker_id, provider, model, status)
  values(picked.id, picked.attempt_count, p_worker_id, picked.preferred_provider, picked.preferred_model, 'running');

  return to_jsonb(picked);
end;
$$;

create or replace function public.kueper_reset_provider(
  p_provider text,
  p_reason text default 'manual or successful availability probe'
)
returns jsonb
language plpgsql
security definer
set search_path = public, ecosystem, pg_temp
as $$
declare
  r ecosystem.provider_state;
begin
  insert into ecosystem.provider_state(provider, status, pause_reason, paused_until, last_error_code, last_error_message, updated_at)
  values(trim(lower(p_provider)), 'available', null, null, null, null, now())
  on conflict(provider) do update set
    status = 'available',
    pause_reason = null,
    paused_until = null,
    last_error_code = null,
    last_error_message = null,
    updated_at = now()
  returning * into r;

  return jsonb_build_object(
    'provider', r.provider,
    'status', r.status,
    'reason', p_reason,
    'updated_at', r.updated_at
  );
end;
$$;

revoke all on function public.kueper_claim_task_v7(text,integer,text,text[]) from public, anon, authenticated;
revoke all on function public.kueper_reset_provider(text,text) from public, anon, authenticated;
grant execute on function public.kueper_claim_task_v7(text,integer,text,text[]) to service_role;
grant execute on function public.kueper_reset_provider(text,text) to service_role;
