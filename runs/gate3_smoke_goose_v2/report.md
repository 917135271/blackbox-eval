# GATE 3 Smoke Report

- run_id: `gate3_smoke_goose_v2`
- generated_at: `2026-07-07T15:23:55`
- candidate: `goose`
- candidate_version: `1.41.0`
- model_endpoint: `https://api.deepseek.com`
- model: `deepseek-v4-flash`
- baseline_note: current endpoint is the user-approved DeepSeek cloud API, not the original local-only target.
- tasks: `L1-001, L1-002, L1-003`

## Fixture Hashes

- `fixtures\policy_query_mcp.py`: `7564a27591683f97`
- `fixtures\expense_query_mcp.py`: `c2b2cee2b9ac3973`
- `fixtures\audit_role_prompt.md`: `beca2dab50e931fe`
- `fixtures\output_contract.md`: `d0c89b9b54cf3b23`

## Summary

- deterministic_score: `2/3`
- format_follow_rate: `67%`
- clean_workdir_rate: `100%`
- failure_layers: `{'ok': 2, 'format_failure': 1}`

## Task Results

| task | kind | score | format | tool_calls | elapsed_s | workdir | failure |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| L1-001 | expected_facts | 1.0 | ok | 4 | 14.41 | clean | ok |
| L1-002 | expected_facts | 1.0 | ok | 2 | 9.28 | clean | ok |
| L1-003 | expected_facts | 0.0 | fail | 5 | 12.54 | clean | format_failure |

## Grade Details

- `L1-001`: facts `现行部门总经理审批线为10000元=hit`; citation_ok `True`
- `L1-002`: facts `费用发生后60天内提交报销=hit`; citation_ok `True`
- `L1-003`: facts ``; citation_ok `None`

## Artifact Completeness

- `L1-001`: ok
- `L1-002`: ok
- `L1-003`: ok

## Manual Check Point

This GATE 3 report is the human confirmation point for deterministic grading before GATE 4 full baseline.
