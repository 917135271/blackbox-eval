import sqlite3
import json
from datetime import datetime
from collections import defaultdict

db = sqlite3.connect('/benchmark/data/expense.db')
db.row_factory = sqlite3.Row

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

budgets = {r['department_id']: r['annual_budget'] for r in db.execute("SELECT * FROM departments")}
dept_names = {r['department_id']: r['department_name'] for r in db.execute("SELECT * FROM departments")}

def approval_tier(amount):
    if amount < 3000: return 'AR-01'
    elif amount < 10000: return 'AR-02'
    elif amount < 50000: return 'AR-03'
    elif amount < 200000: return 'AR-04'
    else: return 'AR-05'

tier_order = {'AR-01': 0, 'AR-02': 1, 'AR-03': 2, 'AR-04': 3, 'AR-05': 4}

# ===== 1. DUPLICATE =====
invoice_usage = defaultdict(list)
for r in records:
    invoice_usage[r['invoice_no']].append(r['record_id'])
duplicates = {inv: rids for inv, rids in invoice_usage.items() if len(rids) > 1}
print(f"DUPLICATE GROUPS: {len(duplicates)}")
for inv, rids in sorted(duplicates.items()):
    print(f"  {inv}: {rids}")

# ===== 2. SPLIT (with tier check) =====
by_emp_type = defaultdict(list)
for r in records:
    by_emp_type[(r['employee_id'], r['expense_type'])].append(r)

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
            max_ind_tier = max(tier_order[approval_tier(r['amount'])] for r in group)
            combined_tier = tier_order[approval_tier(total)]
            if combined_tier > max_ind_tier:
                split_groups.append({
                    'employee_id': emp_id,
                    'employee_name': group[0]['employee_name'],
                    'expense_type': etype,
                    'record_ids': [r['record_id'] for r in group],
                    'total_amount': round(total, 2),
                    'dates': [r['expense_date'] for r in group],
                    'combined_tier': approval_tier(total)
                })
        i = j

print(f"\nSPLIT GROUPS (tier escalation): {len(split_groups)}")
for g in sorted(split_groups, key=lambda x: (x['employee_id'], x['expense_type'], x['dates'][0])):
    print(f"  {g['employee_id']} {g['employee_name']} {g['expense_type']}: {g['record_ids']} total={g['total_amount']} ->{g['combined_tier']}")

# ===== 3. OVER-STANDARD (per-night for lodging) =====
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
        if tier and r['nights'] and r['nights'] > 0 and (level, tier) in travel_standards:
            std = travel_standards[(level, tier)]
            per_night = amount / r['nights']
            if per_night > std:
                over_standard.append({
                    'record_id': r['record_id'],
                    'rule': 'travel_lodging_exceed',
                    'standard_per_night': std,
                    'per_night': round(per_night, 2),
                    'amount': amount,
                    'nights': r['nights'],
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

print(f"\nOVER-STANDARD: {len(over_standard)}")
from collections import Counter
rc = Counter(os['rule'] for os in over_standard)
print(f"  Breakdown: {rc}")
for os in sorted(over_standard, key=lambda x: x['record_id']):
    if os['rule'] == 'travel_lodging_exceed':
        print(f"  {os['record_id']}: {os['rule']} per_night={os['per_night']} std={os['standard_per_night']} amount={os['amount']} nights={os['nights']} level={os['employee_level']} tier={os['city_tier']} {os['employee_name']}")
    elif os['rule'] == 'training_exceed':
        print(f"  {os['record_id']}: {os['rule']} amount={os['amount']} std={os['standard']} {os['employee_name']}")
    elif 'entertainment' in os['rule']:
        print(f"  {os['record_id']}: {os['rule']} amount={os['amount']} std={os['standard']} per_capita={os.get('per_capita','')} participants={os.get('participants','')} {os['employee_name']}")

# ===== 4. OVER-BUDGET =====
dept_cumulative = {}
for dept in budgets:
    dept_cumulative[dept] = {'total': 0.0, 'exceeded': False, 'key_record': None}

for r in sorted(records, key=lambda x: (x['department_id'], x['reimburse_date'], x['record_id'])):
    dept = r['department_id']
    if dept not in dept_cumulative:
        continue
    d = dept_cumulative[dept]
    if not d['exceeded']:
        d['total'] += r['amount']
        if d['total'] > budgets[dept]:
            if r['special_approval'] == 0:
                d['exceeded'] = True
                d['key_record'] = r['record_id']
                d['cumulative_at_key'] = round(d['total'], 2)

print(f"\nOVER-BUDGET:")
for dept, d in sorted(dept_cumulative.items()):
    status = "EXCEEDED" if d['exceeded'] else "OK"
    print(f"  {dept} ({dept_names[dept]}): {status} budget={budgets[dept]:.2f}")
    if d['exceeded']:
        print(f"    key_record={d['key_record']} cumulative_at_key={d['cumulative_at_key']:.2f}")

# ===== 5. OVERDUE (delay > 60) =====
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

print(f"\nOVERDUE (delay > 60): {len(overdue)}")
for od in sorted(overdue, key=lambda x: x['delay_days'], reverse=True):
    print(f"  {od['record_id']}: delay={od['delay_days']}d exp={od['expense_date']} reim={od['reimburse_date']} {od['employee_name']} {od['expense_type']} {od['amount']:.2f}")

# Save results
output = {
    'duplicates': {inv: rids for inv, rids in duplicates.items()},
    'split_groups': split_groups,
    'over_standard': over_standard,
    'over_budget': [{'department_id': dept, 'department_name': dept_names[dept], 'budget': budgets[dept],
                      'key_record': d['key_record'], 'cumulative_at_key': d['cumulative_at_key']}
                     for dept, d in sorted(dept_cumulative.items()) if d['exceeded']],
    'overdue': overdue
}
with open('/workspace/work/analysis3.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)
print("\nSaved to analysis3.json")
