#!/usr/bin/env python3
"""Process all audit rule analyses and compile results."""

import sqlite3
import json
from collections import defaultdict
from datetime import datetime, timedelta

DB_PATH = "/benchmark/data/expense.db"

def get_db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

# ========== RULE 1: Travel Lodging ==========
def check_rule1():
    """Travel lodging over-standard: employee_level x city_tier per night"""
    conn = get_db()
    standards = {
        'E1': {'A': 450, 'B': 380, 'C': 300},
        'M1': {'A': 650, 'B': 550, 'C': 450},
        'D1': {'A': 850, 'B': 700, 'C': 600},
        'X1': {'A': 1100, 'B': 900, 'C': 750},
    }
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, e.employee_level,
               r.city_tier, r.nights, r.amount, r.reason, r.special_approval
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='travel_lodging'
          AND r.nights IS NOT NULL AND r.city_tier IS NOT NULL
          AND (r.reason NOT LIKE '%培训%' AND r.reason NOT LIKE '%training%')
    """)

    violations = []
    for row in cur:
        std = standards.get(row['employee_level'], {}).get(row['city_tier'])
        if std is None:
            continue
        allowed = std * row['nights']
        if row['amount'] > allowed:
            violations.append({
                'record_id': row['record_id'],
                'record_no': row['record_no'],
                'employee_name': row['employee_name'],
                'employee_level': row['employee_level'],
                'city_tier': row['city_tier'],
                'nights': row['nights'],
                'amount': row['amount'],
                'standard_per_night': std,
                'total_allowed': allowed,
                'excess': round(row['amount'] - allowed, 2),
                'reason': row['reason'],
                'special_approval': row['special_approval'],
            })
    conn.close()
    return violations

# ========== RULE 2: Local Transport ==========
def check_rule2():
    """Local transport over-standard: city_tier x days"""
    conn = get_db()
    standards = {'A': 120, 'B': 100, 'C': 80}

    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.city_tier, r.days,
               r.amount, r.reason, r.special_approval
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='local_transport'
          AND r.days IS NOT NULL AND r.city_tier IS NOT NULL
    """)

    violations = []
    for row in cur:
        std = standards.get(row['city_tier'])
        if std is None:
            continue
        allowed = std * row['days']
        if row['amount'] > allowed:
            violations.append({
                'record_id': row['record_id'],
                'record_no': row['record_no'],
                'employee_name': row['employee_name'],
                'city_tier': row['city_tier'],
                'days': row['days'],
                'amount': row['amount'],
                'standard_per_day': std,
                'total_allowed': allowed,
                'excess': round(row['amount'] - allowed, 2),
                'reason': row['reason'],
                'special_approval': row['special_approval'],
            })
    conn.close()
    return violations

# ========== RULE 3a: Training Fee Course ==========
def check_rule3a():
    """Training fee course > 3500 per person per session"""
    conn = get_db()
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.reason, r.special_approval
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='training_fee'
          AND (r.reason NOT LIKE '%住宿%' AND r.reason NOT LIKE '%lodging%')
          AND r.amount > 3500
    """)
    violations = []
    for row in cur:
        violations.append({
            'record_id': row['record_id'],
            'record_no': row['record_no'],
            'employee_name': row['employee_name'],
            'amount': row['amount'],
            'standard': 3500,
            'excess': round(row['amount'] - 3500, 2),
            'reason': row['reason'],
            'special_approval': row['special_approval'],
        })
    conn.close()
    return violations

# ========== RULE 3b: Training Lodging (in travel_lodging type) ==========
def check_rule3b():
    """Training-related lodging in travel_lodging records, checked against training lodging standards"""
    conn = get_db()
    standards = {'A': 500, 'B': 420, 'C': 350}

    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.city_tier, r.nights,
               r.amount, r.reason, r.special_approval
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='travel_lodging'
          AND (r.reason LIKE '%培训%' OR r.reason LIKE '%training%')
          AND r.nights IS NOT NULL AND r.city_tier IS NOT NULL
    """)

    violations = []
    for row in cur:
        std = standards.get(row['city_tier'])
        if std is None:
            continue
        allowed = std * row['nights']
        if row['amount'] > allowed:
            violations.append({
                'record_id': row['record_id'],
                'record_no': row['record_no'],
                'employee_name': row['employee_name'],
                'city_tier': row['city_tier'],
                'nights': row['nights'],
                'amount': row['amount'],
                'standard_per_night': std,
                'total_allowed': allowed,
                'excess': round(row['amount'] - allowed, 2),
                'reason': row['reason'],
                'special_approval': row['special_approval'],
            })
    conn.close()
    return violations

