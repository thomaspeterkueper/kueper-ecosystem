# Cost-aware scheduling

Status: active runtime policy

The KUEPER Agent Runtime treats model price as a scheduling input, not as a reason to weaken correctness. Time-critical and blocking work runs immediately. Expensive work that can wait is moved to configured provider off-peak windows.

## Task policy

Tasks may carry `cost_policy` and `estimated_effort` in their payload or as first-class task fields when the queue schema supports them.

`cost_policy` values:

- `immediate` — execute now, including during a peak window.
- `normal` — use ordinary task-class routing; do not delay solely for price.
- `prefer_off_peak` — defer low/medium-priority work while the provider is in a configured peak window.
- `off_peak_only` — defer non-urgent work whenever the provider is in a configured peak window.

`estimated_effort` values are `low`, `medium`, and `high`. High effort selects the provider's complex model unless a task explicitly requests another model.

High and critical priorities override off-peak deferral. Bugs, security failures and blocking runtime failures remain latency-sensitive by policy.

## External tasks

Routed External Tasks preserve these fields in frontmatter:

```yaml
priority: medium
cost_policy: prefer_off_peak
estimated_effort: high
```

The External Task ingestor copies them into the operational task payload. For older External Tasks without the fields, low/medium-priority repository implementation work defaults to `prefer_off_peak`; high/critical work defaults to `immediate`.

## Model selection

The default DeepSeek policy uses V4 Flash for low/medium effort and V4 Pro for high effort. This keeps repeated classification/routing work cheap while reserving the more expensive model for architecture, research synthesis and substantial repository implementation.

The worker does not hard-code tariff times. `config/provider-policy.json` contains the currently configured peak windows and price multiplier. When the provider changes its tariff windows, only policy configuration should need adjustment.

## NOXIA long simulations

A persistent NOXIA tester should use deterministic/game-native actions for ordinary play. It should accumulate observations and anomalies, then submit bounded reflection or session-analysis tasks. Long simulation analysis is explicitly cost-sensitive and should normally run off-peak; blocking `BUG` and `DEAD_END` reports remain immediate.

This also reduces report noise: many raw observations can be deduplicated and synthesized into a small number of evidenced development requests during a cheaper analysis window.

## Safety invariants

Cost scheduling must never:

- postpone a high/critical task solely to save model cost;
- bypass task deadlines or provider circuit breakers;
- change canonical state directly;
- downgrade correctness requirements;
- automatically merge repository changes.

The scheduler changes *when* and *which configured model* performs work, not the authority granted to an agent.
