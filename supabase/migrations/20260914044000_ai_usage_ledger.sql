-- KUEPER AI Usage Ledger
-- Records why an AI call is considered and what actually happened.
-- Budget reservation remains owned by ecosystem.llm_invocations / kueper_claim_task_with_llm_budget.

create table if not exists ecosystem.ai_usage_intents (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  source_system text not null,
  trigger_type text not null,
  reason text not null,
  provider_requested text not null default 'deepseek',
  model_requested text not null,
  status text not null default 'planned' check (status in ('planned','started','completed','failed','skipped','blocked','deduped')),
  skip_reason text,
  repository text,
  pr_number bigint,
  research_id text,
  task_id text,
  dedup_key text not null unique,
  workflow_run_id bigint,
  commit_sha text,
  is_retry boolean not null default false,
  parent_intent_id uuid references ecosystem.ai_usage_intents(id) on delete set null,
  metadata jsonb not null default '{}'::jsonb,
  started_at timestamptz,
  finished_at timestamptz
);

create table if not exists ecosystem.ai_usage_events (
  id uuid primary key default gen_random_uuid(),
  intent_id uuid not null references ecosystem.ai_usage_intents(id) on delete cascade,
  created_at timestamptz not null default now(),
  event_type text not null check (event_type in ('planned','started','completed','failed','skipped','blocked','deduped')),
  provider text,
  model text,
  input_tokens bigint,
  output_tokens bigint,
  cached_input_tokens bigint,
  estimated_cost_usd numeric(14,6),
  actual_cost_usd numeric(14,6),
  provider_request_id text,
  workflow_run_id bigint,
  error_code text,
  error_message text,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists ai_usage_intents_created_at_idx on ecosystem.ai_usage_intents(created_at desc);
create index if not exists ai_usage_intents_source_idx on ecosystem.ai_usage_intents(source_system, created_at desc);
create index if not exists ai_usage_intents_research_idx on ecosystem.ai_usage_intents(research_id) where research_id is not null;
create index if not exists ai_usage_intents_task_idx on ecosystem.ai_usage_intents(task_id) where task_id is not null;
create index if not exists ai_usage_events_intent_idx on ecosystem.ai_usage_events(intent_id, created_at);
create index if not exists ai_usage_events_created_at_idx on ecosystem.ai_usage_events(created_at desc);

aLter table ecosystem.ai_usage_intents enable row level security;
alter table ecosystem.ai_usage_events enable row level security;

create or replace function public.kueper_log_ai_usage_intent(
  p_source_system text,
  p_trigger_type text,
  p_reason text,
  p_provider_requested text,
  p_model_requested text,
  p_dedup_key text,
  p_repository text default null,
  p_pr_number bigint default null,
  p_research_id text default null,
  p_task_id text default null,
  p_workflow_run_id bigint default null,
  p_commit_sha text default null,
  p_is_retry boolean default false,
  p_parent_intent_id uuid default null,
  p_metadata jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  existing ecosystem.ai_usage_intents%rowtype;
  created ecosystem.ai_usage_intents%rowtype;
begin
  if coalesce(trim(p_source_system),'') = '' or coalesce(trim(p_reason),'') = ''
     or coalesce(trim(p_model_requested),'') = '' or coalesce(trim(p_dedup_key),'') = '' then
    raise exception 'source_system, reason, model_requested and dedup_key are required';
  end if;

  select * into existing from ecosystem.ai_usage_intents where dedup_key = p_dedup_key;
  if found then
    return jsonb_build_object('id', existing.id, 'created', false, 'status', existing.status);
  end if;

  insert into ecosystem.ai_usage_intents(
    source_system, trigger_type, reason, provider_requested, model_requested,
    repository, pr_number, research_id, task_id, dedup_key, workflow_run_id,
    commit_sha, is_retry, parent_intent_id, metadata
  ) values (
    p_source_system, coalesce(nullif(trim(p_trigger_type),''),'unknown'), left(p_reason,2000),
    coalesce(nullif(trim(p_provider_requested),''),'deepseek'), p_model_requested,
    p_repository, p_pr_number, p_research_id, p_task_id, p_dedup_key, p_workflow_run_id,
    p_commit_sha, coalesce(p_is_retry,false), p_parent_intent_id, coalesce(p_metadata,'{}'::jsonb)
  ) returning * into created;

  insert into ecosystem.ai_usage_events(intent_id,event_type,provider,model,workflow_run_id,metadata)
  values(created.id,'planned',created.provider_requested,created.model_requested,created.workflow_run_id,'{}'::jsonb);

  return jsonb_build_object('id', created.id, 'created', true, 'status', created.status);
end;
$$;

create or replace function public.kueper_log_ai_usage_event(
  p_intent_id uuid,
  p_event_type text,
  p_provider text default null,
  p_model text default null,
  p_input_tokens bigint default null,
  p_output_tokens bigint default null,
  p_cached_input_tokens bigint default null,
  p_estimated_cost_usd numeric default null,
  p_actual_cost_usd numeric default null,
  p_provider_request_id text default null,
  p_workflow_run_id bigint default null,
  p_error_code text default null,
  p_error_message text default null,
  p_metadata jsonb default '{}'::jsonb
) returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  event_id uuid;
begin
  if p_event_type not in ('planned','started','completed','failed','skipped','blocked','deduped') then
    raise exception 'invalid AI usage event type: %', p_event_type;
  end if;

  insert into ecosystem.ai_usage_events(
    intent_id,event_type,provider,model,input_tokens,output_tokens,cached_input_tokens,
    estimated_cost_usd,actual_cost_usd,provider_request_id,workflow_run_id,error_code,error_message,metadata
  ) values (
    p_intent_id,p_event_type,p_provider,p_model,p_input_tokens,p_output_tokens,p_cached_input_tokens,
    p_estimated_cost_usd,p_actual_cost_usd,p_provider_request_id,p_workflow_run_id,p_error_code,left(p_error_message,4000),coalesce(p_metadata,'{}'::jsonb)
  ) returning id into event_id;

  update ecosystem.ai_usage_intents
  set status = p_event_type,
      updated_at = now(),
      started_at = case when p_event_type = 'started' then coalesce(started_at,now()) else started_at end,
      finished_at = case when p_event_type in ('completed','failed','skipped','blocked') then now() else finished_at end,
      skip_reason = case when p_event_type in ('skipped','blocked') then coalesce(left(p_error_message,1000),skip_reason) else skip_reason end
  where id = p_intent_id;

  return event_id;
end;
$$;

create or replace function public.kueper_ai_usage_dashboard() returns jsonb
language sql
security definer
set search_path = ''
as $$
  with today_intents as (
    select * from ecosystem.ai_usage_intents where created_at >= date_trunc('day',now())
  ),
  today_events as (
    select e.* from ecosystem.ai_usage_events e where e.created_at >= date_trunc('day',now())
  ),
  source_rollup as (
    select i.source_system,
           count(*)::int as planned,
           count(*) filter (where i.status in ('started','completed','failed'))::int as executed,
           count(*) filter (where i.status = 'completed')::int as completed,
           count(*) filter (where i.status = 'failed')::int as failed,
           count(*) filter (where i.status = 'blocked')::int as blocked,
           count(*) filter (where i.status = 'skipped')::int as skipped,
           coalesce((select sum(e.actual_cost_usd) from today_events e where e.intent_id in (select x.id from today_intents x where x.source_system=i.source_system)),0)::numeric as actual_cost_usd,
           coalesce((select sum(e.estimated_cost_usd) from today_events e where e.intent_id in (select x.id from today_intents x where x.source_system=i.source_system)),0)::numeric as estimated_cost_usd
      from today_intents i
     group by i.source_system
  ), latest as (
    select i.id,i.created_at,i.updated_at,i.source_system,i.trigger_type,i.reason,
           i.provider_requested,i.model_requested,i.status,i.skip_reason,i.repository,
           i.pr_number,i.research_id,i.task_id,i.workflow_run_id,i.commit_sha,i.is_retry,
           coalesce((select sum(e.input_tokens) from ecosystem.ai_usage_events e where e.intent_id=i.id),0)::bigint as input_tokens,
           coalesce((select sum(e.output_tokens) from ecosystem.ai_usage_events e where e.intent_id=i.id),0)::bigint as output_tokens,
           coalesce((select sum(e.actual_cost_usd) from ecosystem.ai_usage_events e where e.intent_id=i.id),0)::numeric as actual_cost_usd,
           coalesce((select sum(e.estimated_cost_usd) from ecosystem.ai_usage_events e where e.intent_id=i.id),0)::numeric as estimated_cost_usd
      from ecosystem.ai_usage_intents i
     order by i.created_at desc
     limit 50
  )
  select jsonb_build_object(
    'planned', (select count(*)::int from today_intents),
    'executed', (select count(*)::int from today_intents where status in ('started','completed','failed')),
    'completed', (select count(*)::int from today_intents where status='completed'),
    'failed', (select count(*)::int from today_intents where status='failed'),
    'blocked', (select count(*)::int from today_intents where status='blocked'),
    'skipped', (select count(*)::int from today_intents where status='skipped'),
    'deduped', (select count(*)::int from today_events where event_type='deduped'),
    'input_tokens', coalesce((select sum(input_tokens) from today_events),0),
    'output_tokens', coalesce((select sum(output_tokens) from today_events),0),
    'estimated_cost_usd', coalesce((select sum(estimated_cost_usd) from today_events),0),
    'actual_cost_usd', coalesce((select sum(actual_cost_usd) from today_events),0),
    'by_source', coalesce((select jsonb_agg(to_jsonb(s) order by s.actual_cost_usd desc, s.planned desc) from source_rollup s),'[]'::jsonb),
    'latest', coalesce((select jsonb_agg(to_jsonb(l) order by l.created_at desc) from latest l),'[]'::jsonb)
  );
$$;

revoke all on ecosystem.ai_usage_intents from public, anon, authenticated;
revoke all on ecosystem.ai_usage_events from public, anon, authenticated;
grant select,insert,update on ecosystem.ai_usage_intents to service_role;
grant select,insert on ecosystem.ai_usage_events to service_role;

revoke all on function public.kueper_log_ai_usage_intent(text,text,text,text,text,text,text,bigint,text,text,bigint,text,boolean,uuid,jsonb) from public, anon, authenticated;
revoke all on function public.kueper_log_ai_usage_event(uuid,text,text,text,bigint,bigint,bigint,numeric,numeric,text,bigint,text,text,jsonb) from public, anon, authenticated;
grant execute on function public.kueper_log_ai_usage_intent(text,text,text,text,text,text,text,bigint,text,text,bigint,text,boolean,uuid,jsonb) to service_role;
grant execute on function public.kueper_log_ai_usage_event(uuid,text,text,text,bigint,bigint,bigint,numeric,numeric,text,bigint,text,text,jsonb) to service_role;
-- Bounded aggregate/read projection: no prompts, secrets or provider payloads are exposed.
grant execute on function public.kueper_ai_usage_dashboard() to anon, authenticated, service_role;
