#!/usr/bin/env python3
"""
L3-003: Single-transaction exceedance analysis against thresholds.
Scans all 4240 approved expense records for single-transaction violations.
"""

import sqlite3
import json
import os

DB_PATH = "/benchmark/data/expense.db"
OUTPUT_DIR = "/workspace/work/subagents/data_analyst"

# Threshold definitions
# travel_lodging per-night caps by (employee_level, city_tier)
LODGING_CAPS = {
    ("E1", "A"): 450, ("E1", "B"): 380, ("E1", "C"): 300,
    ("M1", "A"): 650, ("M1", "B"): 550, ("M1", "C"): 450,
    ("D1", "A"): 850, ("D1", "B"): 700, ("D1", "C"): 600,
    ("X1", "A"): 1100, ("X1", "B"): 900, ("X1", "C"): 750,
}

# local_transport daily caps by city_tier
TRANSPORT_CAPS = {"A": 120, "B": 100, "C": 80}

# Tier display names
TIER_NAMES = {"A": "一类", "B": "二类", "C": "三类"}

LEVEL_NAMES = {"E1": "员工级", "M1": "经理级", "D1": "部门负责人级", "X1": "高管级"}

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Build employee level lookup
    cur.execute("SELECT employee_id, employee_level, employee_name FROM employees")
    emp_levels = {row["employee_id"]: (row["employee_level"], row["employee_name"]) for row in cur.fetchall()}

    # Query ALL approved records joined with employee
    cur.execute("""
        SELECT er.*, e.employee_level, e.employee_name
        FROM expense_records er
        JOIN employees e ON er.employee_id = e.employee_id
        WHERE er.status = 'approved'
        ORDER BY er.record_id
    """)

    violations = []
    counts_by_type = {
        "travel_lodging": {"checked": 0, "violations": 0},
        "local_transport": {"checked": 0, "violations": 0},
        "training_fee": {"checked": 0, "violations": 0},
        "business_entertainment": {"checked": 0, "violations": 0},
        "office_supplies": {"checked": 0, "violations": 0},
        "communication": {"checked": 0, "violations": 0},
    }

    city_tier_from_reason_used = {}  # track mismatches

    for row in cur.fetchall():
        record_id = row["record_id"]
        expense_type = row["expense_type"]
        amount = row["amount"]
        employee_id = row["employee_id"]
        employee_level = row["employee_level"]
        employee_name = row["employee_name"]
        reason = row["reason"]
        db_city_tier = row["city_tier"]  # pre-computed in DB
        nights = row["nights"] or 1
        days = row["days"] or 1

        # Use database city_tier (already pre-computed)
        city_tier = db_city_tier

        if expense_type == "travel_lodging":
            counts_by_type["travel_lodging"]["checked"] += 1
            per_night = amount / nights
            cap_key = (employee_level, city_tier) if city_tier in ("A","B","C") else (employee_level, "C")
            threshold = LODGING_CAPS.get(cap_key, 300)
            if per_night > threshold:
                violations.append({
                    "record_id": record_id,
                    "expense_type": "travel_lodging",
                    "amount": amount,
                    "nights": nights,
                    "per_night": round(per_night, 2),
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "employee_level": employee_level,
                    "employee_level_name": LEVEL_NAMES.get(employee_level, employee_level),
                    "city_tier": TIER_NAMES.get(city_tier, "三类"),
                    "city_tier_code": city_tier,
                    "threshold": threshold,
                    "excess": round(per_night - threshold, 2),
                    "reason": reason,
                    "policy": "04_travel_expense.md 第四条"
                })
                counts_by_type["travel_lodging"]["violations"] += 1

        elif expense_type == "local_transport":
            counts_by_type["local_transport"]["checked"] += 1
            threshold = TRANSPORT_CAPS.get(city_tier, 80)
            per_day = amount / days
            if per_day > threshold:
                violations.append({
                    "record_id": record_id,
                    "expense_type": "local_transport",
                    "amount": amount,
                    "days": days,
                    "per_day": round(per_day, 2),
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "employee_level": employee_level,
                    "employee_level_name": LEVEL_NAMES.get(employee_level, employee_level),
                    "city_tier": TIER_NAMES.get(city_tier, "三类"),
                    "city_tier_code": city_tier,
                    "threshold": threshold,
                    "excess": round(per_day - threshold, 2),
                    "reason": reason,
                    "policy": "04_travel_expense.md 第六条"
                })
                counts_by_type["local_transport"]["violations"] += 1

        elif expense_type == "training_fee":
            counts_by_type["training_fee"]["checked"] += 1
            threshold = 3500
            if amount > threshold:
                violations.append({
                    "record_id": record_id,
                    "expense_type": "training_fee",
                    "amount": amount,
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "employee_level": employee_level,
                    "employee_level_name": LEVEL_NAMES.get(employee_level, employee_level),
                    "threshold": threshold,
                    "excess": round(amount - threshold, 2),
                    "reason": reason,
                    "policy": "05_training_expense.md 第二条"
                })
                counts_by_type["training_fee"]["violations"] += 1

        elif expense_type == "business_entertainment":
            counts_by_type["business_entertainment"]["checked"] += 1
            threshold = 5000
            if amount > threshold:
                violations.append({
                    "record_id": record_id,
                    "expense_type": "business_entertainment",
                    "amount": amount,
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "employee_level": employee_level,
                    "employee_level_name": LEVEL_NAMES.get(employee_level, employee_level),
                    "threshold": threshold,
                    "excess": round(amount - threshold, 2),
                    "reason": reason,
                    "policy": "06_business_entertainment.md 第二条"
                })
                counts_by_type["business_entertainment"]["violations"] += 1

        elif expense_type == "office_supplies":
            counts_by_type["office_supplies"]["checked"] += 1
            threshold = 600
            if amount > threshold:
                violations.append({
                    "record_id": record_id,
                    "expense_type": "office_supplies",
                    "amount": amount,
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "employee_level": employee_level,
                    "employee_level_name": LEVEL_NAMES.get(employee_level, employee_level),
                    "threshold": threshold,
                    "excess": round(amount - threshold, 2),
                    "reason": reason,
                    "policy": "07_office_communication.md 第二条"
                })
                counts_by_type["office_supplies"]["violations"] += 1

        elif expense_type == "communication":
            counts_by_type["communication"]["checked"] += 1
            threshold = 300
            if amount > threshold:
                violations.append({
                    "record_id": record_id,
                    "expense_type": "communication",
                    "amount": amount,
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "employee_level": employee_level,
                    "employee_level_name": LEVEL_NAMES.get(employee_level, employee_level),
                    "threshold": threshold,
                    "excess": round(amount - threshold, 2),
                    "reason": reason,
                    "policy": "07_office_communication.md 第三条"
                })
                counts_by_type["communication"]["violations"] += 1

    conn.close()

    total_checked = sum(c["checked"] for c in counts_by_type.values())
    total_violations = sum(c["violations"] for c in counts_by_type.values())

    # Build summary
    violations_by_type = {}
    for etype, counts in counts_by_type.items():
        violations_by_type[etype] = {
            "checked": counts["checked"],
            "violations": counts["violations"]
        }

    findings = {
        "violations": violations,
        "summary": {
            "total_records_scanned": total_checked,
            "total_violations": total_violations,
            "violations_by_type": violations_by_type
        }
    }

    # Save findings
    output_path = os.path.join(OUTPUT_DIR, "findings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)

    # Save summary stats
    stats_path = os.path.join(OUTPUT_DIR, "stats.txt")
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(f"=== L3-003 Single-Transaction Exceedance Analysis ===\n\n")
        f.write(f"Total records scanned: {total_checked}\n")
        f.write(f"Total violations found: {total_violations}\n\n")
        for etype, counts in counts_by_type.items():
            f.write(f"{etype}: {counts['checked']} checked, {counts['violations']} violations\n")
        f.write(f"\n=== Violation Details ===\n\n")
        for v in violations:
            f.write(f"  {v['record_id']} | {v['expense_type']} | amount={v['amount']} | threshold={v['threshold']} | excess={v['excess']} | {v.get('employee_level_name','')} | {v.get('city_tier','')}\n")

    print(f"Analysis complete. {total_checked} records scanned, {total_violations} violations found.")
    print(f"Results saved to {output_path}")
    for etype, counts in counts_by_type.items():
        print(f"  {etype}: {counts['checked']} checked, {counts['violations']} violations")

if __name__ == "__main__":
    main()
