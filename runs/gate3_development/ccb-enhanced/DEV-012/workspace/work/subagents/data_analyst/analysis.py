import json
from datetime import date, timedelta

records = [
    {"record_id":"R900001","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-01-05","reimburse_date":"2025-01-12","expense_type":"office_supplies","amount":480.0,"reason":"项目装订用品第一次报销","invoice_no":"FPDEV900001"},
    {"record_id":"R900002","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-01-06","reimburse_date":"2025-01-13","expense_type":"office_supplies","amount":480.0,"reason":"项目装订用品第二次报销","invoice_no":"FPDEV900001"},
    {"record_id":"R900018","employee_id":"E9003","employee_name":"开发员工丙","department_id":"D902","expense_date":"2025-01-15","reimburse_date":"2025-01-20","expense_type":"other","amount":45000.0,"reason":"年度基础服务采购","invoice_no":"FPDEV900018"},
    {"record_id":"R900003","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-02-03","reimburse_date":"2025-02-08","expense_type":"travel_transport","amount":5200.0,"reason":"同一客户路演交通费第一笔","invoice_no":"FPDEV900003"},
    {"record_id":"R900004","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-02-06","reimburse_date":"2025-02-10","expense_type":"travel_transport","amount":5200.0,"reason":"同一客户路演交通费第二笔","invoice_no":"FPDEV900004"},
    {"record_id":"R900019","employee_id":"E9003","employee_name":"开发员工丙","department_id":"D902","expense_date":"2025-02-15","reimburse_date":"2025-02-20","expense_type":"other","amount":6000.0,"reason":"新增业务服务采购","invoice_no":"FPDEV900019"},
    {"record_id":"R900006","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-03-01","reimburse_date":"2025-05-05","expense_type":"communication","amount":200.0,"reason":"三月通讯费延迟报销","invoice_no":"FPDEV900006"},
    {"record_id":"R900005","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-03-12","reimburse_date":"2025-03-20","expense_type":"business_entertainment","amount":3600.0,"reason":"客户交流餐叙","invoice_no":"FPDEV900005"},
    {"record_id":"R900020","employee_id":"E9003","employee_name":"开发员工丙","department_id":"D902","expense_date":"2025-03-15","reimburse_date":"2025-03-20","expense_type":"other","amount":5000.0,"reason":"专项批准的连续性支出","invoice_no":"FPDEV900020"},
    {"record_id":"R900007","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-04-08","reimburse_date":"2025-04-12","expense_type":"office_supplies","amount":650.0,"reason":"四月个人办公用品","invoice_no":"FPDEV900007"},
    {"record_id":"R900008","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-05-05","reimburse_date":"2025-05-10","expense_type":"office_supplies","amount":590.0,"reason":"五月办公用品甲","invoice_no":"FPDEV900008"},
    {"record_id":"R900009","employee_id":"E9002","employee_name":"开发经理乙","department_id":"D901","expense_date":"2025-05-05","reimburse_date":"2025-05-10","expense_type":"office_supplies","amount":590.0,"reason":"五月办公用品乙","invoice_no":"FPDEV900009"},
    {"record_id":"R900010","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-06-01","reimburse_date":"2025-06-05","expense_type":"travel_transport","amount":5300.0,"reason":"客户走访交通第一阶段","invoice_no":"FPDEV900010"},
    {"record_id":"R900011","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-06-09","reimburse_date":"2025-06-13","expense_type":"travel_transport","amount":5300.0,"reason":"客户走访交通第二阶段","invoice_no":"FPDEV900011"},
    {"record_id":"R900013","employee_id":"E9002","employee_name":"开发经理乙","department_id":"D901","expense_date":"2025-07-10","reimburse_date":"2025-07-15","expense_type":"travel_lodging","amount":1400.0,"reason":"一类城市经理级住宿两晚","invoice_no":"FPDEV900013"},
    {"record_id":"R900016","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-08-02","reimburse_date":"2025-08-08","expense_type":"training_fee","amount":850.0,"reason":"内部培训综合费用一天","invoice_no":"FPDEV900016"},
    {"record_id":"R900014","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-09-03","reimburse_date":"2025-09-06","expense_type":"communication","amount":180.0,"reason":"九月通讯费上半月","invoice_no":"FPDEV900014"},
    {"record_id":"R900015","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-09-20","reimburse_date":"2025-09-23","expense_type":"communication","amount":160.0,"reason":"九月通讯费下半月","invoice_no":"FPDEV900015"},
    {"record_id":"R900017","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-10-06","reimburse_date":"2025-10-12","expense_type":"business_entertainment","amount":5200.0,"reason":"客户交流活动二十人","invoice_no":"FPDEV900017"},
    {"record_id":"R900021","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-12-02","reimburse_date":"2025-12-08","expense_type":"training_lodging","amount":480.0,"reason":"一类城市培训住宿一晚","invoice_no":"FPDEV900021"},
    {"record_id":"R900012","employee_id":"E9001","employee_name":"开发员工甲","department_id":"D901","expense_date":"2025-12-20","reimburse_date":"2026-01-10","expense_type":"other","amount":900.0,"reason":"年末发生费用补充提交","invoice_no":"FPDEV900012"},
]

