# GATE 3 All Candidates Smoke Report

- generated_at: `2026-07-07T16:05:18`
- model_endpoint: `https://api.deepseek.com`
- model: `deepseek-v4-flash`
- scope: each candidate ran `L1-001`, `L1-002`, `L1-003` with the same prompt variant `precise`.
- baseline_note: current endpoint is the user-approved DeepSeek cloud API, not the original local-only target.

## Candidate Summary

| candidate | run_id | score | format | tool_calls | clean_workdir | artifacts | failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| qwen-code | `gate3_fixed_qwen_v2` | 3/3 | 100% | 10 | 100% | 3/3 | `{'ok': 3}` |
| goose | `gate3_fixed_goose_v2` | 3/3 | 100% | 11 | 100% | 3/3 | `{'ok': 3}` |
| trae-agent | `gate3_fixed_trae_v2` | 3/3 | 100% | 10 | 100% | 3/3 | `{'ok': 3}` |
| opencode | `gate3_fixed_opencode_v2` | 3/3 | 100% | 17 | 100% | 3/3 | `{'ok': 3}` |

## Task Detail

| candidate | task | score | format | tool_calls | elapsed_s | workdir | failure |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| goose | L1-001 | 1.0 | ok | 4 | 16.81 | clean | ok |
| goose | L1-002 | 1.0 | ok | 2 | 9.52 | clean | ok |
| goose | L1-003 | 1.0 | ok | 5 | 19.16 | clean | ok |
| opencode | L1-001 | 1.0 | ok | 5 | 31.59 | clean | ok |
| opencode | L1-002 | 1.0 | ok | 4 | 16.13 | clean | ok |
| opencode | L1-003 | 1.0 | ok | 8 | 23.58 | clean | ok |
| qwen-code | L1-001 | 1.0 | ok | 4 | 24.28 | clean | ok |
| qwen-code | L1-002 | 1.0 | ok | 2 | 18.85 | clean | ok |
| qwen-code | L1-003 | 1.0 | ok | 4 | 23.58 | clean | ok |
| trae-agent | L1-001 | 1.0 | ok | 3 | 23.25 | clean | ok |
| trae-agent | L1-002 | 1.0 | ok | 2 | 20.9 | clean | ok |
| trae-agent | L1-003 | 1.0 | ok | 5 | 21.06 | clean | ok |

## Notes

- `qwen-code`: uses the official headless `--system-prompt` path plus MCP task-log injection. It may still emit explanatory text before a JSON block; the deterministic format metric is based on parseable JSON extraction.
- `opencode`: uses an official custom primary agent plus permission denies for native file/project/shell tools and explicit allows for benchmark MCP namespaces.
- `trae-agent`: requires local engineering patches for YAML `system_prompt`, async cleanup, and `task_done.result` promotion. It is therefore an engineering-usable baseline, not a strict unmodified vendor baseline.
- `goose`: uses extension-based MCP wiring and no candidate source patch.

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
