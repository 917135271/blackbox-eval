from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DB = ROOT / "data" / "expense.db"
DEV_DIR = ROOT / "data" / "development"
DEV_DB = DEV_DIR / "expense_dev.db"
EVALS = DEV_DIR / "evals.json"
GROUND_TRUTH = DEV_DIR / "ground_truth.json"
MANIFEST = DEV_DIR / "manifest.json"


EMPLOYEES = [
    ("E9001", "开发员工甲", "员工级", "D901", "员工", "2023-01-10"),
    ("E9002", "开发经理乙", "经理级", "D901", "部门经理", "2020-06-01"),
    ("E9003", "开发员工丙", "员工级", "D902", "员工", "2022-03-15"),
    ("E9004", "开发经理丁", "部门负责人级", "D902", "部门经理", "2019-08-20"),
]

DEPARTMENTS = [
    ("D901", "开发审计一部", 200000.0, "E9002"),
    ("D902", "开发审计二部", 50000.0, "E9004"),
]

# record_id, employee_id, department_id, expense_date, reimburse_date, type,
# amount, reason, invoice_key, city_tier, nights, days, participants, special_approval
RECORDS = [
    ("R900001", "E9001", "D901", "2025-01-05", "2025-01-12", "office_supplies", 480.0, "项目装订用品第一次报销", "SHARED-901", None, None, None, None, 0),
    ("R900002", "E9001", "D901", "2025-01-06", "2025-01-13", "office_supplies", 480.0, "项目装订用品第二次报销", "SHARED-901", None, None, None, None, 0),
    ("R900003", "E9001", "D901", "2025-02-03", "2025-02-08", "travel_transport", 5200.0, "同一客户路演交通费第一笔", "INV-900003", None, None, None, None, 0),
    ("R900004", "E9001", "D901", "2025-02-06", "2025-02-10", "travel_transport", 5200.0, "同一客户路演交通费第二笔", "INV-900004", None, None, None, None, 0),
    ("R900005", "E9001", "D901", "2025-03-12", "2025-03-20", "business_entertainment", 3600.0, "客户交流餐叙", "INV-900005", None, None, None, 10, 0),
    ("R900006", "E9001", "D901", "2025-03-01", "2025-05-05", "communication", 200.0, "三月通讯费延迟报销", "INV-900006", None, None, None, None, 0),
    ("R900007", "E9001", "D901", "2025-04-08", "2025-04-12", "office_supplies", 650.0, "四月个人办公用品", "INV-900007", None, None, None, None, 0),
    ("R900008", "E9001", "D901", "2025-05-05", "2025-05-10", "office_supplies", 590.0, "五月办公用品甲", "INV-900008", None, None, None, None, 0),
    ("R900009", "E9002", "D901", "2025-05-05", "2025-05-10", "office_supplies", 590.0, "五月办公用品乙", "INV-900009", None, None, None, None, 0),
    ("R900010", "E9001", "D901", "2025-06-01", "2025-06-05", "travel_transport", 5300.0, "客户走访交通第一阶段", "INV-900010", None, None, None, None, 0),
    ("R900011", "E9001", "D901", "2025-06-09", "2025-06-13", "travel_transport", 5300.0, "客户走访交通第二阶段", "INV-900011", None, None, None, None, 0),
    ("R900012", "E9001", "D901", "2025-12-20", "2026-01-10", "other", 900.0, "年末发生费用补充提交", "INV-900012", None, None, None, None, 0),
    ("R900013", "E9002", "D901", "2025-07-10", "2025-07-15", "travel_lodging", 1400.0, "一类城市经理级住宿两晚", "INV-900013", "A", 2, None, None, 0),
    ("R900014", "E9001", "D901", "2025-09-03", "2025-09-06", "communication", 180.0, "九月通讯费上半月", "INV-900014", None, None, None, None, 0),
    ("R900015", "E9001", "D901", "2025-09-20", "2025-09-23", "communication", 160.0, "九月通讯费下半月", "INV-900015", None, None, None, None, 0),
    ("R900016", "E9001", "D901", "2025-08-02", "2025-08-08", "training_fee", 850.0, "内部培训综合费用一天", "INV-900016", None, None, 1, None, 0),
    ("R900017", "E9001", "D901", "2025-10-06", "2025-10-12", "business_entertainment", 5200.0, "客户交流活动二十人", "INV-900017", None, None, None, 20, 0),
    ("R900018", "E9003", "D902", "2025-01-15", "2025-01-20", "other", 45000.0, "年度基础服务采购", "INV-900018", None, None, None, None, 0),
    ("R900019", "E9003", "D902", "2025-02-15", "2025-02-20", "other", 6000.0, "新增业务服务采购", "INV-900019", None, None, None, None, 0),
    ("R900020", "E9003", "D902", "2025-03-15", "2025-03-20", "other", 5000.0, "专项批准的连续性支出", "INV-900020", None, None, None, None, 1),
    ("R900021", "E9001", "D901", "2025-12-02", "2025-12-08", "training_lodging", 480.0, "一类城市培训住宿一晚", "INV-900021", "A", 1, None, None, 0),
]


