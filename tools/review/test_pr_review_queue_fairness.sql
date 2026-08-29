-- KUEPER PR review queue fairness — executable SQL behavior test.
--
-- The starvation fix in 20260829104500_pr_review_queue_fairness.sql rewrites
-- kueper_list_review_pending (exact-head suppression, oldest/newest lane split,
-- interleaved lane ordering) and kueper_note_open_pr_head. This test applies
-- the migration chain to a real Postgres, seeds tasks and pr_review_runs, and
-- asserts the acceptance behavior:
--
--   1. a review_pending task with a persisted run at its *discovered* head is
--      excluded from the queue;
--   2. once discovery observes a changed head (kueper_note_open_pr_head) the
--      same task becomes eligible again;
--   3. lane capacity splits oldest/newest per the (lim+1)/2 formula and the
--      picked batch alternates between the two lanes by lane_order;
--   4. tasks without a discovered head remain eligible;
--   5. kueper_note_open_pr_head validation guards reject malformed input and
--      non-review-pending tasks.
--
-- Run against a scratch database:
--   psql -v ON_ERROR_STOP=1 -f tools/review/test_pr_review_queue_fairness.sql
--
-- Requires a superuser connection (creates the Supabase roles the migrations
-- grant to, and the pgcrypto extension).

\set ON_ERROR_STOP on

-- Supabase roles referenced by migration revoke/grant statements.
do $$
begin
  if not exists (select from pg_roles where rolname = 'anon') then create role anon; end if;
  if not exists (select from pg_roles where rolname = 'authenticated') then create role authenticated; end if;
  if not exists (select from pg_roles where rolname = 'service_role') then create role service_role; end if;
end $$;

-- Migration chain that defines the functions under test.
\ir ../../supabase/migrations/20260726082000_task_bus_v6_ecosystem_schema.sql
\ir ../../supabase/migrations/20260824093000_pr_review_lifecycle.sql
\ir ../../supabase/migrations/20260829104500_pr_review_queue_fairness.sql

create or replace function public.kueper_test_assert(p_cond boolean, p_msg text)
returns void
language plpgsql
as $$
begin
  if not coalesce(p_cond, false) then
    raise exception 'ASSERT FAILED: %', p_msg;
  end if;
end;
$$;

-- Deterministic fixtures. SHAs are 40-char hex; task ids are stable uuids.
-- Queue eligibility order is priority_rank then created_at; distinct
-- created_at values make the expected lane order unambiguous.

insert into ecosystem.tasks
  (id, type, source_project, target_project, status, priority, repository, pr_url,
   created_at, updated_at, completed_at, metadata)
