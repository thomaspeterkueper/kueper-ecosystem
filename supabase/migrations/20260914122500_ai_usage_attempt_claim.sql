-- KUEPER AI usage attempt semantics
-- Separates semantic work identity from execution attempts and makes provider
-- execution a database-claimed decision rather than a best-effort client check.

alter table ecosystem.ai_usage_intents
  add column if not exists semantic_key text,
  add column if not exists attempt_no integer,
  add column if not exists retry_of_intent_id uuid references ecosystem.ai_usage_intents(id) on delete set null,
  add column if not exists retry_reason text,
  add column if not exists retry_mode text,
  add column if not exists failure_class text;

update ecosystem.ai_usage_intents
   set semantic_key = coalesce(semantic_key, dedup_key),
       attempt_no = coalesce(attempt_no, 1),
       retry_mode = coalesce(retry_mode, 'none')
 where semantic_key is null or attempt_no is null or retry_mode is null;

alter table ecosystem.ai_usage_intents
  alter column semantic_key set not null,
  alter column attempt_no set not null,
  alter column retry_mode set default 'none',
  alter column retry_mode set not null;

do $$
begin
  if not exists (
    select 1 from pg_constraint
     where conname = 'ai_usage_intents_retry_mode_check'
       and conrelid = 'ecosystem.ai_usage_intents'::regclass
  ) then
    alter table ecosystem.ai_usage_intents
      add constraint ai_usage_intents_retry_mode_check
      check (retry_mode in ('none','automatic','manual'));
  end if;
end
$$;

create unique index if not exists ai_usage_intents_semantic_attempt_uidx
  on ecosystem.ai_usage_intents(semantic_key, attempt_no);
create index if not exists ai_usage_intents_semantic_idx
  on ecosystem.ai_usage_intents(semantic_key, attempt_no desc);

