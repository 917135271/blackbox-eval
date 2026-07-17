import sqlite3
import json
from datetime import date
from collections import defaultdict

DB = "/benchmark/data/expense.db"

def get_db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

# Policy standards
TRAVEL_LODGING = {
    # (employee_level, city_tier): cap per night
    ('E1', 'A'): 450, ('E1', 'B'): 380, ('E1', 'C'): 300,
    ('M1', 'A'): 650, ('M1', 'B'): 550, ('M1', 'C'): 450,
    ('D1', 'A'): 850, ('D1', 'B'): 700, ('D1', 'C'): 600,
    ('X1', 'A'): 1100, ('X1', 'B'): 900, ('X1', 'C'): 750,
}
LOCAL_TRANSPORT = {'A': 120, 'B': 100, 'C': 80}
TRAINING_LODGING = {'A': 500, 'B': 420, 'C': 350}
TRAINING_COURSE_MAX = 3500
ENTERTAINMENT_SINGLE = 5000
ENTERTAINMENT_PER_CAPITA = 300
OFFICE_MONTHLY = 600
COMM_MONTHLY = 300

# ========== R1 ==========
def r1_analysis():
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
                violations.append({**dict(r), 'delay_days': (reim_date - exp_date).days, 'rule': 'R1_year_end'})
        else:
            diff = (reim_date - exp_date).days
            if diff > 60:
                violations.append({**dict(r), 'delay_days': diff, 'rule': 'R1_standard'})
    conn.close()
    return violations

# ========== R2 ==========
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
        result.append({
            'invoice_no': inv['invoice_no'], 'invoice_id': inv['invoice_id'],
            'vendor_name': inv['vendor_name'], 'invoice_date': inv['invoice_date'],
            'amount': inv['amount'], 'expense_type': inv['expense_type'],
            'usage_count': inv['usage_count'],
            'record_ids': inv['record_ids'].split(',')
        })
    conn.close()
    return result

