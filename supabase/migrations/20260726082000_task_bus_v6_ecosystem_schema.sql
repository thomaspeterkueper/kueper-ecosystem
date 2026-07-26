-- KUEPER Ecosystem V6 — private `ecosystem` state plane with public server-only RPC facade.
-- Apply after the original V6 migrations if they were already applied; if not, this migration
-- safely relocates all V6 tables and rebuilds the RPCs against the private schema.

create schema if not exists ecosystem;

-- Move V6 state tables if they still live in public.
do $$
begin
  if to_regclass('public.tasks') is not null and to_regclass('ecosystem.tasks') is null then
    alter table public.tasks set schema ecosystem;
  end if;
  if to_regclass('public.task_dependencies') is not null and to_regclass('ecosystem.task_dependencies') is null then
    alter table public.task_dependencies set schema ecosystem;
  end if;
  if to_regclass('public.task_runs') is not null and to_regclass('ecosystem.task_runs') is null then
    alter table public.task_runs set schema ecosystem;
  end if;
  if to_regclass('public.task_events') is not null and to_regclass('ecosystem.task_events') is null then
    alter table public.task_events set schema ecosystem;
  end if;
end $$;

-- If V6 was not previously applied, create the private tables directly.
create table if not exists ecosystem.tasks (
  id uuid primary key default gen_random_uuid(),
  external_id text unique,
  type text not null,
  source_project text not null,
  target_project text not null,
  status text not null default 'pending' check (status in ('pending','claimed','running','parked','completed','failed','cancelled')),
  priority text not null default 'medium' check (priority in ('low','medium','high','critical')),
  payload jsonb not null default '{}'::jsonb,
  result jsonb,
  parent_task_id uuid references ecosystem.tasks(id) on delete set null,
  root_task_id uuid references ecosystem.tasks(id) on delete set null,
  depth integer not null default 0 check (depth between 0 and 8),
  available_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  claimed_at timestamptz,
  started_at timestamptz,
  completed_at timestamptz,
  lease_owner text,
  lease_token uuid,
  lease_expires_at timestamptz,
  attempt_count integer not null default 0 check (attempt_count >= 0),
  max_attempts integer not null default 3 check (max_attempts between 1 and 20),
  last_error text,
  blocked_reason text,
  requires_owner_decision boolean not null default false,
  relevance_score numeric(5,4) check (relevance_score between 0 and 1),
  evidence_score numeric(5,4) check (evidence_score between 0 and 1),
  repository text,
  base_sha text,
  branch text,
  pr_url text,
  preferred_provider text,
  preferred_model text,
  agent_provider text,
  agent_model text,
  input_tokens bigint check (input_tokens is null or input_tokens >= 0),
  output_tokens bigint check (output_tokens is null or output_tokens >= 0),
  cost_estimate_eur numeric(12,6) check (cost_estimate_eur is null or cost_estimate_eur >= 0),
  routing_fingerprint text,
  idempotency_key text unique,
  metadata jsonb not null default '{}'::jsonb,
  constraint task_no_self_parent check (parent_task_id is null or parent_task_id <> id),
  constraint task_projects_present check (length(trim(source_project)) > 0 and length(trim(target_project)) > 0),
  constraint task_type_present check (length(trim(type)) > 0),
  constraint task_terminal_consistency check ((status not in ('completed','failed','cancelled')) or completed_at is not null),
  constraint task_lease_consistency check ((status not in ('claimed','running')) or (lease_owner is not null and lease_token is not null and lease_expires_at is not null))
);

