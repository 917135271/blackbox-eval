---
name: result-validator
description: Validate the final audit result before unified submission. Use for every task to check schema, IDs, citations, evidence coverage, report consistency, and the one-repair limit without changing semantic conclusions.
---

# Result Validator

Run immediately before `submit_audit_result`. This is a deterministic gate, not another analysis pass.

## Procedure

1. Build the final result with exactly `anomaly_ids`, `record_ids`, `answer`, and `citations`.
2. Check required fields, types, empty values, duplicates, and unsupported extra fields.
3. Verify record IDs against the read-only database and policy document IDs against the corpus.
4. Check anomaly IDs are non-empty strings and internally consistent. Do not impose a framework-specific naming pattern or consult hidden answer mappings.
5. Check that anomaly and record arrays agree with the answer and evidence matrix.
6. Check that citations belong to applicable policies and evidence rows.
7. Verify evidence status is `pass` with 100 percent coverage.
8. Read `/plugin/shared/shared-audit-core/schemas/evidence-matrix.schema.json`, `validation-report.schema.json`, and `audit-result.schema.json`; if `/plugin` is unavailable, use the equivalent adapter-local `shared/shared-audit-core/schemas/` path. Use their exact field names and types without aliases.
9. Recheck result semantics: positive `record_ids` contain only records participating in an in-scope violation; no-anomaly `record_ids` retain the scoped records checked; pre-crossing budget history, valid special approvals, duplicate aggregation context, and unrelated-rule findings are excluded.
10. Recheck answer completeness: every boundary judgment states its threshold and observed value, and every empty anomaly set explicitly says `无异常`.
11. Call `validate_audit_result` with exactly these arguments: `result`, `evidence_matrix_path`, and `validation_report_path`. Do not use `result_path`, `evidence_matrix`, or `report_path`. This preflight does not consume a submission attempt.
12. If preflight fails, repair every reported field and every correlated artifact before one final preflight. Submit only when `valid=true`.

## Output

Write `work/validation_report.json`. The JSON includes the exact schema fields: status, errors, warnings, field checks, ID checks, evidence checks, answer consistency checks, repair count, repairable fields, and `submission_allowed`. Write the four-field candidate result to `work/final_result.json` only when ready to submit.

Pass the parsed JSON object as `result`; passing the file path string is also accepted. Do not expand the four result fields into top-level tool arguments.

## Repair Limit

Preflight may be repaired and rerun once. After preflight passes, call `submit_audit_result`. If submission still returns `repair_required`, repair every reported field and correlated file before the one allowed resubmission. Never retry after rejection or `REPAIR_LIMIT_EXCEEDED`.

## Guardrails

- Do not add or remove semantic findings.
- Do not infer missing records, policies, or clauses.
- Do not access Ground Truth, evaluation mappings, judging code, or historical answers.

Call `submit_audit_result` only when validation status is `pass`.
