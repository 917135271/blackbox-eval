import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

db = sqlite3.connect('/benchmark/data/expense.db')
db.row_factory = sqlite3.Row

# ============================================================
# 1. 重复报销 (Duplicate Reimbursement)
# Policy: 01_expense_reimbursement_2025.md Article 10
# ============================================================
reused = db.execute("""
    SELECT i.invoice_id, i.invoice_no, i.vendor_name, i.invoice_date, i.amount, i.expense_type,
           COUNT(r.record_id) as usage_count,
           GROUP_CONCAT(r.record_id) as record_ids
    FROM invoices i
    JOIN expense_records r ON r.invoice_id = i.invoice_id
    GROUP BY i.invoice_id
    HAVING usage_count > 1
""").fetchall()

print("=== 重复报销 ===")
dup_groups = []
for row in reused:
    recs = row['record_ids'].split(',')
    dup_groups.append({
        'invoice_id': row['invoice_id'],
        'invoice_no': row['invoice_no'],
        'usage_count': row['usage_count'],
        'record_ids': recs
    })
    print(f"Invoice {row['invoice_no']}: {row['usage_count']} uses, records: {recs}")

# ============================================================
# 2. 拆分报销 (Split Reimbursement)
# Policy: 01_expense_reimbursement_2025.md Article 11
# Same employee, same expense_type, within 7 days
# ============================================================
print("\n=== 拆分报销 ===")
records = db.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, r.expense_type, r.expense_date, r.amount, r.department_id
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.status = 'approved'
    ORDER BY r.employee_id, r.expense_type, r.expense_date