create or replace function public.kueper_claim_ai_usage_attempt(
  p_source_system text,
  p_trigger_type text,
  p_reason text,
  p_provider_requested text,
  p_model_requested text,
  p_semantic_key text,
  p_repository text default null,
  p_pr_number bigint default null,
  p_research_id text default null,
  p_task_id text default null,
  p_workflow_run_id bigint default null,
  p_commit_sha text default null,
  p_retry_mode text default 'none',
  p_retry_reason text default null,
  p_metadata jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  latest ecosystem.ai_usage_intents%rowtype;
  created ecosystem.ai_usage_intents%rowtype;
  next_attempt integer;
  transient_failure boolean := false;
  allow_retry boolean := false;
  decision text;
begin
  if coalesce(trim(p_source_system),'') = ''
     or coalesce(trim(p_reason),'') = ''
     or coalesce(trim(p_model_requested),'') = ''
     or coalesce(trim(p_semantic_key),'') = '' then
    raise exception 'source_system, reason, model_requested and semantic_key are required';
  end if;

  if coalesce(p_retry_mode,'none') not in ('none','automatic','manual') then
    raise exception 'invalid retry mode: %', p_retry_mode;
  end if;

  if p_retry_mode = 'manual' and coalesce(trim(p_retry_reason),'') = '' then
    raise exception 'manual retry requires retry_reason';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('kueper_ai_usage:' || p_semantic_key, 0));

  select * into latest
    from ecosystem.ai_usage_intents
   where semantic_key = p_semantic_key
   order by attempt_no desc
   limit 1;

  if not found then
    insert into ecosystem.ai_usage_intents(
      source_system, trigger_type, reason, provider_requested, model_requested,
      repository, pr_number, research_id, task_id, dedup_key, workflow_run_id,
      commit_sha, is_retry, parent_intent_id, metadata,
      semantic_key, attempt_no, retry_mode, retry_reason
    ) values (
      p_source_system, coalesce(nullif(trim(p_trigger_type),''),'unknown'), left(p_reason,2000),
      coalesce(nullif(trim(p_provider_requested),''),'deepseek'), p_model_requested,
      p_repository, p_pr_number, p_research_id, p_task_id,
      p_semantic_key || ':attempt:1', p_workflow_run_id,
      p_commit_sha, false, null, coalesce(p_metadata,'{}'::jsonb),
      p_semantic_key, 1, 'none', null
    ) returning * into created;

    insert into ecosystem.ai_usage_events(intent_id,event_type,provider,model,workflow_run_id,metadata)
    values(created.id,'planned',created.provider_requested,created.model_requested,created.workflow_run_id,
           jsonb_build_object('decision','new-semantic-work'));

    return jsonb_build_object(
      'id', created.id,
      'execute_allowed', true,
      'decision', 'new-semantic-work',
      'attempt_no', 1,
      'semantic_key', p_semantic_key
    );
  end if;

  if latest.status = 'completed' then
    insert into ecosystem.ai_usage_events(intent_id,event_type,provider,model,workflow_run_id,metadata)
    values(latest.id,'deduped',latest.provider_requested,latest.model_requested,p_workflow_run_id,
           jsonb_build_object('decision','already-completed'));
    return jsonb_build_object('id',latest.id,'execute_allowed',false,'decision','already-completed',
                              'attempt_no',latest.attempt_no,'semantic_key',p_semantic_key);
  end if;

  if latest.status in ('planned','started') then
    insert into ecosystem.ai_usage_events(intent_id,event_type,provider,model,workflow_run_id,metadata)
    values(latest.id,'deduped',latest.provider_requested,latest.model_requested,p_workflow_run_id,
           jsonb_build_object('decision','attempt-in-progress'));
    return jsonb_build_object('id',latest.id,'execute_allowed',false,'decision','attempt-in-progress',
                              'attempt_no',latest.attempt_no,'semantic_key',p_semantic_key);
  end if;

  -- A pre-provider block/skip did not consume an execution attempt. Reclaim the
  -- same attempt and let the caller re-evaluate provider/budget conditions.
  if latest.status in ('blocked','skipped','deduped') then
    update ecosystem.ai_usage_intents
       set status='planned', updated_at=now(), skip_reason=null,
           workflow_run_id=coalesce(p_workflow_run_id,workflow_run_id),
           commit_sha=coalesce(p_commit_sha,commit_sha)
     where id=latest.id;
    insert into ecosystem.ai_usage_events(intent_id,event_type,provider,model,workflow_run_id,metadata)
    values(latest.id,'planned',latest.provider_requested,latest.model_requested,p_workflow_run_id,
           jsonb_build_object('decision','reclaimed-before-provider'));
    return jsonb_build_object('id',latest.id,'execute_allowed',true,'decision','reclaimed-before-provider',
                              'attempt_no',latest.attempt_no,'semantic_key',p_semantic_key);
  end if;

  if latest.status = 'failed' then
    transient_failure := latest.failure_class in ('network','timeout','rate-limit','provider-5xx');
    allow_retry :=
      (p_retry_mode = 'automatic' and transient_failure and latest.attempt_no < 2)
      or (p_retry_mode = 'manual' and coalesce(trim(p_retry_reason),'') <> '');

    if not allow_retry then
      decision := case
        when latest.failure_class in ('provider-billing','auth','configuration') then 'manual-retry-required'
        when transient_failure and latest.attempt_no >= 2 then 'automatic-retry-limit-reached'
        when transient_failure then 'retry-not-requested'
        else 'failed-not-retryable'
      end;
      insert into ecosystem.ai_usage_events(intent_id,event_type,provider,model,workflow_run_id,metadata)
      values(latest.id,'deduped',latest.provider_requested,latest.model_requested,p_workflow_run_id,
             jsonb_build_object('decision',decision,'failure_class',latest.failure_class));
      return jsonb_build_object('id',latest.id,'execute_allowed',false,'decision',decision,
                                'attempt_no',latest.attempt_no,'semantic_key',p_semantic_key,
                                'failure_class',latest.failure_class);
    end if;

    next_attempt := latest.attempt_no + 1;
    insert into ecosystem.ai_usage_intents(
      source_system, trigger_type, reason, provider_requested, model_requested,
      repository, pr_number, research_id, task_id, dedup_key, workflow_run_id,
      commit_sha, is_retry, parent_intent_id, metadata,
      semantic_key, attempt_no, retry_mode, retry_reason, retry_of_intent_id
    ) values (
      p_source_system, coalesce(nullif(trim(p_trigger_type),''),'unknown'), left(p_reason,2000),
      coalesce(nullif(trim(p_provider_requested),''),'deepseek'), p_model_requested,
      p_repository, p_pr_number, p_research_id, p_task_id,
      p_semantic_key || ':attempt:' || next_attempt::text, p_workflow_run_id,
      p_commit_sha, true, latest.id, coalesce(p_metadata,'{}'::jsonb),
      p_semantic_key, next_attempt, p_retry_mode, p_retry_reason, latest.id
    ) returning * into created;

    insert into ecosystem.ai_usage_events(intent_id,event_type,provider,model,workflow_run_id,metadata)
    values(created.id,'planned',created.provider_requested,created.model_requested,created.workflow_run_id,
           jsonb_build_object('decision','retry-approved','retry_mode',p_retry_mode,
                              'retry_reason',p_retry_reason,'retry_of',latest.id));

    return jsonb_build_object('id',created.id,'execute_allowed',true,'decision','retry-approved',
                              'attempt_no',next_attempt,'semantic_key',p_semantic_key,
                              'retry_of',latest.id);
  end if;

  return jsonb_build_object('id',latest.id,'execute_allowed',false,'decision','state-not-executable',
                            'attempt_no',latest.attempt_no,'semantic_key',p_semantic_key);
end;
$$;

