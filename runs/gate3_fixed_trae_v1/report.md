# GATE 3 Smoke Report

- run_id: `gate3_fixed_trae_v1`
- generated_at: `2026-07-07T15:58:57`
- candidate: `trae-agent`
- candidate_version: `0.1.0`
- model_endpoint: `https://api.deepseek.com`
- model: `deepseek-v4-flash`
- baseline_note: current endpoint is the user-approved DeepSeek cloud API, not the original local-only target.
- tasks: `L1-001, L1-002, L1-003`

## Fixture Hashes

- `fixtures\policy_query_mcp.py`: `7564a27591683f97`
- `fixtures\expense_query_mcp.py`: `c2b2cee2b9ac3973`
- `fixtures\audit_role_prompt.md`: `f91af06484f69773`
- `fixtures\output_contract.md`: `7110655287f02d12`

## Summary

- deterministic_score: `3/3`
- format_follow_rate: `100%`
- clean_workdir_rate: `100%`
- failure_layers: `{'ok': 3}`

## Task Results

| task | kind | score | format | tool_calls | elapsed_s | workdir | failure |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| L1-001 | expected_facts | 1.0 | ok | 4 | 28.44 | clean | ok |
| L1-002 | expected_facts | 1.0 | ok | 2 | 16.95 | clean | ok |
| L1-003 | expected_facts | 1.0 | ok | 3 | 19.44 | clean | ok |

## Grade Details

- `L1-001`: facts `现行部门总经理审批线为10000元=hit`; citation_ok `True`
- `L1-002`: facts `费用发生后60天内提交报销=hit`; citation_ok `True`
- `L1-003`: facts `2022版旧值为8000元=hit, 该值已废止=hit`; citation_ok `True`

## Artifact Completeness

- `L1-001`: ok
- `L1-002`: ok
- `L1-003`: ok

## Manual Check Point

This GATE 3 report is the human confirmation point for deterministic grading before GATE 4 full baseline.
