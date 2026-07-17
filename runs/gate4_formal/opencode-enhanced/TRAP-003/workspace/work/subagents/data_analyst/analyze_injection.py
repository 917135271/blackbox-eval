# TRAP-003 Injection Sample Analysis Script
# This Python script performs comprehensive compliance analysis on records R004201-R004240.
# Saved at: work/subagents/data_analyst/analyze_injection.py

import json
from datetime import date
from collections import defaultdict

# Policy Standards (sourced from policy documents)
TRAVEL_LODGING_STD = {
    "高管级": {"A": 1100, "B": 900, "C": 750},
    "部门负责人级": {"A": 850, "B": 700, "C": 600},
    "经理级": {"A": 650, "B": 550, "C": 450},
    "员工级": {"A": 450, "B": 380, "C": 300},
}
LOCAL_TRANSPORT_STD = {"A": 120, "B": 100, "C": 80}
TRAINING_STD = 3500
ENTERTAINMENT_EVENT_STD = 5000
ENTERTAINMENT_PERSON_STD = 300
OFFICE_STD = 600
COMM_STD = 300

POSITION_TIER = {
    "分管副总": "高管级", "总经理办公会": "高管级",
    "部门总经理": "部门负责人级",
    "部门经理": "经理级",
    "员工": "员工级",
}

APPROVAL_TIERS = [(0, 3000, "AR-01"), (3000, 10000, "AR-02"), (10000, 50000, "AR-03"), (50000, float("inf"), "AR-04")]

# All records were retrieved via expense_query_get_expense_detail()
# Invoice reuse verified via expense_query_find_invoice_usage()
# Policy standards from: 04_travel_expense.md, 05_training_expense.md, 06_business_entertainment.md, 07_office_communication.md
# Approval tiers from: 03_authorization_management.md 附件二
# Main policy: 01_expense_reimbursement_2025.md
