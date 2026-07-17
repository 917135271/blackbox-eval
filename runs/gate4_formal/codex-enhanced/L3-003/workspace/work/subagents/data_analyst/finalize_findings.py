import json

with open('/workspace/work/subagents/data_analyst/findings_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count unique record IDs per rule
r9_ids = set()
for g in data['R9']:
    for rid in g['record_ids']:
        r9_ids.add(rid)

r10_ids = set()
for g in data['R10']:
    for rid in g['record_ids']:
        r10_ids.add(rid)

r1_ids = set(f['record_id'] for f in data['R1'])
r2_ids = set(f['record_id'] for f in data['R2'])
r8_ids = set(f['record_id'] for f in data['R8'])
r11_ids = set(f['record_id'] for f in data['R11'])

# Check overlaps
print(f"R1 unique: {len(r1_ids)}")
print(f"R2 unique: {len(r2_ids)}")
print(f"R8 unique: {len(r8_ids)}")
print(f"R9 unique: {len(r9_ids)}")
print(f"R10 unique: {len(r10_ids)}")
print(f"R11 unique: {len(r11_ids)}")

all_ids = r1_ids | r2_ids | r8_ids | r9_ids | r10_ids | r11_ids
print(f"\nTotal unique: {len(all_ids)}")

# Check overlaps
print(f"\nR9 ∩ R11: {len(r9_ids & r11_ids)}")
print(f"R10 ∩ R11: {len(r10_ids & r11_ids)}")
print(f"R9 ∩ R10: {len(r9_ids & r10_ids)}")
print(f"R1/R2/R8 ∩ R9: {len((r1_ids|r2_ids|r8_ids) & r9_ids)}")
print(f"R1/R2/R8 ∩ R10: {len((r1_ids|r2_ids|r8_ids) & r10_ids)}")
print(f"R1/R2/R8 ∩ R11: {len((r1_ids|r2_ids|r8_ids) & r11_ids)}")

# Extract R11 crossing records
print(f"\nR11 crossing records in R9: {r11_ids & r9_ids}")
print(f"R11 crossing records in R10: {r11_ids & r10_ids}")

# Print full R9 and R10 counts
print(f"\nR9 records total (from groups): {sum(len(g['record_ids']) for g in data['R9'])}")
print(f"R10 records total (from groups): {sum(len(g['record_ids']) for g in data['R10'])}")

# Generate anomaly IDs
anomaly_ids = []
for f in data['R1']:
    anomaly_ids.append(f"ANO_R1_{f['record_id']}")
for f in data['R2']:
    anomaly_ids.append(f"ANO_R2_{f['record_id']}")
for f in data['R8']:
    anomaly_ids.append(f"ANO_R8_{f['record_id']}")
for i, g in enumerate(data['R9']):
    anomaly_ids.append(f"ANO_R9_{i+1:03d}_{g['employee_id']}_{g['month']}")
for i, g in enumerate(data['R10']):
    anomaly_ids.append(f"ANO_R10_{i+1:03d}_{g['employee_id']}_{g['month']}")
for f in data['R11']:
    anomaly_ids.append(f"ANO_R11_{f['record_id']}")

print(f"\nTotal anomaly IDs: {len(anomaly_ids)}")

# Save final summary
summary = {
    "decision": "reject",
    "key_findings": [
        f"R1差旅住宿超标准: {len(data['R1'])}条 - R004225 (部门负责人级/一类城市, 900元/晚 > 850标准)",
        f"R2市内交通超标准: {len(data['R2'])}条 - R004226 (三类城市, 92元/日 > 80标准)",
        f"R3培训课程费超标准: 0条 (全部training_fee无participants数据)",
        f"R4内部培训综合超标准: 0条 (全部training_fee无days数据)",
        f"R5外部培训综合超标准: 0条 (全部training_fee无days数据)",
        f"R6培训住宿超标准: 0条 (全部training_fee无nights数据)",
        f"R7招待费单次超标准: 0条",
        f"R8招待费人均超标准: {len(data['R8'])}条 - R004224 (700元/2人=350 > 300标准)",
        f"R9办公用品月度超标准: {len(data['R9'])}组共{sum(g['record_count'] for g in data['R9'])}条记录违规(每人每月超600元)",
        f"R10通讯费月度超标准: {len(data['R10'])}组共{sum(g['record_count'] for g in data['R10'])}条记录违规(每人每月超300元)",
        f"R11部门预算超支: {len(data['R11'])}条(D001-D006共6个部门首个未审批超标记录)"
    ],
    "record_ids": sorted(list(all_ids)),
    "anomaly_ids": anomaly_ids,
    "citations": [
        {"doc_id": "04_travel_expense.md", "clause_no": "4"},
        {"doc_id": "04_travel_expense.md", "clause_no": "6"},
        {"doc_id": "06_business_entertainment.md", "clause_no": "3"},
        {"doc_id": "07_office_communication.md", "clause_no": "2"},
        {"doc_id": "07_office_communication.md", "clause_no": "3"},
        {"doc_id": "08_budget_management.md", "clause_no": "3"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "12"}
    ],
    "unresolved_items": [
        "training_fee全部578条记录的participants/days/nights字段均为0，无法执行R3-R6人均/每日/每晚比对，这些记录以现有数据无法判定违规",
        "R4/R5需区分内部培训与外部培训，但数据中无分类字段"
    ],
    "population": {
        "total_records": 4240,
        "by_type": {
            "travel_lodging": 883,
            "local_transport": 770,
            "training_fee": 578,
            "business_entertainment": 675,
            "office_supplies": 694,
            "communication": 640
        }
    }
}

print(json.dumps(summary, ensure_ascii=False, indent=2))
