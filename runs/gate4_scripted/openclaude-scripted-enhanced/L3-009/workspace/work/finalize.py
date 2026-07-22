import sqlite3
import json
from datetime import datetime
from collections import defaultdict

DB_PATH = "/benchmark/data/expense.db"
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# Load all records with detail
rows = conn.execute("""
    SELECT r.*, e.employee_name, e.employee_level, e.position_role, 
           d.department_name, d.annual_budget,
           i.invoice_no, i.vendor_name, i.invoice_date, i.amount AS invoice_amount,
           i.invoice_id
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    JOIN departments d ON d.department_id = r.department_id
    JOIN invoices i ON i.invoice_id = r.invoice_id
    ORDER BY r.record_id
""").fetchall()
records = [dict(r) for r in rows]

# Position role mapping for travel standards
def get_travel_level(pos_role, emp_level):
    if pos_role in ('分管副总', '总经理办公会'):
        return '高管'
    elif pos_role in ('部门总经理',):
        return '部门负责人'
    elif pos_role in ('部门经理',):
        return '经理'
    else:
        return '员工'

# Standards
travel_std = {
    '员工': {'一类': 450, '二类': 380, '三类': 300},
    '经理': {'一类': 650, '二类': 550, '三类': 450},
    '部门负责人': {'一类': 850, '二类': 700, '三类': 600},
    '高管': {'一类': 1100, '二类': 900, '三类': 750},
}
city_map = {'A': '一类', 'B': '二类', 'C': '三类'}
transport_std = {'一类': 120, '二类': 100, '三类': 80}

# ===================== 1. DUPLICATE =====================
dup_invoices_raw = conn.execute("""
    SELECT i.invoice_id, i.invoice_no, i.vendor_name, i.invoice_date, i.amount, i.expense_type,
           COUNT(r.record_id) AS usage_count,
           GROUP_CONCAT(r.record_id) AS record_ids
    FROM invoices i
    JOIN expense_records r ON r.invoice_id = i.invoice_id
    GROUP BY i.invoice_id
    HAVING COUNT(r.record_id) >= 2
    ORDER BY i.invoice_no
""").fetchall()

dup_groups = []
dup_all_records = []
for idx, row in enumerate(dup_invoices_raw, 1):
    d = dict(row)
    rec_ids = sorted([x for x in d['record_ids'].split(',') if x])
    dup_groups.append({
        'anomaly_id': f'DUP-{idx:03d}',
        'invoice_no': d['invoice_no'],
        'usage_count': d['usage_count'],
        'record_ids': rec_ids
    })
    dup_all_records.extend(rec_ids)

print(f"Duplicate: {len(dup_groups)} groups, {len(dup_all_records)} records")

# ===================== 2. SPLIT =====================
emp_exp = defaultdict(list)
for r in records:
    key = (r['employee_id'], r['expense_type'])
    emp_exp[key].append(r)

split_groups = []
for (emp_id, exp_type), recs in emp_exp.items():
    if len(recs) < 2:
        continue
    recs_sorted = sorted(recs, key=lambda r: r['expense_date'])
    i = 0
    while i < len(recs_sorted):
        window = [recs_sorted[i]]
        j = i + 1
        while j < len(recs_sorted):
            d1 = datetime.strptime(recs_sorted[i]['expense_date'], '%Y-%m-%d')
            d2 = datetime.strptime(recs_sorted[j]['expense_date'], '%Y-%m-%d')
            if (d2 - d1).days <= 7:
                window.append(recs_sorted[j])
                j += 1
            else:
                break
        if len(window) >= 2:
            total = sum(r['amount'] for r in window)
            if total >= 3000:
                split_groups.append({
                    'employee_id': emp_id,
                    'employee_name': window[0]['employee_name'],
                    'expense_type': exp_type,
                    'window_start': window[0]['expense_date'],
                    'window_end': window[-1]['expense_date'],
                    'record_count': len(window),
                    'total_amount': round(total, 2),
                    'record_ids': sorted([r['record_id'] for r in window])
                })
        i = j

