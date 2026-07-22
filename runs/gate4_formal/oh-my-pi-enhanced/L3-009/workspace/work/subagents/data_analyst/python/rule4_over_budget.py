"""
RULE 4: 超预算 (Over-Budget) - Cumulative Budget Tracking

For each department:
1. Order records by reimburse_date ASC, then record_id ASC
2. Calculate cumulative sum
3. Find first record where cumulative > annual_budget AND special_approval=0
4. Records after crossing with special_approval=1 are NOT anomalies
"""

from collections import defaultdict

def load_department_budgets(db_path):
    """Extract department budgets from the database."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT department_id, annual_budget FROM departments")
    return dict(cur.fetchall())

def detect_over_budget(records, dept_budgets):
    """Returns list of crossing record dicts."""
    dept_records = defaultdict(list)
    for r in records:
        dept_records[r['department_id']].append(r)
    
    anomalies = []
    
    for dept_id, dept_recs in dept_records.items():
        budget = dept_budgets.get(dept_id)
        if not budget:
            continue
        
        # Sort by reimburse_date ASC, record_id ASC
        sorted_recs = sorted(dept_recs, key=lambda x: (x['reimburse_date'], x['record_id']))
        
        cumulative = 0.0
        for r in sorted_recs:
            cumulative += r['amount']
            if cumulative > budget and r['special_approval'] == 0:
                anomalies.append({
                    'department_id': dept_id,
                    'annual_budget': budget,
                    'cumulative_at_crossing': cumulative,
                    'crossing_record_id': r['record_id']
                })
                break
    
    return anomalies
