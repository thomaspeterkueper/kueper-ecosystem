-- Cover AI usage lineage foreign keys used for retry/audit traversal.
create index if not exists ai_usage_intents_parent_intent_idx
  on ecosystem.ai_usage_intents(parent_intent_id)
  where parent_intent_id is not null;

create index if not exists ai_usage_intents_retry_of_idx
  on ecosystem.ai_usage_intents(retry_of_intent_id)
  where retry_of_intent_id is not null;
