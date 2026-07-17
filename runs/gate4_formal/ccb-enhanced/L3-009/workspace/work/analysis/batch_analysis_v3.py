#!/usr/bin/env python3
"""Final corrected comprehensive five-rule batch analysis for L3-009 audit task."""
import sqlite3
import json
from datetime import datetime
from collections import defaultdict

DB_PATH = "/benchmark/data/expense.db"

LEVEL_MAP = {'E1': '员工级', 'M1': '经理级', 'D1': '部门负责人级', 'X1': '高管级'}
TRAVEL_STD = {
    'E1': {'A': 450, 'B': 380, 'C': 300},
    'M1': {'A': 650, 'B': 550, 'C': 450},
    'D1': {'A': 850, 'B': 700, 'C': 600},
    'X1': {'A': 1100, 'B': 900, 'C': 750}
}
TRAINING_ACCOM_STD = {'A': 500, 'B': 420, 'C': 350}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rule1_duplicate_invoices(conn):
    """R1: Same invoice used in multiple records (Art.10)"""
    cur = conn.cursor()
    cur.execute("""
        SELECT e.record_id, e.invoice_id, inv.invoice_no, e.amount, e.employee_id,
               e.expense_type, e.department_id, e.expense_date
        FROM expense_records e
        JOIN invoices inv ON e.invoice_id = inv.invoice_id
        WHERE e.invoice_id IN (
            SELECT invoice_id FROM expense_records
            GROUP BY invoice_id HAVING COUNT(*) > 1
        )
        ORDER BY e.invoice_id, e.expense_date
    """)
    groups = defaultdict(list)
    for r in cur.fetchall():
        groups[r['invoice_id']].append({
            'record_id': r['record_id'], 'invoice_id': r['invoice_id'],
            'invoice_no': r['invoice_no'], 'amount': r['amount'],
            'employee_id': r['employee_id'], 'expense_type': r['expense_type'],
            'expense_date': r['expense_date']
        })

    anomaly_groups, all_ids = [], []
    for inv_id, records in groups.items():
        if len(records) > 1:
            anomaly_groups.append({
                'invoice_id': inv_id, 'invoice_no': records[0]['invoice_no'],
                'record_ids': [r['record_id'] for r in records], 'records': records
            })
            all_ids.extend([r['record_id'] for r in records])
    return anomaly_groups, list(set(all_ids))

def rule2_split_reimbursement(conn):
    """R2: Same employee, same expense_type, within 7 days, 2+ records, sum >= 3000"""
    cur = conn.cursor()
    cur.execute("""
        SELECT record_id, employee_id, expense_type, amount, expense_date
        FROM expense_records ORDER BY employee_id, expense_type, expense_date
    """)
    groups = defaultdict(list)
    for r in cur.fetchall():
        groups[(r['employee_id'], r['expense_type'])].append({
            'record_id': r['record_id'], 'amount': r['amount'],
            'expense_date': r['expense_date']
        })

    matched_ids, split_groups, seen = set(), [], set()
    for key, records in groups.items():
        if len(records) < 2:
            continue
        emp, etype = key
        n = len(records)
        for i in range(n):
            d_i = datetime.strptime(records[i]['expense_date'], '%Y-%m-%d')
            window_ids, window_amt = [records[i]['record_id']], records[i]['amount']
            for j in range(n):
                if i == j: continue
                d_j = datetime.strptime(records[j]['expense_date'], '%Y-%m-%d')
                if abs((d_j - d_i).days) <= 7:
                    window_ids.append(records[j]['record_id'])
                    window_amt += records[j]['amount']
            if len(window_ids) >= 2 and window_amt >= 3000:
                key_ids = tuple(sorted(window_ids))
                if key_ids not in seen:
                    seen.add(key_ids)
                    for rid in key_ids: matched_ids.add(rid)
                    split_groups.append({
                        'employee_id': emp, 'expense_type': etype,
                        'record_ids': list(key_ids), 'total_amount': round(window_amt, 2),
                        'count': len(key_ids), 'anchor_date': records[i]['expense_date']
                    })
    return split_groups, list(matched_ids)

