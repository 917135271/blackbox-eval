#!/usr/bin/env python3
"""Comprehensive five-rule batch analysis for L3-009 audit task."""
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = "/benchmark/data/expense.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rule1_duplicate_invoices(conn):
    """R1: Same invoice used in multiple expense records (Art.10)"""
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
    rows = cur.fetchall()
    # Group by invoice_id
    groups = defaultdict(list)
    for r in rows:
        groups[r['invoice_id']].append(dict(r))

    result = []
    for inv_id, records in groups.items():
        if len(records) > 1:
            result.append({
                "invoice_id": inv_id,
                "invoice_no": records[0]['invoice_no'],
                "record_ids": [r['record_id'] for r in records],
                "count": len(records)
            })
    return result

def rule2_split_reimbursement(conn):
    """R2: Same employee, same expense_type, within 7 days, 2+ records, sum >= 3000"""
    cur = conn.cursor()
    cur.execute("""
        SELECT record_id, employee_id, expense_type, amount, expense_date, department_id
        FROM expense_records
        ORDER BY employee_id, expense_type, expense_date
    """)
    rows = cur.fetchall()

    # Group by employee + expense_type
    groups = defaultdict(list)
    for r in rows:
        key = (r['employee_id'], r['expense_type'])
        groups[key].append(dict(r))

    matched_record_ids = set()
    split_groups = []

    for key, records in groups.items():
        if len(records) < 2:
            continue
        n = len(records)
        for i in range(n):
            for j in range(i+1, n):
                d1 = datetime.strptime(records[i]['expense_date'], '%Y-%m-%d')
                d2 = datetime.strptime(records[j]['expense_date'], '%Y-%m-%d')
                if abs((d2 - d1).days) <= 7:
                    # Found at least 2 records within 7 days - now check all in this window
                    window_records = [records[i], records[j]]
                    for k in range(n):
                        if k == i or k == j:
                            continue
                        dk = datetime.strptime(records[k]['expense_date'], '%Y-%m-%d')
                        if abs((dk - d1).days) <= 7 or abs((dk - d2).days) <= 7:
                            window_records.append(records[k])

                    total = sum(r['amount'] for r in window_records)
                    if total >= 3000:
                        ids = [r['record_id'] for r in window_records]
                        for rid in ids:
                            matched_record_ids.add(rid)
                        split_groups.append({
                            "employee_id": key[0],
                            "expense_type": key[1],
                            "record_ids": sorted(ids),
                            "total_amount": round(total, 2),
                            "count": len(ids)
                        })
                    break  # Don't double-count the same group
            else:
                continue
            break

    return split_groups, list(matched_record_ids)

