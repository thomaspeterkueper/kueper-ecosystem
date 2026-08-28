-- KUEPER V7.3 — direct PR intake into the existing review lifecycle.
-- Directly-created PRs do not hold worker leases, so they cannot use
-- kueper_submit_task_for_review. These RPCs are intentionally narrow.

create or replace function public.kueper_get_task_for_pr(
  p_pr_url text
)
returns jsonb
language sql
security definer
set search_path = ecosystem, public, pg_temp
as $$
  select to_jsonb(t)
  from ecosystem.tasks t
  where t.pr_url = nullif(trim(coalesce(p_pr_url, '')), '')
  order by
    case t.status
      when 'review_pending' then 0
      when 'running' then 1
      when 'claimed' then 2
      when 'pending' then 3
      when 'completed' then 4
      else 5
    end,
    t.updated_at desc,
    t.created_at desc
  limit 1;
$$;

create or replace function public.kueper_enqueue_direct_pr_review(
  p_task_id uuid,
  p_pr_url text,
  p_repository text
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  normalized_url text := nullif(trim(coalesce(p_pr_url, '')), '');
  normalized_repo text := nullif(trim(coalesce(p_repository, '')), '');
  url_repo text;
  r ecosystem.tasks;
begin
  if normalized_url is null then
    raise exception 'PR URL is required';
  end if;
  if normalized_repo is null then
    raise exception 'repository is required';
  end if;
  if normalized_repo !~ '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' then
    raise exception 'invalid GitHub repository';
  end if;
  if normalized_url !~ '^https://github\.com/[^/]+/[^/]+/pull/[0-9]+$' then
    raise exception 'invalid GitHub PR URL';
  end if;
  url_repo := substring(
    normalized_url from '^https://github\.com/([^/]+/[^/]+)/pull/[0-9]+$'
  );
  if url_repo is distinct from normalized_repo then
    raise exception 'PR URL/repository mismatch';
  end if;

  select * into r
  from ecosystem.tasks
  where id = p_task_id;

  if r.id is null then
    raise exception 'task not found';
  end if;
  if r.type <> 'PR_REVIEW' then
    raise exception 'direct PR intake requires PR_REVIEW task';
  end if;
  if coalesce(trim(r.repository), '') <> normalized_repo then
    raise exception 'task repository mismatch';
  end if;

  if r.status in ('review_pending', 'completed') then
    if coalesce(trim(r.pr_url), '') <> normalized_url then
      raise exception 'task already processed for different PR';
    end if;
    return to_jsonb(r);
  end if;

  if r.status <> 'pending' then
    raise exception 'direct PR intake task must be pending, review_pending, or completed';
  end if;

  update ecosystem.tasks
  set status = 'review_pending',
      pr_url = normalized_url,
      result = coalesce(result, '{}'::jsonb) || jsonb_build_object('pr_url', normalized_url),
      blocked_reason = null,
      completed_at = null,
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'direct_pr_intake', true,
        'direct_pr_intake_at', now()
      )
  where id = p_task_id
  returning * into r;

  return to_jsonb(r);
end;
$$;

create or replace function public.kueper_requeue_changed_pr_head(
  p_task_id uuid,
  p_pr_url text,
  p_repository text,
  p_head_sha text
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  normalized_url text := nullif(trim(coalesce(p_pr_url, '')), '');
  normalized_repo text := nullif(trim(coalesce(p_repository, '')), '');
  normalized_head text := lower(nullif(trim(coalesce(p_head_sha, '')), ''));
  url_repo text;
  accepted_head text;
  r ecosystem.tasks;
begin
  if normalized_url is null or normalized_repo is null then
    raise exception 'PR URL and repository are required';
  end if;
  if normalized_repo !~ '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' then
    raise exception 'invalid GitHub repository';
  end if;
  if normalized_url !~ '^https://github\.com/[^/]+/[^/]+/pull/[0-9]+$' then
    raise exception 'invalid GitHub PR URL';
  end if;
  url_repo := substring(
    normalized_url from '^https://github\.com/([^/]+/[^/]+)/pull/[0-9]+$'
  );
  if url_repo is distinct from normalized_repo then
    raise exception 'PR URL/repository mismatch';
  end if;
  if normalized_head is null or normalized_head !~ '^[0-9a-f]{40}$' then
    raise exception 'full GitHub head SHA is required';
  end if;

  select * into r
  from ecosystem.tasks
  where id = p_task_id;

  if r.id is null then
    raise exception 'task not found';
  end if;
  if coalesce(trim(r.repository), '') <> normalized_repo then
    raise exception 'task repository mismatch';
  end if;
  if coalesce(trim(r.pr_url), '') <> normalized_url then
    raise exception 'task PR URL mismatch';
  end if;
  if r.status <> 'completed' then
    raise exception 'changed-head requeue requires completed task';
  end if;

  accepted_head := lower(nullif(trim(coalesce(r.metadata->>'accepted_head_sha', '')), ''));
  if accepted_head is null then
    raise exception 'completed task has no accepted_head_sha';
  end if;

  if accepted_head = normalized_head then
    return to_jsonb(r);
  end if;

  if not exists (
    select 1
    from ecosystem.pr_review_runs rr
    where rr.task_id = r.id
      and rr.head_sha = accepted_head
      and rr.verdict = 'PASS'
  ) then
    raise exception 'accepted head has no persisted PASS review';
  end if;

  update ecosystem.tasks
  set status = 'review_pending',
      completed_at = null,
      blocked_reason = null,
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        're_review_requested_at', now(),
        're_review_head_sha', normalized_head
      )
  where id = p_task_id
  returning * into r;

  return to_jsonb(r);
end;
$$;

revoke all on function public.kueper_get_task_for_pr(text)
  from public, anon, authenticated;
revoke all on function public.kueper_enqueue_direct_pr_review(uuid,text,text)
  from public, anon, authenticated;
revoke all on function public.kueper_requeue_changed_pr_head(uuid,text,text,text)
  from public, anon, authenticated;

grant execute on function public.kueper_get_task_for_pr(text)
  to service_role;
grant execute on function public.kueper_enqueue_direct_pr_review(uuid,text,text)
  to service_role;
grant execute on function public.kueper_requeue_changed_pr_head(uuid,text,text,text)
  to service_role;
