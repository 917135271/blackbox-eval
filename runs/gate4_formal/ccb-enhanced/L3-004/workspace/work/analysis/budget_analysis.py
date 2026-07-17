#!/usr/bin/env python3
"""超预算专项扫描 - 全年累计预算分析
规则：部门年度累计费用超过年度预算1.0倍后，未经专项审批的报销记录构成超预算违规。
"""

import sqlite3
import json

DB_PATH = "/benchmark/data/expense.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# 获取所有部门预算
dept_budgets = {}
for row in conn.execute("SELECT department_id, department_name, annual_budget FROM departments"):
    dept_budgets[row["department_id"]] = {
        "name": row["department_name"],
        "budget": row["annual_budget"]
    }

# 获取所有2025年记录，按部门、日期、record_id排序
records = conn.execute("""
    SELECT record_id, department_id, expense_date, amount, special_approval
    FROM expense_records
    WHERE budget_year = 2025
    ORDER BY department_id, expense_date ASC, record_id ASC
""").fetchall()

conn.close()

# 按部门计算累计
results = {}
for dept_id, info in dept_budgets.items():
    results[dept_id] = {
        "department_name": info["name"],
        "annual_budget": info["budget"],
        "total_records": 0,
        "total_amount": 0.0,
        "anomaly_records": [],
        "pre_budget_records": [],
        "crossing_record": None,
        "cumulative_final": 0.0
    }

budget_violations = []  # (dept_id, dept_name, crossing_record, post_records)

for dept_id in dept_budgets:
    dept_records = [r for r in records if r["department_id"] == dept_id]
    budget = dept_budgets[dept_id]["budget"]
    cumulative = 0.0
    crossed = False
    crossing_record = None
    post_records = []
    pre_records = []
    total_amount = 0.0

    for rec in dept_records:
        amount = rec["amount"]
        total_amount += amount
        cumulative_before = cumulative
        cumulative += amount

        if not crossed:
            if cumulative > budget:
                # This record pushed the cumulative over budget
                crossed = True
                crossing_record = {
                    "record_id": rec["record_id"],
                    "expense_date": rec["expense_date"],
                    "amount": amount,
                    "cumulative_before": round(cumulative_before, 2),
                    "cumulative_after": round(cumulative, 2),
                    "special_approval": rec["special_approval"]
                }
            else:
                pre_records.append(rec["record_id"])
        else:
            post_records.append({
                "record_id": rec["record_id"],
                "expense_date": rec["expense_date"],
                "amount": amount,
                "cumulative_at_record": round(cumulative, 2),
                "special_approval": rec["special_approval"]
            })

    results[dept_id]["total_records"] = len(dept_records)
    results[dept_id]["total_amount"] = round(total_amount, 2)
    results[dept_id]["cumulative_final"] = round(cumulative, 2)
    results[dept_id]["crossing_record"] = crossing_record
    results[dept_id]["pre_budget_records"] = pre_records
    results[dept_id]["over_budget"] = cumulative > budget

    if crossing_record is not None:
        anomaly_recs = []
        # crossing record
        if crossing_record["special_approval"] == 0:
            anomaly_recs.append(crossing_record)
        else:
            anomaly_recs.append({**crossing_record, "exempted": True})

        # post records
        for pr in post_records:
            if pr["special_approval"] == 0:
                anomaly_recs.append(pr)
            else:
                anomaly_recs.append({**pr, "exempted": True})

        results[dept_id]["anomaly_records"] = anomaly_recs

    usage_rate = round(cumulative / budget, 4) if budget > 0 else 0
    results[dept_id]["usage_rate"] = usage_rate

# 输出分析结果
over_budget_depts = {k: v for k, v in results.items() if v["over_budget"]}
under_budget_depts = {k: v for k, v in results.items() if not v["over_budget"]}

print("=" * 80)
print("超预算专项扫描 - 分析结果")
print("=" * 80)

print("\n--- 超预算部门 ---")
total_violations = 0
for dept_id, info in over_budget_depts.items():
    anom_count = len([r for r in info["anomaly_records"] if not r.get("exempted")])
    exempt_count = len([r for r in info["anomaly_records"] if r.get("exempted")])
    total_violations += anom_count
    cr = info["crossing_record"]
    print(f"\n{dept_id} {info['department_name']}:")
    print(f"  预算: {info['annual_budget']:,.2f}, 累计: {info['cumulative_final']:,.2f}, 使用率: {info['usage_rate']*100:.2f}%")
    if cr:
        print(f"  穿越阈值记录: {cr['record_id']} (日期: {cr['expense_date']}, 金额: {cr['amount']:,.2f}, 累计前: {cr['cumulative_before']:,.2f}, 累计后: {cr['cumulative_after']:,.2f})")
    print(f"  异常记录数: {anom_count}, 豁免记录数: {exempt_count}")

print(f"\n总违规记录数: {total_violations}")

print("\n--- 未超预算部门 ---")
for dept_id, info in under_budget_depts.items():
    print(f"{dept_id} {info['department_name']}: 预算 {info['annual_budget']:,.2f}, 累计 {info['cumulative_final']:,.2f}, 使用率 {info['usage_rate']*100:.2f}%")

# 保存详细结果
analysis_output = {
    "task": "全年超预算专项扫描",
    "audit_period": "2025-01-01 至 2025-12-31",
    "rule": "部门年度累计费用超过年度预算1.0倍后不得继续报销，专项审批豁免",
    "policy_citations": [
        {"doc_id": "08_budget_management.md", "clause_no": "第三条"},
        {"doc_id": "08_budget_management.md", "clause_no": "第四条"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十三条"}
    ],
    "total_population": 4240,
    "summary": {
        "over_budget_departments": list(over_budget_depts.keys()),
        "under_budget_departments": list(under_budget_depts.keys()),
        "total_violation_records": total_violations
    },
    "departments": {}
}

for dept_id, info in results.items():
    anom_ids = [r["record_id"] for r in info["anomaly_records"] if not r.get("exempted")]
    analysis_output["departments"][dept_id] = {
        "department_name": info["department_name"],
        "annual_budget": info["annual_budget"],
        "total_records": info["total_records"],
        "total_amount": info["total_amount"],
        "cumulative_final": info["cumulative_final"],
        "usage_rate": info["usage_rate"],
        "over_budget": info["over_budget"],
        "crossing_record": info["crossing_record"],
        "violation_record_ids": anom_ids,
        "violation_count": len(anom_ids)
    }

with open("/workspace/work/analysis/data_findings.json", "w") as f:
    json.dump(analysis_output, f, ensure_ascii=False, indent=2)

print(f"\n详细结果已保存到 work/analysis/data_findings.json")
print(f"违规记录总数: {total_violations}")
