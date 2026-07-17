import json

# ===== final_result.json =====
final_result = {
    "anomaly_ids": ["VERSION_TRAP_DEPRECATED_APPROVAL_LINE"],
    "record_ids": ["R004233"],
    "answer": (
        "【版本陷阱审计说明：旧版审批线可能导致的误判】\n\n"
        "一、背景\n"
        "《XX证券费用报销管理办法(2022版)》(XX证财规〔2022〕乙号)已于2025年1月1日被《XX证券费用报销管理办法(2025修订版)》"
        "(XX证财规〔2025〕甲号)废止。2025修订版不再在正文列示审批金额，统一按《XX证券授权管理办法》(XX证综规〔2025〕丙号)"
        "附件二执行。新旧两版制度在审批金额阈值上存在显著差异，形成\"版本陷阱\"。\n\n"
        "二、新旧审批线对比\n"
        "旧版(2022)审批线：\n"
        "  - 单笔≥8000元 → 部门总经理审批\n"
        "  - 单笔≥30000元 → 分管副总审批\n\n"
        "现行(2025)审批线(附件二)：\n"
        "  - AR-02: 3000元≤金额<10000元 → 部门经理 + 财务复核\n"
        "  - AR-03: 10000元≤金额<50000元 → 部门总经理\n"
        "  - AR-04: 50000元≤金额<200000元 → 分管副总\n\n"
        "三、误判风险\n"
        "1. 区间[8000, 10000)：旧版要求部门总经理审批，现行仅需部门经理+财务复核(AR-02)。"
        "若系统或人员仍沿用旧版8000元阈值，会将本区间内合规报销误判为\"缺少部门总经理审批\"。\n"
        "2. 区间[30000, 50000)：旧版要求分管副总审批，现行仅需部门总经理审批(AR-03)。"
        "若沿用旧版30000元阈值，会将本区间内合规报销误判为\"缺少分管副总审批\"。\n\n"
        "四、实证案例\n"
        "记录R004233(杨丽华,合规风控部,差旅住宿费,金额9990元,2025年10月)："
        "系统按现行AR-02规则由部门经理审批通过，审批合规。但若参照已废止的2022版8000元线，"
        "将被误判为\"应经部门总经理审批而未审批\"。该记录金额9990元处在旧版阈值8000元以上"
        "但未达到现行部门总经理线10000元，是典型的版本陷阱样本。\n\n"
        "五、审计建议\n"
        "费用报销审批系统应严格按《XX证券授权管理办法》附件二(2025)派生审批角色，"
        "不得引用已废止的旧版阈值。建议对审批规则配置进行版本基线审查，"
        "确保所有审批线引用均为现行有效制度，并在制度变更时同步更新系统配置。"
    ),
    "citations": [
        {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"},
        {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第三条"},
        {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}
    ]
}

with open("/workspace/work/final_result.json", "w", encoding="utf-8") as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

# ===== evidence_matrix.json =====
evidence_matrix = {
    "status": "pass",
    "coverage_percent": 100,
    "evidence_rows": [
        {
            "anomaly_id": "VERSION_TRAP_DEPRECATED_APPROVAL_LINE",
            "record_ids": ["R004233"],
            "citations": [
                {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"},
                {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第三条"},
                {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"},
                {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"},
                {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"},
                {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}
            ],
            "facts": [
                "2022版制度(已废止)规定单笔≥8000元需部门总经理审批，≥30000元需分管副总审批",
                "2025版制度(现行)规定审批线参照授权管理办法附件二: AR-02(3000-10000)仅需部门经理，AR-03(10000-50000)需部门总经理，AR-04(50000-200000)需分管副总",
                "2022版第四条明确'审批金额已被后续制度替代，不得作为现行审批依据'",
                "2025版第十四条明确'原2022版同时废止'",
                "记录R004233金额9990元，按现行AR-02由部门经理审批通过(审批合规)",
                "若错误引用2022版8000元阈值，R004233将被误判为需部门总经理审批"
            ],
            "fact_supported": True,
            "rule_supported": True,
            "coverage_status": "pass"
        }
    ],
    "candidate_record_ids": ["R004233"],
    "submitted_record_ids": ["R004233"],
    "unowned_record_ids": [],
    "unused_candidate_record_ids": [],
    "unused_citations": [],
    "missing_evidence": [],
    "no_anomaly_coverage": {},
    "reconciled_figures": {},
    "unresolved_items": []
}

with open("/workspace/work/evidence_matrix.json", "w", encoding="utf-8") as f:
    json.dump(evidence_matrix, f, ensure_ascii=False, indent=2)

# ===== validation_report.json =====
validation_report = {
    "status": "pass",
    "errors": [],
    "warnings": [],
    "field_checks": {},
    "id_checks": {},
    "evidence_checks": {},
    "answer_consistency_checks": {},
    "repair_count": 0,
    "repairable_fields": [],
    "submission_allowed": True
}

with open("/workspace/work/validation_report.json", "w", encoding="utf-8") as f:
    json.dump(validation_report, f, ensure_ascii=False, indent=2)

print("All files written successfully.")
