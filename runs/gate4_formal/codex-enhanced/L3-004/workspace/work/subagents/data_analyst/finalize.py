import json

# Full analysis with all records and cumulative calculations
analysis = {
    "methodology": {
        "description": "Cumulative budget overrun analysis for 6 departments over budget in 2025",
        "approach": "For each department, all approved records sorted by reimburse_date ASC then record_id ASC. Cumulative amount accumulated sequentially. First record where cumulative > annual_budget identified as breach record.",
        "sort_order": "reimburse_date ASC, record_id ASC",
        "status_filter": "approved only",
        "budget_year": 2025,
        "rule": "Monthly cap rules do not apply. Budget rules: 08_budget_management.md Article 2,3,4 and 01_expense_reimbursement_2025.md Article 13"
    },
    "departments": {
        "D001": {
            "department_name": "投资银行部",
            "annual_budget": 230395.17,
            "total_approved_records": 525,
            "total_spent": 363614.58,
            "breach": {
                "record_id": "R000079",
                "record_no": "BX2025000079",
                "employee_id": "E0067",
                "employee_name": "毛艳",
                "expense_date": "2025-08-30",
                "reimburse_date": "2025-10-21",
                "expense_type": "office_supplies",
                "amount": 226.98,
                "cumulative_before": 230281.68,
                "cumulative_after": 230508.66,
                "record_index": 326,
                "special_approval": False,
                "violation": True
            }
        },
        "D002": {
            "department_name": "固定收益部",
            "annual_budget": 107785.42,
            "total_approved_records": 254,
            "total_spent": 164928.12,
            "breach": {
                "record_id": "R002009",
                "record_no": "BX2025002009",
                "employee_id": "E0021",
                "employee_name": "王彬",
                "expense_date": "2025-08-21",
                "reimburse_date": "2025-09-28",
                "expense_type": "travel_lodging",
                "amount": 746.04,
                "cumulative_before": 107412.40,
                "cumulative_after": 108158.44,
                "record_index": 158,
                "special_approval": False,
                "violation": True
            }
        },
        "D003": {
            "department_name": "财富管理部",
            "annual_budget": 109772.07,
            "total_approved_records": 249,
            "total_spent": 174150.67,
            "breach": {
                "record_id": "R003968",
                "record_no": "BX2025003968",
                "employee_id": "E0066",
                "employee_name": "何楠",
                "expense_date": "2025-09-08",
                "reimburse_date": "2025-09-28",
                "expense_type": "communication",
                "amount": 213.68,
                "cumulative_before": 109665.23,
                "cumulative_after": 109878.91,
                "record_index": 155,
                "special_approval": False,
                "violation": True
            }
        },
        "D004": {
            "department_name": "研究所",
            "annual_budget": 264890.39,
            "total_approved_records": 611,
            "total_spent": 408832.95,
            "breach": {
                "record_id": "R000894",
                "record_no": "BX2025000894",
                "employee_id": "E0015",
                "employee_name": "顾淑兰",
                "expense_date": "2025-09-23",
                "reimburse_date": "2025-09-30",
                "expense_type": "communication",
                "amount": 126.41,
                "cumulative_before": 264827.18,
                "cumulative_after": 264953.59,
                "record_index": 379,
                "special_approval": False,
                "violation": True
            }
        },
        "D005": {
            "department_name": "机构业务部",
            "annual_budget": 278540.94,
            "total_approved_records": 616,
            "total_spent": 433442.76,
            "breach": {
                "record_id": "R003479",
                "record_no": "BX2025003479",
                "employee_id": "E0018",
                "employee_name": "徐阳",
                "expense_date": "2025-09-12",
                "reimburse_date": "2025-10-13",
                "expense_type": "travel_lodging",
                "amount": 429.21,
                "cumulative_before": 278326.33,
                "cumulative_after": 278755.54,
                "record_index": 382,
                "special_approval": False,
                "violation": True
            }
        },
        "D006": {
            "department_name": "运营管理部",
            "annual_budget": 340961.75,
            "total_approved_records": 833,
            "total_spent": 530241.29,
            "breach": {
                "record_id": "R000312",
                "record_no": "BX2025000312",
                "employee_id": "E0070",
                "employee_name": "李琳",
                "expense_date": "2025-09-17",
                "reimburse_date": "2025-10-06",
                "expense_type": "office_supplies",
                "amount": 256.90,
                "cumulative_before": 340833.30,
                "cumulative_after": 341090.20,
                "record_index": 517,
                "special_approval": False,
                "violation": True
            }
        }
    },
    "policy_citations": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "Article 13", "text": "部门年度预算不足时不得继续报销。预算使用达到预算额度的1.0倍后,确需发生的费用应履行专项审批。"},
        {"doc_id": "08_budget_management.md", "clause_no": "Article 2", "text": "各部门应在年度预算额度内发生费用。"},
        {"doc_id": "08_budget_management.md", "clause_no": "Article 3", "text": "部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。"},
        {"doc_id": "08_budget_management.md", "clause_no": "Article 4", "text": "因监管要求、客户服务或经营连续性确需超预算支出的,应履行专项审批。"}
    ],
    "violation_summary": "All 6 departments exceeded their annual budgets without special approval on the breach records. All 6 breach records have special_approval=false, constituting violations of budget management policy."
}

with open("/workspace/work/subagents/data_analyst/analysis.json", "w", encoding="utf-8") as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)

# Compact summary for the main agent
summary = {
    "decision": "reject",
    "key_findings": [
        "D001 投资银行部: breached budget at R000079 (2025-10-21, office_supplies 226.98), cumulative reached 230,508.66 vs budget 230,395.17, special_approval=False",
        "D002 固定收益部: breached budget at R002009 (2025-09-28, travel_lodging 746.04), cumulative reached 108,158.44 vs budget 107,785.42, special_approval=False",
        "D003 财富管理部: breached budget at R003968 (2025-09-28, communication 213.68), cumulative reached 109,878.91 vs budget 109,772.07, special_approval=False",
        "D004 研究所: breached budget at R000894 (2025-09-30, communication 126.41), cumulative reached 264,953.59 vs budget 264,890.39, special_approval=False",
        "D005 机构业务部: breached budget at R003479 (2025-10-13, travel_lodging 429.21), cumulative reached 278,755.54 vs budget 278,540.94, special_approval=False",
        "D006 运营管理部: breached budget at R000312 (2025-10-06, office_supplies 256.90), cumulative reached 341,090.20 vs budget 340,961.75, special_approval=False"
    ],
    "record_ids": ["R000079", "R002009", "R003968", "R000894", "R003479", "R000312"],
    "citations": [
        "01_expense_reimbursement_2025.md:Article 13",
        "08_budget_management.md:Article 2",
        "08_budget_management.md:Article 3",
        "08_budget_management.md:Article 4"
    ],
    "unresolved_items": [],
    "artifact_paths": [
        "work/subagents/data_analyst/analysis.json",
        "work/subagents/data_analyst/budget_analysis.py",
        "work/subagents/data_analyst/verify_breach.py"
    ]
}

with open("/workspace/work/subagents/data_analyst/summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("Analysis saved to work/subagents/data_analyst/analysis.json")
print("Summary saved to work/subagents/data_analyst/summary.json")
print("\n--- SUMMARY ---")
print(json.dumps(summary, indent=2, ensure_ascii=False))