# ========== RULE 4a: Business Entertainment single event > 5000 ==========
def check_rule4a():
    conn = get_db()
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.participants,
               r.reason, r.special_approval
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='business_entertainment'
          AND r.amount > 5000
    """)
    violations = []
    for row in cur:
        violations.append({
            'record_id': row['record_id'],
            'record_no': row['record_no'],
            'employee_name': row['employee_name'],
            'amount': row['amount'],
            'standard': 5000,
            'excess': round(row['amount'] - 5000, 2),
            'participants': row['participants'],
            'reason': row['reason'],
            'special_approval': row['special_approval'],
        })
    conn.close()
    return violations

# ========== RULE 4b: Business Entertainment per person > 300 ==========
def check_rule4b():
    conn = get_db()
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.participants,
               r.reason, r.special_approval
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='business_entertainment'
          AND r.participants IS NOT NULL AND r.participants > 0
          AND r.amount / r.participants > 300
    """)
    violations = []
    for row in cur:
        per_person = round(row['amount'] / row['participants'], 2)
        violations.append({
            'record_id': row['record_id'],
            'record_no': row['record_no'],
            'employee_name': row['employee_name'],
            'amount': row['amount'],
            'participants': row['participants'],
            'per_person': per_person,
            'standard_per_person': 300,
            'excess_per_person': round(per_person - 300, 2),
            'reason': row['reason'],
            'special_approval': row['special_approval'],
        })
    conn.close()
    return violations

# ========== RULE 5: Office Supplies monthly cap ==========
def check_rule5():
    """Office supplies: per person per month <= 600, with invoice dedup"""
    conn = get_db()

    # First get dedup'd expenses (unique invoice per employee)
    cur = conn.execute("""
        SELECT employee_id, expense_date, invoice_id, MAX(amount) AS amount, MAX(record_id) AS record_id
        FROM expense_records
        WHERE budget_year=2025 AND expense_type='office_supplies'
        GROUP BY employee_id, invoice_id
    """)

    # Group by employee + month
    monthly = defaultdict(lambda: {'total': 0.0, 'record_ids': []})
    for row in cur:
        month = row['expense_date'][:7]  # YYYY-MM
        key = (row['employee_id'], month)
        monthly[key]['total'] += row['amount']
        monthly[key]['record_ids'].append(row['record_id'])

    # Get employee names
    cur2 = conn.execute("SELECT employee_id, employee_name FROM employees")
    emp_names = {row['employee_id']: row['employee_name'] for row in cur2}

    violations = []
    for (emp_id, month), data in sorted(monthly.items()):
        if data['total'] > 600:
            violations.append({
                'employee_id': emp_id,
                'employee_name': emp_names.get(emp_id, 'Unknown'),
                'month': month,
                'total_amount': round(data['total'], 2),
                'standard': 600,
                'excess': round(data['total'] - 600, 2),
                'record_ids': sorted(data['record_ids']),
                'record_count': len(data['record_ids']),
            })

    conn.close()
    return sorted(violations, key=lambda x: x['total_amount'], reverse=True)

