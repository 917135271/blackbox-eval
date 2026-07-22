import sqlite3
import json

DB_PATH = "/benchmark/data/expense.db"

# Department budgets
dept_budgets = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

results = {}

for dept_id, budget in dept_budgets.items():
    # Get ALL approved records for this department, sorted by reimburse_date ASC, record_id ASC
    query = """
    SELECT record_id, record_no, employee_id, department_id, 
           expense_date, reimburse_date, expense_type, amount, 
           reason, invoice_id, status, special_approval,
           city_tier, nights, days, participants, budget_year
    FROM expense_records
    WHERE department_id = ? AND status = 'approved'
    ORDER BY reimburse_date ASC, record_id ASC
    """
    
    cursor = conn.execute(query, (dept_id,))
    records = [dict(row) for row in cursor.fetchall()]
    
    cumulative = 0.0
    breach_record = None
    records_before_breach = 0
    
    for idx, rec in enumerate(records):
        cumulative += rec["amount"]
        if breach_record is None and cumulative > budget:
            breach_record = rec
            records_before_breach = idx  # 0-indexed, means idx records were before/at breach
    
    if breach_record:
        total_spent = sum(r["amount"] for r in records)
        total_records = len(records)
        
        results[dept_id] = {
            "department_id": dept_id,
            "annual_budget": budget,
            "total_records": total_records,
            "total_spent": round(total_spent, 2),
            "breach_record_id": breach_record["record_id"],
            "breach_record_no": breach_record["record_no"],
            "breach_reimburse_date": breach_record["reimburse_date"],
            "breach_expense_date": breach_record["expense_date"],
            "breach_amount": breach_record["amount"],
            "breach_expense_type": breach_record["expense_type"],
            "breach_employee_id": breach_record["employee_id"],
            "breach_special_approval": bool(breach_record["special_approval"]),
            "cumulative_at_breach": round(cumulative, 2),
            "records_before_breach": records_before_breach,
            "all_records_sorted": [
                {
                    "record_id": r["record_id"],
                    "reimburse_date": r["reimburse_date"],
                    "amount": r["amount"],
                    "special_approval": bool(r["special_approval"]),
                    "expense_type": r["expense_type"],
                }
                for r in records
            ],
            "violation": not bool(breach_record["special_approval"]),
        }
    else:
        total_spent = sum(r["amount"] for r in records)
        results[dept_id] = {
            "department_id": dept_id,
            "annual_budget": budget,
            "total_records": len(records),
            "total_spent": round(total_spent, 2),
            "breach_record_id": None,
            "violation": False,
            "note": "No breach - total spending did not exceed budget",
        }

conn.close()

# Save detailed analysis
with open("/workspace/work/subagents/data_analyst/analysis.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

# Print summary
print("=" * 80)
print("CUMULATIVE BUDGET OVERRUN ANALYSIS")
print("=" * 80)
for dept_id in ["D001", "D002", "D003", "D004", "D005", "D006"]:
    r = results[dept_id]
    print(f"\n--- {dept_id} ---")
    print(f"  Annual Budget: {r['annual_budget']:,.2f}")
    print(f"  Total Records (Approved): {r['total_records']}")
    print(f"  Total Spent: {r['total_spent']:,.2f}")
    if r["breach_record_id"]:
        print(f"  Breach Record: {r['breach_record_id']} ({r['breach_record_no']})")
        print(f"    Reimburse Date: {r['breach_reimburse_date']}")
        print(f"    Expense Type: {r['breach_expense_type']}")
        print(f"    Amount: {r['breach_amount']:,.2f}")
        print(f"    Cumulative at Breach: {r['cumulative_at_breach']:,.2f}")
        print(f"    Special Approval: {r['breach_special_approval']}")
        print(f"    VIOLATION: {r['violation']}")
    else:
        print(f"  No breach detected")
print("\nDone.")
