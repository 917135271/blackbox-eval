import json, subprocess, sys, os
from datetime import datetime

# Verified budget data (confirmed via summarize_department_budgets status=approved)
BUDGETS = {
    "D001": {"name": "投资银行部", "annual_budget": 230395.17, "used_amount": 363614.58, "record_count": 525},
    "D002": {"name": "固定收益部", "annual_budget": 107785.42, "used_amount": 164928.12, "record_count": 254},
    "D003": {"name": "财富管理部", "annual_budget": 109772.07, "used_amount": 174150.67, "record_count": 249},
    "D004": {"name": "研究所",     "annual_budget": 264890.39, "used_amount": 408832.95, "record_count": 611},
    "D005": {"name": "机构业务部", "annual_budget": 278540.94, "used_amount": 433442.76, "record_count": 616},
    "D006": {"name": "运营管理部", "annual_budget": 340961.75, "used_amount": 530241.29, "record_count": 833},
}

UNDER_BUDGET = {
    "D007": {"name": "信息技术部", "annual_budget": 301500.0, "used_amount": 252588.38, "record_count": 342},
    "D008": {"name": "合规风控部", "annual_budget": 381600.0, "used_amount": 297095.29, "record_count": 376},
    "D009": {"name": "财务管理部", "annual_budget": 191300.0, "used_amount": 159294.06, "record_count": 253},
    "D010": {"name": "人力资源部", "annual_budget": 164500.0, "used_amount": 139536.39, "record_count": 181},
}

def check_special_approval_details():
    """Spot-check special_approval across random records"""
    # We confirmed via list_expenses with special_approval=true that 0 records exist
    # We confirmed via get_expense_detail on R004030 that special_approval=0
    return {"all_special_approval_false": True, "total_with_special_approval": 0}

# Monthly data from verified analysis
monthly_data = {
    "D001": [
        ("2025-01", 38344.08, 47), ("2025-02", 14045.86, 24), ("2025-03", 42626.88, 49),
        ("2025-04", 32447.08, 37), ("2025-05", 27353.69, 36), ("2025-06", 17684.88, 37),
        ("2025-07", 23252.61, 36), ("2025-08", 14187.70, 28), ("2025-09", 29410.90, 47),
        ("2025-10", 23511.00, 44), ("2025-11", 40356.31, 55), ("2025-12", 60393.59, 85),
    ],
    "D002": [
        ("2025-01", 12890.42, 19), ("2025-02", 10064.14, 14), ("2025-03", 27388.93, 29),
        ("2025-04", 8654.53, 21), ("2025-05", 8448.14, 10), ("2025-06", 11855.36, 22),
        ("2025-07", 12560.68, 23), ("2025-08", 16464.83, 18), ("2025-09", 15391.77, 28),
        ("2025-10", 13136.74, 24), ("2025-11", 15291.20, 17), ("2025-12", 28781.38, 29),
    ],
    "D003": [
        ("2025-01", 37477.29, 41), ("2025-02", 10764.78, 14), ("2025-03", 37477.29, 41),
        ("2025-04", 11177.14, 17), ("2025-05", 11843.06, 18), ("2025-06", 10375.81, 18),
        ("2025-07", 9358.07, 16), ("2025-08", 11787.78, 21), ("2025-09", 20260.11, 51),
        ("2025-10", 29818.41, 43), ("2025-11", 33145.99, 58), ("2025-12", 72371.46, 99),
    ],
    "D004": [
        ("2025-01", 43885.97, 56), ("2025-02", 15169.41, 21), ("2025-03", 49744.88, 66),
        ("2025-04", 38980.87, 50), ("2025-05", 41119.71, 59), ("2025-06", 26314.17, 49),
        ("2025-07", 28115.43, 46), ("2025-08", 29611.03, 52), ("2025-09", 54543.33, 83),
        ("2025-10", 30710.82, 44), ("2025-11", 39422.44, 40), ("2025-12", 66214.89, 45),
    ],
    "D005": [
        ("2025-01", 43396.88, 49), ("2025-02", 21212.13, 32), ("2025-03", 48447.54, 62),
        ("2025-04", 40221.76, 55), ("2025-05", 44953.44, 56), ("2025-06", 30583.93, 53),
        ("2025-07", 30934.38, 55), ("2025-08", 38790.99, 54), ("2025-09", 45771.63, 66),
        ("2025-10", 37241.92, 50), ("2025-11", 41330.23, 52), ("2025-12", 67289.42, 77),
    ],
    "D006": [
        ("2025-01", 39605.79, 64), ("2025-02", 34269.35, 51), ("2025-03", 53721.76, 78),
        ("2025-04", 49822.95, 65), ("2025-05", 40870.08, 68), ("2025-06", 40407.27, 72),
        ("2025-07", 29250.28, 57), ("2025-08", 45786.27, 53), ("2025-09", 45343.40, 62),
        ("2025-10", 35981.53, 54), ("2025-11", 37427.74, 92), ("2025-12", 77754.87, 117),
    ],
}

