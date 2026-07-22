import sqlite3
import json
from datetime import datetime
from collections import defaultdict

db = sqlite3.connect('/benchmark/data/expense.db')
db.row_factory = sqlite3.Row

# Get all approved records with full details
records = list(db.execute("""
    SELECT er.*, inv.invoice_no, inv.vendor_name, 
           emp.employee_name, emp.employee_level, emp.position_role,
           dept.department_name
    FROM expense_records er
    JOIN invoices inv ON er.invoice_id = inv.invoice_id
    JOIN employees emp ON er.employee_id = emp.employee_id
    JOIN departments dept ON er.department_id = dept.department_id
    WHERE er.status = 'approved'
    ORDER BY er.record_id
"""))

# Get budgets
budgets = {r['department_id']: r['annual_budget'] for r in db.execute("SELECT * FROM departments")}
dept_names = {r['department_id']: r['department_name'] for r in db.execute("SELECT * FROM departments")}

print(f"Total approved records: {len(records)}")

# ===== 1. DUPLICATE REIMBURSEMENT =====
invoice_usage = defaultdict(list)
for r in records:
    invoice_usage[r['invoice_no']].append(r['record_id'])

duplicates = {inv: rids for inv, rids in invoice_usage.items() if len(rids) > 1}
print(f"\n=== DUPLICATE GROUPS: {len(duplicates)} ===")
for inv, rids in sorted(duplicates.items()):
    print(f"  {inv}: {rids}")

# ===== 2. SPLIT REIMBURSEMENT =====
by_emp_type = defaultdict(list)
for r in records:
    key = (r['employee_id'], r['expense_type'])
    by_emp_type[key].append(r)

split_groups = []
for (emp_id, etype), recs in by_emp_type.items():
    if len(recs) < 2:
        continue
    recs_sorted = sorted(recs, key=lambda x: x['expense_date'])
    
    i = 0
    while i < len(recs_sorted):
        group = [recs_sorted[i]]
        base_date = datetime.strptime(recs_sorted[i]['expense_date'], '%Y-%m-%d')
        j = i + 1
        while j < len(recs_sorted):
            curr_date = datetime.strptime(recs_sorted[j]['expense_date'], '%Y-%m-%d')
            if (curr_date - base_date).days <= 7:
                group.append(recs_sorted[j])
                j += 1
            else:
                break
        if len(group) >= 2:
            total = sum(r['amount'] for r in group)
            split_groups.append({
                'employee_id': emp_id,
                'employee_name': group[0]['employee_name'],
                'expense_type': etype,
                'record_ids': [r['record_id'] for r in group],
                'total_amount': round(total, 2),
                'dates': [r['expense_date'] for r in group]
            })
        i = j

print(f"\n=== SPLIT GROUPS: {len(split_groups)} ===")
for g in sorted(split_groups, key=lambda x: (x['employee_id'], x['expense_type'], x['dates'][0])):
    print(f"  {g['employee_id']} {g['employee_name']} {g['expense_type']}: {g['record_ids']} dates={g['dates']} total={g['total_amount']}")

# ===== 3. OVER-STANDARD =====
travel_standards = {
    ('E1', 'A'): 450, ('E1', 'B'): 380, ('E1', 'C'): 300,
    ('M1', 'A'): 650, ('M1', 'B'): 550, ('M1', 'C'): 450,
    ('D1', 'A'): 850, ('D1', 'B'): 700, ('D1', 'C'): 600,
    ('X1', 'A'): 1100, ('X1', 'B'): 900, ('X1', 'C'): 750,
}

