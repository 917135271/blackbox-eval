import json, os

# ============================================================
# GATE4 L3-009 Audit Report - Comprehensive Analysis
# ============================================================

# Based on collected MCP data, build the final result

# -- POLICY CITATIONS --
citations_all = [
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第七条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十二条"},
    {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十三条"},
    {"doc_id": "04_travel_expense.md", "clause_no": "第四条"},
    {"doc_id": "05_training_expense.md", "clause_no": "第二条"},
    {"doc_id": "05_training_expense.md", "clause_no": "第五条"},
    {"doc_id": "06_business_entertainment.md", "clause_no": "第二条"},
    {"doc_id": "06_business_entertainment.md", "clause_no": "第三条"},
    {"doc_id": "07_office_communication.md", "clause_no": "第二条"},
    {"doc_id": "07_office_communication.md", "clause_no": "第三条"},
    {"doc_id": "08_budget_management.md", "clause_no": "第三条"},
]

# ============================================================
# 1. DUPLICATE REIMBURSEMENT (Article 10)
# ============================================================
# 6 groups of reused invoices (each invoice used exactly 2 times)
duplicate_groups = [
    {"invoice": "FP202500000002", "records": ["R000002", "R004201"], "type": "office_supplies", "amount": 423.79},
    {"invoice": "FP202500000005", "records": ["R000005", "R004202"], "type": "local_transport", "amount": 88.83},
    {"invoice": "FP202500000020", "records": ["R000020", "R004203"], "type": "travel_lodging", "amount": 669.50},
    {"invoice": "FP202500000028", "records": ["R000028", "R004204"], "type": "communication", "amount": 165.58},
    {"invoice": "FP202500000037", "records": ["R000037", "R004205"], "type": "local_transport", "amount": 84.72},
    {"invoice": "FP202500000055", "records": ["R000055", "R004206"], "type": "business_entertainment", "amount": 999.76},
]
dup_anomaly_ids = ["DUP-001", "DUP-002", "DUP-003", "DUP-004", "DUP-005", "DUP-006"]
dup_record_ids = []
for g in duplicate_groups:
    dup_record_ids.extend(g["records"])

# ============================================================
# 2. OVERDUE REIMBURSEMENT (Article 7, >60 days)
# ============================================================
overdue_records = [
    {"record_id": "R004231", "delay_days": 120, "employee_id": "E0007", "dept": "D007"},
    {"record_id": "R004232", "delay_days": 110, "employee_id": "E0008", "dept": "D008"},
    {"record_id": "R004230", "delay_days": 95, "employee_id": "E0010", "dept": "D010"},
    {"record_id": "R004229", "delay_days": 88, "employee_id": "E0009", "dept": "D009"},
    {"record_id": "R004228", "delay_days": 72, "employee_id": "E0008", "dept": "D008"},
    {"record_id": "R004227", "delay_days": 65, "employee_id": "E0007", "dept": "D007"},
]
overdue_anomaly_ids = ["OVD-001", "OVD-002", "OVD-003", "OVD-004", "OVD-005", "OVD-006"]
overdue_record_ids = [r["record_id"] for r in overdue_records]

# ============================================================
# 3. OVER BUDGET (Article 13)
# ============================================================
# Departments exceeding budget without special approval
# Key record: first record that pushes cumulative above budget
# Sorted by reimburse_date, then record_id
# For the key records, I need to query the actual data.
# From the summarize_department_budgets output:
# D001: budget=230395.17, used=363614.58
# D002: budget=107785.42, used=164928.12
# D003: budget=109772.07, used=174150.67
# D004: budget=264890.39, used=408832.95
# D005: budget=278540.94, used=433442.76
# D006: budget=340961.75, used=530241.29

# For the key records, I'll need to compute from data.
# Using sample analysis from the pages - the specific key records
# will need proper computation. For now, let me use placeholders and 
# compute them accurately.

# I'll write a helper script to compute the actual key records
budget_anomaly_ids = ["BUD-001", "BUD-002", "BUD-003", "BUD-004", "BUD-005", "BUD-006"]

# ============================================================
# 4. SPLIT REIMBURSEMENT (Article 11)
# ============================================================
# Same employee, same expense type, 7-day window, combined >= 10000
# Need to search through all records

# ============================================================
# 5. OVER STANDARD (Article 12)
# ============================================================
# Standards vary by type. Need employee level + additional info

print("Building comprehensive analysis...")
print(f"Duplicate groups: {len(duplicate_groups)}")
print(f"Overdue records: {len(overdue_records)}")
print(f"Over budget depts: 6")
print("Need to compute split and over-standard from full data")

# Save the partial results
os.makedirs("work", exist_ok=True)

