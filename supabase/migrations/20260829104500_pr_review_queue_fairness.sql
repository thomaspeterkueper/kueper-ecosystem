-- KUEPER PR review queue fairness and exact-head suppression.
--
-- A CHANGES_REQUIRED review intentionally leaves the originating task in
-- review_pending while REVIEW_FIX updates the same PR. Previously the same
-- already-reviewed head was therefore returned by kueper_list_review_pending
-- on every run, consuming one of the bounded reviewer slots forever.
--
-- Discovery records the current open-PR head in task metadata. The queue then
-- excludes a task only when that exact discovered head already has a persisted
-- review. Once discovery observes a changed head, the task becomes eligible
-- again automatically.

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
  if substring(normalized_url from '^https://github\.com/([^/]+/[^/]+)/pull/[0-9]+$') is distinct from normalized_repo then
    raise exception 'PR URL/repository mismatch';
  end if;
  if normalized_head is null or normalized_head !~ '^[0-9a-f]{40}$' then
    raise exception 'full GitHub head SHA is required';
  end if;

  update ecosystem.tasks
  set metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'discovered_pr_head_sha', normalized_head,
        'discovered_pr_head_at', now()
      ),
      updated_at = case
        when lower(coalesce(metadata->>'discovered_pr_head_sha', '')) is distinct from normalized_head
          then now()
        else updated_at
      end
  where id = p_task_id
    and pr_url = normalized_url
    and repository = normalized_repo
    and status in ('review_pending','completed')
  returning * into r;

  if r.id is null then
    raise exception 'task is not an active/completed review task for this PR';
  end if;

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
  with params as (
    select greatest(1, least(coalesce(p_limit,10), 50)) as lim
  ),
  eligible as (
    select t.*,
           case t.priority when 'critical' then 0 when 'high' then 1 when 'medium' then 2 else 3 end as priority_rank
    from ecosystem.tasks t
    where t.status = 'review_pending'
      and t.pr_url is not null
      and not exists (
        select 1
        from ecosystem.pr_review_runs rr
        where rr.task_id = t.id
          and rr.head_sha = lower(nullif(trim(coalesce(t.metadata->>'discovered_pr_head_sha', '')), ''))
      )
  ),
  oldest as (
    select e.id, 0 as lane,
           row_number() over (order by e.priority_rank, e.created_at, e.updated_at, e.id) as lane_order
    from eligible e, params p
    order by e.priority_rank, e.created_at, e.updated_at, e.id
    limit (select (lim + 1) / 2 from params)
  ),
  newest as (
    select e.id, 1 as lane,
           row_number() over (order by e.priority_rank, e.created_at desc, e.updated_at desc, e.id) as lane_order
    from eligible e, params p
    where not exists (select 1 from oldest o where o.id = e.id)
    order by e.priority_rank, e.created_at desc, e.updated_at desc, e.id
    limit (select lim - ((lim + 1) / 2) from params)
  ),
  picked as (
    select * from oldest
    union all
    select * from newest
  )
  select t.*
  from picked p
  join ecosystem.tasks t on t.id = p.id
  order by p.lane_order, p.lane
  limit (select lim from params);
$$;

revoke all on function public.kueper_note_open_pr_head(uuid,text,text,text)
  from public, anon, authenticated;
revoke all on function public.kueper_list_review_pending(integer)
  from public, anon, authenticated;

grant execute on function public.kueper_note_open_pr_head(uuid,text,text,text)
  to service_role;
grant execute on function public.kueper_list_review_pending(integer)
  to service_role;
