# Exa Gateway Smoke Test

The workflow `.github/workflows/exa-gateway-smoke.yml` validates the production Exa external-evidence path without running the downstream synthesis agent.

It runs automatically only when the smoke workflow or `tools/research/agent-with-exa.mjs` changes on `main`, and can also be started manually with `workflow_dispatch`.

The smoke test verifies:

- `AI_GATEWAY_API_KEY` is present in GitHub Actions;
- the configured AI Gateway model can execute `gateway.tools.exaSearch()`;
- at least one Exa tool result is returned;
- the generated evidence packet contains at least the configured minimum number of source URLs.

The test prints only non-secret telemetry (`provider`, `transport`, `model`, search-result count and URL count). It never prints the API key or source contents.

## Initial production validation — 2026-08-28

Status: **SUCCESS**

- Provider: `exa`
- Transport: `vercel-ai-gateway`
- Scout model: `deepseek/deepseek-v4-flash-0731`
- Exa search calls: `4`
- Source URLs surfaced: `13`
- GitHub Actions secret check: successful
- Workflow conclusion: `success`

This confirms that the GitHub Actions secret, Vercel AI Gateway authentication, configured scout model, Exa tool execution, and evidence-packet URL gate work together on the production `main` branch.
