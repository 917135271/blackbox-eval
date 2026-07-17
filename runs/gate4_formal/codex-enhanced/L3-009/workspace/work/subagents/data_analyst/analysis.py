import sqlite3
import json
from datetime import date, timedelta, datetime
from collections import defaultdict

DB = "/benchmark/data/expense.db"

def get_db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

# === R1: 时限超期 ===
def r1_analysis():
    """Art.7-9: reimburse delay > 60 days, with year-end grace to 2026-01-15"""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name, 
               er.department_id, d.department_name,
               er.expense_date, er.reimburse_date, er.expense_type, 
               er.amount, er.reason, er.status
        FROM expense_records er
        JOIN employees e ON er.employee_id = e.employee_id
        JOIN departments d ON er.department_id = d.department_id
        WHERE er.expense_date >= '2025-01-01' AND er.expense_date <= '2025-12-31'
          AND er.status = 'approved'
    """)
    rows = cur.fetchall()
    
    violations = []
    for r in rows:
        exp_date = date.fromisoformat(r['expense_date'])
        reim_date = date.fromisoformat(r['reimburse_date'])
        
        if exp_date >= date(2025, 11, 16):
            if reim_date > date(2026, 1, 15):
                diff = (reim_date - exp_date).days
                violations.append({**dict(r), 'delay_days': diff, 'rule': 'R1_year_end'})
        else:
            diff = (reim_date - exp_date).days
            if diff > 60:
                violations.append({**dict(r), 'delay_days': diff, 'rule': 'R1_standard'})
    
    conn.close()
    return violations

# === R2: 重复报销 ===
def r2_analysis():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT i.invoice_no, i.invoice_id, i.vendor_name, i.invoice_date, i.amount, i.expense_type,
               COUNT(er.record_id) as usage_count,
               GROUP_CONCAT(er.record_id) as record_ids
        FROM invoices i
        JOIN expense_records er ON er.invoice_id = i.invoice_id
        WHERE er.expense_date >= '2025-01-01' AND er.expense_date <= '2025-12-31'
        GROUP BY i.invoice_id
        HAVING usage_count >= 2
    """)
    reused = cur.fetchall()
    
    result = []
    for inv in reused:
        record_ids = inv['record_ids'].split(',')
        result.append({
            'invoice_no': inv['invoice_no'],
            'invoice_id': inv['invoice_id'],
            'vendor_name': inv['vendor_name'],
            'invoice_date': inv['invoice_date'],
            'amount': inv['amount'],
            'expense_type': inv['expense_type'],
            'usage_count': inv['usage_count'],
            'record_ids': record_ids
        })
    
    conn.close()
    return result

