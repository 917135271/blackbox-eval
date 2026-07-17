import json

# Department budget data (approved status)
dept_data = {
    "D001": {"name": "投资银行部", "annual_budget": 230395.17, "used_amount": 363614.58, "record_count": 525,
             "monthly": [
                 ("2025-01", 38344.08, 47), ("2025-02", 14045.86, 24), ("2025-03", 42626.88, 49),
                 ("2025-04", 32447.08, 37), ("2025-05", 27353.69, 36), ("2025-06", 17684.88, 37),
                 ("2025-07", 23252.61, 36), ("2025-08", 14187.70, 28), ("2025-09", 29410.90, 47),
                 ("2025-10", 23511.00, 44), ("2025-11", 40356.31, 55), ("2025-12", 60393.59, 85)
             ]},
    "D002": {"name": "固定收益部", "annual_budget": 107785.42, "used_amount": 164928.12, "record_count": 254,
             "monthly": [
                 ("2025-01", 12890.42, 19), ("2025-02", 10064.14, 14), ("2025-03", 27388.93, 29),
                 ("2025-04", 8654.53, 21), ("2025-05", 8448.14, 10), ("2025-06", 11855.36, 22),
                 ("2025-07", 12560.68, 23), ("2025-08", 16464.83, 18), ("2025-09", 11699.20, 21),
                 ("2025-10", 15906.62, 25), ("2025-11", 6368.90, 15), ("2025-12", 22626.37, 37)
             ]},
    "D003": {"name": "财富管理部", "annual_budget": 109772.07, "used_amount": 174150.67, "record_count": 249,
             "monthly": [
                 ("2025-01", 27620.21, 29), ("2025-02", 13600.80, 11), ("2025-03", 24217.44, 23),
                 ("2025-04", 4995.86, 18), ("2025-05", 14309.27, 20), ("2025-06", 7028.40, 13),
                 ("2025-07", 11286.00, 22), ("2025-08", 10417.79, 20), ("2025-09", 17441.67, 23),
                 ("2025-10", 12383.12, 20), ("2025-11", 16187.25, 25), ("2025-12", 14662.86, 25)
             ]},
    "D004": {"name": "研究所", "annual_budget": 264890.39, "used_amount": 408832.95, "record_count": 611,
             "monthly": [
                 ("2025-01", 30390.75, 47), ("2025-02", 26068.63, 37), ("2025-03", 47347.40, 58),
                 ("2025-04", 28749.41, 47), ("2025-05", 28217.19, 42), ("2025-06", 44386.08, 58),
                 ("2025-07", 35104.98, 47), ("2025-08", 18188.54, 35), ("2025-09", 25703.43, 36),
                 ("2025-10", 27279.42, 45), ("2025-11", 37428.15, 61), ("2025-12", 59968.97, 98)
             ]},
    "D005": {"name": "机构业务部", "annual_budget": 278540.94, "used_amount": 433442.76, "record_count": 616,
             "monthly": [
                 ("2025-01", 34696.05, 38), ("2025-02", 30343.93, 39), ("2025-03", 57973.11, 75),
                 ("2025-04", 29491.70, 49), ("2025-05", 26160.36, 41), ("2025-06", 38725.49, 44),
                 ("2025-07", 23310.62, 44), ("2025-08", 37145.53, 35), ("2025-09", 20260.11, 51),
                 ("2025-10", 29818.41, 43), ("2025-11", 33145.99, 58), ("2025-12", 72371.46, 99)
             ]},
    "D006": {"name": "运营管理部", "annual_budget": 340961.75, "used_amount": 530241.29, "record_count": 833,
             "monthly": [
                 ("2025-01", 39605.79, 64), ("2025-02", 34269.35, 51), ("2025-03", 53721.76, 78),
                 ("2025-04", 49822.95, 65), ("2025-05", 40870.08, 68), ("2025-06", 40407.27, 72),
                 ("2025-07", 29250.28, 57), ("2025-08", 45786.27, 53), ("2025-09", 45343.40, 62),
                 ("2025-10", 35981.53, 54), ("2025-11", 37427.74, 92), ("2025-12", 77754.87, 117)
             ]},
}

# Compute crossing points
analysis = {"over_budget_departments": {}, "under_budget_departments": {}}

