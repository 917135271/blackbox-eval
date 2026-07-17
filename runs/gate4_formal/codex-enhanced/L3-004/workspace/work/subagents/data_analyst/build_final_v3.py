import json, os

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

# Verified monthly data (from per-department summarize_expenses, ordered by month)
monthly = {
    "D001": [("2025-01",38344.08,47),("2025-02",14045.86,24),("2025-03",42626.88,49),
             ("2025-04",32447.08,37),("2025-05",27353.69,36),("2025-06",17684.88,37),
             ("2025-07",23252.61,36),("2025-08",14187.70,28),("2025-09",29410.90,47),
             ("2025-10",23511.00,44),("2025-11",40356.31,55),("2025-12",60393.59,85)],
    "D002": [("2025-01",12890.42,19),("2025-02",10064.14,14),("2025-03",27388.93,29),
             ("2025-04",8654.53,21),("2025-05",8448.14,10),("2025-06",11855.36,22),
             ("2025-07",12560.68,23),("2025-08",16464.83,18),("2025-09",11699.20,21),
             ("2025-10",15906.62,25),("2025-11",6368.90,15),("2025-12",22626.37,37)],
    "D003": [("2025-01",27620.21,29),("2025-02",13600.80,11),("2025-03",24217.44,23),
             ("2025-04",4995.86,18),("2025-05",14309.27,20),("2025-06",7028.40,13),
             ("2025-07",11286.00,22),("2025-08",10417.79,20),("2025-09",17441.67,23),
             ("2025-10",12383.12,20),("2025-11",16187.25,25),("2025-12",14662.86,25)],
    "D004": [("2025-01",30390.75,47),("2025-02",26068.63,37),("2025-03",47347.40,58),
             ("2025-04",28749.41,47),("2025-05",28217.19,42),("2025-06",44386.08,58),
             ("2025-07",35104.98,47),("2025-08",18188.54,35),("2025-09",25703.43,36),
             ("2025-10",27279.42,45),("2025-11",37428.15,61),("2025-12",59968.97,98)],
    "D005": [("2025-01",34696.05,38),("2025-02",30343.93,39),("2025-03",57973.11,75),
             ("2025-04",29491.70,49),("2025-05",26160.36,41),("2025-06",38725.49,44),
             ("2025-07",23310.62,44),("2025-08",37145.53,35),("2025-09",20260.11,51),
             ("2025-10",29818.41,43),("2025-11",33145.99,58),("2025-12",72371.46,99)],
    "D006": [("2025-01",39605.79,64),("2025-02",34269.35,51),("2025-03",53721.76,78),
             ("2025-04",49822.95,65),("2025-05",40870.08,68),("2025-06",40407.27,72),
             ("2025-07",29250.28,57),("2025-08",45786.27,53),("2025-09",45343.40,62),
             ("2025-10",35981.53,54),("2025-11",37427.74,92),("2025-12",77754.87,117)],
}

def compute_crossing(dept_id, budget):
    data = monthly[dept_id]
    cumulative = 0.0
    crossing_month = None
    monthly_detail = []
    post_crossing_records = 0
    post_crossing_amount = 0.0
    
    for month, amt, recs in data:
        prev_cum = cumulative
        cumulative += amt
        
        if crossing_month is None and cumulative > budget:
            crossing_month = month
            status = "crossing_month"
            pre_in_month = round(budget - prev_cum, 2)
            post_in_month = round(cumulative - budget, 2)
        elif crossing_month and month > crossing_month:
            status = "post_crossing"
        elif crossing_month and month == crossing_month:
            status = "crossing_month"
        else:
            status = "pre_crossing"
        
        entry = {"month": month, "amount": round(amt,2), "records": recs,
                 "cumulative": round(cumulative,2), "status": status}
        if status == "crossing_month":
            entry["pre_cross_in_month"] = pre_in_month
            entry["post_cross_in_month"] = post_in_month
        
        monthly_detail.append(entry)
        
        if status in ("post_crossing", "crossing_month") and crossing_month:
            post_crossing_records += recs
            post_crossing_amount += amt
    
    return crossing_month, monthly_detail, post_crossing_records, round(post_crossing_amount, 2)

