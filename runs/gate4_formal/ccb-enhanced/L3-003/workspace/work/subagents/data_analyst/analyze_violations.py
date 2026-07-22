#!/usr/bin/env python3
"""
L3-003: Single-transaction threshold exceedance scan.
Scans all 4240 approved expense records for single-transaction exceedances
against type-specific thresholds.
"""

import sqlite3
import json
import re
from collections import defaultdict

DB_PATH = "/benchmark/data/expense.db"
OUTPUT_PATH = "/workspace/work/subagents/data_analyst/findings.json"
DETAIL_PATH = "/workspace/work/subagents/data_analyst/detailed_analysis.json"

# City tier keywords
TIER1_CITIES = ["上海", "北京", "深圳"]
TIER2_CITIES = [
    "杭州", "广州", "成都", "南京", "武汉", "重庆", "天津", "苏州",
    "西安", "长沙", "青岛", "大连", "厦门", "宁波", "福州", "合肥",
    "郑州", "济南", "无锡", "佛山", "东莞"
]

# Travel lodging per-night caps: (employee_level, city_tier) -> cap
LODGING_CAPS = {
    ("E1", "一类"): 450,
    ("E1", "二类"): 380,
    ("E1", "三类"): 300,
    ("M1", "一类"): 650,
    ("M1", "二类"): 550,
    ("M1", "三类"): 450,
    ("D1", "一类"): 850,
    ("D1", "二类"): 700,
    ("D1", "三类"): 600,
    ("X1", "一类"): 1100,
    ("X1", "二类"): 900,
    ("X1", "三类"): 750,
}

# Local transport daily caps by city_tier
TRANSPORT_CAPS = {
    "一类": 120,
    "二类": 100,
    "三类": 80,
}


def extract_city_tier(reason):
    """Extract city tier from reason text using keyword matching."""
    for city in TIER1_CITIES:
        if city in reason:
            return "一类", city
    for city in TIER2_CITIES:
        if city in reason:
            return "二类", city
    return "三类", None


def check_travel_lodging(record, emp_level):
    """Check per-night cap for travel_lodging."""
    amount = record["amount"]
    nights = record["nights"]
    reason = record["reason"]
    rec_id = record["record_id"]

    if nights is None or nights <= 0:
        return None

    per_night = amount / nights
    city_tier, city = extract_city_tier(reason)

    key = (emp_level, city_tier)
    cap = LODGING_CAPS.get(key)

    if cap is None:
        return None

    if per_night > cap:
        return {
            "record_id": rec_id,
            "expense_type": "travel_lodging",
            "amount": round(amount, 2),
            "per_night": round(per_night, 2),
            "nights": nights,
            "employee_id": record["employee_id"],
            "employee_level": emp_level,
            "city_tier": city_tier,
            "city_matched": city,
            "threshold": cap,
            "excess": round(per_night - cap, 2),
            "reason": reason,
            "policy": "04_travel_expense.md 第四条",
            "detail": f"per_night={per_night:.2f} > cap={cap} (nights={nights})"
        }
    return None


def check_local_transport(record, emp_level):
    """Check daily cap for local_transport."""
    amount = record["amount"]
    days = record["days"]
    reason = record["reason"]
    rec_id = record["record_id"]

    if days is None or days <= 0:
        return None

    per_day = amount / days
    city_tier, city = extract_city_tier(reason)
    cap = TRANSPORT_CAPS[city_tier]

    if per_day > cap:
        return {
            "record_id": rec_id,
            "expense_type": "local_transport",
            "amount": round(amount, 2),
            "per_day": round(per_day, 2),
            "days": days,
            "employee_id": record["employee_id"],
            "employee_level": emp_level,
            "city_tier": city_tier,
            "city_matched": city,
            "threshold": cap,
            "excess": round(per_day - cap, 2),
            "reason": reason,
            "policy": "04_travel_expense.md 第六条",
            "detail": f"per_day={per_day:.2f} > cap={cap} (days={days})"
        }
    return None


def check_training_fee(record, emp_level):
    """Check per person per session <= 3500."""
    amount = record["amount"]
    if amount > 3500:
        return {
            "record_id": record["record_id"],
            "expense_type": "training_fee",
            "amount": round(amount, 2),
            "employee_id": record["employee_id"],
            "employee_level": emp_level,
            "city_tier": None,
            "city_matched": None,
            "threshold": 3500,
            "excess": round(amount - 3500, 2),
            "reason": record["reason"],
            "policy": "05_training_expense.md 第二条",
            "detail": f"amount={amount:.2f} > 3500"
        }
    return None


def check_business_entertainment(record, emp_level):
    """Check per event <= 5000."""
    amount = record["amount"]
    if amount > 5000:
        return {
            "record_id": record["record_id"],
            "expense_type": "business_entertainment",
            "amount": round(amount, 2),
            "employee_id": record["employee_id"],
            "employee_level": emp_level,
            "city_tier": None,
            "city_matched": None,
            "threshold": 5000,
            "excess": round(amount - 5000, 2),
            "reason": record["reason"],
            "policy": "06_business_entertainment.md 第二条",
            "detail": f"amount={amount:.2f} > 5000"
        }
    return None