TASKS: list[dict[str, Any]] = [
    {"id": "DEV-001", "level": "dev", "category": "policy_exception", "routing_hint": "complexity=1; compact main-agent flow; no native subagent", "prompt": "核查R900012是否构成超期报销。必须同时考虑费用发生后60天规则和会计年度末15天补充提交规则，并说明现行制度为何适用。"},
    {"id": "DEV-002", "level": "dev", "category": "policy_qa", "routing_hint": "complexity=0; compact main-agent flow; no native subagent", "prompt": "现行培训制度中，内部培训和外部培训的综合费用每日上限分别是多少？"},
    {"id": "DEV-003", "level": "dev", "category": "single_anomaly", "routing_hint": "complexity=1; only follow same-invoice records; no native subagent", "prompt": "以R900001为线索核查重复报销，返回全部相关记录及异常结论。"},
    {"id": "DEV-004", "level": "dev", "category": "single_anomaly", "routing_hint": "complexity=1; only follow same employee/type/7-day records; no native subagent", "prompt": "以R900003为线索核查是否存在拆分报销，返回构成同一异常的全部记录。"},
    {"id": "DEV-005", "level": "dev", "category": "single_anomaly", "routing_hint": "complexity=1; compact threshold calculation; no native subagent", "prompt": "核查R900005的业务招待费是否超标，需要同时计算单次活动总额和人均金额。"},
    {"id": "DEV-006", "level": "dev", "category": "single_anomaly", "routing_hint": "complexity=1; compact threshold calculation; no native subagent", "prompt": "核查R900013的差旅住宿费是否超标，结合员工职级、城市档位和住宿晚数计算。"},
    {"id": "DEV-007", "level": "dev", "category": "batch_analysis", "routing_hint": "complexity=3; authorize and invoke data_analyst once", "prompt": "扫描开发库中的个人办公用品和通讯费月度标准，返回全部超标准异常记录；应按员工和自然月聚合。"},
    {"id": "DEV-008", "level": "dev", "category": "batch_analysis", "routing_hint": "complexity=3; authorize and invoke data_analyst once; review year-end exclusion in main context", "prompt": "扫描开发库中的超期报销，返回全部异常记录，并对年末补充提交记录进行核对。"},
    {"id": "DEV-009", "level": "dev", "category": "clean_trap", "routing_hint": "complexity=1; compact false-positive review in main context; no native subagent", "prompt": "R900008与R900009同日同额且费用类型相同，请核查是否属于重复报销；不同发票时不得误报。"},
    {"id": "DEV-010", "level": "dev", "category": "clean_trap", "routing_hint": "complexity=1; compact date-boundary review in main context; no native subagent", "prompt": "R900010与R900011合计超过10000元，请核查是否构成7天内拆分报销，并准确处理日期边界。"},
    {"id": "DEV-011", "level": "dev", "category": "aggregate_budget", "routing_hint": "complexity=3; authorize and invoke data_analyst once; compact approval review", "prompt": "核查D902部门年度预算执行，识别首次导致预算超限且没有专项审批的报销记录；专项审批记录不得误报。"},
    {"id": "DEV-012", "level": "dev", "category": "audit_report", "routing_hint": "complexity=4; authorize and invoke data_analyst once; do policy and independent review compactly in main context", "prompt": "对完整开发库执行综合费用审计，至少覆盖重复报销、拆分报销、超标准、超期和超预算规则，返回全部异常记录并给出有制度依据的摘要。"},
]


