-- KUEPER Ecosystem V6 — Supabase Task Bus
-- Operational task state lives here; GitHub remains an auditable projection, not the queue.

create extension if not exists pgcrypto;

create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  external_id text unique,
  type text not null,
  source_project text not null,
  target_project text not null,
  status text not null default 'pending'
    check (status in ('pending','claimed','running','parked','completed','failed','cancelled')),
  priority text not null default 'medium'
    check (priority in ('low','medium','high','critical')),

  payload jsonb not null default '{}'::jsonb,
  result jsonb,

  parent_task_id uuid references public.tasks(id) on delete set null,
  root_task_id uuid references public.tasks(id) on delete set null,
  depth integer not null default 0 check (depth >= 0 and depth <= 8),

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
  max_attempts integer not null default 3 check (max_attempts >= 1 and max_attempts <= 20),
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
  constraint task_terminal_consistency check (
    (status not in ('completed','failed','cancelled'))
    or completed_at is not null
  ),
  constraint task_lease_consistency check (
    (status not in ('claimed','running'))
    or (lease_owner is not null and lease_token is not null and lease_expires_at is not null)
  )
);

create table if not exists public.task_dependencies (
  task_id uuid not null references public.tasks(id) on delete cascade,
  depends_on_task_id uuid not null references public.tasks(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (task_id, depends_on_task_id),
  constraint dependency_not_self check (task_id <> depends_on_task_id)
);

create table if not exists public.task_runs (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.tasks(id) on delete cascade,
  attempt integer not null check (attempt >= 1),
  worker_id text not null,
  provider text,
  model text,
  status text not null default 'running'
    check (status in ('running','succeeded','failed','cancelled','lease-expired')),
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

create table if not exists public.task_events (
  id bigint generated always as identity primary key,
  task_id uuid not null references public.tasks(id) on delete cascade,
  event_type text not null,
  actor text not null,
  from_status text,
  to_status text,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists tasks_runnable_idx
  on public.tasks (priority, available_at, created_at)
  where status = 'pending';
create index if not exists tasks_lease_idx
  on public.tasks (lease_expires_at)
  where status in ('claimed','running');
create index if not exists tasks_target_status_idx
  on public.tasks (target_project, status, priority, created_at);
create index if not exists tasks_parent_idx on public.tasks (parent_task_id);
create index if not exists tasks_root_idx on public.tasks (root_task_id);
create index if not exists tasks_fingerprint_idx on public.tasks (routing_fingerprint) where routing_fingerprint is not null;
create index if not exists task_dependencies_reverse_idx on public.task_dependencies (depends_on_task_id);
create index if not exists task_runs_task_idx on public.task_runs (task_id, started_at desc);
create index if not exists task_events_task_idx on public.task_events (task_id, created_at desc);

create or replace function public.kueper_touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists tasks_touch_updated_at on public.tasks;
create trigger tasks_touch_updated_at
before update on public.tasks
for each row execute function public.kueper_touch_updated_at();

create or replace function public.kueper_reject_dependency_cycle()
returns trigger
language plpgsql
as $$
declare
  cycle_found boolean;
begin
  if new.task_id = new.depends_on_task_id then
    raise exception 'task cannot depend on itself';
  end if;

  with recursive ancestors(id) as (
    select new.depends_on_task_id
    union
    select d.depends_on_task_id
      from public.task_dependencies d
      join ancestors a on d.task_id = a.id
  )
  select exists(select 1 from ancestors where id = new.task_id) into cycle_found;

  if cycle_found then
    raise exception 'dependency cycle detected for task %', new.task_id;
  end if;
  return new;
end;
$$;

drop trigger if exists task_dependencies_no_cycles on public.task_dependencies;
create trigger task_dependencies_no_cycles
before insert or update on public.task_dependencies
for each row execute function public.kueper_reject_dependency_cycle();

create or replace function public.kueper_log_task_status_change()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'INSERT' then
    insert into public.task_events(task_id,event_type,actor,to_status,data)
    values(new.id,'task.created',coalesce(new.metadata->>'actor','system'),new.status,'{}'::jsonb);
  elsif new.status is distinct from old.status then
    insert into public.task_events(task_id,event_type,actor,from_status,to_status,data)
    values(new.id,'task.status.changed',coalesce(new.metadata->>'actor','system'),old.status,new.status,'{}'::jsonb);
  end if;
  return new;
end;
$$;

drop trigger if exists tasks_log_status on public.tasks;
create trigger tasks_log_status
after insert or update of status on public.tasks
for each row execute function public.kueper_log_task_status_change();

create or replace function public.kueper_claim_task(
  p_worker_id text,
  p_lease_seconds integer default 600,
  p_target_project text default null,
  p_types text[] default null
)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare
  picked public.tasks;
  new_token uuid := gen_random_uuid();
begin
  if p_worker_id is null or length(trim(p_worker_id)) = 0 then
    raise exception 'worker id is required';
  end if;
  if p_lease_seconds < 30 or p_lease_seconds > 3600 then
    raise exception 'lease seconds must be between 30 and 3600';
  end if;

  select t.* into picked
  from public.tasks t
  where t.status = 'pending'
    and t.available_at <= now()
    and t.attempt_count < t.max_attempts
    and (p_target_project is null or t.target_project = p_target_project)
    and (p_types is null or t.type = any(p_types))
    and not exists (
      select 1
      from public.task_dependencies d
      join public.tasks dep on dep.id = d.depends_on_task_id
      where d.task_id = t.id
        and dep.status <> 'completed'
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

  update public.tasks
  set status = 'claimed',
      claimed_at = now(),
      lease_owner = p_worker_id,
      lease_token = new_token,
      lease_expires_at = now() + make_interval(secs => p_lease_seconds),
      attempt_count = attempt_count + 1,
      last_error = null
  where id = picked.id
  returning * into picked;

  insert into public.task_runs(task_id,attempt,worker_id,provider,model,status)
  values(picked.id,picked.attempt_count,p_worker_id,picked.preferred_provider,picked.preferred_model,'running');

  return picked;
end;
$$;

create or replace function public.kueper_start_task(p_task_id uuid, p_lease_token uuid)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare r public.tasks;
begin
  update public.tasks
  set status='running', started_at=coalesce(started_at,now())
  where id=p_task_id and status='claimed' and lease_token=p_lease_token and lease_expires_at>now()
  returning * into r;
  if r.id is null then raise exception 'task lease invalid or expired'; end if;
  return r;
end;
$$;

create or replace function public.kueper_heartbeat_task(p_task_id uuid, p_lease_token uuid, p_extend_seconds integer default 600)
returns timestamptz
language plpgsql
security definer
set search_path = public
as $$
declare expiry timestamptz;
begin
  if p_extend_seconds < 30 or p_extend_seconds > 3600 then raise exception 'invalid lease extension'; end if;
  update public.tasks
  set lease_expires_at=now()+make_interval(secs=>p_extend_seconds)
  where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token and lease_expires_at>now()
  returning lease_expires_at into expiry;
  if expiry is null then raise exception 'task lease invalid or expired'; end if;
  return expiry;
end;
$$;

create or replace function public.kueper_complete_task(
  p_task_id uuid,
  p_lease_token uuid,
  p_result jsonb default '{}'::jsonb,
  p_provider text default null,
  p_model text default null,
  p_input_tokens bigint default null,
  p_output_tokens bigint default null,
  p_cost_estimate_eur numeric default null
)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare r public.tasks;
begin
  update public.tasks
  set status='completed', result=p_result, completed_at=now(),
      agent_provider=coalesce(p_provider,agent_provider), agent_model=coalesce(p_model,agent_model),
      input_tokens=p_input_tokens, output_tokens=p_output_tokens, cost_estimate_eur=p_cost_estimate_eur,
      lease_owner=null, lease_token=null, lease_expires_at=null, blocked_reason=null
  where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token
  returning * into r;
  if r.id is null then raise exception 'task lease invalid'; end if;

  update public.task_runs set status='succeeded',finished_at=now(),provider=coalesce(p_provider,provider),model=coalesce(p_model,model),
    input_tokens=p_input_tokens,output_tokens=p_output_tokens,cost_estimate_eur=p_cost_estimate_eur,result=p_result
  where task_id=r.id and attempt=r.attempt_count;
  return r;
end;
$$;

create or replace function public.kueper_fail_task(
  p_task_id uuid,
  p_lease_token uuid,
  p_error text,
  p_retry_delay_seconds integer default 300
)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare r public.tasks; terminal boolean;
begin
  select attempt_count >= max_attempts into terminal from public.tasks where id=p_task_id and lease_token=p_lease_token;
  if terminal is null then raise exception 'task lease invalid'; end if;

  update public.tasks
  set status=case when terminal then 'failed' else 'pending' end,
      last_error=p_error,
      available_at=case when terminal then available_at else now()+make_interval(secs=>greatest(0,p_retry_delay_seconds)) end,
      completed_at=case when terminal then now() else null end,
      lease_owner=null,lease_token=null,lease_expires_at=null
  where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token
  returning * into r;
  if r.id is null then raise exception 'task lease invalid'; end if;

  update public.task_runs set status='failed',finished_at=now(),error=p_error where task_id=r.id and attempt=r.attempt_count;
  return r;
end;
$$;

create or replace function public.kueper_park_task(
  p_task_id uuid,
  p_lease_token uuid,
  p_reason text,
  p_requires_owner_decision boolean default false
)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare r public.tasks;
begin
  update public.tasks
  set status='parked',blocked_reason=p_reason,requires_owner_decision=p_requires_owner_decision,
      lease_owner=null,lease_token=null,lease_expires_at=null
  where id=p_task_id and status in ('claimed','running') and lease_token=p_lease_token
  returning * into r;
  if r.id is null then raise exception 'task lease invalid'; end if;
  update public.task_runs set status='succeeded',finished_at=now(),result=jsonb_build_object('parked',true,'reason',p_reason)
  where task_id=r.id and attempt=r.attempt_count;
  return r;
end;
$$;

create or replace function public.kueper_requeue_parked_task(p_task_id uuid)
returns public.tasks
language plpgsql
security definer
set search_path = public
as $$
declare r public.tasks;
begin
  update public.tasks
  set status='pending',available_at=now(),blocked_reason=null,requires_owner_decision=false
  where id=p_task_id and status='parked' and requires_owner_decision=false
  returning * into r;
  return r;
end;
$$;

create or replace function public.kueper_recover_expired_leases()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare n integer;
begin
  with expired as (
    update public.tasks
    set status=case when attempt_count>=max_attempts then 'failed' else 'pending' end,
        last_error=coalesce(last_error,'worker lease expired'),
        available_at=case when attempt_count>=max_attempts then available_at else now()+interval '60 seconds' end,
        completed_at=case when attempt_count>=max_attempts then now() else null end,
        lease_owner=null,lease_token=null,lease_expires_at=null
    where status in ('claimed','running') and lease_expires_at < now()
    returning id,attempt_count
  )
  update public.task_runs r
  set status='lease-expired',finished_at=now(),error=coalesce(error,'worker lease expired')
  from expired e
  where r.task_id=e.id and r.attempt=e.attempt_count and r.status='running';
  get diagnostics n = row_count;
  return n;
end;
$$;

-- State-changing RPCs are server-side only. Service role bypasses RLS in Supabase.
revoke all on function public.kueper_claim_task(text,integer,text,text[]) from public, anon, authenticated;
revoke all on function public.kueper_start_task(uuid,uuid) from public, anon, authenticated;
revoke all on function public.kueper_heartbeat_task(uuid,uuid,integer) from public, anon, authenticated;
revoke all on function public.kueper_complete_task(uuid,uuid,jsonb,text,text,bigint,bigint,numeric) from public, anon, authenticated;
revoke all on function public.kueper_fail_task(uuid,uuid,text,integer) from public, anon, authenticated;
revoke all on function public.kueper_park_task(uuid,uuid,text,boolean) from public, anon, authenticated;
revoke all on function public.kueper_requeue_parked_task(uuid) from public, anon, authenticated;
revoke all on function public.kueper_recover_expired_leases() from public, anon, authenticated;

alter table public.tasks enable row level security;
alter table public.task_dependencies enable row level security;
alter table public.task_runs enable row level security;
alter table public.task_events enable row level security;

comment on table public.tasks is 'Operational source of truth for KUEPER autonomous work. GitHub External Tasks are an audit projection.';
comment on table public.task_dependencies is 'DAG edges between tasks. A task is runnable only when all dependencies are completed.';
comment on table public.task_runs is 'One row per worker attempt, including model/cost telemetry.';
comment on table public.task_events is 'Append-only task lifecycle audit events.';