def rule3_over_standard(conn):
    """R3: Over-standard expenses without special_approval"""
    anomalies = []
    unresolved = []

    # R3a: Travel accommodation
    cur = conn.cursor()
    cur.execute("""
        SELECT er.record_id, er.amount, er.city_tier, er.nights, emp.employee_level
        FROM expense_records er
        JOIN employees emp ON er.employee_id = emp.employee_id
        WHERE er.expense_type = 'travel_lodging' AND er.special_approval = 0
    """)
    for r in cur.fetchall():
        level, tier = r['employee_level'], r['city_tier']
        if level in TRAVEL_STD and tier in TRAVEL_STD[level]:
            max_night = TRAVEL_STD[level][tier]
            nights = max(r['nights'] or 1, 1)
            per_night = r['amount'] / nights
            if per_night > max_night:
                anomalies.append({
                    'record_id': r['record_id'], 'rule': 'R3-差旅住宿超标',
                    'amount': r['amount'], 'standard': max_night,
                    'per_night': round(per_night, 2), 'nights': nights,
                    'level': LEVEL_MAP.get(level, level), 'city_tier': tier
                })

    # R3b: Business entertainment
    cur.execute("""
        SELECT record_id, amount, participants
        FROM expense_records
        WHERE expense_type = 'business_entertainment' AND special_approval = 0
    """)
    for r in cur.fetchall():
        if r['amount'] > 5000:
            anomalies.append({
                'record_id': r['record_id'], 'rule': 'R3-业务招待费单次超标',
                'amount': r['amount'], 'standard': 5000
            })
        else:
            p = max(r['participants'] or 1, 1)
            pp = r['amount'] / p
            if pp > 300:
                anomalies.append({
                    'record_id': r['record_id'], 'rule': 'R3-业务招待费人均超标',
                    'amount': r['amount'], 'standard': 300,
                    'per_person': round(pp, 2), 'participants': p
                })

    # R3c: Training course fee - only reason contains "课程费" or "集中培训课程"
    cur.execute("""
        SELECT record_id, amount, reason
        FROM expense_records
        WHERE expense_type = 'training_fee' AND special_approval = 0
          AND (reason LIKE '%课程费%' OR reason LIKE '%集中培训课程%')
    """)
    for r in cur.fetchall():
        if r['amount'] > 3500:
            anomalies.append({
                'record_id': r['record_id'], 'rule': 'R3-培训课程费超标',
                'amount': r['amount'], 'standard': 3500, 'reason': r['reason']
            })

    # R3d: External training comprehensive fee - need days to calculate per-day
    # Since all training_fee records have NULL days, we cannot determine per-day rate
    cur.execute("""
        SELECT record_id, amount, days, reason
        FROM expense_records
        WHERE expense_type = 'training_fee' AND special_approval = 0
          AND reason LIKE '%外部培训%'
          AND days IS NOT NULL
    """)
    for r in cur.fetchall():
        days = max(r['days'], 1)
        per_day = r['amount'] / days
        if per_day > 1200:
            anomalies.append({
                'record_id': r['record_id'], 'rule': 'R3-外部培训综合费超标',
                'amount': r['amount'], 'standard': 1200,
                'per_day': round(per_day, 2), 'days': days, 'reason': r['reason']
            })

    # Note: all external training records have NULL days - can't verify per-day limit
    cur.execute("""
        SELECT COUNT(*) FROM expense_records
        WHERE expense_type = 'training_fee' AND special_approval = 0
          AND reason LIKE '%外部培训%' AND days IS NULL
    """)
    ext_null_days = cur.fetchone()[0]
    if ext_null_days > 0:
        unresolved.append({
            'rule': 'R3-外部培训综合费超标',
            'issue': f'{ext_null_days} records have NULL days, cannot compute per-day rate',
            'standard': '1200/day'
        })

    # R3e: Internal training - need days to calculate per-day (all have NULL days)
    cur.execute("""
        SELECT record_id, amount, days, reason
        FROM expense_records
        WHERE expense_type = 'training_fee' AND special_approval = 0
          AND reason NOT LIKE '%课程费%'
          AND reason NOT LIKE '%外部培训%'
          AND reason NOT LIKE '%集中培训课程%'
          AND days IS NOT NULL
    """)
    for r in cur.fetchall():
        days = max(r['days'], 1)
        per_day = r['amount'] / days
        if per_day > 800:
            anomalies.append({
                'record_id': r['record_id'], 'rule': 'R3-内部培训综合费超标',
                'amount': r['amount'], 'standard': 800,
                'per_day': round(per_day, 2), 'days': days, 'reason': r['reason']
            })

    cur.execute("""
        SELECT COUNT(*) FROM expense_records
        WHERE expense_type = 'training_fee' AND special_approval = 0
          AND reason NOT LIKE '%课程费%'
          AND reason NOT LIKE '%外部培训%'
          AND reason NOT LIKE '%集中培训课程%'
          AND days IS NULL
    """)
    int_null_days = cur.fetchone()[0]
    if int_null_days > 0:
        unresolved.append({
            'rule': 'R3-内部培训综合费超标',
            'issue': f'{int_null_days} records have NULL days, cannot compute per-day rate',
            'standard': '800/day'
        })

    # R3f: Office supplies per employee per month > 600
    cur.execute("""
        SELECT employee_id, strftime('%Y-%m', expense_date) as month, SUM(amount) as total
        FROM expense_records
        WHERE expense_type = 'office_supplies' AND special_approval = 0
        GROUP BY employee_id, month HAVING SUM(amount) > 600
    """)
    over_office = [(r['employee_id'], r['month'], r['total']) for r in cur.fetchall()]

    cur.execute("""
        SELECT record_id, employee_id, amount, strftime('%Y-%m', expense_date) as month
        FROM expense_records
        WHERE expense_type = 'office_supplies' AND special_approval = 0
    """)
    office_by_key = defaultdict(list)
    for r in cur.fetchall():
        office_by_key[(r['employee_id'], r['month'])].append(r['record_id'])

    for emp, month, total in over_office:
        for rid in office_by_key.get((emp, month), []):
            anomalies.append({
                'record_id': rid, 'rule': 'R3-办公用品月度超标',
                'monthly_total': round(total, 2), 'standard': 600,
                'employee_id': emp, 'month': month
            })

    # R3g: Communication per employee per month > 300
    cur.execute("""
        SELECT employee_id, strftime('%Y-%m', expense_date) as month, SUM(amount) as total
        FROM expense_records
        WHERE expense_type = 'communication' AND special_approval = 0
        GROUP BY employee_id, month HAVING SUM(amount) > 300
    """)
    over_comm = [(r['employee_id'], r['month'], r['total']) for r in cur.fetchall()]

    cur.execute("""
        SELECT record_id, employee_id, amount, strftime('%Y-%m', expense_date) as month
        FROM expense_records
        WHERE expense_type = 'communication' AND special_approval = 0
    """)
    comm_by_key = defaultdict(list)
    for r in cur.fetchall():
        comm_by_key[(r['employee_id'], r['month'])].append(r['record_id'])

    for emp, month, total in over_comm:
        for rid in comm_by_key.get((emp, month), []):
            anomalies.append({
                'record_id': rid, 'rule': 'R3-通讯费月度超标',
                'monthly_total': round(total, 2), 'standard': 300,
                'employee_id': emp, 'month': month
            })

    return anomalies, unresolved

