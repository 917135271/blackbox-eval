# qwen-code setup

Status: installed and configured for GATE 2 setup checks.

## Official Sources

- Install and overview: https://qwenlm.github.io/qwen-code-docs/en/users/overview/
- Headless mode: https://qwenlm.github.io/qwen-code-docs/en/users/features/headless/
- Auth and model providers: https://qwenlm.github.io/qwen-code-docs/en/users/configuration/auth/
- MCP server config: https://qwenlm.github.io/qwen-code-docs/en/developers/tools/mcp-server/
- Shell/tool restrictions: https://qwenlm.github.io/qwen-code-docs/en/developers/tools/shell/

## Pinned Version

- Package: `@qwen-code/qwen-code@0.19.6`
- Install command used: `npm install -g @qwen-code/qwen-code@0.19.6`
- Verified command: `qwen --version`

## Runtime

- Headless command: `qwen --system-prompt <audit-eval-system-prompt> --prompt <task> --output-format json --exclude-tools <native-tools>`
- Workdir: `candidates/qwen-code/workdir`
- Project config: `candidates/qwen-code/workdir/.qwen/settings.json`
- Model protocol: OpenAI-compatible
- Base URL: `https://api.deepseek.com`
- Model: `deepseek-v4-pro`
- API key source: `LLM_API_KEY` environment variable only

## MCP

The project config registers two trusted stdio MCP servers:

- `policy_query`: `fixtures/policy_query_mcp.py`
- `expense_query`: `fixtures/expense_query_mcp.py`

Both servers use `includeTools` to expose only the fixture tools required by the benchmark.

## Native Tool Controls

- Runtime canary and eval commands pass `--exclude-tools` for native coding, file, search, web, user-question, task, and subagent tools.
- Project settings also include matching `tools.exclude` entries for those native tools.
- MCP servers are marked `trust: true` so MCP tool calls can proceed in headless mode without approving shell/write/edit tools.
- GATE 3 task runs dynamically add the task-specific `EVAL_TASK_LOG` env value to the MCP server config, then call official `qwen mcp approve --all` before launching the task so the updated config is non-interactive.
- GATE 3 task runs also pass the official headless `--system-prompt` option so qwen-code treats the prompt as an audit QA task rather than a coding/setup task.
