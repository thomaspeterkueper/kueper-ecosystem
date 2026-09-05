-- KUEPER cost control: route before claim, then atomically reserve LLM budget + claim.

create or replace function public.kueper_peek_runnable_task(
  p_target_project text default null,
  p_types text[] default null
) returns jsonb
language sql
security definer
set search_path = ''
as $$
  select to_jsonb(t)
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
  limit 1;
$$;

create or replace function public.kueper_defer_unclaimed_task(
  p_task_id uuid,
  p_available_at timestamptz,
  p_reason text default null
) returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  update ecosystem.tasks
  set available_at = greatest(coalesce(p_available_at, now()), now()),
      blocked_reason = coalesce(left(p_reason, 500), blocked_reason)
  where id = p_task_id
    and status = 'pending'
    and available_at <= now();
  return found;
end;
$$;

create or replace function public.kueper_claim_task_with_llm_budget(
  p_task_id uuid,
  p_worker_id text,
  p_provider text,
  p_model text,
  p_reason text default null,
  p_lease_seconds integer default 600
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  picked ecosystem.tasks;
  policy ecosystem.llm_budget_policy%rowtype;
  new_token uuid := gen_random_uuid();
  calls_today integer;
  pro_today integer;
  is_pro boolean := position('pro' in lower(coalesce(p_model, ''))) > 0;
begin
  if p_worker_id is null or length(trim(p_worker_id)) = 0 then
    raise exception 'worker id is required';
  end if;
  if p_lease_seconds < 30 or p_lease_seconds > 3600 then
    raise exception 'lease seconds must be between 30 and 3600';
  end if;

  select t.* into picked
  from ecosystem.tasks t
  where t.id = p_task_id
  for update;

  if picked.id is null or picked.status <> 'pending' or picked.available_at > now()
     or picked.attempt_count >= picked.max_attempts
     or exists (
       select 1 from ecosystem.task_dependencies d
       join ecosystem.tasks dep on dep.id = d.depends_on_task_id
       where d.task_id = picked.id and dep.status <> 'completed'
     ) then
    return jsonb_build_object('claimed', false, 'reason', 'task-no-longer-runnable');
  end if;

  select * into policy from ecosystem.llm_budget_policy where provider = p_provider;
  if not found or not policy.enabled then
    return jsonb_build_object('claimed', false, 'reason', 'provider-budget-disabled');
  end if;

  perform pg_advisory_xact_lock(hashtext('kueper-llm-budget:' || p_provider || ':' || current_date::text));
  select count(*), count(*) filter (where position('pro' in lower(model)) > 0)
    into calls_today, pro_today
  from ecosystem.llm_invocations
  where provider = p_provider and created_at >= date_trunc('day', now());

  if calls_today >= policy.max_daily_calls then
    return jsonb_build_object('claimed', false, 'reason', 'daily-call-budget-exhausted',
      'calls', calls_today, 'max_daily_calls', policy.max_daily_calls,
      'pro_calls', pro_today, 'max_daily_pro_calls', policy.max_daily_pro_calls);
  end if;
  if is_pro and pro_today >= policy.max_daily_pro_calls then
    return jsonb_build_object('claimed', false, 'reason', 'daily-pro-budget-exhausted',
      'calls', calls_today, 'max_daily_calls', policy.max_daily_calls,
      'pro_calls', pro_today, 'max_daily_pro_calls', policy.max_daily_pro_calls);
  end if;

  insert into ecosystem.llm_invocations(provider, model, source, task_id, reason)
  values (p_provider, p_model, 'agent-worker-v7', picked.id, left(p_reason, 500));

  update ecosystem.tasks
  set status = 'claimed', claimed_at = now(), lease_owner = p_worker_id,
      lease_token = new_token, lease_expires_at = now() + make_interval(secs => p_lease_seconds),
      attempt_count = attempt_count + 1, last_error = null, blocked_reason = null
  where id = picked.id
  returning * into picked;

  insert into ecosystem.task_runs(task_id, attempt, worker_id, provider, model, status)
  values(picked.id, picked.attempt_count, p_worker_id, p_provider, p_model, 'running');

  return jsonb_build_object(
    'claimed', true,
    'task', to_jsonb(picked),
    'budget', jsonb_build_object('calls', calls_today + 1, 'max_daily_calls', policy.max_daily_calls,
      'pro_calls', pro_today + case when is_pro then 1 else 0 end,
      'max_daily_pro_calls', policy.max_daily_pro_calls)
  );
end;
$$;

create or replace function public.kueper_control_room_operations() returns jsonb
language sql
security definer
set search_path = ''
as $$
  with recent_runs as (
    select id, worker_name, source, status, dispatch_requested_at, started_at,
           finished_at, github_run_id, last_error, created_at,
           row_number() over (partition by worker_name order by created_at desc) as rn,
           max(finished_at) filter (where status = 'succeeded') over (partition by worker_name) as last_success_at,
           max(created_at) filter (where status = 'failed') over (partition by worker_name) as last_failure_at
      from ecosystem.scheduler_runs
     where created_at >= now() - interval '7 days'
  ),
  active_tasks as (
    select status, type, blocked_reason from ecosystem.tasks
     where status in ('pending','review_pending','blocked','failed')
  ),
  budget as (
    select p.provider, p.enabled, p.max_daily_calls, p.max_daily_pro_calls,
           count(i.id)::int as calls,
           count(i.id) filter (where position('pro' in lower(i.model)) > 0)::int as pro_calls
      from ecosystem.llm_budget_policy p
      left join ecosystem.llm_invocations i
        on i.provider = p.provider and i.created_at >= date_trunc('day', now())
     group by p.provider, p.enabled, p.max_daily_calls, p.max_daily_pro_calls
  )
  select jsonb_build_object(
    'workers', coalesce((select jsonb_agg((to_jsonb(r) - 'rn') order by r.created_at desc) from recent_runs r where rn = 1), '[]'::jsonb),
    'queue', coalesce((select jsonb_object_agg(status, cnt) from (select status, count(*)::int as cnt from active_tasks group by status) q), '{}'::jsonb),
    'blocked_tasks', (select count(*)::int from active_tasks where blocked_reason is not null),
    'providers', jsonb_build_object('deepseek', case when public.kueper_provider_available('deepseek') then 'available' else 'paused' end),
    'llm_budget', coalesce((select jsonb_object_agg(provider, jsonb_build_object(
      'enabled', enabled, 'calls', calls, 'max_daily_calls', max_daily_calls,
      'pro_calls', pro_calls, 'max_daily_pro_calls', max_daily_pro_calls,
      'resets_at', date_trunc('day', now()) + interval '1 day')) from budget), '{}'::jsonb)
  );
$$;

revoke all on function public.kueper_peek_runnable_task(text,text[]) from public, anon, authenticated;
revoke all on function public.kueper_defer_unclaimed_task(uuid,timestamptz,text) from public, anon, authenticated;
revoke all on function public.kueper_claim_task_with_llm_budget(uuid,text,text,text,text,integer) from public, anon, authenticated;
grant execute on function public.kueper_peek_runnable_task(text,text[]) to service_role;
grant execute on function public.kueper_defer_unclaimed_task(uuid,timestamptz,text) to service_role;
grant execute on function public.kueper_claim_task_with_llm_budget(uuid,text,text,text,text,integer) to service_role;
-- kueper_control_room_operations remains the deliberately bounded public read projection.
grant execute on function public.kueper_control_room_operations() to anon, authenticated, service_role;
