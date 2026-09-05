create table if not exists ecosystem.llm_budget_policy (
  provider text primary key,
  enabled boolean not null default true,
  max_daily_calls integer not null check (max_daily_calls > 0),
  max_daily_pro_calls integer not null check (max_daily_pro_calls >= 0 and max_daily_pro_calls <= max_daily_calls),
  updated_at timestamptz not null default now()
);

insert into ecosystem.llm_budget_policy(provider, enabled, max_daily_calls, max_daily_pro_calls)
values ('deepseek', true, 12, 2)
on conflict (provider) do update
set enabled = excluded.enabled,
    max_daily_calls = excluded.max_daily_calls,
    max_daily_pro_calls = excluded.max_daily_pro_calls,
    updated_at = now();

create table if not exists ecosystem.llm_invocations (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  model text not null,
  source text not null,
  task_id uuid null,
  reason text null,
  created_at timestamptz not null default now()
);

create index if not exists llm_invocations_provider_created_idx
  on ecosystem.llm_invocations(provider, created_at desc);

create or replace function public.kueper_reserve_llm_invocation(
  p_provider text,
  p_model text,
  p_source text,
  p_task_id uuid default null,
  p_reason text default null
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_policy ecosystem.llm_budget_policy%rowtype;
  v_calls integer;
  v_pro_calls integer;
  v_is_pro boolean := position('pro' in lower(coalesce(p_model,''))) > 0;
begin
  select * into v_policy
  from ecosystem.llm_budget_policy
  where provider = p_provider;

  if not found or not v_policy.enabled then
    return jsonb_build_object('allowed', false, 'reason', 'provider-budget-disabled');
  end if;

  perform pg_advisory_xact_lock(hashtext('kueper-llm-budget:' || p_provider || ':' || current_date::text));

  select count(*), count(*) filter (where position('pro' in lower(model)) > 0)
    into v_calls, v_pro_calls
  from ecosystem.llm_invocations
  where provider = p_provider
    and created_at >= date_trunc('day', now());

  if v_calls >= v_policy.max_daily_calls then
    return jsonb_build_object('allowed', false, 'reason', 'daily-call-budget-exhausted', 'calls', v_calls, 'max_daily_calls', v_policy.max_daily_calls, 'pro_calls', v_pro_calls, 'max_daily_pro_calls', v_policy.max_daily_pro_calls);
  end if;

  if v_is_pro and v_pro_calls >= v_policy.max_daily_pro_calls then
    return jsonb_build_object('allowed', false, 'reason', 'daily-pro-budget-exhausted', 'calls', v_calls, 'max_daily_calls', v_policy.max_daily_calls, 'pro_calls', v_pro_calls, 'max_daily_pro_calls', v_policy.max_daily_pro_calls);
  end if;

  insert into ecosystem.llm_invocations(provider, model, source, task_id, reason)
  values (p_provider, p_model, p_source, p_task_id, left(p_reason, 500));

  return jsonb_build_object('allowed', true, 'reason', 'reserved', 'calls', v_calls + 1, 'max_daily_calls', v_policy.max_daily_calls, 'pro_calls', v_pro_calls + case when v_is_pro then 1 else 0 end, 'max_daily_pro_calls', v_policy.max_daily_pro_calls);
end;
$$;

revoke all on function public.kueper_reserve_llm_invocation(text,text,text,uuid,text) from public, anon, authenticated;
grant execute on function public.kueper_reserve_llm_invocation(text,text,text,uuid,text) to service_role;
