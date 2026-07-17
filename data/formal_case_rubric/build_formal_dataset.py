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
    "DUP": ("重复报销", "费用报销管理办法-6.1"),
    "SPLIT": ("拆分报销", "费用报销管理办法-6.2"),
    "OVERSTD": ("超标准", "费用报销管理办法-6.3"),
    "BUDGET": ("超预算", "预算管理办法-4.1"),
    "OVERDUE": ("超期报销", "费用报销管理办法-6.4"),
}


def anchors(full: str, partial: str, zero: str) -> dict[str, str]:
    return {"full": full, "partial": partial, "zero": zero}


def criterion(
    criterion_id: str,
    title: str,
    description: str,
    weight: int,
    metric: str,
    evaluation_mode: str,
    expected: Any,
    evidence_sources: list[str],
    full: str,
    partial: str,
    zero: str,
) -> dict[str, Any]:
    return {
        "id": criterion_id,
        "title": title,
        "description": description,
        "weight": weight,
        "metric": metric,
        "evaluation_mode": evaluation_mode,
        "expected": expected,
        "evidence_sources": evidence_sources,
        "anchors": anchors(full, partial, zero),
    }


def expected_output(task: dict[str, Any]) -> dict[str, Any]:
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
    required_citations = [
        ref for ref in task["ground_truth_refs"] if ref.startswith(("clause:", "document:", "policy:"))
    ]
    if required_citations:
        output["required_citations"] = required_citations
    return output


def critical_failures(*, trap: bool = False, version: bool = False, full_year: bool = False) -> list[dict[str, Any]]:
    failures = [
        {
            "id": "fabricated-record-id",
            "condition": "提交数据库中不存在的record_id，或用无关记录支撑核心结论",
            "score_cap": 20,
        }
    ]
    if trap:
        failures.append(
            {
                "id": "trap-false-positive",
                "condition": "把本题合规记录判为实质异常",
                "score_cap": 30,
            }
        )
    if version:
        failures.append(
            {
                "id": "deprecated-policy-as-current",
                "condition": "使用已废止制度形成当前适用结论",
                "score_cap": 40,
            }
        )
    if full_year:
        failures.append(
            {
                "id": "partial-scan-presented-as-complete",
                "condition": "只检查部分月份或样例记录，却将结果表述为全年完整扫描",
                "score_cap": 50,
            }
        )
    return failures


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


