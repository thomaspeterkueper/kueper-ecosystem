-- Contract smoke test for KUEPER V7.1 claim RPC.
-- Execute after applying migrations in a disposable/test database.
-- The important invariant is that a claimed task always returns a non-null lease_token.

begin;

select public.kueper_create_task(
  p_type => 'worker-v71-smoke',
  p_source_project => 'ecosystem',
  p_target_project => 'ecosystem',
  p_payload => '{"smoke":true}'::jsonb,
  p_priority => 'low',
  p_idempotency_key => 'worker-v71-claim-contract'
);

with claimed as (
  select public.kueper_claim_task_v7(
    p_worker_id => 'worker-v71-contract-test',
    p_lease_seconds => 600,
    p_target_project => 'ecosystem',
    p_types => array['worker-v71-smoke']::text[]
  ) as task
)
select
  case
    when task is null then 'FAIL: no task claimed'
    when nullif(task->>'id', '') is null then 'FAIL: id missing'
    when nullif(task->>'lease_token', '') is null then 'FAIL: lease_token missing'
    else 'OK'
  end as claim_contract
from claimed;

rollback;
