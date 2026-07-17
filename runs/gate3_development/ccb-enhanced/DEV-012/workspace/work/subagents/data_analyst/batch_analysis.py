#!/usr/bin/env python3
"""
Comprehensive batch expense analysis for DEV-012.
Checks 5 audit rules against 21 expense records.

Rules:
  1. Duplicate Invoice (01_expense_reimbursement_2025.md Art.10)
  2. Split Claims (01_expense_reimbursement_2025.md Art.11)
  3. Over-standard (01_expense_reimbursement_2025.md Art.12)
  4. Overdue (01_expense_reimbursement_2025.md Art.7, Art.9)
  5. Over-budget (08_budget_management.md Art.3)

Policy standards:
  - office_supplies: 600/person/month (07_office_communication Art.2)
  - communication: 300/person/month (07_office_communication Art.3)
  - travel_lodging: manager tier1 650/night, staff tier1 450/night (04_travel Art.4)
  - training_fee internal: 800/day (05_training Art.3)
  - training_lodging tier1: 500/night (05_training Art.5)
  - business_entertainment: 5000/event AND 300/person (06_business_entertainment Art.2-3)
  - AR thresholds: 0-3000(AR-01), 3000-10000(AR-02), 10000-50000(AR-03),
                   50000-200000(AR-04), 200000+(AR-05)
"""

import json
from datetime import date, timedelta
from collections import defaultdict

# =============================================================================
# FULL RECORD DATA (from MCP detailed lookups + overview)
# =============================================================================

