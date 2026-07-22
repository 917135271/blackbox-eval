from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCE_EVALS = ROOT / "data" / "evals.json"
SOURCE_GROUND_TRUTH = ROOT / "data" / "ground_truth.yaml"
OUTPUT_CASES = Path(__file__).with_name("cases.json")
OUTPUT_EVALS = Path(__file__).with_name("evals.json")
RUBRIC_CHECKLISTS = Path(__file__).with_name("rubric_checklists.json")

CASE_SPECS = [
    ("L1-001", "policy_and_version", "现行审批线基础题，验证制度事实与版本意识"),
    ("L3-006", "policy_and_version", "新旧制度冲突题，验证适用版本选择"),
    ("L3-008", "policy_and_version", "近似条款区分题，验证适用场景判断"),
    ("L2-003", "record_audit", "重复报销单案，验证跨记录证据关联"),
    ("L2-008", "record_audit", "拆分报销双记录案例，验证窗口和合计金额"),
    ("L2-013", "record_audit", "培训费超标准案例，验证金额与费用类型标准"),
    ("L3-001", "full_year_audit", "全年重复报销扫描，验证完整召回"),
    ("L3-003", "full_year_audit", "全年超标准扫描，验证多费用类型标准"),
    ("L3-004", "full_year_audit", "全年超预算扫描，验证部门聚合"),
    ("TRAP-002", "clean_trap", "同组记录但发票不同且合计未越线"),
    ("TRAP-003", "clean_trap", "超过聚合时间窗，验证窗口边界"),
    ("TRAP-005", "clean_trap", "多条件均合规，验证综合反向复核"),
    ("L3-007", "retrieval_and_report", "二跳制度检索，验证交叉引用"),
    ("L3-009", "retrieval_and_report", "全年综合报告，验证五类规则汇总"),
    ("L3-010", "retrieval_and_report", "制度版本风险报告，验证审计表达"),
]

RULES = {
    "DUP": ("重复报销", "01_expense_reimbursement_2025.md 第十条"),
    "SPLIT": ("拆分报销", "01_expense_reimbursement_2025.md 第十一条及03_authorization_management.md附件二"),
    "OVERSTD": ("超标准", "01_expense_reimbursement_2025.md 第十二条及对应专项费用标准"),
    "BUDGET": ("超预算", "08_budget_management.md 第二条至第四条"),
    "OVERDUE": ("超期报销", "01_expense_reimbursement_2025.md 第七条及第九条"),
}

