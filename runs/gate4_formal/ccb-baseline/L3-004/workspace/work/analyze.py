import sqlite3
import json

DB_PATH = "/benchmark/data/expense.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Get department budgets
depts = {}
for row in conn.execute("SELECT department_id, department_name, annual_budget FROM departments"):
    depts[row['department_id']] = {
        'name': row['department_name'],
        'budget': row['annual_budget']
    }

# Get all approved expense records, sorted by reimburse_date, record_id
query = """
SELECT record_id, department_id, reimburse_date, amount, expense_type, reason
FROM expense_records
WHERE status = 'approved'
ORDER BY department_id, reimburse_date, record_id
"""

results = {}
for dept_id in depts:
    results[dept_id] = {
        'name': depts[dept_id]['name'],
        'budget': depts[dept_id]['budget'],
        'cumulative': 0.0,
        'critical_record': None,
        'critical_cumulative': 0.0,
        'over_budget': False,
        'total_records': 0,
        'total_spent': 0.0,
        'records_before_critical': 0,
    }

cursor = conn.execute(query)
for row in cursor:
    dept_id = row['department_id']
    if dept_id not in results:
        continue
    
    amount = row['amount']
    r = results[dept_id]
    r['total_records'] += 1
    r['total_spent'] += amount
    
    # If not yet over budget, accumulate
    if not r['over_budget']:
        r['cumulative'] += amount
        if r['cumulative'] > r['budget']:
            r['over_budget'] = True
            r['critical_record'] = row['record_id']
            r['critical_cumulative'] = round(r['cumulative'], 2)
            r['records_before_critical'] = r['total_records'] - 1
    else:
        # Still count after critical
        pass

conn.close()

# Report results
print("=" * 90)
print(f"{'Dept':6s} {'Department Name':12s} {'Budget':>10s} {'Total Spent':>12s} {'Over?':5s} {'Critical Record':14s} {'Cum@Critical':>14s}")
print("-" * 90)

over_budget_depts = []
for dept_id in sorted(results.keys()):
    r = results[dept_id]
    print(f"{dept_id:6s} {r['name']:12s} {r['budget']:>10.2f} {r['total_spent']:>12.2f} {'YES' if r['over_budget'] else 'no':>5s} {r['critical_record'] or 'N/A':14s} {r['critical_cumulative']:>14.2f}")
    if r['over_budget']:
        over_budget_depts.append(dept_id)

print("\n" + "=" * 90)
print("OVER BUDGET DEPARTMENTS (no special approval):")
for dept_id in over_budget_depts:
    r = results[dept_id]
    print(f"  {dept_id} ({r['name']}): Budget={r['budget']:.2f}, Total={r['total_spent']:.2f}, "
          f"Over by={r['total_spent']-r['budget']:.2f}")
    print(f"    Critical record: {r['critical_record']} (cumulative at this point: {r['critical_cumulative']:.2f})")

# Save intermediate results
output = {}
for dept_id in over_budget_depts:
    r = results[dept_id]
    output[dept_id] = {
        'department_name': r['name'],
        'annual_budget': r['budget'],
        'total_spent': r['total_spent'],
        'critical_record_id': r['critical_record'],
        'cumulative_at_critical': r['critical_cumulative'],
        'total_records': r['total_records'],
        'records_before_critical': r['records_before_critical'],
        'over_by': round(r['total_spent'] - r['budget'], 2)
    }

with open('/workspace/work/analysis_result.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nResults saved to work/analysis_result.json")