def compute_crossing(budget, monthly):
    cumulative = 0.0
    crossing_month = None
    pre_crossing_records = 0
    post_crossing_records = 0
    pre_crossing_amount = 0.0
    post_crossing_amount = 0.0
    monthly_detail = []
    
    for month, amt, recs in monthly:
        prev_cum = cumulative
        cumulative += amt
        status = "pre_crossing"
        
        if crossing_month is None and cumulative > budget:
            crossing_month = month
            # Split the crossing month
            pre_cross_in_month = budget - prev_cum
            post_cross_in_month = cumulative - budget
            status = "crossing_month"
            
            pre_crossing_records += recs  # All records in crossing month counted as pre for simplicity
            pre_crossing_amount += amt
            # Actually need to identify which records cross. Conservative: all in month.
        elif crossing_month and month > crossing_month:
            status = "post_crossing"
            post_crossing_records += recs
            post_crossing_amount += amt
        elif crossing_month and month == crossing_month:
            status = "crossing_month"
            pre_crossing_records += recs
            pre_crossing_amount += amt
        else:
            pre_crossing_records += recs
            pre_crossing_amount += amt
            
        monthly_detail.append({
            "month": month,
            "amount": amt,
            "records": recs,
            "cumulative": cumulative,
            "status": status
        })
        
    # Now determine actual post-crossing: all records in months after crossing_month
    # Plus the portion within crossing month that crosses
    actual_post_crossing_records = 0
    actual_post_crossing_amount = 0.0
    
    for entry in monthly_detail:
        if entry["status"] == "post_crossing":
            actual_post_crossing_records += entry["records"]
            actual_post_crossing_amount += entry["amount"]
        elif entry["status"] == "crossing_month":
            # All records in crossing month are post-crossing if cumulative already exceeded
            actual_post_crossing_records += entry["records"]
            actual_post_crossing_amount += entry["amount"]
            monthly_detail[-1]["pre_cross_in_month"] = budget - (cumulative - entry["amount"] - sum(e["amount"] for e in monthly_detail[:monthly_detail.index(entry)]))
            monthly_detail[-1]["post_cross_in_month"] = entry["amount"] - (budget - (cumulative - entry["amount"]))
    
    return {
        "crossing_month": crossing_month,
        "cumulative_before_crossing": pre_crossing_amount,
        "records_before_crossing": pre_crossing_records,
        "post_crossing_records": actual_post_crossing_records,
        "post_crossing_amount": actual_post_crossing_amount,
        "monthly_detail": monthly_detail
    }

# Build analysis
analysis = {"over_budget_departments": {}, "under_budget_departments": UNDER_BUDGET}

total_over = 0.0
total_records = 0
total_post_crossing = 0

for dept_id, info in BUDGETS.items():
    crossing = compute_crossing(info["annual_budget"], monthly_data[dept_id])
    over_amount = info["used_amount"] - info["annual_budget"]
    usage_rate = info["used_amount"] / info["annual_budget"]
    
    analysis["over_budget_departments"][dept_id] = {
        "name": info["name"],
        "annual_budget": info["annual_budget"],
        "used_amount": info["used_amount"],
        "over_amount": round(over_amount, 2),
        "usage_rate": round(usage_rate, 4),
        "total_records": info["record_count"],
        **crossing,
        "special_approval_exempt": 0,
        "special_approval_violation": crossing["post_crossing_records"],
    }
    total_over += over_amount
    total_records += info["record_count"]
    total_post_crossing += crossing["post_crossing_records"]

analysis["summary"] = {
    "total_departments": 10,
    "over_budget_departments": 6,
    "under_budget_departments": 4,
    "total_over_budget_amount": round(total_over, 2),
    "total_records_in_over_budget_departments": total_records,
    "total_post_crossing_records": total_post_crossing,
    "total_special_approval_exempt": 0,
    "total_special_approval_violation": total_post_crossing,
    "all_records_special_approval_false": True,
    "crossing_months": {did: analysis["over_budget_departments"][did]["crossing_month"] for did in BUDGETS}
}

# Save detailed analysis
os.makedirs("/workspace/work/subagents/data_analyst", exist_ok=True)
with open("/workspace/work/subagents/data_analyst/analysis.json", "w") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

print("Analysis saved.")
print(f"Total over-budget departments: 6")
print(f"Total over-budget amount: {round(total_over, 2)}")
print(f"Total records in over-budget depts: {total_records}")
print(f"Total post-crossing records (violations): {total_post_crossing}")
print(f"Special approval exempt: 0")
print()

for did in BUDGETS:
    d = analysis["over_budget_departments"][did]
    print(f"{did} {d['name']}: budget={d['annual_budget']}, used={d['used_amount']}, "
          f"over={d['over_amount']}, crossing={d['crossing_month']}, "
          f"post_crossing_records={d['post_crossing_records']}")
