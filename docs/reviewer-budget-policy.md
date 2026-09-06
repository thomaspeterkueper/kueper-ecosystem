# Reviewer budget policy

The DeepSeek PR-review budget reserves model-specific capacity instead of allowing routine Flash reviews to consume every daily slot.

Current production policy:

- `max_daily_calls = 14` total DeepSeek review reservations per UTC day.
- `max_daily_pro_calls = 2` of those slots are reserved for Pro reviews.
- Routine Flash reviews therefore consume at most 12 slots.
- Pro routing remains evidence-based (`pr_review_agent_v07.py`): privileged workflow/migration/security paths, high/critical priority, or explicit deep-reasoning evidence.

This prevents a full day of routine Flash traffic from blocking a later security- or migration-sensitive PR even while the configured Pro quota is still unused.
