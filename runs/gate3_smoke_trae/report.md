# GATE 3 Smoke Report

- run_id: `gate3_smoke_trae`
- generated_at: `2026-07-07T15:32:30`
- candidate: `trae-agent`
- candidate_version: `0.1.0`
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

- deterministic_score: `0/3`
- format_follow_rate: `0%`
- clean_workdir_rate: `100%`
- failure_layers: `{'format_failure': 3}`

## Task Results

| task | kind | score | format | tool_calls | elapsed_s | workdir | failure |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| L1-001 | expected_facts | 0.0 | fail | 0 | 28.32 | clean | format_failure |
| L1-002 | expected_facts | 0.0 | fail | 0 | 23.04 | clean | format_failure |
| L1-003 | expected_facts | 0.0 | fail | 0 | 25.57 | clean | format_failure |

## Grade Details

- `L1-001`: facts ``; citation_ok `None`
- `L1-002`: facts ``; citation_ok `None`
- `L1-003`: facts ``; citation_ok `None`

## Artifact Completeness

- `L1-001`: ok
- `L1-002`: ok
- `L1-003`: ok

## Manual Check Point

This GATE 3 report is the human confirmation point for deterministic grading before GATE 4 full baseline.
