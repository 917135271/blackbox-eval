# GATE 4 Baseline Report

- generated_at: `2026-07-09T21:27:30`
- runs: `qwen-code=gate4_standard_qwen_v4pro_v1, trae-agent=gate4_standard_trae_v4pro_v2, opencode=gate4_standard_opencode_v4pro_v1, claude-code=gate4_standard_claude_v4pro_v1, codex=gate4_standard_codex_v4pro_v2`
- task_scope: `qwen-code=55 results, trae-agent=55 results, opencode=55 results, claude-code=55 results, codex=55 results`
- failure_detail: `output/gate4_failure_attribution.jsonl`
- scoring: `LLM judge semantic score; format_ok is tracked separately`

## Experiment Setup

- model_endpoint: `https://api.deepseek.com`
- model: `deepseek-v4-pro`
- temperature: `0`
- max_tokens: `4096`
- judge_mode: `llm`
- judge_model: `deepseek-v4-pro`
- judge_require_parseable_json: `False`
- baseline_note: current endpoint is the user-approved DeepSeek cloud API; this is a recorded deviation from the original local-only target.
- timeout_seconds: `900`
- prompt_variants: `precise`

## Candidate Versions

| candidate | version | setup | run_id | started | finished | wall_min |
| --- | --- | --- | --- | --- | --- | ---: |
| qwen-code | 0.19.6 | `candidates/qwen-code/setup.md` | `gate4_standard_qwen_v4pro_v1` | `2026-07-09T14:30:44` | `2026-07-09T15:53:05` | 82.3 |
| trae-agent | 0.1.0 | `candidates/trae-agent/setup.md` | `gate4_standard_trae_v4pro_v2` | `2026-07-09T15:02:39` | `2026-07-09T16:15:14` | 72.6 |
| opencode | 1.17.14 | `candidates/opencode/setup.md` | `gate4_standard_opencode_v4pro_v1` | `2026-07-09T14:41:03` | `2026-07-09T16:11:49` | 90.8 |
| claude-code | 2.8.3 | `candidates/claude-code/setup.md` | `gate4_standard_claude_v4pro_v1` | `2026-07-09T14:41:03` | `2026-07-09T15:56:48` | 75.8 |
| codex | 0.81.0 | `candidates/codex/setup.md` | `gate4_standard_codex_v4pro_v2` | `2026-07-09T15:02:39` | `2026-07-09T16:36:30` | 93.8 |

## Fixture And Dataset Hashes

- `fixtures/policy_query_mcp.py`: `c8af02ea0e5e523e`
- `fixtures/expense_query_mcp.py`: `6f227b5948eb3aa5`
- `fixtures/audit_role_prompt.md`: `e8358b66d81b0fee`
- `fixtures/output_contract.md`: `0a9845820a3abd12`
- `data/evals.json`: `ee51bd3dbabc0a32`
- `data/ground_truth.yaml`: `38bfd3b2eb4f415e`
- `data/expense.db`: `8d6a115d60775736`

## Main Results

| candidate | completed | llm_score | L1 | L2 | L3 | TRAP | format_ok | clean_workdir | artifacts | timeouts | avg_tool_calls | trap_fp_ids |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen-code | 55/55 | 33/55 (60.0%) | 66.7% | 52.0% | 60.0% | 80.0% | 100.0% | 100.0% | 100.0% | 0 | 13.35 | 0 |
| trae-agent | 55/55 | 45/55 (81.8%) | 86.7% | 80.0% | 80.0% | 80.0% | 100.0% | 100.0% | 100.0% | 0 | 5.84 | 0 |
| opencode | 55/55 | 41/55 (74.5%) | 93.3% | 76.0% | 60.0% | 40.0% | 100.0% | 100.0% | 100.0% | 0 | 9.76 | 0 |
| claude-code | 55/55 | 32/55 (58.2%) | 86.7% | 44.0% | 60.0% | 40.0% | 100.0% | 100.0% | 100.0% | 0 | 14.47 | 0 |
| codex | 55/55 | 31/55 (56.4%) | 80.0% | 44.0% | 50.0% | 60.0% | 100.0% | 98.2% | 100.0% | 0 | 17.58 | 0 |

