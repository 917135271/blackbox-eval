import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = "/benchmark/data/expense.db"

conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# ===================== LOAD ALL DATA =====================

# All expense records with detail
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
print(f"Total records: {len(records)}")

# ===================== 1. DUPLICATE REIMBURSEMENT =====================
# Find invoices with usage_count >= 2
dup_invoices = conn.execute("""
    SELECT i.invoice_id, i.invoice_no, i.vendor_name, i.invoice_date, i.amount, i.expense_type,
           COUNT(r.record_id) AS usage_count,
           GROUP_CONCAT(r.record_id) AS record_ids
    FROM invoices i
    JOIN expense_records r ON r.invoice_id = i.invoice_id
    GROUP BY i.invoice_id
    HAVING COUNT(r.record_id) >= 2
    ORDER BY i.invoice_no
""").fetchall()

dup_invoice_list = []
for row in dup_invoices:
    d = dict(row)
    d['record_ids'] = [x for x in d['record_ids'].split(',') if x]
    dup_invoice_list.append(d)

print(f"\n=== DUPLICATE INVOICES: {len(dup_invoice_list)} groups ===")
for d in dup_invoice_list:
    print(f"  Invoice {d['invoice_no']}: {d['usage_count']} usages, records: {d['record_ids']}")

# ===================== 2. SPLIT REIMBURSEMENT =====================
# Same employee + same expense_type + within 7-day window
# Policy Article 11: "同一员工、同一费用类型在7天内出现2笔及以上报销，且合计金额达到《授权管理办法》附件二较高审批线的，应重点核查拆分规避审批"
# Higher approval threshold = AR-02 (>=3000)

# Group by employee + expense_type
from itertools import groupby

# Sort by employee_id, expense_type, expense_date
sorted_recs = sorted(records, key=lambda r: (r['employee_id'], r['expense_type'], r['expense_date']))

split_groups = []
for (emp_id, exp_type), group in groupby(
    [(r['employee_id'], r['expense_type']) for r in sorted_recs], 
    lambda x: x
):
    pass

# Better: iterate through each employee/expense_type group
emp_exp_groups = defaultdict(list)
for r in records:
    key = (r['employee_id'], r['expense_type'])
    emp_exp_groups[key].append(r)

split_findings = []
for (emp_id, exp_type), recs in emp_exp_groups.items():
    if len(recs) < 2:
        continue
    
    # Sort by expense_date
    recs_sorted = sorted(recs, key=lambda r: r['expense_date'])
    
    # Sliding window: find groups within 7 days
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
            total_amount = sum(r['amount'] for r in window)
            # Check if total >= 3000 (AR-02 higher threshold)
            if total_amount >= 3000:
                split_findings.append({
                    'employee_id': emp_id,
                    'employee_name': window[0]['employee_name'],
                    'expense_type': exp_type,
                    'window_start': window[0]['expense_date'],
                    'window_end': window[-1]['expense_date'],
                    'record_count': len(window),
                    'total_amount': round(total_amount, 2),
                    'record_ids': [r['record_id'] for r in window],
                })
        
        i = j  # Move to next window start

print(f"\n=== SPLIT REIMBURSEMENT: {len(split_findings)} groups ===")
for sf in split_findings:
    print(f"  {sf['employee_name']} ({sf['employee_id']}) / {sf['expense_type']}: "
          f"{sf['window_start']}~{sf['window_end']}, {sf['record_count']} records, "
          f"total={sf['total_amount']}, records={sf['record_ids']}")

# ===================== 3. OVER-STANDARD =====================
# Per Article 12: 无专项审批时，报销金额不得超过对应制度标准的1.0倍
# Standards:
# - travel_lodging: based on employee_level + city_tier (04_travel_expense.md Article 4)
#   Employee levels: X1->员工级, E1->经理级, D1->部门负责人级, G1->高管级 (need to map)
# - training_fee: max 3500 per person per session (05_training_expense.md Article 2)
# - business_entertainment: max 5000 per event (06_business_entertainment.md Article 2), 300 per person (Article 3)
# - office_supplies: max 600 per person per month (07_office_communication.md Article 2) 
#   BUT: "办公用品和通讯费用不评价多笔月度累计" -> only check single record > 600
# - communication: max 300 per person per month (07_office_communication.md Article 3)
#   BUT: same as above - only single record > 300
# - local_transport: based on city_tier and days (04_travel_expense.md Article 6)

# Map employee_level to position
# Looking at data: X1->员工, E1->员工, D1->员工... Let me check
level_map = {}
for r in records:
    level_map[r['employee_level']] = r['position_role']
print(f"\nLevel mapping: {level_map}")

