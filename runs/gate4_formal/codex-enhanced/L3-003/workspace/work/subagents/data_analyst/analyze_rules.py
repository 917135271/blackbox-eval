import csv
import json
from collections import defaultdict
from datetime import datetime, date

# Level mapping
LEVEL_MAP = {
    'E1': '员工级',
    'M1': '经理级',
    'D1': '部门负责人级',
    'X1': '高管级'
}

# R1 standard table: level -> city_tier -> per_night_rate
R1_STANDARD = {
    '员工级': {'一类': 450, '二类': 380, '三类': 300},
    '经理级': {'一类': 650, '二类': 550, '三类': 450},
    '部门负责人级': {'一类': 850, '二类': 700, '三类': 600},
    '高管级': {'一类': 1100, '二类': 900, '三类': 750}
}

# R2 standard: city_tier -> per_day_rate
R2_STANDARD = {'一类': 120, '二类': 100, '三类': 80}

# R6 standard: city_tier -> per_night_rate
R6_STANDARD = {'一类': 500, '二类': 420, '三类': 350}

def load_records(csv_path):
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['amount'] = float(row['amount'])
            row['nights'] = int(row['nights']) if row['nights'] else 0
            row['days'] = int(row['days']) if row['days'] else 0
            row['participants'] = int(row['participants']) if row['participants'] else 0
            row['special_approval'] = int(row['special_approval']) == 1
            row['annual_budget'] = float(row['annual_budget'])
            records.append(row)
    return records

def check_R1(records):
    """R1: 差旅住宿超标准 - amount/nights > standard by level×city_tier, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'travel_lodging':
            continue
        if r['special_approval']:
            continue
        if not r['nights'] or r['nights'] <= 0:
            continue
        level = LEVEL_MAP.get(r['employee_level'], r['employee_level'])
        city = r['city_tier']
        if city not in ('一类', '二类', '三类'):
            continue
        standard = R1_STANDARD.get(level, {}).get(city)
        if standard is None:
            continue
        per_night = r['amount'] / r['nights']
        if per_night > standard:
            findings.append({
                'rule': 'R1',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'level': level,
                'city_tier': city,
                'amount': r['amount'],
                'nights': r['nights'],
                'per_night': round(per_night, 2),
                'standard': standard,
                'excess': round(per_night - standard, 2),
                'special_approval': False,
                'invoice_no': r['invoice_no']
            })
    return findings

def check_R2(records):
    """R2: 市内交通超标准 - amount/days > city_tier_rate, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'local_transport':
            continue
        if r['special_approval']:
            continue
        if not r['days'] or r['days'] <= 0:
            continue
        city = r['city_tier']
        if city not in ('一类', '二类', '三类'):
            continue
        standard = R2_STANDARD.get(city)
        if standard is None:
            continue
        per_day = r['amount'] / r['days']
        if per_day > standard:
            findings.append({
                'rule': 'R2',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'city_tier': city,
                'amount': r['amount'],
                'days': r['days'],
                'per_day': round(per_day, 2),
                'standard': standard,
                'excess': round(per_day - standard, 2),
                'special_approval': False
            })
    return findings

def check_R3(records):
    """R3: 培训课程费超标准 - amount/participants > 3500, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'training_fee':
            continue
        if r['special_approval']:
            continue
        if not r['participants'] or r['participants'] <= 0:
            continue
        per_person = r['amount'] / r['participants']
        if per_person > 3500:
            findings.append({
                'rule': 'R3',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'amount': r['amount'],
                'participants': r['participants'],
                'per_person': round(per_person, 2),
                'standard': 3500,
                'excess': round(per_person - 3500, 2),
                'special_approval': False
            })
    return findings

def check_R4(records):
    """R4: 内部培训综合超标准 - internal training, amount/days > 800, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'training_fee':
            continue
        if r['special_approval']:
            continue
        if not r['days'] or r['days'] <= 0:
            continue
        # R4 applies to internal training; we identify by looking at the reason/vendor
        # If we need explicit training category, look at reason or vendor
        # For now, check all training_fee with days: they must be internal or external
        # The rule says "内部培训" - we'll need to classify
        per_day = r['amount'] / r['days']
        if per_day > 800:
            # We flag all training_fee with days > 800 as potential R4 candidates
            # Later we'll classify as internal/external
            findings.append({
                'rule': 'R4_candidate',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'amount': r['amount'],
                'days': r['days'],
                'per_day': round(per_day, 2),
                'standard': 800,
                'excess': round(per_day - 800, 2),
                'special_approval': False,
                'invoice_no': r['invoice_no'],
                'vendor_name': r['vendor_name'],
                'reason': r.get('reason', '')
            })
    return findings

