---
name: evidence-coverage-check
description: Check evidence coverage before reporting any audit result. Use for every task to connect each anomaly to records, policy clauses, and facts, and to prove complete search coverage for no-anomaly conclusions.
---

# Evidence Coverage Check

Run after policy and data analysis and before review or reporting. This skill is mandatory for every task, including no-anomaly answers.

## Procedure

1. Build one evidence row for every preliminary anomaly.
2. Link each anomaly to a rule, supporting facts, business record IDs, and applicable policy clauses. A multi-record anomaly must include every participating record, not only the later or payable record.
3. Verify every proposed record ID belongs to a finding.
4. Verify every applicable citation supports a stated rule.
5. Compare all candidate records with the proposed final record set.
6. Reconcile report amounts, counts, and dates with analysis artifacts.
7. For a no-anomaly conclusion, record the searched population, query conditions, completed rules, and population count.
8. Calculate coverage and list precise gaps.
9. Reject every candidate finding outside the frozen task rule and scope; discovering an unrelated concern does not make it part of the submitted answer.
10. Separate anomalous supporting records from calculation context. For cumulative budget findings, do not submit pre-crossing history or records cleared by valid special approval. For monthly caps, do not double-count one underlying invoice solely because it was submitted more than once.

## Output

Before writing, read `/plugin/shared/shared-audit-core/schemas/evidence-matrix.schema.json`; if `/plugin` is unavailable, use the equivalent adapter-local `shared/shared-audit-core/schemas/evidence-matrix.schema.json`. Write `work/evidence_matrix.json` once with the exact schema fields.

The top-level JSON includes exactly: `status`, `coverage_percent`, `evidence_rows`, `candidate_record_ids`, `submitted_record_ids`, `unowned_record_ids`, `unused_candidate_record_ids`, `unused_citations`, `missing_evidence`, `no_anomaly_coverage`, `reconciled_figures`, and `unresolved_items`. Every positive evidence row includes `anomaly_id`, `record_ids`, `citations`, `facts`, `fact_supported`, `rule_supported`, and `coverage_status`; `citations` is an array of `{doc_id, clause_no}` objects and `facts` is an array of non-empty fact strings.

Do not use aliases such as `coverage_pct`, `evidence`, `all_record_ids`, row-level `doc_id`, or `covered`. Do not set `facts` to a string or leave it empty. `submitted_record_ids` must exactly match the final result's `record_ids`: positive findings include every supporting record, while no-anomaly answers include the scoped records named by the conclusion. Every positive evidence row sets `fact_supported` and `rule_supported` to boolean `true` and `coverage_status` to `pass`.

`unowned_record_ids` contains only submitted records that lack an evidence row. `unused_candidate_record_ids` contains only candidates that have not been adjudicated. A candidate explicitly cleared by an exception or reverse check is adjudicated; record that clearance in the matrix and do not leave it in either gap list.

For a positive result, include only records that participate in the stated violation. Context records used to calculate a running balance are not automatically finding records. For a no-anomaly result, include every record explicitly named by the task or covered by the submitted conclusion even though `anomaly_ids` is empty.

For a no-anomaly result, set `no_anomaly_coverage.complete` to boolean `true` and include the searched population, query conditions, checked rules, population count, and conclusion inside that object. A top-level `search_proof` string alone is not a replacement for `no_anomaly_coverage`.

## Blocking Rules

Set status to `blocked` when a finding lacks a valid record, a required policy basis is missing, a confirmed candidate is omitted, report figures conflict with analysis, or a no-anomaly answer lacks full search proof. Permit one targeted evidence supplement only.

Set status to `pass` only when evidence coverage is 100 percent and no blocking gap remains.
