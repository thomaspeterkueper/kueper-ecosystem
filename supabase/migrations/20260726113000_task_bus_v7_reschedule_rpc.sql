-- KUEPER Ecosystem V7 — controlled cost/availability rescheduling.

create or replace function public.kueper_reschedule_task(
  p_task_id uuid,
  p_lease_token uuid,
  p_available_at timestamptz,
  p_reason text default null
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
      available_at=greatest(coalesce(p_available_at, now()), now()),
      blocked_reason=coalesce(p_reason, blocked_reason),
      lease_owner=null,
      lease_token=null,
      lease_expires_at=null
  where id=p_task_id
    and status in ('claimed','running')
    and lease_token=p_lease_token
  returning * into r;
  if r.id is null then raise exception 'task lease invalid'; end if;

  update ecosystem.task_runs
  set status='succeeded',
      finished_at=now(),
      result=jsonb_build_object('rescheduled',true,'available_at',r.available_at,'reason',p_reason)
  where task_id=r.id and attempt=r.attempt_count;

  return r;
end;
$$;

revoke all on function public.kueper_reschedule_task(uuid,uuid,timestamptz,text) from public, anon, authenticated;
grant execute on function public.kueper_reschedule_task(uuid,uuid,timestamptz,text) to service_role;