def check_R5(records):
    """R5: 外部培训综合超标准 - external training, amount/days > 1200, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'training_fee':
            continue
        if r['special_approval']:
            continue
        if not r['days'] or r['days'] <= 0:
            continue
        per_day = r['amount'] / r['days']
        if per_day > 1200:
            findings.append({
                'rule': 'R5_candidate',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'amount': r['amount'],
                'days': r['days'],
                'per_day': round(per_day, 2),
                'standard': 1200,
                'excess': round(per_day - 1200, 2),
                'special_approval': False,
                'invoice_no': r['invoice_no'],
                'vendor_name': r['vendor_name'],
                'reason': r.get('reason', '')
            })
    return findings

def check_R6(records):
    """R6: 培训住宿超标准 - amount/nights > city_tier_rate, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'training_fee':
            continue
        if r['special_approval']:
            continue
        if not r['nights'] or r['nights'] <= 0:
            continue
        city = r['city_tier']
        if city not in ('一类', '二类', '三类'):
            continue
        standard = R6_STANDARD.get(city)
        if standard is None:
            continue
        per_night = r['amount'] / r['nights']
        if per_night > standard:
            findings.append({
                'rule': 'R6',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'city_tier': city,
                'amount': r['amount'],
                'nights': r['nights'],
                'per_night': round(per_night, 2),
                'standard': standard,
                'excess': round(per_night - standard, 2),
                'special_approval': False
            })
    return findings

