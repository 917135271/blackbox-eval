#!/usr/bin/env python3
"""Aggregate office_supplies and communication expenses by employee-month
and compare against policy standards."""

import json
from collections import defaultdict
from datetime import date

# === Policy standards ===
STANDARDS = {
    "office_supplies": 600.00,
    "communication": 300.00,
}

# === Raw records from task ===
office_supplies_records = [
    {"record_id": "R900001", "employee_id": "E9001", "employee_name": "开发员工甲", "expense_date": "2025-01-05", "amount": 480.00, "expense_type": "office_supplies"},
    {"record_id": "R900002", "employee_id": "E9001", "employee_name": "开发员工甲", "expense_date": "2025-01-06", "amount": 480.00, "expense_type": "office_supplies"},
    {"record_id": "R900007", "employee_id": "E9001", "employee_name": "开发员工甲", "expense_date": "2025-04-08", "amount": 650.00, "expense_type": "office_supplies"},
    {"record_id": "R900008", "employee_id": "E9001", "employee_name": "开发员工甲", "expense_date": "2025-05-05", "amount": 590.00, "expense_type": "office_supplies"},
    {"record_id": "R900009", "employee_id": "E9002", "employee_name": "开发经理乙", "expense_date": "2025-05-05", "amount": 590.00, "expense_type": "office_supplies"},
]

communication_records = [
    {"record_id": "R900006", "employee_id": "E9001", "employee_name": "开发员工甲", "expense_date": "2025-03-01", "amount": 200.00, "expense_type": "communication"},
    {"record_id": "R900014", "employee_id": "E9001", "employee_name": "开发员工甲", "expense_date": "2025-09-03", "amount": 180.00, "expense_type": "communication"},
    {"record_id": "R900015", "employee_id": "E9001", "employee_name": "开发员工甲", "expense_date": "2025-09-20", "amount": 160.00, "expense_type": "communication"},
]

all_records = office_supplies_records + communication_records


def calendar_month(d):
    """Extract YYYY-MM from a date string."""
    return d[:7]  # "2025-01-05" -> "2025-01"


# === Aggregate by (employee_id, calendar_month, expense_type) ===
# Key: (employee_id, employee_name, month, expense_type)
aggregation = defaultdict(lambda: {"records": [], "total": 0.0})

for rec in all_records:
    key = (rec["employee_id"], rec["employee_name"], calendar_month(rec["expense_date"]), rec["expense_type"])
    aggregation[key]["records"].append(rec["record_id"])
    aggregation[key]["total"] = round(aggregation[key]["total"] + rec["amount"], 2)

# === Compare against standards ===
all_aggregations = []
violations = []

for (emp_id, emp_name, month, exp_type), data in sorted(aggregation.items()):
    standard = STANDARDS[exp_type]
    total = data["total"]
    excess = round(total - standard, 2)
    is_violation = excess > 0

    entry = {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "calendar_month": month,
        "expense_type": exp_type,
        "record_ids": sorted(data["records"]),
        "total": total,
        "standard": standard,
        "excess": excess if is_violation else 0.0,
        "is_violation": is_violation,
    }
    all_aggregations.append(entry)

    if is_violation:
        violations.append(entry)

# === Detailed analysis output ===
analysis = {
    "task": "DEV-007",
    "description": "Aggregate office_supplies and communication expenses by employee-month, compare against policy standards",
    "policy_standards": STANDARDS,
    "total_records_analyzed": len(all_records),
    "total_aggregations": len(all_aggregations),
    "all_aggregations": all_aggregations,
    "violations": violations,
    "violation_count": len(violations),
}

with open("/workspace/work/subagents/data_analyst/analysis.json", "w", encoding="utf-8") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

# === Compact summary ===
violating_record_ids = []
for v in violations:
    violating_record_ids.extend(v["record_ids"])
violating_record_ids = sorted(set(violating_record_ids))

key_findings = []
for v in violations:
    key_findings.append(
        f"{v['employee_id']} {v['employee_name']} exceeded {v['expense_type']} monthly cap "
        f"({v['standard']}元) in {v['calendar_month']}: total={v['total']}元, excess={v['total'] - v['standard']}元"
    )

if not violations:
    key_findings.append("No employee-month-expense_type combinations exceed policy standards.")

summary = {
    "decision": "anomaly_found" if violations else "no_anomaly",
    "key_findings": key_findings,
    "record_ids": violating_record_ids,
    "citations": [
        {"doc_id": "07_office_communication.md", "clause_no": "Article 2"},
        {"doc_id": "07_office_communication.md", "clause_no": "Article 3"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "Article 12"},
    ],
    "unresolved_items": [],
    "artifact_paths": [
        "/workspace/work/subagents/data_analyst/analysis.json",
        "/workspace/work/subagents/data_analyst/summary.json",
    ],
}

with open("/workspace/work/subagents/data_analyst/summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("=== ANALYSIS COMPLETE ===")
print(f"Aggregations: {len(all_aggregations)} total, {len(violations)} violations")
for v in violations:
    print(f"  VIOLATION: {v['employee_id']} {v['employee_name']} | {v['calendar_month']} | {v['expense_type']} | "
          f"total={v['total']} standard={v['standard']} excess={v['total'] - v['standard']}")
print(f"Violating record_ids: {violating_record_ids}")
print(f"Analysis saved to: /workspace/work/subagents/data_analyst/analysis.json")
print(f"Summary saved to: /workspace/work/subagents/data_analyst/summary.json")
