---
name: audit-report
description: Produce the final evidence-grounded securities expense audit narrative. Use for every task after evidence coverage and any required independent review have passed.
---

# Audit Report

Run for every task after evidence coverage passes and any required review is resolved.

## Procedure

1. State the audited object, period, organization, and data scope.
2. Separate verified facts from policy rules and audit judgment.
3. For each finding, state the applicable policy and clause, record IDs, impact, and recommendation.
4. For no-anomaly results, state the completed query scope, rules checked, conclusion, and any genuine data limitation.
5. Reconcile all IDs, dates, amounts, and counts with approved intermediate artifacts.
6. Keep simple answers concise and comprehensive reports complete but compact. Do not repeat full policy text or duplicate evidence already stored in the matrix; keep the report draft under 6000 Chinese characters.
7. Recheck that every finding belongs to the question's frozen rule and scope. Remove unrelated findings even when they were noticed during investigation.
8. State both the applicable threshold and observed value for every amount or date-boundary judgment, using plain digits. For example, state `7天` as well as the observed interval, and state both the budget limit and crossing balance.
9. Use the explicit phrase `无异常` when `anomaly_ids` is empty. No-anomaly `record_ids` still contain all records directly named or covered by the conclusion.
10. In positive results, keep contextual and exempt records out of `record_ids`: a budget history record before crossing and a record with valid special approval may be explained in the answer but are not anomaly records.

## Output

Write `work/report_draft.json`. The JSON includes audit scope, verified facts, applicable policies, findings, impact, recommendations, anomaly IDs, record IDs, citations, answer text, and limitations.

## Guardrails

- Do not introduce a new finding, record, citation, amount, or date at report time.
- Do not broaden a single-rule task into a general audit.
- Every finding must be supported by the passed evidence matrix.
- Do not amplify a result with unsupported language such as broad or systemic impact.
- Keep an empty anomaly set explicit for a no-anomaly result.

Finish only when the report and evidence matrix agree exactly on findings, IDs, citations, and material figures.