# ========== RULE 6: Communication monthly cap ==========
def check_rule6():
    """Communication: per person per month <= 300, with invoice dedup"""
    conn = get_db()

    cur = conn.execute("""
        SELECT employee_id, expense_date, invoice_id, MAX(amount) AS amount, MAX(record_id) AS record_id
        FROM expense_records
        WHERE budget_year=2025 AND expense_type='communication'
        GROUP BY employee_id, invoice_id
    """)

    monthly = defaultdict(lambda: {'total': 0.0, 'record_ids': []})
    for row in cur:
        month = row['expense_date'][:7]
        key = (row['employee_id'], month)
        monthly[key]['total'] += row['amount']
        monthly[key]['record_ids'].append(row['record_id'])

    cur2 = conn.execute("SELECT employee_id, employee_name FROM employees")
    emp_names = {row['employee_id']: row['employee_name'] for row in cur2}

    violations = []
    for (emp_id, month), data in sorted(monthly.items()):
        if data['total'] > 300:
            violations.append({
                'employee_id': emp_id,
                'employee_name': emp_names.get(emp_id, 'Unknown'),
                'month': month,
                'total_amount': round(data['total'], 2),
                'standard': 300,
                'excess': round(data['total'] - 300, 2),
                'record_ids': sorted(data['record_ids']),
                'record_count': len(data['record_ids']),
            })

    conn.close()
    return sorted(violations, key=lambda x: x['total_amount'], reverse=True)

# ========== RULE 7: Duplicate Invoices ==========
def check_rule7():
    conn = get_db()
    cur = conn.execute("""
        SELECT i.invoice_no, COUNT(*) as cnt, GROUP_CONCAT(r.record_id) as record_ids
        FROM expense_records r
        JOIN invoices i ON r.invoice_id = i.invoice_id
        WHERE r.budget_year=2025
        GROUP BY i.invoice_no
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
    """)
    violations = []
    for row in cur:
        record_ids = row['record_ids'].split(',')
        violations.append({
            'invoice_no': row['invoice_no'],
            'count': row['cnt'],
            'record_ids': sorted(record_ids),
        })
    conn.close()
    return violations

# ========== RULE 8: Split Billing ==========
def check_rule8():
    """Split billing: same employee, same expense_type, within 7 days, >=2 records, sum >=3000"""
    conn = get_db()

    cur = conn.execute("""
        SELECT r.record_id, r.record_no, r.employee_id, e.employee_name, r.expense_type,
               r.expense_date, r.amount, r.reason
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025
        ORDER BY r.employee_id, r.expense_type, r.expense_date
    """)

    records = [dict(row) for row in cur]
    conn.close()

    # Group by (employee_id, expense_type)
    groups = defaultdict(list)
    for rec in records:
        groups[(rec['employee_id'], rec['expense_type'])].append(rec)

    # For each group, find connected components (within 7 days)
    split_groups = []

    for (emp_id, exp_type), recs in groups.items():
        if len(recs) < 2:
            continue

        # Build adjacency: records within 7 days of each other
        recs_sorted = sorted(recs, key=lambda r: r['expense_date'])
        n = len(recs_sorted)

        # Use Union-Find to find connected components
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for i in range(n):
            for j in range(i+1, n):
                d1 = datetime.strptime(recs_sorted[i]['expense_date'], '%Y-%m-%d')
                d2 = datetime.strptime(recs_sorted[j]['expense_date'], '%Y-%m-%d')
                if (d2 - d1).days <= 7:
                    union(i, j)

        # Collect components
        components = defaultdict(list)
        for i in range(n):
            root = find(i)
            components[root].append(recs_sorted[i])

        for comp_recs in components.values():
            if len(comp_recs) >= 2:
                total = sum(r['amount'] for r in comp_recs)
                if total >= 3000:
                    split_groups.append({
                        'employee_id': emp_id,
                        'employee_name': comp_recs[0]['employee_name'],
                        'expense_type': exp_type,
                        'record_count': len(comp_recs),
                        'total_amount': round(total, 2),
                        'date_range': f"{comp_recs[0]['expense_date']} to {comp_recs[-1]['expense_date']}",
                        'date_span_days': (datetime.strptime(comp_recs[-1]['expense_date'], '%Y-%m-%d') -
                                          datetime.strptime(comp_recs[0]['expense_date'], '%Y-%m-%d')).days,
                        'records': [{
                            'record_id': r['record_id'],
                            'record_no': r['record_no'],
                            'expense_date': r['expense_date'],
                            'amount': r['amount'],
                            'reason': r['reason'],
                        } for r in comp_recs],
                    })

    return split_groups

