# OpenCode Adapter

The runtime wrapper copies generated `skills/` to `.opencode/skills/`, keeps the three Markdown subagents under `.opencode/agents/`, and merges `opencode.fragment.json` with the frozen DeepSeek and MCP configuration.

Business behavior comes from the generated `skills/` and `shared/` directories. Edit the canonical shared core instead of these generated copies.
