# Upstream

`index.ts` and `agents.ts` are derived from the Pi Agent `v0.80.10` official subagent extension example at `packages/coding-agent/examples/extensions/subagent/`.

The adapter changes the single-agent text result to include the upstream usage counters alongside the structured summary. This allows the parent audit agent to register actual token usage through `complete_audit_subagent`.