## Variant Results

| candidate | precise |
| --- | ---: |
| qwen-code | 60.0% |
| trae-agent | 81.8% |
| opencode | 74.5% |
| claude-code | 58.2% |
| codex | 56.4% |

## Behavior Summary

| candidate | avg_policy_calls | avg_expense_calls | get_detail_task_rate | invalid_tool_calls | deprecated_citations | contract_warning_tasks | avg_elapsed_s | wall_min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen-code | 4.35 | 9.0 | 80.0% | 0 | 4 | 20 | 88.71 | 82.3 |
| trae-agent | 2.76 | 3.07 | 74.5% | 0 | 8 | 4 | 87.45 | 72.6 |
| opencode | 3.45 | 6.31 | 74.5% | 0 | 8 | 10 | 98.93 | 90.8 |
| claude-code | 5.16 | 9.31 | 78.2% | 0 | 6 | 11 | 83.67 | 75.8 |
| codex | 5.11 | 12.47 | 81.8% | 0 | 8 | 28 | 98.08 | 93.8 |

## Operational Failure Distribution

This distribution prioritizes timeout/format/workdir issues before semantic judge failures; therefore `ok` here can be lower than `llm_score` when an answer is semantically correct but violates the JSON output contract.

| candidate | failure_layers |
| --- | --- |
| qwen-code | `{'ok': 33, 'fact_miss': 3, 'record_id_miss': 7, 'reasoning_or_retrieval_error': 7, 'no_anomaly_false_positive': 4, 'rubric_miss': 1}` |
| trae-agent | `{'ok': 45, 'reasoning_or_retrieval_error': 3, 'record_id_miss': 5, 'fact_miss': 1, 'no_anomaly_false_positive': 1}` |
| opencode | `{'ok': 41, 'record_id_miss': 6, 'no_anomaly_false_positive': 4, 'reasoning_or_retrieval_error': 2, 'fact_miss': 1, 'rubric_miss': 1}` |
| claude-code | `{'ok': 32, 'record_id_miss': 10, 'no_anomaly_false_positive': 10, 'reasoning_or_retrieval_error': 2, 'fact_miss': 1}` |
| codex | `{'ok': 30, 'workdir_changed': 1, 'record_id_miss': 8, 'no_anomaly_false_positive': 13, 'reasoning_or_retrieval_error': 1, 'fact_miss': 1, 'rubric_miss': 1}` |

## Failure Attribution

Each failed row below has a traceable run path and a trajectory line. Full machine-readable details are in the JSONL artifact listed at the top.

