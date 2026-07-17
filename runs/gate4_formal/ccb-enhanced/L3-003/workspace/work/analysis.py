import sqlite3
import json
from collections import defaultdict

conn = sqlite3.connect('file:/benchmark/data/expense.db?mode=ro', uri=True)

# Get all records with employee info
cursor = conn.execute("""
SELECT er.record_id, er.employee_id, e.employee_name, e.employee_level, 
       er.expense_type, er.amount, er.expense_date, er.city_tier, er.nights, 
       er.days, er.participants, er.special_approval, er.reason, er.department_id
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
ORDER BY er.record_id
""")
records = {}
for row in cursor:
    records[row[0]] = {
        'record_id': row[0], 'employee_id': row[1], 'employee_name': row[2],
        'employee_level': row[3], 'expense_type': row[4], 'amount': row[5],
        'expense_date': row[6], 'city_tier': row[7], 'nights': row[8],
        'days': row[9], 'participants': row[10], 'special_approval': row[11],
        'reason': row[12], 'department_id': row[13]
    }

# --- Split billing: group records by employee+type, then find 7-day windows with sum>=3000 ---
from datetime import datetime, timedelta

def find_split_groups(records_dict, exclude_planted=True):
    """Find groups of same employee, same type, within 7-day window, sum>=3000"""
    # Group by employee_id + expense_type
    groups = defaultdict(list)
    for rid, r in records_dict.items():
        if r['special_approval'] != 0:
            continue
        if exclude_planted and rid >= 'R004200':
            continue
        key = (r['employee_id'], r['expense_type'])
        groups[key].append(r)
    
    # For each group, find clusters within 7-day windows
    all_clusters = []
    for key, recs in groups.items():
        if len(recs) < 2:
            continue
        recs.sort(key=lambda x: x['expense_date'])
        
        # Use sliding window approach
        for i in range(len(recs)):
            window_recs = [recs[i]]
            window_sum = recs[i]['amount']
            d0 = datetime.strptime(recs[i]['expense_date'], '%Y-%m-%d')
            for j in range(i+1, len(recs)):
                dj = datetime.strptime(recs[j]['expense_date'], '%Y-%m-%d')
                if (dj - d0).days <= 7:
                    window_recs.append(recs[j])
                    window_sum += recs[j]['amount']
                else:
                    break
            if len(window_recs) >= 2 and window_sum >= 3000:
                all_clusters.append({
                    'employee_id': key[0],
                    'employee_name': window_recs[0]['employee_name'],
                    'expense_type': key[1],
                    'record_ids': sorted([r['record_id'] for r in window_recs]),
                    'total_amount': window_sum,
                    'record_count': len(window_recs),
                    'date_range': f"{window_recs[0]['expense_date']} ~ {window_recs[-1]['expense_date']}",
                    'day_span': (datetime.strptime(window_recs[-1]['expense_date'], '%Y-%m-%d') - d0).days
                })
    
    # Deduplicate: keep only maximal clusters (supersets subsume subsets)
    # Sort by size descending, then remove subsets
    all_clusters.sort(key=lambda x: (-len(x['record_ids']), -x['total_amount']))
    
    deduped = []
    used_rids = set()
    for c in all_clusters:
        c_rids = set(c['record_ids'])
        if c_rids.issubset(used_rids):
            continue
        # Check if this adds new records
        new_rids = c_rids - used_rids
        if len(new_rids) > 0:
            # Keep the cluster that covers the most records
            deduped.append(c)
            used_rids.update(c_rids)
    
    return deduped

# Find natural split billing groups
natural_splits = find_split_groups(records)
print(f"Natural split billing groups: {len(natural_splits)}")
for s in natural_splits[:5]:
    print(f"  {s['employee_name']} {s['expense_type']}: {s['record_count']} records, {s['total_amount']:.2f}, {s['date_range']}")