""").fetchall()

emp_type_groups = defaultdict(list)
for row in records:
    key = (row['employee_id'], row['expense_type'])
    emp_type_groups[key].append(dict(row))

split_groups = []
for (emp_id, exp_type), recs in emp_type_groups.items():
    if len(recs) < 2:
        continue
    recs.sort(key=lambda x: x['expense_date'])
    
    i = 0
    while i < len(recs):
        cluster = [recs[i]]
        j = i + 1
        while j < len(recs):
            d1 = datetime.strptime(recs[i]['expense_date'], '%Y-%m-%d')
            d2 = datetime.strptime(recs[j]['expense_date'], '%Y-%m-%d')
            if (d2 - d1).days <= 7:
                cluster.append(recs[j])
                j += 1
            else:
                break
        if len(cluster) >= 2:
            total = sum(r['amount'] for r in cluster)
            split_groups.append({
                'employee_id': emp_id,
                'employee_name': cluster[0]['employee_name'],
                'expense_type': exp_type,
                'record_ids': [r['record_id'] for r in cluster],
                'total_amount': round(total, 2),
                'count': len(cluster),
                'date_range': f"{cluster[0]['expense_date']} to {cluster[-1]['expense_date']}"
            })
        i = j

print(f"Found {len(split_groups)} split groups")
for g in split_groups[:30]:
    print(f"  {g['employee_id']} {g['employee_name']} {g['expense_type']}: {g['count']} records, total={g['total_amount']}, dates={g['date_range']}")

# ============================================================
# 3. 超标准 (Over-standard)
# Policy: 01_expense_reimbursement_2025.md Article 12
# ============================================================
print("\n=== 超标准 ===")

lodging_std = {
    'E1': {'一类城市': 450, '二类城市': 380, '三类城市': 300},
    'M1': {'一类城市': 650, '二类城市': 550, '三类城市': 450},
    'D1': {'一类城市': 850, '二类城市': 700, '三类城市': 600},
    'X1': {'一类城市': 1100, '二类城市': 900, '三类城市': 750},
}

over_std_records = []

# 3a. travel_lodging
lodging_records = db.execute("""
    SELECT r.record_id, e.employee_name, e.employee_level, r.amount, 
           r.city_tier, r.nights, r.special_approval
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.expense_type = 'travel_lodging' AND r.status = 'approved' AND r.special_approval = 0
""").fetchall()

for r in lodging_records:
    level = r['employee_level']
    city = r['city_tier']
    nights = r['nights'] if r['nights'] else 1
    amount = r['amount']
    
    if city and level in lodging_std and city in lodging_std[level]:
        std_per_night = lodging_std[level][city]
        std_total = std_per_night * nights
        if amount > std_total:
            over_std_records.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': 'travel_lodging',
                'amount': amount,
                'standard': std_total,
                'level': level,
                'city': city,
                'nights': nights,
                'reason': f"住宿{amount}元 > 标准{std_total}元({std_per_night}×{nights}晚)"
            })

# 3b. business_entertainment
ent_records = db.execute("""
    SELECT r.record_id, e.employee_name, r.amount, r.participants, r.special_approval
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.expense_type = 'business_entertainment' AND r.status = 'approved' AND r.special_approval = 0
""").fetchall()

for r in ent_records:
    amount = r['amount']
    participants = r['participants'] if r['participants'] else 1
    if amount > 5000:
        over_std_records.append({
            'record_id': r['record_id'],
            'employee_name': r['employee_name'],
            'expense_type': 'business_entertainment',
            'amount': amount,
            'standard': 5000,
            'reason': f"单次招待费{amount}元 > 标准5000元"
        })
    elif participants > 0 and amount / participants > 300:
        over_std_records.append({
            'record_id': r['record_id'],
            'employee_name': r['employee_name'],
            'expense_type': 'business_entertainment',
            'amount': amount,
            'standard': 300 * participants,
            'participants': participants,
            'reason': f"人均{(amount/participants):.2f}元 > 标准300元 ({amount}/{participants}人)"
        })

# 3c. training_fee
training_records = db.execute("""
    SELECT r.record_id, e.employee_name, r.amount, r.special_approval
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.expense_type = 'training_fee' AND r.status = 'approved' AND r.special_approval = 0
""").fetchall()

for r in training_records:
    if r['amount'] > 3500:
        over_std_records.append({
            'record_id': r['record_id'],
            'employee_name': r['employee_name'],
            'expense_type': 'training_fee',
            'amount': r['amount'],
            'standard': 3500,
            'reason': f"培训费{r['amount']}元 > 标准3500元/人/期"
        })

# 3d. office_supplies - single record > 600
office_records = db.execute("""
    SELECT r.record_id, e.employee_name, r.amount, r.special_approval
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.expense_type = 'office_supplies' AND r.status = 'approved' AND r.special_approval = 0
""").fetchall()

for r in office_records:
    if r['amount'] > 600:
        over_std_records.append({
            'record_id': r['record_id'],
            'employee_name': r['employee_name'],
            'expense_type': 'office_supplies',
            'amount': r['amount'],
            'standard': 600,
            'reason': f"单笔办公用品{r['amount']}元 > 月标准600元"
        })

# 3e. communication - single record > 300
comm_records = db.execute("""
    SELECT r.record_id, e.employee_name, r.amount, r.special_approval
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.expense_type = 'communication' AND r.status = 'approved' AND r.special_approval = 0
""").fetchall()

for r in comm_records:
    if r['amount'] > 300:
        over_std_records.append({
            'record_id': r['record_id'],
            'employee_name': r['employee_name'],
            'expense_type': 'communication',
            'amount': r['amount'],
            'standard': 300,
            'reason': f"单笔通讯费{r['amount']}元 > 月标准300元"
        })

# 3f. local_transport
transport_std = {'一类城市': 120, '二类城市': 100, '三类城市': 80}
transport_records = db.execute("""
    SELECT r.record_id, e.employee_name, r.amount, r.city_tier, r.days, r.special_approval
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.expense_type = 'local_transport' AND r.status = 'approved' AND r.special_approval = 0
""").fetchall()

for r in transport_records:
    if r['city_tier'] and r['city_tier'] in transport_std:
        days = r['days'] if r['days'] and r['days'] > 0 else 1
        daily_std = transport_std[r['city_tier']]
        total_std = daily_std * days
        if r['amount'] > total_std:
            over_std_records.append({
                'record_id': r['record_id'],
                'employee_name': r['employee_name'],
                'expense_type': 'local_transport',
                'amount': r['amount'],
                'standard': total_std,
                'city': r['city_tier'],
                'days': days,
                'reason': f"市内交通{r['amount']}元 > 标准{total_std}元({daily_std}×{days}天)"
            })

print(f"Found {len(over_std_records)} over-standard records")
for r in over_std_records[:40]:
    print(f"  {r['record_id']} {r['expense_type']}: {r['reason']}")

# ============================================================
# 4. 超预算 (Over-budget)
# ============================================================
print("\n=== 超预算 ===")

budget_records = db.execute("""
    SELECT r.record_id, r.department_id, d.department_name, d.annual_budget,
           r.amount, r.reimburse_date, r.special_approval
    FROM expense_records r
    JOIN departments d ON r.department_id = d.department_id
    WHERE r.status = 'approved'
    ORDER BY r.department_id, r.reimburse_date, r.record_id
