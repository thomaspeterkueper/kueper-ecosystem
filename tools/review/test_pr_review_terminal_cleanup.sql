-- KUEPER terminal PR cleanup — executable SQL behavior test.
-- Run against a scratch database:
--   psql -v ON_ERROR_STOP=1 -f tools/review/test_pr_review_terminal_cleanup.sql

\set ON_ERROR_STOP on

do $$
begin
  if not exists (select from pg_roles where rolname = 'anon') then create role anon; end if;
  if not exists (select from pg_roles where rolname = 'authenticated') then create role authenticated; end if;
  if not exists (select from pg_roles where rolname = 'service_role') then create role service_role; end if;
end $$;

\ir ../../supabase/migrations/20260726082000_task_bus_v6_ecosystem_schema.sql
\ir ../../supabase/migrations/20260824093000_pr_review_lifecycle.sql
\ir ../../supabase/migrations/20260829104500_pr_review_queue_fairness.sql
\ir ../../supabase/migrations/20260831193000_close_inactive_pr_review_tasks.sql

insert into ecosystem.tasks
  (id, type, source_project, target_project, status, priority, repository, pr_url, metadata)
values
  ('10000000-0000-0000-0000-000000000001', 'PR_REVIEW', 'ECO', 'NOXIA',
   'review_pending', 'medium', 'thomaspeterkueper/noxiagame',
   'https://github.com/thomaspeterkueper/noxiagame/pull/10',
   '{"discovered_pr_head_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'),
  ('10000000-0000-0000-0000-000000000002', 'PR_REVIEW', 'ECO', 'NOXIA',
   'review_pending', 'medium', 'thomaspeterkueper/noxiagame',
   'https://github.com/thomaspeterkueper/noxiagame/pull/11',
   '{"discovered_pr_head_sha":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}');

do $$
declare
  r jsonb;
  n integer;
begin
  select public.kueper_close_inactive_pr_review_task(
    '10000000-0000-0000-0000-000000000001',
    'https://github.com/thomaspeterkueper/noxiagame/pull/10',
    'MERGED'
  ) into r;
  if r->>'status' <> 'cancelled' or r->'metadata'->>'pr_terminal_state' <> 'MERGED' then
    raise exception 'terminal cleanup did not cancel and annotate the task';
  end if;

  select count(*) into n from public.kueper_list_review_pending(3);
  if n <> 1 then
    raise exception 'cancelled task still occupies the bounded queue: % rows', n;
  end if;

  -- Idempotent retry must return the same terminal row.
  perform public.kueper_close_inactive_pr_review_task(
    '10000000-0000-0000-0000-000000000001',
    'https://github.com/thomaspeterkueper/noxiagame/pull/10',
    'MERGED'
  );

  -- Discovery of a reopened PR reactivates the exact task.
  select public.kueper_note_open_pr_head(
    '10000000-0000-0000-0000-000000000001',
    'https://github.com/thomaspeterkueper/noxiagame/pull/10',
    'thomaspeterkueper/noxiagame',
    'cccccccccccccccccccccccccccccccccccccccc'
  ) into r;
  if r->>'status' <> 'review_pending' or r->'metadata' ? 'pr_terminal_state' then
    raise exception 'reopened PR was not reactivated cleanly';
  end if;

  select count(*) into n from public.kueper_list_review_pending(3);
  if n <> 2 then
    raise exception 'reactivated task did not return to queue: % rows', n;
  end if;
end $$;

select 'pr_review_terminal_cleanup: all SQL assertions passed' as result;
