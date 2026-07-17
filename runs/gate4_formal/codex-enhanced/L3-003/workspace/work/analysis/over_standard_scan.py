#!/usr/bin/env python3
"""Full-year over-standard scan for all expense types."""

import sqlite3
import json
from collections import defaultdict

DB = "/benchmark/data/expense.db"

# Level mapping for travel lodging
LEVEL_MAP = {
    "E1": "employee",    # 员工级
    "M1": "manager",     # 经理级
    "D1": "dept_head",   # 部门负责人级
    "X1": "executive",   # 高管级
}

# Lodging standards: [tier_A, tier_B, tier_C]
LODGING_STANDARD = {
    "employee":   {"A": 450, "B": 380, "C": 300},
    "manager":    {"A": 650, "B": 550, "C": 450},
    "dept_head":  {"A": 850, "B": 700, "C": 600},
    "executive":  {"A": 1100, "B": 900, "C": 750},
}

# Local transport standard: [tier_A, tier_B, tier_C]
TRANSPORT_STANDARD = {"A": 120, "B": 100, "C": 80}

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

results = {}  # anomaly_id -> {records, rule, facts}

# ============================================================
# R1: Travel lodging over standard
# ============================================================
print("=== R1: Travel Lodging ===")
query = """
SELECT er.record_id, er.employee_id, er.amount, er.city_tier, er.nights,
       er.special_approval, e.employee_level
FROM expense_records er
JOIN employees e ON er.employee_id = e.employee_id
WHERE er.expense_type = 'travel_lodging'
  AND er.budget_year = 2025
  AND er.city_tier IS NOT NULL
  AND er.nights IS NOT NULL
  AND er.nights > 0
"""
rows = conn.execute(query).fetchall()
print(f"  Total travel_lodging records with city_tier+nights: {len(rows)}")

r1_anomalies = []
for r in rows:
    if r["special_approval"] == 1:
        continue
    level_key = LEVEL_MAP.get(r["employee_level"])
    if level_key is None:
        continue
    tier = r["city_tier"]
    if tier not in ("A", "B", "C"):
        continue
    standard_per_night = LODGING_STANDARD[level_key][tier]
    actual_per_night = r["amount"] / r["nights"]
    if actual_per_night > standard_per_night:
        r1_anomalies.append({
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "employee_level": r["employee_level"],
            "city_tier": tier,
            "amount": r["amount"],
            "nights": r["nights"],
            "actual_per_night": round(actual_per_night, 2),
            "standard_per_night": standard_per_night,
            "excess": round(actual_per_night - standard_per_night, 2)
        })

print(f"  R1 anomalies: {len(r1_anomalies)}")
if r1_anomalies:
    results["ANOM-R1"] = {
        "rule": "R1-差旅住宿费超标准",
        "policy": "04_travel_expense.md",
        "clauses": ["第四条", "第五条"],
        "records": [a["record_id"] for a in r1_anomalies],
        "details": r1_anomalies
    }

# ============================================================
# R2: Local transport over standard
# ============================================================
print("=== R2: Local Transport ===")
query = """
SELECT er.record_id, er.employee_id, er.amount, er.city_tier, er.days,
       er.special_approval
FROM expense_records er
WHERE er.expense_type = 'local_transport'
  AND er.budget_year = 2025
  AND er.city_tier IS NOT NULL
  AND er.days IS NOT NULL
  AND er.days > 0
"""
rows = conn.execute(query).fetchall()
print(f"  Total local_transport records: {len(rows)}")

r2_anomalies = []
for r in rows:
    if r["special_approval"] == 1:
        continue
    tier = r["city_tier"]
    if tier not in ("A", "B", "C"):
        continue
    standard_per_day = TRANSPORT_STANDARD[tier]
    actual_per_day = r["amount"] / r["days"]
    if actual_per_day > standard_per_day:
        r2_anomalies.append({
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "city_tier": tier,
            "amount": r["amount"],
            "days": r["days"],
            "actual_per_day": round(actual_per_day, 2),
            "standard_per_day": standard_per_day,
            "excess": round(actual_per_day - standard_per_day, 2)
        })

print(f"  R2 anomalies: {len(r2_anomalies)}")
if r2_anomalies:
    results["ANOM-R2"] = {
        "rule": "R2-出差市内交通包干超标准",
        "policy": "04_travel_expense.md",
        "clauses": ["第六条"],
        "records": [a["record_id"] for a in r2_anomalies],
        "details": r2_anomalies
    }

