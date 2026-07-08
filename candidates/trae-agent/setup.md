# trae-agent setup

Status: installed and configured for GATE 2 setup checks.

Patch status: locally patched for engineering usability. This candidate is no longer a strict unmodified black-box baseline unless the patch is reverted.

## Official Sources

- Repository and install instructions: https://github.com/bytedance/trae-agent
- YAML config, custom `base_url`, CLI usage, and MCP examples are documented in the repository README.

## Pinned Version

- Repository: `https://github.com/bytedance/trae-agent.git`
- Commit: `e839e559ac61bdd0e057c375dd1dee391fee797d`
- Install command used inside the pinned checkout: `uv sync --all-extras`
- Runtime entry: `candidates/trae-agent/vendor/trae-agent/.venv/Scripts/trae-cli.exe`
- Verified command: `trae-cli.exe --version`

## Runtime

- Headless command: `trae-cli.exe run <task> --config-file candidates/trae-agent/config/trae_config.yaml --working-dir candidates/trae-agent/workdir`
- Provider: `openrouter` client pointed at the same OpenAI-compatible DeepSeek endpoint
- Base URL: `https://api.deepseek.com`
- Model: `deepseek-v4-flash`
- API key mapping: `OPENROUTER_API_KEY` is populated from `LLM_API_KEY` by the runner.

## MCP

The YAML config registers and allows two MCP servers:

- `policy_query`: `fixtures/policy_query_mcp.py`
- `expense_query`: `fixtures/expense_query_mcp.py`

## Native Tool Controls

- Trae loads default native tools when its configured tool list is empty.
- To avoid that fallback, `agents.trae_agent.tools` contains only `task_done`.
- MCP tools are then appended through `allow_mcp_servers`, so bash/edit tools are not exposed by config.

## Local Patch

Four local patches were applied after the user approved engineering usability fixes:

- `trae_agent/agent/trae_agent.py`: suppresses `asyncio.CancelledError` during MCP stdio cleanup.
- `trae_agent/agent/trae_agent.py` and `trae_agent/utils/config.py`: add YAML `system_prompt` support so this software-engineering agent can run the audit QA benchmark without its default GitHub-issue prompt.
- `trae_agent/tools/task_done_tool.py` and `trae_agent/agent/trae_agent.py`: add an optional `task_done.result` field and promote it to `final_result`, so headless runs can return a machine-parseable benchmark answer.
- `trae_agent/agent/agent.py`: suppresses `asyncio.CancelledError` while awaiting the auxiliary simple-console task.

These patches prevent successful runs from exiting with code 1 during async teardown.