# Actually, let me re-read the travel policy: it says 员工级, 经理级, 部门负责人级, 高管级
# And the employee data has employee_level and position_role
# Let me check what levels exist
levels = conn.execute("SELECT DISTINCT employee_level, position_role FROM employees").fetchall()
print(f"Employee levels: {[(l['employee_level'], l['position_role']) for l in levels]}")

# The policy specifies by position_role, so let me use that
travel_standards = {
    '员工': {'一类': 450, '二类': 380, '三类': 300},
    '经理': {'一类': 650, '二类': 550, '三类': 450},
    '部门负责人': {'一类': 850, '二类': 700, '三类': 600},
    '高管': {'一类': 1100, '二类': 900, '三类': 750},
}

# city_tier mapping: A->一类, B->二类, C->三类
city_tier_map = {'A': '一类', 'B': '二类', 'C': '三类'}

# local_transport standards (per day)
transport_standards = {'一类': 120, '二类': 100, '三类': 80}

over_standard_findings = []

for r in records:
    if r['special_approval'] == 1:
        continue  # Has special approval, skip
    
    exp_type = r['expense_type']
    amount = r['amount']
    
    if exp_type == 'travel_lodging':
        city_tier = r.get('city_tier')
        position = r.get('position_role', '员工')
        nights = r.get('nights')
        
        if city_tier and position in travel_standards:
            tier = city_tier_map.get(city_tier, '二类')
            per_night_std = travel_standards[position].get(tier, 380)
            if nights and nights > 0:
                per_night_actual = amount / nights
                if per_night_actual > per_night_std:
                    over_standard_findings.append({
                        'record_id': r['record_id'],
                        'employee_name': r['employee_name'],
                        'expense_type': exp_type,
                        'amount': amount,
                        'standard': per_night_std,
                        'actual_per_unit': round(per_night_actual, 2),
                        'unit': 'per_night',
                        'detail': f"{nights}晚, {city_tier}({tier}), {position}"
                    })
    
    elif exp_type == 'training_fee':
        std = 3500
        if amount > std:
            over_standard_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': std,
                'actual_per_unit': amount,
                'unit': 'per_session',
                'detail': f"每人每期不超过{std}元"
            })
    
    elif exp_type == 'business_entertainment':
        std_event = 5000
        std_per_person = 300
        participants = r.get('participants')
        
        if amount > std_event:
            over_standard_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': std_event,
                'actual_per_unit': amount,
                'unit': 'per_event',
                'detail': f"单次活动不超过{std_event}元"
            })
        elif participants and participants > 0:
            per_person = amount / participants
            if per_person > std_per_person:
                over_standard_findings.append({
                    'record_id': r['record_id'],
                    'employee_name': r['employee_name'],
                    'expense_type': exp_type,
                    'amount': amount,
                    'standard': std_per_person,
                    'actual_per_unit': round(per_person, 2),
                    'unit': 'per_person',
                    'detail': f"{participants}人, 人均不超过{std_per_person}元"
                })
    
    elif exp_type == 'office_supplies':
        std = 600
        if amount > std:
            over_standard_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': std,
                'actual_per_unit': amount,
                'unit': 'per_record',
                'detail': f"每人每月不超过{std}元（仅计单笔）"
            })
    
    elif exp_type == 'communication':
        std = 300
        if amount > std:
            over_standard_findings.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': exp_type,
                'amount': amount,
                'standard': std,
                'actual_per_unit': amount,
                'unit': 'per_record',
                'detail': f"每人每月不超过{std}元（仅计单笔）"
            })
    
    elif exp_type == 'local_transport':
        city_tier = r.get('city_tier')
        days = r.get('days')
        if city_tier and days and days > 0:
            tier = city_tier_map.get(city_tier, '二类')
            daily_std = transport_standards.get(tier, 100)
            per_day_actual = amount / days
            if per_day_actual > daily_std:
                over_standard_findings.append({
                    'record_id': r['record_id'],
                    'employee_name': r['employee_name'],
                    'expense_type': exp_type,
                    'amount': amount,
                    'standard': daily_std,
                    'actual_per_unit': round(per_day_actual, 2),
                    'unit': 'per_day',
                    'detail': f"{days}天, {city_tier}({tier}), 每日{daily_std}元"
                })

print(f"\n=== OVER-STANDARD: {len(over_standard_findings)} records ===")
for osf in over_standard_findings[:20]:
    print(f"  {osf['record_id']}: {osf['employee_name']} / {osf['expense_type']}: "
          f"{osf['amount']} > {osf['standard']} ({osf['unit']}), {osf['detail']}")