# ========== RULE 9: Department Budget ==========
def check_rule9():
    """Department budget exceedance: first record that causes running total > budget"""
    conn = get_db()

    cur = conn.execute("""
        WITH dedup_expenses AS (
          SELECT department_id, expense_date, invoice_id, MAX(amount) AS amount, MAX(record_id) AS record_id
          FROM expense_records
          WHERE budget_year=2025
          GROUP BY department_id, invoice_id
        ),
        ranked AS (
          SELECT de.department_id, de.record_id, de.expense_date, de.amount,
                 d.annual_budget, d.department_name,
                 SUM(de.amount) OVER (PARTITION BY de.department_id ORDER BY de.expense_date, de.record_id) AS running_total,
                 SUM(de.amount) OVER (PARTITION BY de.department_id ORDER BY de.expense_date, de.record_id) - de.amount AS prev_total
          FROM dedup_expenses de
          JOIN departments d ON de.department_id = d.department_id
          JOIN expense_records r ON de.record_id = r.record_id
        )
        SELECT department_id, department_name, record_id, expense_date, amount, annual_budget, running_total
        FROM ranked
        WHERE prev_total <= annual_budget AND running_total > annual_budget
        ORDER BY department_id
    """)

    crossing_records = [dict(row) for row in cur]

    # Get employee details for crossing records
    violations = []
    for cr in crossing_records:
        cur2 = conn.execute("""
            SELECT r.record_id, r.record_no, e.employee_name, r.expense_type, r.amount, r.expense_date, r.special_approval
            FROM expense_records r
            JOIN employees e ON r.employee_id = e.employee_id
            WHERE r.record_id = ?
        """, (cr['record_id'],))
        detail = dict(cur2.fetchone())
        violations.append({
            'department_id': cr['department_id'],
            'department_name': cr['department_name'],
            'annual_budget': cr['annual_budget'],
            'running_total_at_crossing': cr['running_total'],
            'crossing_record_id': cr['record_id'],
            'crossing_record_no': detail['record_no'],
            'employee_name': detail['employee_name'],
            'expense_type': detail['expense_type'],
            'amount': cr['amount'],
            'expense_date': cr['expense_date'],
            'special_approval': detail['special_approval'],
        })

    conn.close()
    return violations

