# KUEPER Agent Worker V7

Status: implementation ready  
State Plane: Supabase `ecosystem.*` via `public.kueper_*` RPCs  
Default provider: DeepSeek

## Secrets

The GitHub repository requires:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `DEEPSEEK_API_KEY`
- `KUEPER_BOT_TOKEN`

## Lifecycle

Each GitHub Actions run processes at most `KUEPER_MAX_TASKS` tasks (default 3):

```text
recover expired leases
        ↓
claim
        ↓
provider/cost route
   ├─ defer → reschedule via available_at
   └─ execute
        ↓
start + heartbeat
        ↓
DeepSeek
   ├─ repository task → Claude Code agent frontend
   └─ non-repository task → DeepSeek Chat API
        ↓
complete | fail/retry | park
```

## Repository tasks

The worker clones the target repository itself. An optional `base_sha` is checked before agent execution. Claude Code runs against DeepSeek's Anthropic-compatible endpoint and may edit only the checked-out target repository. The worker, not the model, owns branch creation, commit, push and PR creation.

Agent output markers:

- `KUEPER_PARK: <reason>` — temporary internal blocker.
- `KUEPER_PARK_OWNER: <reason>` — explicit owner/creative decision required.

## Cost scheduling

`config/provider-policy.json` contains mutable provider policy. Peak windows currently reflect the Owner-provided DeepSeek pricing notice and are deliberately configuration rather than code.

Low/medium cost-sensitive work is deferred to the end of a peak interval. High/critical work and operational coding/bug/security tasks continue immediately.

## Required V7 DB extension

After V6 is installed, apply:

`supabase/migrations/20260726113000_task_bus_v7_reschedule_rpc.sql`

This adds the server-only `kueper_reschedule_task()` RPC used to return a claimed task to `pending` with a future `available_at` without counting it as a failed execution.

## Current trigger

The worker runs every 15 minutes and can be started manually. This polling schedule is a bridge to the later event-driven dispatcher; it remains useful as a watchdog/fallback after event dispatch is introduced.