PROMPT_OVERRIDES = {
    "L1-001": "现行制度下，单笔费用报销达到多少金额需要部门总经理审批？请说明适用版本、金额边界及费用报销办法与授权管理办法中的制度依据，并说明旧版审批线是否仍适用。",
    "L3-006": "请判断费用报销审批线应采用2022版还是2025修订版，指出部门总经理审批线，并提供新旧版本效力状态及现行金额出处。",
    "L3-008": "分别比较差旅住宿和培训住宿的适用制度、标准维度和数值。请列出培训住宿一、二、三类城市标准，并至少举一个同城市档位下与某职级差旅标准的数值对照，说明为什么不能混用。",
    "L3-001": "请对全年数据做重复报销专项扫描，按重复发票组生成稳定的发现ID，返回全部发现ID和关联record_id集合，并说明全量扫描方法和制度依据。",
    "L3-003": "请对全年数据做单笔或单次即可确认的超标准专项扫描，返回全部发现ID和关联record_id集合，并说明各费用类型的计算口径、全量扫描方法和制度依据。办公用品和通讯费用本题只识别单笔自身已经超过月度上限的明确异常，不评价多笔记录的月度累计超限。",
    "L3-004": "请对全年数据做超预算专项扫描。按reimburse_date和record_id依次累计部门已批准费用，每个超预算部门形成1项发现，以首次使累计支出超过年度预算且无专项审批的记录作为关键record_id。请返回全部发现ID和关键record_id集合，并说明计算方法和制度依据。",
    "L2-003": "结合制度和业务数据，核查以R000020为线索的重复报销异常，返回发现ID和record_id集合，并说明关键业务事实和制度依据。",
    "L2-008": "结合制度和业务数据，核查以R004212为线索的拆分报销异常，返回发现ID和record_id集合，并说明日期窗口、合计金额和制度依据。",
    "L2-013": "结合制度和业务数据，核查以R004223为线索的超标准异常，返回发现ID和record_id集合，并说明费用类型、金额、适用标准和制度依据。",
    "TRAP-002": "请核查R004234和R004235是否构成重复报销或拆分报销。必须核对发票是否相同及7天内合计金额；若不构成异常，请明确说明无异常、原因和制度依据。",
    "TRAP-003": "请核查R004236和R004237是否构成7天内拆分报销。必须按费用发生日期计算间隔并核对合计金额；若不构成异常，请明确说明无异常、原因和制度依据。",
    "TRAP-005": "请核查R004239和R004240是否构成重复报销、拆分报销或业务招待费超标准。必须核对发票、日期、单次金额和人均金额；若不构成异常，请明确说明无异常、原因和制度依据。",
    "L3-009": "请基于全年数据形成费用异常审计摘要，覆盖重复报销、拆分报销、超标准、超预算和超期报销五类规则。发现口径为：重复报销按重复发票组计1项；拆分报销按同一员工、同一费用类型7天窗口聚合组计1项；超标准只计单笔或单次即可确认的异常，办公用品和通讯费用不评价多笔月度累计；超预算按部门计1项，以按reimburse_date和record_id累计时首次使累计支出超过预算且无专项审批的记录作为关键记录；超期报销按记录计1项。请按规则类型生成稳定的发现ID，说明各类发现数量，在record_ids中返回全部异常发现涉及的记录，并在审计说明中至少逐类给出一个发现与record_id的对应示例，同时说明制度依据、影响和建议；不得把仅接近阈值但实际合规的记录计入异常。",
    "L3-010": "请专门写一段版本陷阱审计说明，列明新旧审批线及其效力状态，说明现行金额的交叉引用依据、使用旧版可能造成的误判，并提出版本校验措施。",
}

PROMPT_CHANGE_REASONS = {
    "L1-001": "使题面明确覆盖适用版本、制度证据和旧值排除要求",
    "L3-006": "使题面明确覆盖Rubric要求的新旧状态和现行金额证据",
    "L3-008": "补充可客观评分的标准维度、数值和对照要求",
    "L3-001": "明确发现分组、全量扫描方法和制度依据交付要求",
    "L3-003": "明确单记录超标准口径，排除制度中的月度跨记录累计歧义",
    "L3-004": "明确超预算发现按部门计数及首次越线关键记录口径",
    "L2-003": "使题面明确要求案件事实和制度证据",
    "L2-008": "使题面明确要求日期、合计金额和制度证据",
    "L2-013": "使题面明确要求适用标准和制度证据",
    "TRAP-002": "原题只给不可见TRAP标签，补充候选可查询的record_id和核查边界",
    "TRAP-003": "原题只给不可见TRAP标签，补充候选可查询的record_id和核查边界",
    "TRAP-005": "原题只给不可见TRAP标签，补充候选可查询的record_id和核查边界",
    "L3-009": "删除不可见TRAP总数要求，明确发现ID和五类规则的可复算统计口径",
    "L3-010": "使题面明确覆盖新旧数值、现行依据、误判风险和控制建议",
}

TRAP_REASON_ZH = {
    "TRAP-002": "两条记录发票不同，且同一员工同类费用7天内合计500元，未达到10000元审批线",
    "TRAP-003": "两条记录合计10400元，虽达到10000元审批线，但费用发生日期相隔8天，超出7天聚合窗口",
    "TRAP-005": "两条记录分别对应客户甲产品方案交流和客户乙投行业务沟通，费用发生日期相隔1天；发票不同，单次金额分别为540元和545元、各3人，人均分别为180元和约181.67元，均未超过单次5000元和人均300元标准，合计也未达到10000元审批线",
}

