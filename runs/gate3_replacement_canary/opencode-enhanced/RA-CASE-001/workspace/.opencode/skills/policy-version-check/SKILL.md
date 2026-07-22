---
name: policy-version-check
description: Resolve which policy version and clauses apply to an expense event. Use for effective dates, historical or repealed policies, replacements, transitions, conflicts, multiple policies, exemptions, or unclear applicability periods.
---

# Policy Version Check

Determine the policy that governed the business event. Never treat the newest retrieved document as automatically applicable.

## Trigger

Run the full check when dates, historical versions, replacements, transitions, conflicts, multiple documents, or exceptions matter. For a single unambiguous current policy, run the same procedure in compact form without a subagent.

## Procedure

1. Read policy metadata and the relevant clauses through `policy_query`.
2. Extract publication, effective, expiry, repeal, replacement, and transition information.
3. Build a policy timeline and compare it with the business period.
4. Identify the applicable policy and clause for each rule.
5. Record every excluded candidate policy and the reason it does not apply.
6. Mark unresolved status explicitly when the corpus does not determine applicability.

## Policy Researcher

Request `policy_researcher` through `authorize_audit_subagent` when there are at least two candidate policies, a historical/repealed/replacement relationship, conflicting requirements, an unclear applicable period, or multiple clauses supporting the conclusion. Register the native role's compact summary and artifacts through `complete_audit_subagent`. Invoke it at most once.

## Output

Write `work/policy_applicability.json`. The JSON includes applicable policies and clauses, excluded policies, policy status, effective and expiry dates, version relationships, conflicts, applicability or exclusion reasons, and unresolved items.

## Guardrails

- Cite only documents and clauses actually retrieved from the policy corpus.
- Do not infer missing dates or replacement relationships.
- Do not quote a policy without explaining why it applies to the audited period.

Finish only when every policy used in the conclusion has a dated applicability reason and every excluded candidate has an exclusion reason.