# ============================================================
# R7: Business entertainment single-event over standard (>5000)
# ============================================================
print("=== R7: Business Entertainment Single Event ===")
query = """
SELECT er.record_id, er.employee_id, er.amount, er.participants, er.special_approval
FROM expense_records er
WHERE er.expense_type = 'business_entertainment'
  AND er.budget_year = 2025
"""
rows = conn.execute(query).fetchall()
print(f"  Total business_entertainment records: {len(rows)}")

r7_anomalies = []
for r in rows:
    if r["special_approval"] == 1:
        continue
    if r["amount"] > 5000:
        r7_anomalies.append({
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "amount": r["amount"],
            "standard": 5000,
            "excess": round(r["amount"] - 5000, 2)
        })

print(f"  R7 anomalies: {len(r7_anomalies)}")
if r7_anomalies:
    results["ANOM-R7"] = {
        "rule": "R7-业务招待费单次超标准",
        "policy": "06_business_entertainment.md",
        "clauses": ["第二条"],
        "records": [a["record_id"] for a in r7_anomalies],
        "details": r7_anomalies
    }

# ============================================================
# R8: Business entertainment per-capita over standard (>300)
# ============================================================
print("=== R8: Business Entertainment Per Capita ===")
r8_anomalies = []
for r in rows:
    if r["special_approval"] == 1:
        continue
    if r["participants"] is None or r["participants"] == 0:
        continue
    per_capita = r["amount"] / r["participants"]
    if per_capita > 300:
        r8_anomalies.append({
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "amount": r["amount"],
            "participants": r["participants"],
            "per_capita": round(per_capita, 2),
            "standard": 300,
            "excess": round(per_capita - 300, 2)
        })

print(f"  R8 anomalies: {len(r8_anomalies)}")
if r8_anomalies:
    results["ANOM-R8"] = {
        "rule": "R8-业务招待费人均超标准",
        "policy": "06_business_entertainment.md",
        "clauses": ["第三条"],
        "records": [a["record_id"] for a in r8_anomalies],
        "details": r8_anomalies
    }

# ============================================================
# R9: Office supplies monthly per employee > 600
# ============================================================
print("=== R9: Office Supplies Monthly ===")
query = """
SELECT er.record_id, er.employee_id, er.amount, er.expense_date, er.special_approval
FROM expense_records er
WHERE er.expense_type = 'office_supplies'
  AND er.budget_year = 2025
ORDER BY er.employee_id, er.expense_date
"""
rows = conn.execute(query).fetchall()
print(f"  Total office_supplies records: {len(rows)}")

# Group by employee_id + month
monthly = defaultdict(lambda: {"total": 0.0, "records": [], "any_special": False})
for r in rows:
    month_key = r["expense_date"][:7]  # YYYY-MM
    key = (r["employee_id"], month_key)
    monthly[key]["total"] += r["amount"]
    monthly[key]["records"].append(r["record_id"])
    if r["special_approval"] == 1:
        monthly[key]["any_special"] = True

r9_anomalies = []
for (emp_id, month), data in monthly.items():
    if data["any_special"]:
        continue  # group has special approval, exempt
    if data["total"] > 600:
        r9_anomalies.append({
            "employee_id": emp_id,
            "month": month,
            "total_amount": round(data["total"], 2),
            "standard": 600,
            "excess": round(data["total"] - 600, 2),
            "record_ids": data["records"]
        })

print(f"  R9 anomaly groups: {len(r9_anomalies)}")
if r9_anomalies:
    all_r9_records = []
    for a in r9_anomalies:
        all_r9_records.extend(a["record_ids"])
    results["ANOM-R9"] = {
        "rule": "R9-办公用品月度超标准",
        "policy": "07_office_communication.md",
        "clauses": ["第二条"],
        "records": sorted(set(all_r9_records)),
        "details": r9_anomalies
    }

# ============================================================
# R10: Communication monthly per employee > 300
# ============================================================
print("=== R10: Communication Monthly ===")
query = """
SELECT er.record_id, er.employee_id, er.amount, er.expense_date, er.special_approval
FROM expense_records er
WHERE er.expense_type = 'communication'
  AND er.budget_year = 2025
ORDER BY er.employee_id, er.expense_date
"""
rows = conn.execute(query).fetchall()
print(f"  Total communication records: {len(rows)}")

