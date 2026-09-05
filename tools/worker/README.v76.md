# Agent Worker v7.6

Execution flow:

`peek → route → provider check → cost-window check → atomic budget+claim → start → execute`

This replaces the previous `claim → route` ordering. Therefore temporary provider pauses, off-peak scheduling and exhausted daily LLM budgets no longer consume task attempts.