# ========== R3 ==========
def r3_analysis():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name,
               er.department_id, d.department_name,
               er.expense_date, er.expense_type, er.amount
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
        groups[(r['employee_id'], r['expense_type'])].append(dict(r))
    
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
                prev_d = date.fromisoformat(cluster[-1]['expense_date'])
                curr_d = date.fromisoformat(recs[j]['expense_date'])
                if (curr_d - prev_d).days <= 7:
                    cluster.append(recs[j]); j += 1
                else:
                    break
            if len(cluster) >= 2:
                total = sum(r['amount'] for r in cluster)
                if total >= 10000:
                    violations.append({
                        'employee_id': key[0], 'employee_name': cluster[0]['employee_name'],
                        'expense_type': key[1], 'cluster_size': len(cluster),
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

# ========== R4 ==========
def r4_analysis():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name, e.employee_level,
               er.department_id, d.department_name,
               er.expense_date, er.expense_type, er.amount, er.reason,
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
        amt = rd['amount']
        ct = rd['city_tier'] or 'A'
        lvl = rd['employee_level']
        part = rd['participants'] or 0
        
        v = None
        if etype == 'travel_lodging':
            cap = TRAVEL_LODGING.get((lvl, ct))
            if cap and amt > cap:
                v = {**rd, 'limit': cap, 'limit_type': f'travel_lodging_{lvl}_{ct}', 'excess': round(amt - cap, 2)}
        elif etype == 'local_transport':
            cap = LOCAL_TRANSPORT.get(ct, 120)
            if amt > cap:
                v = {**rd, 'limit': cap, 'limit_type': f'local_transport_{ct}', 'excess': round(amt - cap, 2)}
        elif etype == 'training_fee':
            if amt > TRAINING_COURSE_MAX:
                v = {**rd, 'limit': TRAINING_COURSE_MAX, 'limit_type': 'training_course_max', 'excess': round(amt - TRAINING_COURSE_MAX, 2)}
        elif etype == 'business_entertainment':
            if amt > ENTERTAINMENT_SINGLE:
                v = {**rd, 'limit': ENTERTAINMENT_SINGLE, 'limit_type': 'entertainment_single', 'excess': round(amt - ENTERTAINMENT_SINGLE, 2)}
            elif part > 0 and amt/part > ENTERTAINMENT_PER_CAPITA:
                v = {**rd, 'limit': ENTERTAINMENT_PER_CAPITA, 'limit_type': 'entertainment_per_capita',
                     'per_capita': round(amt/part, 2), 'excess': round(amt/part - ENTERTAINMENT_PER_CAPITA, 2)}
        elif etype == 'office_supplies':
            if amt > OFFICE_MONTHLY:
                v = {**rd, 'limit': OFFICE_MONTHLY, 'limit_type': 'office_per_record_over_monthly', 'excess': round(amt - OFFICE_MONTHLY, 2)}
        elif etype == 'communication':
            if amt > COMM_MONTHLY:
                v = {**rd, 'limit': COMM_MONTHLY, 'limit_type': 'comm_per_record_over_monthly', 'excess': round(amt - COMM_MONTHLY, 2)}
        if v:
            violations.append(v)
    conn.close()
    return violations

# ========== R4b: Monthly Caps ==========
def r4_monthly_caps():
    """Reconcile duplicate invoice identity, then group by employee+type+month"""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT er.record_id, er.record_no, er.employee_id, e.employee_name,
               er.department_id, d.department_name,
               er.expense_date, er.expense_type, er.amount,
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
    
    # Group by employee+type+month
    monthly = defaultdict(list)
    for r in rows:
        rd = dict(r)
        month_key = rd['expense_date'][:7]
        monthly[(rd['employee_id'], rd['expense_type'], month_key)].append(rd)
    
    violations = []
    caps = {'office_supplies': OFFICE_MONTHLY, 'communication': COMM_MONTHLY}
    
    for (emp_id, etype, month), recs in monthly.items():
        cap = caps[etype]
        
        # Reconcile duplicate invoice identity: deduplicate by invoice_id
        seen_invs = set()
        deduped_recs = []
        for r in recs:
            if r['invoice_id'] not in seen_invs:
                seen_invs.add(r['invoice_id'])
                deduped_recs.append(r)
            # Duplicate invoices are skipped (same invoice used twice in same month)
        
        total = sum(r['amount'] for r in deduped_recs)
        if total > cap:
            violations.append({
                'employee_id': emp_id,
                'employee_name': deduped_recs[0]['employee_name'],
                'expense_type': etype, 'month': month, 'cap': cap,
                'total_amount': round(total, 2),
                'excess': round(total - cap, 2),
                'record_count': len(deduped_recs),
                'record_ids': [r['record_id'] for r in deduped_recs],
                'amounts': [r['amount'] for r in deduped_recs],
                'department_id': deduped_recs[0]['department_id'],
                'department_name': deduped_recs[0]['department_name']
            })
    conn.close()
    return violations

# ========== R5 ==========
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
               er.amount, er.reason, er.special_approval
        FROM expense_records er
        JOIN employees e ON er.employee_id = e.employee_id
        JOIN departments d ON er.department_id = d.department_id
        WHERE er.expense_date >= '2025-01-01' AND er.expense_date <= '2025-12-31'
          AND er.status = 'approved'
        ORDER BY er.department_id, er.reimburse_date, er.record_id
    """)
    rows = cur.fetchall()
    
    dept_recs = defaultdict(list)
    for r in rows:
        dept_recs[r['department_id']].append(dict(r))
    
    violations = []
    
    for dept_id, recs in dept_recs.items():
        budget = depts[dept_id]['annual_budget']
        rs = 0.0
        exceeded_at = None
        
        for i, rec in enumerate(recs):
            rs += rec['amount']
            if exceeded_at is None and rs > budget:
                exceeded_at = i
        
        if exceeded_at is not None:
            rs2 = 0.0
            for i, rec in enumerate(recs):
                rs2 += rec['amount']
                rec['running_total'] = round(rs2, 2)
                if i >= exceeded_at and rec['special_approval'] == 0:
                    violations.append({
                        'record_id': rec['record_id'], 'record_no': rec['record_no'],
                        'employee_id': rec['employee_id'], 'employee_name': rec['employee_name'],
                        'department_id': rec['department_id'], 'department_name': rec['department_name'],
                        'expense_date': rec['expense_date'], 'reimburse_date': rec['reimburse_date'],
                        'expense_type': rec['expense_type'], 'amount': rec['amount'],
                        'reason': rec['reason'],
                        'running_total': rec['running_total'],
                        'budget': budget,
                        'exceeded_by': round(rec['running_total'] - budget, 2)
                    })
    conn.close()
    return violations, depts

# Run
print("=== R1 ===")
r1 = r1_analysis()
print(f"Count: {len(r1)}")
for v in r1:
    print(f"  {v['record_id']} {v['employee_name']} {v['expense_date']}->{v['reimburse_date']} ({v['delay_days']}d) {v['rule']}")

print("\n=== R2 ===")
r2 = r2_analysis()
print(f"Count: {len(r2)}")
for inv in r2:
    print(f"  {inv['invoice_no']} x{inv['usage_count']}: {inv['record_ids']}")

print("\n=== R3 ===")
r3 = r3_analysis()
print(f"Count: {len(r3)}")
for v in r3:
    print(f"  {v['employee_name']}({v['employee_id']}) {v['expense_type']}: {v['total_amount']} in {v['cluster_size']} recs")
    for rid, dt, am in zip(v['record_ids'], v['expense_dates'], v['amounts']):
        print(f"    {rid} {dt} {am}")

print("\n=== R4 ===")
r4 = r4_analysis()
print(f"Count: {len(r4)}")
tc = defaultdict(int)
for v in r4:
    tc[v['expense_type']] += 1
for t, c in sorted(tc.items()):
    print(f"  {t}: {c}")

print("\n=== R4b ===")
r4b = r4_monthly_caps()
print(f"Count: {len(r4b)}")
for v in r4b[:10]:
    print(f"  {v['employee_name']} {v['expense_type']} {v['month']}: {v['total_amount']} > {v['cap']}")

print("\n=== R5 ===")
r5, depts = r5_analysis()
print(f"Count: {len(r5)}")
dc = defaultdict(int)
for v in r5:
    dc[v['department_name']] += 1
for d, c in sorted(dc.items(), key=lambda x: -x[1]):
    print(f"  {d}: {c}")

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

print(f"\nSaved.")