def rule3_over_standard(conn):
    """R3: Exceeds standard without special_approval"""
    anomalies = []

    # R3a: Travel accommodation - needs employee_level join
    cur = conn.cursor()
    cur.execute("""
        SELECT er.record_id, er.employee_id, er.amount, er.city_tier, er.nights,
               er.expense_type, er.special_approval, emp.employee_level, emp.employee_name
        FROM expense_records er
        JOIN employees emp ON er.employee_id = emp.employee_id
        WHERE er.expense_type = '差旅住宿费'
    """)
    travel_std = {
        '员工级': {'一类城市': 450, '二类城市': 380, '三类城市': 300},
        '经理级': {'一类城市': 650, '二类城市': 550, '三类城市': 450},
        '部门负责人级': {'一类城市': 850, '二类城市': 700, '三类城市': 600},
        '高管级': {'一类城市': 1100, '二类城市': 900, '三类城市': 750}
    }
    for r in cur.fetchall():
        if r['special_approval']:
            continue
        level = r['employee_level']
        tier = r['city_tier']
        if level in travel_std and tier in travel_std[level]:
            max_per_night = travel_std[level][tier]
            nights = r['nights'] or 1
            per_night = r['amount'] / nights
            if per_night > max_per_night:
                anomalies.append({
                    "record_id": r['record_id'],
                    "rule": "R3-差旅住宿超标",
                    "amount": r['amount'],
                    "standard_limit": max_per_night,
                    "per_night": round(per_night, 2),
                    "employee_level": level,
                    "city_tier": tier,
                    "nights": nights
                })

    # R3b: Training course fee > 3500/person/period
    cur.execute("""
        SELECT record_id, amount, employee_id, expense_type, special_approval
        FROM expense_records
        WHERE expense_type = '培训课程费'
    """)
    for r in cur.fetchall():
        if r['special_approval']:
            continue
        if r['amount'] > 3500:
            anomalies.append({
                "record_id": r['record_id'],
                "rule": "R3-培训课程费超标",
                "amount": r['amount'],
                "standard_limit": 3500,
                "employee_id": r['employee_id']
            })

    # R3c: Training internal > 800/day
    cur.execute("""
        SELECT record_id, amount, days, employee_id, expense_type, special_approval
        FROM expense_records
        WHERE expense_type = '内部培训综合费'
    """)
    for r in cur.fetchall():
        if r['special_approval']:
            continue
        days = r['days'] or 1
        per_day = r['amount'] / days
        if per_day > 800:
            anomalies.append({
                "record_id": r['record_id'],
                "rule": "R3-内部培训综合费超标",
                "amount": r['amount'],
                "standard_limit": 800,
                "per_day": round(per_day, 2),
                "days": days
            })

    # R3d: Training external > 1200/day
    cur.execute("""
        SELECT record_id, amount, days, employee_id, expense_type, special_approval
        FROM expense_records
        WHERE expense_type = '外部培训综合费'
    """)
    for r in cur.fetchall():
        if r['special_approval']:
            continue
        days = r['days'] or 1
        per_day = r['amount'] / days
        if per_day > 1200:
            anomalies.append({
                "record_id": r['record_id'],
                "rule": "R3-外部培训综合费超标",
                "amount": r['amount'],
                "standard_limit": 1200,
                "per_day": round(per_day, 2),
                "days": days
            })

    # R3e: Training accommodation
    cur.execute("""
        SELECT er.record_id, er.amount, er.city_tier, er.nights, er.expense_type, er.special_approval
        FROM expense_records er
        WHERE er.expense_type = '培训住宿费'
    """)
    training_accom_std = {'一类城市': 500, '二类城市': 420, '三类城市': 350}
    for r in cur.fetchall():
        if r['special_approval']:
            continue
        tier = r['city_tier']
        if tier in training_accom_std:
            max_per_night = training_accom_std[tier]
            nights = r['nights'] or 1
            per_night = r['amount'] / nights
            if per_night > max_per_night:
                anomalies.append({
                    "record_id": r['record_id'],
                    "rule": "R3-培训住宿超标",
                    "amount": r['amount'],
                    "standard_limit": max_per_night,
                    "per_night": round(per_night, 2),
                    "city_tier": tier,
                    "nights": nights
                })

    # R3f: Business entertainment - single > 5000 or per_person > 300
    cur.execute("""
        SELECT record_id, amount, participants, employee_id, expense_type, special_approval
        FROM expense_records
        WHERE expense_type = '业务招待费'
    """)
    for r in cur.fetchall():
        if r['special_approval']:
            continue
        if r['amount'] > 5000:
            anomalies.append({
                "record_id": r['record_id'],
                "rule": "R3-业务招待费单次超标",
                "amount": r['amount'],
                "standard_limit": 5000
            })
            continue
        participants = r['participants'] or 1
        per_person = r['amount'] / participants
        if per_person > 300:
            anomalies.append({
                "record_id": r['record_id'],
                "rule": "R3-业务招待费人均超标",
                "amount": r['amount'],
                "standard_limit": 300,
                "per_person": round(per_person, 2),
                "participants": participants
            })

    # R3g: Office supplies - per person per month > 600
    cur.execute("""
        SELECT record_id, employee_id, amount, expense_date, expense_type, special_approval
        FROM expense_records
        WHERE expense_type = '办公用品'
    """)
    office_by_emp_month = defaultdict(list)
    for r in cur.fetchall():
        month = r['expense_date'][:7]
        office_by_emp_month[(r['employee_id'], month)].append(dict(r))

    for (emp, month), records in office_by_emp_month.items():
        total = sum(r['amount'] for r in records)
        if total > 600:
            for r in records:
                if r['special_approval']:
                    continue
                anomalies.append({
                    "record_id": r['record_id'],
                    "rule": "R3-办公用品月度超标",
                    "amount": r['amount'],
                    "monthly_total": round(total, 2),
                    "standard_limit": 600,
                    "employee_id": emp,
                    "month": month
                })

    # R3h: Communication - per person per month > 300
    cur.execute("""
        SELECT record_id, employee_id, amount, expense_date, expense_type, special_approval
        FROM expense_records
        WHERE expense_type = '通讯费'
    """)
    comm_by_emp_month = defaultdict(list)
    for r in cur.fetchall():
        month = r['expense_date'][:7]
        comm_by_emp_month[(r['employee_id'], month)].append(dict(r))

    for (emp, month), records in comm_by_emp_month.items():
        total = sum(r['amount'] for r in records)
        if total > 300:
            for r in records:
                if r['special_approval']:
                    continue
                anomalies.append({
                    "record_id": r['record_id'],
                    "rule": "R3-通讯费月度超标",
                    "amount": r['amount'],
                    "monthly_total": round(total, 2),
                    "standard_limit": 300,
                    "employee_id": emp,
                    "month": month
                })

    return anomalies