def check_office_supplies(record, emp_level):
    """Check single transaction > 600."""
    amount = record["amount"]
    if amount > 600:
        return {
            "record_id": record["record_id"],
            "expense_type": "office_supplies",
            "amount": round(amount, 2),
            "employee_id": record["employee_id"],
            "employee_level": emp_level,
            "city_tier": None,
            "city_matched": None,
            "threshold": 600,
            "excess": round(amount - 600, 2),
            "reason": record["reason"],
            "policy": "07_office_communication.md 第二条",
            "detail": f"amount={amount:.2f} > 600"
        }
    return None


def check_communication(record, emp_level):
    """Check single transaction > 300."""
    amount = record["amount"]
    if amount > 300:
        return {
            "record_id": record["record_id"],
            "expense_type": "communication",
            "amount": round(amount, 2),
            "employee_id": record["employee_id"],
            "employee_level": emp_level,
            "city_tier": None,
            "city_matched": None,
            "threshold": 300,
            "excess": round(amount - 300, 2),
            "reason": record["reason"],
            "policy": "07_office_communication.md 第三条",
            "detail": f"amount={amount:.2f} > 300"
        }
    return None


CHECKERS = {
    "travel_lodging": check_travel_lodging,
    "local_transport": check_local_transport,
    "training_fee": check_training_fee,
    "business_entertainment": check_business_entertainment,
    "office_supplies": check_office_supplies,
    "communication": check_communication,
}


def main():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # Load employees
    emp_levels = {}
    for row in conn.execute("SELECT employee_id, employee_level FROM employees"):
        emp_levels[row["employee_id"]] = row["employee_level"]

    # Query all approved records
    query = """
    SELECT record_id, employee_id, expense_type, amount, reason,
           nights, days, expense_date, reimburse_date
    FROM expense_records
    WHERE status = 'approved'
    ORDER BY record_id
    """

    cursor = conn.execute(query)
    violations = []
    violations_by_type = defaultdict(int)
    total_scanned = 0
    skipped_no_level = 0
    skipped_no_nights = 0
    skipped_no_days = 0

    for row in cursor:
        total_scanned += 1
        record = {
            "record_id": row["record_id"],
            "employee_id": row["employee_id"],
            "expense_type": row["expense_type"],
            "amount": row["amount"],
            "reason": row["reason"],
            "nights": row["nights"],
            "days": row["days"],
            "expense_date": row["expense_date"],
        }

        expense_type = record["expense_type"]
        emp_id = record["employee_id"]
        emp_level = emp_levels.get(emp_id)

        if emp_level is None:
            skipped_no_level += 1
            continue

        checker = CHECKERS.get(expense_type)
        if checker is None:
            continue

        result = checker(record, emp_level)
        if result is not None:
            violations.append(result)
            violations_by_type[expense_type] += 1

    conn.close()

    # Sort violations by expense_type then excess descending
    violations.sort(key=lambda v: (v["expense_type"], -v["excess"]))

    # Build summary
    summary = {
        "total_records_scanned": total_scanned,
        "violations_by_type": dict(violations_by_type),
        "total_violations": len(violations),
        "skipped_no_employee_level": skipped_no_level,
        "skipped_no_nights_or_days": skipped_no_nights + skipped_no_days,
    }

    # Violations by type with excess stats
    for vtype in sorted(violations_by_type.keys()):
        type_violations = [v for v in violations if v["expense_type"] == vtype]
        excesses = [v["excess"] for v in type_violations]
        summary[f"{vtype}_max_excess"] = round(max(excesses), 2) if excesses else 0

    output = {
        "violations": violations,
        "summary": summary,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Write detailed analysis
    detail = {
        "analysis_info": {
            "task": "L3-003",
            "description": "Single-transaction threshold exceedance scan",
            "total_records": total_scanned,
            "violation_count": len(violations),
        },
        "thresholds_applied": {
            "travel_lodging": "Per-night cap by employee_level x city_tier (04_travel_expense.md 第四条)",
            "local_transport": "Daily cap by city_tier: 一类120/二类100/三类80 (04_travel_expense.md 第六条)",
            "training_fee": "Per person per session <= 3500 (05_training_expense.md 第二条)",
            "business_entertainment": "Per event <= 5000 (06_business_entertainment.md 第二条)",
            "office_supplies": "Single transaction > 600 (07_office_communication.md 第二条)",
            "communication": "Single transaction > 300 (07_office_communication.md 第三条)",
        },
        "violations_by_type": dict(violations_by_type),
        "city_tier_extraction": {
            "method": "Keyword matching from reason field",
            "tier1": TIER1_CITIES,
            "tier2": TIER2_CITIES,
            "tier3": "All other cities or no city mentioned",
        },
    }

    with open(DETAIL_PATH, "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)

    # Print summary to stdout
    print(f"=== L3-003 Analysis Complete ===")
    print(f"Total records scanned: {total_scanned}")
    print(f"Total violations found: {len(violations)}")
    print(f"Violations by type:")
    for vtype, count in sorted(violations_by_type.items()):
        print(f"  {vtype}: {count}")
    print(f"\nOutput written to: {OUTPUT_PATH}")
    print(f"Detail written to: {DETAIL_PATH}")
    print(f"\nTop violations per type:")
    for vtype in sorted(violations_by_type.keys()):
        type_violations = [v for v in violations if v["expense_type"] == vtype]
        top3 = sorted(type_violations, key=lambda v: -v["excess"])[:3]
        print(f"\n  {vtype}:")
        for v in top3:
            print(f"    {v['record_id']}: {v['detail']} [excess={v['excess']}]")


if __name__ == "__main__":
    main()