create or replace function public.kueper_log_ai_usage_event_v2(
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
  p_failure_class text default null,
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
    p_estimated_cost_usd,p_actual_cost_usd,p_provider_request_id,p_workflow_run_id,p_error_code,
    left(p_error_message,4000),coalesce(p_metadata,'{}'::jsonb)
  ) returning id into event_id;

  update ecosystem.ai_usage_intents
     set status = p_event_type,
         updated_at = now(),
         started_at = case when p_event_type='started' then coalesce(started_at,now()) else started_at end,
         finished_at = case when p_event_type in ('completed','failed') then now() else finished_at end,
         skip_reason = case when p_event_type in ('skipped','blocked') then coalesce(left(p_error_message,1000),skip_reason) else skip_reason end,
         failure_class = case when p_event_type='failed' then p_failure_class else failure_class end
   where id = p_intent_id;

  return event_id;
end;
$$;

-- Replace the dashboard projection so unknown provider cost never renders as zero.
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
  per_intent as (
    select i.id,
           sum(e.input_tokens) as input_tokens,
           sum(e.output_tokens) as output_tokens,
           sum(e.estimated_cost_usd) as estimated_cost_usd,
           sum(e.actual_cost_usd) as actual_cost_usd,
           bool_or(e.event_type='started') as provider_started,
           bool_or(e.actual_cost_usd is not null) as cost_reconciled
      from today_intents i
      left join today_events e on e.intent_id=i.id
     group by i.id
  ),
  source_rollup as (
    select i.source_system,
           count(*)::int as planned,
           count(*) filter (where p.provider_started)::int as executed,
           count(*) filter (where i.status='completed')::int as completed,
           count(*) filter (where i.status='failed')::int as failed,
           count(*) filter (where i.status='blocked')::int as blocked,
           count(*) filter (where i.status='skipped')::int as skipped,
           count(*) filter (where p.provider_started and not p.cost_reconciled)::int as unreconciled_calls,
           case when bool_or(p.cost_reconciled) then sum(p.actual_cost_usd) filter (where p.cost_reconciled) else null end as actual_cost_usd,
           sum(p.estimated_cost_usd) as estimated_cost_usd
      from today_intents i
      join per_intent p on p.id=i.id
     group by i.source_system
  ),
  latest as (
    select i.id,i.created_at,i.updated_at,i.source_system,i.trigger_type,i.reason,
           i.provider_requested,i.model_requested,i.status,i.skip_reason,i.repository,
           i.pr_number,i.research_id,i.task_id,i.workflow_run_id,i.commit_sha,i.is_retry,
           i.semantic_key,i.attempt_no,i.retry_mode,i.retry_reason,i.retry_of_intent_id,i.failure_class,
           coalesce(p.input_tokens,0)::bigint as input_tokens,
           coalesce(p.output_tokens,0)::bigint as output_tokens,
           p.actual_cost_usd,
           p.estimated_cost_usd,
           p.cost_reconciled
      from ecosystem.ai_usage_intents i
      left join per_intent p on p.id=i.id
     order by i.created_at desc
     limit 50
  )
  select jsonb_build_object(
    'planned',(select count(*)::int from today_intents),
    'executed',(select count(*)::int from per_intent where provider_started),
    'completed',(select count(*)::int from today_intents where status='completed'),
    'failed',(select count(*)::int from today_intents where status='failed'),
    'blocked',(select count(*)::int from today_intents where status='blocked'),
    'skipped',(select count(*)::int from today_intents where status='skipped'),
    'deduped',(select count(*)::int from today_events where event_type='deduped'),
    'unreconciled_calls',(select count(*)::int from per_intent where provider_started and not cost_reconciled),
    'input_tokens',coalesce((select sum(input_tokens) from today_events),0),
    'output_tokens',coalesce((select sum(output_tokens) from today_events),0),
    'estimated_cost_usd',(select sum(estimated_cost_usd) from today_events),
    'actual_cost_usd',case when exists(select 1 from per_intent where cost_reconciled)
                           then (select sum(actual_cost_usd) from per_intent where cost_reconciled)
                           else null end,
    'by_source',coalesce((select jsonb_agg(to_jsonb(s) order by s.unreconciled_calls desc,s.planned desc) from source_rollup s),'[]'::jsonb),
    'latest',coalesce((select jsonb_agg(to_jsonb(l) order by l.created_at desc) from latest l),'[]'::jsonb)
  );
$$;

revoke all on function public.kueper_claim_ai_usage_attempt(text,text,text,text,text,text,text,bigint,text,text,bigint,text,text,text,jsonb) from public, anon, authenticated;
revoke all on function public.kueper_log_ai_usage_event_v2(uuid,text,text,text,bigint,bigint,bigint,numeric,numeric,text,bigint,text,text,text,jsonb) from public, anon, authenticated;
grant execute on function public.kueper_claim_ai_usage_attempt(text,text,text,text,text,text,text,bigint,text,text,bigint,text,text,text,jsonb) to service_role;
grant execute on function public.kueper_log_ai_usage_event_v2(uuid,text,text,text,bigint,bigint,bigint,numeric,numeric,text,bigint,text,text,text,jsonb) to service_role;
revoke all on function public.kueper_ai_usage_dashboard() from public, anon, authenticated;
grant execute on function public.kueper_ai_usage_dashboard() to service_role;
