# Exa Gateway Smoke Test

The workflow `.github/workflows/exa-gateway-smoke.yml` validates the production Exa external-evidence path without running the downstream synthesis agent.

It runs automatically only when the smoke workflow or `tools/research/agent-with-exa.mjs` changes on `main`, and can also be started manually with `workflow_dispatch`.

The smoke test verifies:

- `AI_GATEWAY_API_KEY` is present in GitHub Actions;
- the configured AI Gateway model can execute `gateway.tools.exaSearch()`;
- at least one Exa tool result is returned;
- the generated evidence packet contains at least the configured minimum number of source URLs.

The test prints only non-secret telemetry (`provider`, `transport`, `model`, evidence profile, adaptive escalation state, search-call count and URL count). It never prints the API key or source contents.

## Cost-aware scout behavior

The production scout now uses two model steps as its normal path: one forced Exa search followed by synthesis. It does not perform another search merely to increase source count when the first pass already satisfies the evidence profile.

A second two-step pass is available only when the first pass has insufficient URL coverage, explicitly requests follow-up because of unresolved conflict/source quality, or reports low confidence. This keeps the normal ceiling at one Exa search call while preserving a maximum of four model steps for genuinely difficult questions.

## Initial production validation — 2026-08-28

Status: **SUCCESS**

- Provider: `exa`
- Transport: `vercel-ai-gateway`
- Scout model: `deepseek/deepseek-v4-flash-0731`
- Exa search calls: `4`
- Source URLs surfaced: `13`
- GitHub Actions secret check: successful
- Workflow conclusion: `success`

This confirmed the initial end-to-end Gateway/Exa integration.

## Cost-aware validation — 2026-08-28

Status: **SUCCESS**

- Base steps: `2`
- Maximum steps: `4`
- Adaptive escalation: `false`
- Exa search calls: `1`
- Source URLs surfaced: `6`
- Research configuration check: `success`
- Exa Gateway smoke test: `success`

For the same simple documentation-validation class of smoke query, the scout therefore completed with one Exa search call instead of four while still exceeding the required source-URL gate.
