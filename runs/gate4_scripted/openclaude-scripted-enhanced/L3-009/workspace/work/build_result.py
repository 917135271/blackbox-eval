import json

with open('/workspace/work/finalized_analysis.json') as f:
    data = json.load(f)

dup_groups = data['dup_groups']
split_groups = data['split_groups']
os_findings = data['os_findings']
ob_findings = data['ob_findings']
overdue_findings = data['overdue_findings']
all_anomaly_ids = data['all_anomaly_ids']
all_record_ids = data['all_record_ids']

# Build citations
citations = [
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十二条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十三条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第七条"},
    {"doc_id": "04_travel_expense.md", "clause_no": "第四条"},
    {"doc_id": "04_travel_expense.md", "clause_no": "第五条"},
    {"doc_id": "05_training_expense.md", "clause_no": "第二条"},
    {"doc_id": "06_business_entertainment.md", "clause_no": "第二条"},
    {"doc_id": "06_business_entertainment.md", "clause_no": "第三条"},
    {"doc_id": "07_office_communication.md", "clause_no": "第二条"},
    {"doc_id": "07_office_communication.md", "clause_no": "第三条"},
    {"doc_id": "08_budget_management.md", "clause_no": "第三条"},
    {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
]

# Build answer
dup_count = len(dup_groups)
spl_count = len(split_groups)
std_count = len(os_findings)
bud_count = len(ob_findings)
ovd_count = len(overdue_findings)

# Pick examples
dup_example = dup_groups[0] if dup_groups else None
spl_example = split_groups[0] if split_groups else None
# Find a non-R0042xx example for split
spl_example_normal = None
for sg in split_groups:
    if not any(rid.startswith('R004') for rid in sg['record_ids']):
        spl_example_normal = sg
        break
spl_example = spl_example_normal if spl_example_normal else spl_example

# Examples by type for over-standard
std_by_type = {}
for osf in os_findings:
    t = osf['expense_type']
    if t not in std_by_type:
        std_by_type[t] = osf

bud_example = ob_findings[0] if ob_findings else None
ovd_example = overdue_findings[0] if overdue_findings else None

answer_parts = []
answer_parts.append(f"一、重复报销（{dup_count}项）")
answer_parts.append(f"发现{dup_count}组重复发票，涉及12条记录。依据《XX证券费用报销管理办法(2025修订版)》（XX证财规〔2025〕甲号）第十条"同一发票最多报销1次"。")
if dup_example:
    answer_parts.append(f"示例：{dup_example['anomaly_id']}——发票{dup_example['invoice_no']}被记录{dup_example['record_ids'][0]}和{dup_example['record_ids'][1]}各报销1次。影响：虚增费用支出，违反发票唯一性原则。建议：追回重复报销款项，完善发票校验机制。")

answer_parts.append(f"\n二、拆分报销（{spl_count}项）")
answer_parts.append(f"发现{spl_count}组拆分报销，涉及{len(set(r for sg in split_groups for r in sg['record_ids']))}条记录。依据《XX证券费用报销管理办法(2025修订版)》第十一条及《XX证券授权管理办法》附件二AR-02审批线（≥3000元）。")
if spl_example:
    answer_parts.append(f"示例：{spl_example['anomaly_id']}——员工{spl_example['employee_name']}在{spl_example['window_start']}至{spl_example['window_end']}期间（7天内）报销{spl_example['expense_type']}共{spl_example['record_count']}笔，合计{spl_example['total_amount']}元，达到较高审批线，涉嫌拆分规避审批。影响：规避适当审批层级，削弱内部控制。建议：建立同类型费用7天窗口聚合监控。")

answer_parts.append(f"\n三、超标准报销（{std_count}项）")
answer_parts.append(f"发现{std_count}笔超标准报销。依据《XX证券费用报销管理办法(2025修订版)》第十二条及各费用类型专项制度标准。")
answer_parts.append(f"其中差旅住宿费{sum(1 for o in os_findings if o['expense_type']=='travel_lodging')}笔（依据《XX证券差旅费管理办法》第四条、第五条）")
answer_parts.append(f"培训费{sum(1 for o in os_findings if o['expense_type']=='training_fee')}笔（依据《XX证券培训费管理办法》第二条，每人每期不超过3500元）")
answer_parts.append(f"业务招待费{sum(1 for o in os_findings if o['expense_type']=='business_entertainment')}笔（依据《XX证券业务招待费管理办法》第二条、第三条）")
answer_parts.append(f"办公用品{sum(1 for o in os_findings if o['expense_type']=='office_supplies')}笔（依据《XX证券办公与通讯费用管理办法》第二条，每人每月不超过600元）")
answer_parts.append(f"通讯费{sum(1 for o in os_findings if o['expense_type']=='communication')}笔（依据《XX证券办公与通讯费用管理办法》第三条，每人每月不超过300元）")
answer_parts.append(f"市内交通费{sum(1 for o in os_findings if o['expense_type']=='local_transport')}笔（依据《XX证券差旅费管理办法》第六条）")

for t, osf in std_by_type.items():
    answer_parts.append(f"示例：{osf['anomaly_id']}——{osf['record_id']}，{osf['employee_name']}，{osf['detail']}。")

answer_parts.append(f"影响：超标准支出增加公司成本，违反预算纪律。建议：强化报销标准前置校验，超标须事先申请专项审批。")

answer_parts.append(f"\n四、超预算（{bud_count}项）")
answer_parts.append(f"发现{bud_count}个部门超预算。依据《XX证券预算管理办法》第三条及《XX证券费用报销管理办法(2025修订版)》第十三条。")
for obf in ob_findings:
    answer_parts.append(f"{obf['anomaly_id']}——部门{obf['department_name']}（{obf['department_id']}），年度预算{obf['annual_budget']:.2f}元，累计支出{obf['total_used']:.2f}元，使用率{obf['usage_rate']*100:.2f}%，关键记录为{obf['key_record_id']}。")
answer_parts.append(f"影响：预算失控，资金使用缺乏有效约束。建议：严格预算执行监控，超预算费用须经专项审批。")

answer_parts.append(f"\n五、超期报销（{ovd_count}项）")
answer_parts.append(f"发现{ovd_count}笔超期报销（提交日距费用发生日超过60天）。依据《XX证券费用报销管理办法(2025修订版)》第七条。")
if ovd_example:
    answer_parts.append(f"示例：{ovd_example['anomaly_id']}——记录{ovd_example['record_id']}，{ovd_example['employee_name']}，{ovd_example['expense_type']}，费用日期{ovd_example['expense_date']}，报销日期{ovd_example['reimburse_date']}，延迟{ovd_example['delay_days']}天。")
answer_parts.append(f"影响：影响财务核算及时性和费用归集准确性。建议：严格执行60天报销时限，超期报销需说明原因并经特别审批。")

answer = "\n".join(answer_parts)

# Build final_result.json
final_result = {
    "anomaly_ids": all_anomaly_ids,
    "record_ids": all_record_ids,
    "answer": answer,
    "citations": citations
}

with open('/workspace/work/final_result.json', 'w') as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print("final_result.json written")
print(f"anomaly_ids count: {len(all_anomaly_ids)}")
print(f"record_ids count: {len(all_record_ids)}")
print(f"answer length: {len(answer)} chars")
print(f"citations count: {len(citations)}")

# Build evidence_input.json
evidence_rows = []

# Duplicate
for dg in dup_groups:
    evidence_rows.append({
        "anomaly_id": dg['anomaly_id'],
        "rule_type": "重复报销",
        "record_ids": dg['record_ids'],
        "citations": [
            {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}
        ],
        "facts": f"发票{dg['invoice_no']}存在{dg['usage_count']}次报销使用记录（{', '.join(dg['record_ids'])}），违反同一发票最多报销1次的规定。"
    })

# Split
for sg in split_groups:
    evidence_rows.append({
        "anomaly_id": sg['anomaly_id'],
        "rule_type": "拆分报销",
        "record_ids": sg['record_ids'],
        "citations": [
            {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"},
            {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}
        ],
        "facts": f"员工{sg['employee_name']}({sg['employee_id']})在{sg['window_start']}至{sg['window_end']}(7天内)报销{sg['expense_type']}共{sg['record_count']}笔，合计{sg['total_amount']}元，达到AR-02审批线(≥3000元)，涉嫌拆分规避审批。"
    })

# Over-standard
for osf in os_findings:
    citations = [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十二条"}]
    if osf['expense_type'] == 'travel_lodging':
        citations.append({"doc_id": "04_travel_expense.md", "clause_no": "第四条"})
        citations.append({"doc_id": "04_travel_expense.md", "clause_no": "第五条"})
    elif osf['expense_type'] == 'training_fee':
        citations.append({"doc_id": "05_training_expense.md", "clause_no": "第二条"})
    elif osf['expense_type'] == 'business_entertainment':
        citations.append({"doc_id": "06_business_entertainment.md", "clause_no": "第二条"})
        citations.append({"doc_id": "06_business_entertainment.md", "clause_no": "第三条"})
    elif osf['expense_type'] == 'office_supplies':
        citations.append({"doc_id": "07_office_communication.md", "clause_no": "第二条"})
    elif osf['expense_type'] == 'communication':
        citations.append({"doc_id": "07_office_communication.md", "clause_no": "第三条"})
    elif osf['expense_type'] == 'local_transport':
        citations.append({"doc_id": "04_travel_expense.md", "clause_no": "第六条"})
    
    evidence_rows.append({
        "anomaly_id": osf['anomaly_id'],
        "rule_type": "超标准报销",
        "record_ids": [osf['record_id']],
        "citations": citations,
        "facts": osf['detail']
    })

# Over-budget
for obf in ob_findings:
    evidence_rows.append({
        "anomaly_id": obf['anomaly_id'],
        "rule_type": "超预算",
        "record_ids": obf['record_ids'],
        "citations": [
            {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十三条"},
            {"doc_id": "08_budget_management.md", "clause_no": "第三条"}
        ],
        "facts": f"部门{obf['department_name']}({obf['department_id']})年度预算{obf['annual_budget']:.2f}元，累计支出{obf['total_used']:.2f}元（使用率{obf['usage_rate']*100:.2f}%），无专项审批。关键记录为{obf['key_record_id']}，按reimburse_date和record_id累计时首次使累计支出超过预算。"
    })

# Overdue
for od in overdue_findings:
    evidence_rows.append({
        "anomaly_id": od['anomaly_id'],
        "rule_type": "超期报销",
        "record_ids": [od['record_id']],
        "citations": [
            {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第七条"}
        ],
        "facts": f"费用日期{od['expense_date']}，报销日期{od['reimburse_date']}，延迟{od['delay_days']}天，超过60天报销期限。"
    })

evidence_input = {
    "evidence_rows": evidence_rows,
    "no_anomaly_coverage": {
        "checked_rules": ["重复报销", "拆分报销", "超标准", "超预算", "超期报销"],
        "complete": True,
        "conclusion": "已对全年全部4240条记录按五类规则逐一核查，各类均有异常发现，无规则需要标记为无异常。",
        "population_count": 4240,
        "query_conditions": "全年（2025-01-01至2025-12-31）全部已审批报销记录",
        "searched_population": "2025年全年全部4240条费用报销记录"
    }
}

with open('/workspace/work/evidence_input.json', 'w') as f:
    json.dump(evidence_input, f, ensure_ascii=False, indent=2)

print("evidence_input.json written")
print(f"evidence_rows count: {len(evidence_rows)}")