# ========== RULE 10: General Standard Exceedance ==========
def check_rule10():
    """Cannot exceed 1.0x standard without special approval"""
    conn = get_db()
    violations = []

    # Travel lodging
    standards_tl = {
        'E1': {'A': 450, 'B': 380, 'C': 300},
        'M1': {'A': 650, 'B': 550, 'C': 450},
        'D1': {'A': 850, 'B': 700, 'C': 600},
        'X1': {'A': 1100, 'B': 900, 'C': 750},
    }
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, e.employee_level, r.city_tier, r.nights, r.amount, r.special_approval, r.reason
        FROM expense_records r
        JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='travel_lodging' AND r.special_approval=0
          AND r.nights IS NOT NULL AND r.city_tier IS NOT NULL
          AND (r.reason NOT LIKE '%培训%' AND r.reason NOT LIKE '%training%')
    """)
    for row in cur:
        std = standards_tl.get(row['employee_level'], {}).get(row['city_tier'])
        if std and row['amount'] > std * row['nights']:
            violations.append({
                'record_id': row['record_id'], 'record_no': row['record_no'],
                'employee_name': row['employee_name'], 'expense_type': 'travel_lodging',
                'amount': row['amount'], 'standard_desc': f'{std}/night × {row["nights"]} nights = {std * row["nights"]}',
                'reason': row['reason'],
            })

    # Local transport
    standards_lt = {'A': 120, 'B': 100, 'C': 80}
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.city_tier, r.days, r.amount, r.special_approval, r.reason
        FROM expense_records r JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='local_transport' AND r.special_approval=0
          AND r.days IS NOT NULL AND r.city_tier IS NOT NULL
    """)
    for row in cur:
        std = standards_lt.get(row['city_tier'])
        if std and row['amount'] > std * row['days']:
            violations.append({
                'record_id': row['record_id'], 'record_no': row['record_no'],
                'employee_name': row['employee_name'], 'expense_type': 'local_transport',
                'amount': row['amount'], 'standard_desc': f'{std}/day × {row["days"]} days = {std * row["days"]}',
                'reason': row['reason'],
            })

    # Training fee course
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.special_approval, r.reason
        FROM expense_records r JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='training_fee' AND r.special_approval=0
          AND (r.reason NOT LIKE '%住宿%' AND r.reason NOT LIKE '%lodging%')
          AND r.amount > 3500
    """)
    for row in cur:
        violations.append({
            'record_id': row['record_id'], 'record_no': row['record_no'],
            'employee_name': row['employee_name'], 'expense_type': 'training_fee',
            'amount': row['amount'], 'standard_desc': '3500 per session',
            'reason': row['reason'],
        })

    # Business entertainment single event
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.special_approval, r.reason
        FROM expense_records r JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='business_entertainment' AND r.special_approval=0
          AND r.amount > 5000
    """)
    for row in cur:
        violations.append({
            'record_id': row['record_id'], 'record_no': row['record_no'],
            'employee_name': row['employee_name'], 'expense_type': 'business_entertainment',
            'amount': row['amount'], 'standard_desc': '5000 per event',
            'reason': row['reason'],
        })

    # Business entertainment per person
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.participants, r.special_approval, r.reason
        FROM expense_records r JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='business_entertainment' AND r.special_approval=0
          AND r.participants IS NOT NULL AND r.participants > 0
          AND r.amount / r.participants > 300
    """)
    for row in cur:
        violations.append({
            'record_id': row['record_id'], 'record_no': row['record_no'],
            'employee_name': row['employee_name'], 'expense_type': 'business_entertainment',
            'amount': row['amount'], 'participants': row['participants'],
            'per_person': round(row['amount']/row['participants'], 2),
            'standard_desc': '300 per person',
            'reason': row['reason'],
        })

    # Office supplies per record > 600
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.special_approval, r.reason
        FROM expense_records r JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='office_supplies' AND r.special_approval=0
          AND r.amount > 600
    """)
    for row in cur:
        violations.append({
            'record_id': row['record_id'], 'record_no': row['record_no'],
            'employee_name': row['employee_name'], 'expense_type': 'office_supplies',
            'amount': row['amount'], 'standard_desc': '600 per record (monthly cap)',
            'reason': row['reason'],
        })

    # Communication per record > 300
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.amount, r.special_approval, r.reason
        FROM expense_records r JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='communication' AND r.special_approval=0
          AND r.amount > 300
    """)
    for row in cur:
        violations.append({
            'record_id': row['record_id'], 'record_no': row['record_no'],
            'employee_name': row['employee_name'], 'expense_type': 'communication',
            'amount': row['amount'], 'standard_desc': '300 per record (monthly cap)',
            'reason': row['reason'],
        })

    # Training-related lodging in travel_lodging
    standards_tr = {'A': 500, 'B': 420, 'C': 350}
    cur = conn.execute("""
        SELECT r.record_id, r.record_no, e.employee_name, r.city_tier, r.nights, r.amount, r.special_approval, r.reason
        FROM expense_records r JOIN employees e ON r.employee_id = e.employee_id
        WHERE r.budget_year=2025 AND r.expense_type='travel_lodging' AND r.special_approval=0
          AND (r.reason LIKE '%培训%' OR r.reason LIKE '%training%')
          AND r.nights IS NOT NULL AND r.city_tier IS NOT NULL
    """)
    for row in cur:
        std = standards_tr.get(row['city_tier'])
        if std and row['amount'] > std * row['nights']:
            violations.append({
                'record_id': row['record_id'], 'record_no': row['record_no'],
                'employee_name': row['employee_name'], 'expense_type': 'travel_lodging (training)',
                'amount': row['amount'], 'standard_desc': f'{std}/night (training) × {row["nights"]} nights = {std * row["nights"]}',
                'reason': row['reason'],
            })

    conn.close()
    return violations


# ========== MAIN ==========
if __name__ == '__main__':
    results = {}

    print("Checking Rule 1: Travel Lodging...")
    results['rule1_travel_lodging'] = check_rule1()
    print(f"  Found {len(results['rule1_travel_lodging'])} violations")

    print("Checking Rule 2: Local Transport...")
    results['rule2_local_transport'] = check_rule2()
    print(f"  Found {len(results['rule2_local_transport'])} violations")

    print("Checking Rule 3a: Training Fee Course...")
    results['rule3a_training_fee_course'] = check_rule3a()
    print(f"  Found {len(results['rule3a_training_fee_course'])} violations")

    print("Checking Rule 3b: Training Lodging (in travel_lodging)...")
    results['rule3b_training_lodging'] = check_rule3b()
    print(f"  Found {len(results['rule3b_training_lodging'])} violations")

    print("Checking Rule 4a: Business Entertainment single event...")
    results['rule4a_entertainment_event'] = check_rule4a()
    print(f"  Found {len(results['rule4a_entertainment_event'])} violations")

    print("Checking Rule 4b: Business Entertainment per person...")
    results['rule4b_entertainment_per_person'] = check_rule4b()
    print(f"  Found {len(results['rule4b_entertainment_per_person'])} violations")

    print("Checking Rule 5: Office Supplies monthly cap...")
    results['rule5_office_supplies'] = check_rule5()
    print(f"  Found {len(results['rule5_office_supplies'])} violation groups")

    print("Checking Rule 6: Communication monthly cap...")
    results['rule6_communication'] = check_rule6()
    print(f"  Found {len(results['rule6_communication'])} violation groups")

    print("Checking Rule 7: Duplicate Invoices...")
    results['rule7_duplicate_invoices'] = check_rule7()
    print(f"  Found {len(results['rule7_duplicate_invoices'])} duplicate groups")

    print("Checking Rule 8: Split Billing...")
    results['rule8_split_billing'] = check_rule8()
    print(f"  Found {len(results['rule8_split_billing'])} split groups")

    print("Checking Rule 9: Department Budget...")
    results['rule9_budget_exceedance'] = check_rule9()
    print(f"  Found {len(results['rule9_budget_exceedance'])} crossing records")

    print("Checking Rule 10: General Standard Exceedance...")
    results['rule10_general_standard'] = check_rule10()
    print(f"  Found {len(results['rule10_general_standard'])} violations")

    # Save results
    with open('/workspace/work/subagents/data_analyst/analysis_detail.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nSaved detailed analysis to work/subagents/data_analyst/analysis_detail.json")

    # Print summaries
    for rule_name, violations in results.items():
        print(f"\n=== {rule_name} ===")
        if isinstance(violations, list):
            for v in violations[:5]:
                print(json.dumps(v, ensure_ascii=False, indent=2))
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
