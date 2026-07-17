#!/usr/bin/env python3
"""
Comprehensive 13-rule audit analysis against full 2025 expense data.
FIXED: city_tier mapping A/B/C -> 一类/二类/三类, per-night/per-day checks.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = "/benchmark/data/expense.db"
OUT_DIR = "/workspace/work/subagents/data_analyst"

def connect():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def load_all(conn):
    sql = """
    SELECT 
        r.record_id, r.record_no, r.employee_id, r.department_id,
        r.expense_date, r.reimburse_date, r.expense_type, r.amount,
        r.reason, r.invoice_id, r.status, r.city_tier, r.nights, r.days,
        r.participants, r.budget_year, r.special_approval,
        e.employee_name, e.employee_level, e.position_role, e.hire_date,
        i.invoice_no, i.vendor_name, i.invoice_date AS inv_invoice_date
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    JOIN invoices i ON r.invoice_id = i.invoice_id
    WHERE r.budget_year = 2025
    ORDER BY r.record_id
    """
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]

def load_departments(conn):
    rows = conn.execute("SELECT * FROM departments").fetchall()
    return {r['department_id']: dict(r) for r in rows}

# ===================================================================
# Mappings
# ===================================================================

# City tier: A=一类, B=二类, C=三类
TIER_MAP = {'A': '一类', 'B': '二类', 'C': '三类'}
LEVEL_TO_CATEGORY = {'E1': 'employee', 'M1': 'manager', 'D1': 'dept_head', 'X1': 'executive'}

# Travel lodging (04 Art.4): per night per person
TRAVEL_LODGING = {
    'employee':  {'一类': 450, '二类': 380, '三类': 300},
    'manager':   {'一类': 650, '二类': 550, '三类': 450},
    'dept_head': {'一类': 850, '二类': 700, '三类': 600},
    'executive': {'一类': 1100, '二类': 900, '三类': 750},
}

# Local transport (04 Art.6): per day
LOCAL_TRANSPORT = {'一类': 120, '二类': 100, '三类': 80}

# Training standards
TRAINING_FEE_THRESHOLD = 3500       # 05 Art.2: per person per session
TRAINING_DAILY_INTERNAL = 800       # 05 Art.3: internal daily
TRAINING_DAILY_EXTERNAL = 1200      # 05 Art.4: external daily
TRAINING_LODGING = {'一类': 500, '二类': 420, '三类': 350}  # 05 Art.5: per person per night

# Business entertainment (06 Art.2,3)
ENTERTAINMENT_PER_EVENT = 5000
ENTERTAINMENT_PER_PERSON = 300

# Office supplies (07 Art.2): per person per month
OFFICE_SUPPLIES_MONTHLY = 600

# Communication (07 Art.3): per person per month
COMMUNICATION_MONTHLY = 300

# ===================================================================
# Check helper: amount per night vs standard
# ===================================================================

def get_tier(tier_raw):
    """Map A/B/C to 一类/二类/三类. Return None if unknown."""
    return TIER_MAP.get(tier_raw)

def per_night_violation(amount, nights, tier, level_cat, standards):
    """Check if amount per night exceeds standard for level+tier."""
    if tier not in standards.get(level_cat, {}):
        return False
    std = standards[level_cat][tier]
    n = nights if nights and nights > 0 else 1
    return (amount / n) > std

# ===================================================================
# RULE FUNCTIONS
# ===================================================================

def check_r01_travel_lodging(records):
    """R01: travel_lodging per night > standard for level+tier. Exempt: special_approval."""
    violations = []
    for r in records:
        if r['expense_type'] != 'travel_lodging': continue
        if r['special_approval']: continue
        tier = get_tier(r.get('city_tier'))
        if not tier: continue
        cat = LEVEL_TO_CATEGORY.get(r['employee_level'], 'employee')
        std = TRAVEL_LODGING[cat][tier]
        nights = r.get('nights') or 1
        if (r['amount'] / nights) > std:
            violations.append(r['record_id'])
    return violations

def check_r02_local_transport(records):
    """R02: local_transport per day > standard for tier. Exempt: special_approval."""
    violations = []
    for r in records:
        if r['expense_type'] != 'local_transport': continue
        if r['special_approval']: continue
        tier = get_tier(r.get('city_tier'))
        if not tier: continue
        std = LOCAL_TRANSPORT[tier]
        days = r.get('days') or 1
        if (r['amount'] / days) > std:
            violations.append(r['record_id'])
    return violations

def check_r03_training_fee(records):
    """R03: training_fee per person > 3500. Exempt: special_approval."""
    violations = []
    for r in records:
        if r['expense_type'] != 'training_fee': continue
        if r['special_approval']: continue
        participants = r.get('participants') or 1
        per_person = r['amount'] / participants if participants > 0 else r['amount']
        if per_person > TRAINING_FEE_THRESHOLD:
            violations.append(r['record_id'])
    return violations

def check_r04_training_daily(records):
    """R04: training_fee per day > 800 (internal) or > 1200 (external). 
    Records with days field. Exempt: special_approval."""
    violations = []
    for r in records:
        if r['expense_type'] != 'training_fee': continue
        if r['special_approval']: continue
        days = r.get('days')
        if not days or days <= 0: continue
        daily = r['amount'] / days
        if daily > TRAINING_DAILY_INTERNAL:
            violations.append(r['record_id'])
    return violations

def check_r05_training_lodging(records):
    """R05: training_fee/training_lodging per person per night > standard. Exempt: special_approval."""
    violations = []
    for r in records:
        if r['expense_type'] not in ('training_lodging', 'training_fee'): continue
        if r['special_approval']: continue
        tier = get_tier(r.get('city_tier'))
        if not tier or tier not in TRAINING_LODGING: continue
        std = TRAINING_LODGING[tier]
        participants = r.get('participants') or 1
        nights = r.get('nights') or 1
        denom = participants * nights
        if denom <= 0: denom = 1
        if (r['amount'] / denom) > std:
            violations.append(r['record_id'])
    return violations

def check_r06_entertainment(records):
    """R06: business_entertainment > 5000/event or > 300/person. Exempt: special_approval."""
    violations = []
    for r in records:
        if r['expense_type'] != 'business_entertainment': continue
        if r['special_approval']: continue
        participants = r.get('participants') or 1
        per_person = r['amount'] / participants if participants > 0 else r['amount']
        if r['amount'] > ENTERTAINMENT_PER_EVENT or per_person > ENTERTAINMENT_PER_PERSON:
            violations.append(r['record_id'])
    return violations

def check_r07_office_supplies(records):
    """R07: office_supplies per person per month > 600. Exempt: special_approval records
    excluded from sum and from violations."""
    violations = []
    monthly = defaultdict(list)
    for r in records:
        if r['expense_type'] != 'office_supplies': continue
        year_month = r['expense_date'][:7]
        monthly[(r['employee_id'], year_month)].append(r)
    
    for key, recs in monthly.items():
        non_exempt = [r for r in recs if not r['special_approval']]
        total = sum(r['amount'] for r in non_exempt)
        if total > OFFICE_SUPPLIES_MONTHLY:
            for r in non_exempt:
                violations.append(r['record_id'])
    return violations

def check_r08_communication(records):
    """R08: communication per person per month > 300. Exempt: special_approval."""
    violations = []
    monthly = defaultdict(list)
    for r in records:
        if r['expense_type'] != 'communication': continue
        year_month = r['expense_date'][:7]
        monthly[(r['employee_id'], year_month)].append(r)
    
    for key, recs in monthly.items():
        non_exempt = [r for r in recs if not r['special_approval']]
        total = sum(r['amount'] for r in non_exempt)
        if total > COMMUNICATION_MONTHLY:
            for r in non_exempt:
                violations.append(r['record_id'])
    return violations

def check_r09_duplicate_invoices(records):
    """R09: same invoice_no in >= 2 records. No exemption."""
    invoice_groups = defaultdict(list)
    for r in records:
        invoice_groups[r['invoice_no']].append(r['record_id'])
    violations = []
    for inv_no, rec_ids in invoice_groups.items():
        if len(rec_ids) >= 2:
            violations.extend(rec_ids)
    return violations

def check_r10_split_claims(records):
    """R10: same employee + expense_type + within 7 days + >=2 records + total >= 10000."""
    groups = defaultdict(list)
    for r in records:
        groups[(r['employee_id'], r['expense_type'])].append(r)
    
    violations = set()
    for key, recs in groups.items():
        if len(recs) < 2: continue
        recs_sorted = sorted(recs, key=lambda x: x['expense_date'])
        n = len(recs_sorted)
        adj = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i+1, n):
                d1 = datetime.strptime(recs_sorted[i]['expense_date'], '%Y-%m-%d')
                d2 = datetime.strptime(recs_sorted[j]['expense_date'], '%Y-%m-%d')
                if (d2 - d1).days <= 7:
                    adj[i].append(j)
                    adj[j].append(i)
        
        visited = [False] * n
        for i in range(n):
            if visited[i]: continue
            stack = [i]
            component = []
            while stack:
                node = stack.pop()
                if visited[node]: continue
                visited[node] = True
                component.append(node)
                for neighbor in adj[node]:
                    if not visited[neighbor]:
                        stack.append(neighbor)
            if len(component) >= 2:
                total = sum(recs_sorted[idx]['amount'] for idx in component)
                if total >= 10000:
                    for idx in component:
                        violations.add(recs_sorted[idx]['record_id'])
    return sorted(violations)

def check_r11_late_submission(records):
    """R11: reimburse_date - expense_date > 60 days (75 if after Nov 1)."""
    violations = []
    nov1 = datetime(2025, 11, 1)
    for r in records:
        exp_date = datetime.strptime(r['expense_date'], '%Y-%m-%d')
        reim_date = datetime.strptime(r['reimburse_date'], '%Y-%m-%d')
        delay = (reim_date - exp_date).days
        threshold = 75 if exp_date >= nov1 else 60
        if delay > threshold:
            violations.append(r['record_id'])
    return violations

def check_r12_budget_exceeded(records, departments):
    """R12: department cumulative approved > annual budget.
    All approved records count toward cumulative.
    First record that exceeds and all subsequent are violations."""
    dept_records = defaultdict(list)
    for r in records:
        dept_records[r['department_id']].append(r)
    
    violations = []
    for dept_id, recs in dept_records.items():
        budget = departments.get(dept_id, {}).get('annual_budget', 0)
        if budget <= 0: continue
        recs_sorted = sorted(recs, key=lambda x: (x['expense_date'], x['record_id']))
        cumulative = 0
        exceeded = False
        for r in recs_sorted:
            if r['status'] != 'approved': continue
            cumulative += r['amount']
            if cumulative > budget:
                exceeded = True
                violations.append(r['record_id'])
    return violations

def check_r13_above_standard(records):
    """R13: Art.12 catch-all: amount > 1.0x standard. Exempt: special_approval."""
    violations = []
    for r in records:
        if r['special_approval']: continue
        etype = r['expense_type']
        exceeded = False
        
        if etype == 'travel_lodging':
            cat = LEVEL_TO_CATEGORY.get(r['employee_level'], 'employee')
            tier = get_tier(r.get('city_tier'))
            if tier:
                std = TRAVEL_LODGING[cat][tier]
                nights = r.get('nights') or 1
                if (r['amount'] / nights) > std:
                    exceeded = True
        
        elif etype == 'local_transport':
            tier = get_tier(r.get('city_tier'))
            if tier:
                std = LOCAL_TRANSPORT[tier]
                days = r.get('days') or 1
                if (r['amount'] / days) > std:
                    exceeded = True
        
        elif etype == 'training_fee':
            participants = r.get('participants') or 1
            per_person = r['amount'] / participants
            if per_person > TRAINING_FEE_THRESHOLD:
                exceeded = True
            days = r.get('days')
            if days and days > 0:
                if (r['amount'] / days) > TRAINING_DAILY_INTERNAL:
                    exceeded = True
            # Also check lodging for training_fee
            tier = get_tier(r.get('city_tier'))
            if tier and tier in TRAINING_LODGING:
                participants2 = r.get('participants') or 1
                nights = r.get('nights') or 1
                denom = participants2 * nights
                if denom > 0 and (r['amount'] / denom) > TRAINING_LODGING[tier]:
                    exceeded = True
        
        elif etype == 'training_lodging':
            tier = get_tier(r.get('city_tier'))
            if tier and tier in TRAINING_LODGING:
                participants = r.get('participants') or 1
                nights = r.get('nights') or 1
                denom = participants * nights
                if denom > 0 and (r['amount'] / denom) > TRAINING_LODGING[tier]:
                    exceeded = True
        
        elif etype == 'business_entertainment':
            participants = r.get('participants') or 1
            per_person = r['amount'] / participants
            if r['amount'] > ENTERTAINMENT_PER_EVENT or per_person > ENTERTAINMENT_PER_PERSON:
                exceeded = True
        
        elif etype == 'office_supplies':
            if r['amount'] > OFFICE_SUPPLIES_MONTHLY:
                exceeded = True
        
        elif etype == 'communication':
            if r['amount'] > COMMUNICATION_MONTHLY:
                exceeded = True
        
        if exceeded:
            violations.append(r['record_id'])
    return violations

# ===================================================================
# MAIN
# ===================================================================

def main():
    conn = connect()
    
    print("Loading all records...")
    records = load_all(conn)
    print(f"Total records: {len(records)}")
    
    departments = load_departments(conn)
    
    # Stats
    type_counts = defaultdict(int)
    for r in records: type_counts[r['expense_type']] += 1
    print("Expense types:", dict(type_counts))
    
    spec_approved = sum(1 for r in records if r['special_approval'])
    print(f"Records with special_approval=true: {spec_approved}")
    
    # Tier distribution
    tier_counts = defaultdict(int)
    for r in records:
        tier_counts[r.get('city_tier', 'None')] += 1
    print("City tier distribution:", dict(tier_counts))
    
    results = {}
    
    checks = [
        ('R01', 'travel_lodging above standard (per night)', check_r01_travel_lodging),
        ('R02', 'local_transport above standard (per day)', check_r02_local_transport),
        ('R03', 'training_fee per person > 3500', check_r03_training_fee),
        ('R04', 'training daily > 800', check_r04_training_daily),
        ('R05', 'training lodging above standard', check_r05_training_lodging),
        ('R06', 'entertainment >5000/event or >300/person', check_r06_entertainment),
        ('R07', 'office_supplies >600/person/month', check_r07_office_supplies),
        ('R08', 'communication >300/person/month', check_r08_communication),
        ('R09', 'duplicate invoices', check_r09_duplicate_invoices),
        ('R10', 'split claims', check_r10_split_claims),
        ('R11', 'late submission', check_r11_late_submission),
        ('R12', 'budget exceeded', lambda recs: check_r12_budget_exceeded(recs, departments)),
        ('R13', 'above standard (Art.12 catch-all)', check_r13_above_standard),
    ]
    
    for rule_id, desc, func in checks:
        print(f"\n=== {rule_id}: {desc} ===")
        vios = func(records)
        results[rule_id] = {'description': desc, 'violations': vios, 'count': len(vios)}
        print(f"  Violations: {len(vios)}")
        if vios and len(vios) <= 20:
            print(f"  IDs: {vios[:20]}")
    
    # Save
    with open(f"{OUT_DIR}/rule_analysis.json", 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    all_vios = set()
    for v in results.values():
        all_vios.update(v['violations'])
    
    summary = {
        'total_records': len(records),
        'total_special_approval': spec_approved,
        'expense_types': dict(type_counts),
        'rules': {k: v['count'] for k, v in results.items()},
        'total_unique_violations': len(all_vios),
        'all_violation_record_ids': sorted(list(all_vios)),
    }
    
    with open(f"{OUT_DIR}/summary.json", 'w') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== TOTAL UNIQUE VIOLATIONS: {len(all_vios)} ===")
    conn.close()

if __name__ == '__main__':
    main()
