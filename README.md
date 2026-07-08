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
all four candidates. Model-backed canaries and eval runs require `LLM_API_KEY`
to be present in the shell environment.

Large, reproducible runtime installs are deliberately not tracked in Git:

- `candidates/goose/install/`
- `candidates/trae-agent/vendor/`

Trae Agent's local engineering fixes are preserved as
`candidates/trae-agent/patches/engineering-usability.patch` and summarized in
`candidates/trae-agent/setup.md`.

## Model And Candidate Config

Current config enables all four requested candidates:

- `qwen-code`
- `goose`
- `trae-agent`
- `opencode`

The configured OpenAI-compatible endpoint is:

- `base_url`: `https://api.deepseek.com`
- `model`: `deepseek-v4-flash`
- `api_key_env`: `LLM_API_KEY`

Before running any candidate, set the API key in the shell environment instead of writing it to config:

```powershell
$env:LLM_API_KEY = "<your key>"
```

Important: the original prompt required a local model endpoint and prohibited cloud APIs. `https://api.deepseek.com` is a public endpoint, so reports must mark this as a baseline deviation unless it is replaced by an internal/local proxy.

## Data Fixture Paths

The config points to the generated synthetic assets:

- Expense SQLite: `../synth-pipeline/output/data/expense.db`
- Policy corpus: `../synth-pipeline/output/corpus`
- Ground truth: `../synth-pipeline/output/ground_truth.yaml`
- Eval tasks: `../synth-pipeline/output/evals.json`

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
- `list_employees`
- `get_employee`
- `get_department_budget`
- `list_approvals`

It deliberately does not expose anomaly detectors such as `find_duplicates` or `detect_split_reimbursement`.

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

Run the completed GATE 4 baseline shape:

```powershell
$env:LLM_API_KEY = [Environment]::GetEnvironmentVariable("LLM_API_KEY", "User")
python runner/run_eval.py --candidate qwen-code --all-tasks --all-variants --run-id gate4_baseline_qwen_v1 --timeout-seconds 900
python runner/run_eval.py --candidate goose --all-tasks --all-variants --run-id gate4_baseline_goose_v1 --timeout-seconds 900
python runner/run_eval.py --candidate trae-agent --all-tasks --all-variants --run-id gate4_baseline_trae_v1 --timeout-seconds 900
python runner/run_eval.py --candidate opencode --all-tasks --all-variants --run-id gate4_baseline_opencode_v1 --timeout-seconds 900
python runner/grade.py --run-id gate4_baseline_qwen_v1 --candidate qwen-code
python runner/grade.py --run-id gate4_baseline_goose_v1 --candidate goose
python runner/grade.py --run-id gate4_baseline_trae_v1 --candidate trae-agent
python runner/grade.py --run-id gate4_baseline_opencode_v1 --candidate opencode
python runner/report_gate4.py --run qwen-code=gate4_baseline_qwen_v1 --run goose=gate4_baseline_goose_v1 --run trae-agent=gate4_baseline_trae_v1 --run opencode=gate4_baseline_opencode_v1
```

## Design Decisions

- No existing `policy_query_mcp.py` skeleton was found in the workspace, so this gate includes a conservative in-memory BM25 implementation.
- Both MCP fixtures support simple JSON-RPC stdio methods (`initialize`, `tools/list`, `tools/call`) plus `--self-test` for local verification.
- Fixture logs accept `EVAL_TASK_LOG` as either a directory or a file path; if it is a directory, `tool_calls.jsonl` is created inside it.
- The current endpoint is DeepSeek's cloud API because the local model is not deployed yet; reports must record this as a temporary baseline deviation from the original no-cloud requirement.
- Candidate configs never store the API key. The runner maps `LLM_API_KEY` to each candidate's expected provider variables at process launch.
- For qwen-code task runs, `run_eval.py` temporarily injects the task-specific `EVAL_TASK_LOG` directory into `.qwen/settings.json` MCP server env entries, approves that config with official `qwen mcp approve --all`, and restores the original config after each task. This keeps task-level MCP logs isolated while using the candidate's official configuration surface.
