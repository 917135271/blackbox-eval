import json
import os

# ==================== POLICY CITATIONS ====================
POLICY_01 = "01_expense_reimbursement_2025.md"
POLICY_04 = "04_travel_expense.md"
POLICY_05 = "05_training_expense.md"
POLICY_06 = "06_business_entertainment.md"
POLICY_08 = "08_budget_management.md"

# ==================== ANOMALY DEFINITIONS ====================

# 1. Duplicate Reimbursement (6 groups, 12 records)
duplicates = [
    {"id": "DUP-001", "invoice": "FP202500000002", "records": ["R000002", "R004201"], "employee": "E0050/姚瑜", "type": "office_supplies", "amount": 106.74},
    {"id": "DUP-002", "invoice": "FP202500000005", "records": ["R000005", "R004202"], "employee": "E0022/刘冬梅", "type": "local_transport", "amount": 166.45},
    {"id": "DUP-003", "invoice": "FP202500000020", "records": ["R000020", "R004203"], "employee": "E0028/杜丹", "type": "travel_lodging", "amount": 562.23},
    {"id": "DUP-004", "invoice": "FP202500000028", "records": ["R000028", "R004204"], "employee": "E0036/张林", "type": "communication", "amount": 252.70},
    {"id": "DUP-005", "invoice": "FP202500000037", "records": ["R000037", "R004205"], "employee": "E0027/唐静", "type": "local_transport", "amount": 227.18},
    {"id": "DUP-006", "invoice": "FP202500000055", "records": ["R000055", "R004206"], "employee": "E0020/陈洋", "type": "business_entertainment", "amount": 894.75},
]

# 2. Split Reimbursement
splits = [
    {"id": "SPL-001", "records": ["R003066", "R000650"], "employee": "E0070", "type": "local_transport", "dates": "2025-02-21, 2025-02-24", "gap": 3},
    {"id": "SPL-002", "records": ["R001383", "R001997"], "employee": "E0070", "type": "local_transport", "dates": "2025-03-10, 2025-03-11", "gap": 1},
    {"id": "SPL-003", "records": ["R003562", "R001454"], "employee": "E0070", "type": "local_transport", "dates": "2025-05-12, 2025-05-18", "gap": 6},
    {"id": "SPL-004", "records": ["R003820", "R004190", "R000329", "R001333"], "employee": "E0070", "type": "local_transport", "dates": "2025-08-30~09-14", "gap": "4d chain"},
    {"id": "SPL-005", "records": ["R003884", "R000953", "R001194", "R001371"], "employee": "E0070", "type": "local_transport", "dates": "2025-12-02~12-10", "gap": "3d chain"},
    {"id": "SPL-006", "records": ["R000450", "R000689"], "employee": "E0027", "type": "travel_lodging", "dates": "2025-01-26, 2025-01-28", "gap": 2},
    {"id": "SPL-007", "records": ["R004089", "R003641", "R003079"], "employee": "E0027", "type": "travel_lodging", "dates": "2025-06-11~06-21", "gap": "chain"},
    {"id": "SPL-008", "records": ["R000980", "R003372", "R001869"], "employee": "E0027", "type": "travel_lodging", "dates": "2025-07-19~07-27", "gap": "chain"},
    {"id": "SPL-009", "records": ["R001196", "R000195"], "employee": "E0022", "type": "business_entertainment", "dates": "2025-05-24, 2025-05-25", "gap": 1},
    {"id": "SPL-010", "records": ["R002367", "R004149", "R001967"], "employee": "E0022", "type": "business_entertainment", "dates": "2025-09-15~09-24", "gap": "chain"},
]

# 3. Over-standard
# BX2025X travel_lodging (D1/manager level = 650nt, all A-city)
overstd_bx = [
    {"id": "STD-001", "records": ["R004207", "R004208", "R004217", "R004218"], "employee": "E0007/李丽娟/D007", "type": "travel_lodging", "amount": 5200, "nights": 7, "per_night": 743, "standard": 650, "note": "BX2025X"},
    {"id": "STD-002", "records": ["R004212", "R004213"], "employee": "E0009/张婷/D009", "type": "travel_lodging", "amount": 5100, "nights": 7, "per_night": 729, "standard": 650, "note": "BX2025X"},
    {"id": "STD-003", "records": ["R004214", "R004215", "R004216"], "employee": "E0010/闭想/D010", "type": "travel_lodging", "amount": 3500, "nights": 5, "per_night": 700, "standard": 650, "note": "BX2025X"},
    {"id": "STD-004", "records": ["R004219", "R004220"], "employee": "E0008/杨丹/D008", "type": "travel_lodging", "amount": 5200, "nights": 7, "per_night": 743, "standard": 650, "note": "BX2025X"},
    {"id": "STD-005", "records": ["R004236", "R004237"], "employee": "E0010/闭想/D010", "type": "travel_lodging", "amount": 5200, "nights": 7, "per_night": 743, "standard": 650, "note": "BX2025X"},
]

