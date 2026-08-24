-- KUEPER V7.3 — PR review lifecycle and persisted review generations.

alter table ecosystem.tasks drop constraint if exists tasks_status_check;
alter table ecosystem.tasks add constraint tasks_status_check
  check (status in ('pending','claimed','running','review_pending','parked','completed','failed','cancelled'));

create table if not exists ecosystem.pr_review_runs (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references ecosystem.tasks(id) on delete cascade,
  pr_url text not null,
  head_sha text not null,
  verdict text not null check (verdict in ('PASS','CHANGES_REQUIRED')),
  provider text,
  model text,
  summary text,
  findings jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique(task_id, head_sha)
);

create index if not exists pr_review_runs_task_idx
  on ecosystem.pr_review_runs(task_id, created_at desc);

create or replace function public.kueper_submit_task_for_review(
  p_task_id uuid,
  p_lease_token uuid,
  p_result jsonb default '{}'::jsonb,
  p_provider text default null,
  p_model text default null,
  p_input_tokens bigint default null,
  p_output_tokens bigint default null,
  p_cost_estimate_eur numeric default null
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  r ecosystem.tasks;
  derived_pr_url text;
begin
  derived_pr_url := nullif(trim(coalesce(p_result->>'pr_url','')), '');
  if derived_pr_url is null then
    raise exception 'review submission requires result.pr_url';
  end if;

  update ecosystem.tasks
  set status = 'review_pending',
      result = coalesce(p_result, '{}'::jsonb),
      pr_url = derived_pr_url,
      agent_provider = coalesce(p_provider, agent_provider),
      agent_model = coalesce(p_model, agent_model),
      input_tokens = p_input_tokens,
      output_tokens = p_output_tokens,
      cost_estimate_eur = p_cost_estimate_eur,
      lease_owner = null,
      lease_token = null,
      lease_expires_at = null,
      blocked_reason = null,
      completed_at = null
  where id = p_task_id
    and status in ('claimed','running')
    and lease_token = p_lease_token
  returning * into r;

  if r.id is null then
    raise exception 'task lease invalid';
  end if;

  update ecosystem.task_runs
  set status = 'succeeded',
      finished_at = now(),
      provider = coalesce(p_provider, provider),
      model = coalesce(p_model, model),
      input_tokens = p_input_tokens,
      output_tokens = p_output_tokens,
      cost_estimate_eur = p_cost_estimate_eur,
      result = p_result,
      metadata = metadata || jsonb_build_object('next_state','review_pending')
  where task_id = r.id and attempt = r.attempt_count;

  return to_jsonb(r);
end;
$$;

create or replace function public.kueper_list_review_pending(
  p_limit integer default 10
)
returns setof ecosystem.tasks
language sql
security definer
set search_path = ecosystem, public, pg_temp
as $$
  select t.*
  from ecosystem.tasks t
  where t.status = 'review_pending'
    and t.pr_url is not null
  order by
    case t.priority when 'critical' then 0 when 'high' then 1 when 'medium' then 2 else 3 end,
    t.updated_at,
    t.created_at
  limit greatest(1, least(coalesce(p_limit,10), 50));
$$;

create or replace function public.kueper_get_pr_review(
  p_task_id uuid,
  p_head_sha text
)
returns jsonb
language sql
security definer
set search_path = ecosystem, public, pg_temp
as $$
  select to_jsonb(r)
  from ecosystem.pr_review_runs r
  where r.task_id = p_task_id and r.head_sha = p_head_sha
  limit 1;
$$;

create or replace function public.kueper_record_pr_review(
  p_task_id uuid,
  p_pr_url text,
  p_head_sha text,
  p_verdict text,
  p_provider text default null,
  p_model text default null,
  p_summary text default null,
  p_findings jsonb default '[]'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  r ecosystem.pr_review_runs;
begin
  if p_verdict not in ('PASS','CHANGES_REQUIRED') then
    raise exception 'invalid review verdict';
  end if;
  if p_head_sha is null or length(trim(p_head_sha)) < 7 then
    raise exception 'head sha required';
  end if;
  if jsonb_typeof(coalesce(p_findings,'[]'::jsonb)) <> 'array' then
    raise exception 'findings must be a JSON array';
  end if;
  if not exists (
    select 1 from ecosystem.tasks
    where id = p_task_id and status = 'review_pending' and pr_url = p_pr_url
  ) then
    raise exception 'task is not review_pending for this PR';
  end if;

  insert into ecosystem.pr_review_runs(task_id, pr_url, head_sha, verdict, provider, model, summary, findings)
  values(p_task_id, p_pr_url, lower(trim(p_head_sha)), p_verdict, p_provider, p_model, p_summary, coalesce(p_findings,'[]'::jsonb))
  on conflict(task_id, head_sha) do nothing;

  select * into r
  from ecosystem.pr_review_runs
  where task_id = p_task_id and head_sha = lower(trim(p_head_sha));

  return to_jsonb(r);
end;
$$;

create or replace function public.kueper_complete_reviewed_task(
  p_task_id uuid,
  p_head_sha text
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  r ecosystem.tasks;
begin
  if not exists (
    select 1
    from ecosystem.pr_review_runs rr
    where rr.task_id = p_task_id
      and rr.head_sha = lower(trim(p_head_sha))
      and rr.verdict = 'PASS'
  ) then
    raise exception 'no PASS review recorded for task/head';
  end if;

  update ecosystem.tasks
  set status = 'completed',
      completed_at = now(),
      blocked_reason = null,
      metadata = metadata || jsonb_build_object('accepted_head_sha', lower(trim(p_head_sha)))
  where id = p_task_id and status = 'review_pending'
  returning * into r;

  if r.id is null then
    raise exception 'task is not review_pending';
  end if;

  return to_jsonb(r);
end;
$$;

revoke all on function public.kueper_submit_task_for_review(uuid,uuid,jsonb,text,text,bigint,bigint,numeric) from public, anon, authenticated;
revoke all on function public.kueper_list_review_pending(integer) from public, anon, authenticated;
revoke all on function public.kueper_get_pr_review(uuid,text) from public, anon, authenticated;
revoke all on function public.kueper_record_pr_review(uuid,text,text,text,text,text,text,jsonb) from public, anon, authenticated;
revoke all on function public.kueper_complete_reviewed_task(uuid,text) from public, anon, authenticated;

grant execute on function public.kueper_submit_task_for_review(uuid,uuid,jsonb,text,text,bigint,bigint,numeric) to service_role;
grant execute on function public.kueper_list_review_pending(integer) to service_role;
grant execute on function public.kueper_get_pr_review(uuid,text) to service_role;
grant execute on function public.kueper_record_pr_review(uuid,text,text,text,text,text,text,jsonb) to service_role;
grant execute on function public.kueper_complete_reviewed_task(uuid,text) to service_role;