analysis = {"over_budget_departments": {}, "under_budget_departments": UNDER_BUDGET}
total_over = 0.0
total_post_crossing = 0
crossing_months = {}

for did, info in BUDGETS.items():
    cm, md, pc_recs, pc_amt = compute_crossing(did, info["annual_budget"])
    over = round(info["used_amount"] - info["annual_budget"], 2)
    ur = round(info["used_amount"] / info["annual_budget"], 4)
    
    analysis["over_budget_departments"][did] = {
        "name": info["name"],
        "annual_budget": info["annual_budget"],
        "used_amount": info["used_amount"],
        "over_amount": over,
        "usage_rate": ur,
        "total_records": info["record_count"],
        "crossing_month": cm,
        "post_crossing_records": pc_recs,
        "post_crossing_amount": pc_amt,
        "special_approval_exempt": 0,
        "special_approval_violation": pc_recs,
        "monthly_detail": md
    }
    total_over += over
    total_post_crossing += pc_recs
    crossing_months[did] = cm

analysis["summary"] = {
    "total_departments": 10,
    "over_budget_departments": 6,
    "under_budget_departments": 4,
    "total_over_budget_amount": round(total_over, 2),
    "total_records_in_over_budget_departments": sum(d["record_count"] for d in BUDGETS.values()),
    "total_post_crossing_records": total_post_crossing,
    "total_special_approval_exempt": 0,
    "total_special_approval_violation": total_post_crossing,
    "all_records_special_approval_false": True,
    "crossing_months": crossing_months
}

os.makedirs("/workspace/work/subagents/data_analyst", exist_ok=True)
with open("/workspace/work/subagents/data_analyst/analysis.json", "w") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

# Now build summary.json
summary = {
    "decision": "reject",
    "key_findings": [
        f"全年共6个部门超预算: D001(投资银行部,超{analysis['over_budget_departments']['D001']['over_amount']}元), D002(固定收益部,超{analysis['over_budget_departments']['D002']['over_amount']}元), D003(财富管理部,超{analysis['over_budget_departments']['D003']['over_amount']}元), D004(研究所,超{analysis['over_budget_departments']['D004']['over_amount']}元), D005(机构业务部,超{analysis['over_budget_departments']['D005']['over_amount']}元), D006(运营管理部,超{analysis['over_budget_departments']['D006']['over_amount']}元)",
        f"超预算总额: {round(total_over, 2)}元",
        f"超预算部门共{sum(d['record_count'] for d in BUDGETS.values())}条报销记录",
        f"其中{total_post_crossing}条记录发生在预算额度用尽后(即违规记录)",
        "所有记录special_approval均为0(否),无豁免记录",
        "预算用尽月份: D001-2025年9月, D002-2025年8月, D003-2025年8月, D004-2025年9月, D005-2025年9月, D006-2025年9月",
        "4个部门在预算范围内: D007(信息技术部), D008(合规风控部), D009(财务管理部), D010(人力资源部)"
    ],
    "record_ids": [],  # Will be populated with post-crossing record IDs
    "citations": [
        {"doc_id": "08_budget_management.md", "clause_no": "第2条"},
        {"doc_id": "08_budget_management.md", "clause_no": "第3条"},
        {"doc_id": "08_budget_management.md", "clause_no": "第4条"}
    ],
    "unresolved_items": ["record_ids字段需要从分页查询中填充所有post-crossing记录的具体record_id"],
    "artifact_paths": [
        "work/subagents/data_analyst/analysis.json",
        "work/subagents/data_analyst/summary.json"
    ]
}

with open("/workspace/work/subagents/data_analyst/summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("Analysis and summary built successfully.")
print(f"Crossing months: {crossing_months}")
print(f"Total post-crossing: {total_post_crossing}")
print(f"Total over amount: {round(total_over, 2)}")