def policy_rubric(task_id: str) -> dict[str, Any]:
    if task_id == "L1-001":
        criteria = [
            criterion("current-threshold", "现行金额", "指出现行部门总经理审批线", 45, "conclusion", "hybrid", "10000元，达到该金额即进入该审批档位", ["final_answer", "submitted_json"], "金额和包含边界均正确", "金额正确但边界表达不清", "金额错误或未回答"),
            criterion("current-version", "现行版本", "明确结论基于2025修订版或现行制度", 20, "policy", "hybrid", "2025修订版为现行制度", ["final_answer", "tool_trace"], "明确识别现行版本", "只写现行但无版本依据", "使用旧版作为当前依据"),
            criterion("policy-citation", "制度依据", "引用审批档位的有效制度或授权附件", 20, "policy", "hybrid", ["费用报销管理办法", "授权管理办法附件二"], ["submitted_json", "tool_trace"], "引用有效且能支持10000元", "只引用制度名称未定位审批档位", "无引用或引用无关制度"),
            criterion("old-value-control", "旧值排除", "不把2022版8000元旧值当作当前标准", 10, "false_positive", "llm", "8000元不得作为当前审批线", ["final_answer"], "明确排除旧值", "未提旧值但当前值正确", "把8000元作为当前值"),
            criterion("submission", "结果提交", "最终字段完整且结论一致", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
        ]
    elif task_id == "L1-003":
        criteria = [
            criterion("old-threshold", "旧版金额", "指出2022版部门总经理审批线", 30, "conclusion", "hybrid", "8000元", ["final_answer", "submitted_json"], "准确给出8000元", "表达为约8000元但语义明确", "金额错误或缺失"),
            criterion("deprecated-status", "废止状态", "明确2022版旧值现在已废止", 30, "policy", "hybrid", "2022版8000元已废止", ["final_answer", "tool_trace"], "明确说明已废止", "仅说不是现行但状态不清", "称其仍有效"),
            criterion("current-context", "现行对照", "给出现行10000元以完成版本对照", 20, "reasoning", "hybrid", "2025修订版现行值10000元", ["final_answer", "tool_trace"], "现行值和版本均正确", "只给现行值或只给版本", "现行对照错误"),
            criterion("version-citation", "版本证据", "引用新旧制度的状态或替代关系", 15, "policy", "hybrid", ["2022版废止标识", "2025修订版现行标识"], ["submitted_json", "tool_trace"], "新旧证据完整", "只有一侧证据", "无版本证据"),
            criterion("submission", "结果提交", "最终字段完整且结论一致", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
        ]
    elif task_id == "L3-006":
        criteria = [
            criterion("current-value", "现行审批线", "指出2025修订版现行值", 30, "conclusion", "hybrid", "10000元", ["final_answer", "submitted_json"], "现行值准确", "值正确但版本表达不清", "现行值错误"),
            criterion("deprecated-value", "旧版状态", "指出2022版8000元已经废止", 25, "policy", "hybrid", "8000元已废止", ["final_answer", "tool_trace"], "金额和废止状态均正确", "仅正确一项", "称旧值仍有效"),
            criterion("applicable-version", "适用版本", "明确当前应采用2025修订版", 20, "reasoning", "llm", "采用2025修订版，不采用2022版", ["final_answer", "tool_trace"], "选择正确并说明时间适用关系", "选择正确但理由薄弱", "选择旧版"),
            criterion("two-version-evidence", "双版本证据", "提供新旧制度的可核查出处", 20, "policy", "hybrid", ["01_expense_reimbursement_2025.md", "02_expense_reimbursement_2022_deprecated.md"], ["submitted_json", "tool_trace"], "两份制度证据均完整", "只有一份有效证据", "无有效证据"),
            criterion("submission", "结果提交", "最终字段完整且结论一致", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
        ]
    else:
        criteria = [
            criterion("travel-policy", "差旅住宿适用制度", "指出差旅住宿适用差旅费管理办法", 25, "policy", "hybrid", "差旅费管理办法", ["final_answer", "tool_trace"], "制度和场景均正确", "制度正确但场景不清", "制度错误"),
            criterion("training-policy", "培训住宿适用制度", "指出培训期间住宿适用培训费管理办法", 25, "policy", "hybrid", "培训费管理办法", ["final_answer", "tool_trace"], "制度和场景均正确", "制度正确但场景不清", "制度错误"),
            criterion("no-mixing", "不得混用", "解释两套标准因适用事项和数值不同不能混用", 25, "reasoning", "llm", "差旅与培训是不同业务场景，标准表和数值不同", ["final_answer"], "场景与数值差异均说明", "只说明其中一个差异", "认为可以混用"),
            criterion("comparison-evidence", "比较证据", "引用两份制度并给出可核查的比较依据", 20, "evidence", "hybrid", ["04_travel_expense.md", "05_training_expense.md"], ["submitted_json", "tool_trace"], "两份制度证据完整", "只有一份有效证据", "无有效证据"),
            criterion("submission", "结果提交", "最终字段完整且结论一致", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
        ]
    return {
        "max_score": 100,
        "pass_score": 70,
        "criteria": criteria,
        "critical_failures": critical_failures(version=True),
    }


def record_audit_rubric(task: dict[str, Any], anomaly_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected_ids = task["scoring"]["expected_anomaly_ids"]
    expected_records = task["scoring"]["expected_record_ids"]
    anomaly = anomaly_map[expected_ids[0]]
    prefix = expected_ids[0].split("-", 1)[0]
    rule_name, clause = RULES[prefix]
    fact = anomaly_fact(anomaly)
    criteria = [
        criterion("audit-conclusion", "异常结论", f"正确判断本案构成{rule_name}", 20, "conclusion", "hybrid", {"rule": rule_name, "anomaly_ids": expected_ids}, ["final_answer", "submitted_json"], "结论和异常类型均正确", "识别可疑但结论不明确", "判为无异常或类型错误"),
        criterion("anomaly-id", "异常标识", f"准确返回本案异常ID {', '.join(expected_ids)}", 15, "evidence", "deterministic", expected_ids, ["submitted_json"], "集合完全一致", "核心结论正确但异常ID缺失", "返回错误异常ID"),
        criterion("record-set", "记录证据集合", f"完整返回关联记录 {', '.join(expected_records)}", 25, "evidence", "deterministic", expected_records, ["submitted_json", "tool_trace"], "集合准确且无多余记录", "只遗漏一个关联记录且无错误记录", "核心记录缺失或含无关记录"),
        criterion("policy-basis", "制度依据", f"引用{clause}并说明其适用性", 15, "policy", "hybrid", clause, ["submitted_json", "tool_trace"], "条款有效且直接支持结论", "制度正确但条款定位不完整", "无依据或使用错误制度"),
        criterion("case-reasoning", "案件推理", f"用业务数据说明：{fact}", 20, "reasoning", "hybrid", fact, ["final_answer", "tool_trace", "workspace_artifact"], "关键数值或关联事实完整且计算一致", "结论正确但只给部分事实", "推理与数据矛盾"),
        criterion("submission", "结果提交", "最终字段完整且中间证据一致", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
    ]
    return {
        "max_score": 100,
        "pass_score": 70,
        "criteria": criteria,
        "critical_failures": critical_failures(),
    }


def full_year_rubric(task: dict[str, Any]) -> dict[str, Any]:
    expected_ids = task["scoring"]["expected_anomaly_ids"]
    expected_records = task["scoring"]["expected_record_ids"]
    prefix = expected_ids[0].split("-", 1)[0]
    rule_name, clause = RULES[prefix]
    criteria = [
        criterion("all-anomaly-ids", "异常完整召回", f"返回全年{rule_name}的全部{len(expected_ids)}个异常ID", 25, "conclusion", "deterministic", expected_ids, ["submitted_json"], "异常ID集合完全一致", "召回多数且无错误类型", "遗漏一半以上或类型错误"),
        criterion("all-record-ids", "记录完整召回", f"返回全部{len(expected_records)}个关联record_id", 30, "evidence", "deterministic", expected_records, ["submitted_json", "tool_trace"], "记录集合完全一致", "召回率不低于80%且错误记录很少", "召回率低于50%或含大量无关记录"),
        criterion("full-scan-method", "全年扫描方法", f"对全年数据执行可复核的{rule_name}查询或计算", 15, "reasoning", "hybrid", {"rule": rule_name, "expected_count": len(expected_ids)}, ["tool_trace", "workspace_artifact"], "范围、查询和统计均能证明全量扫描", "执行批量查询但范围或复核不完整", "只查看样例记录"),
        criterion("policy-basis", "制度依据", f"引用{clause}并将规则落实到查询条件", 10, "policy", "hybrid", clause, ["submitted_json", "tool_trace"], "条款和查询条件对应", "有制度引用但未对应计算", "无有效制度依据"),
        criterion("false-positive-control", "误报控制", "不混入其他规则异常、TRAP记录或无关业务记录", 15, "false_positive", "hybrid", {"allowed_anomaly_ids": expected_ids, "allowed_record_ids": expected_records}, ["submitted_json", "final_answer"], "无任何实质误报", "仅有一个可解释的边界争议", "混入其他规则或TRAP记录"),
        criterion("submission", "结果提交", "最终字段完整且集合去重", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整、去重且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
    ]
    return {
        "max_score": 100,
        "pass_score": 70,
        "criteria": criteria,
        "critical_failures": critical_failures(full_year=True),
    }


def trap_rubric(task: dict[str, Any]) -> dict[str, Any]:
    records = task["scoring"]["expected_record_ids"]
    reason = task["scoring"]["expected_reason"]
    criteria = [
        criterion("clean-conclusion", "无异常结论", "明确判断本题记录不构成异常", 30, "conclusion", "hybrid", {"anomaly_ids": [], "conclusion": "无异常"}, ["final_answer", "submitted_json"], "明确无异常且无矛盾表述", "倾向合规但表述保留", "报告实质异常"),
        criterion("record-scope", "核查记录范围", f"核查并准确保留记录范围 {', '.join(records)}", 15, "evidence", "deterministic", records, ["submitted_json", "tool_trace"], "记录集合准确", "记录已核查但最终少列一条", "未核查核心记录或加入无关记录"),
        criterion("case-specific-reason", "本题合规原因", f"说明本题专属合规原因：{reason}", 25, "reasoning", "hybrid", reason, ["final_answer", "tool_trace"], "完整说明专属边界或例外", "只说明部分原因", "原因错误或与数据矛盾"),
        criterion("reverse-check", "反向验证", "轨迹中核对阈值、日期、发票或聚合窗口，而非凭题目暗示直接答无异常", 15, "false_positive", "hybrid", "存在针对本题边界条件的工具证据", ["tool_trace", "workspace_artifact"], "完成与本题匹配的反向核查", "只核查一部分关键条件", "没有核查证据"),
        criterion("no-unsupported-output", "无多余异常", "不返回任何异常ID或无关record_id", 10, "false_positive", "deterministic", {"anomaly_ids": [], "record_ids": records}, ["submitted_json"], "无任何多余项", "仅有不影响结论的文字疑虑", "含实质异常或无关记录"),
        criterion("submission", "结果提交", "最终字段完整且结论一致", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
    ]
    return {
        "max_score": 100,
        "pass_score": 70,
        "criteria": criteria,
        "critical_failures": critical_failures(trap=True),
    }


def report_rubric(task_id: str) -> dict[str, Any]:
    if task_id == "L3-007":
        criteria = [
            criterion("threshold", "审批金额", "给出部门总经理审批线10000元", 35, "conclusion", "hybrid", "10000元", ["final_answer", "submitted_json"], "金额和边界正确", "金额正确但边界不清", "金额错误"),
            criterion("two-hop-path", "二跳检索路径", "说明从费用报销办法交叉引用到授权管理办法附件二", 30, "reasoning", "hybrid", ["费用报销管理办法", "授权管理办法附件二"], ["final_answer", "tool_trace"], "两跳路径完整可复核", "找到附件但未说明交叉引用", "停在第一份制度或路径错误"),
            criterion("citations", "双文档证据", "引用两份制度中的相关内容", 20, "policy", "hybrid", ["01_expense_reimbursement_2025.md", "03_authorization_management.md"], ["submitted_json", "tool_trace"], "两份证据均有效", "只有一份有效证据", "无有效证据"),
            criterion("no-premature-stop", "检索完整性", "不因首份制度未列金额而提前结束", 10, "false_positive", "llm", "继续追踪交叉引用", ["tool_trace", "final_answer"], "轨迹证明继续检索", "最终正确但轨迹不完整", "提前停止并猜测"),
            criterion("submission", "结果提交", "最终字段完整且结论一致", 5, "format", "deterministic", "统一Schema可解析", ["submitted_json"], "字段完整且一致", "可修复的非核心缺陷", "无法解析或字段冲突"),
        ]
        failures = critical_failures(version=True)
    elif task_id == "L3-009":
        criteria = [
            criterion("overall-count", "总体数量", "说明全年共30个异常，5个TRAP不计异常", 20, "conclusion", "hybrid", {"anomaly_count": 30, "trap_count": 5}, ["final_answer", "submitted_json"], "两个数量均正确", "只给出一个正确数量", "异常总量明显错误"),
            criterion("five-rule-coverage", "五类规则覆盖", "覆盖重复、拆分、超标准、超预算和超期五类规则", 20, "conclusion", "hybrid", ["重复报销", "拆分报销", "超标准", "超预算", "超期报销"], ["final_answer"], "五类均有结论", "覆盖三至四类", "覆盖少于三类"),
            criterion("representative-ids", "关键异常证据", "每类至少列出一个正确异常ID并给出对应记录证据", 25, "evidence", "hybrid", {"prefixes": ["DUP", "SPLIT", "OVERSTD", "BUDGET", "OVERDUE"], "minimum_per_prefix": 1}, ["submitted_json", "tool_trace"], "五类均有正确ID和记录", "四类有完整证据", "少于三类有完整证据"),
            criterion("policy-coverage", "制度依据", "费用类规则引用费用报销制度，预算规则引用预算制度", 15, "policy", "hybrid", ["费用报销管理办法-6.1至6.4", "预算管理办法-4.1"], ["submitted_json", "tool_trace"], "两类制度与规则准确对应", "只有一类制度完整", "无有效制度依据"),
            criterion("trap-control", "陷阱误报控制", "不得把TRAP-001至TRAP-005计入异常", 15, "false_positive", "deterministic", ["TRAP-001", "TRAP-002", "TRAP-003", "TRAP-004", "TRAP-005"], ["submitted_json", "final_answer"], "无TRAP误报", "只出现非结论性的风险提示", "把任一TRAP计为异常"),
            criterion("report-shape", "报告表达", "报告包含事实、规则、判断、影响和建议，且与结构化结果一致", 5, "format", "llm", ["事实", "规则", "判断", "影响", "建议"], ["final_answer", "submitted_json"], "结构完整且一致", "缺一个非核心部分", "报告与结果冲突"),
        ]
        failures = critical_failures(full_year=True)
        failures.append({"id": "trap-included-as-anomaly", "condition": "把任一TRAP记录计入正式异常", "score_cap": 30})
    else:
        criteria = [
            criterion("current-threshold", "现行审批线", "指出2025修订版现行值为10000元", 30, "conclusion", "hybrid", "10000元", ["final_answer", "submitted_json"], "现行值准确", "金额正确但版本不清", "金额错误"),
            criterion("old-threshold-status", "旧版状态", "指出2022版8000元审批线已废止", 25, "policy", "hybrid", "8000元已废止", ["final_answer", "tool_trace"], "旧值和状态均正确", "只说明其中一项", "把旧值当作现行"),
            criterion("cross-reference", "制度关系", "说明报销办法通过授权管理办法附件二取得现行金额", 20, "reasoning", "hybrid", ["费用报销管理办法", "授权管理办法附件二"], ["final_answer", "tool_trace"], "制度关系完整", "提到两份制度但关系不清", "制度关系错误"),
            criterion("risk-explanation", "误判风险", "解释使用旧线会错误扩大需升级审批的记录范围，并提出版本校验措施", 20, "reasoning", "llm", ["误报风险", "版本校验建议"], ["final_answer"], "风险与建议均具体", "只有风险或建议", "未解释误判影响"),
            criterion("report-shape", "报告表达", "以审计说明形式提交并保持字段一致", 5, "format", "hybrid", "事实、规则、判断和建议一致", ["final_answer", "submitted_json"], "表达完整且一致", "轻微缺项", "报告与结构化结果冲突"),
        ]
        failures = critical_failures(version=True)
    return {"max_score": 100, "pass_score": 70, "criteria": criteria, "critical_failures": failures}


def build_dataset() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tasks = json.loads(SOURCE_EVALS.read_text(encoding="utf-8"))
    task_map = {task["id"]: task for task in tasks}
    ground_truth = yaml.safe_load(SOURCE_GROUND_TRUTH.read_text(encoding="utf-8"))
    anomaly_map = {item["anomaly_id"]: item for item in ground_truth["anomalies"]}

    cases: list[dict[str, Any]] = []
    evals: list[dict[str, Any]] = []
    for task_id, family, reason in CASE_SPECS:
        task = task_map[task_id]
        if family == "policy_and_version":
            rubric = policy_rubric(task_id)
        elif family == "record_audit":
            rubric = record_audit_rubric(task, anomaly_map)
        elif family == "full_year_audit":
            rubric = full_year_rubric(task)
        elif family == "clean_trap":
            rubric = trap_rubric(task)
        else:
            rubric = report_rubric(task_id)

        case = {
            "id": task_id,
            "source_task_id": task_id,
            "level": task["level"],
            "category": task["category"],
            "case_family": family,
            "prompt": task["prompt_variants"]["precise"],
            "selection_reason": reason,
            "ground_truth_refs": task["ground_truth_refs"],
            "expected_output": expected_output(task),
            "rubric": rubric,
        }
        cases.append(case)
        evals.append(
            {
                "id": task_id,
                "level": task["level"],
                "category": task["category"],
                "case_family": family,
                "prompt_variants": {"precise": task["prompt_variants"]["precise"]},
                "scoring": {"type": "case_rubric", "rubric_ref": f"cases.json#/cases/{len(cases) - 1}/rubric"},
            }
        )

    counts = Counter(case["case_family"] for case in cases)
    dataset = {
        "dataset_id": "securities-expense-audit-formal-15-v1",
        "case_count": len(cases),
        "source": {"evals": "data/evals.json", "ground_truth": "data/ground_truth.yaml"},
        "case_family_counts": dict(sorted(counts.items())),
        "cases": cases,
    }
    return dataset, evals


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the 15-case formal dataset and case-by-case rubrics.")
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
