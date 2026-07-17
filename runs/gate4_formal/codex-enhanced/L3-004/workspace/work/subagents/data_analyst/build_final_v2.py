import json, os, sys
from collections import defaultdict

# Verified budget data from summarize_department_budgets (status=approved)
BUDGETS = {
    "D001": {"name": "投资银行部", "annual_budget": 230395.17, "used_amount": 363614.58, "record_count": 525},
    "D002": {"name": "固定收益部", "annual_budget": 107785.42, "used_amount": 164928.12, "record_count": 254},
    "D003": {"name": "财富管理部", "annual_budget": 109772.07, "used_amount": 174150.67, "record_count": 249},
    "D004": {"name": "研究所",     "annual_budget": 264890.39, "used_amount": 408832.95, "record_count": 611},
    "D005": {"name": "机构业务部", "annual_budget": 278540.94, "used_amount": 433442.76, "record_count": 616},
    "D006": {"name": "运营管理部", "annual_budget": 340961.75, "used_amount": 530241.29, "record_count": 833},
}

UNDER_BUDGET = {
    "D007": {"name": "信息技术部", "annual_budget": 301500.0, "used_amount": 252588.38, "record_count": 342, "usage_rate": 0.8378},
    "D008": {"name": "合规风控部", "annual_budget": 381600.0, "used_amount": 297095.29, "record_count": 376, "usage_rate": 0.7786},
    "D009": {"name": "财务管理部", "annual_budget": 191300.0, "used_amount": 159294.06, "record_count": 253, "usage_rate": 0.8327},
    "D010": {"name": "人力资源部", "annual_budget": 164500.0, "used_amount": 139536.39, "record_count": 181, "usage_rate": 0.8482},
}

# Monthly data from summarize_expenses (group_by: department_id,month), all have status=approved
# Parsed from the raw output
monthly_raw = {
    # D001
    ("D001","2025-01"): (38344.08, 47), ("D001","2025-02"): (14045.86, 24),
    ("D001","2025-03"): (42626.88, 49), ("D001","2025-04"): (32447.08, 37),
    ("D001","2025-05"): (27353.69, 36), ("D001","2025-06"): (17684.88, 37),
    ("D001","2025-07"): (23252.61, 36), ("D001","2025-08"): (14187.70, 28),
    ("D001","2025-09"): (29410.90, 47), ("D001","2025-10"): (23511.00, 44),
    ("D001","2025-11"): (40356.31, 55), ("D001","2025-12"): (60393.59, 85),
    # D002
    ("D002","2025-01"): (12890.42, 19), ("D002","2025-02"): (10064.14, 14),
    ("D002","2025-03"): (27388.93, 29), ("D002","2025-04"): (8654.53, 21),
    ("D002","2025-05"): (8448.14, 10), ("D002","2025-06"): (11855.36, 22),
    ("D002","2025-07"): (12560.68, 23), ("D002","2025-08"): (16464.83, 18),
    ("D002","2025-09"): (11699.20, 21), ("D002","2025-10"): (15069.98, 24),
    ("D002","2025-11"): (6368.90, 15), ("D002","2025-12"): (23462.97, 18),
    # D003 - fixed from summarize output
    ("D003","2025-01"): (10440.61, 21), ("D003","2025-02"): (13600.80, 11),
    ("D003","2025-03"): (25897.22, 25), ("D003","2025-04"): (4995.86, 18),
    ("D003","2025-05"): (8924.56, 15), ("D003","2025-06"): (7028.40, 13),
    ("D003","2025-07"): (11286.00, 22), ("D003","2025-08"): (10417.79, 20),
    ("D003","2025-09"): (16328.31, 23), ("D003","2025-10"): (12383.12, 20),
    ("D003","2025-11"): (21525.47, 28), ("D003","2025-12"): (31322.53, 33),
    # D004
    ("D004","2025-01"): (30390.75, 47), ("D004","2025-02"): (23556.91, 37),
    ("D004","2025-03"): (47347.40, 58), ("D004","2025-04"): (30310.60, 52),
    ("D004","2025-05"): (25738.68, 44), ("D004","2025-06"): (44386.08, 58),
    ("D004","2025-07"): (35104.98, 47), ("D004","2025-08"): (28206.89, 47),
    ("D004","2025-09"): (29890.89, 49), ("D004","2025-10"): (28661.32, 48),
    ("D004","2025-11"): (37428.15, 61), ("D004","2025-12"): (59968.97, 98),
    # D005
    ("D005","2025-01"): (34696.05, 38), ("D005","2025-02"): (30343.93, 39),
    ("D005","2025-03"): (57973.11, 75), ("D005","2025-04"): (24505.58, 31),
    ("D005","2025-05"): (21262.90, 35), ("D005","2025-06"): (38725.49, 44),
    ("D005","2025-07"): (25781.68, 39), ("D005","2025-08"): (37145.53, 35),
    ("D005","2025-09"): (23427.67, 30), ("D005","2025-10"): (21561.27, 31),
    ("D005","2025-11"): (33145.99, 58), ("D005","2025-12"): (72371.46, 99),
    # D006
    ("D006","2025-01"): (39605.79, 64), ("D006","2025-02"): (34269.35, 51),
    ("D006","2025-03"): (53721.76, 78), ("D006","2025-04"): (49822.95, 65),
    ("D006","2025-05"): (40870.08, 68), ("D006","2025-06"): (40407.27, 72),
    ("D006","2025-07"): (29250.28, 57), ("D006","2025-08"): (45786.27, 53),
    ("D006","2025-09"): (45343.40, 62), ("D006","2025-10"): (35981.53, 54),
    ("D006","2025-11"): (37427.74, 92), ("D006","2025-12"): (77754.87, 117),
}