def rule4_over_budget(conn):
    """R4: Department cumulative exceeds annual budget"""
    cur = conn.cursor()
    cur.execute("SELECT department_id, annual_budget FROM departments")
    budgets = {r['department_id']: r['annual_budget'] for r in cur.fetchall()}

    cur.execute("""
        SELECT record_id, department_id, amount, expense_date, special_approval
        FROM expense_records ORDER BY department_id, expense_date, record_id
    """)
    rows = cur.fetchall()

    anomalies = []
    cum = defaultdict(float)
    crossed = {}

    for r in rows:
        dept = r['department_id']
        cum[dept] += r['amount']
        budget = budgets.get(dept, float('inf'))

        if cum[dept] > budget and dept not in crossed:
            crossed[dept] = True

        if dept in crossed and not r['special_approval']:
            anomalies.append({
                'record_id': r['record_id'], 'rule': 'R4-超预算报销',
                'amount': r['amount'], 'department_id': dept,
                'cumulative': round(cum[dept], 2), 'budget': budget,
                'expense_date': r['expense_date']
            })
    return anomalies

def rule5_late_reimbursement(conn):
    """R5: expense_date to reimburse_date > 60 days"""
    cur = conn.cursor()
    cur.execute("""
        SELECT record_id, amount, expense_date, reimburse_date, employee_id, expense_type
        FROM expense_records
    """)
    anomalies = []
    for r in cur.fetchall():
        exp = datetime.strptime(r['expense_date'], '%Y-%m-%d')
        reim = datetime.strptime(r['reimburse_date'], '%Y-%m-%d')
        days = (reim - exp).days
        if days > 60:
            anomalies.append({
                'record_id': r['record_id'], 'rule': 'R5-超期报销',
                'amount': r['amount'], 'expense_date': r['expense_date'],
                'reimburse_date': r['reimburse_date'], 'days_diff': days,
                'employee_id': r['employee_id'], 'expense_type': r['expense_type']
            })
    return anomalies