over_standard = []
for r in records:
    amount = r['amount']
    etype = r['expense_type']
    level = r['employee_level']
    tier = r['city_tier']
    
    if etype == 'travel_lodging':
        if tier and (level, tier) in travel_standards:
            std = travel_standards[(level, tier)]
            if amount > std:
                over_standard.append({
                    'record_id': r['record_id'],
                    'rule': 'travel_lodging_exceed',
                    'standard': std,
                    'amount': amount,
                    'employee_level': level,
                    'city_tier': tier,
                    'employee_name': r['employee_name']
                })
    
    elif etype == 'business_entertainment':
        if amount > 5000:
            over_standard.append({
                'record_id': r['record_id'],
                'rule': 'entertainment_event_exceed',
                'standard': 5000,
                'amount': amount,
                'employee_name': r['employee_name']
            })
        elif r['participants'] and r['participants'] > 0 and amount / r['participants'] > 300:
            over_standard.append({
                'record_id': r['record_id'],
                'rule': 'entertainment_per_capita_exceed',
                'standard': 300,
                'per_capita': round(amount / r['participants'], 2),
                'amount': amount,
                'participants': r['participants'],
                'employee_name': r['employee_name']
            })
    
    elif etype == 'training_fee':
        if amount > 3500:
            over_standard.append({
                'record_id': r['record_id'],
                'rule': 'training_exceed',
                'standard': 3500,
                'amount': amount,
                'employee_name': r['employee_name']
            })

print(f"\n=== OVER-STANDARD: {len(over_standard)} ===")
for os in sorted(over_standard, key=lambda x: x['record_id']):
    print(f"  {os['record_id']}: {os['rule']} std={os['standard']} amount={os['amount']:.2f} {os.get('employee_name','')}")

# ===== 4. OVER-BUDGET =====
dept_cumulative = {}
for dept in budgets:
    dept_cumulative[dept] = {'total': 0.0, 'records': [], 'exceeded': False, 'key_record': None}

for r in sorted(records, key=lambda x: (x['department_id'], x['reimburse_date'], x['record_id'])):
    dept = r['department_id']
    if dept not in dept_cumulative:
        continue
    d = dept_cumulative[dept]
    if d['exceeded']:
        d['records'].append(r['record_id'])
        d['total'] += r['amount']
    else:
        d['total'] += r['amount']
        d['records'].append(r['record_id'])
        if d['total'] > budgets[dept]:
            if r['special_approval'] == 0:
                d['exceeded'] = True
                d['key_record'] = r['record_id']
                d['cumulative_at_key'] = round(d['total'], 2)

print(f"\n=== OVER-BUDGET ===")
over_budget = []
for dept, d in sorted(dept_cumulative.items()):
    if d['exceeded']:
        print(f"  {dept} ({dept_names[dept]}): budget={budgets[dept]:.2f} cumulative_at_key={d['cumulative_at_key']:.2f} key_record={d['key_record']}")
        over_budget.append({
            'department_id': dept,
            'department_name': dept_names[dept],
            'budget': budgets[dept],
            'key_record': d['key_record'],
            'cumulative_at_key': d['cumulative_at_key']
        })

# ===== 5. OVERDUE =====
overdue = []
for r in records:
    exp_date = datetime.strptime(r['expense_date'], '%Y-%m-%d')
    reim_date = datetime.strptime(r['reimburse_date'], '%Y-%m-%d')
    delay = (reim_date - exp_date).days
    if delay > 60:
        overdue.append({
            'record_id': r['record_id'],
            'expense_date': r['expense_date'],
            'reimburse_date': r['reimburse_date'],
            'delay_days': delay,
            'amount': r['amount'],
            'expense_type': r['expense_type'],
            'employee_name': r['employee_name'],
            'department_name': r['department_name']
        })

print(f"\n=== OVERDUE: {len(overdue)} ===")
for od in sorted(overdue, key=lambda x: x['delay_days'], reverse=True):
    print(f"  {od['record_id']}: delay={od['delay_days']}d exp={od['expense_date']} reim={od['reimburse_date']} {od['employee_name']} {od['expense_type']} {od['amount']:.2f}")

# Save all analysis to JSON
output = {
    'duplicates': {inv: rids for inv, rids in duplicates.items()},
    'split_groups': split_groups,
    'over_standard': over_standard,
    'over_budget': over_budget,
    'overdue': overdue
}

with open('/workspace/work/analysis.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

print("\nAnalysis saved to /workspace/work/analysis.json")