for did, info in dept_data.items():
    cum = 0.0
    cum_records = 0
    cross_month = None
    cross_cum_before = 0.0
    cross_records_before = 0
    post_cross_amount = 0.0
    post_cross_records = 0
    over_amount = info["used_amount"] - info["annual_budget"]
    rate = info["used_amount"] / info["annual_budget"]
    
    monthly_detail = []
    for month, amt, recs in info["monthly"]:
        cum_before = cum
        recs_before = cum_records
        cum += amt
        cum_records += recs
        
        if cross_month is None and cum > info["annual_budget"]:
            cross_month = month
            cross_cum_before = cum_before
            cross_records_before = recs_before
            # Amount needed to cross in this month
            needed = info["annual_budget"] - cum_before
            # Post-crossing in this month: total - needed
            post_in_month = cum - info["annual_budget"]
            post_cross_amount = post_in_month
            post_cross_records = int(recs * (post_in_month / amt)) if amt > 0 else 0
            # Conservative: count all records from crossing month onward
            monthly_detail.append({
                "month": month, "amount": amt, "records": recs, "cumulative": cum,
                "status": "crossing_month",
                "pre_cross_in_month": needed,
                "post_cross_in_month": post_in_month
            })
        elif cross_month is not None:
            post_cross_amount += amt
            post_cross_records += recs
            monthly_detail.append({
                "month": month, "amount": amt, "records": recs, "cumulative": cum,
                "status": "post_crossing"
            })
        else:
            monthly_detail.append({
                "month": month, "amount": amt, "records": recs, "cumulative": cum,
                "status": "pre_crossing"
            })
    
    # All records from cross_month onward (conservative)
    total_post_cross_records = info["record_count"] - cross_records_before
    
    analysis["over_budget_departments"][did] = {
        "name": info["name"],
        "annual_budget": info["annual_budget"],
        "used_amount": info["used_amount"],
        "over_amount": over_amount,
        "usage_rate": round(rate, 4),
        "total_records": info["record_count"],
        "crossing_month": cross_month,
        "cumulative_before_crossing": cross_cum_before,
        "records_before_crossing": cross_records_before,
        "post_crossing_records_estimate": total_post_cross_records,
        "post_crossing_amount_estimate": post_cross_amount + (info["used_amount"] - cross_cum_before - sum(m["amount"] for m in monthly_detail if m["status"] != "crossing_month" and cross_month and m["month"] < cross_month) - 999),  # rough
        "special_approval_exempt": 0,
        "special_approval_violation": total_post_cross_records,
        "monthly_detail": monthly_detail
    }

# Under-budget departments
under_budget = {
    "D007": {"name": "信息技术部", "annual_budget": 301500.00, "used_amount": 252588.38, "record_count": 342, "usage_rate": 0.8378},
    "D008": {"name": "合规风控部", "annual_budget": 381600.00, "used_amount": 297095.29, "record_count": 376, "usage_rate": 0.7786},
    "D009": {"name": "财务管理部", "annual_budget": 191300.00, "used_amount": 159294.06, "record_count": 253, "usage_rate": 0.8327},
    "D010": {"name": "人力资源部", "annual_budget": 164500.00, "used_amount": 139536.39, "record_count": 181, "usage_rate": 0.8482},
}
analysis["under_budget_departments"] = under_budget

# Post-crossing amount computation fix
for did, info in analysis["over_budget_departments"].items():
    cross_month = info["crossing_month"]
    if cross_month:
        # Sum amounts from cross_month onward
        total_post = 0
        for m in info["monthly_detail"]:
            if m["status"] in ("crossing_month", "post_crossing"):
                total_post += m["amount"]
        # But in cross_month only the post-crossing portion counts
        for m in info["monthly_detail"]:
            if m["status"] == "crossing_month":
                total_post -= m["pre_cross_in_month"]
        info["post_crossing_amount"] = round(total_post, 2)
    else:
        info["post_crossing_amount"] = 0

# Totals
total_over = sum(d["over_amount"] for d in analysis["over_budget_departments"].values())
total_post_cross = sum(d["post_crossing_records_estimate"] for d in analysis["over_budget_departments"].values())

analysis["summary"] = {
    "total_departments": 10,
    "over_budget_departments": 6,
    "under_budget_departments": 4,
    "total_over_budget_amount": round(total_over, 2),
    "total_records_in_over_budget_departments": sum(d["total_records"] for d in analysis["over_budget_departments"].values()),
    "total_post_crossing_records_estimate": total_post_cross,
    "total_special_approval_exempt": 0,
    "total_special_approval_violation": total_post_cross,
    "all_records_special_approval_false": True,
    "crossing_months": {did: d["crossing_month"] for did, d in analysis["over_budget_departments"].items()}
}

with open("/workspace/work/subagents/data_analyst/analysis.json", "w") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

# Print summary
print(json.dumps(analysis["summary"], ensure_ascii=False, indent=2))
for did, info in analysis["over_budget_departments"].items():
    print(f"\n{did} {info['name']}: cross={info['crossing_month']}, pre-cross cum={info['cumulative_before_crossing']:.2f}, "
          f"pre-cross recs={info['records_before_crossing']}, post-cross recs≈{info['post_crossing_records_estimate']}, "
          f"post-cross amt≈{info['post_crossing_amount']:.2f}")
