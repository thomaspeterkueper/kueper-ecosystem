-- KUEPER Ecosystem V6 — harden direct table access and add controlled dependency mutation.

create or replace function public.kueper_add_dependency(
  p_task_id uuid,
  p_depends_on_task_id uuid
)
returns public.task_dependencies
language plpgsql
security definer
set search_path = public
as $$
declare r public.task_dependencies;
begin
  if not exists(select 1 from public.tasks where id=p_task_id) then raise exception 'task not found'; end if;
  if not exists(select 1 from public.tasks where id=p_depends_on_task_id) then raise exception 'dependency task not found'; end if;

  insert into public.task_dependencies(task_id,depends_on_task_id)
  values(p_task_id,p_depends_on_task_id)
  on conflict (task_id,depends_on_task_id) do update set task_id=excluded.task_id
  returning * into r;
  return r;
end;
$$;

create or replace function public.kueper_remove_dependency(
  p_task_id uuid,
  p_depends_on_task_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare n integer;
begin
  delete from public.task_dependencies
  where task_id=p_task_id and depends_on_task_id=p_depends_on_task_id;
  get diagnostics n = row_count;
  return n > 0;
end;
$$;

revoke all on function public.kueper_add_dependency(uuid,uuid) from public, anon, authenticated;
revoke all on function public.kueper_remove_dependency(uuid,uuid) from public, anon, authenticated;
grant execute on function public.kueper_add_dependency(uuid,uuid) to service_role;
grant execute on function public.kueper_remove_dependency(uuid,uuid) to service_role;

-- No browser/client role may access the operational bus directly.
revoke all on table public.tasks from anon, authenticated;
revoke all on table public.task_dependencies from anon, authenticated;
revoke all on table public.task_runs from anon, authenticated;
revoke all on table public.task_events from anon, authenticated;

-- Trusted backend callers may inspect state, but mutation must go through the RPC state machine.
revoke insert, update, delete on table public.tasks from service_role;
revoke insert, update, delete on table public.task_dependencies from service_role;
revoke insert, update, delete on table public.task_runs from service_role;
revoke insert, update, delete on table public.task_events from service_role;
grant select on table public.tasks to service_role;
grant select on table public.task_dependencies to service_role;
grant select on table public.task_runs to service_role;
grant select on table public.task_events to service_role;

comment on function public.kueper_add_dependency is 'Adds a dependency through the cycle-protected state machine.';
comment on function public.kueper_remove_dependency is 'Removes a dependency through the server-only state machine.';