def compute_crossing(budget, dept_id):
    months = sorted([k for k in monthly_raw if k[0] == dept_id], key=lambda x: x[1])
    cumulative = 0.0
    crossing_month = None
    monthly_detail = []
    pre_crossing_records = 0
    post_crossing_records = 0
    post_crossing_amount = 0.0
    
    for month_key in months:
        amt, recs = monthly_raw[month_key]
        month = month_key[1]
        prev_cum = cumulative
        cumulative += amt
        
        if crossing_month is None and cumulative > budget:
            crossing_month = month
            pre_cross_in_month = budget - prev_cum
            post_cross_in_month = cumulative - budget
            status = "crossing_month"
        elif crossing_month and month > crossing_month:
            status = "post_crossing"
        elif crossing_month and month == crossing_month:
            status = "crossing_month"
        else:
            status = "pre_crossing"
            pre_crossing_records += recs
            
        if status == "post_crossing":
            post_crossing_records += recs
            post_crossing_amount += amt
        elif status == "crossing_month":
            post_crossing_records += recs
            post_crossing_amount += amt
            
        entry = {
            "month": month,
            "amount": round(amt, 2),
            "records": recs,
            "cumulative": round(cumulative, 2),
            "status": status
        }
        if status == "crossing_month":
            entry["pre_cross_in_month"] = round(budget - prev_cum, 2)
            entry["post_cross_in_month"] = round(cumulative - budget, 2)
        monthly_detail.append(entry)
    
    return {
        "crossing_month": crossing_month,
        "pre_crossing_records": pre_crossing_records,
        "post_crossing_records": post_crossing_records,
        "post_crossing_amount": round(post_crossing_amount, 2),
        "monthly_detail": monthly_detail
    }

# Build analysis
analysis = {"over_budget_departments": {}, "under_budget_departments": UNDER_BUDGET}

total_over = 0.0
total_records = 0
total_post_crossing = 0

for dept_id, info in BUDGETS.items():
    crossing = compute_crossing(info["annual_budget"], dept_id)
    over_amount = info["used_amount"] - info["annual_budget"]
    usage_rate = info["used_amount"] / info["annual_budget"]
    
    # Verify monthly totals
    dept_monthly = sum(v[0] for k, v in monthly_raw.items() if k[0] == dept_id)
    dept_records = sum(v[1] for k, v in monthly_raw.items() if k[0] == dept_id)
    
    analysis["over_budget_departments"][dept_id] = {
        "name": info["name"],
        "annual_budget": info["annual_budget"],
        "used_amount": info["used_amount"],
        "over_amount": round(over_amount, 2),
        "usage_rate": round(usage_rate, 4),
        "total_records": info["record_count"],
        "monthly_total_amount": round(dept_monthly, 2),
        "monthly_total_records": dept_records,
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

os.makedirs("/workspace/work/subagents/data_analyst", exist_ok=True)
with open("/workspace/work/subagents/data_analyst/analysis.json", "w") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

print("=== Budget Overrun Analysis Summary ===")
print(f"Total over-budget departments: 6")
print(f"Total over-budget amount: {round(total_over, 2)}")
print(f"Total records in over-budget depts: {total_records}")
print(f"Total post-crossing records (violations): {total_post_crossing}")
print()

for did in BUDGETS:
    d = analysis["over_budget_departments"][did]
    msum = d["monthly_total_amount"]
    print(f"{did} {d['name']}: budget={d['annual_budget']}, used={d['used_amount']}, "
          f"monthly_sum={msum}, delta={round(d['used_amount']-msum,2)}, "
          f"over={d['over_amount']}, crossing={d['crossing_month']}, "
          f"post_x_recs={d['post_crossing_records']}")
    # Verify monthly records tally
    mrecs = d["monthly_total_records"]
    if mrecs != d["total_records"]:
        print(f"  *** RECORD COUNT MISMATCH: monthly={mrecs}, budget_api={d['total_records']}")

print()
print("Monthly verification complete.")