| candidate | task | level | variant | score | layer | evidence |
| --- | --- | --- | --- | ---: | --- | --- |
| claude-code | L1-014 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-014/trajectory.json:17` |
| claude-code | L1-015 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-015/trajectory.json:17` |
| claude-code | L2-012 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-012/trajectory.json:17` |
| claude-code | L2-013 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-013/trajectory.json:17` |
| claude-code | L2-014 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-014/trajectory.json:17` |
| claude-code | L2-015 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-015/trajectory.json:17` |
| claude-code | L2-016 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-016/trajectory.json:17` |
| claude-code | L2-017 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-017/trajectory.json:17` |
| claude-code | L2-018 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-018/trajectory.json:17` |
| claude-code | L2-019 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-019/trajectory.json:17` |
| claude-code | L2-020 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-020/trajectory.json:17` |
| claude-code | L2-021 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-021/trajectory.json:17` |
| claude-code | L2-022 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-022/trajectory.json:17` |
| claude-code | L2-023 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-023/trajectory.json:17` |
| claude-code | L2-024 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-024/trajectory.json:17` |
| claude-code | L2-025 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-025/trajectory.json:17` |
| claude-code | L3-002 | L3 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-002/trajectory.json:17` |
| claude-code | L3-003 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-003/trajectory.json:17` |
| claude-code | L3-004 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-004/trajectory.json:17` |
| claude-code | L3-009 | L3 | precise | 0.0 | fact_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-009/trajectory.json:17` |
| claude-code | TRAP-002 | trap | precise | 0.0 | record_id_miss | `runs/gate4_standard_claude_v4pro_v1/claude-code/TRAP-002/trajectory.json:17` |
| claude-code | TRAP-003 | trap | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/TRAP-003/trajectory.json:17` |
| claude-code | TRAP-005 | trap | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_claude_v4pro_v1/claude-code/TRAP-005/trajectory.json:17` |
| codex | L1-007 | L1 | precise | 1.0 | workdir_changed | `runs/gate4_standard_codex_v4pro_v2/codex/L1-007/trajectory.json:542` |
| codex | L1-012 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L1-012/trajectory.json:318` |
| codex | L1-014 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L1-014/trajectory.json:1298` |
| codex | L1-015 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L1-015/trajectory.json:1514` |
| codex | L2-009 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-009/trajectory.json:1148` |
| codex | L2-013 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-013/trajectory.json:488` |
| codex | L2-014 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-014/trajectory.json:1612` |
| codex | L2-015 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-015/trajectory.json:1762` |
| codex | L2-016 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_codex_v4pro_v2/codex/L2-016/trajectory.json:1196` |
| codex | L2-017 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L2-017/trajectory.json:895` |
| codex | L2-018 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L2-018/trajectory.json:810` |
| codex | L2-019 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-019/trajectory.json:836` |
| codex | L2-020 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-020/trajectory.json:1288` |
| codex | L2-021 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-021/trajectory.json:350` |
| codex | L2-022 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-022/trajectory.json:308` |
| codex | L2-023 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-023/trajectory.json:404` |
| codex | L2-024 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-024/trajectory.json:210` |
| codex | L2-025 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L2-025/trajectory.json:212` |
| codex | L3-002 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L3-002/trajectory.json:2591` |
| codex | L3-003 | L3 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/L3-003/trajectory.json:2836` |
| codex | L3-004 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L3-004/trajectory.json:1490` |
| codex | L3-006 | L3 | precise | 0.0 | fact_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L3-006/trajectory.json:242` |
| codex | L3-009 | L3 | precise | 0.0 | rubric_miss | `runs/gate4_standard_codex_v4pro_v2/codex/L3-009/trajectory.json:1366` |
| codex | TRAP-001 | trap | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_codex_v4pro_v2/codex/TRAP-001/trajectory.json:1082` |
| codex | TRAP-004 | trap | precise | 0.0 | record_id_miss | `runs/gate4_standard_codex_v4pro_v2/codex/TRAP-004/trajectory.json:1554` |
| opencode | L1-014 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-014/trajectory.json:860` |
| opencode | L2-014 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-014/trajectory.json:1321` |
| opencode | L2-021 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-021/trajectory.json:180` |
| opencode | L2-022 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-022/trajectory.json:207` |
| opencode | L2-023 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-023/trajectory.json:180` |
| opencode | L2-024 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-024/trajectory.json:180` |
| opencode | L2-025 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-025/trajectory.json:180` |
| opencode | L3-003 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-003/trajectory.json:1049` |
| opencode | L3-004 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-004/trajectory.json:1098` |
| opencode | L3-006 | L3 | precise | 0.0 | fact_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-006/trajectory.json:241` |
| opencode | L3-009 | L3 | precise | 0.0 | rubric_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-009/trajectory.json:1073` |
| opencode | TRAP-001 | trap | precise | 0.0 | record_id_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/TRAP-001/trajectory.json:177` |
| opencode | TRAP-002 | trap | precise | 0.0 | record_id_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/TRAP-002/trajectory.json:1456` |
| opencode | TRAP-004 | trap | precise | 0.0 | record_id_miss | `runs/gate4_standard_opencode_v4pro_v1/opencode/TRAP-004/trajectory.json:1462` |
| qwen-code | L1-009 | L1 | precise | 0.0 | fact_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-009/trajectory.json:6` |
| qwen-code | L1-010 | L1 | precise | 0.0 | fact_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-010/trajectory.json:8` |
| qwen-code | L1-012 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-012/trajectory.json:6` |
| qwen-code | L1-014 | L1 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-014/trajectory.json:6` |
| qwen-code | L1-015 | L1 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-015/trajectory.json:13` |
| qwen-code | L2-011 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-011/trajectory.json:6` |
| qwen-code | L2-015 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-015/trajectory.json:6` |
| qwen-code | L2-016 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-016/trajectory.json:6` |
| qwen-code | L2-017 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-017/trajectory.json:6` |
| qwen-code | L2-018 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-018/trajectory.json:6` |
| qwen-code | L2-019 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-019/trajectory.json:6` |
| qwen-code | L2-020 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-020/trajectory.json:24` |
| qwen-code | L2-021 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-021/trajectory.json:6` |
| qwen-code | L2-022 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-022/trajectory.json:13` |
| qwen-code | L2-023 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-023/trajectory.json:6` |
| qwen-code | L2-024 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-024/trajectory.json:6` |
| qwen-code | L2-025 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-025/trajectory.json:6` |
| qwen-code | L3-003 | L3 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-003/trajectory.json:6` |
| qwen-code | L3-004 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-004/trajectory.json:6` |
| qwen-code | L3-006 | L3 | precise | 0.0 | fact_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-006/trajectory.json:6` |
| qwen-code | L3-009 | L3 | precise | 0.0 | rubric_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-009/trajectory.json:6` |
| qwen-code | TRAP-003 | trap | precise | 0.0 | record_id_miss | `runs/gate4_standard_qwen_v4pro_v1/qwen-code/TRAP-003/trajectory.json:4` |
| trae-agent | L1-009 | L1 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-009/trajectory.json:647` |
| trae-agent | L1-014 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-014/trajectory.json:1674` |
| trae-agent | L2-021 | L2 | precise | 0.0 | fact_miss | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L2-021/trajectory.json:468` |
| trae-agent | L2-022 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L2-022/trajectory.json:521` |
| trae-agent | L2-023 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L2-023/trajectory.json:527` |
| trae-agent | L2-024 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L2-024/trajectory.json:468` |
| trae-agent | L2-025 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L2-025/trajectory.json:468` |
| trae-agent | L3-004 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-004/trajectory.json:32` |
| trae-agent | L3-009 | L3 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-009/trajectory.json:32` |
| trae-agent | TRAP-001 | trap | precise | 0.0 | record_id_miss | `runs/gate4_standard_trae_v4pro_v2/trae-agent/TRAP-001/trajectory.json:1061` |

## Canary And Tool Disable Validation

- GATE2 setup and canary checks are recorded in `output/gate2_candidate_check.md`.
- GATE2 canary status is candidate-specific and recorded in `output/gate2_candidate_check.md` before GATE4.
- GATE4 tool logs contain only `policy_query_mcp` and `expense_query_mcp` server calls when parsed from `tool_calls.jsonl`; see `invalid_tool_calls` in the behavior table.
- Workdir mutation checks are reported as `clean_workdir`; any non-empty `workdir_diff.txt` would be surfaced in failure attribution.

## Acceptance Self Check

- Per-task five-piece artifacts: reported in `artifacts`; required files are stdout.log, tool_calls.jsonl, trajectory.json, result.json, workdir_diff.txt.
- Workdir diff empty: reported in `clean_workdir` and failure attribution.
- Resumability: `run_eval.py` skips completed task directories with existing completed result.json; this was used by the GATE4 runner structure and remains available for interruption recovery.
- Traceability: every LLM judge score comes from `grades.jsonl`; every failure row points back to its per-task run directory and trajectory line.
- `rule_score` remains in `grades.jsonl` for comparison with the previous deterministic scorer.
- Fixture hashes and candidate versions are included above.

## Limitations

- Synthetic data is useful for relative ranking and harness behavior comparison; absolute production readiness needs recalibration on internal real-data labels.
- This is a single baseline pass with no per-candidate tuning beyond the already documented engineering viability fixes.
- The current model endpoint is a cloud DeepSeek-compatible API approved for this trial, not the intended future local model deployment.
- Trae Agent required local engineering patches to become runnable, so it should be read as an engineering-usable baseline rather than a strict unmodified vendor runtime.