# ===================== 4. OVER-BUDGET =====================
# Per Article 13 of 01_expense_reimbursement_2025.md and Article 3 of 08_budget_management.md
# Department budget exceeded + no special approval
# "以按reimburse_date和record_id累计时首次使累计支出超过预算且无专项审批的记录作为关键记录"

# Get department budgets
dept_budgets = {}
for row in conn.execute("SELECT department_id, annual_budget FROM departments").fetchall():
    dept_budgets[row['department_id']] = float(row['annual_budget'])

# For each department, accumulate by reimburse_date, record_id
over_budget_findings = []

for dept_id, budget in dept_budgets.items():
    dept_recs = [r for r in records if r['department_id'] == dept_id]
    dept_recs_sorted = sorted(dept_recs, key=lambda r: (r['reimburse_date'], r['record_id']))
    
    cumulative = 0.0
    exceeded = False
    key_record = None
    all_over_records = []
    
    for r in dept_recs_sorted:
        cumulative += r['amount']
        if not exceeded and cumulative > budget:
            exceeded = True
            # The key record is the one that first pushed cumulative over budget
            # and has no special approval
            if r['special_approval'] == 0:
                key_record = r['record_id']
        
        if cumulative > budget and r['special_approval'] == 0:
            all_over_records.append(r['record_id'])
    
    if exceeded and key_record:
        over_budget_findings.append({
            'department_id': dept_id,
            'department_name': dept_recs[0]['department_name'] if dept_recs else '',
            'annual_budget': budget,
            'total_used': round(cumulative, 2),
            'usage_rate': round(cumulative / budget, 4),
            'key_record_id': key_record,
            'all_over_record_ids': all_over_records
        })

print(f"\n=== OVER-BUDGET: {len(over_budget_findings)} departments ===")
for obf in over_budget_findings:
    print(f"  {obf['department_id']} {obf['department_name']}: "
          f"budget={obf['annual_budget']}, used={obf['total_used']}, "
          f"key_record={obf['key_record_id']}, "
          f"over_records_count={len(obf['all_over_record_ids'])}")

# ===================== 5. OVERDUE REIMBURSEMENT =====================
# Article 7: 60 days from expense_date to submit
# Article 9: year-end expenses can be submitted within 15 days after fiscal year end
# For records where reimburse_date - expense_date > 60 days

overdue_findings = []
for r in records:
    exp_date = datetime.strptime(r['expense_date'], '%Y-%m-%d')
    reim_date = datetime.strptime(r['reimburse_date'], '%Y-%m-%d')
    delay = (reim_date - exp_date).days
    
    # Article 9: year-end expenses (Dec) can be extended by 15 days after year end
    # So the cutoff is: for Dec expenses, could be up to Jan 15 of next year
    # Let's check: if expense is in Dec 2025, the deadline extends to... 
    # "会计年度末发生的费用，最迟可在财政年度结束后15天内补充提交" 
    # This means expenses at year-end can be submitted up to Jan 15, 2026 (15 days after fiscal year end)
    # But reimburse_date for all records should be in 2025 (since budget_year=2025)
    # Actually, if the standard is 60 days, and year-end extends to +15 days after year end,
    # For Dec expenses, the extended deadline is Jan 15 next year, which would be at most 
    # ~46 days for Dec 1 expense or ~15 days for Dec 31 expense. 
    # So year-end expenses have a stricter limit than 60 days.
    # But the base rule is "60 days after expense occurs" and year-end is the alternative.
    # Let me just apply: delay > 60 days is overdue.
    
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

print(f"\n=== OVERDUE: {len(overdue_findings)} records ===")
for od in overdue_findings[:10]:
    print(f"  {od['record_id']}: {od['employee_name']} / {od['expense_type']}: "
          f"{od['expense_date']} -> {od['reimburse_date']}, delay={od['delay_days']}d")

# ===================== SAVE RESULTS =====================
output = {
    'duplicate': {
        'count': len(dup_invoice_list),
        'groups': dup_invoice_list
    },
    'split': {
        'count': len(split_findings),
        'groups': split_findings
    },
    'over_standard': {
        'count': len(over_standard_findings),
        'records': over_standard_findings
    },
    'over_budget': {
        'count': len(over_budget_findings),
        'departments': over_budget_findings
    },
    'overdue': {
        'count': len(overdue_findings),
        'records': overdue_findings
    }
}

with open('/workspace/work/analysis_output.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n=== SUMMARY ===")
print(f"Duplicate groups: {len(dup_invoice_list)}")
print(f"Split groups: {len(split_findings)}")
print(f"Over-standard records: {len(over_standard_findings)}")
print(f"Over-budget departments: {len(over_budget_findings)}")
print(f"Overdue records: {len(overdue_findings)}")

conn.close()