# Assign IDs
for idx, sg in enumerate(split_groups, 1):
    sg['anomaly_id'] = f'SPL-{idx:03d}'

split_all_records = []
for sg in split_groups:
    split_all_records.extend(sg['record_ids'])

print(f"Split: {len(split_groups)} groups, {len(split_all_records)} records (unique: {len(set(split_all_records))})")

# ===================== 3. OVER-STANDARD =====================
os_findings = []

for r in records:
    if r['special_approval'] == 1:
        continue
    
    exp_type = r['expense_type']
    amount = r['amount']
    
    if exp_type == 'travel_lodging':
        city_tier = r.get('city_tier')
        nights = r.get('nights')
        if city_tier and nights and nights > 0:
            level = get_travel_level(r['position_role'], r['employee_level'])
            tier = city_map.get(city_tier, '二类')
            per_night_std = travel_std.get(level, {}).get(tier, 380)
            per_night = amount / nights
            if per_night > per_night_std:
                os_findings.append({
                    'record_id': r['record_id'],
                    'employee_name': r['employee_name'],
                    'expense_type': exp_type,
                    'amount': amount,
                    'standard': per_night_std,
                    'actual': round(per_night, 2),
                    'unit': '元/晚',
                    'detail': f"{nights}晚, {city_tier}({tier}), {level}标准{per_night_std}元/晚, 实际{per_night:.2f}元/晚"
                })
    
    elif exp_type == 'training_fee':
        if amount > 3500:
            os_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': 3500,
                'actual': amount,
                'unit': '元/人次',
                'detail': f"培训费标准每人每期不超过3500元, 实际{amount}元"
            })
    
    elif exp_type == 'business_entertainment':
        participants = r.get('participants')
        if amount > 5000:
            os_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': 5000,
                'actual': amount,
                'unit': '元/次',
                'detail': f"招待费单次不超过5000元, 实际{amount}元"
            })
        elif participants and participants > 0 and (amount / participants) > 300:
            os_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': 300,
                'actual': round(amount / participants, 2),
                'unit': '元/人',
                'detail': f"{participants}人参会, 人均标准300元, 实际{amount/participants:.2f}元/人"
            })
    
    elif exp_type == 'office_supplies':
        if amount > 600:
            os_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': 600,
                'actual': amount,
                'unit': '元/月',
                'detail': f"办公用品每人每月不超过600元, 单笔实际{amount}元"
            })
    
    elif exp_type == 'communication':
        if amount > 300:
            os_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': 300,
                'actual': amount,
                'unit': '元/月',
                'detail': f"通讯费每人每月不超过300元, 单笔实际{amount}元"
            })
    
    elif exp_type == 'local_transport':
        city_tier = r.get('city_tier')
        days = r.get('days')
        if city_tier and days and days > 0:
            tier = city_map.get(city_tier, '二类')
            daily_std = transport_std.get(tier, 100)
            per_day = amount / days
            if per_day > daily_std:
                os_findings.append({
                    'record_id': r['record_id'],
                    'employee_name': r['employee_name'],
                    'expense_type': exp_type,
                    'amount': amount,
                    'standard': daily_std,
                    'actual': round(per_day, 2),
                    'unit': '元/天',
                    'detail': f"{days}天, {city_tier}({tier}), 每日标准{daily_std}元, 实际{per_day:.2f}元/天"
                })

for idx, osf in enumerate(os_findings, 1):
    osf['anomaly_id'] = f'STD-{idx:03d}'

os_all_records = [f['record_id'] for f in os_findings]
print(f"Over-standard: {len(os_findings)} findings, {len(os_all_records)} records")

# ===================== 4. OVER-BUDGET =====================
dept_budgets = {}
for row in conn.execute("SELECT department_id, annual_budget, department_name FROM departments").fetchall():
    dept_budgets[row['department_id']] = {
        'budget': float(row['annual_budget']),
        'name': row['department_name']
    }