monthly = defaultdict(lambda: {"total": 0.0, "records": [], "any_special": False})
for r in rows:
    month_key = r["expense_date"][:7]
    key = (r["employee_id"], month_key)
    monthly[key]["total"] += r["amount"]
    monthly[key]["records"].append(r["record_id"])
    if r["special_approval"] == 1:
        monthly[key]["any_special"] = True

r10_anomalies = []
for (emp_id, month), data in monthly.items():
    if data["any_special"]:
        continue
    if data["total"] > 300:
        r10_anomalies.append({
            "employee_id": emp_id,
            "month": month,
            "total_amount": round(data["total"], 2),
            "standard": 300,
            "excess": round(data["total"] - 300, 2),
            "record_ids": data["records"]
        })

print(f"  R10 anomaly groups: {len(r10_anomalies)}")
if r10_anomalies:
    all_r10_records = []
    for a in r10_anomalies:
        all_r10_records.extend(a["record_ids"])
    results["ANOM-R10"] = {
        "rule": "R10-通讯费月度超标准",
        "policy": "07_office_communication.md",
        "clauses": ["第三条"],
        "records": sorted(set(all_r10_records)),
        "details": r10_anomalies
    }

# ============================================================
# R11: Department budget overrun
# ============================================================
print("=== R11: Department Budget ===")
query = """
SELECT er.record_id, er.department_id, er.amount, er.expense_date,
       er.special_approval, d.annual_budget
FROM expense_records er
JOIN departments d ON er.department_id = d.department_id
WHERE er.budget_year = 2025
ORDER BY er.department_id, er.expense_date, er.record_id
"""
rows = conn.execute(query).fetchall()
print(f"  Total all records for budget: {len(rows)}")

r11_anomalies = []
dept_cumulative = defaultdict(float)
for r in rows:
    dept_id = r["department_id"]
    budget = r["annual_budget"]
    cumulative_before = dept_cumulative[dept_id]
    
    if cumulative_before >= budget:
        # Already over budget before this record
        if r["special_approval"] == 0:
            r11_anomalies.append({
                "record_id": r["record_id"],
                "department_id": dept_id,
                "amount": r["amount"],
                "cumulative_before": round(cumulative_before, 2),
                "annual_budget": budget,
                "expense_date": r["expense_date"]
            })
    elif cumulative_before + r["amount"] > budget:
        # This record crosses the threshold
        if r["special_approval"] == 0:
            r11_anomalies.append({
                "record_id": r["record_id"],
                "department_id": dept_id,
                "amount": r["amount"],
                "cumulative_before": round(cumulative_before, 2),
                "cumulative_after": round(cumulative_before + r["amount"], 2),
                "annual_budget": budget,
                "expense_date": r["expense_date"]
            })
    
    dept_cumulative[dept_id] += r["amount"]

print(f"  R11 anomalies: {len(r11_anomalies)}")
if r11_anomalies:
    results["ANOM-R11"] = {
        "rule": "R11-部门预算超支",
        "policy": "08_budget_management.md",
        "clauses": ["第三条"],
        "records": [a["record_id"] for a in r11_anomalies],
        "details": r11_anomalies
    }

# ============================================================
# Summary
# ============================================================
print("\n=== SUMMARY ===")
all_anomaly_ids = sorted(results.keys())
all_record_ids = sorted(set(
    rid for v in results.values() for rid in v["records"]
))

print(f"Anomaly IDs: {all_anomaly_ids}")
print(f"Total anomaly types: {len(all_anomaly_ids)}")
print(f"Total unique records: {len(all_record_ids)}")

# Save results
output = {
    "scan_date": "2025-07-16",
    "audit_period": "2025-01-01 to 2025-12-31",
    "anomaly_ids": all_anomaly_ids,
    "record_ids": all_record_ids,
    "total_anomaly_types": len(all_anomaly_ids),
    "total_anomaly_records": len(all_record_ids),
    "results": results
}

with open("/workspace/work/analysis/data_findings.json", "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\nResults saved to work/analysis/data_findings.json")
print(f"\nAnomaly counts by rule:")
for aid in sorted(results.keys()):
    print(f"  {aid}: {len(results[aid]['records'])} records")

conn.close()
