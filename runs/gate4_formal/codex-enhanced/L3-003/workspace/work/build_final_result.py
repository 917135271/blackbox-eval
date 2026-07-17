import json

with open('/workspace/work/subagents/data_analyst/findings_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Build anomaly_ids
anomaly_ids = []
for f_item in data['R1']:
    anomaly_ids.append(f"ANO_R1_{f_item['record_id']}")
for f_item in data['R2']:
    anomaly_ids.append(f"ANO_R2_{f_item['record_id']}")
for f_item in data['R8']:
    anomaly_ids.append(f"ANO_R8_{f_item['record_id']}")
for i, g in enumerate(data['R9']):
    anomaly_ids.append(f"ANO_R9_{i+1:03d}_{g['employee_id']}_{g['month']}")
for i, g in enumerate(data['R10']):
    anomaly_ids.append(f"ANO_R10_{i+1:03d}_{g['employee_id']}_{g['month']}")
for f_item in data['R11']:
    anomaly_ids.append(f"ANO_R11_{f_item['record_id']}")

# Build record_ids: all unique
all_record_ids = set()
for f_item in data['R1']:
    all_record_ids.add(f_item['record_id'])
for f_item in data['R2']:
    all_record_ids.add(f_item['record_id'])
for f_item in data['R8']:
    all_record_ids.add(f_item['record_id'])
for g in data['R9']:
    for rid in g['record_ids']:
        all_record_ids.add(rid)
for g in data['R10']:
    for rid in g['record_ids']:
        all_record_ids.add(rid)
for f_item in data['R11']:
    all_record_ids.add(f_item['record_id'])

record_ids = sorted(list(all_record_ids))

# Verify format
import re
for rid in record_ids:
    if not re.match(r'^R[0-9]{6}$', rid):
        print(f"INVALID record_id format: {rid}")

# Citations
citations = [
    {"doc_id": "04_travel_expense.md", "clause_no": "4"},
    {"doc_id": "04_travel_expense.md", "clause_no": "6"},
    {"doc_id": "06_business_entertainment.md", "clause_no": "3"},
    {"doc_id": "07_office_communication.md", "clause_no": "2"},
    {"doc_id": "07_office_communication.md", "clause_no": "3"},
    {"doc_id": "08_budget_management.md", "clause_no": "3"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "12"}
]

answer = (
    "2025年度超标准专项扫描完成。对6种费用类型4240条记录按11条子规则逐一比对。"
    "R1差旅住宿超标准发现1条: R004225(部门负责人级/A类城市,900元/晚>850标准)。"
    "R2市内交通超标准发现1条: R004226(C类城市,92元/日>80标准)。"
    "R3培训课程费:R3-R6因training_fee全部578条记录participants/days/nights字段为0无法比对。"
    "R7招待费单次:全部675条均未超5000元标准。"
    "R8招待费人均超标准发现1条: R004224(350元/人>300标准)。"
    "R9办公用品月度超标准发现114个违规组共285条记录(按employee_id×月度GROUP BY sum>600)。"
    "R10通讯费月度超标准发现132个违规组共307条记录(按employee_id×月度GROUP BY sum>300)。"
    "R11部门预算超支发现6条(D001-D006共6个部门首个未审批超标记录)。"
    "共计255项异常,601条异常记录。"
)

result = {
    "anomaly_ids": anomaly_ids,
    "record_ids": record_ids,
    "answer": answer,
    "citations": citations
}

# Verify uniqueness
assert len(result['anomaly_ids']) == len(set(result['anomaly_ids'])), "Duplicate anomaly_ids!"
assert len(result['record_ids']) == len(set(result['record_ids'])), "Duplicate record_ids!"

with open('/workspace/work/final_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Final result built:")
print(f"  anomaly_ids: {len(result['anomaly_ids'])}")
print(f"  record_ids: {len(result['record_ids'])}")
print(f"  citations: {len(result['citations'])}")
print(f"  answer length: {len(result['answer'])} chars")