values
  -- T1: reviewed exactly at its discovered head -> must be suppressed.
  ('00000000-0000-0000-0000-000000000001', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'medium',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-01 10:00:00+00', '2026-08-01 10:00:00+00', null,
   '{"discovered_pr_head_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'),
  -- T2: discovered head changed away from the reviewed head -> must reappear.
  ('00000000-0000-0000-0000-000000000002', 'IMPLEMENT_EXTERNAL_REQUIREMENT', 'ECO', 'ECO', 'review_pending', 'medium',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-02 10:00:00+00', '2026-08-02 10:00:00+00', null,
   '{"discovered_pr_head_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}'),
  -- T3: no discovered head -> must remain eligible.
  ('00000000-0000-0000-0000-000000000003', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'high',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-03 10:00:00+00', '2026-08-03 10:00:00+00', null, '{}'),
  -- T4/T5/T6/T7: unreviewed heads -> eligible; priorities/timestamps shape lanes.
  ('00000000-0000-0000-0000-000000000004', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'medium',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-04 10:00:00+00', '2026-08-04 10:00:00+00', null,
   '{"discovered_pr_head_sha": "dddddddddddddddddddddddddddddddddddddddd"}'),
  ('00000000-0000-0000-0000-000000000005', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'critical',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-05 10:00:00+00', '2026-08-05 10:00:00+00', null,
   '{"discovered_pr_head_sha": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"}'),
  ('00000000-0000-0000-0000-000000000006', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'medium',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-06 10:00:00+00', '2026-08-06 10:00:00+00', null,
   '{"discovered_pr_head_sha": "ffffffffffffffffffffffffffffffffffffffff"}'),
  ('00000000-0000-0000-0000-000000000007', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'low',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-07 10:00:00+00', '2026-08-07 10:00:00+00', null,
   '{"discovered_pr_head_sha": "1111111111111111111111111111111111111111"}'),
  -- T11: unreviewed newest medium -> makes the eligible count odd so the
  -- (lim+1)/2 lane split is observable in the interleaved output.
  ('00000000-0000-0000-0000-00000000000b', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'medium',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-11 10:00:00+00', '2026-08-11 10:00:00+00', null,
   '{"discovered_pr_head_sha": "4444444444444444444444444444444444444444"}'),
  -- T8: completed task on the same PR -> never listed.
  ('00000000-0000-0000-0000-000000000008', 'PR_REVIEW', 'ECO', 'ECO', 'completed', 'medium',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-08 10:00:00+00', '2026-08-08 10:00:00+00', '2026-08-08 11:00:00+00',
   '{"discovered_pr_head_sha": "2222222222222222222222222222222222222222"}'),
  -- T9: review_pending without pr_url -> never listed.
  ('00000000-0000-0000-0000-000000000009', 'PR_REVIEW', 'ECO', 'ECO', 'review_pending', 'medium',
   'thomaspeterkueper/kueper-ecosystem', null,
   '2026-08-09 10:00:00+00', '2026-08-09 10:00:00+00', null,
   '{"discovered_pr_head_sha": "3333333333333333333333333333333333333333"}'),
  -- T10: pending (not review_pending/completed) on the same PR -> note must reject.
  ('00000000-0000-0000-0000-00000000000a', 'PR_REVIEW', 'ECO', 'ECO', 'pending', 'medium',
   'thomaspeterkueper/kueper-ecosystem', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-10 10:00:00+00', '2026-08-10 10:00:00+00', null, '{}');

insert into ecosystem.pr_review_runs (task_id, pr_url, head_sha, verdict) values
  -- T1 has a persisted run at its discovered head -> suppresses T1.
  ('00000000-0000-0000-0000-000000000001', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'CHANGES_REQUIRED'),
  -- T2 has a persisted run at an *older* head only -> does not suppress T2.
  ('00000000-0000-0000-0000-000000000002', 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   'cccccccccccccccccccccccccccccccccccccccc', 'CHANGES_REQUIRED');

-- 1. Suppression + lane split with limit 5.
-- Eligible: T2, T3, T4, T5, T6, T7, T11 (7 tasks). Oldest lane = (5+1)/2 = 3
-- (T5 critical, T3 high, T2 oldest medium), newest lane = 5-3 = 2
-- (T11 newest medium, T6 next-newest; low-priority T7 loses the tie).
-- The final ORDER BY lane_order, lane interleaves the lanes: oldest[1],
-- newest[1], oldest[2], newest[2], oldest[3].
create temp table picked_5 as
select t.id::text as task_id
from public.kueper_list_review_pending(5) t;

do $$
declare
  n integer;
  got text[];
begin
  select count(*) into n from picked_5;
  perform public.kueper_test_assert(n = 5, 'limit 5 must return 5 eligible tasks, got ' || n);

  select array_agg(task_id order by ord) into got
  from (select task_id, row_number() over () as ord from picked_5) s;
  perform public.kueper_test_assert(
    got = array[
      '00000000-0000-0000-0000-000000000005', -- oldest lane 1: critical
      '00000000-0000-0000-0000-00000000000b', -- newest lane 1: newest medium T11
      '00000000-0000-0000-0000-000000000003', -- oldest lane 2: high
      '00000000-0000-0000-0000-000000000006', -- newest lane 2: next newest medium
      '00000000-0000-0000-0000-000000000002'  -- oldest lane 3: oldest medium
    ],
    'limit 5 must interleave oldest lane and newest lane by lane_order, got: ' || array_to_string(got, ','));

  select count(*) into n from picked_5 where task_id = '00000000-0000-0000-0000-000000000001';
  perform public.kueper_test_assert(n = 0, 'task with persisted run at its discovered head must be suppressed');

  select count(*) into n from picked_5 where task_id = '00000000-0000-0000-0000-000000000002';
  perform public.kueper_test_assert(n = 1, 'task whose discovered head differs from the reviewed head must reappear');

  select count(*) into n from picked_5 where task_id = '00000000-0000-0000-0000-000000000003';
  perform public.kueper_test_assert(n = 1, 'task without a discovered head must remain eligible');

  select count(*) into n from picked_5
  where task_id in ('00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000009');
  perform public.kueper_test_assert(n = 0, 'completed tasks and tasks without pr_url must never be listed');
end $$;

-- 2. Lane split scales: limit 4 -> oldest (4+1)/2 = 2, newest 4-2 = 2.
create temp table picked_4 as
select t.id::text as task_id
from public.kueper_list_review_pending(4) t;

do $$
declare
  got text[];
begin
  select array_agg(task_id order by ord) into got
  from (select task_id, row_number() over () as ord from picked_4) s;
  perform public.kueper_test_assert(
    got = array[
      '00000000-0000-0000-0000-000000000005', -- oldest lane 1: critical
      '00000000-0000-0000-0000-00000000000b', -- newest lane 1: newest medium T11
      '00000000-0000-0000-0000-000000000003', -- oldest lane 2: high
      '00000000-0000-0000-0000-000000000006'  -- newest lane 2: next newest medium
    ],
    'limit 4 must split lanes 2/2 and interleave, got: ' || array_to_string(got, ','));
end $$;

-- 3. Limit clamps: 0 -> 1, oversized -> all eligible (7).
do $$
declare
  n integer;
begin
  select count(*) into n from public.kueper_list_review_pending(0) t;
  perform public.kueper_test_assert(n = 1, 'limit 0 must clamp to 1 row, got ' || n);
  select count(*) into n from public.kueper_list_review_pending(100) t;
  perform public.kueper_test_assert(n = 7, 'limit 100 must clamp to 50 and return all 7 eligible tasks, got ' || n);
end $$;

-- 4. kueper_note_open_pr_head guards: malformed input and ineligible tasks
-- must raise, never silently no-op.
do $$
begin
  begin
    perform public.kueper_note_open_pr_head(
      '00000000-0000-0000-0000-000000000001',
      'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
      'thomaspeterkueper', -- missing owner/repo slash
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
    raise exception 'ASSERT FAILED: repository without owner/repo accepted';
  exception when others then
    if sqlerrm not like '%invalid GitHub repository%' then raise; end if;
  end;

  begin
    perform public.kueper_note_open_pr_head(
      '00000000-0000-0000-0000-000000000001',
      'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/not-a-number',
      'thomaspeterkueper/kueper-ecosystem',
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
    raise exception 'ASSERT FAILED: malformed PR URL accepted';
  exception when others then
    if sqlerrm not like '%invalid GitHub PR URL%' then raise; end if;
  end;

  begin
    perform public.kueper_note_open_pr_head(
      '00000000-0000-0000-0000-000000000001',
      'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
      'other/org', -- does not match the URL's repository
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
    raise exception 'ASSERT FAILED: mismatched repository accepted';
  exception when others then
    if sqlerrm not like '%PR URL/repository mismatch%' then raise; end if;
  end;

  begin
    perform public.kueper_note_open_pr_head(
      '00000000-0000-0000-0000-000000000001',
      'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
      'thomaspeterkueper/kueper-ecosystem',
      'short-sha');
    raise exception 'ASSERT FAILED: short head sha accepted';
  exception when others then
    if sqlerrm not like '%full GitHub head SHA is required%' then raise; end if;
  end;

  begin
    perform public.kueper_note_open_pr_head(
      'ffffffff-ffff-ffff-ffff-ffffffffffff', -- unknown task
      'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
      'thomaspeterkueper/kueper-ecosystem',
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
    raise exception 'ASSERT FAILED: unknown task accepted';
  exception when others then
    if sqlerrm not like '%task is not an active/completed review task%' then raise; end if;
  end;

  begin
    perform public.kueper_note_open_pr_head(
      '00000000-0000-0000-0000-00000000000a', -- pending task on the same PR
      'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
      'thomaspeterkueper/kueper-ecosystem',
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
    raise exception 'ASSERT FAILED: pending task accepted';
  exception when others then
    if sqlerrm not like '%task is not an active/completed review task%' then raise; end if;
  end;
end $$;

-- 5. Head-change transition: noting a new head on the suppressed task must
-- make it eligible again.
do $$
declare
  r jsonb;
  n integer;
  got text[];
begin
  select public.kueper_note_open_pr_head(
    '00000000-0000-0000-0000-000000000001',
    'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
    'thomaspeterkueper/kueper-ecosystem',
    '9999999999999999999999999999999999999999'
  ) into r;
  perform public.kueper_test_assert(
    r->'metadata'->>'discovered_pr_head_sha' = '9999999999999999999999999999999999999999',
    'note_open_pr_head must persist the discovered head');
  perform public.kueper_test_assert(
    r->>'status' = 'review_pending',
    'note_open_pr_head must return the updated task');
  perform public.kueper_test_assert(
    r->'metadata' ? 'discovered_pr_head_at',
    'note_open_pr_head must record when the head was observed');

  select count(*) into n from public.kueper_list_review_pending(10) t;
  perform public.kueper_test_assert(n = 8, 'after head change all 8 review_pending tasks must be eligible, got ' || n);

  select array_agg(t.id::text order by ord) into got
  from (select t.id, row_number() over () as ord from public.kueper_list_review_pending(10) t) q
  join ecosystem.tasks t on t.id = q.id;
  -- Oldest lane 5: T5 critical, T3 high, then oldest mediums T1, T2, T4.
  -- Newest lane 3: T11 (newest medium), T6, T7 (low). Interleaved by lane_order.
  perform public.kueper_test_assert(
    got = array[
      '00000000-0000-0000-0000-000000000005', -- oldest lane 1: critical
      '00000000-0000-0000-0000-00000000000b', -- newest lane 1: newest medium T11
      '00000000-0000-0000-0000-000000000003', -- oldest lane 2: high
      '00000000-0000-0000-0000-000000000006', -- newest lane 2
      '00000000-0000-0000-0000-000000000001', -- oldest lane 3: T1 back with its new head
      '00000000-0000-0000-0000-000000000007', -- newest lane 3: low priority
      '00000000-0000-0000-0000-000000000002', -- oldest lane 4
      '00000000-0000-0000-0000-000000000004'  -- oldest lane 5
    ],
    'head-changed task must reappear in lane order, got: ' || array_to_string(got, ','));
end $$;

-- 6. Legacy rows (created by kueper_reopen_legacy_pr_for_review /
-- kueper_submit_task_for_review before repository tracking) carry pr_url but a
-- null repository column. note_open_pr_head must backfill the repository from
-- the validated PR URL instead of raising; raising would abort the whole
-- discovery batch and starve the review queue.
insert into ecosystem.tasks
  (id, type, source_project, target_project, status, priority, repository, pr_url,
   created_at, updated_at, completed_at, metadata)
values
  ('00000000-0000-0000-0000-00000000000c', 'IMPLEMENT_EXTERNAL_REQUIREMENT', 'ECO', 'ECO', 'review_pending', 'medium',
   null, 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
   '2026-08-12 10:00:00+00', '2026-08-12 10:00:00+00', null, '{}');

do $$
declare
  r jsonb;
  backfilled text;
  n integer;
begin
  select public.kueper_note_open_pr_head(
    '00000000-0000-0000-0000-00000000000c',
    'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/37',
    'thomaspeterkueper/kueper-ecosystem',
    '5555555555555555555555555555555555555555'
  ) into r;
  perform public.kueper_test_assert(
    r->'metadata'->>'discovered_pr_head_sha' = '5555555555555555555555555555555555555555',
    'note_open_pr_head must note the head on a legacy row without repository');
  perform public.kueper_test_assert(
    r->>'status' = 'review_pending',
    'note_open_pr_head must return the updated legacy task');

  select repository into backfilled
  from ecosystem.tasks
  where id = '00000000-0000-0000-0000-00000000000c';
  perform public.kueper_test_assert(
    backfilled = 'thomaspeterkueper/kueper-ecosystem',
    'note_open_pr_head must backfill the repository column, got: ' || coalesce(backfilled, '<null>'));

  select count(*) into n
  from public.kueper_list_review_pending(100) t
  where t.id = '00000000-0000-0000-0000-00000000000c';
  perform public.kueper_test_assert(n = 1, 'backfilled legacy task must be eligible for review');
end $$;

select 'pr_review_queue_fairness: all SQL assertions passed' as result;
