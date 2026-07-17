#!/usr/bin/env python3
"""Compute over-budget records per department."""
import sqlite3
import json

DB_PATH = "/benchmark/data/expense.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Get department budgets
depts = {}
for row in conn.execute("SELECT department_id, annual_budget FROM departments"):
    depts[row["department_id"]] = row["annual_budget"]

# For each over-budget department, find records after budget crossing
over_budget_depts = {k: v for k, v in depts.items() if k in ('D001','D002','D003','D004','D005','D006')}

results = {}
for dept_id, budget in sorted(over_budget_depts.items()):
    # Get all records for this department, ordered by expense_date, then record_id
    rows = conn.execute("""
        SELECT record_id, amount, expense_date, reimburse_date, expense_type, reason, status
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

    if crossing_idx is not None:
        # Records from crossing_idx onward are over-budget
        violation_records = [rows[i]["record_id"] for i in range(crossing_idx, len(rows))]
        results[dept_id] = {
            "budget": budget,
            "total_spent": cumulative,
            "total_records": len(rows),
            "crossing_idx": crossing_idx,
            "crossing_record_id": rows[crossing_idx]["record_id"],
            "crossing_date": rows[crossing_idx]["expense_date"],
            "cumulative_before": sum(rows[i]["amount"] for i in range(crossing_idx)),
            "violation_count": len(violation_records),
            "violation_amount": sum(rows[i]["amount"] for i in range(crossing_idx, len(rows))),
            "violation_records": violation_records
        }
        print(f"{dept_id}: budget={budget}, total={cumulative:.2f}, crossing at idx={crossing_idx}/{len(rows)}, "
              f"violation_count={len(violation_records)}, "
              f"violation_amount={results[dept_id]['violation_amount']:.2f}")
    else:
        results[dept_id] = {"error": "no crossing found"}

# Save results
with open("/workspace/work/budget_analysis.json", "w") as f:
    # Convert to serializable format
    serializable = {}
    for k, v in results.items():
        serializable[k] = {kk: vv for kk, vv in v.items()}
    json.dump(serializable, f, ensure_ascii=False, indent=2)

conn.close()
print("\nAnalysis saved to work/budget_analysis.json")