records = [
    {"record_id":"R900001","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-01-05","reimburse_date":"2025-01-12","expense_type":"office_supplies","amount":480.0,"reason":"项目装订用品第一次报销","invoice_id":"INV900001","invoice_no":"FPDEV900001","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":7,"approval_tier":"AR-01"},
    {"record_id":"R900002","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-01-06","reimburse_date":"2025-01-13","expense_type":"office_supplies","amount":480.0,"reason":"项目装订用品第二次报销","invoice_id":"INV900001","invoice_no":"FPDEV900001","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":7,"approval_tier":"AR-01"},
    {"record_id":"R900003","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-02-03","reimburse_date":"2025-02-08","expense_type":"travel_transport","amount":5200.0,"reason":"同一客户路演交通费第一笔","invoice_id":"INV900003","invoice_no":"FPDEV900003","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":5,"approval_tier":"AR-02"},
    {"record_id":"R900004","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-02-06","reimburse_date":"2025-02-10","expense_type":"travel_transport","amount":5200.0,"reason":"同一客户路演交通费第二笔","invoice_id":"INV900004","invoice_no":"FPDEV900004","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":4,"approval_tier":"AR-02"},
    {"record_id":"R900005","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-03-12","reimburse_date":"2025-03-20","expense_type":"business_entertainment","amount":3600.0,"reason":"客户交流餐叙","invoice_id":"INV900005","invoice_no":"FPDEV900005","status":"approved","city_tier":None,"nights":None,"days":None,"participants":10,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":8,"approval_tier":"AR-02"},
    {"record_id":"R900006","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-03-01","reimburse_date":"2025-05-05","expense_type":"communication","amount":200.0,"reason":"三月通讯费延迟报销","invoice_id":"INV900006","invoice_no":"FPDEV900006","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":65,"approval_tier":"AR-01"},
    {"record_id":"R900007","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-04-08","reimburse_date":"2025-04-12","expense_type":"office_supplies","amount":650.0,"reason":"四月个人办公用品","invoice_id":"INV900007","invoice_no":"FPDEV900007","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":4,"approval_tier":"AR-01"},
    {"record_id":"R900008","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-05-05","reimburse_date":"2025-05-10","expense_type":"office_supplies","amount":590.0,"reason":"五月办公用品甲","invoice_id":"INV900008","invoice_no":"FPDEV900008","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":5,"approval_tier":"AR-01"},
    {"record_id":"R900009","employee_id":"E9002","employee_name":"开发经理乙","department_id":"D901","expense_date":"2025-05-05","reimburse_date":"2025-05-10","expense_type":"office_supplies","amount":590.0,"reason":"五月办公用品乙","invoice_id":"INV900009","invoice_no":"FPDEV900009","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"经理级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":5,"approval_tier":"AR-01"},
    {"record_id":"R900010","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-06-01","reimburse_date":"2025-06-05","expense_type":"travel_transport","amount":5300.0,"reason":"客户走访交通第一阶段","invoice_id":"INV900010","invoice_no":"FPDEV900010","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":4,"approval_tier":"AR-02"},
    {"record_id":"R900011","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-06-09","reimburse_date":"2025-06-13","expense_type":"travel_transport","amount":5300.0,"reason":"客户走访交通第二阶段","invoice_id":"INV900011","invoice_no":"FPDEV900011","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":4,"approval_tier":"AR-02"},
    {"record_id":"R900012","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-12-20","reimburse_date":"2026-01-10","expense_type":"other","amount":900.0,"reason":"年末发生费用补充提交","invoice_id":"INV900012","invoice_no":"FPDEV900012","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":21,"approval_tier":"AR-01"},
    {"record_id":"R900013","employee_id":"E9002","employee_name":"开发经理乙","department_id":"D901","expense_date":"2025-07-10","reimburse_date":"2025-07-15","expense_type":"travel_lodging","amount":1400.0,"reason":"一类城市经理级住宿两晚","invoice_id":"INV900013","invoice_no":"FPDEV900013","status":"approved","city_tier":"A","nights":2,"days":None,"participants":None,"special_approval":0,"employee_level":"经理级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":5,"approval_tier":"AR-01"},
    {"record_id":"R900014","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-09-03","reimburse_date":"2025-09-06","expense_type":"communication","amount":180.0,"reason":"九月通讯费上半月","invoice_id":"INV900014","invoice_no":"FPDEV900014","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":3,"approval_tier":"AR-01"},
    {"record_id":"R900015","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-09-20","reimburse_date":"2025-09-23","expense_type":"communication","amount":160.0,"reason":"九月通讯费下半月","invoice_id":"INV900015","invoice_no":"FPDEV900015","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":3,"approval_tier":"AR-01"},
    {"record_id":"R900016","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-08-02","reimburse_date":"2025-08-08","expense_type":"training_fee","amount":850.0,"reason":"内部培训综合费用一天","invoice_id":"INV900016","invoice_no":"FPDEV900016","status":"approved","city_tier":None,"nights":None,"days":1,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":6,"approval_tier":"AR-01"},
    {"record_id":"R900017","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-10-06","reimburse_date":"2025-10-12","expense_type":"business_entertainment","amount":5200.0,"reason":"客户交流活动二十人","invoice_id":"INV900017","invoice_no":"FPDEV900017","status":"approved","city_tier":None,"nights":None,"days":None,"participants":20,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":6,"approval_tier":"AR-02"},
    {"record_id":"R900018","employee_id":"E9003","employee_name":"开发员工丙","department_id":"D902","expense_date":"2025-01-15","reimburse_date":"2025-01-20","expense_type":"other","amount":45000.0,"reason":"年度基础服务采购","invoice_id":"INV900018","invoice_no":"FPDEV900018","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计二部","annual_budget":50000.0,"delay_days":5,"approval_tier":"AR-03"},
    {"record_id":"R900019","employee_id":"E9003","employee_name":"开发员工丙","department_id":"D902","expense_date":"2025-02-15","reimburse_date":"2025-02-20","expense_type":"other","amount":6000.0,"reason":"新增业务服务采购","invoice_id":"INV900019","invoice_no":"FPDEV900019","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计二部","annual_budget":50000.0,"delay_days":5,"approval_tier":"AR-02"},
    {"record_id":"R900020","employee_id":"E9003","employee_name":"开发员工丙","department_id":"D902","expense_date":"2025-03-15","reimburse_date":"2025-03-20","expense_type":"other","amount":5000.0,"reason":"专项批准的连续性支出","invoice_id":"INV900020","invoice_no":"FPDEV900020","status":"approved","city_tier":None,"nights":None,"days":None,"participants":None,"special_approval":1,"employee_level":"员工级","department_name":"开发审计二部","annual_budget":50000.0,"delay_days":5,"approval_tier":"AR-02"},
    {"record_id":"R900021","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-12-02","reimburse_date":"2025-12-08","expense_type":"training_lodging","amount":480.0,"reason":"一类城市培训住宿一晚","invoice_id":"INV900021","invoice_no":"FPDEV900021","status":"approved","city_tier":"A","nights":1,"days":None,"participants":None,"special_approval":0,"employee_level":"员工级","department_name":"开发审计一部","annual_budget":200000.0,"delay_days":6,"approval_tier":"AR-01"},
]

# =============================================================================
# POLICY THRESHOLDS
# =============================================================================
POLICY = {
    "office_supplies_per_person_month": 600,
    "communication_per_person_month": 300,
    "travel_lodging_manager_tier1_per_night": 650,
    "travel_lodging_staff_tier1_per_night": 450,
    "training_fee_internal_per_day": 800,
    "training_lodging_tier1_per_night": 500,
    "business_entertainment_per_event": 5000,
    "business_entertainment_per_person": 300,
    "overdue_days": 60,
    "dec_extension_days": 15,
}

# AR thresholds: (lower_bound, upper_bound, tier_name)
AR_THRESHOLDS = [
    (0, 3000, "AR-01"),
    (3000, 10000, "AR-02"),
    (10000, 50000, "AR-03"),
    (50000, 200000, "AR-04"),
    (200000, float("inf"), "AR-05"),
]


def get_ar_tier(amount):
    for lo, hi, tier in AR_THRESHOLDS:
        if lo < amount <= hi:
            return tier
    return None


def parse_date(s):
    return date.fromisoformat(s)


# =============================================================================
# RULE 1: DUPLICATE INVOICE (Art.10)
# =============================================================================
print("=" * 70)
print("RULE 1: DUPLICATE INVOICE (01_expense_reimbursement_2025.md Art.10)")
print("  Same invoice max 1 time.")
print("=" * 70)

invoice_map = defaultdict(list)
for r in records:
    invoice_map[r["invoice_id"]].append(r)

dup_anomalies = []
dup_record_ids = set()
for inv_id, recs in invoice_map.items():
    if len(recs) > 1:
        # The first claim is valid, subsequent claims using same invoice are duplicates
        for i, r in enumerate(recs):
            dup_record_ids.add(r["record_id"])
            role = "original" if i == 0 else "duplicate"
            print(f"  Invoice {inv_id} ({r['invoice_no']}) used {len(recs)} times:")
            print(f"    {r['record_id']}: {r['reason']} ({role}) amount={r['amount']}")
        dup_anomalies.append({
            "invoice_id": inv_id,
            "invoice_no": recs[0]["invoice_no"],
            "records": [r["record_id"] for r in recs],
            "duplicate_record": recs[1]["record_id"],  # the 2nd use
            "amount": recs[0]["amount"],
        })

if not dup_anomalies:
    print("  No duplicate invoice violations found.")
else:
    print(f"\n  TOTAL DUPLICATE VIOLATIONS: {len(dup_anomalies)}")

# =============================================================================
# RULE 2: SPLIT CLAIMS (Art.11)
# =============================================================================
print("\n" + "=" * 70)
print("RULE 2: SPLIT CLAIMS (01_expense_reimbursement_2025.md Art.11)")
print("  Same employee, same expense_type within 7 calendar days,")
print("  combined reaching higher AR level.")
print("=" * 70)

# Group by (employee, expense_type) for pairwise checking
split_groups = defaultdict(list)
for r in records:
    key = (r["employee_id"], r["expense_type"])
    # Only consider types that could be split - but check all per policy
    split_groups[key].append(r)

split_record_ids = set()
split_anomalies = []

for key, recs in sorted(split_groups.items()):
    emp_id, exp_type = key
    if len(recs) < 2:
        continue
    # Sort by expense_date
    recs_sorted = sorted(recs, key=lambda r: r["expense_date"])
    for i in range(len(recs_sorted)):
        for j in range(i + 1, len(recs_sorted)):
            r1, r2 = recs_sorted[i], recs_sorted[j]
            d1 = parse_date(r1["expense_date"])
            d2 = parse_date(r2["expense_date"])
            diff = (d2 - d1).days
            if diff <= 7:
                combined = r1["amount"] + r2["amount"]
                tier_each = get_ar_tier(max(r1["amount"], r2["amount"]))
                tier_combined = get_ar_tier(combined)
                print(f"  {emp_id} {exp_type}: {r1['record_id']}({r1['expense_date']},{r1['amount']}) + "
                      f"{r2['record_id']}({r2['expense_date']},{r2['amount']}) = {combined}, "
                      f"diff={diff}d, each_tier={tier_each}, combined_tier={tier_combined}")
                if tier_each != tier_combined:
                    print(f"    >>> SPLIT VIOLATION: each AR={tier_each}, combined AR={tier_combined}")
                    split_record_ids.add(r1["record_id"])
                    split_record_ids.add(r2["record_id"])
                    split_anomalies.append({
                        "records": [r1["record_id"], r2["record_id"]],
                        "employee_id": emp_id,
                        "expense_type": exp_type,
                        "amounts": [r1["amount"], r2["amount"]],
                        "combined": combined,
                        "dates_diff": diff,
                        "individual_tier": tier_each,
                        "combined_tier": tier_combined,
                    })
                else:
                    print(f"    Same AR tier {tier_each} -- not a split violation")

if not split_anomalies:
    print("  No split claim violations found.")
else:
    print(f"\n  TOTAL SPLIT VIOLATIONS: {len(split_anomalies)}")

# =============================================================================
# RULE 3: OVER-STANDARD (Art.12)
# =============================================================================
print("\n" + "=" * 70)
print("RULE 3: OVER-STANDARD (01_expense_reimbursement_2025.md Art.12)")
print("  Max 1.0x standard.")
print("=" * 70)

over_std_record_ids = set()
over_std_anomalies = []

# --- 3a. office_supplies: 600/person/month ---
print("\n  --- office_supplies (600/person/month, 07_office_communication Art.2) ---")
# Reconcile duplicate invoices first: dedupe by invoice_id within each (employee, month) group
os_groups = defaultdict(lambda: {"invoices_seen": set(), "total": 0, "records": []})
for r in records:
    if r["expense_type"] != "office_supplies":
        continue
    d = parse_date(r["expense_date"])
    month_key = f"{d.year}-{d.month:02d}"
    key = (r["employee_id"], month_key)
    if r["invoice_id"] not in os_groups[key]["invoices_seen"]:
        os_groups[key]["invoices_seen"].add(r["invoice_id"])
        os_groups[key]["total"] += r["amount"]
    os_groups[key]["records"].append(r)

for key, grp in sorted(os_groups.items()):
    emp_id, month = key
    actual = grp["total"]
    std = POLICY["office_supplies_per_person_month"]
    status = "OVER" if actual > std else "OK"
    print(f"    {emp_id} {month}: sum={actual} vs std={std} [{status}]")
    if actual > std:
        for r in grp["records"]:
            over_std_record_ids.add(r["record_id"])
        over_std_anomalies.append({
            "rule": "office_supplies_monthly",
            "employee_id": emp_id,
            "month": month,
            "actual": actual,
            "standard": std,
            "excess": actual - std,
            "records": [r["record_id"] for r in grp["records"]],
            "citation": {"doc_id": "07_office_communication", "clause_no": "Art.2"},
        })

# --- 3b. communication: 300/person/month ---
print("\n  --- communication (300/person/month, 07_office_communication Art.3) ---")
comm_groups = defaultdict(lambda: {"total": 0, "records": []})
for r in records:
    if r["expense_type"] != "communication":
        continue
    d = parse_date(r["expense_date"])
    month_key = f"{d.year}-{d.month:02d}"
    key = (r["employee_id"], month_key)
    comm_groups[key]["total"] += r["amount"]
    comm_groups[key]["records"].append(r)

for key, grp in sorted(comm_groups.items()):
    emp_id, month = key
    actual = grp["total"]
    std = POLICY["communication_per_person_month"]
    status = "OVER" if actual > std else "OK"
    print(f"    {emp_id} {month}: sum={actual} vs std={std} [{status}]")
    if actual > std:
        for r in grp["records"]:
            over_std_record_ids.add(r["record_id"])
        over_std_anomalies.append({
            "rule": "communication_monthly",
            "employee_id": emp_id,
            "month": month,
            "actual": actual,
            "standard": std,
            "excess": actual - std,
            "records": [r["record_id"] for r in grp["records"]],
            "citation": {"doc_id": "07_office_communication", "clause_no": "Art.3"},
        })

# --- 3c. travel_lodging ---
print("\n  --- travel_lodging (04_travel Art.4) ---")
for r in records:
    if r["expense_type"] != "travel_lodging":
        continue
    if r["city_tier"] == "A" and r["nights"] and r["nights"] > 0:
        per_night = r["amount"] / r["nights"]
        if r["employee_level"] == "经理级":
            std = POLICY["travel_lodging_manager_tier1_per_night"]
        else:
            std = POLICY["travel_lodging_staff_tier1_per_night"]
        status = "OVER" if per_night > std else "OK"
        print(f"    {r['record_id']}: {r['employee_name']}({r['employee_level']}), "
              f"tier1, {r['nights']} nights, {r['amount']} total, "
              f"{per_night:.0f}/night vs std {std} [{status}]")
        if per_night > std:
            over_std_record_ids.add(r["record_id"])
            over_std_anomalies.append({
                "rule": "travel_lodging_per_night",
                "record_id": r["record_id"],
                "employee_level": r["employee_level"],
                "per_night": per_night,
                "standard": std,
                "excess": per_night - std,
                "nights": r["nights"],
                "citation": {"doc_id": "04_travel", "clause_no": "Art.4"},
            })

# --- 3d. training_fee ---
print("\n  --- training_fee internal (800/day, 05_training Art.3) ---")
for r in records:
    if r["expense_type"] != "training_fee":
        continue
    if r["days"] and r["days"] > 0:
        per_day = r["amount"] / r["days"]
        std = POLICY["training_fee_internal_per_day"]
        status = "OVER" if per_day > std else "OK"
        print(f"    {r['record_id']}: {r['employee_name']}, {r['days']} day(s), "
              f"{r['amount']} total, {per_day:.0f}/day vs std {std} [{status}]")
        if per_day > std:
            over_std_record_ids.add(r["record_id"])
            over_std_anomalies.append({
                "rule": "training_fee_per_day",
                "record_id": r["record_id"],
                "per_day": per_day,
                "standard": std,
                "excess": per_day - std,
                "days": r["days"],
                "citation": {"doc_id": "05_training", "clause_no": "Art.3"},
            })

# --- 3e. training_lodging ---
print("\n  --- training_lodging tier1 (500/night, 05_training Art.5) ---")
for r in records:
    if r["expense_type"] != "training_lodging":
        continue
    if r["city_tier"] == "A" and r["nights"] and r["nights"] > 0:
        per_night = r["amount"] / r["nights"]
        std = POLICY["training_lodging_tier1_per_night"]
        status = "OVER" if per_night > std else "OK"
        print(f"    {r['record_id']}: {r['employee_name']}, tier1, "
              f"{r['nights']} night(s), {r['amount']} total, "
              f"{per_night:.0f}/night vs std {std} [{status}]")
        if per_night > std:
            over_std_record_ids.add(r["record_id"])
            over_std_anomalies.append({
                "rule": "training_lodging_per_night",
                "record_id": r["record_id"],
                "per_night": per_night,
                "standard": std,
                "excess": per_night - std,
                "nights": r["nights"],
                "citation": {"doc_id": "05_training", "clause_no": "Art.5"},
            })

# --- 3f. business_entertainment ---
print("\n  --- business_entertainment (5000/event AND 300/person, 06_business_entertainment Art.2-3) ---")
for r in records:
    if r["expense_type"] != "business_entertainment":
        continue
    violations = []
    # Per-event check
    if r["amount"] > POLICY["business_entertainment_per_event"]:
        violations.append(f"event cap: {r['amount']} > {POLICY['business_entertainment_per_event']}")
    # Per-person check
    if r["participants"] and r["participants"] > 0:
        per_person = r["amount"] / r["participants"]
        if per_person > POLICY["business_entertainment_per_person"]:
            violations.append(f"per-person: {per_person:.0f} > {POLICY['business_entertainment_per_person']}")
        print(f"    {r['record_id']}: {r['amount']} total, {r['participants']} ppl, "
              f"{per_person:.0f}/person, event_cap={POLICY['business_entertainment_per_event']} "
              f"{'OVER' if violations else 'OK'}")
    else:
        print(f"    {r['record_id']}: {r['amount']} total, no participant data "
              f"{'OVER' if violations else 'OK'}")

    if violations:
        over_std_record_ids.add(r["record_id"])
        over_std_anomalies.append({
            "rule": "business_entertainment",
            "record_id": r["record_id"],
            "amount": r["amount"],
            "participants": r["participants"],
            "violations": violations,
            "citation": {"doc_id": "06_business_entertainment", "clause_no": "Art.2-3"},
        })

if not over_std_anomalies:
    print("\n  No over-standard violations found.")
else:
    print(f"\n  TOTAL OVER-STANDARD VIOLATIONS: {len(over_std_anomalies)}")

# =============================================================================
# RULE 4: OVERDUE (Art.7, Art.9)
# =============================================================================
print("\n" + "=" * 70)
print("RULE 4: OVERDUE (01_expense_reimbursement_2025.md Art.7, Art.9)")
print("  Reimburse within 60 days of expense date.")
print("  Dec expenses: 15-day extension from Dec 31.")
print("  Checking delay_days from MCP list_records_by_reimburse_delay.")
print("=" * 70)

overdue_record_ids = set()
overdue_anomalies = []

for r in records:
    delay = r["delay_days"]
    exp_date = parse_date(r["expense_date"])
    is_dec = (exp_date.month == 12)

    # Effective threshold
    effective_threshold = POLICY["overdue_days"]
    if is_dec:
        # Dec expenses: 60 days + 15-day extension from Dec 31
        # The delay_days is raw expense_date -> reimburse_date.
        # For Dec expenses, the effective deadline extends by 15 days beyond the normal 60.
        # So we compare against 75 days total for December expenses.
        effective_threshold = POLICY["overdue_days"] + POLICY["dec_extension_days"]

    status = "OVERDUE" if delay > effective_threshold else "OK"
    dec_note = " (Dec extension applied)" if is_dec else ""
    print(f"  {r['record_id']}: expense={r['expense_date']}, reimburse={r['reimburse_date']}, "
          f"delay={delay}d, threshold={effective_threshold}d{dec_note} [{status}]")
    if delay > effective_threshold:
        overdue_record_ids.add(r["record_id"])
        overdue_anomalies.append({
            "record_id": r["record_id"],
            "expense_date": r["expense_date"],
            "reimburse_date": r["reimburse_date"],
            "delay_days": delay,
            "threshold": effective_threshold,
            "excess_days": delay - effective_threshold,
            "is_december": is_dec,
            "citation": {"doc_id": "01_expense_reimbursement_2025", "clause_no": "Art.7" if not is_dec else "Art.7, Art.9"},
        })

if not overdue_anomalies:
    print("\n  No overdue violations found.")
else:
    print(f"\n  TOTAL OVERDUE VIOLATIONS: {len(overdue_anomalies)}")

# =============================================================================
# RULE 5: OVER-BUDGET (Art.3)
# =============================================================================
print("\n" + "=" * 70)
print("RULE 5: OVER-BUDGET (08_budget_management.md Art.3)")
print("  Department used > annual budget x 1.0")
print("=" * 70)

dept_usage = defaultdict(lambda: {"total": 0, "budget": 0, "records": [], "name": ""})
for r in records:
    dept_id = r["department_id"]
    dept_usage[dept_id]["total"] += r["amount"]
    dept_usage[dept_id]["budget"] = r["annual_budget"]
    dept_usage[dept_id]["name"] = r["department_name"]
    dept_usage[dept_id]["records"].append(r)

budget_record_ids = set()
budget_anomalies = []

for dept_id, info in sorted(dept_usage.items()):
    used = info["total"]
    budget = info["budget"]
    ratio = used / budget if budget > 0 else float("inf")
    status = "OVER" if used > budget else "OK"
    print(f"  {dept_id} ({info['name']}): budget={budget}, used={used}, ratio={ratio:.2%} [{status}]")

    if used > budget:
        # Find the record that first crosses the budget
        # Sort records by expense_date
        running = 0
        crossing_records = []
        for r in sorted(info["records"], key=lambda x: x["expense_date"]):
            running += r["amount"]
            if running > budget and running - r["amount"] <= budget:
                # This record causes the first crossing
                # Per instructions: only include unapproved records; approved and special_approval are context
                if r["status"] != "approved" and r["special_approval"] != 1:
                    crossing_records.append(r["record_id"])
                    budget_record_ids.add(r["record_id"])
                    print(f"    Crossing record: {r['record_id']} (amount={r['amount']}, "
                          f"running={running}, status={r['status']}, special_approval={r['special_approval']})")
        if not crossing_records:
            print(f"    Budget exceeded but all crossing records are either approved or have special approval.")
            print(f"    No unapproved crossing records to flag as anomaly records.")

        budget_anomalies.append({
            "department_id": dept_id,
            "department_name": info["name"],
            "budget": budget,
            "used": used,
            "excess": used - budget,
            "ratio": ratio,
            "crossing_records_flagged": crossing_records,
            "citation": {"doc_id": "08_budget_management", "clause_no": "Art.3"},
        })

if not budget_anomalies:
    print("\n  No over-budget violations found.")
else:
    print(f"\n  TOTAL OVER-BUDGET VIOLATIONS: {len(budget_anomalies)}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

all_anomaly_record_ids = (
    dup_record_ids
    | split_record_ids
    | over_std_record_ids
    | overdue_record_ids
    | budget_record_ids
)

print(f"\n  Rule 1 (Duplicate Invoice): {len(dup_anomalies)} violations, "
      f"records: {sorted(dup_record_ids)}")
print(f"  Rule 2 (Split Claims):      {len(split_anomalies)} violations, "
      f"records: {sorted(split_record_ids)}")
print(f"  Rule 3 (Over-standard):     {len(over_std_anomalies)} violations, "
      f"records: {sorted(over_std_record_ids)}")
print(f"  Rule 4 (Overdue):           {len(overdue_anomalies)} violations, "
      f"records: {sorted(overdue_record_ids)}")
print(f"  Rule 5 (Over-budget):       {len(budget_anomalies)} violations (departments), "
      f"records: {sorted(budget_record_ids)}")
print(f"\n  TOTAL UNIQUE ANOMALY RECORDS: {len(all_anomaly_record_ids)}")
print(f"  Record IDs: {sorted(all_anomaly_record_ids)}")

# =============================================================================
# EXPORT JSON
# =============================================================================
result = {
    "rules": {
        "duplicate_invoice": {
            "violations": len(dup_anomalies),
            "record_ids": sorted(dup_record_ids),
            "details": dup_anomalies,
            "citations": [{"doc_id": "01_expense_reimbursement_2025", "clause_no": "Art.10"}],
        },
        "split_claims": {
            "violations": len(split_anomalies),
            "record_ids": sorted(split_record_ids),
            "details": split_anomalies,
            "citations": [{"doc_id": "01_expense_reimbursement_2025", "clause_no": "Art.11"}],
        },
        "over_standard": {
            "violations": len(over_std_anomalies),
            "record_ids": sorted(over_std_record_ids),
            "details": over_std_anomalies,
            "citations": [
                {"doc_id": "07_office_communication", "clause_no": "Art.2"},
                {"doc_id": "07_office_communication", "clause_no": "Art.3"},
                {"doc_id": "04_travel", "clause_no": "Art.4"},
                {"doc_id": "05_training", "clause_no": "Art.3"},
                {"doc_id": "05_training", "clause_no": "Art.5"},
                {"doc_id": "06_business_entertainment", "clause_no": "Art.2-3"},
                {"doc_id": "01_expense_reimbursement_2025", "clause_no": "Art.12"},
            ],
        },
        "overdue": {
            "violations": len(overdue_anomalies),
            "record_ids": sorted(overdue_record_ids),
            "details": overdue_anomalies,
            "citations": [{"doc_id": "01_expense_reimbursement_2025", "clause_no": "Art.7, Art.9"}],
        },
        "over_budget": {
            "violations": len(budget_anomalies),
            "record_ids": sorted(budget_record_ids),
            "details": budget_anomalies,
            "citations": [{"doc_id": "08_budget_management", "clause_no": "Art.3"}],
        },
    },
    "total_unique_anomaly_records": len(all_anomaly_record_ids),
    "all_anomaly_record_ids": sorted(all_anomaly_record_ids),
}

with open("/workspace/work/subagents/data_analyst/analysis_results.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n  Results saved to /workspace/work/subagents/data_analyst/analysis_results.json")