def check_R7(records):
    """R7: 招待费单次超标准 - amount > 5000, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'business_entertainment':
            continue
        if r['special_approval']:
            continue
        if r['amount'] > 5000:
            findings.append({
                'rule': 'R7',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'amount': r['amount'],
                'standard': 5000,
                'excess': round(r['amount'] - 5000, 2),
                'special_approval': False
            })
    return findings

def check_R8(records):
    """R8: 招待费人均超标准 - amount/participants > 300, special_approval=false"""
    findings = []
    for r in records:
        if r['expense_type'] != 'business_entertainment':
            continue
        if r['special_approval']:
            continue
        if not r['participants'] or r['participants'] <= 0:
            continue
        per_person = r['amount'] / r['participants']
        if per_person > 300:
            findings.append({
                'rule': 'R8',
                'record_id': r['record_id'],
                'employee_id': r['employee_id'],
                'amount': r['amount'],
                'participants': r['participants'],
                'per_person': round(per_person, 2),
                'standard': 300,
                'excess': round(per_person - 300, 2),
                'special_approval': False
            })
    return findings

def check_R9(records):
    """
    R9: 办公用品月度超标准 - GROUP BY employee_id, month: sum(amount) > 600
    All records in the violating group must have special_approval=false
    First reconcile duplicate invoice identity
    """
    # Step 1: Collect office_supplies records, deduplicate by invoice
    invoice_seen = {}
    os_records = []
    for r in records:
        if r['expense_type'] != 'office_supplies':
            continue
        inv = r['invoice_no']
        if inv in invoice_seen:
            # Same invoice used again - reconcile (skip duplicate invoice reimbursement)
            continue
        invoice_seen[inv] = r['record_id']
        os_records.append(r)
    
    # Step 2: Group by employee_id + month
    monthly = defaultdict(lambda: {'records': [], 'total': 0.0, 'all_no_sp': True})
    for r in os_records:
        month_key = r['expense_date'][:7]  # YYYY-MM
        key = (r['employee_id'], month_key)
        monthly[key]['records'].append(r)
        monthly[key]['total'] += r['amount']
        if r['special_approval']:
            monthly[key]['all_no_sp'] = False
    
    # Step 3: Identify violations
    findings = []
    for (emp_id, month), data in sorted(monthly.items()):
        if data['total'] > 600 and data['all_no_sp']:
            record_ids = [r['record_id'] for r in data['records']]
            findings.append({
                'rule': 'R9',
                'employee_id': emp_id,
                'month': month,
                'total_amount': round(data['total'], 2),
                'standard': 600,
                'excess': round(data['total'] - 600, 2),
                'record_count': len(data['records']),
                'record_ids': record_ids,
                'all_no_special_approval': True
            })
    return findings

def check_R10(records):
    """
    R10: 通讯费月度超标准 - GROUP BY employee_id, month: sum(amount) > 300
    All records in the violating group must have special_approval=false
    First reconcile duplicate invoice identity
    """
    invoice_seen = {}
    comm_records = []
    for r in records:
        if r['expense_type'] != 'communication':
            continue
        inv = r['invoice_no']
        if inv in invoice_seen:
            continue
        invoice_seen[inv] = r['record_id']
        comm_records.append(r)
    
    monthly = defaultdict(lambda: {'records': [], 'total': 0.0, 'all_no_sp': True})
    for r in comm_records:
        month_key = r['expense_date'][:7]
        key = (r['employee_id'], month_key)
        monthly[key]['records'].append(r)
        monthly[key]['total'] += r['amount']
        if r['special_approval']:
            monthly[key]['all_no_sp'] = False
    
    findings = []
    for (emp_id, month), data in sorted(monthly.items()):
        if data['total'] > 300 and data['all_no_sp']:
            record_ids = [r['record_id'] for r in data['records']]
            findings.append({
                'rule': 'R10',
                'employee_id': emp_id,
                'month': month,
                'total_amount': round(data['total'], 2),
                'standard': 300,
                'excess': round(data['total'] - 300, 2),
                'record_count': len(data['records']),
                'record_ids': record_ids,
                'all_no_special_approval': True
            })
    return findings

def check_R11(records):
    """
    R11: 部门预算超支 - cumulative per department, ordered by reimburse_date
    First record that pushes balance over budget without special_approval is anomalous.
    Pre-crossing and valid special_approval records are context, not anomalies.
    """
    # Get all departments with their budgets
    dept_budgets = {}
    for r in records:
        dept_budgets[r['department_id']] = {
            'budget': r['annual_budget'],
            'name': r['department_name']
        }
    
    findings = []
    for dept_id, dept_info in dept_budgets.items():
        budget = dept_info['budget']
        dept_records = [r for r in records if r['department_id'] == dept_id]
        # Sort by reimburse_date then record_id for determinism
        dept_records.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
        
        cumulative = 0.0
        crossed = False
        for r in dept_records:
            cumulative += r['amount']
            if not crossed and cumulative > budget:
                crossed = True
                # This record caused the crossing
                if not r['special_approval']:
                    # Check: was there any approved record before this that also crossed?
                    # Actually: the first record that pushes over is the crossing point.
                    # If it has special_approval, it's cleared.
                    # If it doesn't, it's anomalous.
                    # But wait - the rule says "超出预算后无special_approval的记录"
                    # So we need to find records AFTER crossing that lack special_approval
                    pass
            
        # Now find all records after crossing that lack special_approval
        # The first such record is the anomaly
        cumulative = 0.0
        crossed = False
        for r in dept_records:
            cumulative += r['amount']
            if not crossed and cumulative > budget:
                crossed = True
            if crossed and not r['special_approval']:
                findings.append({
                    'rule': 'R11',
                    'record_id': r['record_id'],
                    'employee_id': r['employee_id'],
                    'department_id': dept_id,
                    'department_name': dept_info['name'],
                    'amount': r['amount'],
                    'annual_budget': budget,
                    'cumulative_at_record': round(cumulative, 2),
                    'excess_over_budget': round(cumulative - budget, 2),
                    'reimburse_date': r['reimburse_date'],
                    'special_approval': False,
                    'expense_type': r['expense_type']
                })
    return findings

# Main execution
print("Loading records...")
records = load_records('/workspace/work/analysis/all_records.csv')
print(f"Loaded {len(records)} records")

print("\n=== R1: 差旅住宿超标准 ===")
r1 = check_R1(records)
print(f"Found {len(r1)} anomalies")
for f in r1:
    print(f"  {f['record_id']}: level={f['level']} city={f['city_tier']} amount={f['amount']} nights={f['nights']} per_night={f['per_night']} standard={f['standard']} excess={f['excess']}")

print("\n=== R2: 市内交通超标准 ===")
r2 = check_R2(records)
print(f"Found {len(r2)} anomalies")
for f in r2:
    print(f"  {f['record_id']}: city={f['city_tier']} amount={f['amount']} days={f['days']} per_day={f['per_day']} standard={f['standard']} excess={f['excess']}")

print("\n=== R3: 培训课程费超标准 ===")
r3 = check_R3(records)
print(f"Found {len(r3)} anomalies")
for f in r3:
    print(f"  {f['record_id']}: amount={f['amount']} participants={f['participants']} per_person={f['per_person']} standard=3500 excess={f['excess']}")

print("\n=== R4: 内部培训综合超标准 ===")
r4 = check_R4(records)
print(f"Found {len(r4)} R4 candidates (per_day > 800)")
for f in r4:
    print(f"  {f['record_id']}: amount={f['amount']} days={f['days']} per_day={f['per_day']} vendor={f['vendor_name']} reason={f['reason']}")

print("\n=== R5: 外部培训综合超标准 ===")
r5 = check_R5(records)
print(f"Found {len(r5)} R5 candidates (per_day > 1200)")
for f in r5:
    print(f"  {f['record_id']}: amount={f['amount']} days={f['days']} per_day={f['per_day']} vendor={f['vendor_name']} reason={f['reason']}")

print("\n=== R6: 培训住宿超标准 ===")
r6 = check_R6(records)
print(f"Found {len(r6)} anomalies")
for f in r6:
    print(f"  {f['record_id']}: city={f['city_tier']} amount={f['amount']} nights={f['nights']} per_night={f['per_night']} standard={f['standard']} excess={f['excess']}")

print("\n=== R7: 招待费单次超标准 ===")
r7 = check_R7(records)
print(f"Found {len(r7)} anomalies")
for f in r7:
    print(f"  {f['record_id']}: amount={f['amount']} standard=5000 excess={f['excess']}")

print("\n=== R8: 招待费人均超标准 ===")
r8 = check_R8(records)
print(f"Found {len(r8)} anomalies")
for f in r8:
    print(f"  {f['record_id']}: amount={f['amount']} participants={f['participants']} per_person={f['per_person']} standard=300 excess={f['excess']}")

print("\n=== R9: 办公用品月度超标准 ===")
r9 = check_R9(records)
print(f"Found {len(r9)} anomaly groups")
for f in r9:
    print(f"  {f['employee_id']} {f['month']}: total={f['total_amount']} standard=600 excess={f['excess']} records={f['record_ids']}")

print("\n=== R10: 通讯费月度超标准 ===")
r10 = check_R10(records)
print(f"Found {len(r10)} anomaly groups")
for f in r10:
    print(f"  {f['employee_id']} {f['month']}: total={f['total_amount']} standard=300 excess={f['excess']} records={f['record_ids']}")

print("\n=== R11: 部门预算超支 ===")
r11_all = check_R11(records)
print(f"Found {len(r11_all)} candidate records after budget crossing (no special_approval)")
# But we need to be more precise: only the FIRST unapproved record that causes the exceedance
# Let me also refine R11

# Combine all findings
all_findings = {
    'R1': r1,
    'R2': r2,
    'R3': r3,
    'R4_candidates': r4,
    'R5_candidates': r5,
    'R6': r6,
    'R7': r7,
    'R8': r8,
    'R9': r9,
    'R10': r10,
    'R11_candidates': r11_all
}

with open('/workspace/work/subagents/data_analyst/raw_findings.json', 'w', encoding='utf-8') as f:
    json.dump(all_findings, f, ensure_ascii=False, indent=2, default=str)

print("\n\nRaw findings saved to raw_findings.json")
print(f"Total R1-R8, R11 individual anomalies: {len(r1)+len(r2)+len(r3)+len(r6)+len(r7)+len(r8)+len(r11_all)}")
print(f"R9 groups: {len(r9)}, total records: {sum(len(g['record_ids']) for g in r9)}")
print(f"R10 groups: {len(r10)}, total records: {sum(len(g['record_ids']) for g in r10)}")
