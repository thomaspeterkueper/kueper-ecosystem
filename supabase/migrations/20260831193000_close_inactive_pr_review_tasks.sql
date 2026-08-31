-- Close stale PR-review tasks without starving the bounded reviewer queue.
--
-- GitHub is authoritative for OPEN/CLOSED/MERGED. The reviewer resolves that
-- state with its trusted bot token, then this narrow RPC records a terminal
-- cancellation. If GitHub later reopens the PR, normal direct-PR discovery
-- calls kueper_note_open_pr_head and reactivates the cancelled task.

create or replace function public.kueper_close_inactive_pr_review_task(
  p_task_id uuid,
  p_pr_url text,
  p_pr_state text
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  normalized_url text := nullif(trim(coalesce(p_pr_url, '')), '');
  normalized_state text := upper(nullif(trim(coalesce(p_pr_state, '')), ''));
  r ecosystem.tasks;
begin
  if normalized_url is null
     or normalized_url !~ '^https://github\.com/[^/]+/[^/]+/pull/[0-9]+$' then
    raise exception 'invalid GitHub PR URL';
  end if;
  if normalized_state not in ('CLOSED', 'MERGED') then
    raise exception 'inactive PR state must be CLOSED or MERGED';
  end if;

  update ecosystem.tasks
  set status = 'cancelled',
      completed_at = now(),
      blocked_reason = null,
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'pr_terminal_state', normalized_state,
        'pr_terminal_at', now()
      )
  where id = p_task_id
    and pr_url = normalized_url
    and status = 'review_pending'
  returning * into r;

  if r.id is null then
    select * into r
    from ecosystem.tasks
    where id = p_task_id
      and pr_url = normalized_url
      and status = 'cancelled'
      and metadata->>'pr_terminal_state' = normalized_state;
  end if;

  if r.id is null then
    raise exception 'task is not an active or matching terminal review task for this PR';
  end if;

  return to_jsonb(r);
end;
$$;

-- Extend open-head observation with the inverse transition. Only discovery of
-- an actually open PR calls this RPC; ordinary completed tasks retain their
-- existing exact-head behavior.
create or replace function public.kueper_note_open_pr_head(
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
  if substring(normalized_url from '^https://github\.com/([^/]+/[^/]+)/pull/[0-9]+$')
       is distinct from normalized_repo then
    raise exception 'PR URL/repository mismatch';
  end if;
  if normalized_head is null or normalized_head !~ '^[0-9a-f]{40}$' then
    raise exception 'full GitHub head SHA is required';
  end if;

  update ecosystem.tasks
  set status = case when status = 'cancelled' then 'review_pending' else status end,
      completed_at = case when status = 'cancelled' then null else completed_at end,
      metadata = (coalesce(metadata, '{}'::jsonb) - 'pr_terminal_state' - 'pr_terminal_at')
        || jsonb_build_object(
          'discovered_pr_head_sha', normalized_head,
          'discovered_pr_head_at', now()
        ),
      updated_at = case
        when status = 'cancelled'
          or lower(coalesce(metadata->>'discovered_pr_head_sha', '')) is distinct from normalized_head
          then now()
        else updated_at
      end,
      repository = normalized_repo
  where id = p_task_id
    and pr_url = normalized_url
    and status in ('review_pending', 'completed', 'cancelled')
  returning * into r;

  if r.id is null then
    raise exception 'task is not an active/completed/cancelled review task for this PR';
  end if;

  return to_jsonb(r);
end;
$$;

revoke all on function public.kueper_close_inactive_pr_review_task(uuid,text,text)
  from public, anon, authenticated;
revoke all on function public.kueper_note_open_pr_head(uuid,text,text,text)
  from public, anon, authenticated;

grant execute on function public.kueper_close_inactive_pr_review_task(uuid,text,text)
  to service_role;
grant execute on function public.kueper_note_open_pr_head(uuid,text,text,text)
  to service_role;
