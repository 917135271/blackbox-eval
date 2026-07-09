# blackbox-eval

This directory contains the black-box evaluation runner scaffold for the B-domain synthetic audit fixture.

## Current Gate

GATE 1 through GATE 4 are implemented. The repository contains the runner,
fixtures, candidate setup/configuration, reports, and persisted run artifacts for
the completed baseline:

- `config/eval_config.yaml`
- `fixtures/policy_query_mcp.py`
- `fixtures/expense_query_mcp.py`
- `fixtures/audit_role_prompt.md`
- `fixtures/output_contract.md`
- `output/gate1_*` after manual fixture verification
- `candidates/*/setup.md`
- `candidates/*/workdir`
- `runner/gate2_candidate_check.py`
- `runner/run_eval.py`
- `runner/grade.py`
- `runner/report.py`
- `runner/report_gate3_all.py`
- `runner/report_gate4.py`
- `output/gate2_candidate_check.md` after setup/canary checks
- `output/gate3_smoke_report.md` after smoke execution, grading, and reporting
- `output/gate4_baseline_report.md` after full baseline execution
- `output/gate4_failure_attribution.jsonl` with per-failure trace evidence

Candidate installation and project-level configuration have been completed for
the current five active candidates. Model-backed canaries and eval runs require `LLM_API_KEY`
to be present in the shell environment.

Large, reproducible runtime installs are deliberately not tracked in Git:

- `candidates/goose/install/`
- `candidates/claude-code/vendor/`
- `candidates/claude-code/runtime/`
- `candidates/trae-agent/vendor/`
- `candidates/codex/runtime*/`

Candidate-local state caches, such as `candidates/claude-code/config/` and
Codex session/sqlite files, are also ignored. Reproducible evidence lives under
`runs/` and the generated reports under `output/`.

Trae Agent's local engineering fixes are preserved as
`candidates/trae-agent/patches/engineering-usability.patch` and summarized in
`candidates/trae-agent/setup.md`.

## Model And Candidate Config

Current config enables the standard-55-task candidate set:

- `qwen-code`
- `trae-agent`
- `opencode`
- `claude-code`
- `codex`

`goose` remains in the repository for historical result reproducibility, but it
is disabled in `config/eval_config.yaml` and is not part of the next standard
55-task run.

The configured OpenAI-compatible endpoint is:

- `base_url`: `https://api.deepseek.com`
- `model`: `deepseek-v4-pro`
- `api_key_env`: `LLM_API_KEY`

The grader now uses an LLM judge by default, configured under `judge:` in
`config/eval_config.yaml`. It uses the same `LLM_API_KEY` environment variable
and does not store secrets in the repository. Each grade row keeps both:

- `score`: LLM judge semantic score.
- `rule_score`: deterministic rule score for comparison. Detection tasks can pass the rule scorer by matching either standard `anomaly_ids` or the expected supporting `record_ids`, depending on task type.

The candidate output contract is:

```json
{"anomaly_ids": [], "record_ids": [], "answer": "结论摘要", "citations": []}
```

`record_ids` is the primary business-evidence field for audit detection tasks. `anomaly_ids` is still recorded when a candidate can infer the synthetic benchmark label, but it is no longer the only usable evidence channel.

Before running any candidate, set the API key in the shell environment instead of writing it to config:

```powershell
$env:LLM_API_KEY = "<your key>"
```

Important: the original prompt required a local model endpoint and prohibited cloud APIs. `https://api.deepseek.com` is a public endpoint, so reports must mark this as a baseline deviation unless it is replaced by an internal/local proxy.

## Data Fixture Paths

The repository now includes the synthetic benchmark fixture needed by the runner:

- Eval tasks: `data/evals.json`
- Ground truth: `data/ground_truth.yaml`
- Expense SQLite: `data/expense.db`
- Raw CSV tables: `data/csv/`
- Policy corpus: `data/corpus/`
- Synthetic generation and consistency reports: `data/reports/`

## MCP Fixtures

`policy_query_mcp.py` exposes only policy-corpus retrieval primitives:

- `list_policy_docs`
- `search_policy`
- `get_policy_doc`
- `get_policy_excerpt`

`expense_query_mcp.py` exposes only raw business-fact primitives:

- `list_expenses`
- `get_expense_detail`
- `find_invoice_usage`
- `list_invoices`
- `find_reused_invoices`
- `summarize_expenses`
- `summarize_department_budgets`
- `list_records_by_reimburse_delay`
- `list_records_missing_approval`
- `list_employees`
- `get_employee`
- `get_department_budget`
- `list_approvals`

It deliberately does not expose anomaly detectors such as `find_duplicates` or `detect_split_reimbursement`.
The added tools expose filters, paging, aggregation, invoice usage counts, reimbursement delays, and missing approval-role facts; they do not return `anomaly_id` labels or final anomaly conclusions.

