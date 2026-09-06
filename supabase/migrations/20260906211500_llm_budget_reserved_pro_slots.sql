-- Preserve the configured Pro review capacity when routine Flash reviews exhaust
-- the ordinary daily call budget.
--
-- Policy semantics after this migration:
--   max_daily_calls     = total daily DeepSeek budget
--   max_daily_pro_calls = slots reserved inside that total for Pro reviews
-- Therefore Flash may consume at most (max_daily_calls - max_daily_pro_calls)
-- calls, while Pro may consume the reserved remainder.

update ecosystem.llm_budget_policy
set max_daily_calls = 14,
    max_daily_pro_calls = 2
where provider = 'deepseek'
  and max_daily_calls = 12
  and max_daily_pro_calls = 2;

create or replace function public.kueper_reserve_llm_invocation(
  p_provider text,
  p_model text,
  p_source text,
  p_task_id uuid default null,
  p_reason text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_policy ecosystem.llm_budget_policy%rowtype;
  v_calls integer;
  v_pro_calls integer;
  v_flash_calls integer;
  v_flash_limit integer;
  v_is_pro boolean := position('pro' in lower(coalesce(p_model,''))) > 0;
begin
  select * into v_policy
  from ecosystem.llm_budget_policy
  where provider = p_provider;

  if not found or not v_policy.enabled then
    return jsonb_build_object('allowed', false, 'reason', 'provider-budget-disabled');
  end if;

  perform pg_advisory_xact_lock(hashtext('kueper-llm-budget:' || p_provider || ':' || current_date::text));

  select count(*),
         count(*) filter (where position('pro' in lower(model)) > 0)
    into v_calls, v_pro_calls
  from ecosystem.llm_invocations
  where provider = p_provider
    and created_at >= date_trunc('day', now());

  v_flash_calls := v_calls - v_pro_calls;
  v_flash_limit := greatest(0, v_policy.max_daily_calls - v_policy.max_daily_pro_calls);

  if v_calls >= v_policy.max_daily_calls then
    return jsonb_build_object(
      'allowed', false,
      'reason', 'daily-call-budget-exhausted',
      'calls', v_calls,
      'max_daily_calls', v_policy.max_daily_calls,
      'flash_calls', v_flash_calls,
      'max_daily_flash_calls', v_flash_limit,
      'pro_calls', v_pro_calls,
      'max_daily_pro_calls', v_policy.max_daily_pro_calls
    );
  end if;

  if v_is_pro then
    if v_pro_calls >= v_policy.max_daily_pro_calls then
      return jsonb_build_object(
        'allowed', false,
        'reason', 'daily-pro-budget-exhausted',
        'calls', v_calls,
        'max_daily_calls', v_policy.max_daily_calls,
        'flash_calls', v_flash_calls,
        'max_daily_flash_calls', v_flash_limit,
        'pro_calls', v_pro_calls,
        'max_daily_pro_calls', v_policy.max_daily_pro_calls
      );
    end if;
  elsif v_flash_calls >= v_flash_limit then
    return jsonb_build_object(
      'allowed', false,
      'reason', 'daily-flash-budget-exhausted',
      'calls', v_calls,
      'max_daily_calls', v_policy.max_daily_calls,
      'flash_calls', v_flash_calls,
      'max_daily_flash_calls', v_flash_limit,
      'pro_calls', v_pro_calls,
      'max_daily_pro_calls', v_policy.max_daily_pro_calls
    );
  end if;

  insert into ecosystem.llm_invocations(provider, model, source, task_id, reason)
  values (p_provider, p_model, p_source, p_task_id, left(p_reason, 500));

  return jsonb_build_object(
    'allowed', true,
    'reason', 'reserved',
    'calls', v_calls + 1,
    'max_daily_calls', v_policy.max_daily_calls,
    'flash_calls', v_flash_calls + case when v_is_pro then 0 else 1 end,
    'max_daily_flash_calls', v_flash_limit,
    'pro_calls', v_pro_calls + case when v_is_pro then 1 else 0 end,
    'max_daily_pro_calls', v_policy.max_daily_pro_calls
  );
end;
$$;

revoke all on function public.kueper_reserve_llm_invocation(text,text,text,uuid,text) from public;
grant execute on function public.kueper_reserve_llm_invocation(text,text,text,uuid,text) to service_role;
