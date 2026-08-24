-- KUEPER V7.3 — recovery path for legacy repository tasks completed before review_pending existed.

create or replace function public.kueper_reopen_legacy_pr_for_review(
  p_pr_url text
)
returns jsonb
language plpgsql
security definer
set search_path = ecosystem, public, pg_temp
as $$
declare
  normalized_url text := nullif(trim(coalesce(p_pr_url,'')), '');
  match_count integer;
  r ecosystem.tasks;
begin
  if normalized_url is null then
    raise exception 'PR URL is required';
  end if;

  select count(*) into match_count
  from ecosystem.tasks t
  where t.status = 'completed'
    and coalesce(nullif(trim(t.pr_url), ''), nullif(trim(t.result->>'pr_url'), '')) = normalized_url;

  if match_count = 0 then
    raise exception 'no completed legacy task found for PR %', normalized_url;
  end if;
  if match_count > 1 then
    raise exception 'multiple completed legacy tasks found for PR %; refuse ambiguous recovery', normalized_url;
  end if;

  update ecosystem.tasks
  set status = 'review_pending',
      pr_url = normalized_url,
      completed_at = null,
      blocked_reason = null,
      metadata = metadata || jsonb_build_object(
        'legacy_review_recovery', true,
        'legacy_review_recovery_at', now()
      )
  where id = (
    select t.id
    from ecosystem.tasks t
    where t.status = 'completed'
      and coalesce(nullif(trim(t.pr_url), ''), nullif(trim(t.result->>'pr_url'), '')) = normalized_url
    limit 1
  )
  returning * into r;

  return to_jsonb(r);
end;
$$;

revoke all on function public.kueper_reopen_legacy_pr_for_review(text) from public, anon, authenticated;
grant execute on function public.kueper_reopen_legacy_pr_for_review(text) to service_role;