def rule4_over_budget(conn):
    """R4: Department cumulative expense exceeds annual budget"""
    cur = conn.cursor()

    # Get department budgets
    cur.execute("SELECT department_id, annual_budget FROM departments")
    budgets = {r['department_id']: r['annual_budget'] for r in cur.fetchall()}

    # Get all expense records ordered by expense_date
    cur.execute("""
        SELECT record_id, department_id, amount, expense_date, special_approval
        FROM expense_records
        ORDER BY department_id, expense_date, record_id
    """)
    rows = cur.fetchall()

    anomalies = []
    dept_cumulative = defaultdict(float)
    dept_budget_exceeded = {}

    for r in rows:
        dept = r['department_id']
        dept_cumulative[dept] += r['amount']
        budget = budgets.get(dept, float('inf'))

        if dept_cumulative[dept] > budget:
            if dept not in dept_budget_exceeded:
                dept_budget_exceeded[dept] = True
            # This record was submitted after budget exceeded
            if not r['special_approval']:
                anomalies.append({
                    "record_id": r['record_id'],
                    "rule": "R4-超预算报销",
                    "amount": r['amount'],
                    "department_id": dept,
                    "cumulative_amount": round(dept_cumulative[dept], 2),
                    "annual_budget": budget,
                    "expense_date": r['expense_date']
                })

    return anomalies

def rule5_late_reimbursement(conn):
    """R5: expense_date to reimburse_date > 60 days"""
    cur = conn.cursor()
    cur.execute("""
        SELECT record_id, employee_id, amount, expense_date, reimburse_date, expense_type
        FROM expense_records
    """)
    anomalies = []
    for r in cur.fetchall():
        exp_date = datetime.strptime(r['expense_date'], '%Y-%m-%d')
        reim_date = datetime.strptime(r['reimburse_date'], '%Y-%m-%d')
        days_diff = (reim_date - exp_date).days
        if days_diff > 60:
            anomalies.append({
                "record_id": r['record_id'],
                "rule": "R5-超期报销",
                "amount": r['amount'],
                "expense_date": r['expense_date'],
                "reimburse_date": r['reimburse_date'],
                "days_diff": days_diff,
                "employee_id": r['employee_id'],
                "expense_type": r['expense_type']
            })
    return anomalies

