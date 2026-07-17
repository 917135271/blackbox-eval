---
name: false-positive-review
description: Independently challenge preliminary audit findings. Use for exceptions, approval exemptions, threshold or date boundaries, historical policies, inconsistent evidence, comprehensive tasks, or broad no-anomaly conclusions.
---

# False Positive Review

Try to disprove the preliminary conclusion before final reporting.

## Trigger

Run when a rule has exceptions or approvals, values are near a boundary, historical or cross-period policies apply, policy and data results conflict, the evidence check found a gap, the task is comprehensive, or a broad no-anomaly conclusion requires a second look.

Do not run for a straightforward positive one-rule task with no boundary, exception, conflict, or evidence gap.

## Procedure

1. Form the strongest plausible compliant explanation for every finding.
2. Recheck equality, amount, date, timezone, and effective-date boundaries.
3. Recheck exemptions, special approvals, transition clauses, classification, and employee role.
4. Fetch record detail when an exemption field is absent from a list result. If a valid special approval or explicit exception applies, remove that record from the finding and document the clearance before rebuilding the evidence matrix.
5. Recheck duplicates, reversals, cancellations, nulls, and double-counted aggregates.
6. For cumulative budget findings, challenge each record separately: remove records before the crossing point, retain an unapproved record that causes the first exceedance, and remove later records covered by valid special approval. Department totals remain calculation context and do not make every department record anomalous.
7. When a per-person, per-day, per-night, city-tier, or approval decision depends on a field absent from a preview, fetch the record detail. Do not clear the candidate from the preview alone.
8. For no-anomaly results, rerun the omission test against scope and rules.
9. Decide `pass`, `reject`, or `needs_more_evidence` and state the exact reason.

## Independent Reviewer

Request `independent_reviewer` through `authorize_audit_subagent` at most once. Give it only the preliminary findings, evidence matrix, necessary policy clauses, and artifact paths. Do not give it the main agent's full trajectory. The reviewer cannot create another subagent. Register its summary and artifacts through `complete_audit_subagent` before accepting or resolving the review decision.

## Output

Write `work/independent_review.json`. The JSON includes decision, challenged findings, supporting evidence, opposing evidence, exceptions or boundaries, required changes, one targeted supplemental query if needed, rationale, and unresolved conflicts.

After `needs_more_evidence`, run only the specified supplement and do not invoke the reviewer again. Do not report while a material conflict remains unresolved.
