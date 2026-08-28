# Exa Gateway Smoke Test

The workflow `.github/workflows/exa-gateway-smoke.yml` validates the production Exa external-evidence path without running the downstream synthesis agent.

It runs automatically only when the smoke workflow or `tools/research/agent-with-exa.mjs` changes on `main`, and can also be started manually with `workflow_dispatch`.

The smoke test verifies:

- `AI_GATEWAY_API_KEY` is present in GitHub Actions;
- the configured AI Gateway model can execute `gateway.tools.exaSearch()`;
- at least one Exa tool result is returned;
- the generated evidence packet contains at least the configured minimum number of source URLs.

The test prints only non-secret telemetry (`provider`, `transport`, `model`, search-result count and URL count). It never prints the API key or source contents.
