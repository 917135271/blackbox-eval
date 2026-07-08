# GATE 4 Baseline Report

- generated_at: `2026-07-08T12:55:54`
- runs: `qwen-code=gate4_baseline_qwen_v1, goose=gate4_baseline_goose_v1, trae-agent=gate4_baseline_trae_v1, opencode=gate4_baseline_opencode_v1`
- task_scope: `55 tasks x 3 variants x 1 repeat = 165 results per candidate`
- failure_detail: `output/gate4_failure_attribution.jsonl`
- scoring: `LLM judge semantic score; format_ok is tracked separately`

## Experiment Setup

- model_endpoint: `https://api.deepseek.com`
- model: `deepseek-v4-flash`
- temperature: `0`
- max_tokens: `4096`
- judge_mode: `llm`
- judge_model: `deepseek-v4-flash`
- judge_require_parseable_json: `False`
- baseline_note: current endpoint is the user-approved DeepSeek cloud API; this is a recorded deviation from the original local-only target.
- timeout_seconds: `900`
- prompt_variants: `precise, casual, distracted`

## Candidate Versions

| candidate | version | setup | run_id | started | finished | wall_min |
| --- | --- | --- | --- | --- | --- | ---: |
| qwen-code | 0.19.6 | `candidates/qwen-code/setup.md` | `gate4_baseline_qwen_v1` | `2026-07-07T16:09:39` | `2026-07-08T01:06:40` | 537.0 |
| goose | 1.41.0 | `candidates/goose/setup.md` | `gate4_baseline_goose_v1` | `2026-07-07T16:09:39` | `2026-07-07T17:19:11` | 69.5 |
| trae-agent | 0.1.0 | `candidates/trae-agent/setup.md` | `gate4_baseline_trae_v1` | `2026-07-07T16:09:39` | `2026-07-07T23:32:46` | 443.1 |
| opencode | 1.17.14 | `candidates/opencode/setup.md` | `gate4_baseline_opencode_v1` | `2026-07-07T16:09:39` | `2026-07-07T23:59:48` | 470.1 |

## Fixture And Dataset Hashes

- `fixtures/policy_query_mcp.py`: `7564a27591683f97`
- `fixtures/expense_query_mcp.py`: `c2b2cee2b9ac3973`
- `fixtures/audit_role_prompt.md`: `f91af06484f69773`
- `fixtures/output_contract.md`: `f4d021e4bda746fb`
- `data/evals.json`: `ee51bd3dbabc0a32`
- `data/ground_truth.yaml`: `38bfd3b2eb4f415e`
- `D:/算法LLM/项目篇/东方证券/agent/synth-pipeline/output/data/expense.db`: `8d6a115d60775736`

## Main Results

| candidate | completed | llm_score | L1 | L2 | L3 | TRAP | format_ok | clean_workdir | artifacts | timeouts | avg_tool_calls | trap_fp_ids |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen-code | 165/165 | 65/165 (39.4%) | 62.2% | 30.7% | 43.3% | 6.7% | 74.5% | 100.0% | 100.0% | 2 | 21.25 | 0 |
| goose | 165/165 | 42/165 (25.5%) | 37.8% | 17.3% | 30.0% | 20.0% | 37.0% | 100.0% | 100.0% | 0 | 8.72 | 0 |
| trae-agent | 165/165 | 31/165 (18.8%) | 31.1% | 9.3% | 26.7% | 13.3% | 22.4% | 100.0% | 100.0% | 1 | 12.54 | 0 |
| opencode | 165/165 | 62/165 (37.6%) | 35.6% | 46.7% | 30.0% | 13.3% | 67.9% | 100.0% | 100.0% | 1 | 11.56 | 0 |

## Variant Results

| candidate | precise | casual | distracted |
| --- | ---: | ---: | ---: |
| qwen-code | 41.8% | 47.3% | 29.1% |
| goose | 34.5% | 23.6% | 18.2% |
| trae-agent | 20.0% | 23.6% | 12.7% |
| opencode | 43.6% | 38.2% | 30.9% |

## Behavior Summary

| candidate | avg_policy_calls | avg_expense_calls | get_detail_task_rate | invalid_tool_calls | deprecated_citations | avg_elapsed_s | wall_min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen-code | 5.76 | 15.49 | 75.2% | 0 | 13 | 194.2 | 537.0 |
| goose | 4.07 | 4.65 | 47.9% | 0 | 16 | 25.23 | 69.5 |
| trae-agent | 5.88 | 6.66 | 60.6% | 0 | 7 | 161.07 | 443.1 |
| opencode | 5.24 | 6.32 | 53.3% | 0 | 17 | 170.88 | 470.1 |

## Operational Failure Distribution

This distribution prioritizes timeout/format/workdir issues before semantic judge failures; therefore `ok` here can be lower than `llm_score` when an answer is semantically correct but violates the JSON output contract.

| candidate | failure_layers |
| --- | --- |
| qwen-code | `{'ok': 55, 'fact_miss': 6, 'no_anomaly_false_positive': 24, 'format_failure': 40, 'reasoning_or_retrieval_error': 17, 'record_id_miss': 21, 'timeout': 2}` |
| goose | `{'ok': 42, 'format_failure': 104, 'reasoning_or_retrieval_error': 8, 'record_id_miss': 3, 'no_anomaly_false_positive': 2, 'fact_miss': 5, 'rubric_miss': 1}` |
| trae-agent | `{'ok': 29, 'format_failure': 127, 'fact_miss': 3, 'no_anomaly_false_positive': 2, 'reasoning_or_retrieval_error': 2, 'record_id_miss': 1, 'timeout': 1}` |
| opencode | `{'ok': 46, 'fact_miss': 12, 'format_failure': 53, 'no_anomaly_false_positive': 19, 'reasoning_or_retrieval_error': 10, 'record_id_miss': 24, 'timeout': 1}` |

## Failure Attribution

Each failed row below has a traceable run path and a trajectory line. Full machine-readable details are in the JSONL artifact listed at the top.

