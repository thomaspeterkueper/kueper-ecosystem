-- KUEPER PR review lifecycle — server-side evidence gate for research candidates.
--
-- A technical PASS is necessary but not sufficient for research/candidates/*.
-- The reviewer marks the exact PASS head as evidence-gated. Completion then fails
-- closed until a trusted critical evidence review explicitly approves that same head.

create or replace function public.kueper_mark_research_evidence_gate(
  p_task_id uuid,
  p_head_sha text
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  normalized_head text := lower(trim(coalesce(p_head_sha, '')));
  r ecosystem.tasks;
begin
  if normalized_head !~ '^[0-9a-f]{40}$' then
    raise exception 'full head sha required';
  end if;

  if not exists (
    select 1
    from ecosystem.pr_review_runs rr
    where rr.task_id = p_task_id
      and rr.head_sha = normalized_head
      and rr.verdict = 'PASS'
  ) then
    raise exception 'no PASS review recorded for task/head';
  end if;

  update ecosystem.tasks
  set blocked_reason = 'critical scientific/evidence review required',
      requires_owner_decision = true,
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'research_evidence_gate', true,
        'technical_pass_head_sha', normalized_head,
        'research_evidence_gate_at', now()
      )
  where id = p_task_id
    and status = 'review_pending'
  returning * into r;

  if r.id is null then
    raise exception 'task is not review_pending';
  end if;

  return to_jsonb(r);
end;
$$;

create or replace function public.kueper_approve_research_candidate(
  p_task_id uuid,
  p_head_sha text
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  normalized_head text := lower(trim(coalesce(p_head_sha, '')));
  r ecosystem.tasks;
begin
  if normalized_head !~ '^[0-9a-f]{40}$' then
    raise exception 'full head sha required';
  end if;

  if not exists (
    select 1
    from ecosystem.pr_review_runs rr
    where rr.task_id = p_task_id
      and rr.head_sha = normalized_head
      and rr.verdict = 'PASS'
  ) then
    raise exception 'no PASS review recorded for task/head';
  end if;

  update ecosystem.tasks
  set blocked_reason = null,
      requires_owner_decision = false,
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'evidence_approved_head_sha', normalized_head,
        'evidence_approved_at', now()
      )
  where id = p_task_id
    and status = 'review_pending'
    and coalesce(metadata, '{}'::jsonb) @> '{"research_evidence_gate": true}'::jsonb
    and lower(coalesce(metadata->>'technical_pass_head_sha', '')) = normalized_head
  returning * into r;

  if r.id is null then
    raise exception 'research evidence gate is not active for task/head';
  end if;

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
  normalized_head text := lower(trim(coalesce(p_head_sha, '')));
  r ecosystem.tasks;
begin
  if not exists (
    select 1
    from ecosystem.pr_review_runs rr
    where rr.task_id = p_task_id
      and rr.head_sha = normalized_head
      and rr.verdict = 'PASS'
  ) then
    raise exception 'no PASS review recorded for task/head';
  end if;

  if exists (
    select 1
    from ecosystem.tasks t
    where t.id = p_task_id
      and t.status = 'review_pending'
      and coalesce(t.metadata, '{}'::jsonb) @> '{"research_evidence_gate": true}'::jsonb
      and lower(coalesce(t.metadata->>'evidence_approved_head_sha', '')) <> normalized_head
  ) then
    raise exception 'research evidence gate not approved for task/head';
  end if;

  update ecosystem.tasks
  set status = 'completed',
      completed_at = now(),
      blocked_reason = null,
      requires_owner_decision = false,
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'accepted_head_sha', normalized_head
      )
  where id = p_task_id and status = 'review_pending'
  returning * into r;

  if r.id is null then
    raise exception 'task is not review_pending';
  end if;

  return to_jsonb(r);
end;
$$;

revoke all on function public.kueper_mark_research_evidence_gate(uuid,text)
  from public, anon, authenticated;
revoke all on function public.kueper_approve_research_candidate(uuid,text)
  from public, anon, authenticated;
revoke all on function public.kueper_complete_reviewed_task(uuid,text)
  from public, anon, authenticated;

grant execute on function public.kueper_mark_research_evidence_gate(uuid,text)
  to service_role;
grant execute on function public.kueper_approve_research_candidate(uuid,text)
  to service_role;
grant execute on function public.kueper_complete_reviewed_task(uuid,text)
  to service_role;