FORMAL_CITATIONS = {
    "L1-001": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
    "L3-006": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"},
        {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条、第二条、第四条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
    "L3-008": [
        {"doc_id": "04_travel_expense.md", "clause_no": "第三条、第四条、第七条"},
        {"doc_id": "05_training_expense.md", "clause_no": "第五条、第六条"},
    ],
    "L2-003": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}],
    "L2-008": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
    "L2-013": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十二条"},
        {"doc_id": "05_training_expense.md", "clause_no": "第二条"},
    ],
    "L3-001": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}],
    "L3-003": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十二条"},
        {"doc_id": "04_travel_expense.md", "clause_no": "第三条至第六条"},
        {"doc_id": "05_training_expense.md", "clause_no": "第二条至第五条"},
        {"doc_id": "06_business_entertainment.md", "clause_no": "第二条、第三条"},
        {"doc_id": "07_office_communication.md", "clause_no": "第二条、第三条"},
    ],
    "L3-004": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十三条"},
        {"doc_id": "08_budget_management.md", "clause_no": "第二条至第四条"},
    ],
    "TRAP-002": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条、第十一条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
    "TRAP-003": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
    "TRAP-005": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条、第十一条"},
        {"doc_id": "06_business_entertainment.md", "clause_no": "第二条至第四条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
    "L3-007": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
    "L3-009": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第七条、第九条至第十三条"},
        {"doc_id": "04_travel_expense.md", "clause_no": "第三条至第六条"},
        {"doc_id": "05_training_expense.md", "clause_no": "第二条至第五条"},
        {"doc_id": "06_business_entertainment.md", "clause_no": "第二条、第三条"},
        {"doc_id": "07_office_communication.md", "clause_no": "第二条、第三条"},
        {"doc_id": "08_budget_management.md", "clause_no": "第二条至第四条"},
    ],
    "L3-010": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条、第十四条"},
        {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条、第二条、第四条"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
    ],
}


def formal_ground_truth_refs(task: dict[str, Any]) -> list[str]:
    refs = [
        str(ref)
        for ref in task.get("ground_truth_refs", [])
        if not str(ref).startswith(("document:", "clause:"))
    ]
    for citation in FORMAL_CITATIONS.get(str(task["id"]), []):
        doc_id = str(citation["doc_id"])
        clause_no = str(citation["clause_no"])
        refs.extend(
            [
                f"document:{doc_id}",
                f"clause:{doc_id}#{clause_no}",
            ]
        )
    return list(dict.fromkeys(refs))


def criterion(
    criterion_id: str,
    title: str,
    description: str,
    metric: str,
    evaluation_mode: str,
    expected: Any,
    evidence_sources: list[str],
    full: str,
    _partial: str,
    _zero: str,
) -> dict[str, Any]:
    return {
        "id": criterion_id,
        "check": f"{title}：{description}",
        "metric": metric,
        "evaluation_mode": evaluation_mode,
        "expected": expected,
        "evidence_sources": evidence_sources,
        "pass_condition": full,
        "fail_condition": f"未完全满足通过条件：{full}",
    }


def comprehensive_expectations(
    task: dict[str, Any], ground_truth: dict[str, Any]
) -> dict[str, Any]:
    anomaly_ids = [
        str(ref).removeprefix("ground_truth:")
        for ref in task.get("ground_truth_refs", [])
        if str(ref).startswith("ground_truth:")
    ]
    anomaly_map = {
        str(item["anomaly_id"]): item for item in ground_truth["anomalies"]
    }
    known_ids = set(anomaly_map)
    unknown_ids = sorted(set(anomaly_ids) - known_ids)
    if unknown_ids:
        raise ValueError(f"unknown comprehensive anomaly references: {unknown_ids}")
    finding_counts = Counter(item.split("-", 1)[0] for item in anomaly_ids)
    rule_types = list(finding_counts)
    excluded_record_ids = list(
        dict.fromkeys(
            str(record_id)
            for trap in ground_truth["traps"]
            for record_id in trap.get("record_ids", [])
        )
    )
    finding_groups = []
    expected_record_ids: list[str] = []
    for anomaly_id in anomaly_ids:
        anomaly = anomaly_map[anomaly_id]
        record_ids = [str(record_id) for record_id in anomaly["record_ids"]]
        expected_record_ids.extend(record_ids)
        group = {
            "rule_type": anomaly_id.split("-", 1)[0],
            "record_ids": record_ids,
        }
        department_id = (anomaly.get("params") or {}).get("department_id")
        if department_id:
            group["department_id"] = str(department_id)
        finding_groups.append(group)
    return {
        "expected_anomaly_count": len(anomaly_ids),
        "expected_rule_types": rule_types,
        "expected_findings_by_type": dict(finding_counts),
        "expected_record_ids": list(dict.fromkeys(expected_record_ids)),
        "expected_finding_groups": finding_groups,
        "excluded_record_ids": excluded_record_ids,
    }


