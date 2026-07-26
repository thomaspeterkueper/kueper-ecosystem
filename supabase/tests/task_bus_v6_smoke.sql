-- Run against a disposable/local Supabase database after applying V6 migrations.
-- Entire test rolls back.

begin;

do $$
declare
  a public.tasks;
  b public.tasks;
  c public.tasks;
  claimed public.tasks;
  started public.tasks;
  completed public.tasks;
begin
  a := public.kueper_create_task(
    p_type => 'TEST_A', p_source_project => 'ECO', p_target_project => 'KG',
    p_idempotency_key => 'v6-smoke-a', p_metadata => '{"actor":"smoke-test"}'::jsonb
  );

  -- Idempotent create must return the same row.
  if (public.kueper_create_task(
    p_type => 'TEST_A', p_source_project => 'ECO', p_target_project => 'KG',
    p_idempotency_key => 'v6-smoke-a'
  )).id <> a.id then
    raise exception 'idempotency failed';
  end if;

  b := public.kueper_create_task(
    p_type => 'TEST_B', p_source_project => 'KG', p_target_project => 'MISH',
    p_parent_task_id => a.id, p_dependencies => array[a.id], p_idempotency_key => 'v6-smoke-b'
  );

  if b.depth <> 1 or b.root_task_id <> a.id then raise exception 'parent/root derivation failed'; end if;

  -- B is blocked by A, therefore A must be claimed first.
  claimed := public.kueper_claim_task('smoke-worker',600,null,null);
  if claimed.id <> a.id or claimed.status <> 'claimed' or claimed.lease_token is null then
    raise exception 'claim did not select runnable root task';
  end if;

  started := public.kueper_start_task(claimed.id,claimed.lease_token);
  if started.status <> 'running' then raise exception 'start failed'; end if;

  perform public.kueper_heartbeat_task(started.id,started.lease_token,600);
  completed := public.kueper_complete_task(started.id,started.lease_token,'{"ok":true}'::jsonb,'deepseek','test-model',100,20,0.001);
  if completed.status <> 'completed' then raise exception 'complete failed'; end if;

  -- Dependency is now satisfied, so B becomes runnable.
  claimed := public.kueper_claim_task('smoke-worker',600,'MISH',array['TEST_B']);
  if claimed.id <> b.id then raise exception 'dependency unblock failed'; end if;

  -- A non-owner parked task can later be requeued.
  started := public.kueper_start_task(claimed.id,claimed.lease_token);
  perform public.kueper_park_task(started.id,started.lease_token,'temporary internal blocker',false);
  if (select status from public.tasks where id=b.id) <> 'parked' then raise exception 'park failed'; end if;
  perform public.kueper_requeue_parked_task(b.id);
  if (select status from public.tasks where id=b.id) <> 'pending' then raise exception 'requeue failed'; end if;

  -- Retry path: create C with two attempts, fail once, then reclaim.
  c := public.kueper_create_task(
    p_type => 'TEST_C', p_source_project => 'ECO', p_target_project => 'KG',
    p_idempotency_key => 'v6-smoke-c', p_max_attempts => 2
  );
  claimed := public.kueper_claim_task('smoke-worker',600,'KG',array['TEST_C']);
  started := public.kueper_start_task(claimed.id,claimed.lease_token);
  perform public.kueper_fail_task(started.id,started.lease_token,'synthetic transient error',0);
  if (select status from public.tasks where id=c.id) <> 'pending' then raise exception 'retry requeue failed'; end if;

  -- Dependency cycles must be rejected.
  begin
    insert into public.task_dependencies(task_id,depends_on_task_id) values(a.id,b.id);
    raise exception 'cycle guard failed';
  exception when others then
    if sqlerrm = 'cycle guard failed' then raise; end if;
  end;
end;
$$;

rollback;
