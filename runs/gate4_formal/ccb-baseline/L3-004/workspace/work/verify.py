import sqlite3

DB_PATH = "/benchmark/data/expense.db"
conn = sqlite3.connect(DB_PATH)

# For each over-budget department, verify the critical record
depts_to_check = ['D001', 'D002', 'D003', 'D004', 'D005', 'D006']
budgets = dict(conn.execute("SELECT department_id, annual_budget FROM departments").fetchall())

for dept_id in depts_to_check:
    budget = budgets[dept_id]
    print(f"\n{'='*80}")
    print(f"Department: {dept_id}, Annual Budget: {budget:.2f}")
    
    # Get all approved records sorted by reimburse_date, record_id
    records = conn.execute("""
        SELECT record_id, reimburse_date, amount
        FROM expense_records
        WHERE department_id = ? AND status = 'approved'
        ORDER BY reimburse_date, record_id
    """, (dept_id,)).fetchall()
    
    cum = 0.0
    critical_found = None
    for i, (rid, rdate, amt) in enumerate(records):
        prev_cum = cum
        cum += amt
        if prev_cum <= budget and cum > budget and critical_found is None:
            critical_found = (rid, rdate, amt, cum, i+1)
            print(f"  >>> CRITICAL: record #{i+1}: {rid} on {rdate}, amount={amt:.2f}, cumulative went from {prev_cum:.2f} to {cum:.2f}")
    
    print(f"  Total records: {len(records)}, Total spent: {cum:.2f}, Over by: {cum - budget:.2f}")
    
conn.close()