create table if not exists ecosystem.task_dependencies (
  task_id uuid not null references ecosystem.tasks(id) on delete cascade,
  depends_on_task_id uuid not null references ecosystem.tasks(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (task_id, depends_on_task_id),
  constraint dependency_not_self check (task_id <> depends_on_task_id)
);

create table if not exists ecosystem.task_runs (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references ecosystem.tasks(id) on delete cascade,
  attempt integer not null check (attempt >= 1),
  worker_id text not null,
  provider text,
  model text,
  status text not null default 'running' check (status in ('running','succeeded','failed','cancelled','lease-expired')),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  input_tokens bigint check (input_tokens is null or input_tokens >= 0),
  output_tokens bigint check (output_tokens is null or output_tokens >= 0),
  cost_estimate_eur numeric(12,6) check (cost_estimate_eur is null or cost_estimate_eur >= 0),
  error text,
  result jsonb,
  metadata jsonb not null default '{}'::jsonb,
  unique (task_id, attempt)
);

create table if not exists ecosystem.task_events (
  id bigint generated always as identity primary key,
  task_id uuid not null references ecosystem.tasks(id) on delete cascade,
  event_type text not null,
  actor text not null,
  from_status text,
  to_status text,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists tasks_runnable_idx on ecosystem.tasks(priority,available_at,created_at) where status='pending';
create index if not exists tasks_lease_idx on ecosystem.tasks(lease_expires_at) where status in ('claimed','running');
create index if not exists tasks_target_status_idx on ecosystem.tasks(target_project,status,priority,created_at);
create index if not exists tasks_parent_idx on ecosystem.tasks(parent_task_id);
create index if not exists tasks_root_idx on ecosystem.tasks(root_task_id);
create index if not exists tasks_fingerprint_idx on ecosystem.tasks(routing_fingerprint) where routing_fingerprint is not null;
create index if not exists task_dependencies_reverse_idx on ecosystem.task_dependencies(depends_on_task_id);
create index if not exists task_runs_task_idx on ecosystem.task_runs(task_id,started_at desc);
create index if not exists task_events_task_idx on ecosystem.task_events(task_id,created_at desc);

create or replace function ecosystem.kueper_touch_updated_at() returns trigger language plpgsql set search_path=ecosystem,pg_temp as $$
begin new.updated_at=now(); return new; end $$;
drop trigger if exists tasks_touch_updated_at on ecosystem.tasks;
create trigger tasks_touch_updated_at before update on ecosystem.tasks for each row execute function ecosystem.kueper_touch_updated_at();

create or replace function ecosystem.kueper_reject_dependency_cycle() returns trigger language plpgsql set search_path=ecosystem,pg_temp as $$
declare cycle_found boolean;
begin
  if new.task_id=new.depends_on_task_id then raise exception 'task cannot depend on itself'; end if;
  with recursive ancestors(id) as (
    select new.depends_on_task_id union
    select d.depends_on_task_id from ecosystem.task_dependencies d join ancestors a on d.task_id=a.id
  ) select exists(select 1 from ancestors where id=new.task_id) into cycle_found;
  if cycle_found then raise exception 'dependency cycle detected for task %',new.task_id; end if;
  return new;
end $$;
drop trigger if exists task_dependencies_no_cycles on ecosystem.task_dependencies;
create trigger task_dependencies_no_cycles before insert or update on ecosystem.task_dependencies for each row execute function ecosystem.kueper_reject_dependency_cycle();

create or replace function ecosystem.kueper_log_task_status_change() returns trigger language plpgsql set search_path=ecosystem,pg_temp as $$
begin
  if tg_op='INSERT' then
    insert into ecosystem.task_events(task_id,event_type,actor,to_status,data) values(new.id,'task.created',coalesce(new.metadata->>'actor','system'),new.status,'{}');
  elsif new.status is distinct from old.status then
    insert into ecosystem.task_events(task_id,event_type,actor,from_status,to_status,data) values(new.id,'task.status.changed',coalesce(new.metadata->>'actor','system'),old.status,new.status,'{}');
  end if;
  return new;
end $$;
drop trigger if exists tasks_log_status on ecosystem.tasks;
create trigger tasks_log_status after insert or update of status on ecosystem.tasks for each row execute function ecosystem.kueper_log_task_status_change();

-- Public RPC facade: PostgREST can call these without exposing the private ecosystem schema.
create or replace function public.kueper_create_task(
  p_type text,p_source_project text,p_target_project text,p_payload jsonb default '{}'::jsonb,p_priority text default 'medium',
  p_parent_task_id uuid default null,p_dependencies uuid[] default '{}'::uuid[],p_idempotency_key text default null,p_external_id text default null,
  p_available_at timestamptz default now(),p_max_attempts integer default 3,p_preferred_provider text default null,p_preferred_model text default null,
  p_repository text default null,p_base_sha text default null,p_relevance_score numeric default null,p_evidence_score numeric default null,p_metadata jsonb default '{}'::jsonb
) returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.tasks; parent ecosystem.tasks; derived_root uuid; derived_depth integer:=0; dep uuid;
begin
  if p_type is null or length(trim(p_type))=0 then raise exception 'task type is required'; end if;
  if p_source_project is null or length(trim(p_source_project))=0 then raise exception 'source project is required'; end if;
  if p_target_project is null or length(trim(p_target_project))=0 then raise exception 'target project is required'; end if;
  if p_priority not in ('low','medium','high','critical') then raise exception 'invalid priority'; end if;
  if p_max_attempts<1 or p_max_attempts>20 then raise exception 'max attempts must be between 1 and 20'; end if;
  if p_idempotency_key is not null then select * into r from ecosystem.tasks where idempotency_key=p_idempotency_key; if r.id is not null then return r; end if; end if;
  if p_parent_task_id is not null then
    select * into parent from ecosystem.tasks where id=p_parent_task_id; if parent.id is null then raise exception 'parent task not found'; end if;
    derived_root:=coalesce(parent.root_task_id,parent.id); derived_depth:=parent.depth+1; if derived_depth>8 then raise exception 'task depth limit exceeded'; end if;
  end if;
  begin
    insert into ecosystem.tasks(external_id,type,source_project,target_project,status,priority,payload,parent_task_id,root_task_id,depth,available_at,max_attempts,preferred_provider,preferred_model,repository,base_sha,relevance_score,evidence_score,idempotency_key,metadata)
    values(p_external_id,trim(p_type),trim(p_source_project),trim(p_target_project),'pending',p_priority,coalesce(p_payload,'{}'),p_parent_task_id,derived_root,derived_depth,coalesce(p_available_at,now()),p_max_attempts,p_preferred_provider,p_preferred_model,p_repository,p_base_sha,p_relevance_score,p_evidence_score,p_idempotency_key,coalesce(p_metadata,'{}')) returning * into r;
  exception when unique_violation then
    if p_idempotency_key is not null then select * into r from ecosystem.tasks where idempotency_key=p_idempotency_key; if r.id is not null then return r; end if; end if; raise;
  end;
  if p_parent_task_id is null then update ecosystem.tasks set root_task_id=r.id where id=r.id returning * into r; end if;
  foreach dep in array coalesce(p_dependencies,'{}'::uuid[]) loop if dep is not null then insert into ecosystem.task_dependencies(task_id,depends_on_task_id) values(r.id,dep) on conflict do nothing; end if; end loop;
  return r;
end $$;

create or replace function public.kueper_claim_task(p_worker_id text,p_lease_seconds integer default 600,p_target_project text default null,p_types text[] default null)
returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare picked ecosystem.tasks; new_token uuid:=gen_random_uuid();
begin
  if p_worker_id is null or length(trim(p_worker_id))=0 then raise exception 'worker id is required'; end if;
  if p_lease_seconds<30 or p_lease_seconds>3600 then raise exception 'lease seconds must be between 30 and 3600'; end if;
  select t.* into picked from ecosystem.tasks t where t.status='pending' and t.available_at<=now() and t.attempt_count<t.max_attempts
    and (p_target_project is null or t.target_project=p_target_project) and (p_types is null or t.type=any(p_types))
    and not exists(select 1 from ecosystem.task_dependencies d join ecosystem.tasks dep on dep.id=d.depends_on_task_id where d.task_id=t.id and dep.status<>'completed')
    order by case t.priority when 'critical' then 0 when 'high' then 1 when 'medium' then 2 else 3 end,t.available_at,t.created_at for update skip locked limit 1;
  if picked.id is null then return null; end if;
  update ecosystem.tasks set status='claimed',claimed_at=now(),lease_owner=p_worker_id,lease_token=new_token,lease_expires_at=now()+make_interval(secs=>p_lease_seconds),attempt_count=attempt_count+1,last_error=null where id=picked.id returning * into picked;
  insert into ecosystem.task_runs(task_id,attempt,worker_id,provider,model,status) values(picked.id,picked.attempt_count,p_worker_id,picked.preferred_provider,picked.preferred_model,'running');
  return picked;
end $$;

create or replace function public.kueper_start_task(p_task_id uuid,p_lease_token uuid) returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.tasks; begin update ecosystem.tasks set status='running',started_at=coalesce(started_at,now()) where id=p_task_id and status='claimed' and lease_token=p_lease_token and lease_expires_at>now() returning * into r; if r.id is null then raise exception 'task lease invalid or expired'; end if; return r; end $$;

create or replace function public.kueper_heartbeat_task(p_task_id uuid,p_lease_token uuid,p_extend_seconds integer default 600) returns timestamptz language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare expiry timestamptz; begin if p_extend_seconds<30 or p_extend_seconds>3600 then raise exception 'invalid lease extension'; end if; update ecosystem.tasks set lease_expires_at=now()+make_interval(secs=>p_extend_seconds) where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token and lease_expires_at>now() returning lease_expires_at into expiry; if expiry is null then raise exception 'task lease invalid or expired'; end if; return expiry; end $$;

create or replace function public.kueper_complete_task(p_task_id uuid,p_lease_token uuid,p_result jsonb default '{}'::jsonb,p_provider text default null,p_model text default null,p_input_tokens bigint default null,p_output_tokens bigint default null,p_cost_estimate_eur numeric default null)
returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.tasks; begin update ecosystem.tasks set status='completed',result=p_result,completed_at=now(),agent_provider=coalesce(p_provider,agent_provider),agent_model=coalesce(p_model,agent_model),input_tokens=p_input_tokens,output_tokens=p_output_tokens,cost_estimate_eur=p_cost_estimate_eur,lease_owner=null,lease_token=null,lease_expires_at=null,blocked_reason=null where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token returning * into r; if r.id is null then raise exception 'task lease invalid'; end if; update ecosystem.task_runs set status='succeeded',finished_at=now(),provider=coalesce(p_provider,provider),model=coalesce(p_model,model),input_tokens=p_input_tokens,output_tokens=p_output_tokens,cost_estimate_eur=p_cost_estimate_eur,result=p_result where task_id=r.id and attempt=r.attempt_count; return r; end $$;

create or replace function public.kueper_fail_task(p_task_id uuid,p_lease_token uuid,p_error text,p_retry_delay_seconds integer default 300)
returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.tasks; terminal boolean; begin select attempt_count>=max_attempts into terminal from ecosystem.tasks where id=p_task_id and lease_token=p_lease_token; if terminal is null then raise exception 'task lease invalid'; end if; update ecosystem.tasks set status=case when terminal then 'failed' else 'pending' end,last_error=p_error,available_at=case when terminal then available_at else now()+make_interval(secs=>greatest(0,p_retry_delay_seconds)) end,completed_at=case when terminal then now() else null end,lease_owner=null,lease_token=null,lease_expires_at=null where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token returning * into r; if r.id is null then raise exception 'task lease invalid'; end if; update ecosystem.task_runs set status='failed',finished_at=now(),error=p_error where task_id=r.id and attempt=r.attempt_count; return r; end $$;

create or replace function public.kueper_park_task(p_task_id uuid,p_lease_token uuid,p_reason text,p_requires_owner_decision boolean default false)
returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.tasks; begin update ecosystem.tasks set status='parked',blocked_reason=p_reason,requires_owner_decision=p_requires_owner_decision,lease_owner=null,lease_token=null,lease_expires_at=null where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token returning * into r; if r.id is null then raise exception 'task lease invalid'; end if; update ecosystem.task_runs set status='succeeded',finished_at=now(),result=jsonb_build_object('parked',true,'reason',p_reason) where task_id=r.id and attempt=r.attempt_count; return r; end $$;

create or replace function public.kueper_requeue_parked_task(p_task_id uuid) returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.tasks; begin update ecosystem.tasks set status='pending',available_at=now(),blocked_reason=null,requires_owner_decision=false where id=p_task_id and status='parked' and requires_owner_decision=false returning * into r; return r; end $$;

create or replace function public.kueper_cancel_task(p_task_id uuid,p_reason text default null) returns ecosystem.tasks language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.tasks; begin update ecosystem.tasks set status='cancelled',completed_at=now(),blocked_reason=coalesce(p_reason,blocked_reason),lease_owner=null,lease_token=null,lease_expires_at=null where id=p_task_id and status not in ('completed','failed','cancelled') returning * into r; return r; end $$;

create or replace function public.kueper_add_dependency(p_task_id uuid,p_depends_on_task_id uuid) returns ecosystem.task_dependencies language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare r ecosystem.task_dependencies; begin if not exists(select 1 from ecosystem.tasks where id=p_task_id) then raise exception 'task not found'; end if; if not exists(select 1 from ecosystem.tasks where id=p_depends_on_task_id) then raise exception 'dependency task not found'; end if; insert into ecosystem.task_dependencies(task_id,depends_on_task_id) values(p_task_id,p_depends_on_task_id) on conflict(task_id,depends_on_task_id) do update set task_id=excluded.task_id returning * into r; return r; end $$;

create or replace function public.kueper_remove_dependency(p_task_id uuid,p_depends_on_task_id uuid) returns boolean language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare n integer; begin delete from ecosystem.task_dependencies where task_id=p_task_id and depends_on_task_id=p_depends_on_task_id; get diagnostics n=row_count; return n>0; end $$;

create or replace function public.kueper_recover_expired_leases() returns integer language plpgsql security definer set search_path=ecosystem,public,pg_temp as $$
declare n integer; begin with expired as (update ecosystem.tasks set status=case when attempt_count>=max_attempts then 'failed' else 'pending' end,last_error=coalesce(last_error,'worker lease expired'),available_at=case when attempt_count>=max_attempts then available_at else now()+interval '60 seconds' end,completed_at=case when attempt_count>=max_attempts then now() else null end,lease_owner=null,lease_token=null,lease_expires_at=null where status in ('claimed','running') and lease_expires_at<now() returning id,attempt_count) update ecosystem.task_runs r set status='lease-expired',finished_at=now(),error=coalesce(error,'worker lease expired') from expired e where r.task_id=e.id and r.attempt=e.attempt_count and r.status='running'; get diagnostics n=row_count; return n; end $$;

-- Security: private state tables are not exposed to browser roles. Backend reads state; all mutation goes through RPCs.
alter table ecosystem.tasks enable row level security;
alter table ecosystem.task_dependencies enable row level security;
alter table ecosystem.task_runs enable row level security;
alter table ecosystem.task_events enable row level security;

revoke all on schema ecosystem from public,anon,authenticated;
grant usage on schema ecosystem to service_role;
revoke all on all tables in schema ecosystem from public,anon,authenticated;
grant select on ecosystem.tasks,ecosystem.task_dependencies,ecosystem.task_runs,ecosystem.task_events to service_role;

revoke all on function public.kueper_create_task(text,text,text,jsonb,text,uuid,uuid[],text,text,timestamptz,integer,text,text,text,text,numeric,numeric,jsonb) from public,anon,authenticated;
revoke all on function public.kueper_claim_task(text,integer,text,text[]) from public,anon,authenticated;
revoke all on function public.kueper_start_task(uuid,uuid) from public,anon,authenticated;
revoke all on function public.kueper_heartbeat_task(uuid,uuid,integer) from public,anon,authenticated;
revoke all on function public.kueper_complete_task(uuid,uuid,jsonb,text,text,bigint,bigint,numeric) from public,anon,authenticated;
revoke all on function public.kueper_fail_task(uuid,uuid,text,integer) from public,anon,authenticated;
revoke all on function public.kueper_park_task(uuid,uuid,text,boolean) from public,anon,authenticated;
revoke all on function public.kueper_requeue_parked_task(uuid) from public,anon,authenticated;
revoke all on function public.kueper_cancel_task(uuid,text) from public,anon,authenticated;
revoke all on function public.kueper_add_dependency(uuid,uuid) from public,anon,authenticated;
revoke all on function public.kueper_remove_dependency(uuid,uuid) from public,anon,authenticated;
revoke all on function public.kueper_recover_expired_leases() from public,anon,authenticated;

grant execute on function public.kueper_create_task(text,text,text,jsonb,text,uuid,uuid[],text,text,timestamptz,integer,text,text,text,text,numeric,numeric,jsonb) to service_role;
grant execute on function public.kueper_claim_task(text,integer,text,text[]) to service_role;
grant execute on function public.kueper_start_task(uuid,uuid) to service_role;
grant execute on function public.kueper_heartbeat_task(uuid,uuid,integer) to service_role;
grant execute on function public.kueper_complete_task(uuid,uuid,jsonb,text,text,bigint,bigint,numeric) to service_role;
grant execute on function public.kueper_fail_task(uuid,uuid,text,integer) to service_role;
grant execute on function public.kueper_park_task(uuid,uuid,text,boolean) to service_role;
grant execute on function public.kueper_requeue_parked_task(uuid) to service_role;
grant execute on function public.kueper_cancel_task(uuid,text) to service_role;
grant execute on function public.kueper_add_dependency(uuid,uuid) to service_role;
grant execute on function public.kueper_remove_dependency(uuid,uuid) to service_role;
grant execute on function public.kueper_recover_expired_leases() to service_role;

comment on schema ecosystem is 'Private operational state plane for KUEPER autonomous work; not a Knowledge Graph namespace.';
comment on table ecosystem.tasks is 'Operational source of truth for autonomous work. GitHub External Tasks remain an audit projection.';
