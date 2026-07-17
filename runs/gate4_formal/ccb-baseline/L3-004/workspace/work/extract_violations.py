#!/usr/bin/env python3
"""Extract violation record IDs and build result structures."""
import sqlite3
import json

DB_PATH = "/benchmark/data/expense.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

dept_rows = conn.execute("SELECT department_id, annual_budget, department_name FROM departments").fetchall()
dept_budgets = {r["department_id"]: r["annual_budget"] for r in dept_rows}
dept_names = {r["department_id"]: r["department_name"] for r in dept_rows}

over_budget_depts = {
    'D001': 'BUDGET_OVERAGE_D001',
    'D002': 'BUDGET_OVERAGE_D002',
    'D003': 'BUDGET_OVERAGE_D003',
    'D004': 'BUDGET_OVERAGE_D004',
    'D005': 'BUDGET_OVERAGE_D005',
    'D006': 'BUDGET_OVERAGE_D006',
}

all_violation_records = []
anomaly_details = {}

for dept_id, anomaly_id in sorted(over_budget_depts.items()):
    budget = dept_budgets[dept_id]

    rows = conn.execute("""
        SELECT record_id, amount, expense_date
        FROM expense_records
        WHERE department_id = ?
        ORDER BY expense_date ASC, record_id ASC
    """, (dept_id,)).fetchall()

    cumulative = 0.0
    crossing_idx = None

    for i, row in enumerate(rows):
        cumulative += row["amount"]
        if crossing_idx is None and cumulative > budget:
            crossing_idx = i

    violation_ids = [rows[i]["record_id"] for i in range(crossing_idx, len(rows))]
    all_violation_records.extend(violation_ids)

    dept_name = dept_names[dept_id]

    anomaly_details[anomaly_id] = {
        "dept_id": dept_id,
        "dept_name": dept_name,
        "budget": budget,
        "total_spent": cumulative,
        "crossing_record": rows[crossing_idx]["record_id"],
        "crossing_date": rows[crossing_idx]["expense_date"],
        "violation_ids": violation_ids,
        "violation_count": len(violation_ids),
        "usage_rate": round(cumulative / budget, 4)
    }

# Print summary
for aid, detail in sorted(anomaly_details.items()):
    print(f"{aid}: {detail['dept_name']}({detail['dept_id']}) budget={detail['budget']:.2f} "
          f"spent={detail['total_spent']:.2f} usage={detail['usage_rate']*100:.2f}% "
          f"violations={detail['violation_count']}")

print(f"\nTotal violation records: {len(all_violation_records)}")
print(f"Unique violation records: {len(set(all_violation_records))}")

# Ensure uniqueness
assert len(all_violation_records) == len(set(all_violation_records)), "Duplicate record IDs found!"

# Save details
with open("/workspace/work/anomaly_details.json", "w") as f:
    json.dump(anomaly_details, f, ensure_ascii=False, indent=2)

with open("/workspace/work/all_violation_records.json", "w") as f:
    json.dump(sorted(all_violation_records), f, ensure_ascii=False, indent=2)

conn.close()
print("\nFiles saved.")
