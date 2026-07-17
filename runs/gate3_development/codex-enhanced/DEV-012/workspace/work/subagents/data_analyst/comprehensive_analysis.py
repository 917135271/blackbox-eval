#!/usr/bin/env python3
"""
DEV-012: Comprehensive 5-rule analysis of 21 reimbursement records
Data Analyst subagent — batch expense analysis
"""

import json
from datetime import date, timedelta

# ============================================================
# DATA — All 21 records from MCP list_expenses
# ============================================================
records = [
    {"record_id":"R900001","employee_id":"E9001","dept_id":"D901","expense_date":"2025-01-05","reimburse_date":"2025-01-12","expense_type":"office_supplies","amount":480,"invoice_no":"FPDEV900001","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900002","employee_id":"E9001","dept_id":"D901","expense_date":"2025-01-06","reimburse_date":"2025-01-13","expense_type":"office_supplies","amount":480,"invoice_no":"FPDEV900001","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900018","employee_id":"E9003","dept_id":"D902","expense_date":"2025-01-15","reimburse_date":"2025-01-20","expense_type":"other","amount":45000,"invoice_no":"FPDEV900018","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900003","employee_id":"E9001","dept_id":"D901","expense_date":"2025-02-03","reimburse_date":"2025-02-08","expense_type":"travel_transport","amount":5200,"invoice_no":"FPDEV900003","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900004","employee_id":"E9001","dept_id":"D901","expense_date":"2025-02-06","reimburse_date":"2025-02-10","expense_type":"travel_transport","amount":5200,"invoice_no":"FPDEV900004","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900019","employee_id":"E9003","dept_id":"D902","expense_date":"2025-02-15","reimburse_date":"2025-02-20","expense_type":"other","amount":6000,"invoice_no":"FPDEV900019","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900006","employee_id":"E9001","dept_id":"D901","expense_date":"2025-03-01","reimburse_date":"2025-05-05","expense_type":"communication","amount":200,"invoice_no":"FPDEV900006","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900005","employee_id":"E9001","dept_id":"D901","expense_date":"2025-03-12","reimburse_date":"2025-03-20","expense_type":"business_entertainment","amount":3600,"invoice_no":"FPDEV900005","status":"approved","city_tier":None,"nights":None,"days":None,"participants":10,"special_approval":0},
    {"record_id":"R900020","employee_id":"E9003","dept_id":"D902","expense_date":"2025-03-15","reimburse_date":"2025-03-20","expense_type":"other","amount":5000,"invoice_no":"FPDEV900020","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":1},
    {"record_id":"R900007","employee_id":"E9001","dept_id":"D901","expense_date":"2025-04-08","reimburse_date":"2025-04-12","expense_type":"office_supplies","amount":650,"invoice_no":"FPDEV900007","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900008","employee_id":"E9001","dept_id":"D901","expense_date":"2025-05-05","reimburse_date":"2025-05-10","expense_type":"office_supplies","amount":590,"invoice_no":"FPDEV900008","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900009","employee_id":"E9002","dept_id":"D901","expense_date":"2025-05-05","reimburse_date":"2025-05-10","expense_type":"office_supplies","amount":590,"invoice_no":"FPDEV900009","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900010","employee_id":"E9001","dept_id":"D901","expense_date":"2025-06-01","reimburse_date":"2025-06-05","expense_type":"travel_transport","amount":5300,"invoice_no":"FPDEV900010","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900011","employee_id":"E9001","dept_id":"D901","expense_date":"2025-06-09","reimburse_date":"2025-06-13","expense_type":"travel_transport","amount":5300,"invoice_no":"FPDEV900011","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900013","employee_id":"E9002","dept_id":"D901","expense_date":"2025-07-10","reimburse_date":"2025-07-15","expense_type":"travel_lodging","amount":1400,"invoice_no":"FPDEV900013","status":"approved","city_tier":"A","nights":2,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900016","employee_id":"E9001","dept_id":"D901","expense_date":"2025-08-02","reimburse_date":"2025-08-08","expense_type":"training_fee","amount":850,"invoice_no":"FPDEV900016","status":"approved","city_tier":None,"nights":None,"days":1,"participants":None,"special_approval":0},
    {"record_id":"R900014","employee_id":"E9001","dept_id":"D901","expense_date":"2025-09-03","reimburse_date":"2025-09-06","expense_type":"communication","amount":180,"invoice_no":"FPDEV900014","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900015","employee_id":"E9001","dept_id":"D901","expense_date":"2025-09-20","reimburse_date":"2025-09-23","expense_type":"communication","amount":160,"invoice_no":"FPDEV900015","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900017","employee_id":"E9001","dept_id":"D901","expense_date":"2025-10-06","reimburse_date":"2025-10-12","expense_type":"business_entertainment","amount":5200,"invoice_no":"FPDEV900017","status":"approved","city_tier":None,"nights":None,"days":None,"participants":20,"special_approval":0},
    {"record_id":"R900021","employee_id":"E9001","dept_id":"D901","expense_date":"2025-12-02","reimburse_date":"2025-12-08","expense_type":"training_lodging","amount":480,"invoice_no":"FPDEV900021","status":"approved","city_tier":"A","nights":1,"days":None,"participants":None,"special_approval":0},
    {"record_id":"R900012","employee_id":"E9001","dept_id":"D901","expense_date":"2025-12-20","reimburse_date":"2026-01-10","expense_type":"other","amount":900,"invoice_no":"FPDEV900012","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0},
]

# Employee data
employees = {
    "E9001": {"level": "员工级", "dept": "D901", "name": "开发员工甲"},
    "E9002": {"level": "经理级", "dept": "D901", "name": "开发经理乙"},
    "E9003": {"level": "员工级", "dept": "D902", "name": "开发员工丙"},
    "E9004": {"level": "部门负责人级", "dept": "D902", "name": "开发经理丁"},
}

# Department budgets
budgets = {"D901": 200000, "D902": 50000}

# Policy standards
POLICY = {
    "office_supplies_monthly": 600,        # 07_office_communication Article 2
    "communication_monthly": 300,          # 07_office_communication Article 3
    "training_fee_daily_internal": 800,    # 05_training_expense Article 3
    "training_lodging_tier": {"A": 500},   # 05_training_expense Article 5
    "travel_lodging": {
        "经理级": {"A": 650},
        "员工级": {"A": 450},
    },                                      # 04_travel_expense Article 4
    "entertainment_per_event": 5000,        # 06_business_entertainment Article 2
    "entertainment_per_person": 300,        # 06_business_entertainment Article 3
    "overdue_days": 60,                     # 01_expense_reimbursement Article 7
    "yearend_deadline": date(2026, 1, 15),  # Article 9
    "split_days": 7,                        # Article 11
    "split_threshold": 10000,               # AR-03
}

# Parse dates
def parse_date(s):
    return date.fromisoformat(s)

for r in records:
    r["_ed"] = parse_date(r["expense_date"])
    r["_rd"] = parse_date(r["reimburse_date"])
    r["_month"] = (r["_ed"].year, r["_ed"].month)

# ============================================================
# 1. DUPLICATE — Article 10: same invoice used ≥2 records
# ============================================================
print("=" * 60)
print("1. DUPLICATE (重复报销) — Article 10")
print("=" * 60)

from collections import defaultdict
invoice_map = defaultdict(list)
for r in records:
    invoice_map[r["invoice_no"]].append(r)

duplicate_records = []
for inv, recs in invoice_map.items():
    if len(recs) >= 2:
        print(f"  INVOICE {inv}: {len(recs)} records → DUPLICATE")
        for rr in recs:
            print(f"    {rr['record_id']}: {rr['employee_id']} {rr['expense_type']} {rr['amount']}元")
            duplicate_records.append(rr["record_id"])

print(f"  → Duplicate records: {duplicate_records}")

# ============================================================
# 2. SPLIT — Article 11: same employee, same type, ≤7 days, combined ≥ AR-03 (10000)
# ============================================================
print("\n" + "=" * 60)
print("2. SPLIT (拆分报销) — Article 11 + AR-03 (≥10000元)")
print("=" * 60)

# Group by (employee, expense_type)
from itertools import groupby

split_key = lambda r: (r["employee_id"], r["expense_type"])
recs_sorted = sorted(records, key=lambda r: (split_key(r), r["_ed"]))

split_results = []
for (emp, etype), group in groupby(recs_sorted, key=split_key):
    grp = list(group)
    if len(grp) < 2:
        continue
    # Sliding window: check adjacent within 7 days
    for i in range(len(grp)):
        window = [grp[i]]
        for j in range(i+1, len(grp)):
            if (grp[j]["_ed"] - grp[i]["_ed"]).days <= POLICY["split_days"]:
                window.append(grp[j])
            else:
                break
        if len(window) >= 2:
            combined = sum(r["amount"] for r in window)
            if combined >= POLICY["split_threshold"]:
                ids = [r["record_id"] for r in window]
                print(f"  SPLIT: {emp} {etype}: {ids}")
                print(f"    Dates: {[r['expense_date'] for r in window]}")
                print(f"    Combined: {combined}元 ≥ {POLICY['split_threshold']}元 (AR-03)")
                split_results.extend(ids)

print(f"  → Split records: {list(set(split_results))}")

# ============================================================
# 3. OVER-STANDARD
# ============================================================
print("\n" + "=" * 60)
print("3. OVER-STANDARD (超标准)")
print("=" * 60)

over_standard = []

# 3a. office_supplies > 600/month per person
print("\n3a. office_supplies monthly cap (600元/person/month)")
office_by_month = defaultdict(list)
for r in records:
    if r["expense_type"] == "office_supplies":
        key = (r["employee_id"], r["_month"])
        office_by_month[key].append(r)

os_records = []
for (emp, month), recs in office_by_month.items():
    total = sum(r["amount"] for r in recs)
    status = "OVER" if total > POLICY["office_supplies_monthly"] else "OK"
    print(f"  {emp} {month[0]}-{month[1]:02d}: {total}元 {'>' if total > POLICY['office_supplies_monthly'] else '≤'} {POLICY['office_supplies_monthly']} → {status}")
    if total > POLICY["office_supplies_monthly"]:
        for r in recs:
            os_records.append(r["record_id"])
            over_standard.append(r["record_id"])

print(f"  → Over-standard office_supplies: {list(set(os_records))}")

# 3b. communication > 300/month per person
print("\n3b. communication monthly cap (300元/person/month)")
comm_by_month = defaultdict(list)
for r in records:
    if r["expense_type"] == "communication":
        key = (r["employee_id"], r["_month"])
        comm_by_month[key].append(r)

comm_records = []
for (emp, month), recs in comm_by_month.items():
    total = sum(r["amount"] for r in recs)
    status = "OVER" if total > POLICY["communication_monthly"] else "OK"
    print(f"  {emp} {month[0]}-{month[1]:02d}: {total}元 {'>' if total > POLICY['communication_monthly'] else '≤'} {POLICY['communication_monthly']} → {status}")
    if total > POLICY["communication_monthly"]:
        for r in recs:
            comm_records.append(r["record_id"])
            over_standard.append(r["record_id"])

print(f"  → Over-standard communication: {list(set(comm_records))}")

# 3c. travel_lodging
print("\n3c. travel_lodging (per night standard)")
for r in records:
    if r["expense_type"] == "travel_lodging" and r["city_tier"] and r["nights"]:
        emp_level = employees[r["employee_id"]]["level"]
        std = POLICY["travel_lodging"].get(emp_level, {}).get(r["city_tier"])
        if std:
            per_night = r["amount"] / r["nights"]
            status = "OVER" if per_night > std else "OK"
            print(f"  {r['record_id']}: {emp_level} city_tier={r['city_tier']} {r['nights']}晚 {r['amount']}元 ({per_night:.0f}元/晚), std={std}元/晚 → {status}")
            if per_night > std:
                over_standard.append(r["record_id"])

# 3d. training_fee
print("\n3d. training_fee (internal ≤800元/day)")
for r in records:
    if r["expense_type"] == "training_fee" and r["days"]:
        per_day = r["amount"] / r["days"]
        status = "OVER" if per_day > POLICY["training_fee_daily_internal"] else "OK"
        print(f"  {r['record_id']}: {r['amount']}元 / {r['days']}天 = {per_day:.0f}元/天, std={POLICY['training_fee_daily_internal']} → {status}")
        if per_day > POLICY["training_fee_daily_internal"]:
            over_standard.append(r["record_id"])

# 3e. business_entertainment
print("\n3e. business_entertainment (≤5000/event AND ≤300/person)")
for r in records:
    if r["expense_type"] == "business_entertainment" and r["participants"]:
        event_ok = r["amount"] <= POLICY["entertainment_per_event"]
        per_person = r["amount"] / r["participants"]
        person_ok = per_person <= POLICY["entertainment_per_person"]
        issues = []
        if not event_ok:
            issues.append(f"event: {r['amount']} > {POLICY['entertainment_per_event']}")
        if not person_ok:
            issues.append(f"per_person: {per_person:.0f} > {POLICY['entertainment_per_person']}")
        status = "OVER" if issues else "OK"
        print(f"  {r['record_id']}: {r['amount']}元, {r['participants']}人 ({per_person:.0f}元/人) → {status} {' | '.join(issues)}")
        if issues:
            over_standard.append(r["record_id"])

# 3f. training_lodging
print("\n3f. training_lodging (一类城市 500元/晚)")
for r in records:
    if r["expense_type"] == "training_lodging" and r["city_tier"] and r["nights"]:
        std = POLICY["training_lodging_tier"].get(r["city_tier"])
        if std:
            per_night = r["amount"] / r["nights"]
            status = "OVER" if per_night > std else "OK"
            print(f"  {r['record_id']}: city_tier={r['city_tier']} {r['nights']}晚 {r['amount']}元 ({per_night:.0f}元/晚), std={std} → {status}")
            if per_night > std:
                over_standard.append(r["record_id"])

over_standard = list(set(over_standard))
print(f"\n  → All over-standard records: {sorted(over_standard)}")

# ============================================================
# 4. OVERDUE — Articles 7, 9
# ============================================================
print("\n" + "=" * 60)
print("4. OVERDUE (超期) — Articles 7 (60 days), 9 (year-end ≤ Jan 15)")
print("=" * 60)

overdue_records = []
for r in records:
    delay = (r["_rd"] - r["_ed"]).days
    is_december = r["_ed"].month == 12
    if is_december and r["_rd"] <= POLICY["yearend_deadline"]:
        print(f"  {r['record_id']}: {delay}d (Dec expense, deadline met: {r['_rd']} ≤ {POLICY['yearend_deadline']}) → OK (year-end)")
        continue
    if delay > POLICY["overdue_days"]:
        print(f"  {r['record_id']}: {delay}d > {POLICY['overdue_days']}d → OVERDUE")
        overdue_records.append(r["record_id"])
    else:
        print(f"  {r['record_id']}: {delay}d → OK")

print(f"  → Overdue records: {overdue_records}")

# ============================================================
# 5. OVER-BUDGET — Article 13 + 08_budget_management Article 3
# ============================================================
print("\n" + "=" * 60)
print("5. OVER-BUDGET (超预算) — D902 budget=50000")
print("=" * 60)

# Sort D902 records by expense_date
d902_recs = sorted([r for r in records if r["dept_id"] == "D902"], key=lambda r: r["_ed"])
cum = 0
budget = budgets["D902"]
budget_violation = []
for r in d902_recs:
    cum += r["amount"]
    crossing = cum > budget
    prev_crossing = (cum - r["amount"]) >= budget
    causing = crossing and not prev_crossing  # first record that crosses
    sp = "special_approval" if r["special_approval"] else "no special_approval"
    status = ""
    if crossing and not r["special_approval"]:
        status = "→ OVER-BUDGET VIOLATION"
        budget_violation.append(r["record_id"])
    elif crossing and r["special_approval"]:
        status = f"→ over budget but has {sp} (exempt)"
    else:
        status = f"→ OK (cum={cum} ≤ {budget})"
    print(f"  {r['record_id']}: {r['expense_date']} {r['amount']}元 cum={cum} budget={budget} {sp} {status}")

print(f"  → Over-budget violation records: {budget_violation}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)

all_violations = {
    "DUPLICATE": sorted(set(duplicate_records)),
    "SPLIT": sorted(set(split_results)),
    "OVER_STANDARD": sorted(over_standard),
    "OVERDUE": sorted(overdue_records),
    "OVER_BUDGET": sorted(budget_violation),
}

all_ids = sorted(set(sum(all_violations.values(), [])))
print(f"Total records: {len(records)}")
print(f"Records with violations: {len(all_ids)}")
for vtype, ids in all_violations.items():
    print(f"  {vtype}: {ids}")

# ============================================================
# BUILD SUMMARY JSON
# ============================================================
summary = {
    "decision": "reject",
    "key_findings": [
        "DUPLICATE: Invoice FPDEV900001 used by R900001 and R900002 — violates Article 10",
        "SPLIT: E9001 travel_transport R900003+R900004 within 3 days, combined 10400≥10000 — violates Article 11 + AR-03",
        "OVER-STANDARD office_supplies: E9001 Jan(960), Apr(650) exceed 600/month cap — Article 2 of 07",
        "OVER-STANDARD communication: E9001 Sep(340) exceeds 300/month cap — Article 3 of 07",
        "OVER-STANDARD travel_lodging: R900013 E9002经理级 一类城市 700/晚 > 650标准 — Article 4 of 04",
        "OVER-STANDARD training_fee: R900016 850/day > 800 internal cap — Article 3 of 05",
        "OVER-STANDARD business_entertainment: R900005 360/人 > 300/人; R900017 5200 > 5000/event — Articles 2,3 of 06",
        "OVERDUE: R900006 65-day delay exceeds 60-day limit — Article 7",
        "OVER-BUDGET: D902 R900019 causes cumulative crossing of 50000 budget without special_approval — Article 13 + 08 Article 3",
    ],
    "record_ids": all_ids,
    "citations": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "10"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "11"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "7"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "13"},
        {"doc_id": "03_authorization_management.md", "clause_no": "AR-03"},
        {"doc_id": "04_travel_expense.md", "clause_no": "4"},
        {"doc_id": "05_training_expense.md", "clause_no": "3"},
        {"doc_id": "05_training_expense.md", "clause_no": "5"},
        {"doc_id": "06_business_entertainment.md", "clause_no": "2"},
        {"doc_id": "06_business_entertainment.md", "clause_no": "3"},
        {"doc_id": "07_office_communication.md", "clause_no": "2"},
        {"doc_id": "07_office_communication.md", "clause_no": "3"},
        {"doc_id": "08_budget_management.md", "clause_no": "3"},
    ],
    "unresolved_items": [],
    "artifact_paths": [
        "work/subagents/data_analyst/comprehensive_analysis.py",
        "work/subagents/data_analyst/summary.json",
    ]
}

with open("/workspace/work/subagents/data_analyst/summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"\nSummary written to work/subagents/data_analyst/summary.json")
print(f"record_ids count: {len(all_ids)}")
