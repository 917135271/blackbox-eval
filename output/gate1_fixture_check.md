# GATE 1 Fixture Manual Check

## policy_query_mcp

- initialize: ok
- tools/list count: 4
- list_policy_docs: ok
- search_policy: ok
- get_policy_doc: ok
- get_policy_excerpt: ok

## expense_query_mcp

- initialize: ok
- tools/list count: 13
- list_expenses: ok
- get_expense_detail: ok
- find_invoice_usage: ok
- list_invoices: ok
- find_reused_invoices: ok
- summarize_expenses: ok
- summarize_department_budgets: ok
- list_records_by_reimburse_delay: ok
- list_records_missing_approval: ok
- list_employees: ok
- get_employee: ok
- get_department_budget: ok
- list_approvals: ok

## Log Files

- `output/gate1_policy_logs/tool_calls.jsonl`
- `output/gate1_expense_logs/tool_calls.jsonl`
- `output/gate1_policy_rpc_results.json`
- `output/gate1_expense_rpc_results.json`
