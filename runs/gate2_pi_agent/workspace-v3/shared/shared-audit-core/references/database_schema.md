# Expense Database Reference

Open the SQLite database in read-only mode. The business key returned to the evaluator is `expense_records.record_id`.

## Tables

- `expense_records`: `record_id`, `record_no`, `employee_id`, `department_id`, `expense_date`, `reimburse_date`, `expense_type`, `amount`, `reason`, `invoice_id`, `status`, `city_tier`, `nights`, `days`, `participants`, `budget_year`, `special_approval`.
- `invoices`: `invoice_id`, `invoice_no`, `vendor_name`, `invoice_date`, `amount`, `expense_type`.
- `approvals`: `approval_id`, `record_id`, `tier_id`, `approver_employee_id`, `approver_role`, `approved_at`, `approval_status`.
- `employees`: `employee_id`, `employee_name`, `employee_level`, `department_id`, `position_role`, `hire_date`.
- `departments`: `department_id`, `department_name`, `annual_budget`, `manager_employee_id`.

## Query Rules

- Count the in-scope population before filtering findings.
- Join with declared keys; do not infer identity from names.
- Preserve all matched `record_id` values, not only preview rows.
- Save query text, parameters, counts, and result paths in the task workspace.
- Never execute writes or schema changes.