def finding_groups_for_task(
    task: dict[str, Any], anomaly_map: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for anomaly_id in task["scoring"].get("expected_anomaly_ids", []):
        anomaly = anomaly_map[str(anomaly_id)]
        group = {
            "rule_type": str(anomaly_id).split("-", 1)[0],
            "record_ids": [str(record_id) for record_id in anomaly["record_ids"]],
        }
        department_id = (anomaly.get("params") or {}).get("department_id")
        if department_id:
            group["department_id"] = str(department_id)
        groups.append(group)
    return groups


def expected_output(
    task: dict[str, Any],
    comprehensive: dict[str, Any] | None = None,
    finding_groups: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    scoring = task["scoring"]
    output = {"scoring_kind": scoring.get("kind", scoring.get("type"))}
    for key in (
        "expected_facts",
        "expected_anomaly_ids",
        "expected_record_ids",
        "expected_reason",
        "rubric_assertions",
    ):
        if key in scoring:
            output[key] = scoring[key]
    internal_anomaly_ids = [str(item) for item in output.pop("expected_anomaly_ids", [])]
    if internal_anomaly_ids:
        finding_counts = Counter(item.split("-", 1)[0] for item in internal_anomaly_ids)
        output["scoring_kind"] = "finding_type_count"
        output["expected_findings_by_type"] = dict(finding_counts)
        output["expected_anomaly_count"] = len(internal_anomaly_ids)
    elif scoring.get("kind") == "no_anomaly":
        output["expected_anomaly_ids"] = []
    if finding_groups:
        output["expected_finding_groups"] = finding_groups
    task_id = task["id"]
    if task_id in TRAP_REASON_ZH:
        output["expected_reason"] = TRAP_REASON_ZH[task_id]
    if task_id == "L3-008":
        output["expected_facts"] = [
            "差旅住宿按员工职级和城市档位共同确定",
            "培训住宿一二三类城市标准分别为500元、420元、350元每人每晚",
            "培训住宿与差旅住宿不得混用",
        ]
    if task_id == "L3-009":
        if comprehensive is None:
            raise ValueError("L3-009 requires Ground Truth-derived comprehensive expectations")
        rule_names = [RULES[rule_type][0] for rule_type in comprehensive["expected_rule_types"]]
        output["rubric_assertions"] = [
            f"报告说明{len(rule_names)}类规则共形成{comprehensive['expected_anomaly_count']}项异常发现。",
            f"报告覆盖{'、'.join(rule_names)}。",
            "record_ids完整覆盖全部异常发现涉及的业务记录。",
            "每类至少给出一个可复核的发现ID及record_id对应示例。",
            "不得把合规边界记录计入异常。",
        ]
        output.update(comprehensive)
    required_citations = FORMAL_CITATIONS.get(task_id, [])
    if required_citations:
        output["required_citations"] = required_citations
    return output


def anomaly_fact(anomaly: dict[str, Any]) -> str:
    params = anomaly.get("params") or {}
    rule = anomaly["rule"]
    if rule == "duplicate_invoice":
        return f"同一发票被重复使用，源金额为{params.get('source_amount')}元"
    if rule == "split_reimbursement":
        return (
            f"{params.get('window_days')}天窗口内合计{params.get('sum_amount')}元，"
            f"超过{params.get('approval_line')}元审批线"
        )
    if rule == "over_standard":
        return (
            f"费用类型{params.get('expense_type')}金额{params.get('amount')}元，"
            f"超过{params.get('limit')}元标准"
        )
    if rule == "budget_overrun":
        return (
            f"部门预算{params.get('annual_budget')}元，报销前累计{params.get('cumulative_before')}元，"
            f"报销后累计{params.get('cumulative_after')}元"
        )
    if rule == "overdue_reimbursement":
        return f"实际间隔{params.get('actual_days')}天，超过{params.get('deadline_days')}天期限"
    return json.dumps(params, ensure_ascii=False, sort_keys=True)


def load_rubric_templates() -> dict[str, list[dict[str, Any]]]:
    templates = json.loads(RUBRIC_CHECKLISTS.read_text(encoding="utf-8"))
    expected_ids = {task_id for task_id, _, _ in CASE_SPECS}
    actual_ids = set(templates)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        raise ValueError(f"rubric checklist keys mismatch: missing={missing}, extra={extra}")
    return templates


def rubric_for_task(
    task_id: str,
    templates: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    checklist = templates.get(task_id)
    if checklist is None:
        raise ValueError(f"missing checklist rubric for {task_id}")
    return {
        "scoring_method": "binary_checklist",
        "item_result_values": [0, 1],
        "normalization": "equal_item_ratio",
        "checklist": checklist,
    }


def build_dataset() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tasks = json.loads(SOURCE_EVALS.read_text(encoding="utf-8"))
    task_map = {task["id"]: task for task in tasks}
    ground_truth = yaml.safe_load(SOURCE_GROUND_TRUTH.read_text(encoding="utf-8"))
    anomaly_map = {item["anomaly_id"]: item for item in ground_truth["anomalies"]}
    rubric_templates = load_rubric_templates()

    cases: list[dict[str, Any]] = []
    evals: list[dict[str, Any]] = []
    for task_id, family, reason in CASE_SPECS:
        task = task_map[task_id]
        finding_groups = (
            finding_groups_for_task(task, anomaly_map)
            if family == "full_year_audit"
            else None
        )
        comprehensive = (
            comprehensive_expectations(task, ground_truth)
            if task_id == "L3-009"
            else None
        )
        source_prompt = task["prompt_variants"]["precise"]
        prompt = PROMPT_OVERRIDES.get(task_id, source_prompt)
        rubric = rubric_for_task(task_id, rubric_templates)

        case = {
            "id": task_id,
            "source_task_id": task_id,
            "level": task["level"],
            "category": task["category"],
            "case_family": family,
            "prompt": prompt,
            "selection_reason": reason,
            "ground_truth_refs": formal_ground_truth_refs(task),
            "expected_output": expected_output(task, comprehensive, finding_groups),
            "rubric": rubric,
        }
        if prompt != source_prompt:
            case["source_prompt"] = source_prompt
            case["prompt_change_reason"] = PROMPT_CHANGE_REASONS[task_id]
        cases.append(case)
        evals.append(
            {
                "id": task_id,
                "level": task["level"],
                "category": task["category"],
                "case_family": family,
                "prompt_variants": {"precise": prompt},
                "scoring": {"type": "case_rubric", "rubric_ref": f"cases.json#/cases/{len(cases) - 1}/rubric"},
            }
        )

    counts = Counter(case["case_family"] for case in cases)
    dataset = {
        "dataset_id": "securities-expense-audit-formal-15-v7",
        "rubric_version": "atomic-binary-checklist-v5",
        "case_count": len(cases),
        "source": {"evals": "data/evals.json", "ground_truth": "data/ground_truth.yaml"},
        "case_family_counts": dict(sorted(counts.items())),
        "cases": cases,
    }
    return dataset, evals


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Build the {len(CASE_SPECS)}-case formal dataset and case-by-case rubrics."
    )
    parser.add_argument("--check", action="store_true", help="Fail if generated files are missing or stale.")
    args = parser.parse_args()
    dataset, evals = build_dataset()
    expected = {OUTPUT_CASES: render(dataset), OUTPUT_EVALS: render(evals)}
    if args.check:
        stale = [str(path) for path, content in expected.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if stale:
            raise SystemExit("stale generated files: " + ", ".join(stale))
        print(json.dumps({"status": "pass", "case_count": len(dataset["cases"]), "files": [str(path) for path in expected]}, ensure_ascii=False))
        return 0
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    print(json.dumps({"status": "built", "case_count": len(dataset["cases"]), "files": [str(path) for path in expected]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
