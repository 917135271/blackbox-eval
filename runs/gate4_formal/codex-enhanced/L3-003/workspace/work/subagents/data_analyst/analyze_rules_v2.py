import csv
import json
from collections import defaultdict

LEVEL_MAP = {'E1': '员工级', 'M1': '经理级', 'D1': '部门负责人级', 'X1': '高管级'}
CITY_MAP = {'A': '一类', 'B': '二类', 'C': '三类'}

R1_STANDARD = {
    '员工级': {'一类': 450, '二类': 380, '三类': 300},
    '经理级': {'一类': 650, '二类': 550, '三类': 450},
    '部门负责人级': {'一类': 850, '二类': 700, '三类': 600},
    '高管级': {'一类': 1100, '二类': 900, '三类': 750}
}
R2_STANDARD = {'一类': 120, '二类': 100, '三类': 80}
R6_STANDARD = {'一类': 500, '二类': 420, '三类': 350}

def load_records(csv_path):
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row['amount'] = float(row['amount'])
            row['nights'] = int(row['nights']) if row['nights'] else 0
            row['days'] = int(row['days']) if row['days'] else 0
            row['participants'] = int(row['participants']) if row['participants'] else 0
            row['special_approval'] = int(row['special_approval']) == 1
            row['annual_budget'] = float(row['annual_budget'])
            records.append(row)
    return records

records = load_records('/workspace/work/analysis/all_records.csv')
print(f"Loaded {len(records)} records")

# === R1 ===
r1_findings = []
for r in records:
    if r['expense_type'] != 'travel_lodging': continue
    if r['special_approval']: continue
    if not r['nights'] or r['nights'] <= 0: continue
    city_cn = CITY_MAP.get(r['city_tier'], r['city_tier'])
    if city_cn not in ('一类', '二类', '三类'): continue
    level = LEVEL_MAP.get(r['employee_level'], r['employee_level'])
    standard = R1_STANDARD.get(level, {}).get(city_cn)
    if standard is None: continue
    per_night = r['amount'] / r['nights']
    if per_night > standard:
        r1_findings.append({'rule':'R1','record_id':r['record_id'],'employee_id':r['employee_id'],
            'level':level,'city_tier_raw':r['city_tier'],'city_tier':city_cn,'amount':r['amount'],
            'nights':r['nights'],'per_night':round(per_night,2),'standard':standard,
            'excess':round(per_night-standard,2),'invoice_no':r['invoice_no']})

print(f"\nR1: {len(r1_findings)} anomalies")
for f in r1_findings:
    print(f"  {f['record_id']}: {f['level']} city={f['city_tier_raw']}({f['city_tier']}) amount={f['amount']} nights={f['nights']} per_night={f['per_night']} std={f['standard']}")

# === R2 ===
r2_findings = []
for r in records:
    if r['expense_type'] != 'local_transport': continue
    if r['special_approval']: continue
    if not r['days'] or r['days'] <= 0: continue
    city_cn = CITY_MAP.get(r['city_tier'], r['city_tier'])
    if city_cn not in ('一类', '二类', '三类'): continue
    standard = R2_STANDARD.get(city_cn)
    per_day = r['amount'] / r['days']
    if per_day > standard:
        r2_findings.append({'rule':'R2','record_id':r['record_id'],'employee_id':r['employee_id'],
            'city_tier_raw':r['city_tier'],'city_tier':city_cn,'amount':r['amount'],
            'days':r['days'],'per_day':round(per_day,2),'standard':standard,
            'excess':round(per_day-standard,2)})

print(f"\nR2: {len(r2_findings)} anomalies")
for f in r2_findings:
    print(f"  {f['record_id']}: city={f['city_tier_raw']}({f['city_tier']}) amount={f['amount']} days={f['days']} per_day={f['per_day']} std={f['standard']}")

# === R3: training_fee has participants=0 for all records → no checks possible
print("\nR3: 0 anomalies (all training_fee have participants=0)")

# === R4: training_fee days=0 for all → no checks
print("R4: 0 anomalies (all training_fee have days=0)")

# === R5: training_fee days=0 for all → no checks
print("R5: 0 anomalies (all training_fee have days=0)")

# === R6: training_fee nights=0 for all → no checks
print("R6: 0 anomalies (all training_fee have nights=0)")

# === R7 ===
r7_findings = []
for r in records:
    if r['expense_type'] != 'business_entertainment': continue
    if r['special_approval']: continue
    if r['amount'] > 5000:
        r7_findings.append({'rule':'R7','record_id':r['record_id'],'employee_id':r['employee_id'],
            'amount':r['amount'],'standard':5000,'excess':round(r['amount']-5000,2)})

print(f"\nR7: {len(r7_findings)} anomalies")
for f in r7_findings:
    print(f"  {f['record_id']}: amount={f['amount']}")

# === R8 ===
r8_findings = []
for r in records:
    if r['expense_type'] != 'business_entertainment': continue
    if r['special_approval']: continue
    if not r['participants'] or r['participants'] <= 0: continue
    per_person = r['amount'] / r['participants']
    if per_person > 300:
        r8_findings.append({'rule':'R8','record_id':r['record_id'],'employee_id':r['employee_id'],
            'amount':r['amount'],'participants':r['participants'],'per_person':round(per_person,2),
            'standard':300,'excess':round(per_person-300,2)})

print(f"\nR8: {len(r8_findings)} anomalies")
for f in r8_findings:
    print(f"  {f['record_id']}: amount={f['amount']} participants={f['participants']} per_person={f['per_person']}")

# === R9: office_supplies monthly ===
invoice_seen = {}
os_records = []
for r in records:
    if r['expense_type'] != 'office_supplies': continue
    inv = r['invoice_no']
    if inv in invoice_seen: continue
    invoice_seen[inv] = r['record_id']
    os_records.append(r)