ob_findings = []
for dept_id, info in dept_budgets.items():
    dept_recs = [r for r in records if r['department_id'] == dept_id]
    dept_recs_sorted = sorted(dept_recs, key=lambda r: (r['reimburse_date'], r['record_id']))
    
    cum = 0.0
    exceeded = False
    key_record = None
    over_records = []
    
    for r in dept_recs_sorted:
        cum += r['amount']
        if not exceeded and cum > info['budget']:
            exceeded = True
            if r['special_approval'] == 0:
                key_record = r['record_id']
        if cum > info['budget'] and r['special_approval'] == 0:
            over_records.append(r['record_id'])
    
    if exceeded and key_record:
        ob_findings.append({
            'department_id': dept_id,
            'department_name': info['name'],
            'annual_budget': info['budget'],
            'total_used': round(cum, 2),
            'usage_rate': round(cum / info['budget'], 4),
            'key_record_id': key_record,
            'record_ids': over_records
        })

for idx, obf in enumerate(ob_findings, 1):
    obf['anomaly_id'] = f'BUD-{idx:03d}'

ob_all_records = []
for obf in ob_findings:
    ob_all_records.extend(obf['record_ids'])
# deduplicate
ob_all_records = list(set(ob_all_records))

print(f"Over-budget: {len(ob_findings)} departments, {len(ob_all_records)} records")

# ===================== 5. OVERDUE =====================
overdue_findings = []
for r in records:
    exp_date = datetime.strptime(r['expense_date'], '%Y-%m-%d')
    reim_date = datetime.strptime(r['reimburse_date'], '%Y-%m-%d')
    delay = (reim_date - exp_date).days
    if delay > 60:
        overdue_findings.append({
            'record_id': r['record_id'],
            'employee_name': r['employee_name'],
            'expense_type': r['expense_type'],
            'expense_date': r['expense_date'],
            'reimburse_date': r['reimburse_date'],
            'delay_days': delay,
            'amount': r['amount']
        })

for idx, od in enumerate(overdue_findings, 1):
    od['anomaly_id'] = f'OVD-{idx:03d}'

overdue_all_records = [f['record_id'] for f in overdue_findings]
print(f"Overdue: {len(overdue_findings)} records")

# ===================== COMBINE ALL RECORD_IDS =====================
all_anomaly_ids = []
all_record_ids = set()

for dg in dup_groups:
    all_anomaly_ids.append(dg['anomaly_id'])
    all_record_ids.update(dg['record_ids'])

for sg in split_groups:
    all_anomaly_ids.append(sg['anomaly_id'])
    all_record_ids.update(sg['record_ids'])

for osf in os_findings:
    all_anomaly_ids.append(osf['anomaly_id'])
    all_record_ids.add(osf['record_id'])

for obf in ob_findings:
    all_anomaly_ids.append(obf['anomaly_id'])
    all_record_ids.update(obf['record_ids'])

for od in overdue_findings:
    all_anomaly_ids.append(od['anomaly_id'])
    all_record_ids.add(od['record_id'])

all_record_ids = sorted(all_record_ids)

print(f"\n=== FINAL SUMMARY ===")
print(f"Total anomaly IDs: {len(all_anomaly_ids)}")
print(f"Total unique record IDs: {len(all_record_ids)}")
print(f" - DUP: {len(dup_groups)} findings, {len(set(d['record_ids'][0] for d in dup_groups) | set(d['record_ids'][1] for d in dup_groups))} records")
print(f" - SPL: {len(split_groups)} findings")
print(f" - STD: {len(os_findings)} findings")
print(f" - BUD: {len(ob_findings)} findings")
print(f" - OVD: {len(overdue_findings)} findings")

# Save detailed results
result = {
    'dup_groups': dup_groups,
    'split_groups': split_groups,
    'os_findings': os_findings,
    'ob_findings': ob_findings,
    'overdue_findings': overdue_findings,
    'all_anomaly_ids': all_anomaly_ids,
    'all_record_ids': all_record_ids
}

with open('/workspace/work/finalized_analysis.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

conn.close()
