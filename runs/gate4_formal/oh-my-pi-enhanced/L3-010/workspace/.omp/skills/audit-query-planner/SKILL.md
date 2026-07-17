---
name: audit-query-planner
description: Plan every securities expense-audit task before querying. Use for all audit questions to define scope, applicable rule questions, required data fields, evidence needs, complexity, stopping conditions, and controlled subagent routing.
---

# Audit Query Planner

Run this skill first for every task. Produce an execution plan, not an audit conclusion.

## Procedure

1. Extract the audit object, expense types, business period, organization scope, and requested deliverable.
2. List the policy questions and all material boundaries: dates, amounts, equality conditions, exemptions, approvals, and exceptions.
3. List the tables, fields, policy documents, and evidence needed to answer each question.
4. Split work into policy research, data analysis, evidence review, reporting, validation, and submission.
5. Define the expected artifact and stopping condition for each step.
6. Calculate complexity from 0 to 6, adding one point for each condition:
   - policy version, effective date, or repeal relationship;
   - two or more policies;
   - aggregation, grouping, joins, or batch filtering;
   - two or more business rules;
   - thresholds, dates, exemptions, or exceptions;
   - a comprehensive audit report.
7. Create a subagent plan using the routing rules below.

Calibrate before finalizing the score:

- A policy fact question or one-rule known-record task with only directly related records is complexity 0-1, even if one lookup or join is needed.
- A one-rule batch, grouping, threshold, date-boundary, or aggregation task is complexity 2-3.
- A policy-version ambiguity, material exception, or no-anomaly trap is complexity 2-3.
- Only a genuine multi-rule, multi-policy, period-wide, or comprehensive audit is complexity 4-6.
- Do not add complexity merely because the workflow requires evidence files, validation, or a short report.

## Subagent Routing

- Complexity 0-1: keep the task in the main agent.
- Complexity 2-3: request at most one professional subagent.
- Complexity 4-6: policy researcher and data analyst may both be requested; request an independent reviewer only after a preliminary finding and evidence matrix exist.
- Use only these reason codes: policy researcher uses `MULTI_POLICY_VERSION_CHECK`, `HISTORICAL_POLICY`, `POLICY_CONFLICT`, `POLICY_PERIOD_UNCLEAR`, or `MULTI_CLAUSE_SUPPORT`; data analyst uses `AGGREGATION_REQUIRED`, `MULTI_TABLE_JOIN`, `MULTI_RECORD_SCOPE`, `DATE_AMOUNT_BOUNDARY`, or `PYTHON_RECONCILIATION`; reviewer uses `EXCEPTION_OR_EXEMPTION`, `THRESHOLD_BOUNDARY`, `HISTORICAL_CROSS_PERIOD`, `POLICY_DATA_CONFLICT`, `EVIDENCE_GAP`, `COMPREHENSIVE_AUDIT`, or `NO_ANOMALY_RECHECK`.
- Obtain authorization from `authorize_audit_subagent` before invoking a native subagent.
- Call authorization with these exact parameters: `role`, `reason_code`, `complexity`, `context`, `artifact_paths`, and `requested_token_budget`. Put the bounded role task and question inside `context`; do not invent parameters such as `prompt`, `task`, or `subagent_type`.
- When the plan selects a subagent, write the audit plan and then authorize and launch that subagent immediately, before the main agent performs the delegated investigation. While it runs, the main agent may perform only non-overlapping work such as policy applicability checks. After the native role writes its summary and artifacts, call `complete_audit_subagent` before using the result.
- A planned professional role must be authorized and invoked; otherwise remove it from the plan and state why compact mode is sufficient.

## Output

Write `work/audit_plan.json`. The JSON includes task scope, audit period, policy questions, data questions, required fields, evidence requirements, execution steps, complexity score and reasons, subagent plan, stopping conditions, and unresolved items.

## Guardrails

- Do not create anomaly findings during planning.
- Do not assume the task contains an anomaly.
- Freeze the requested rule and scope. A clue-record task may expand only to records needed to decide that requested rule; do not add unrelated rule findings.
- Do not read evaluation answers, judging code, historical trajectories, or another task workspace.
- Do not use formal benchmark task labels or hidden expected IDs for routing.

Finish only when scope, rules, fields, evidence, routing, and stopping conditions are explicit.