# === R3: 拆分规避审批 ===
def r3_analysis():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name, 
               er.department_id, d.department_name,
               er.expense_date, er.reimburse_date, er.expense_type, 
               er.amount, er.reason, er.status,
               er.city_tier, er.nights, er.days, er.participants, er.special_approval
        FROM expense_records er
        JOIN employees e ON er.employee_id = e.employee_id
        JOIN departments d ON er.department_id = d.department_id
        WHERE er.expense_date >= '2025-01-01' AND er.expense_date <= '2025-12-31'
          AND er.status = 'approved'
        ORDER BY er.employee_id, er.expense_type, er.expense_date
    """)
    rows = cur.fetchall()
    
    groups = defaultdict(list)
    for r in rows:
        key = (r['employee_id'], r['expense_type'])
        groups[key].append(dict(r))
    
    violations = []
    for key, recs in groups.items():
        if len(recs) < 2:
            continue
        
        recs.sort(key=lambda x: x['expense_date'])
        
        i = 0
        while i < len(recs):
            cluster = [recs[i]]
            j = i + 1
            while j < len(recs):
                prev_date = date.fromisoformat(cluster[-1]['expense_date'])
                curr_date = date.fromisoformat(recs[j]['expense_date'])
                if (curr_date - prev_date).days <= 7:
                    cluster.append(recs[j])
                    j += 1
                else:
                    break
            
            if len(cluster) >= 2:
                total = sum(r['amount'] for r in cluster)
                if total >= 10000:
                    violations.append({
                        'employee_id': key[0],
                        'employee_name': cluster[0]['employee_name'],
                        'expense_type': key[1],
                        'cluster_size': len(cluster),
                        'total_amount': round(total, 2),
                        'record_ids': [r['record_id'] for r in cluster],
                        'expense_dates': [r['expense_date'] for r in cluster],
                        'amounts': [r['amount'] for r in cluster],
                        'department_id': cluster[0]['department_id'],
                        'department_name': cluster[0]['department_name']
                    })
            i = j
    
    conn.close()
    return violations

# === R4: 单笔超标 ===
def r4_analysis():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name, e.employee_level,
               er.department_id, d.department_name,
               er.expense_date, er.reimburse_date, er.expense_type, 
               er.amount, er.reason, er.status,
               er.city_tier, er.nights, er.days, er.participants, er.special_approval
        FROM expense_records er
        JOIN employees e ON er.employee_id = e.employee_id
        JOIN departments d ON er.department_id = d.department_id
        WHERE er.expense_date >= '2025-01-01' AND er.expense_date <= '2025-12-31'
          AND er.status = 'approved'
          AND er.special_approval = 0
    """)
    rows = cur.fetchall()
    
    violations = []
    
    for r in rows:
        rd = dict(r)
        etype = rd['expense_type']
        amount = rd['amount']
        city_tier = str(rd['city_tier']) if rd['city_tier'] else '1'
        employee_level = rd['employee_level']
        nights = rd['nights'] or 0
        days = rd['days'] or 0
        participants = rd['participants'] or 0
        
        violation = None
        
        # Travel lodging
        if etype == 'travel_lodging':
            lodging_standards = {
                ('P1', '1'): 800, ('P1', '2'): 650, ('P1', '3'): 500, ('P1', '4'): 400,
                ('P2', '1'): 700, ('P2', '2'): 550, ('P2', '3'): 420, ('P2', '4'): 350,
                ('P3', '1'): 600, ('P3', '2'): 480, ('P3', '3'): 380, ('P3', '4'): 300,
                ('P4', '1'): 500, ('P4', '2'): 420, ('P4', '3'): 350, ('P4', '4'): 280,
                ('P5', '1'): 450, ('P5', '2'): 380, ('P5', '3'): 300, ('P5', '4'): 250,
            }
            cap = lodging_standards.get((employee_level, city_tier), None)
            if cap and amount > cap:
                violation = {
                    **rd, 'limit': cap,
                    'limit_type': f'travel_lodging_L{employee_level}_T{city_tier}',
                    'excess': round(amount - cap, 2)
                }
        
        # Local transport
        elif etype == 'local_transport':
            transport_standards = {'1': 150, '2': 120, '3': 100, '4': 80}
            cap = transport_standards.get(city_tier, 150)
            if amount > cap:
                violation = {
                    **rd, 'limit': cap,
                    'limit_type': f'local_transport_T{city_tier}',
                    'excess': round(amount - cap, 2)
                }
        
        # Training fee
        elif etype == 'training_fee':
            if amount > 3500:
                violation = {
                    **rd, 'limit': 3500,
                    'limit_type': 'training_course_max',
                    'excess': round(amount - 3500, 2)
                }
        
        # Business entertainment
        elif etype == 'business_entertainment':
            if amount > 5000:
                violation = {
                    **rd, 'limit': 5000,
                    'limit_type': 'entertainment_single_max',
                    'excess': round(amount - 5000, 2)
                }
            elif participants > 0 and amount / participants > 300:
                violation = {
                    **rd, 'limit': 300,
                    'limit_type': 'entertainment_per_capita',
                    'excess': round(amount / participants - 300, 2),
                    'per_capita': round(amount / participants, 2)
                }
        
        # Office supplies
        elif etype == 'office_supplies':
            if amount > 600:
                violation = {
                    **rd, 'limit': 600,
                    'limit_type': 'office_per_record_cap',
                    'excess': round(amount - 600, 2)
                }
        
        # Communication
        elif etype == 'communication':
            if amount > 300:
                violation = {
                    **rd, 'limit': 300,
                    'limit_type': 'communication_per_record_cap',
                    'excess': round(amount - 300, 2)
                }
        
        if violation:
            violations.append(violation)
    
    conn.close()
    return violations

