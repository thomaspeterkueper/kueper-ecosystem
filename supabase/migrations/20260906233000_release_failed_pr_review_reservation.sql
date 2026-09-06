-- Release a PR-review LLM budget reservation only when it did not produce a review run.
-- This prevents ProviderUnavailable failures from permanently consuming the task/head retry slot.

create or replace function public.kueper_release_llm_invocation(
  p_provider text,
  p_source text,
  p_task_id uuid,
  p_reason text
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_invocation_id uuid;
  v_created_at timestamptz;
begin
  select i.id, i.created_at
    into v_invocation_id, v_created_at
  from ecosystem.llm_invocations i
  where i.provider = p_provider
    and i.source = p_source
    and i.task_id = p_task_id
    and i.reason = left(p_reason, 500)
    and i.created_at >= date_trunc('day', now())
  order by i.created_at desc
  limit 1;

  if v_invocation_id is null then
    return false;
  end if;

  if exists (
    select 1
    from ecosystem.pr_review_runs rr
    where rr.task_id = p_task_id
      and rr.created_at >= v_created_at
  ) then
    return false;
  end if;

  delete from ecosystem.llm_invocations
  where id = v_invocation_id;

  return found;
end;
$function$;

revoke all on function public.kueper_release_llm_invocation(text,text,uuid,text) from public;
grant execute on function public.kueper_release_llm_invocation(text,text,uuid,text) to service_role;