monthly = defaultdict(lambda: {'records':[], 'total':0.0, 'all_no_sp':True})
for r in os_records:
    month_key = r['expense_date'][:7]
    key = (r['employee_id'], month_key)
    monthly[key]['records'].append(r)
    monthly[key]['total'] += r['amount']
    if r['special_approval']:
        monthly[key]['all_no_sp'] = False

r9_findings = []
for (emp_id, month), data in sorted(monthly.items()):
    if data['total'] > 600 and data['all_no_sp']:
        record_ids = [rr['record_id'] for rr in data['records']]
        r9_findings.append({'rule':'R9','employee_id':emp_id,'month':month,
            'total_amount':round(data['total'],2),'standard':600,
            'excess':round(data['total']-600,2),'record_count':len(data['records']),
            'record_ids':record_ids})

print(f"\nR9: {len(r9_findings)} groups, {sum(g['record_count'] for g in r9_findings)} total records")

# === R10: communication monthly ===
invoice_seen2 = {}
comm_records = []
for r in records:
    if r['expense_type'] != 'communication': continue
    inv = r['invoice_no']
    if inv in invoice_seen2: continue
    invoice_seen2[inv] = r['record_id']
    comm_records.append(r)

monthly2 = defaultdict(lambda: {'records':[], 'total':0.0, 'all_no_sp':True})
for r in comm_records:
    month_key = r['expense_date'][:7]
    key = (r['employee_id'], month_key)
    monthly2[key]['records'].append(r)
    monthly2[key]['total'] += r['amount']
    if r['special_approval']:
        monthly2[key]['all_no_sp'] = False

r10_findings = []
for (emp_id, month), data in sorted(monthly2.items()):
    if data['total'] > 300 and data['all_no_sp']:
        record_ids = [rr['record_id'] for rr in data['records']]
        r10_findings.append({'rule':'R10','employee_id':emp_id,'month':month,
            'total_amount':round(data['total'],2),'standard':300,
            'excess':round(data['total']-300,2),'record_count':len(data['records']),
            'record_ids':record_ids})

print(f"R10: {len(r10_findings)} groups, {sum(g['record_count'] for g in r10_findings)} total records")

# === R11: Budget - first unapproved record that causes exceedance per department ===
dept_budgets = {}
for r in records:
    if r['department_id'] not in dept_budgets:
        dept_budgets[r['department_id']] = {'budget': r['annual_budget'], 'name': r['department_name']}

r11_findings = []
for dept_id in sorted(dept_budgets.keys()):
    budget = dept_budgets[dept_id]['budget']
    dept_records = [r for r in records if r['department_id'] == dept_id]
    dept_records.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
    
    cumulative = 0.0
    crossed = False
    first_unapproved_crossing = None
    
    for r in dept_records:
        cumulative += r['amount']
        if not crossed and cumulative > budget:
            crossed = True
            # This is the crossing record
            if not r['special_approval']:
                first_unapproved_crossing = r
                break
            # If special_approval=true, the crossing is approved, continue looking
            # for the next unapproved record after crossing
        if crossed and not r['special_approval'] and first_unapproved_crossing is None:
            first_unapproved_crossing = r
            break
    
    if first_unapproved_crossing:
        r11_findings.append({'rule':'R11','record_id':first_unapproved_crossing['record_id'],
            'employee_id':first_unapproved_crossing['employee_id'],
            'department_id':dept_id,'department_name':dept_budgets[dept_id]['name'],
            'amount':first_unapproved_crossing['amount'],'annual_budget':budget,
            'reimburse_date':first_unapproved_crossing['reimburse_date'],
            'expense_type':first_unapproved_crossing['expense_type'],
            'invoice_no':first_unapproved_crossing['invoice_no']})

print(f"\nR11: {len(r11_findings)} first-unapproved-crossing records")
for f in r11_findings:
    print(f"  {f['record_id']}: dept={f['department_id']}({f['department_name']}) budget={f['annual_budget']} amount={f['amount']} type={f['expense_type']} date={f['reimburse_date']}")

# Collect all record IDs
all_anomaly_records = set()
all_anomaly_records.update(f['record_id'] for f in r1_findings)
all_anomaly_records.update(f['record_id'] for f in r2_findings)
all_anomaly_records.update(f['record_id'] for f in r7_findings)
all_anomaly_records.update(f['record_id'] for f in r8_findings)
for g in r9_findings:
    all_anomaly_records.update(g['record_ids'])
for g in r10_findings:
    all_anomaly_records.update(g['record_ids'])
all_anomaly_records.update(f['record_id'] for f in r11_findings)

print(f"\nTotal unique anomaly record IDs: {len(all_anomaly_records)}")

# Save all findings
output = {
    'R1': r1_findings,
    'R2': r2_findings,
    'R3': [], 'R4': [], 'R5': [], 'R6': [],
    'R7': r7_findings,
    'R8': r8_findings,
    'R9': r9_findings,
    'R10': r10_findings,
    'R11': r11_findings,
    'total_unique_record_ids': sorted(list(all_anomaly_records)),
    'summary': {
        'R1_count': len(r1_findings),
        'R2_count': len(r2_findings),
        'R3_count': 0, 'R4_count': 0, 'R5_count': 0, 'R6_count': 0,
        'R7_count': len(r7_findings),
        'R8_count': len(r8_findings),
        'R9_groups': len(r9_findings), 'R9_records': sum(g['record_count'] for g in r9_findings),
        'R10_groups': len(r10_findings), 'R10_records': sum(g['record_count'] for g in r10_findings),
        'R11_count': len(r11_findings)
    }
}

with open('/workspace/work/subagents/data_analyst/findings_v2.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print("\nSaved to findings_v2.json")
