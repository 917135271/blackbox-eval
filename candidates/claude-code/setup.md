# claude-code setup

This candidate uses the user-requested fork:

- Source: `https://github.com/claude-code-best/claude-code.git`
- Local clone: `candidates/claude-code/vendor/claude-code`
- Verified source commit: `7680c291ee7d8aa9cb291d518273352ad32256ec`
- Runtime package: `claude-code-best@2.8.3`
- Runtime command: `candidates/claude-code/runtime/node_modules/.bin/ccb.cmd`

The source repository requires Bun to build from source. For this benchmark,
the runnable npm package is installed locally with:

```powershell
npm install --prefix candidates/claude-code/runtime claude-code-best@2.8.3 --ignore-scripts
```

The runner starts `ccb.cmd` in non-interactive print mode with:

- `--bare`
- `--print`
- `--output-format json`
- `--settings candidates/claude-code/settings.json`
- `--mcp-config candidates/claude-code/mcp_config.json`
- `--strict-mcp-config`
- `--no-session-persistence`

OpenAI-compatible routing is enabled without storing secrets in repo:

- `CLAUDE_CODE_USE_OPENAI=1`
- `OPENAI_BASE_URL=https://api.deepseek.com`
- `OPENAI_MODEL=deepseek-v4-pro`
- `OPENAI_API_KEY` is injected from `LLM_API_KEY` by the runner.

MCP tools are loaded from `mcp_config.json`. Shell, file-editing, file-read,
web, and task/subagent tools are denied by the runner command line.
