# GATE 3 All Candidates Smoke Report

- generated_at: `2026-07-07T15:34:37`
- model_endpoint: `https://api.deepseek.com`
- model: `deepseek-v4-flash`
- scope: each candidate ran `L1-001`, `L1-002`, `L1-003` with the same prompt variant `precise`.
- baseline_note: current endpoint is the user-approved DeepSeek cloud API, not the original local-only target.

## Candidate Summary

| candidate | run_id | score | format | tool_calls | clean_workdir | artifacts | failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| qwen-code | `gate3_smoke_qwen_v3` | 0/3 | 0% | 1 | 100% | 3/3 | `{'format_failure': 3}` |
| goose | `gate3_smoke_goose_v2` | 2/3 | 67% | 11 | 100% | 3/3 | `{'ok': 2, 'format_failure': 1}` |
| trae-agent | `gate3_smoke_trae` | 0/3 | 0% | 0 | 100% | 3/3 | `{'format_failure': 3}` |
| opencode | `gate3_smoke_opencode` | 0/3 | 0% | 0 | 100% | 3/3 | `{'format_failure': 3}` |

## Task Detail

| candidate | task | score | format | tool_calls | elapsed_s | workdir | failure |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| goose | L1-001 | 1.0 | ok | 4 | 14.41 | clean | ok |
| goose | L1-002 | 1.0 | ok | 2 | 9.28 | clean | ok |
| goose | L1-003 | 0.0 | fail | 5 | 12.54 | clean | format_failure |
| opencode | L1-001 | 0.0 | fail | 0 | 82.96 | clean | format_failure |
| opencode | L1-002 | 0.0 | fail | 0 | 107.91 | clean | format_failure |
| opencode | L1-003 | 0.0 | fail | 0 | 78.29 | clean | format_failure |
| qwen-code | L1-001 | 0.0 | fail | 1 | 24.37 | clean | format_failure |
| qwen-code | L1-002 | 0.0 | fail | 0 | 22.16 | clean | format_failure |
| qwen-code | L1-003 | 0.0 | fail | 0 | 22.81 | clean | format_failure |
| trae-agent | L1-001 | 0.0 | fail | 0 | 28.32 | clean | format_failure |
| trae-agent | L1-002 | 0.0 | fail | 0 | 23.04 | clean | format_failure |
| trae-agent | L1-003 | 0.0 | fail | 0 | 25.57 | clean | format_failure |

## Observed Issues

- `qwen-code`: GATE 3 tasks completed at process level, but the agent still treated the prompt as an environment/setup request and asked for a concrete task instead of answering the already-provided question.
- `opencode`: used native `read` and `task` tools to explore the project/workdir, then asked for a concrete task; it did not call the benchmark MCP tools in these smoke tasks.
- `trae-agent`: answered substantively in console output, but final JSON was not machine-parseable in this run and task-level MCP server logs were empty; its config needs task-specific `EVAL_TASK_LOG` injection before GATE 4.
- `goose`: completed the task chain with MCP logs and clean workdir; `L1-003` failed only because the final JSON string contained an unescaped quote, which the deterministic grader correctly marked as `format_failure`.

## Artifact Notes

- `goose/L1-001`: ok
- `goose/L1-002`: ok
- `goose/L1-003`: ok
- `opencode/L1-001`: ok
- `opencode/L1-002`: ok
- `opencode/L1-003`: ok
- `qwen-code/L1-001`: ok
- `qwen-code/L1-002`: ok
- `qwen-code/L1-003`: ok
- `trae-agent/L1-001`: ok
- `trae-agent/L1-002`: ok
- `trae-agent/L1-003`: ok