GROUND_TRUTHS: dict[str, dict[str, Any]] = {
    "DEV-001": {"anomaly_ids": [], "record_ids": ["R900012"], "required_facts": ["21", "60", "无异常"], "citations": [["01_expense_reimbursement_2025.md", "第七条"], ["01_expense_reimbursement_2025.md", "第九条"], ["01_expense_reimbursement_2025.md", "第十四条"]]},
    "DEV-002": {"anomaly_ids": [], "record_ids": [], "required_facts": ["800", "1200"], "citations": [["05_training_expense.md", "第三条"], ["05_training_expense.md", "第四条"]]},
    "DEV-003": {"anomaly_ids": ["A901"], "record_ids": ["R900001", "R900002"], "required_facts": ["重复"], "citations": [["01_expense_reimbursement_2025.md", "第十条"]]},
    "DEV-004": {"anomaly_ids": ["A902"], "record_ids": ["R900003", "R900004"], "required_facts": ["7天", "10400"], "citations": [["01_expense_reimbursement_2025.md", "第十一条"]]},
    "DEV-005": {"anomaly_ids": ["A903"], "record_ids": ["R900005"], "required_facts": ["360", "300"], "citations": [["06_business_entertainment.md", "第三条"]]},
    "DEV-006": {"anomaly_ids": ["A906"], "record_ids": ["R900013"], "required_facts": ["1300", "1400"], "citations": [["04_travel_expense.md", "第四条"], ["04_travel_expense.md", "第五条"]]},
    "DEV-007": {"anomaly_ids": ["A905", "A907"], "record_ids": ["R900007", "R900014", "R900015"], "required_facts": ["600", "300", "340"], "citations": [["07_office_communication.md", "第二条"], ["07_office_communication.md", "第三条"]]},
    "DEV-008": {"anomaly_ids": ["A904"], "record_ids": ["R900006"], "required_facts": ["65", "60", "R900012"], "citations": [["01_expense_reimbursement_2025.md", "第七条"], ["01_expense_reimbursement_2025.md", "第九条"]]},
    "DEV-009": {"anomaly_ids": [], "record_ids": ["R900008", "R900009"], "required_facts": ["不同发票", "无异常"], "citations": [["01_expense_reimbursement_2025.md", "第十条"]]},
    "DEV-010": {"anomaly_ids": [], "record_ids": ["R900010", "R900011"], "required_facts": ["8天", "无异常"], "citations": [["01_expense_reimbursement_2025.md", "第十一条"]]},
    "DEV-011": {"anomaly_ids": ["A910"], "record_ids": ["R900019"], "required_facts": ["50000", "51000", "专项审批"], "citations": [["08_budget_management.md", "第三条"], ["08_budget_management.md", "第四条"]]},
    "DEV-012": {"anomaly_ids": [f"A{number}" for number in (901, 902, 903, 904, 905, 906, 907, 908, 909, 910)], "record_ids": ["R900001", "R900002", "R900003", "R900004", "R900005", "R900006", "R900007", "R900013", "R900014", "R900015", "R900016", "R900017", "R900019"], "required_facts": ["重复", "拆分", "超标准", "超期", "超预算"], "citations": []},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_schema(connection: sqlite3.Connection) -> None:
    with sqlite3.connect(SOURCE_DB) as source:
        rows = source.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    for _, statement in rows:
        connection.execute(statement)


def approval_tier(amount: float) -> tuple[str, str]:
    if amount < 3000:
        return "AR-01", "部门经理"
    if amount < 10000:
        return "AR-02", "部门经理"
    if amount < 50000:
        return "AR-03", "部门总经理"
    if amount < 200000:
        return "AR-04", "分管副总"
    return "AR-05", "总经理办公会"


def build_database() -> None:
    if DEV_DB.exists():
        DEV_DB.unlink()
    with sqlite3.connect(DEV_DB) as connection:
        create_schema(connection)
        connection.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?)", EMPLOYEES)
        connection.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", DEPARTMENTS)
        invoice_rows: dict[str, tuple[Any, ...]] = {}
        expense_rows = []
        approval_rows = []
        for index, row in enumerate(RECORDS, start=1):
            (record_id, employee_id, department_id, expense_date, reimburse_date, expense_type,
             amount, reason, invoice_key, city_tier, nights, days, participants, special_approval) = row
            invoice_id = "INV900001" if invoice_key == "SHARED-901" else f"INV{record_id[1:]}"
            invoice_no = "FPDEV900001" if invoice_key == "SHARED-901" else f"FPDEV{record_id[1:]}"
            invoice_rows.setdefault(
                invoice_id,
                (invoice_id, invoice_no, f"开发供应商{index:02d}", expense_date, amount, expense_type),
            )
            expense_rows.append(
                (record_id, f"BXDEV{record_id[1:]}", employee_id, department_id, expense_date,
                 reimburse_date, expense_type, amount, reason, invoice_id, "approved", city_tier,
                 nights, days, participants, 2025, special_approval)
            )
            tier_id, role = approval_tier(amount)
            approver = "E9002" if department_id == "D901" else "E9004"
            approval_rows.append(
                (f"AP{index:06d}", record_id, tier_id, approver, role, reimburse_date, "approved")
            )
        connection.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?)", invoice_rows.values())
        connection.executemany(
            "INSERT INTO expense_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            expense_rows,
        )
        connection.executemany("INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?, ?)", approval_rows)
        connection.commit()


def main() -> None:
    DEV_DIR.mkdir(parents=True, exist_ok=True)
    build_database()
    evals = [
        {"id": task["id"], "level": task["level"], "category": task["category"], "routing_hint": task["routing_hint"], "prompt": task["prompt"]}
        for task in TASKS
    ]
    EVALS.write_text(json.dumps(evals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    GROUND_TRUTH.write_text(json.dumps(GROUND_TRUTHS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "purpose": "GATE3 development only; never mount ground_truth.json into candidate containers.",
        "task_count": len(evals),
        "record_count": len(RECORDS),
        "record_namespace": "R900xxx",
        "formal_evals_read": False,
        "formal_ground_truth_read": False,
        "files": {
            "evals.json": sha256(EVALS),
            "ground_truth.json": sha256(GROUND_TRUTH),
            "expense_dev.db": sha256(DEV_DB),
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
