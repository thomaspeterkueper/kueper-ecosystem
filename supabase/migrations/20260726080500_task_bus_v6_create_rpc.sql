-- KUEPER Ecosystem V6 — controlled task creation and cancellation RPCs.

create or replace function public.kueper_create_task(
  p_type text,
  p_source_project text,
  p_target_project text,
  p_payload jsonb default '{}'::jsonb,
  p_priority text default 'medium',
  p_parent_task_id uuid default null,
  p_dependencies uuid[] default '{}'::uuid[],
  p_idempotency_key text default null,
  p_external_id text default null,
  p_available_at timestamptz default now(),
  p_max_attempts integer default 3,
  p_preferred_provider text default null,
  p_preferred_model text default null,
  p_repository text default null,
  p_base_sha text default null,
  p_relevance_score numeric default null,
  p_evidence_score numeric default null,
  p_metadata jsonb default '{}'::jsonb
)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare
  r public.tasks;
  parent public.tasks;
  derived_root uuid;
  derived_depth integer := 0;
  dep uuid;
begin
  if p_type is null or length(trim(p_type)) = 0 then raise exception 'task type is required'; end if;
  if p_source_project is null or length(trim(p_source_project)) = 0 then raise exception 'source project is required'; end if;
  if p_target_project is null or length(trim(p_target_project)) = 0 then raise exception 'target project is required'; end if;
  if p_priority not in ('low','medium','high','critical') then raise exception 'invalid priority'; end if;
  if p_max_attempts < 1 or p_max_attempts > 20 then raise exception 'max attempts must be between 1 and 20'; end if;

  if p_idempotency_key is not null then
    select * into r from public.tasks where idempotency_key = p_idempotency_key;
    if r.id is not null then return r; end if;
  end if;

  if p_parent_task_id is not null then
    select * into parent from public.tasks where id = p_parent_task_id;
    if parent.id is null then raise exception 'parent task not found'; end if;
    derived_root := coalesce(parent.root_task_id, parent.id);
    derived_depth := parent.depth + 1;
    if derived_depth > 8 then raise exception 'task depth limit exceeded'; end if;
  end if;

  begin
    insert into public.tasks(
      external_id,type,source_project,target_project,status,priority,payload,
      parent_task_id,root_task_id,depth,available_at,max_attempts,
      preferred_provider,preferred_model,repository,base_sha,
      relevance_score,evidence_score,idempotency_key,metadata
    ) values (
      p_external_id,trim(p_type),trim(p_source_project),trim(p_target_project),'pending',p_priority,coalesce(p_payload,'{}'::jsonb),
      p_parent_task_id,derived_root,derived_depth,coalesce(p_available_at,now()),p_max_attempts,
      p_preferred_provider,p_preferred_model,p_repository,p_base_sha,
      p_relevance_score,p_evidence_score,p_idempotency_key,coalesce(p_metadata,'{}'::jsonb)
    ) returning * into r;
  exception when unique_violation then
    if p_idempotency_key is not null then
      select * into r from public.tasks where idempotency_key = p_idempotency_key;
      if r.id is not null then return r; end if;
    end if;
    raise;
  end;

  if p_parent_task_id is null then
    update public.tasks set root_task_id = r.id where id = r.id returning * into r;
  end if;

  if p_dependencies is not null then
    foreach dep in array p_dependencies loop
      if dep is not null then
        insert into public.task_dependencies(task_id,depends_on_task_id)
        values(r.id,dep)
        on conflict do nothing;
      end if;
    end loop;
  end if;

  return r;
end;
$$;

create or replace function public.kueper_cancel_task(
  p_task_id uuid,
  p_reason text default null
)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare r public.tasks;
begin
  update public.tasks
  set status='cancelled',
      completed_at=now(),
      blocked_reason=coalesce(p_reason,blocked_reason),
      lease_owner=null,lease_token=null,lease_expires_at=null
  where id=p_task_id and status not in ('completed','failed','cancelled')
  returning * into r;
  return r;
end;
$$;

revoke all on function public.kueper_create_task(text,text,text,jsonb,text,uuid,uuid[],text,text,timestamptz,integer,text,text,text,text,numeric,numeric,jsonb) from public, anon, authenticated;
revoke all on function public.kueper_cancel_task(uuid,text) from public, anon, authenticated;

comment on function public.kueper_create_task is 'Creates an idempotent KUEPER task and derives root/depth from its parent. Server-side only.';
comment on function public.kueper_cancel_task is 'Cancels a non-terminal KUEPER task. Server-side only.';