# === R4b: 月度累计超标 ===
def r4_monthly_caps():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name,
               er.department_id, d.department_name,
               er.expense_date, er.reimburse_date, er.expense_type, 
               er.amount, er.reason, er.status,
               er.special_approval, er.invoice_id
        FROM expense_records er
        JOIN employees e ON er.employee_id = e.employee_id
        JOIN departments d ON er.department_id = d.department_id
        WHERE er.expense_date >= '2025-01-01' AND er.expense_date <= '2025-12-31'
          AND er.status = 'approved'
          AND er.special_approval = 0
          AND er.expense_type IN ('office_supplies', 'communication')
        ORDER BY er.employee_id, er.expense_type, er.expense_date
    """)
    rows = cur.fetchall()
    
    monthly = defaultdict(list)
    for r in rows:
        rd = dict(r)
        month_key = rd['expense_date'][:7]
        group_key = (rd['employee_id'], rd['expense_type'], month_key)
        monthly[group_key].append(rd)
    
    violations = []
    caps = {'office_supplies': 600, 'communication': 300}
    
    for (emp_id, etype, month), recs in monthly.items():
        cap = caps[etype]
        total = sum(r['amount'] for r in recs)
        if total > cap:
            violations.append({
                'employee_id': emp_id,
                'employee_name': recs[0]['employee_name'],
                'expense_type': etype,
                'month': month,
                'cap': cap,
                'total_amount': round(total, 2),
                'excess': round(total - cap, 2),
                'record_count': len(recs),
                'record_ids': [r['record_id'] for r in recs],
                'amounts': [r['amount'] for r in recs],
                'invoice_ids': list(set(r['invoice_id'] for r in recs)),
                'department_id': recs[0]['department_id'],
                'department_name': recs[0]['department_name']
            })
    
    conn.close()
    return violations

# === R5: 预算不足 ===
def r5_analysis():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM departments")
    depts = {d['department_id']: dict(d) for d in cur.fetchall()}
    
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name,
               er.department_id, d.department_name,
               er.expense_date, er.reimburse_date, er.expense_type,
               er.amount, er.reason, er.status,
               er.special_approval, er.budget_year
        FROM expense_records er
        JOIN employees e ON er.employee_id = e.employee_id
        JOIN departments d ON er.department_id = d.department_id
        WHERE er.expense_date >= '2025-01-01' AND er.expense_date <= '2025-12-31'
          AND er.status = 'approved'
        ORDER BY er.department_id, er.reimburse_date, er.record_id
    """)
    rows = cur.fetchall()
    
    dept_records = defaultdict(list)
    for r in rows:
        dept_records[r['department_id']].append(dict(r))
    
    violations = []
    
    for dept_id, recs in dept_records.items():
        budget = depts[dept_id]['annual_budget']
        running_sum = 0.0
        exceeded_at = None
        
        for i, rec in enumerate(recs):
            running_sum += rec['amount']
            if exceeded_at is None and running_sum > budget:
                exceeded_at = i
            
        if exceeded_at is not None:
            # Recompute to attach running totals
            rs = 0.0
            for i, rec in enumerate(recs):
                rs += rec['amount']
                rec['running_total'] = round(rs, 2)
                if i >= exceeded_at and rec['special_approval'] == 0:
                    violations.append({
                        'record_id': rec['record_id'],
                        'record_no': rec['record_no'],
                        'employee_id': rec['employee_id'],
                        'employee_name': rec['employee_name'],
                        'department_id': rec['department_id'],
                        'department_name': rec['department_name'],
                        'expense_date': rec['expense_date'],
                        'reimburse_date': rec['reimburse_date'],
                        'expense_type': rec['expense_type'],
                        'amount': rec['amount'],
                        'reason': rec['reason'],
                        'running_total': rec['running_total'],
                        'budget': budget,
                        'exceeded_by': round(rec['running_total'] - budget, 2)
                    })
    
    conn.close()
    return violations, depts

# Run all
print("=== R1: 时限超期 ===")
r1 = r1_analysis()
print(f"R1 violations: {len(r1)}")

print("\n=== R2: 重复报销 ===")
r2 = r2_analysis()
print(f"R2 reused invoices: {len(r2)}")
for inv in r2:
    print(f"  {inv['invoice_no']}: {inv['record_ids']}")

print("\n=== R3: 拆分规避审批 ===")
r3 = r3_analysis()
print(f"R3 violations: {len(r3)}")

print("\n=== R4: 单笔超标 ===")
r4 = r4_analysis()
print(f"R4 per-record violations: {len(r4)}")
type_counts = defaultdict(int)
for v in r4:
    type_counts[v['expense_type']] += 1
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")

print("\n=== R4b: 月度累计超标 ===")
r4b = r4_monthly_caps()
print(f"R4b monthly cap violations: {len(r4b)}")

print("\n=== R5: 预算不足 ===")
r5, depts = r5_analysis()
print(f"R5 violations: {len(r5)}")

# Save
output = {
    'R1': {'violations': r1, 'count': len(r1)},
    'R2': {'reused_invoices': r2, 'count': len(r2)},
    'R3': {'split_violations': r3, 'count': len(r3)},
    'R4': {'per_record_violations': r4, 'count': len(r4)},
    'R4b': {'monthly_cap_violations': r4b, 'count': len(r4b)},
    'R5': {'budget_violations': r5, 'count': len(r5)}
}

with open('/workspace/work/subagents/data_analyst/detailed_analysis.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print(f"\nSaved to detailed_analysis.json")
