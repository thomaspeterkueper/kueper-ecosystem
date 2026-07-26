-- KUEPER V7 first live end-to-end task.
-- Run this ONCE in the kueper-knowledge-graph Supabase SQL Editor.
-- Unlike the V6 smoke test, this intentionally COMMITs one harmless task so the GitHub worker can claim it.

select public.kueper_create_task(
  p_type => 'CLASSIFY',
  p_source_project => 'ECO',
  p_target_project => 'ECO',
  p_payload => jsonb_build_object(
    'instruction', 'Classify this pilot task only. Do not modify any repository. Return JSON with keys classification, confidence, rationale.',
    'text', 'A scheduled research job should be delayed when the configured provider is in an expensive peak window unless the task is urgent.'
  ),
  p_priority => 'high',
  p_idempotency_key => 'v7-first-live-task-20260726',
  p_external_id => 'V7-PILOT-0001',
  p_preferred_provider => 'deepseek',
  p_preferred_model => 'deepseek-v4-flash',
  p_metadata => jsonb_build_object('actor','manual-v7-pilot','pilot',true)
);

-- Expected immediately after creation: status = pending.
-- The V7 GitHub worker should later move it through claimed/running to completed.
