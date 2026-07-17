import sqlite3
import json
from collections import defaultdict
from datetime import datetime

conn = sqlite3.connect('file:/benchmark/data/expense.db?mode=ro', uri=True)

# Load all records with employee info
cursor = conn.execute("""
SELECT er.record_id, er.employee_id, e.employee_name, e.employee_level, 
       er.expense_type, er.amount, er.expense_date, er.city_tier, er.nights, 
       er.days, er.participants, er.special_approval, er.reason, er.department_id,
       er.invoice_id, i.invoice_no
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
JOIN invoices i ON er.invoice_id = i.invoice_id
ORDER BY er.record_id
""")
records = {}
for row in cursor:
    records[row[0]] = {
        'record_id': row[0], 'employee_id': row[1], 'employee_name': row[2],
        'employee_level': row[3], 'expense_type': row[4], 'amount': row[5],
        'expense_date': row[6], 'city_tier': row[7], 'nights': row[8],
        'days': row[9], 'participants': row[10], 'special_approval': row[11],
        'reason': row[12], 'department_id': row[13], 'invoice_id': row[14],
        'invoice_no': row[15]
    }

# Standards
TRAVEL_STD = {
    'E1': {'A': 450, 'B': 380, 'C': 300},
    'M1': {'A': 650, 'B': 550, 'C': 450},
    'D1': {'A': 850, 'B': 700, 'C': 600},
    'X1': {'A': 1100, 'B': 900, 'C': 750},
}
LOCAL_TRANSPORT_STD = {'A': 120, 'B': 100, 'C': 80}

anomalies = []
anomaly_counter = [0]

def next_aid(cat):
    anomaly_counter[0] += 1
    return f"L3-003-{cat}-{anomaly_counter[0]:03d}"

# === A: Travel Lodging ===
for rid, r in records.items():
    if r['expense_type'] != 'travel_lodging' or r['special_approval'] != 0:
        continue
    level = r['employee_level']
    tier = r['city_tier']
    if tier not in ('A','B','C') or level not in TRAVEL_STD:
        continue
    std_per_night = TRAVEL_STD[level][tier]
    nights = r['nights'] or 1
    max_allowed = std_per_night * nights
    if r['amount'] > max_allowed:
        anomalies.append({
            'anomaly_id': next_aid('A'),
            'category': '差旅住宿超标准',
            'policy': '04_travel_expense.md',
            'clause': '第四条',
            'record_ids': [rid],
            'facts': f"{r['employee_name']}({level}) {tier}类城市 {nights}晚, 标准{std_per_night}元/晚×{nights}={max_allowed}元, 实际{r['amount']}元, 超标{r['amount']-max_allowed:.2f}元",
            'reason': r['reason']
        })

print(f"A: {len([a for a in anomalies if a['category']=='差旅住宿超标准'])}")

# === B: Local Transport ===
for rid, r in records.items():
    if r['expense_type'] != 'local_transport' or r['special_approval'] != 0:
        continue
    tier = r['city_tier']
    if tier not in ('A','B','C'):
        continue
    std_per_day = LOCAL_TRANSPORT_STD[tier]
    days = r['days'] or 1
    max_allowed = std_per_day * days
    if r['amount'] > max_allowed:
        anomalies.append({
            'anomaly_id': next_aid('B'),
            'category': '市内交通超标准',
            'policy': '04_travel_expense.md',
            'clause': '第六条',
            'record_ids': [rid],
            'facts': f"{r['employee_name']} {tier}类城市 {days}天, 标准{std_per_day}元/天×{days}={max_allowed}元, 实际{r['amount']}元, 超标{r['amount']-max_allowed:.2f}元",
            'reason': r['reason']
        })

print(f"B: {len([a for a in anomalies if a['category']=='市内交通超标准'])}")

# === C: Training Fee > 3500 ===
for rid, r in records.items():
    if r['expense_type'] == 'training_fee' and r['special_approval'] == 0 and r['amount'] > 3500:
        anomalies.append({
            'anomaly_id': next_aid('C'),
            'category': '培训课程费超标准',
            'policy': '05_training_expense.md',
            'clause': '第二条',
            'record_ids': [rid],
            'facts': f"{r['employee_name']} 培训费{r['amount']}元, 超过3500元/人/期标准",
            'reason': r['reason']
        })

