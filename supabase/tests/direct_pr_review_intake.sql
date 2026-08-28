-- Run after applying the task-bus, PR-review lifecycle, and direct-intake migrations.
-- The entire test rolls back and leaves no test data.

begin;

do $$
declare
  task_id uuid;
  wildcard_task_id uuid;
  first_result jsonb;
  repeated_result jsonb;
begin
  insert into ecosystem.tasks (
    type, source_project, target_project, status, priority, payload,
    repository, idempotency_key, metadata
  ) values (
    'PR_REVIEW', 'ECO', 'ECO', 'pending', 'medium', '{}'::jsonb,
    'thomaspeterkueper/kueper-ecosystem',
    'direct-pr-rpc-test-' || gen_random_uuid()::text,
    '{}'::jsonb
  ) returning id into task_id;

  first_result := public.kueper_enqueue_direct_pr_review(
    task_id,
    'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/999999',
    'thomaspeterkueper/kueper-ecosystem'
  );
  if first_result->>'status' <> 'review_pending'
     or first_result->>'pr_url' <> 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/999999'
     or first_result->'result'->>'pr_url' <> 'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/999999'
     or first_result->'metadata'->>'direct_pr_intake' <> 'true'
     or first_result->'metadata'->>'direct_pr_intake_at' is null then
    raise exception 'pending intake transition did not persist the expected state';
  end if;

  repeated_result := public.kueper_enqueue_direct_pr_review(
    task_id,
    'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/999999',
    'thomaspeterkueper/kueper-ecosystem'
  );
  if repeated_result->>'id' <> task_id::text
     or repeated_result->>'status' <> 'review_pending'
     or repeated_result->'metadata'->>'direct_pr_intake_at'
        is distinct from first_result->'metadata'->>'direct_pr_intake_at' then
    raise exception 'review_pending retry was not idempotent';
  end if;

  update ecosystem.tasks
  set status = 'completed', completed_at = now()
  where id = task_id;
  repeated_result := public.kueper_enqueue_direct_pr_review(
    task_id,
    'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/999999',
    'thomaspeterkueper/kueper-ecosystem'
  );
  if repeated_result->>'id' <> task_id::text
     or repeated_result->>'status' <> 'completed' then
    raise exception 'completed retry was not treated as already processed';
  end if;

  begin
    perform public.kueper_enqueue_direct_pr_review(
      task_id,
      'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/999998',
      'thomaspeterkueper/kueper-ecosystem'
    );
    raise exception 'different PR URL was accepted for an existing task';
  exception when others then
    if sqlerrm = 'different PR URL was accepted for an existing task' then raise; end if;
    if sqlerrm <> 'task already processed for different PR' then
      raise exception 'unexpected different-URL error: %', sqlerrm;
    end if;
  end;

  begin
    perform public.kueper_requeue_changed_pr_head(
      wildcard_task_id,
      'https://github.com/example/repoXname/pull/123',
      'example/repo_name',
      repeat('1', 40)
    );
    raise exception 'changed-head RPC accepted repository LIKE-wildcard mismatch';
  exception when others then
    if sqlerrm = 'changed-head RPC accepted repository LIKE-wildcard mismatch' then raise; end if;
    if sqlerrm <> 'PR URL/repository mismatch' then
      raise exception 'unexpected changed-head repository mismatch error: %', sqlerrm;
    end if;
  end;

  insert into ecosystem.tasks (
    type, source_project, target_project, status, priority, payload,
    repository, idempotency_key, metadata
  ) values (
    'PR_REVIEW', 'ECO', 'ECO', 'pending', 'medium', '{}'::jsonb,
    'example/repo_name',
    'direct-pr-wildcard-test-' || gen_random_uuid()::text,
    '{}'::jsonb
  ) returning id into wildcard_task_id;

  begin
    perform public.kueper_enqueue_direct_pr_review(
      wildcard_task_id,
      'https://github.com/example/repoXname/pull/123',
      'example/repo_name'
    );
    raise exception 'repository LIKE-wildcard mismatch was accepted';
  exception when others then
    if sqlerrm = 'repository LIKE-wildcard mismatch was accepted' then raise; end if;
    if sqlerrm <> 'PR URL/repository mismatch' then
      raise exception 'unexpected repository mismatch error: %', sqlerrm;
    end if;
  end;

  if public.kueper_get_task_for_pr(
       'https://github.com/thomaspeterkueper/kueper-ecosystem/pull/999999'
     )->>'id' <> task_id::text then
    raise exception 'PR lookup did not return the existing task';
  end if;
end;
$$;

rollback;
