# Isolated Task Workspace Contract

Each task receives a fresh workspace and may only read the task prompt, policy corpus, read-only expense database, plugin files, and files created inside that workspace.

Required artifact paths:

- `work/task_state.json`
- `work/evidence_index.json`
- `work/decision_log.jsonl`
- `work/context_checkpoint.json`
- `work/artifact_index.json`
- `work/audit_plan.json`
- `work/policy_applicability.json` when policy analysis is relevant
- `work/analysis/data_findings.json` when data analysis is relevant
- `work/evidence_matrix.json`
- `work/independent_review.json` when review is triggered
- `work/report_draft.json`
- `work/validation_report.json`
- `work/final_result.json`

Subagent artifacts belong under `work/subagents/<role>/`. SQL and Python analysis belongs under `work/sql/` and `work/analysis/`.

Audit traces belong under `traces/`, including `events.jsonl`, `tool_calls.jsonl`, `subagents.jsonl`, `context_events.jsonl`, and `artifact_manifest.json`. The outer runner writes `run_manifest.json`.

Never read `ground_truth.yaml`, `evals.json`, judge code, prior candidate trajectories, prior task workspaces, or historical standard answers. Never write credentials to any artifact. Do not modify the source database or policy corpus.
