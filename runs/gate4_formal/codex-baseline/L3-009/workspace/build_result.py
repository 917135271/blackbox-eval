import json

# ============================================================
# GATE4 L3-009 Audit Report - Comprehensive Analysis
# ============================================================

# ---- Policy References ----
# 01_expense_reimbursement_2025.md:
#   Art 7: 60天提交期限 (超期)
#   Art 10: 同一发票最多1次 (重复)
#   Art 11: 同一员工同一类型7天内2+笔 (拆分)
#   Art 12: 不得超过制度标准1.0倍 (超标准)
#   Art 13: 预算不足时不得报销,超预算需专项审批 (超预算)
# 04_travel_expense.md: 住宿标准表 (超标准-住宿)
# 05_training_expense.md: ≤3500/人/期 (超标准-培训)
# 06_business_entertainment.md: ≤5000/次, ≤300/人 (超标准-招待)
# 08_budget_management.md: 预算约束 (超预算)

citations = [
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第七条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十二条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十三条"},
    {"doc_id": "04_travel_expense.md", "clause_no": "第四条"},
    {"doc_id": "04_travel_expense.md", "clause_no": "第五条"},
    {"doc_id": "05_training_expense.md", "clause_no": "第二条"},
    {"doc_id": "06_business_entertainment.md", "clause_no": "第二条"},
    {"doc_id": "06_business_entertainment.md", "clause_no": "第三条"},
    {"doc_id": "08_budget_management.md", "clause_no": "第三条"},
    {"doc_id": "08_budget_management.md", "clause_no": "第四条"},
]

print("Citations:", len(citations))
print(json.dumps(citations, indent=2, ensure_ascii=False))