print(f"C: {len([a for a in anomalies if a['category']=='培训课程费超标准'])}")

# === D: Business Entertainment ===
for rid, r in records.items():
    if r['expense_type'] != 'business_entertainment' or r['special_approval'] != 0:
        continue
    if r['amount'] > 5000:
        anomalies.append({
            'anomaly_id': next_aid('D'),
            'category': '业务招待单次超标准',
            'policy': '06_business_entertainment.md',
            'clause': '第二条',
            'record_ids': [rid],
            'facts': f"{r['employee_name']} 单次招待{r['amount']}元, 超过5000元标准",
            'reason': r['reason']
        })
    elif r['participants'] and r['participants'] > 0 and r['amount'] / r['participants'] > 300:
        anomalies.append({
            'anomaly_id': next_aid('D'),
            'category': '业务招待人均超标准',
            'policy': '06_business_entertainment.md',
            'clause': '第三条',
            'record_ids': [rid],
            'facts': f"{r['employee_name']} 招待{r['amount']}元/{r['participants']}人={r['amount']/r['participants']:.2f}元/人, 超过300元/人标准",
            'reason': r['reason']
        })

print(f"D: {len([a for a in anomalies if a['category'].startswith('业务招待')])}")

# === G: Duplicate Invoice ===
inv_map = defaultdict(list)
for rid, r in records.items():
    inv_map[r['invoice_no']].append(rid)

for inv_no, rids in inv_map.items():
    if len(rids) > 1:
        anomalies.append({
            'anomaly_id': next_aid('G'),
            'category': '重复报销',
            'policy': '01_expense_reimbursement_2025.md',
            'clause': '第十条',
            'record_ids': sorted(rids),
            'facts': f"发票{inv_no}在{len(rids)}条报销记录中重复出现",
            'reason': '/'.join([records[rid]['reason'] for rid in sorted(rids)])
        })

print(f"G: {len([a for a in anomalies if a['category']=='重复报销'])}")

# === H: Split Billing ===
groups = defaultdict(list)
for rid, r in records.items():
    if r['special_approval'] != 0:
        continue
    groups[(r['employee_id'], r['expense_type'])].append(r)

all_windows = []
for key, recs in groups.items():
    if len(recs) < 2:
        continue
    recs.sort(key=lambda x: x['expense_date'])
    for i in range(len(recs)):
        window = [recs[i]]
        wsum = recs[i]['amount']
        d0 = datetime.strptime(recs[i]['expense_date'], '%Y-%m-%d')
        for j in range(i+1, len(recs)):
            dj = datetime.strptime(recs[j]['expense_date'], '%Y-%m-%d')
            if (dj - d0).days <= 7:
                window.append(recs[j])
                wsum += recs[j]['amount']
            else:
                break
        if len(window) >= 2 and wsum >= 3000:
            all_windows.append({
                'key': key, 'records': window, 'total': wsum,
                'rids': frozenset(r['record_id'] for r in window)
            })

all_windows.sort(key=lambda w: (-len(w['records']), -w['total']))
used_rids = set()
for w in all_windows:
    if w['rids'].issubset(used_rids):
        continue
    new_rids = w['rids'] - used_rids
    if len(new_rids) >= 2 or (len(new_rids) == 1 and len(w['rids']) >= 2):
        used_rids.update(w['rids'])
        rids_sorted = sorted(w['rids'])
        recs_sorted = sorted(w['records'], key=lambda x: x['expense_date'])
        anomalies.append({
            'anomaly_id': next_aid('H'),
            'category': '拆分报销规避审批',
            'policy': '01_expense_reimbursement_2025.md',
            'clause': '第十一条',
            'record_ids': rids_sorted,
            'facts': f"{recs_sorted[0]['employee_name']} {recs_sorted[0]['expense_type']} {recs_sorted[0]['expense_date']}~{recs_sorted[-1]['expense_date']}共{len(w['records'])}笔合计{w['total']:.2f}元, 达到AR-02线(≥3000), 涉嫌拆分规避审批",
            'reason': '; '.join([f"{r['record_id']}:{r['amount']}元({r['expense_date']})" for r in recs_sorted])
        })

print(f"H: {len([a for a in anomalies if a['category']=='拆分报销规避审批'])}")

