# opencode setup

Status: installed and configured for GATE 2 setup checks.

## Official Sources

- Install: https://opencode.ai/docs/
- CLI headless run: https://opencode.ai/docs/cli/
- Config: https://opencode.ai/docs/config/
- Providers: https://opencode.ai/docs/providers/
- Permissions: https://opencode.ai/docs/permissions/
- MCP servers: https://opencode.ai/docs/mcp-servers/

## Pinned Version

- Package: `opencode-ai@1.17.14`
- Install command used: `npm install -g opencode-ai@1.17.14`
- Verified command: `opencode --version`

## Runtime

- Headless command: `opencode run --dir candidates/opencode/workdir --format json --agent audit-eval <task>`
- Workdir: `candidates/opencode/workdir`
- Project config: `candidates/opencode/workdir/opencode.json`
- Provider id: `deepseek`
- Base URL: `https://api.deepseek.com`
- Model: `deepseek/deepseek-v4-pro`
- API key source: `LLM_API_KEY` environment variable only

## MCP

The project config registers two local MCP servers:

- `policy_query`: `fixtures/policy_query_mcp.py`
- `expense_query`: `fixtures/expense_query_mcp.py`

## Native Tool Controls

- `opencode.json` defines a custom primary `audit-eval` agent with an audit QA system prompt in `audit_eval_prompt.txt`.
- Native tools are denied through `permission`, including `read`, `task`, `glob`, `grep`, `edit`, `write`, `bash`, `webfetch`, `websearch`, question, and todo tools.
- The config allows only `policy_query_*` and `expense_query_*` MCP tool namespaces for benchmark tasks.
- `run_eval.py` temporarily adds task-specific `EVAL_TASK_LOG` to both MCP server environments before each task and restores the original config afterward.
