
const result = {
  anomaly_ids: ["ANOM-001","ANOM-002","ANOM-003","ANOM-004","ANOM-005","ANOM-006"],
  record_ids: ["R000002","R004201","R000005","R004202","R000020","R004203","R000028","R004204","R000037","R004205","R000055","R004206"],
  answer: "2025 full year duplicate reimbursement scan found 6 anomalies per Article 10",
  citations: [{"doc_id":"01_expense_reimbursement_2025.md","clause_no":"10"}]
};

const r1 = await agent({
  description: "validate preflight",
  prompt: "SearchExtraTools query 'select:mcp__plugin_securities-expense-audit_audit_control__validate_audit_result' then ExecuteExtraTool with tool_name 'mcp__plugin_securities-expense-audit_audit_control__validate_audit_result' params {\"result\": " + JSON.stringify(result) + ", \"evidence_matrix_path\": \"work/evidence_matrix.json\", \"validation_report_path\": \"work/validation_report.json\"}. Report the response.",
  subagent_type: "general-purpose"
});

return {validate_result: r1};