| candidate | task | level | variant | score | layer | evidence |
| --- | --- | --- | --- | ---: | --- | --- |
| goose | L1-006 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-006__casual__r1/trajectory.json:547` |
| goose | L1-006 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-006__distracted__r1/trajectory.json:633` |
| goose | L1-007 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-007__casual__r1/trajectory.json:584` |
| goose | L1-007 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-007__distracted__r1/trajectory.json:631` |
| goose | L1-007 | L1 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L1-007/trajectory.json:435` |
| goose | L1-008 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-008__casual__r1/trajectory.json:543` |
| goose | L1-008 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-008__distracted__r1/trajectory.json:586` |
| goose | L1-008 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-008/trajectory.json:539` |
| goose | L1-009 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-009__casual__r1/trajectory.json:589` |
| goose | L1-009 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-009__distracted__r1/trajectory.json:803` |
| goose | L1-009 | L1 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L1-009/trajectory.json:298` |
| goose | L1-010 | L1 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L1-010__casual__r1/trajectory.json:433` |
| goose | L1-010 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-010__distracted__r1/trajectory.json:556` |
| goose | L1-011 | L1 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L1-011__casual__r1/trajectory.json:293` |
| goose | L1-011 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-011__distracted__r1/trajectory.json:629` |
| goose | L1-011 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-011/trajectory.json:497` |
| goose | L1-012 | L1 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_goose_v1/goose/L1-012__casual__r1/trajectory.json:207` |
| goose | L1-012 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-012__distracted__r1/trajectory.json:533` |
| goose | L1-012 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-012/trajectory.json:629` |
| goose | L1-013 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-013__casual__r1/trajectory.json:496` |
| goose | L1-013 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-013__distracted__r1/trajectory.json:418` |
| goose | L1-013 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-013/trajectory.json:495` |
| goose | L1-014 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-014__casual__r1/trajectory.json:538` |
| goose | L1-014 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-014__distracted__r1/trajectory.json:708` |
| goose | L1-014 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-014/trajectory.json:1097` |
| goose | L1-015 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-015__casual__r1/trajectory.json:584` |
| goose | L1-015 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-015__distracted__r1/trajectory.json:500` |
| goose | L1-015 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L1-015/trajectory.json:542` |
| goose | L2-001 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-001__casual__r1/trajectory.json:327` |
| goose | L2-002 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-002__casual__r1/trajectory.json:349` |
| goose | L2-002 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-002__distracted__r1/trajectory.json:537` |
| goose | L2-002 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-002/trajectory.json:316` |
| goose | L2-003 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-003__distracted__r1/trajectory.json:579` |
| goose | L2-004 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-004__casual__r1/trajectory.json:290` |
| goose | L2-004 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-004__distracted__r1/trajectory.json:750` |
| goose | L2-004 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-004/trajectory.json:428` |
| goose | L2-005 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-005__distracted__r1/trajectory.json:600` |
| goose | L2-006 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-006__casual__r1/trajectory.json:225` |
| goose | L2-006 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-006/trajectory.json:589` |
| goose | L2-007 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_goose_v1/goose/L2-007__casual__r1/trajectory.json:627` |
| goose | L2-007 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-007__distracted__r1/trajectory.json:351` |
| goose | L2-008 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-008__casual__r1/trajectory.json:625` |
| goose | L2-008 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-008__distracted__r1/trajectory.json:667` |
| goose | L2-008 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-008/trajectory.json:630` |
| goose | L2-009 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-009__casual__r1/trajectory.json:972` |
| goose | L2-009 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-009__distracted__r1/trajectory.json:401` |
| goose | L2-009 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L2-009/trajectory.json:672` |
| goose | L2-010 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_goose_v1/goose/L2-010__casual__r1/trajectory.json:729` |
| goose | L2-010 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-010__distracted__r1/trajectory.json:345` |
| goose | L2-010 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-010/trajectory.json:967` |
| goose | L2-011 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-011__casual__r1/trajectory.json:372` |
| goose | L2-011 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-011__distracted__r1/trajectory.json:331` |
| goose | L2-011 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-011/trajectory.json:579` |
| goose | L2-012 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-012__casual__r1/trajectory.json:415` |
| goose | L2-012 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-012__distracted__r1/trajectory.json:517` |
| goose | L2-012 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-012/trajectory.json:580` |
| goose | L2-013 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-013__casual__r1/trajectory.json:1005` |
| goose | L2-013 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-013__distracted__r1/trajectory.json:883` |
| goose | L2-013 | L2 | precise | 0.0 | fact_miss | `runs/gate4_baseline_goose_v1/goose/L2-013/trajectory.json:579` |
| goose | L2-014 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-014__casual__r1/trajectory.json:374` |
| goose | L2-014 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-014__distracted__r1/trajectory.json:284` |
| goose | L2-015 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-015__casual__r1/trajectory.json:458` |
| goose | L2-015 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-015__distracted__r1/trajectory.json:833` |
| goose | L2-015 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-015/trajectory.json:628` |
| goose | L2-016 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-016__casual__r1/trajectory.json:270` |
| goose | L2-016 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-016__distracted__r1/trajectory.json:551` |
| goose | L2-016 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-016/trajectory.json:458` |
| goose | L2-017 | L2 | casual | 0.0 | fact_miss | `runs/gate4_baseline_goose_v1/goose/L2-017__casual__r1/trajectory.json:438` |
| goose | L2-017 | L2 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_goose_v1/goose/L2-017__distracted__r1/trajectory.json:558` |
| goose | L2-017 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-017/trajectory.json:366` |
| goose | L2-018 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-018__casual__r1/trajectory.json:370` |
| goose | L2-018 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-018__distracted__r1/trajectory.json:412` |
| goose | L2-018 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-018/trajectory.json:713` |
| goose | L2-019 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-019__casual__r1/trajectory.json:224` |
| goose | L2-019 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-019__distracted__r1/trajectory.json:588` |
| goose | L2-019 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L2-019/trajectory.json:462` |
| goose | L2-020 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-020__casual__r1/trajectory.json:535` |
| goose | L2-020 | L2 | distracted | 0.0 | fact_miss | `runs/gate4_baseline_goose_v1/goose/L2-020__distracted__r1/trajectory.json:366` |
| goose | L2-020 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-020/trajectory.json:185` |
| goose | L2-021 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-021__casual__r1/trajectory.json:374` |
| goose | L2-021 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-021__distracted__r1/trajectory.json:464` |
| goose | L2-022 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-022__casual__r1/trajectory.json:229` |
| goose | L2-022 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-022__distracted__r1/trajectory.json:583` |
| goose | L2-022 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L2-022/trajectory.json:250` |
| goose | L2-023 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-023__distracted__r1/trajectory.json:539` |
| goose | L2-024 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-024__casual__r1/trajectory.json:583` |
| goose | L2-024 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-024__distracted__r1/trajectory.json:545` |
| goose | L2-024 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_goose_v1/goose/L2-024/trajectory.json:418` |
| goose | L2-025 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-025__casual__r1/trajectory.json:433` |
| goose | L2-025 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L2-025__distracted__r1/trajectory.json:286` |
| goose | L3-001 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-001__casual__r1/trajectory.json:964` |
| goose | L3-001 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-001__distracted__r1/trajectory.json:451` |
| goose | L3-001 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-001/trajectory.json:544` |
| goose | L3-002 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-002__casual__r1/trajectory.json:227` |
| goose | L3-002 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-002__distracted__r1/trajectory.json:753` |
| goose | L3-002 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-002/trajectory.json:584` |
| goose | L3-003 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-003__casual__r1/trajectory.json:1180` |
| goose | L3-003 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-003__distracted__r1/trajectory.json:1024` |
| goose | L3-003 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-003/trajectory.json:288` |
| goose | L3-004 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-004__casual__r1/trajectory.json:753` |
| goose | L3-004 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-004__distracted__r1/trajectory.json:973` |
| goose | L3-004 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-004/trajectory.json:225` |
| goose | L3-005 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-005__casual__r1/trajectory.json:878` |
| goose | L3-005 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-005__distracted__r1/trajectory.json:493` |
| goose | L3-005 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-005/trajectory.json:1224` |
| goose | L3-006 | L3 | casual | 0.0 | fact_miss | `runs/gate4_baseline_goose_v1/goose/L3-006__casual__r1/trajectory.json:253` |
| goose | L3-006 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-006__distracted__r1/trajectory.json:628` |
| goose | L3-009 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-009__casual__r1/trajectory.json:353` |
| goose | L3-009 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-009__distracted__r1/trajectory.json:1177` |
| goose | L3-009 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/L3-009/trajectory.json:1030` |
| goose | L3-010 | L3 | casual | 0.0 | rubric_miss | `runs/gate4_baseline_goose_v1/goose/L3-010__casual__r1/trajectory.json:337` |
| goose | TRAP-001 | trap | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-001__casual__r1/trajectory.json:578` |
| goose | TRAP-001 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-001__distracted__r1/trajectory.json:125` |
| goose | TRAP-001 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-001/trajectory.json:532` |
| goose | TRAP-002 | trap | casual | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-002__casual__r1/trajectory.json:716` |
| goose | TRAP-002 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-002__distracted__r1/trajectory.json:620` |
| goose | TRAP-002 | trap | precise | 0.0 | fact_miss | `runs/gate4_baseline_goose_v1/goose/TRAP-002/trajectory.json:248` |
| goose | TRAP-003 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-003__distracted__r1/trajectory.json:627` |
| goose | TRAP-003 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_goose_v1/goose/TRAP-003/trajectory.json:307` |
| goose | TRAP-004 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-004__distracted__r1/trajectory.json:185` |
| goose | TRAP-004 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-004/trajectory.json:535` |
| goose | TRAP-005 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-005__distracted__r1/trajectory.json:714` |
| goose | TRAP-005 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_goose_v1/goose/TRAP-005/trajectory.json:581` |
| opencode | L1-003 | L1 | casual | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L1-003__casual__r1/trajectory.json:271` |
| opencode | L1-006 | L1 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L1-006__distracted__r1/trajectory.json:679` |
| opencode | L1-006 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-006/trajectory.json:456` |
| opencode | L1-007 | L1 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L1-007__casual__r1/trajectory.json:549` |
| opencode | L1-007 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-007__distracted__r1/trajectory.json:602` |
| opencode | L1-007 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-007/trajectory.json:603` |
| opencode | L1-008 | L1 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L1-008__casual__r1/trajectory.json:567` |
| opencode | L1-008 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-008__distracted__r1/trajectory.json:590` |
| opencode | L1-008 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-008/trajectory.json:492` |
| opencode | L1-009 | L1 | distracted | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L1-009__distracted__r1/trajectory.json:572` |
| opencode | L1-009 | L1 | precise | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L1-009/trajectory.json:485` |
| opencode | L1-010 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-010__casual__r1/trajectory.json:487` |
| opencode | L1-010 | L1 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L1-010__distracted__r1/trajectory.json:546` |
| opencode | L1-010 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-010/trajectory.json:596` |
| opencode | L1-011 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-011__casual__r1/trajectory.json:515` |
| opencode | L1-011 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-011__distracted__r1/trajectory.json:800` |
| opencode | L1-011 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-011/trajectory.json:489` |
| opencode | L1-012 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-012__casual__r1/trajectory.json:575` |
| opencode | L1-012 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-012__distracted__r1/trajectory.json:711` |
| opencode | L1-012 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-012/trajectory.json:459` |
| opencode | L1-013 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-013__casual__r1/trajectory.json:719` |
| opencode | L1-013 | L1 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L1-013__distracted__r1/trajectory.json:771` |
| opencode | L1-013 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-013/trajectory.json:576` |
| opencode | L1-014 | L1 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L1-014__casual__r1/trajectory.json:487` |
| opencode | L1-014 | L1 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L1-014__distracted__r1/trajectory.json:876` |
| opencode | L1-014 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L1-014/trajectory.json:566` |
| opencode | L1-015 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-015__casual__r1/trajectory.json:516` |
| opencode | L1-015 | L1 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L1-015__distracted__r1/trajectory.json:543` |
| opencode | L1-015 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L1-015/trajectory.json:458` |
| opencode | L2-001 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-001__casual__r1/trajectory.json:511` |
| opencode | L2-001 | L2 | distracted | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-001__distracted__r1/trajectory.json:481` |
| opencode | L2-001 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-001/trajectory.json:516` |
| opencode | L2-002 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-002__casual__r1/trajectory.json:420` |
| opencode | L2-002 | L2 | distracted | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-002__distracted__r1/trajectory.json:538` |
| opencode | L2-003 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-003__casual__r1/trajectory.json:542` |
| opencode | L2-003 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-003/trajectory.json:477` |
| opencode | L2-004 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-004__casual__r1/trajectory.json:486` |
| opencode | L2-004 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-004__distracted__r1/trajectory.json:676` |
| opencode | L2-005 | L2 | distracted | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L2-005__distracted__r1/trajectory.json:567` |
| opencode | L2-006 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-006__casual__r1/trajectory.json:569` |
| opencode | L2-006 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-006__distracted__r1/trajectory.json:541` |
| opencode | L2-007 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-007__casual__r1/trajectory.json:627` |
| opencode | L2-007 | L2 | distracted | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-007__distracted__r1/trajectory.json:545` |
| opencode | L2-009 | L2 | distracted | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-009__distracted__r1/trajectory.json:511` |
| opencode | L2-009 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-009/trajectory.json:605` |
| opencode | L2-010 | L2 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L2-010__casual__r1/trajectory.json:572` |
| opencode | L2-010 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-010__distracted__r1/trajectory.json:709` |
| opencode | L2-011 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-011__casual__r1/trajectory.json:677` |
| opencode | L2-011 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-011__distracted__r1/trajectory.json:568` |
| opencode | L2-011 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-011/trajectory.json:547` |
| opencode | L2-012 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-012__casual__r1/trajectory.json:734` |
| opencode | L2-012 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-012__distracted__r1/trajectory.json:454` |
| opencode | L2-013 | L2 | distracted | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-013__distracted__r1/trajectory.json:455` |
| opencode | L2-013 | L2 | precise | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-013/trajectory.json:624` |
| opencode | L2-014 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-014__casual__r1/trajectory.json:964` |
| opencode | L2-014 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-014__distracted__r1/trajectory.json:684` |
| opencode | L2-015 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-015__casual__r1/trajectory.json:732` |
| opencode | L2-015 | L2 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-015__distracted__r1/trajectory.json:454` |
| opencode | L2-016 | L2 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-016__casual__r1/trajectory.json:450` |
| opencode | L2-016 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-016__distracted__r1/trajectory.json:569` |
| opencode | L2-017 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-017__casual__r1/trajectory.json:574` |
| opencode | L2-017 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-017__distracted__r1/trajectory.json:570` |
| opencode | L2-017 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L2-017/trajectory.json:583` |
| opencode | L2-018 | L2 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-018__casual__r1/trajectory.json:570` |
| opencode | L2-018 | L2 | distracted | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-018__distracted__r1/trajectory.json:483` |
| opencode | L2-019 | L2 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L2-019__casual__r1/trajectory.json:486` |
| opencode | L2-019 | L2 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-019__distracted__r1/trajectory.json:512` |
| opencode | L2-019 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-019/trajectory.json:690` |
| opencode | L2-020 | L2 | casual | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-020__casual__r1/trajectory.json:457` |
| opencode | L2-020 | L2 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-020__distracted__r1/trajectory.json:598` |
| opencode | L2-020 | L2 | precise | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-020/trajectory.json:485` |
| opencode | L2-021 | L2 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-021__casual__r1/trajectory.json:570` |
| opencode | L2-021 | L2 | distracted | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L2-021__distracted__r1/trajectory.json:604` |
| opencode | L2-021 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-021/trajectory.json:488` |
| opencode | L2-022 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-022__casual__r1/trajectory.json:738` |
| opencode | L2-022 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-022__distracted__r1/trajectory.json:658` |
| opencode | L2-022 | L2 | precise | 0.0 | timeout | `runs/gate4_baseline_opencode_v1/opencode/L2-022/trajectory.json:653` |
| opencode | L2-023 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-023__casual__r1/trajectory.json:652` |
| opencode | L2-023 | L2 | distracted | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-023__distracted__r1/trajectory.json:457` |
| opencode | L2-023 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-023/trajectory.json:627` |
| opencode | L2-024 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L2-024/trajectory.json:458` |
| opencode | L2-025 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L2-025__casual__r1/trajectory.json:353` |
| opencode | L2-025 | L2 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-025__distracted__r1/trajectory.json:483` |
| opencode | L2-025 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L2-025/trajectory.json:516` |
| opencode | L3-001 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-001__casual__r1/trajectory.json:655` |
| opencode | L3-001 | L3 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-001__distracted__r1/trajectory.json:679` |
| opencode | L3-001 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-001/trajectory.json:709` |
| opencode | L3-002 | L3 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L3-002__casual__r1/trajectory.json:628` |
| opencode | L3-002 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-002__distracted__r1/trajectory.json:906` |
| opencode | L3-002 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-002/trajectory.json:583` |
| opencode | L3-003 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-003__casual__r1/trajectory.json:827` |
| opencode | L3-003 | L3 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/L3-003__distracted__r1/trajectory.json:1218` |
| opencode | L3-003 | L3 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_opencode_v1/opencode/L3-003/trajectory.json:1230` |
| opencode | L3-004 | L3 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-004__casual__r1/trajectory.json:1197` |
| opencode | L3-004 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-004__distracted__r1/trajectory.json:996` |
| opencode | L3-004 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-004/trajectory.json:1171` |
| opencode | L3-005 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-005__casual__r1/trajectory.json:624` |
| opencode | L3-005 | L3 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-005__distracted__r1/trajectory.json:883` |
| opencode | L3-005 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-005/trajectory.json:763` |
| opencode | L3-006 | L3 | casual | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-006__casual__r1/trajectory.json:421` |
| opencode | L3-006 | L3 | precise | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-006/trajectory.json:391` |
| opencode | L3-009 | L3 | casual | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-009__casual__r1/trajectory.json:1069` |
| opencode | L3-009 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-009__distracted__r1/trajectory.json:1161` |
| opencode | L3-009 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-009/trajectory.json:1027` |
| opencode | L3-010 | L3 | casual | 1.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/L3-010__casual__r1/trajectory.json:607` |
| opencode | L3-010 | L3 | distracted | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/L3-010__distracted__r1/trajectory.json:421` |
| opencode | TRAP-001 | trap | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/TRAP-001__casual__r1/trajectory.json:514` |
| opencode | TRAP-001 | trap | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/TRAP-001__distracted__r1/trajectory.json:1104` |
| opencode | TRAP-001 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/TRAP-001/trajectory.json:388` |
| opencode | TRAP-002 | trap | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/TRAP-002__casual__r1/trajectory.json:686` |
| opencode | TRAP-002 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_opencode_v1/opencode/TRAP-002__distracted__r1/trajectory.json:1252` |
| opencode | TRAP-002 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/TRAP-002/trajectory.json:457` |
| opencode | TRAP-003 | trap | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/TRAP-003__distracted__r1/trajectory.json:1312` |
| opencode | TRAP-003 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/TRAP-003/trajectory.json:513` |
| opencode | TRAP-004 | trap | distracted | 0.0 | fact_miss | `runs/gate4_baseline_opencode_v1/opencode/TRAP-004__distracted__r1/trajectory.json:548` |
| opencode | TRAP-004 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/TRAP-004/trajectory.json:602` |
| opencode | TRAP-005 | trap | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_opencode_v1/opencode/TRAP-005__casual__r1/trajectory.json:517` |
| opencode | TRAP-005 | trap | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/TRAP-005__distracted__r1/trajectory.json:807` |
| opencode | TRAP-005 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_opencode_v1/opencode/TRAP-005/trajectory.json:488` |
| qwen-code | L1-003 | L1 | casual | 0.0 | fact_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-003__casual__r1/trajectory.json:3` |
| qwen-code | L1-004 | L1 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L1-004__distracted__r1/trajectory.json:29` |
| qwen-code | L1-006 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L1-006__distracted__r1/trajectory.json:4` |
| qwen-code | L1-007 | L1 | casual | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L1-007__casual__r1/trajectory.json:6` |
| qwen-code | L1-007 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L1-007__distracted__r1/trajectory.json:6` |
| qwen-code | L1-008 | L1 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L1-008__distracted__r1/trajectory.json:6` |
| qwen-code | L1-009 | L1 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L1-009/trajectory.json:5` |
| qwen-code | L1-010 | L1 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L1-010__distracted__r1/trajectory.json:6` |
| qwen-code | L1-010 | L1 | precise | 0.0 | fact_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-010/trajectory.json:5` |
| qwen-code | L1-011 | L1 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-011__distracted__r1/trajectory.json:5` |
| qwen-code | L1-011 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L1-011/trajectory.json:4` |
| qwen-code | L1-012 | L1 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-012__distracted__r1/trajectory.json:38` |
| qwen-code | L1-012 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L1-012/trajectory.json:8` |
| qwen-code | L1-013 | L1 | distracted | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L1-013__distracted__r1/trajectory.json:6` |
| qwen-code | L1-013 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-013/trajectory.json:6` |
| qwen-code | L1-014 | L1 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L1-014__casual__r1/trajectory.json:3` |
| qwen-code | L1-014 | L1 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-014__distracted__r1/trajectory.json:5` |
| qwen-code | L1-014 | L1 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-014/trajectory.json:5` |
| qwen-code | L1-015 | L1 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L1-015__distracted__r1/trajectory.json:5` |
| qwen-code | L2-001 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-001/trajectory.json:13` |
| qwen-code | L2-002 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-002__distracted__r1/trajectory.json:8` |
| qwen-code | L2-003 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-003__distracted__r1/trajectory.json:7` |
| qwen-code | L2-004 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-004__casual__r1/trajectory.json:21` |
| qwen-code | L2-004 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-004/trajectory.json:6` |
| qwen-code | L2-005 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-005__casual__r1/trajectory.json:6` |
| qwen-code | L2-005 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-005__distracted__r1/trajectory.json:6` |
| qwen-code | L2-006 | L2 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-006__casual__r1/trajectory.json:8` |
| qwen-code | L2-006 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-006/trajectory.json:6` |
| qwen-code | L2-007 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-007__casual__r1/trajectory.json:6` |
| qwen-code | L2-007 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-007__distracted__r1/trajectory.json:14` |
| qwen-code | L2-007 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-007/trajectory.json:6` |
| qwen-code | L2-009 | L2 | casual | 0.0 | timeout | `runs/gate4_baseline_qwen_v1/qwen-code/L2-009__casual__r1/trajectory.json:1` |
| qwen-code | L2-009 | L2 | distracted | 0.0 | timeout | `runs/gate4_baseline_qwen_v1/qwen-code/L2-009__distracted__r1/trajectory.json:16` |
| qwen-code | L2-010 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-010__casual__r1/trajectory.json:6` |
| qwen-code | L2-010 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-010__distracted__r1/trajectory.json:4` |
| qwen-code | L2-010 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-010/trajectory.json:6` |
| qwen-code | L2-011 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-011__casual__r1/trajectory.json:6` |
| qwen-code | L2-011 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-011__distracted__r1/trajectory.json:6` |
| qwen-code | L2-011 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-011/trajectory.json:6` |
| qwen-code | L2-012 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-012__casual__r1/trajectory.json:6` |
| qwen-code | L2-012 | L2 | distracted | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-012__distracted__r1/trajectory.json:15` |
| qwen-code | L2-012 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-012/trajectory.json:6` |
| qwen-code | L2-013 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-013__casual__r1/trajectory.json:8` |
| qwen-code | L2-013 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-013__distracted__r1/trajectory.json:6` |
| qwen-code | L2-013 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-013/trajectory.json:7` |
| qwen-code | L2-014 | L2 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-014__casual__r1/trajectory.json:14` |
| qwen-code | L2-014 | L2 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-014__distracted__r1/trajectory.json:6` |
| qwen-code | L2-014 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-014/trajectory.json:7` |
| qwen-code | L2-015 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-015__casual__r1/trajectory.json:15` |
| qwen-code | L2-015 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-015__distracted__r1/trajectory.json:12` |
| qwen-code | L2-015 | L2 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-015/trajectory.json:6` |
| qwen-code | L2-016 | L2 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-016__casual__r1/trajectory.json:6` |
| qwen-code | L2-016 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-016__distracted__r1/trajectory.json:6` |
| qwen-code | L2-016 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-016/trajectory.json:6` |
| qwen-code | L2-017 | L2 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-017__casual__r1/trajectory.json:8` |
| qwen-code | L2-017 | L2 | distracted | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-017__distracted__r1/trajectory.json:3` |
| qwen-code | L2-017 | L2 | precise | 0.0 | fact_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-017/trajectory.json:6` |
| qwen-code | L2-018 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-018__casual__r1/trajectory.json:6` |
| qwen-code | L2-018 | L2 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-018__distracted__r1/trajectory.json:6` |
| qwen-code | L2-019 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-019__casual__r1/trajectory.json:6` |
| qwen-code | L2-019 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-019__distracted__r1/trajectory.json:6` |
| qwen-code | L2-019 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-019/trajectory.json:6` |
| qwen-code | L2-020 | L2 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-020__casual__r1/trajectory.json:6` |
| qwen-code | L2-020 | L2 | distracted | 0.0 | fact_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-020__distracted__r1/trajectory.json:6` |
| qwen-code | L2-020 | L2 | precise | 0.0 | fact_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-020/trajectory.json:6` |
| qwen-code | L2-021 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-021__casual__r1/trajectory.json:6` |
| qwen-code | L2-021 | L2 | distracted | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-021__distracted__r1/trajectory.json:6` |
| qwen-code | L2-021 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-021/trajectory.json:9` |
| qwen-code | L2-022 | L2 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L2-022__casual__r1/trajectory.json:6` |
| qwen-code | L2-022 | L2 | distracted | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-022__distracted__r1/trajectory.json:6` |
| qwen-code | L2-022 | L2 | precise | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-022/trajectory.json:6` |
| qwen-code | L2-023 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-023/trajectory.json:4` |
| qwen-code | L2-024 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-024__casual__r1/trajectory.json:6` |
| qwen-code | L2-024 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L2-024/trajectory.json:34` |
| qwen-code | L2-025 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-025__casual__r1/trajectory.json:6` |
| qwen-code | L2-025 | L2 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L2-025__distracted__r1/trajectory.json:6` |
| qwen-code | L2-025 | L2 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L2-025/trajectory.json:6` |
| qwen-code | L3-001 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-001__casual__r1/trajectory.json:6` |
| qwen-code | L3-001 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-001__distracted__r1/trajectory.json:6` |
| qwen-code | L3-001 | L3 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L3-001/trajectory.json:13` |
| qwen-code | L3-002 | L3 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L3-002__casual__r1/trajectory.json:6` |
| qwen-code | L3-002 | L3 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L3-002__distracted__r1/trajectory.json:8` |
| qwen-code | L3-002 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L3-002/trajectory.json:14` |
| qwen-code | L3-003 | L3 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L3-003__casual__r1/trajectory.json:6` |
| qwen-code | L3-003 | L3 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/L3-003__distracted__r1/trajectory.json:6` |
| qwen-code | L3-003 | L3 | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/L3-003/trajectory.json:113` |
| qwen-code | L3-004 | L3 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L3-004__casual__r1/trajectory.json:11` |
| qwen-code | L3-004 | L3 | distracted | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L3-004__distracted__r1/trajectory.json:6` |
| qwen-code | L3-004 | L3 | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L3-004/trajectory.json:10` |
| qwen-code | L3-005 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-005__distracted__r1/trajectory.json:6` |
| qwen-code | L3-006 | L3 | casual | 0.0 | fact_miss | `runs/gate4_baseline_qwen_v1/qwen-code/L3-006__casual__r1/trajectory.json:3` |
| qwen-code | L3-009 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-009__casual__r1/trajectory.json:6` |
| qwen-code | L3-009 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-009__distracted__r1/trajectory.json:14` |
| qwen-code | L3-009 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-009/trajectory.json:20` |
| qwen-code | L3-010 | L3 | casual | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-010__casual__r1/trajectory.json:6` |
| qwen-code | L3-010 | L3 | distracted | 1.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/L3-010__distracted__r1/trajectory.json:6` |
| qwen-code | TRAP-001 | trap | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-001__distracted__r1/trajectory.json:6` |
| qwen-code | TRAP-001 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-001/trajectory.json:3` |
| qwen-code | TRAP-002 | trap | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-002__casual__r1/trajectory.json:6` |
| qwen-code | TRAP-002 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-002__distracted__r1/trajectory.json:6` |
| qwen-code | TRAP-002 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-002/trajectory.json:3` |
| qwen-code | TRAP-003 | trap | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-003__casual__r1/trajectory.json:6` |
| qwen-code | TRAP-003 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-003__distracted__r1/trajectory.json:16` |
| qwen-code | TRAP-003 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-003/trajectory.json:3` |
| qwen-code | TRAP-004 | trap | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-004__casual__r1/trajectory.json:6` |
| qwen-code | TRAP-004 | trap | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-004__distracted__r1/trajectory.json:6` |
| qwen-code | TRAP-004 | trap | precise | 0.0 | record_id_miss | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-004/trajectory.json:3` |
| qwen-code | TRAP-005 | trap | casual | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-005__casual__r1/trajectory.json:6` |
| qwen-code | TRAP-005 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-005__distracted__r1/trajectory.json:6` |
| qwen-code | TRAP-005 | trap | precise | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-005/trajectory.json:3` |
| trae-agent | L1-003 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-003__distracted__r1/trajectory.json:566` |
| trae-agent | L1-006 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-006__casual__r1/trajectory.json:1027` |
| trae-agent | L1-006 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-006__distracted__r1/trajectory.json:1236` |
| trae-agent | L1-006 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-006/trajectory.json:971` |
| trae-agent | L1-007 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-007__casual__r1/trajectory.json:971` |
| trae-agent | L1-007 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-007__distracted__r1/trajectory.json:1251` |
| trae-agent | L1-007 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-007/trajectory.json:1299` |
| trae-agent | L1-008 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-008__casual__r1/trajectory.json:983` |
| trae-agent | L1-008 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-008__distracted__r1/trajectory.json:1080` |
| trae-agent | L1-008 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-008/trajectory.json:1080` |
| trae-agent | L1-009 | L1 | casual | 0.0 | fact_miss | `runs/gate4_baseline_trae_v1/trae-agent/L1-009__casual__r1/trajectory.json:972` |
| trae-agent | L1-009 | L1 | distracted | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_trae_v1/trae-agent/L1-009__distracted__r1/trajectory.json:1284` |
| trae-agent | L1-009 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-009/trajectory.json:968` |
| trae-agent | L1-010 | L1 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_trae_v1/trae-agent/L1-010__casual__r1/trajectory.json:892` |
| trae-agent | L1-010 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-010__distracted__r1/trajectory.json:1080` |
| trae-agent | L1-010 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-010/trajectory.json:915` |
| trae-agent | L1-011 | L1 | casual | 0.0 | record_id_miss | `runs/gate4_baseline_trae_v1/trae-agent/L1-011__casual__r1/trajectory.json:898` |
| trae-agent | L1-011 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-011__distracted__r1/trajectory.json:912` |
| trae-agent | L1-011 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-011/trajectory.json:1192` |
| trae-agent | L1-012 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-012__casual__r1/trajectory.json:962` |
| trae-agent | L1-012 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-012__distracted__r1/trajectory.json:945` |
| trae-agent | L1-012 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-012/trajectory.json:1239` |
| trae-agent | L1-013 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-013__casual__r1/trajectory.json:1791` |
| trae-agent | L1-013 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-013__distracted__r1/trajectory.json:1062` |
| trae-agent | L1-013 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-013/trajectory.json:1192` |
| trae-agent | L1-014 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-014__casual__r1/trajectory.json:1593` |
| trae-agent | L1-014 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-014__distracted__r1/trajectory.json:1439` |
| trae-agent | L1-014 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-014/trajectory.json:1790` |
| trae-agent | L1-015 | L1 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-015__casual__r1/trajectory.json:1133` |
| trae-agent | L1-015 | L1 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-015__distracted__r1/trajectory.json:1183` |
| trae-agent | L1-015 | L1 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L1-015/trajectory.json:1089` |
| trae-agent | L2-001 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-001__casual__r1/trajectory.json:959` |
| trae-agent | L2-001 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-001__distracted__r1/trajectory.json:1048` |
| trae-agent | L2-001 | L2 | precise | 1.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-001/trajectory.json:833` |
| trae-agent | L2-002 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-002__distracted__r1/trajectory.json:1098` |
| trae-agent | L2-002 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-002/trajectory.json:968` |
| trae-agent | L2-003 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-003__casual__r1/trajectory.json:1018` |
| trae-agent | L2-003 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-003__distracted__r1/trajectory.json:1188` |
| trae-agent | L2-003 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-003/trajectory.json:965` |
| trae-agent | L2-004 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-004__distracted__r1/trajectory.json:1007` |
| trae-agent | L2-004 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-004/trajectory.json:1169` |
| trae-agent | L2-005 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-005__distracted__r1/trajectory.json:1038` |
| trae-agent | L2-006 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-006__casual__r1/trajectory.json:1339` |
| trae-agent | L2-006 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-006__distracted__r1/trajectory.json:1260` |
| trae-agent | L2-006 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-006/trajectory.json:1230` |
| trae-agent | L2-007 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-007__casual__r1/trajectory.json:1336` |
| trae-agent | L2-007 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-007__distracted__r1/trajectory.json:1099` |
| trae-agent | L2-007 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-007/trajectory.json:1062` |
| trae-agent | L2-008 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-008__casual__r1/trajectory.json:1068` |
| trae-agent | L2-008 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-008__distracted__r1/trajectory.json:1127` |
| trae-agent | L2-008 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-008/trajectory.json:1357` |
| trae-agent | L2-009 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-009__casual__r1/trajectory.json:1340` |
| trae-agent | L2-009 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-009__distracted__r1/trajectory.json:1012` |
| trae-agent | L2-009 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-009/trajectory.json:1333` |
| trae-agent | L2-010 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-010__casual__r1/trajectory.json:1286` |
| trae-agent | L2-010 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-010__distracted__r1/trajectory.json:1115` |
| trae-agent | L2-010 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-010/trajectory.json:1484` |
| trae-agent | L2-011 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-011__casual__r1/trajectory.json:1442` |
| trae-agent | L2-011 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-011__distracted__r1/trajectory.json:1475` |
| trae-agent | L2-011 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-011/trajectory.json:1027` |
| trae-agent | L2-012 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-012__casual__r1/trajectory.json:1754` |
| trae-agent | L2-012 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-012__distracted__r1/trajectory.json:1484` |
| trae-agent | L2-012 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-012/trajectory.json:1033` |
| trae-agent | L2-013 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-013__casual__r1/trajectory.json:1665` |
| trae-agent | L2-013 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-013__distracted__r1/trajectory.json:1260` |
| trae-agent | L2-013 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-013/trajectory.json:1177` |
| trae-agent | L2-014 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-014__casual__r1/trajectory.json:1430` |
| trae-agent | L2-014 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-014__distracted__r1/trajectory.json:1316` |
| trae-agent | L2-014 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-014/trajectory.json:1110` |
| trae-agent | L2-015 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-015__casual__r1/trajectory.json:1501` |
| trae-agent | L2-015 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-015__distracted__r1/trajectory.json:1218` |
| trae-agent | L2-015 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-015/trajectory.json:971` |
| trae-agent | L2-016 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-016__casual__r1/trajectory.json:1104` |
| trae-agent | L2-016 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-016__distracted__r1/trajectory.json:1037` |
| trae-agent | L2-016 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-016/trajectory.json:1074` |
| trae-agent | L2-017 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-017__casual__r1/trajectory.json:1071` |
| trae-agent | L2-017 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-017__distracted__r1/trajectory.json:1018` |
| trae-agent | L2-017 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-017/trajectory.json:1127` |
| trae-agent | L2-018 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-018__casual__r1/trajectory.json:1395` |
| trae-agent | L2-018 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-018__distracted__r1/trajectory.json:1006` |
| trae-agent | L2-018 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-018/trajectory.json:1130` |
| trae-agent | L2-019 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-019__casual__r1/trajectory.json:1729` |
| trae-agent | L2-019 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-019__distracted__r1/trajectory.json:1183` |
| trae-agent | L2-019 | L2 | precise | 0.0 | fact_miss | `runs/gate4_baseline_trae_v1/trae-agent/L2-019/trajectory.json:1245` |
| trae-agent | L2-020 | L2 | casual | 0.0 | reasoning_or_retrieval_error | `runs/gate4_baseline_trae_v1/trae-agent/L2-020__casual__r1/trajectory.json:986` |
| trae-agent | L2-020 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-020__distracted__r1/trajectory.json:1124` |
| trae-agent | L2-020 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-020/trajectory.json:1280` |
| trae-agent | L2-021 | L2 | casual | 0.0 | no_anomaly_false_positive | `runs/gate4_baseline_trae_v1/trae-agent/L2-021__casual__r1/trajectory.json:1241` |
| trae-agent | L2-021 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-021__distracted__r1/trajectory.json:965` |
| trae-agent | L2-021 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-021/trajectory.json:1278` |
| trae-agent | L2-022 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-022__casual__r1/trajectory.json:1018` |
| trae-agent | L2-022 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-022__distracted__r1/trajectory.json:1074` |
| trae-agent | L2-022 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-022/trajectory.json:1056` |
| trae-agent | L2-023 | L2 | casual | 1.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-023__casual__r1/trajectory.json:1048` |
| trae-agent | L2-023 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-023__distracted__r1/trajectory.json:915` |
| trae-agent | L2-024 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-024__casual__r1/trajectory.json:1210` |
| trae-agent | L2-024 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-024__distracted__r1/trajectory.json:1062` |
| trae-agent | L2-024 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-024/trajectory.json:1080` |
| trae-agent | L2-025 | L2 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-025__casual__r1/trajectory.json:1065` |
| trae-agent | L2-025 | L2 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-025__distracted__r1/trajectory.json:1012` |
| trae-agent | L2-025 | L2 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L2-025/trajectory.json:1074` |
| trae-agent | L3-001 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-001__casual__r1/trajectory.json:1096` |
| trae-agent | L3-001 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-001__distracted__r1/trajectory.json:1358` |
| trae-agent | L3-001 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-001/trajectory.json:1177` |
| trae-agent | L3-002 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-002__casual__r1/trajectory.json:1493` |
| trae-agent | L3-002 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-002__distracted__r1/trajectory.json:1222` |
| trae-agent | L3-002 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-002/trajectory.json:1369` |
| trae-agent | L3-003 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-003__casual__r1/trajectory.json:1277` |
| trae-agent | L3-003 | L3 | distracted | 0.0 | timeout | `runs/gate4_baseline_trae_v1/trae-agent/L3-003__distracted__r1/trajectory.json:1505` |
| trae-agent | L3-003 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-003/trajectory.json:2483` |
| trae-agent | L3-004 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-004__casual__r1/trajectory.json:1794` |
| trae-agent | L3-004 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-004__distracted__r1/trajectory.json:1822` |
| trae-agent | L3-004 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-004/trajectory.json:2020` |
| trae-agent | L3-005 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-005__casual__r1/trajectory.json:912` |
| trae-agent | L3-005 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-005__distracted__r1/trajectory.json:1107` |
| trae-agent | L3-005 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-005/trajectory.json:1080` |
| trae-agent | L3-006 | L3 | casual | 0.0 | fact_miss | `runs/gate4_baseline_trae_v1/trae-agent/L3-006__casual__r1/trajectory.json:662` |
| trae-agent | L3-006 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-006__distracted__r1/trajectory.json:1021` |
| trae-agent | L3-009 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-009__casual__r1/trajectory.json:2429` |
| trae-agent | L3-009 | L3 | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-009__distracted__r1/trajectory.json:2175` |
| trae-agent | L3-009 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-009/trajectory.json:1813` |
| trae-agent | L3-010 | L3 | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-010__casual__r1/trajectory.json:1066` |
| trae-agent | L3-010 | L3 | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/L3-010/trajectory.json:1075` |
| trae-agent | TRAP-001 | trap | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-001__casual__r1/trajectory.json:900` |
| trae-agent | TRAP-001 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-001__distracted__r1/trajectory.json:1420` |
| trae-agent | TRAP-001 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-001/trajectory.json:1102` |
| trae-agent | TRAP-002 | trap | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-002__casual__r1/trajectory.json:1177` |
| trae-agent | TRAP-002 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-002__distracted__r1/trajectory.json:2015` |
| trae-agent | TRAP-002 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-002/trajectory.json:968` |
| trae-agent | TRAP-003 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-003__distracted__r1/trajectory.json:1074` |
| trae-agent | TRAP-003 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-003/trajectory.json:1178` |
| trae-agent | TRAP-004 | trap | casual | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-004__casual__r1/trajectory.json:1234` |
| trae-agent | TRAP-004 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-004__distracted__r1/trajectory.json:1440` |
| trae-agent | TRAP-004 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-004/trajectory.json:1071` |
| trae-agent | TRAP-005 | trap | distracted | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-005__distracted__r1/trajectory.json:954` |
| trae-agent | TRAP-005 | trap | precise | 0.0 | format_failure | `runs/gate4_baseline_trae_v1/trae-agent/TRAP-005/trajectory.json:1320` |

## Canary And Tool Disable Validation

- GATE2 setup and canary checks are recorded in `output/gate2_candidate_check.md`.
- All four candidates passed canary-bash, canary-write, and canary-mcp before GATE4.
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