for r in records:
    r['expense_date_obj'] = date.fromisoformat(r['expense_date'])
    r['reimburse_date_obj'] = date.fromisoformat(r['reimburse_date'])

# AR thresholds
def ar_level(amount):
    if amount < 3000: return "AR-01"
    if amount < 10000: return "AR-02"
    if amount < 50000: return "AR-03"
    if amount < 200000: return "AR-04"
    return "AR-05"

anomalies = []
all_anomaly_records = set()
citations_used = set()

# ======= RULE 1: Duplicate reimbursement (Art.10) =======
print("=== RULE 1: DUPLICATE REIMBURSEMENT ===")
from collections import defaultdict
invoice_map = defaultdict(list)
for r in records:
    invoice_map[r['invoice_no']].append(r)

for inv, recs in invoice_map.items():
    if len(recs) > 1:
        ids = [r['record_id'] for r in recs]
        print(f"DUPLICATE: invoice {inv} -> {ids}")
        anomaly_id = "ANOM-DUP-001"
        anomalies.append({
            "anomaly_id": anomaly_id,
            "rule": "duplicate_reimbursement",
            "record_ids": ids,
            "citations": [{"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.10"}],
            "facts": [f"发票{inv}在记录{ids[0]}和{ids[1]}中重复出现，金额均为{recs[0]['amount']}元，违反同一发票最多报销1次的规定"]
        })
        all_anomaly_records.update(ids)
        citations_used.add(("01_expense_reimbursement_2025.md", "Art.10"))

# ======= RULE 2: Split reimbursement (Art.11) =======
print("\n=== RULE 2: SPLIT REIMBURSEMENT ===")
# Group by employee + expense_type
emp_type_groups = defaultdict(list)
for r in records:
    key = (r['employee_id'], r['expense_type'])
    emp_type_groups[key].append(r)