def main():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM expense_records")
    total = cur.fetchone()[0]
    print(f"Total records: {total}")

    r1_groups, r1_ids = rule1_duplicate_invoices(conn)
    print(f"R1-重复报销: {len(r1_groups)} groups, {len(r1_ids)} records")

    r2_groups, r2_ids = rule2_split_reimbursement(conn)
    print(f"R2-拆分报销: {len(r2_groups)} groups, {len(r2_ids)} records")

    r3, r3_unresolved = rule3_over_standard(conn)
    r3_ids = sorted(set(a['record_id'] for a in r3))
    r3_bd = defaultdict(lambda: {'count': 0, 'ids': []})
    for a in r3:
        r3_bd[a['rule']]['count'] += 1
        r3_bd[a['rule']]['ids'].append(a['record_id'])
    print(f"R3-超标准报销: {len(r3)} records, {len(r3_ids)} unique")
    for rule, info in sorted(r3_bd.items()):
        print(f"  {rule}: {info['count']}")
    if r3_unresolved:
        print(f"  Unresolved: {len(r3_unresolved)} items")
        for u in r3_unresolved:
            print(f"    {u['rule']}: {u['issue']}")

    r4 = rule4_over_budget(conn)
    r4_ids = [a['record_id'] for a in r4]
    print(f"R4-超预算报销: {len(r4)} records")
    r4_dept = defaultdict(int)
    for a in r4: r4_dept[a['department_id']] += 1
    for d, c in sorted(r4_dept.items()):
        print(f"  {d}: {c}")

    r5 = rule5_late_reimbursement(conn)
    r5_ids = [a['record_id'] for a in r5]
    print(f"R5-超期报销: {len(r5)} records")
    for a in r5:
        print(f"  {a['record_id']}: {a['days_diff']}d, {a['expense_type']}")

    all_ids = sorted(set(r1_ids + r2_ids + r3_ids + r4_ids + r5_ids))
    print(f"\nTotal unique anomaly records: {len(all_ids)}")

    results = {
        'task_id': 'L3-009', 'in_scope_population': total,
        'total_anomaly_count': len(all_ids), 'all_anomaly_ids': all_ids,
        'rules': {
            'R1-重复报销': {'anomaly_count': len(r1_ids), 'record_ids': r1_ids, 'groups': r1_groups},
            'R2-拆分报销': {'anomaly_count': len(r2_ids), 'record_ids': r2_ids, 'groups': r2_groups},
            'R3-超标准报销': {
                'anomaly_count': len(r3_ids), 'record_ids': r3_ids,
                'breakdown': {k: {'count': v['count'], 'record_ids': v['ids']}
                             for k, v in r3_bd.items()},
                'unresolved': r3_unresolved
            },
            'R4-超预算报销': {
                'anomaly_count': len(r4_ids), 'record_ids': r4_ids,
                'per_department': {k: v for k, v in r4_dept.items()}
            },
            'R5-超期报销': {
                'anomaly_count': len(r5_ids), 'record_ids': r5_ids, 'details': r5
            }
        },
        'unresolved_items': r3_unresolved
    }

    with open('/workspace/work/analysis/data_findings.json', 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open('/workspace/work/analysis/r1_duplicates.json', 'w') as f:
        json.dump(r1_groups, f, ensure_ascii=False, indent=2)
    with open('/workspace/work/analysis/r2_splits.json', 'w') as f:
        json.dump(r2_groups, f, ensure_ascii=False, indent=2)
    with open('/workspace/work/analysis/r3_over_standard.json', 'w') as f:
        json.dump({'anomalies': r3, 'unresolved': r3_unresolved}, f, ensure_ascii=False, indent=2)
    with open('/workspace/work/analysis/r4_over_budget.json', 'w') as f:
        json.dump(r4, f, ensure_ascii=False, indent=2)
    with open('/workspace/work/analysis/r5_late.json', 'w') as f:
        json.dump(r5, f, ensure_ascii=False, indent=2)

    conn.close()

if __name__ == '__main__':
    main()
