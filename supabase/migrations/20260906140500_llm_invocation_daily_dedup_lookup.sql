create or replace function public.kueper_llm_invocation_reserved_today(
  p_provider text,
  p_source text,
  p_task_id uuid,
  p_reason text
) returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from ecosystem.llm_invocations i
    where i.provider = p_provider
      and i.source = p_source
      and i.task_id = p_task_id
      and i.reason = p_reason
      and i.created_at >= date_trunc('day', now() at time zone 'UTC') at time zone 'UTC'
      and i.created_at < (date_trunc('day', now() at time zone 'UTC') + interval '1 day') at time zone 'UTC'
  );
$$;

revoke all on function public.kueper_llm_invocation_reserved_today(text,text,uuid,text)
  from public, anon, authenticated;
grant execute on function public.kueper_llm_invocation_reserved_today(text,text,uuid,text)
  to service_role;