for (emp, etype), recs in emp_type_groups.items():
    if len(recs) < 2:
        continue
    # Sort by expense_date
    recs_sorted = sorted(recs, key=lambda r: r['expense_date_obj'])
    for i in range(len(recs_sorted)):
        for j in range(i+1, len(recs_sorted)):
            r1, r2 = recs_sorted[i], recs_sorted[j]
            delta = (r2['expense_date_obj'] - r1['expense_date_obj']).days
            if delta <= 7:
                combined = r1['amount'] + r2['amount']
                ar_each_max = max(ar_level(r1['amount']), ar_level(r2['amount']))
                ar_combined = ar_level(combined)
                if ar_combined != ar_each_max:
                    print(f"SPLIT: {emp} {etype} {r1['record_id']}({r1['amount']}) + {r2['record_id']}({r2['amount']}) = {combined}, {delta}d, AR {ar_each_max}->{ar_combined}")
                    ids = [r1['record_id'], r2['record_id']]
                    anomaly_id = f"ANOM-SPLIT-{len(anomalies)+1:03d}"
                    anomalies.append({
                        "anomaly_id": anomaly_id,
                        "rule": "split_reimbursement",
                        "record_ids": ids,
                        "citations": [
                            {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.11"},
                            {"doc_id":"03_authorization_management.md","clause_no":"Annex2"}
                        ],
                        "facts": [f"员工{emp}{r1['employee_name']}在{delta}天内对同一费用类型{etype}报销{r1['record_id']}({r1['amount']}元,{ar_level(r1['amount'])})和{r2['record_id']}({r2['amount']}元,{ar_level(r2['amount'])}),合计{combined}元达到{ar_combined}级审批,涉嫌拆分规避审批"]
                    })
                    all_anomaly_records.update(ids)
                    citations_used.add(("01_expense_reimbursement_2025.md", "Art.11"))
                    citations_used.add(("03_authorization_management.md", "Annex2"))

# ======= RULE 3: Over-standard (Art.12) =======
print("\n=== RULE 3: OVER-STANDARD ===")

# 3a: office_supplies: 600/month/person
print("--- Office supplies (600/month/person) ---")
office_monthly = defaultdict(float)
office_records = defaultdict(list)
for r in records:
    if r['expense_type'] == 'office_supplies':
        month_key = (r['employee_id'], r['expense_date_obj'].month)
        office_monthly[month_key] += r['amount']
        office_records[month_key].append(r)

for (emp, month), total in office_monthly.items():
    recs = office_records[(emp, month)]
    if total > 600:
        ids = [r['record_id'] for r in recs]
        print(f"OVER-STANDARD office: {emp} month {month} total {total} > 600 -> {ids}")
        anomaly_id = f"ANOM-STD-{len(anomalies)+1:03d}"
        anomalies.append({
            "anomaly_id": anomaly_id,
            "rule": "over_standard",
            "record_ids": ids,
            "citations": [
                {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.12"},
                {"doc_id":"07_office_communication.md","clause_no":"Art.2"}
            ],
            "facts": [f"员工{emp}在{month}月办公用品报销合计{total}元,超过600元/人/月的标准"]
        })
        all_anomaly_records.update(ids)
        citations_used.add(("01_expense_reimbursement_2025.md", "Art.12"))
        citations_used.add(("07_office_communication.md", "Art.2"))

# 3b: communication: 300/month/person
print("--- Communication (300/month/person) ---")
comm_monthly = defaultdict(float)
comm_records = defaultdict(list)
for r in records:
    if r['expense_type'] == 'communication':
        month_key = (r['employee_id'], r['expense_date_obj'].month)
        comm_monthly[month_key] += r['amount']
        comm_records[month_key].append(r)

for (emp, month), total in comm_monthly.items():
    recs = comm_records[(emp, month)]
    if total > 300:
        ids = [r['record_id'] for r in recs]
        print(f"OVER-STANDARD comm: {emp} month {month} total {total} > 300 -> {ids}")
        anomaly_id = f"ANOM-STD-{len(anomalies)+1:03d}"
        anomalies.append({
            "anomaly_id": anomaly_id,
            "rule": "over_standard",
            "record_ids": ids,
            "citations": [
                {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.12"},
                {"doc_id":"07_office_communication.md","clause_no":"Art.3"}
            ],
            "facts": [f"员工{emp}在{month}月通讯费报销合计{total}元,超过300元/人/月的标准"]
        })
        all_anomaly_records.update(ids)
        citations_used.add(("01_expense_reimbursement_2025.md", "Art.12"))
        citations_used.add(("07_office_communication.md", "Art.3"))

# 3c: travel_lodging - check per-night rate
print("--- Travel lodging ---")
# Manager (E9002): 650/night tier1, Staff (E9001): 450/night tier1
for r in records:
    if r['expense_type'] == 'travel_lodging':
        reason = r['reason']
        if '两晚' in reason:
            nights = 2
        elif '一晚' in reason:
            nights = 1
        else:
            nights = 1  # default
        per_night = r['amount'] / nights
        if r['employee_id'] == 'E9002':  # manager
            std = 650
        else:
            std = 450
        if per_night > std:
            print(f"OVER-STANDARD lodging: {r['record_id']} {per_night}/night > {std} -> {r['amount']} for {nights} nights")
            anomaly_id = f"ANOM-STD-{len(anomalies)+1:03d}"
            anomalies.append({
                "anomaly_id": anomaly_id,
                "rule": "over_standard",
                "record_ids": [r['record_id']],
                "citations": [
                    {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.12"},
                    {"doc_id":"04_travel_expense.md","clause_no":"Art.4"}
                ],
                "facts": [f"{r['employee_name']}({r['employee_id']})在一类城市住宿{nights}晚共{r['amount']}元,折合{per_night}元/晚,超过标准{std}元/晚"]
            })
            all_anomaly_records.add(r['record_id'])
            citations_used.add(("01_expense_reimbursement_2025.md", "Art.12"))
            citations_used.add(("04_travel_expense.md", "Art.4"))

# 3d: training_fee internal: 800/day
print("--- Training fee ---")
for r in records:
    if r['expense_type'] == 'training_fee':
        if r['amount'] > 800:
            print(f"OVER-STANDARD training: {r['record_id']} {r['amount']} > 800")
            anomaly_id = f"ANOM-STD-{len(anomalies)+1:03d}"
            anomalies.append({
                "anomaly_id": anomaly_id,
                "rule": "over_standard",
                "record_ids": [r['record_id']],
                "citations": [
                    {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.12"},
                    {"doc_id":"05_training_expense.md","clause_no":"Art.3"}
                ],
                "facts": [f"内部培训综合费用一天{r['amount']}元,超过800元/天的标准"]
            })
            all_anomaly_records.add(r['record_id'])
            citations_used.add(("01_expense_reimbursement_2025.md", "Art.12"))
            citations_used.add(("05_training_expense.md", "Art.3"))

# 3e: training_lodging tier1: 500/night
print("--- Training lodging ---")
for r in records:
    if r['expense_type'] == 'training_lodging':
        std = 500
        if r['amount'] > std:
            print(f"OVER-STANDARD training lodging: {r['record_id']} {r['amount']} > {std}")
            anomaly_id = f"ANOM-STD-{len(anomalies)+1:03d}"
            anomalies.append({
                "anomaly_id": anomaly_id,
                "rule": "over_standard",
                "record_ids": [r['record_id']],
                "citations": [
                    {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.12"},
                    {"doc_id":"05_training_expense.md","clause_no":"Art.5"}
                ],
                "facts": [f"一类城市培训住宿一晚{r['amount']}元,超过500元/晚的标准"]
            })
            all_anomaly_records.add(r['record_id'])
            citations_used.add(("01_expense_reimbursement_2025.md", "Art.12"))
            citations_used.add(("05_training_expense.md", "Art.5"))
        else:
            print(f"OK training lodging: {r['record_id']} {r['amount']} <= {std}")

# 3f: business_entertainment: 5000/event, 300/person
print("--- Business entertainment ---")
for r in records:
    if r['expense_type'] == 'business_entertainment':
        reason = r['reason']
        over_total = r['amount'] > 5000
        # Extract person count from reason
        import re
        pax_match = re.search(r'(\d+)人', reason)
        pax = int(pax_match.group(1)) if pax_match else None
        over_per_capita = (pax is not None) and (r['amount'] / pax > 300)

        issues = []
        if over_total:
            issues.append(f"单次活动{r['amount']}元超过5000元上限")
        if over_per_capita:
            issues.append(f"人均{r['amount']/pax:.1f}元超过300元/人上限(pax={pax})")

        if issues:
            print(f"OVER-STANDARD entertainment: {r['record_id']} {'; '.join(issues)}")
            anomaly_id = f"ANOM-STD-{len(anomalies)+1:03d}"
            anomalies.append({
                "anomaly_id": anomaly_id,
                "rule": "over_standard",
                "record_ids": [r['record_id']],
                "citations": [
                    {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.12"},
                    {"doc_id":"06_business_entertainment.md","clause_no":"Art.2" if over_total else "Art.3"}
                ],
                "facts": [f"业务招待费{r['reason']},金额{r['amount']}元,{'; '.join(issues)}"]
            })
            all_anomaly_records.add(r['record_id'])
            citations_used.add(("01_expense_reimbursement_2025.md", "Art.12"))
            if over_total:
                citations_used.add(("06_business_entertainment.md", "Art.2"))
            if over_per_capita:
                citations_used.add(("06_business_entertainment.md", "Art.3"))
        else:
            print(f"OK entertainment: {r['record_id']} {r['amount']} (pax={pax}, per_capita={r['amount']/pax if pax else 'N/A'})")

# ======= RULE 4: Overdue (Art.7, Art.9) =======
print("\n=== RULE 4: OVERDUE ===")
for r in records:
    delay = (r['reimburse_date_obj'] - r['expense_date_obj']).days
    is_year_end = r['expense_date_obj'].month == 12
    if is_year_end:
        # Year-end: deadline is Jan 15 of next year
        deadline = date(r['expense_date_obj'].year, 12, 31) + timedelta(days=15)
        overdue = r['reimburse_date_obj'] > deadline
    else:
        overdue = delay > 60

    if overdue:
        print(f"OVERDUE: {r['record_id']} expense={r['expense_date']} reimburse={r['reimburse_date']} delay={delay}d")
        anomaly_id = f"ANOM-OVD-{len(anomalies)+1:03d}"
        clause = "Art.9" if is_year_end else "Art.7"
        anomalies.append({
            "anomaly_id": anomaly_id,
            "rule": "overdue",
            "record_ids": [r['record_id']],
            "citations": [{"doc_id":"01_expense_reimbursement_2025.md","clause_no":clause}],
            "facts": [f"费用发生日期{r['expense_date']},报销日期{r['reimburse_date']},间隔{delay}天,超过{'年末延期15天' if is_year_end else '60天'}的规定期限"]
        })
        all_anomaly_records.add(r['record_id'])
        citations_used.add(("01_expense_reimbursement_2025.md", clause))

# ======= RULE 5: Over-budget (08_budget Art.3) =======
print("\n=== RULE 5: OVER-BUDGET ===")
budgets = {"D901": 200000.0, "D902": 50000.0}
dept_totals = defaultdict(float)
dept_records = defaultdict(list)
for r in records:
    dept_totals[r['department_id']] += r['amount']
    dept_records[r['department_id']].append(r)

for dept, total in dept_totals.items():
    budget = budgets[dept]
    if total > budget:
        ids = [r['record_id'] for r in dept_records[dept]]
        print(f"OVER-BUDGET: {dept} total {total} > budget {budget} (rate {total/budget:.2%}) -> all {len(ids)} records")
        anomaly_id = f"ANOM-BUD-{len(anomalies)+1:03d}"
        anomalies.append({
            "anomaly_id": anomaly_id,
            "rule": "over_budget",
            "record_ids": ids,
            "citations": [
                {"doc_id":"08_budget_management.md","clause_no":"Art.3"},
                {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"Art.13"}
            ],
            "facts": [f"部门{dept}年度预算{budget}元,实际使用{total}元,超出{total-budget}元,使用率{total/budget:.2%},超过1.0倍预算限额"]
        })
        all_anomaly_records.update(ids)
        citations_used.add(("08_budget_management.md", "Art.3"))
        citations_used.add(("01_expense_reimbursement_2025.md", "Art.13"))

# ======= SUMMARY =======
print("\n=== SUMMARY ===")
print(f"Total anomalies: {len(anomalies)}")
all_ids = sorted(all_anomaly_records)
print(f"Total unique record_ids in violations: {len(all_ids)} -> {all_ids}")

# Save output
output = {
    "anomalies": anomalies,
    "all_anomaly_record_ids": all_ids,
    "citations": [{"doc_id": d, "clause_no": c} for d, c in sorted(citations_used)],
    "anomaly_count": len(anomalies),
    "unique_record_count": len(all_ids)
}

with open("/workspace/work/subagents/data_analyst/batch_analysis.json", "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\nOutput saved to work/subagents/data_analyst/batch_analysis.json")
