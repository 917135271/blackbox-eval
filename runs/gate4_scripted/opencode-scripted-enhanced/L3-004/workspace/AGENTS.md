# Scripted Audit Workflow

This experiment moves deterministic orchestration out of the model context.

Read `work/scripted_workflow.json` once. Follow only the route and Skills listed there. Do not create or maintain an audit plan, generated evidence matrix, validation report, task-state snapshot, artifact index, or context checkpoint manually; the scripted control layer owns those files.

Use policy and expense tools to gather evidence. Use Shell, SQLite, and Python only when they materially help answer the task. A listed subagent role is optional, not mandatory: authorize it only when the delegated investigation is genuinely independent or broad enough to justify the extra context and time. Simple retrieval, one-record comparison, and direct calculations stay in the main agent.

After deciding the answer, update the pre-created `work/final_result.json` with exactly four semantic fields: `anomaly_ids`, `record_ids`, `answer`, and `citations`. Also update `work/evidence_input.json`: for a positive result, write one row per anomaly with only that finding's actual `record_ids`, `citations`, and verified `facts`; for a no-anomaly result, record the searched population, query conditions, checked rules, population count, conclusion, and set `complete=true`. This semantic evidence must come from the investigation. The script will normalize and check it, but will not infer or duplicate evidence for you.

Then call `validate_audit_result` with an empty argument object. The scripted control layer reads both files, checks exact anomaly/record/citation coverage, generates the common evidence matrix and validation report, updates the final task-state snapshot, and records a recoverable checkpoint. Repair only the errors returned by preflight. Once preflight returns `valid=true`, call `submit_audit_result` with an empty argument object. Avoid embedding the full Chinese answer in MCP arguments because some compatibility runtimes corrupt long nested tool JSON.

Do not call `checkpoint_audit_context` unless the scripted control layer explicitly reports a failure. Do not invoke the removed `evidence-coverage-check` or `result-validator` Skills. Format, exact-set consistency, and workflow success are script responsibilities; policy interpretation, evidence retrieval, finding-to-evidence mapping, audit judgment, and the answer remain model responsibilities. The snapshots make the task recoverable but do not claim native in-model context compression.