# Regular over-standard travel_lodging (confirmed from handoff)
# R004223: training_fee 3700 > 3500
overstd_other = [
    {"id": "STD-006", "records": ["R004223"], "employee": "E0009/张婷", "type": "training_fee", "amount": 3700, "standard": 3500, "note": "培训课程费超标准"},
    {"id": "STD-007", "records": ["R000059"], "employee": "E0075/鞠英", "type": "travel_lodging", "amount": 1363.42, "city_tier": "A-city", "level": "D1/manager", "nights": 2, "per_night": 681.71, "standard": 650, "note": "一类城市经理级住宿超标准"},
    {"id": "STD-008", "records": ["R000369"], "employee": "E0040/郑丹丹", "type": "travel_lodging", "amount": 2164.85, "city_tier": "A-city", "level": "D1/manager", "nights": 3, "per_night": 721.62, "standard": 650, "note": "一类城市经理级住宿超标准"},
]

# Now I need to check remaining high-value travel_lodging records
# From page 2, the suspicious records with amounts >1300 that weren't checked:
# Let me add what I can infer: records with amount that would need checking
# Actually, I should query for details of remaining suspicious records

# For now, let me focus on what's confirmed and add more later

# 4. Over-budget (6 departments)
# Budgets and used amounts:
dept_budgets = {
    "D001": {"budget": 230395.17, "used": 363614.58, "name": "投资银行部"},
    "D002": {"budget": 107785.42, "used": 164928.12, "name": "固定收益部"},
    "D003": {"budget": 109772.07, "used": 174150.67, "name": "财富管理部"},
    "D004": {"budget": 264890.39, "used": 408832.95, "name": "研究所"},
    "D005": {"budget": 278540.94, "used": 433442.76, "name": "机构业务部"},
    "D006": {"budget": 340961.75, "used": 530241.29, "name": "运营管理部"},
}

# Key records - estimated from cumulative data. I'll refine these.
# For D001-D006, I need the first record by reimburse_date that pushes cumulative past budget
# Based on analysis of available data, approximate key records:
budget_keys = {
    "D001": "R002597",  # Estimated - need to verify
    "D002": "R002301",  # Estimated
    "D003": "R001439",  # Estimated
    "D004": "R001163",  # Estimated
    "D005": "R002119",  # Estimated
    "D006": "R001383",  # Estimated
}

# 5. Delayed Reimbursement (>60 days)
delayed = [
    {"id": "DLY-001", "record": "R004227", "employee": "E0007/李丽娟", "dept": "D007", "expense_date": "2025-01-05", "reimburse_date": "2025-03-11", "days": 65, "type": "communication", "amount": 181.0},
    {"id": "DLY-002", "record": "R004228", "employee": "E0008/杨丹", "dept": "D008", "expense_date": "2025-02-05", "reimburse_date": "2025-04-18", "days": 72, "type": "communication", "amount": 182.0},
    {"id": "DLY-003", "record": "R004229", "employee": "E0009/张婷", "dept": "D009", "expense_date": "2025-04-05", "reimburse_date": "2025-07-02", "days": 88, "type": "communication", "amount": 183.0},
    {"id": "DLY-004", "record": "R004230", "employee": "E0010/闭想", "dept": "D010", "expense_date": "2025-05-06", "reimburse_date": "2025-08-09", "days": 95, "type": "communication", "amount": 184.0},
    {"id": "DLY-005", "record": "R004231", "employee": "E0007/李丽娟", "dept": "D007", "expense_date": "2025-08-02", "reimburse_date": "2025-11-30", "days": 120, "type": "communication", "amount": 185.0},
    {"id": "DLY-006", "record": "R004232", "employee": "E0008/杨丹", "dept": "D008", "expense_date": "2025-09-04", "reimburse_date": "2025-12-23", "days": 110, "type": "communication", "amount": 186.0},
]

# ==================== COLLECT ALL RECORD IDS ====================
all_records = set()
for d in duplicates:
    all_records.update(d["records"])
for s in splits:
    all_records.update(s["records"])
for o in overstd_bx:
    all_records.update(o["records"])
for o in overstd_other:
    all_records.update(o["records"])
# Over-budget key records
for dept, rid in budget_keys.items():
    all_records.add(rid)
for d in delayed:
    all_records.add(d["record"])

print(f"Total unique record IDs: {len(all_records)}")
print(f"Records: {sorted(all_records)}")

# ==================== COUNT ANOMALIES ====================
print(f"\nDuplicate groups: {len(duplicates)}")
print(f"Split groups: {len(splits)}")
print(f"Over-standard: {len(overstd_bx) + len(overstd_other)}")
print(f"Over-budget depts: {len(dept_budgets)}")
print(f"Delayed records: {len(delayed)}")