# === I: Budget Exceedance ===
dept_budgets = {}
cursor = conn.execute("SELECT department_id, department_name, annual_budget FROM departments")
for row in cursor:
    dept_budgets[row[0]] = (row[1], row[2])

dept_recs = defaultdict(list)
for rid, r in records.items():
    dept_recs[r['department_id']].append(r)

for did, (dname, budget) in dept_budgets.items():
    recs = sorted(dept_recs[did], key=lambda x: (x['expense_date'], x['record_id']))
    running = 0.0
    for r in recs:
        running += r['amount']
        if running > budget and (running - r['amount']) <= budget:
            anomalies.append({
                'anomaly_id': next_aid('I'),
                'category': '部门预算超支',
                'policy': '08_budget_management.md',
                'clause': '第三条',
                'record_ids': [r['record_id']],
                'facts': f"{dname} 年度预算{budget:.2f}元, {r['expense_date']}报销{r['amount']:.2f}元后累计{running:.2f}元, 超过预算1.0倍, 无专项审批",
                'reason': r['reason']
            })
            break

print(f"I: {len([a for a in anomalies if a['category']=='部门预算超支'])}")

# === E: Office Supplies Monthly ===
cursor = conn.execute("""
SELECT er.employee_id, e.employee_name, strftime('%Y-%m', er.expense_date) AS month,
       SUM(er.amount) AS total_amount, GROUP_CONCAT(er.record_id, ',') AS rids
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
WHERE er.expense_type = 'office_supplies' AND er.special_approval = 0
GROUP BY er.employee_id, strftime('%Y-%m', er.expense_date)
HAVING SUM(er.amount) > 600
ORDER BY total_amount DESC
""")
off_count = 0
for row in cursor:
    rids_list = sorted(row[4].split(','))
    off_count += 1
    anomalies.append({
        'anomaly_id': next_aid('E'),
        'category': '办公用品月度超标准',
        'policy': '07_office_communication.md',
        'clause': '第二条',
        'record_ids': rids_list,
        'facts': f"{row[1]} {row[2]} 办公用品合计{row[3]:.2f}元, 超过600元/人/月标准",
        'reason': f"月合计{row[3]:.2f}元, 共{len(rids_list)}笔"
    })
print(f"E: {off_count}")

# === F: Communication Monthly ===
cursor = conn.execute("""
SELECT er.employee_id, e.employee_name, strftime('%Y-%m', er.expense_date) AS month,
       SUM(er.amount) AS total_amount, GROUP_CONCAT(er.record_id, ',') AS rids
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
WHERE er.expense_type = 'communication' AND er.special_approval = 0
GROUP BY er.employee_id, strftime('%Y-%m', er.expense_date)
HAVING SUM(er.amount) > 300
ORDER BY total_amount DESC
""")
comm_count = 0
for row in cursor:
    rids_list = sorted(row[4].split(','))
    comm_count += 1
    anomalies.append({
        'anomaly_id': next_aid('F'),
        'category': '通讯费用月度超标准',
        'policy': '07_office_communication.md',
        'clause': '第三条',
        'record_ids': rids_list,
        'facts': f"{row[1]} {row[2]} 通讯费合计{row[3]:.2f}元, 超过300元/人/月标准",
        'reason': f"月合计{row[3]:.2f}元, 共{len(rids_list)}笔"
    })
print(f"F: {comm_count}")

print(f"\n=== TOTAL ANOMALIES: {len(anomalies)} ===")

# Collect all unique record IDs
all_rids = sorted(set().union(*[set(a['record_ids']) for a in anomalies]))
print(f"Total unique record IDs: {len(all_rids)}")

# Count by category
cats = defaultdict(int)
for a in anomalies:
    cats[a['category']] += 1
for c, n in sorted(cats.items()):
    print(f"  {c}: {n}")

# Save findings
with open('/workspace/work/analysis/data_findings.json', 'w') as f:
    json.dump({
        'total_records': len(records),
        'total_anomalies': len(anomalies),
        'total_unique_record_ids': len(all_rids),
        'anomalies': anomalies,
        'all_anomaly_ids': [a['anomaly_id'] for a in anomalies],
        'all_record_ids': all_rids
    }, f, ensure_ascii=False, indent=2)

conn.close()
print("\nSaved to work/analysis/data_findings.json")