## Gate Checks

Run:

```bash
python fixtures/policy_query_mcp.py --self-test
python fixtures/expense_query_mcp.py --self-test
python runner/gate1_manual_check.py
python runner/gate2_candidate_check.py
```

When `EVAL_TASK_LOG` points to a directory, both servers write JSONL tool-call events to `tool_calls.jsonl` inside that directory.

Run GATE 2 canaries only after setting `LLM_API_KEY`:

```powershell
$env:LLM_API_KEY = "<your key>"
python runner/gate2_candidate_check.py --run-canaries
```

Run GATE 3 smoke after setting `LLM_API_KEY`:

```powershell
$env:LLM_API_KEY = [Environment]::GetEnvironmentVariable("LLM_API_KEY", "User")
$runId = "gate3_smoke_qwen"
python runner/run_eval.py --candidate qwen-code --level L1 --limit 3 --variant precise --run-id $runId
python runner/grade.py --run-id $runId --candidate qwen-code
python runner/report.py --run-id $runId
```

Run the current GATE 4 standard shape, which is 55 tasks with the single
`precise` prompt variant:

```powershell
$env:LLM_API_KEY = [Environment]::GetEnvironmentVariable("LLM_API_KEY", "User")
python runner/run_eval.py --candidate qwen-code --all-tasks --variant precise --run-id gate4_standard_qwen_v4pro_v1 --timeout-seconds 900
python runner/run_eval.py --candidate trae-agent --all-tasks --variant precise --run-id gate4_standard_trae_v4pro_v2 --timeout-seconds 900
python runner/run_eval.py --candidate opencode --all-tasks --variant precise --run-id gate4_standard_opencode_v4pro_v1 --timeout-seconds 900
python runner/run_eval.py --candidate claude-code --all-tasks --variant precise --run-id gate4_standard_claude_v4pro_v1 --timeout-seconds 900
python runner/run_eval.py --candidate codex --all-tasks --variant precise --run-id gate4_standard_codex_v4pro_v2 --timeout-seconds 900
python runner/grade.py --run-id gate4_standard_qwen_v4pro_v1 --candidate qwen-code --judge-mode llm
python runner/grade.py --run-id gate4_standard_trae_v4pro_v2 --candidate trae-agent --judge-mode llm
python runner/grade.py --run-id gate4_standard_opencode_v4pro_v1 --candidate opencode --judge-mode llm
python runner/grade.py --run-id gate4_standard_claude_v4pro_v1 --candidate claude-code --judge-mode llm
python runner/grade.py --run-id gate4_standard_codex_v4pro_v2 --candidate codex --judge-mode llm
python runner/report_gate4.py --run qwen-code=gate4_standard_qwen_v4pro_v1 --run trae-agent=gate4_standard_trae_v4pro_v2 --run opencode=gate4_standard_opencode_v4pro_v1 --run claude-code=gate4_standard_claude_v4pro_v1 --run codex=gate4_standard_codex_v4pro_v2
python runner/report_gate4_tasktypes.py
```

If the judge API has transient network failures, retry only failed judge rows and
merge them back into the existing grade file:

```powershell
python runner/grade.py --run-id gate4_standard_claude_v4pro_v1 --candidate claude-code --judge-mode llm --workers 1 --only-judge-errors
```

Use `--judge-mode rule` when you need to reproduce the old deterministic scorer.

## Design Decisions

- No existing `policy_query_mcp.py` skeleton was found in the workspace, so this gate includes a conservative in-memory BM25 implementation.
- Both MCP fixtures support simple JSON-RPC stdio methods (`initialize`, `tools/list`, `tools/call`) plus `--self-test` for local verification.
- Fixture logs accept `EVAL_TASK_LOG` as either a directory or a file path; if it is a directory, `tool_calls.jsonl` is created inside it.
- The current endpoint is DeepSeek's cloud API because the local model is not deployed yet; reports must record this as a temporary baseline deviation from the original no-cloud requirement.
- Candidate configs never store the API key. The runner maps `LLM_API_KEY` to each candidate's expected provider variables at process launch.
- The grader uses LLM judge semantic scoring by default and records the previous deterministic result as `rule_score`.
- Candidate step/tool-call limits are configured under `execution.candidate_max_steps` in `config/eval_config.yaml`; Trae is no longer hard-coded to `--max-steps 8`.
- The active prompt scope is now the single standard `precise` variant, so a full run is 55 tasks per candidate instead of 55 x 3 variants.
- For qwen-code task runs, `run_eval.py` temporarily injects the task-specific `EVAL_TASK_LOG` directory into `.qwen/settings.json` MCP server env entries, approves that config with official `qwen mcp approve --all`, and restores the original config after each task. This keeps task-level MCP logs isolated while using the candidate's official configuration surface.
