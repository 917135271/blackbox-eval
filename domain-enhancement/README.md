# Securities Expense Audit Domain Enhancement

This directory implements the GATE2 shared-domain layer for Claude Code Best, Codex, OpenClaude, and OpenCode.

## Layout

- `shared-audit-core/`: canonical skills, routing rules, schemas, references, and deterministic control code.
- `control-mcp/`: common `run_audit_subagent` and `submit_audit_result` MCP server.
- `adapters/claude-code-best/`: Claude plugin manifest and Markdown subagents.
- `adapters/codex/`: Codex plugin manifest, TOML subagents, and config fragment.
- `adapters/openclaude/`: OpenClaude plugin directory and Markdown subagents.
- `adapters/opencode/`: OpenCode skills package, subagents, and config fragment.
- `build_adapters.py`: copies the canonical shared core into all four runnable packages and records content hashes.

## Build And Check

Run from the benchmark root:

```powershell
python domain-enhancement/build_adapters.py
python domain-enhancement/control-mcp/audit_control_mcp.py --self-test
python -m unittest tests.test_domain_enhancement
python runner/run_gate2_domain_canary.py
python runner/report_gate2_domain_enhancement.py
```

The generated adapter copies are disposable build output. Edit only `shared-audit-core/` for business behavior and rerun the build. OpenCode's runtime wrapper copies the generated `skills/` directory to `.opencode/skills/`; OpenClaude loads its package through `--plugin-dir`.

## Runtime Contract

Set `AUDIT_TASK_ID`, `AUDIT_WORK_DIR`, `EVAL_EXPENSE_DB`, and `EVAL_POLICY_CORPUS_DIR` for each isolated task. The base evaluation harness supplies `policy_query` and `expense_query`; the plugin supplies `audit_control`.

The agent must call the seven skills in the order defined by `shared-audit-core/references/main_workflow.md` and finish through `submit_audit_result`. Direct final JSON is not the enhanced-group submission path.

Codex uses the stable `multi_agent` V1 tool protocol for this DeepSeek-backed evaluation. The under-development `multi_agent_v2` deferred-tool protocol is disabled because the source Canary showed that it could report a spawn without returning a real child thread through the Responses-to-Chat adapter.