def main():
    conn = get_db()

    # Total population count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM expense_records")
    total_records = cur.fetchone()['cnt']

    results = {
        "task_id": "L3-009",
        "in_scope_population": total_records,
        "analysis_date": "2025-07-16",
        "rules": {}
    }

    # R1
    r1 = rule1_duplicate_invoices(conn)
    r1_ids = []
    for g in r1:
        r1_ids.extend(g['record_ids'])
    results["rules"]["R1-重复报销"] = {
        "anomaly_groups": r1,
        "anomaly_count": len(r1),
        "record_ids": list(set(r1_ids))
    }

    # R2
    r2_groups, r2_ids = rule2_split_reimbursement(conn)
    results["rules"]["R2-拆分报销"] = {
        "anomaly_groups": r2_groups,
        "anomaly_count": len(r2_groups),
        "record_ids": r2_ids
    }

    # R3
    r3 = rule3_over_standard(conn)
    r3_ids = list(set(a['record_id'] for a in r3))
    results["rules"]["R3-超标准报销"] = {
        "anomalies": len(r3),
        "record_ids": r3_ids,
        "breakdown": {}
    }
    # Group by sub-rule
    for a in r3:
        sub = a['rule']
        if sub not in results["rules"]["R3-超标准报销"]["breakdown"]:
            results["rules"]["R3-超标准报销"]["breakdown"][sub] = {"count": 0, "record_ids": []}
        results["rules"]["R3-超标准报销"]["breakdown"][sub]["count"] += 1
        results["rules"]["R3-超标准报销"]["breakdown"][sub]["record_ids"].append(a['record_id'])

    # R4
    r4 = rule4_over_budget(conn)
    r4_ids = [a['record_id'] for a in r4]
    results["rules"]["R4-超预算报销"] = {
        "anomaly_count": len(r4),
        "record_ids": r4_ids
    }

    # R5
    r5 = rule5_late_reimbursement(conn)
    r5_ids = [a['record_id'] for a in r5]
    results["rules"]["R5-超期报销"] = {
        "anomaly_count": len(r5),
        "record_ids": r5_ids
    }

    # All unique anomaly IDs
    all_ids = set()
    for rule_data in results["rules"].values():
        all_ids.update(rule_data.get("record_ids", []))
    results["total_anomaly_records"] = len(all_ids)
    results["all_anomaly_ids"] = sorted(list(all_ids))

    # Save detailed analysis
    with open("/workspace/work/analysis/data_findings.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Save detailed breakdowns
    with open("/workspace/work/analysis/r1_duplicates.json", "w") as f:
        json.dump(r1, f, ensure_ascii=False, indent=2)
    with open("/workspace/work/analysis/r2_splits.json", "w") as f:
        json.dump(r2_groups, f, ensure_ascii=False, indent=2)
    with open("/workspace/work/analysis/r3_over_standard.json", "w") as f:
        json.dump(r3, f, ensure_ascii=False, indent=2)
    with open("/workspace/work/analysis/r4_over_budget.json", "w") as f:
        json.dump(r4, f, ensure_ascii=False, indent=2)
    with open("/workspace/work/analysis/r5_late.json", "w") as f:
        json.dump(r5, f, ensure_ascii=False, indent=2)

    print(f"Total records: {total_records}")
    print(f"R1-重复报销: {len(r1)} groups, {len(set(r1_ids))} records")
    print(f"R2-拆分报销: {len(r2_groups)} groups, {len(r2_ids)} records")
    print(f"R3-超标准报销: {len(r3)} anomalies, {len(r3_ids)} records")
    print(f"R4-超预算报销: {len(r4)} anomalies, {len(r4_ids)} records")
    print(f"R5-超期报销: {len(r5)} anomalies, {len(r5_ids)} records")
    print(f"Total unique anomaly records: {len(all_ids)}")

    conn.close()

if __name__ == "__main__":
    main()
