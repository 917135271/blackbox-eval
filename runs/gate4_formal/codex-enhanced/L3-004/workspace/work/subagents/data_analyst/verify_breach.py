import sqlite3
import json

DB_PATH = "/benchmark/data/expense.db"

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

for dept_id, budget in dept_budgets.items():
    query = """
    SELECT record_id, reimburse_date, amount, special_approval, expense_type
    FROM expense_records
    WHERE department_id = ? AND status = 'approved'
    ORDER BY reimburse_date ASC, record_id ASC
    """
    cursor = conn.execute(query, (dept_id,))
    records = [dict(row) for row in cursor.fetchall()]
    
    cumulative = 0.0
    breach_idx = None
    prev_cumulative = 0.0
    
    for idx, rec in enumerate(records):
        prev_cumulative = cumulative
        cumulative += rec["amount"]
        if breach_idx is None and cumulative > budget:
            breach_idx = idx
            print(f"\n=== {dept_id} BREACH DETAIL ===")
            print(f"  Budget: {budget:,.2f}")
            print(f"  Record #{idx+1} of {len(records)} (0-indexed: {idx})")
            print(f"  Record: {rec['record_id']} | Date: {rec['reimburse_date']} | Amount: {rec['amount']:,.2f} | Type: {rec['expense_type']}")
            print(f"  Cumulative BEFORE this record: {prev_cumulative:,.2f}")
            print(f"  Cumulative AFTER this record:  {cumulative:,.2f}")
            print(f"  Budget exceeded by: {cumulative - budget:,.2f}")
            print(f"  Special Approval: {bool(rec['special_approval'])}")
            # Show the previous record too
            if idx > 0:
                prev_rec = records[idx-1]
                print(f"  Previous record: {prev_rec['record_id']} | Date: {prev_rec['reimburse_date']} | Amount: {prev_rec['amount']:,.2f}")
            break
    
    total = sum(r["amount"] for r in records)
    print(f"  Total of all {len(records)} records: {total:,.2f}")

conn.close()
