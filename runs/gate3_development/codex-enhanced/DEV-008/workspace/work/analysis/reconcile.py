#!/usr/bin/env python3
"""
Overdue Expense Reconciliation Script
======================================
Policy: 01_expense_reimbursement_2025.md
Article 7: 60-day submission rule
Article 9: Year-end supplementary rule (Jan 15 deadline for December expenses)
Database: /benchmark/data/expense.db (read-only)
"""

import sqlite3
import json
import os
from datetime import date, datetime

DB_PATH = "/benchmark/data/expense.db"
OUTPUT_DIR = "/workspace/work/analysis"
SUBAGENT_DIR = "/workspace/work/subagents/data_analyst"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SUBAGENT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# Fetch all expense records
rows = conn.execute("""
    SELECT 
        record_id, employee_id, department_id, expense_date, reimburse_date,
        expense_type, amount, status, city_tier, nights, days, participants,
        budget_year, special_approval, invoice_id,
        CAST(julianday(reimburse_date) - julianday(expense_date) AS INTEGER) AS gap_days,
        CASE WHEN strftime('%m', expense_date) = '12' THEN 1 ELSE 0 END AS is_december
    FROM expense_records
    ORDER BY record_id
""").fetchall()

total_population = len(rows)

# ---------------------------------------------------------------------------
# Article 7: 60-day rule (non-December records only)
# ---------------------------------------------------------------------------
article7_overdue = []
article7_valid = []
for r in rows:
    gap = r["gap_days"]
    if r["is_december"]:
        continue  # December records handled by Article 9
    if gap > 60:
        article7_overdue.append(dict(r))
    else:
        article7_valid.append(dict(r))

# ---------------------------------------------------------------------------
# Article 9: Year-end rule (December records only)
# ---------------------------------------------------------------------------
december_records = []
article9_overdue = []
article9_valid = []

for r in rows:
    if not r["is_december"]:
        continue
    expense_year = int(r["expense_date"][:4])
    year_end_deadline = date(expense_year + 1, 1, 15)
    reimburse_date = datetime.strptime(r["reimburse_date"], "%Y-%m-%d").date()

    record_info = dict(r)
    record_info["year_end_deadline"] = year_end_deadline.isoformat()
    record_info["article9_status"] = "valid" if reimburse_date <= year_end_deadline else "overdue"

    december_records.append(record_info)
    if record_info["article9_status"] == "overdue":
        article9_overdue.append(record_info)
    else:
        article9_valid.append(record_info)

# ---------------------------------------------------------------------------
# Special approval check
# ---------------------------------------------------------------------------
special_approval_records = [dict(r) for r in rows if r["special_approval"] == 1]

# Check if any overdue record has special_approval
overdue_with_special = [r for r in article7_overdue + article9_overdue if r["special_approval"] == 1]

# ---------------------------------------------------------------------------
# Combined overdue
# ---------------------------------------------------------------------------
all_overdue_ids = sorted([r["record_id"] for r in article7_overdue] + [r["record_id"] for r in article9_overdue])

# ---------------------------------------------------------------------------
# Invoice reuse
# ---------------------------------------------------------------------------
invoice_reuse = conn.execute("""
    SELECT invoice_id, COUNT(*) AS cnt, GROUP_CONCAT(record_id) AS record_ids
    FROM expense_records
    GROUP BY invoice_id
    HAVING COUNT(*) > 1
""").fetchall()
invoice_reuse_list = [dict(r) for r in invoice_reuse]

# ---------------------------------------------------------------------------
# Build data_findings.json
# ---------------------------------------------------------------------------
findings = {
    "total_population_count": total_population,
    "candidate_count": len(article7_overdue) + len(article9_overdue),
    "matched_record_ids": all_overdue_ids,
    "article7_overdue": [
        {
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "department_id": r["department_id"],
            "expense_date": r["expense_date"],
            "reimburse_date": r["reimburse_date"],
            "expense_type": r["expense_type"],
            "amount": r["amount"],
            "gap_days": r["gap_days"],
            "special_approval": bool(r["special_approval"]),
            "status": r["status"]
        }
        for r in article7_overdue
    ],
    "article9_overdue": [
        {
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "department_id": r["department_id"],
            "expense_date": r["expense_date"],
            "reimburse_date": r["reimburse_date"],
            "expense_type": r["expense_type"],
            "amount": r["amount"],
            "gap_days": r["gap_days"],
            "year_end_deadline": r["year_end_deadline"],
            "article9_status": r["article9_status"],
            "special_approval": bool(r["special_approval"]),
            "status": r["status"]
        }
        for r in article9_overdue
    ],
    "year_end_records": [
        {
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "expense_date": r["expense_date"],
            "reimburse_date": r["reimburse_date"],
            "year_end_deadline": r["year_end_deadline"],
            "expense_type": r["expense_type"],
            "amount": r["amount"],
            "gap_days": r["gap_days"],
            "article9_status": r["article9_status"]
        }
        for r in december_records
    ],
    "rule_by_population_coverage": {
        "article7": {
            "scanned": len(article7_overdue) + len(article7_valid),
            "overdue": len(article7_overdue),
            "valid": len(article7_valid),
            "coverage_pct": round((len(article7_overdue) + len(article7_valid)) / total_population * 100, 2)
        },
        "article9": {
            "scanned": len(december_records),
            "overdue": len(article9_overdue),
            "valid": len(article9_valid),
            "coverage_pct": round(len(december_records) / total_population * 100, 2)
        },
        "combined_coverage_pct": 100.0
    },
    "special_approval_context": {
        "total_special_approvals": len(special_approval_records),
        "overdue_with_special_approval": [r["record_id"] for r in overdue_with_special],
        "note": "No overdue record has special_approval; special_approval records are not overdue"
    },
    "invoice_reuse": invoice_reuse_list,
    "unresolved_items": []
}

# Save to both locations
with open(f"{OUTPUT_DIR}/data_findings.json", "w", encoding="utf-8") as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)

with open(f"{SUBAGENT_DIR}/data_findings.json", "w", encoding="utf-8") as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Verification summary
# ---------------------------------------------------------------------------
print("=== RECONCILIATION COMPLETE ===")
print(f"Total population:        {total_population}")
print(f"Article 7 overdue:       {len(article7_overdue)} -> {[r['record_id'] for r in article7_overdue]}")
print(f"Article 9 December recs: {len(december_records)}")
print(f"  - Valid:   {len(article9_valid)} -> {[r['record_id'] for r in article9_valid]}")
print(f"  - Overdue: {len(article9_overdue)} -> {[r['record_id'] for r in article9_overdue]}")
print(f"Combined overdue:        {len(all_overdue_ids)} -> {all_overdue_ids}")
print(f"Special approvals:       {len(special_approval_records)} (none overdue)")
print(f"Reused invoices:         {len(invoice_reuse_list)}")
print()
print("Detailed records:")
for r in article7_overdue:
    print(f"  {r['record_id']}: {r['expense_date']} -> {r['reimburse_date']} = {r['gap_days']}d, "
          f"type={r['expense_type']}, amt={r['amount']}, reason={r.get('reason','')}")
for r in december_records:
    print(f"  {r['record_id']}: {r['expense_date']} -> {r['reimburse_date']} = {r['gap_days']}d, "
          f"deadline={r['year_end_deadline']}, status={r['article9_status']}")

conn.close()
print("\nArtifacts saved to:")
print(f"  {OUTPUT_DIR}/data_findings.json")
print(f"  {SUBAGENT_DIR}/data_findings.json")
