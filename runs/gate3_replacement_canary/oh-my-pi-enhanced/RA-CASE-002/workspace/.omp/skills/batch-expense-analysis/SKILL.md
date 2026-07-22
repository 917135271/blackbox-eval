---
name: batch-expense-analysis
description: Perform complete read-only SQL and Python analysis of expense data. Use for batch record retrieval, date ranges, aggregation, joins, thresholds, duplicates, split claims, approvals, or any task where one lookup cannot prove coverage.
---

# Batch Expense Analysis

Use executable SQL and Python to prove full data coverage. A preview or a few matching rows is not a complete audit.

## Trigger

Run for multiple records, period-wide checks, aggregation, grouping, joins, thresholds, duplicates, split claims, or MCP result limits. A single known-record lookup may use compact mode without a subagent.

For a one-rule clue-record task, follow only the relational closure needed by that rule: for example, the same invoice for duplicate reimbursement or the same employee/type/window for split reimbursement. Do not turn it into a full-database or multi-rule scan.

## Procedure

1. Inspect the schema, primary keys, date fields, amount fields, and join keys.
2. Open SQLite in read-only mode.
3. Count the complete in-scope population before filtering findings.
4. Save parameterized SQL in `work/sql/query.sql` and its parameters separately.
5. Use Python for complex calculations, duplicate detection, or independent reconciliation when needed.
6. Reconcile SQL and Python counts and amounts.
7. Save the full result set; never stop at displayed preview rows.
8. Deduplicate record IDs and verify each against the database.
9. Treat query failure or partial coverage as unresolved, not as a complete conclusion.
10. Derive each rule's comparison unit before testing it: per transaction, employee, day, night, event, month, rolling window, or department-year. Aggregate by that unit before comparing with a threshold.
11. For comprehensive audits, build a rule-by-population coverage checklist and run every applicable rule independently. Clearing a record under one rule never clears it under another; for example, records outside a split-reimbursement window may still breach a monthly employee cap.
12. Treat list and summary tools as candidate discovery only. Before clearing or confirming a candidate, fetch record detail for every rule-dependent field omitted from a list result, including participants, days, nights, city tier, employee level, and special approval. An omitted preview field is not a database null.
13. Apply policy exceptions and approval exemptions before finalizing matched record IDs. A threshold breach with a verified applicable exemption is a cleared candidate, not an anomaly or unresolved gap.
14. Query the mounted SQLite database directly for batch work; do not transcribe preview rows into a hard-coded Python list. Select every field used by a rule, especially `participants`, `days`, `nights`, `city_tier`, `special_approval`, invoice identity, employee, and department.
15. Build a requested-rule whitelist from the task and audit plan. Save unrelated concerns separately, but never place them in findings, evidence rows, or the final result for a single-rule task.
16. For every monthly employee cap, first reconcile repeated invoice identity, then `GROUP BY employee_id, expense_type, natural_month` and compare the grouped sum with the threshold. Never compare each row independently to a monthly cap. Office-supplies and communication monthly caps are `超标准` rules, not budget rules. Report invoice reuse under the duplicate rule only when that rule is in scope.
17. For a 7-day split check, compare the policy-defined expense date consistently for both records. Do not replace start-to-start distance with the gap between one period's end and another period's start.
18. For cumulative budget checks, order records deterministically and calculate the balance after each record. A pre-crossing record is calculation context, not an anomaly; the first record that pushes the balance over the limit is anomalous when it lacks required special approval; a valid approved record is cleared and excluded.

## Data Analyst

Request `data_analyst` through `authorize_audit_subagent` for aggregation, joins, multiple candidate records, date or amount boundaries, duplicates, or Python reconciliation. If the audit plan routes to `data_analyst`, authorization and native launch are the first actions of this skill; do not query and solve the delegated data scope in the main agent first. While the subagent runs, perform only non-overlapping policy work. Register the compact summary and artifacts through `complete_audit_subagent` before consuming them. Invoke it at most once.

## Output

Write `work/analysis/data_findings.json`. The JSON includes in-scope population count, candidate count, matched record IDs, aggregate results, rule-by-population coverage, completed checks, query and result artifact paths, data-quality issues, limitations, and unresolved items. Keep SQL, Python, and tabular result data in separate files referenced by path.

## Guardrails

- Never execute database writes or schema changes.
- Never replace a failed query with an estimate.
- Never invent record IDs or return only the first page of matches.
- Never treat a field omitted from an MCP preview as missing in the business database.
- Never report an anomaly from a rule the task did not request unless the task explicitly asks for a comprehensive audit.

Finish only when scope, query logic, counts, calculations, and every returned record ID are reproducible.
