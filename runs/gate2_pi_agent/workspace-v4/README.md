# Pi Agent Adapter

The runner loads the seven generated business Skills explicitly with `--skill`, loads the audit governance and official-derived subagent extensions with `-e`, and mounts `shared/` as the common control runtime.

Pi Agent has no built-in MCP or subagent primitive. The governance extension exposes the five common audit control operations as native Pi tools backed by the same Python control core. The subagent extension starts isolated Pi processes using the three bounded role definitions in `.pi/agents/`.

Business behavior comes from generated `skills/` and `shared/`. Edit the canonical shared core instead of those generated copies.
