# Worker V7.1 recovery fix

This patch addresses three failure modes observed in `KUEPER Agent Worker V7`:

1. a stale DeepSeek provider pause after billing had been replenished;
2. a claimed task reaching the worker without a usable serialized `lease_token`;
3. Python failures being hidden by `| tee` because the workflow step did not enable `pipefail`.

## Deployment order

1. Apply `supabase/migrations/20260821163500_worker_v71_claim_and_provider_reset.sql` to the production Supabase project.
2. Merge the worker branch/PR.
3. Re-run `KUEPER Agent Worker V7` with one task first.
4. Confirm that `Process bounded task batch` either completes a task or produces a real red workflow failure.

The V7.1 wrapper probes DeepSeek only when the circuit breaker says the provider is paused. A successful `/models` response is treated as evidence that a billing-related pause is stale. Real 402/429/503 errors are still handled by the existing V7 circuit breaker during task execution.