# Find planted split billing groups
planted_splits = find_split_groups({k:v for k,v in records.items() if k >= 'R004200' and k <= 'R004240'}, exclude_planted=False)
print(f"\nPlanted split billing groups: {len(planted_splits)}")
for s in planted_splits:
    print(f"  {s['employee_name']} {s['expense_type']}: {s['record_ids']} total={s['total_amount']:.2f}")

# --- Budget exceedance ---
dept_budgets = {
    'D001': ('投资银行部', 230395.17), 'D002': ('固定收益部', 107785.42),
    'D003': ('财富管理部', 109772.07), 'D004': ('研究所', 264890.39),
    'D005': ('机构业务部', 278540.94), 'D006': ('运营管理部', 340961.75),
    'D007': ('信息技术部', 301500.00), 'D008': ('合规风控部', 381600.00),
    'D009': ('财务管理部', 191300.00), 'D010': ('人力资源部', 164500.00)
}

# Find first crossing record per overspent department
dept_records = defaultdict(list)
for rid, r in records.items():
    dept_records[r['department_id']].append(r)

budget_crossings = []
for did, (dname, budget) in dept_budgets.items():
    recs = sorted(dept_records[did], key=lambda x: x['expense_date'])
    running = 0
    for r in recs:
        running += r['amount']
        if running > budget and (running - r['amount']) <= budget:
            budget_crossings.append({
                'department_id': did, 'department_name': dname,
                'annual_budget': budget, 'record_id': r['record_id'],
                'amount': r['amount'], 'expense_date': r['expense_date'],
                'running_total': running, 'before_total': running - r['amount']
            })
            break

print(f"\nBudget crossing records:")
for b in budget_crossings:
    print(f"  {b['department_name']}: {b['record_id']} on {b['expense_date']}, running={b['running_total']:.2f} > budget={b['annual_budget']:.2f}")

# --- Monthly office_supplies violations ---
cursor = conn.execute("""
SELECT er.employee_id, e.employee_name, strftime('%Y-%m', er.expense_date) AS month,
       SUM(er.amount) AS total_amount, COUNT(*) AS record_count,
       GROUP_CONCAT(er.record_id, ',') AS record_ids
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
WHERE er.expense_type = 'office_supplies' AND er.special_approval = 0
GROUP BY er.employee_id, strftime('%Y-%m', er.expense_date)
HAVING SUM(er.amount) > 600
ORDER BY total_amount DESC
""")
office_violations = []
for row in cursor:
    office_violations.append({
        'employee_id': row[0], 'employee_name': row[1], 'month': row[2],
        'total_amount': row[3], 'record_count': row[4],
        'record_ids': row[5].split(',')
    })
print(f"\nOffice supplies violations: {len(office_violations)}")

# --- Monthly communication violations ---
cursor = conn.execute("""
SELECT er.employee_id, e.employee_name, strftime('%Y-%m', er.expense_date) AS month,
       SUM(er.amount) AS total_amount, COUNT(*) AS record_count,
       GROUP_CONCAT(er.record_id, ',') AS record_ids
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
WHERE er.expense_type = 'communication' AND er.special_approval = 0
GROUP BY er.employee_id, strftime('%Y-%m', er.expense_date)
HAVING SUM(er.amount) > 300
ORDER BY total_amount DESC
""")
comm_violations = []
for row in cursor:
    comm_violations.append({
        'employee_id': row[0], 'employee_name': row[1], 'month': row[2],
        'total_amount': row[3], 'record_count': row[4],
        'record_ids': row[5].split(',')
    })
print(f"Communication violations: {len(comm_violations)}")

# Save all findings
findings = {
    'natural_split_billing': natural_splits,
    'planted_split_billing': planted_splits,
    'budget_crossings': budget_crossings,
    'office_supplies_violations': office_violations,
    'communication_violations': comm_violations
}

with open('/workspace/work/analysis/findings.json', 'w') as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)

print("\nFindings saved to work/analysis/findings.json")
conn.close()