""").fetchall()

dept_cumulative = {}
over_budget_depts = []

for row in budget_records:
    dept_id = row['department_id']
    if dept_id not in dept_cumulative:
        dept_cumulative[dept_id] = {'cumulative': 0, 'budget': row['annual_budget'], 'key_record': None, 'name': row['department_name']}
    
    dept = dept_cumulative[dept_id]
    if dept['key_record'] is None:
        dept['cumulative'] += row['amount']
        if dept['cumulative'] > dept['budget'] and row['special_approval'] == 0:
            dept['key_record'] = row['record_id']

for dept_id, dept in dept_cumulative.items():
    if dept['cumulative'] > dept['budget'] and dept['key_record']:
        over_budget_depts.append({
            'department_id': dept_id,
            'department_name': dept['name'],
            'annual_budget': dept['budget'],
            'total_spent': round(dept['cumulative'], 2),
            'key_record': dept['key_record'],
            'excess': round(dept['cumulative'] - dept['budget'], 2)
        })

# Also check if key_record itself has special_approval
for d in over_budget_depts:
    kr = db.execute("SELECT special_approval FROM expense_records WHERE record_id = ?", (d['key_record'],)).fetchone()
    if kr and kr['special_approval'] == 1:
        d['exclude'] = True

over_budget_depts = [d for d in over_budget_depts if not d.get('exclude')]

print(f"Found {len(over_budget_depts)} over-budget departments")
for d in over_budget_depts:
    print(f"  {d['department_id']} {d['department_name']}: budget={d['annual_budget']}, spent={d['total_spent']}, key_record={d['key_record']}")

# ============================================================
# 5. 超期报销 (Late Reimbursement)
# ============================================================
print("\n=== 超期报销 ===")
late_records = db.execute("""
    SELECT r.record_id, e.employee_name, r.expense_date, r.reimburse_date,
           CAST(julianday(r.reimburse_date) - julianday(r.expense_date) AS INTEGER) as delay_days,
           r.amount, r.expense_type
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.status = 'approved' 
      AND CAST(julianday(r.reimburse_date) - julianday(r.expense_date) AS INTEGER) > 60
    ORDER BY delay_days DESC
""").fetchall()

print(f"Found {len(late_records)} late reimbursement records")
for r in late_records[:20]:
    print(f"  {r['record_id']}: {r['expense_date']} -> {r['reimburse_date']}, delay={r['delay_days']}d, {r['expense_type']} {r['amount']}")

# ============================================================
# Summary
# ============================================================
print("\n=== SUMMARY ===")
print(f"重复报销 groups: {len(dup_groups)}")
print(f"拆分报销 groups: {len(split_groups)}")
print(f"超标准 records: {len(over_std_records)}")
print(f"超预算 departments: {len(over_budget_depts)}")
print(f"超期报销 records: {len(late_records)}")

results = {
    'dup_groups': dup_groups,
    'split_groups': split_groups,
    'over_std_records': over_std_records,
    'over_budget_depts': over_budget_depts,
    'late_records': [dict(r) for r in late_records]
}

with open('/workspace/work/audit_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

print("\nResults saved to /workspace/work/audit_results.json")
