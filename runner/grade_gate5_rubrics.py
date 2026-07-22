from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from formal_eval_plan import (  # noqa: E402
    GROUPS,
    JUDGE_AUDIT_REPEAT_COUNT,
    JUDGE_AUDIT_SAMPLE_RATE,
    JUDGE_AUDIT_SELECTION_SEED,
    JUDGE_AUDIT_TIEBREAKER,
    JUDGE_MAX_TOKENS,
    JUDGE_RETRIES,
    JUDGE_TIMEOUT_SECONDS,
    MODEL_BASE_URL,
    MODEL_NAME,
)


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gate4_formal"
CASES_PATH = ROOT / "data" / "formal_case_rubric" / "cases.json"
DB_PATH = ROOT / "data" / "formal_case_rubric" / "expense_formal.db"
GRADE_ROOT = RUN_ROOT / "gate5_judge_v6"
GRADES_PATH = RUN_ROOT / "gate5_grades_v6.jsonl"
JUDGE_CHECKLIST_BATCH_SIZE = 4
TYPE_ALIASES = {
    "DUP": ("DUP", "REUSE", "REPEAT", "重复"),
    "SPLIT": ("SPLIT", "SPL", "拆分"),
    "OVERSTD": ("OVERSTD", "STD", "EXCESS", "OVERSTANDARD", "超标准"),
    "BUDGET": ("BUDGET", "BUD", "OVER_BUDGET", "OVERBUDGET", "超预算"),
    "OVERDUE": ("OVERDUE", "LATE", "DELAY", "TIM", "超期"),
}
def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def clip(text: Any, limit: int) -> str:
    value = "" if text is None else str(text)
    return value if len(value) <= limit else value[:limit] + "\n...[truncated]"


def normalize_id(value: Any) -> str:
    return re.sub(r"[^A-Z0-9\u4e00-\u9fff]+", "", str(value).upper())


def classify_anomaly_id(value: Any) -> str | None:
    normalized = normalize_id(value)
    for canonical, aliases in TYPE_ALIASES.items():
        if any(normalize_id(alias) in normalized for alias in aliases):
            return canonical
    return None


def expected_anomaly_types(expected_ids: list[str]) -> Counter[str]:
    return Counter(
        anomaly_type
        for anomaly_id in expected_ids
        if (anomaly_type := classify_anomaly_id(anomaly_id))
    )


def candidate_anomaly_types(candidate_ids: list[str], answer: str) -> Counter[str]:
    counts = Counter(
        anomaly_type
        for anomaly_id in candidate_ids
        if (anomaly_type := classify_anomaly_id(anomaly_id))
    )
    if counts or not candidate_ids:
        return counts
    # Generic IDs are allowed. Infer a single-task category from the answer only
    # when all submitted anomalies belong to one clearly named rule.
    matched = [
        canonical
        for canonical, aliases in TYPE_ALIASES.items()
        if any(alias.upper() in answer.upper() for alias in aliases)
    ]
    if len(matched) == 1:
        counts[matched[0]] = len(candidate_ids)
    return counts


def set_metrics(expected: list[str], actual: list[str]) -> dict[str, float]:
    expected_set = set(expected)
    actual_set = set(actual)
    true_positive = len(expected_set & actual_set)
    precision = true_positive / len(actual_set) if actual_set else (1.0 if not expected_set else 0.0)
    recall = true_positive / len(expected_set) if expected_set else (1.0 if not actual_set else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "exact": expected_set == actual_set,
        "missing_count": len(expected_set - actual_set),
        "extra_count": len(actual_set - expected_set),
    }


def anomaly_metrics(expected: list[str], actual: list[str], answer: str) -> dict[str, Any]:
    expected_counter = expected_anomaly_types(expected)
    actual_counter = candidate_anomaly_types(actual, answer)
    if not expected and not actual:
        precision = recall = f1 = 1.0
    elif not expected:
        precision = recall = f1 = 0.0
    elif not actual:
        precision = recall = f1 = 0.0
    else:
        matches = sum(min(count, actual_counter.get(kind, 0)) for kind, count in expected_counter.items())
        precision = matches / len(actual)
        recall = matches / len(expected)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "count_exact": len(expected) == len(actual),
        "expected_types": dict(expected_counter),
        "actual_types": dict(actual_counter),
    }


def valid_record_ids() -> set[str]:
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute("SELECT record_id FROM expense_records").fetchall()
    return {str(row[0]) for row in rows}


def summarize_tools(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    counts = Counter(str(row.get("tool", "unknown")) for row in rows)
    failed = [row for row in rows if row.get("ok") is False]
    samples: list[dict[str, Any]] = []
    for row in rows:
        if len(samples) >= 36:
            break
        samples.append(
            {
                "tool": row.get("tool"),
                "arguments": row.get("arguments"),
                "ok": row.get("ok"),
                "result_preview": clip(
                    json.dumps(row.get("result_preview"), ensure_ascii=False),
                    500,
                ),
                "error": clip(row.get("error"), 250),
            }
        )
    return {
        "call_count": len(rows),
        "tool_counts": dict(counts),
        "failed_count": len(failed),
        "samples": samples,
    }


def deterministic_diagnostics(
    case: dict[str, Any],
    submission: dict[str, Any],
    receipt: dict[str, Any],
    run_result: dict[str, Any],
    existing_record_ids: set[str],
) -> dict[str, Any]:
    expected = case["expected_output"]
    actual_anomalies = [str(item) for item in submission.get("anomaly_ids", [])]
    actual_records = [str(item) for item in submission.get("record_ids", [])]
    answer = str(submission.get("answer", ""))
    expected_anomalies = [str(item) for item in expected.get("expected_anomaly_ids", [])]
    if not expected_anomalies:
        expected_anomalies = [
            f"{rule_type}-{index + 1:03d}"
            for rule_type, count in (expected.get("expected_findings_by_type") or {}).items()
            for index in range(int(count))
        ]
    expected_records = [str(item) for item in expected.get("expected_record_ids", [])]
    excluded_records = {str(item) for item in expected.get("excluded_record_ids", [])}
    excluded_records_in_submission = sorted(excluded_records & set(actual_records))
    unknown_records = sorted(set(actual_records) - existing_record_ids)
    anomaly = anomaly_metrics(expected_anomalies, actual_anomalies, answer)
    record = set_metrics(expected_records, actual_records) if "expected_record_ids" in expected else None
    trap_case = case["case_family"] == "clean_trap"
    trap_false_positive = trap_case and bool(actual_anomalies)
    trap_tokens = sorted(
        set(re.findall(r"\bTRAP-\d{3}\b", answer.upper()))
        | {item for item in actual_records if item.upper().startswith("TRAP")}
        | {item for item in actual_anomalies if "TRAP" in item.upper()}
    )
    return {
        "submission_accepted": receipt.get("status") == "accepted",
        "schema_valid": receipt.get("status") == "accepted",
        "timed_out": bool(run_result.get("timed_out")),
        "elapsed_seconds": run_result.get("elapsed_seconds"),
        "expected_anomaly_ids": expected_anomalies,
        "actual_anomaly_ids": actual_anomalies,
        "anomaly_metrics": anomaly,
        "expected_record_ids": expected_records if "expected_record_ids" in expected else None,
        "actual_record_ids": actual_records,
        "record_metrics": record,
        "excluded_record_ids": sorted(excluded_records),
        "excluded_record_ids_in_submission": excluded_records_in_submission,
        "unknown_record_ids": unknown_records,
        "trap_false_positive": trap_false_positive,
        "trap_tokens_in_conclusion": trap_tokens,
        "citation_count": len(submission.get("citations", [])),
        "required_citations": expected.get("required_citations", []),
    }


def deterministic_criterion(
    criterion: dict[str, Any],
    diagnostics: dict[str, Any],
) -> dict[str, Any] | None:
    criterion_id = criterion["id"]
    if criterion["evaluation_mode"] != "deterministic":
        return None
    deterministic_rule = criterion.get("deterministic_rule")
    if deterministic_rule == "expected-record-present":
        passed = str(criterion["expected"]) in diagnostics["actual_record_ids"]
        reason = "期望record_id已提交" if passed else "期望record_id缺失"
    elif deterministic_rule == "no-unexpected-records":
        allowed = {str(item) for item in criterion["expected"]}
        extra = sorted(set(diagnostics["actual_record_ids"]) - allowed)
        passed = not extra
        reason = "没有范围外record_id" if passed else f"存在范围外record_id：{extra}"
    elif deterministic_rule == "anomaly-rule-type-exact":
        metrics = diagnostics["anomaly_metrics"]
        passed = set(metrics["actual_types"]) == {str(criterion["expected"])}
        reason = "发现规则类型完全匹配" if passed else "发现规则类型不匹配"
    elif deterministic_rule == "anomaly-count-exact":
        passed = len(diagnostics["actual_anomaly_ids"]) == int(criterion["expected"])
        reason = "发现数量完全匹配" if passed else "发现数量不匹配"
    elif deterministic_rule == "anomaly-type-count-exact":
        expected = criterion["expected"]
        rule_type = str(expected["rule_type"])
        expected_count = int(expected["count"])
        actual_count = int(diagnostics["anomaly_metrics"]["actual_types"].get(rule_type, 0))
        passed = actual_count == expected_count
        reason = (
            f"{rule_type}类发现数量完全匹配"
            if passed
            else f"{rule_type}类发现数量应为{expected_count}，实际为{actual_count}"
        )
    elif deterministic_rule == "no-anomaly-ids":
        passed = not diagnostics["actual_anomaly_ids"]
        reason = "未提交异常ID" if passed else "提交了异常ID"
    elif deterministic_rule == "record-ids-unique":
        actual_records = diagnostics["actual_record_ids"]
        passed = len(actual_records) == len(set(actual_records))
        reason = "record_ids没有重复项" if passed else "record_ids存在重复项"
    elif deterministic_rule in {"record-recall-at-least", "record-precision-at-least"}:
        metric_name = deterministic_rule.removeprefix("record-").removesuffix("-at-least")
        threshold = float(criterion["expected"])
        metrics = diagnostics.get("record_metrics") or {}
        actual = float(metrics.get(metric_name, 0.0))
        passed = actual + 1e-9 >= threshold
        reason = f"record_id{metric_name}={actual:.3f}，阈值={threshold:.3f}"
    elif deterministic_rule in {"anomaly-recall-at-least", "anomaly-precision-at-least"}:
        metric_name = deterministic_rule.removeprefix("anomaly-").removesuffix("-at-least")
        threshold = float(criterion["expected"])
        actual = float(diagnostics["anomaly_metrics"].get(metric_name, 0.0))
        passed = actual + 1e-9 >= threshold
        reason = f"异常发现{metric_name}={actual:.3f}，阈值={threshold:.3f}"
    elif deterministic_rule == "excluded-records-absent":
        excluded = {str(item) for item in criterion["expected"]}
        included = sorted(excluded & set(diagnostics["actual_record_ids"]))
        passed = not included
        reason = "未包含合规边界记录" if passed else f"误报合规边界记录：{included}"
    elif criterion_id == "submission":
        passed = bool(diagnostics["submission_accepted"] and diagnostics["schema_valid"])
        reason = "统一提交已接受且Schema有效" if passed else "未形成被接受的统一提交"
    elif criterion_id in {"anomaly-id", "all-anomaly-ids", "anomaly-type-count", "finding-type-count"}:
        exact = float(diagnostics["anomaly_metrics"]["f1"]) == 1.0
        passed = exact
        reason = (
            "异常类型和数量完全匹配；不要求猜测隐藏内部编号"
            if passed
            else "异常类型或数量未完全匹配"
        )
    elif criterion_id in {"record-set", "all-record-ids", "record-scope"}:
        metrics = diagnostics.get("record_metrics")
        passed = bool(metrics and metrics.get("exact"))
        reason = "record_ids集合完全匹配" if passed else "record_ids集合不完全匹配"
    elif criterion_id == "no-unsupported-output":
        record_metrics = diagnostics.get("record_metrics") or {}
        passed = not diagnostics["actual_anomaly_ids"] and bool(record_metrics.get("exact"))
        reason = (
            "未提交实质异常，且record_ids仅包含题目要求核查的记录"
            if passed
            else "提交了实质异常，或record_ids包含缺失/多余记录"
        )
    elif criterion_id == "trap-control":
        included = diagnostics.get("excluded_record_ids_in_submission", [])
        passed = not included and not diagnostics["trap_tokens_in_conclusion"]
        reason = (
            "未将合规边界记录计入异常"
            if passed
            else f"误报合规边界记录：{included}"
        )
    else:
        return None
    value = 1 if passed else 0
    return {
        "id": criterion_id,
        "value": value,
        "reason": reason,
        "answer_evidence": "",
        "trace_evidence": "规则程序计算",
        "source": "rule",
    }


def evaluate_critical_failures(
    case: dict[str, Any],
    diagnostics: dict[str, Any],
) -> tuple[list[dict[str, Any]], float | None]:
    triggered: list[dict[str, Any]] = []
    for definition in case["rubric"].get("critical_failures", []):
        rule = str(definition["deterministic_rule"])
        hit = False
        detail = ""
        if rule == "unexpected-anomaly-reported":
            hit = bool(diagnostics["actual_anomaly_ids"])
            detail = f"实际提交异常数={len(diagnostics['actual_anomaly_ids'])}"
        elif rule == "record-precision-below":
            threshold = float(definition["expected"])
            actual = float((diagnostics.get("record_metrics") or {}).get("precision", 0.0))
            hit = actual + 1e-9 < threshold
            detail = f"record_id precision={actual:.3f}，下限={threshold:.3f}"
        elif rule == "anomaly-precision-below":
            threshold = float(definition["expected"])
            actual = float(diagnostics["anomaly_metrics"].get("precision", 0.0))
            hit = actual + 1e-9 < threshold
            detail = f"异常发现precision={actual:.3f}，下限={threshold:.3f}"
        else:
            raise ValueError(f"unsupported critical failure rule: {rule}")
        if hit:
            triggered.append(
                {
                    "id": definition["id"],
                    "check": definition["check"],
                    "score_cap": float(definition["score_cap"]),
                    "reason": detail,
                }
            )
    score_cap = min((item["score_cap"] for item in triggered), default=None)
    return triggered, score_cap


def checklist_pass_rate(checklist: list[dict[str, Any]]) -> tuple[int, int, float]:
    passed_count = sum(int(item.get("value", 0)) for item in checklist)
    total_count = len(checklist)
    pass_rate = round(100 * passed_count / total_count, 3) if total_count else 0.0
    return passed_count, total_count, pass_rate


def build_judge_messages(
    case: dict[str, Any],
    criteria_to_score: list[dict[str, Any]],
    submission: dict[str, Any],
    evidence_matrix: dict[str, Any],
    validation_report: dict[str, Any],
    diagnostics: dict[str, Any],
    tool_summary: dict[str, Any],
) -> list[dict[str, str]]:
    system = """你是证券费用审计评测的严格判卷员。你必须只依据给定的冻结二元Checklist、候选最终提交和轨迹摘要逐项判断。
要求：
1. 每个检查项只能返回value=0或value=1。满足pass_condition记1，否则记0；禁止部分分、小数分和折中分。
2. 不得因文风、篇幅或候选异常ID命名不同而扣分，只评价事实、范围、制度、证据和推理。
3. 工具调用过并不自动代表结论正确；候选自写的evidence_matrix也不能替代事实核验。
4. answer_evidence和trace_evidence必须简短引用可核查内容，不得输出思维链。
5. 如果检查项的evidence_sources不包含final_answer，仅凭最终答案复述事实不得判1，必须存在对应工具轨迹或工作产物。
6. 所有确定性集合、数量和阈值项目均由规则程序最终裁决，不会提交给你复核。
只输出一个JSON对象，不要Markdown。"""
    payload = {
        "case": {
            "id": case["id"],
            "prompt": case["prompt"],
            "case_family": case["case_family"],
            "expected_output": case["expected_output"],
            "checklist_to_judge": criteria_to_score,
        },
        "candidate_submission": submission,
        "candidate_evidence_matrix": evidence_matrix,
        "candidate_validation_report": validation_report,
        "rule_diagnostics": diagnostics,
        "tool_trace_summary": tool_summary,
        "required_output": {
            "checklist": [
                {
                    "id": "check item id",
                    "value": "0 or 1",
                    "reason": "Chinese concise reason",
                    "answer_evidence": "Chinese concise evidence",
                    "trace_evidence": "Chinese concise evidence",
                }
            ],
            "overall_comment": "Chinese concise summary",
            "confidence": "0..1",
        },
    }
    user = clip(json.dumps(payload, ensure_ascii=False), 52000)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


class DeepSeekJudge:
    def __init__(self) -> None:
        self.base_url = os.environ.get("LLM_BASE_URL", MODEL_BASE_URL).rstrip("/")
        self.model = os.environ.get("LLM_MODEL_NAME", MODEL_NAME)
        self.api_key = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        self.timeout = JUDGE_TIMEOUT_SECONDS
        self.max_tokens = JUDGE_MAX_TOKENS
        self.retries = JUDGE_RETRIES
        if not self.api_key:
            user_key = os.environ.get("LLM_API_KEY_USER")
            if user_key:
                self.api_key = user_key
        if not self.api_key:
            raise RuntimeError("missing LLM_API_KEY")

    def complete(self, messages: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        error: Exception | None = None
        request_max_tokens = self.max_tokens
        for attempt in range(1, self.retries + 1):
            try:
                payload["max_tokens"] = request_max_tokens
                request = urllib.request.Request(
                    f"{self.base_url}/chat/completions",
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw_response = json.loads(response.read().decode("utf-8"))
                choices = raw_response.get("choices") or []
                content = ((choices[0].get("message") or {}).get("content") if choices else None)
                if not content:
                    finish_reason = choices[0].get("finish_reason") if choices else None
                    if finish_reason == "length" and request_max_tokens < 8192:
                        request_max_tokens = 8192
                    raise RuntimeError(
                        f"judge response has empty content (finish_reason={finish_reason})"
                    )
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("judge JSON root must be object")
                return parsed, {
                    "model": self.model,
                    "usage": raw_response.get("usage", {}),
                    "finish_reason": choices[0].get("finish_reason"),
                    "attempt": attempt,
                    "max_tokens": request_max_tokens,
                }
            except (OSError, ValueError, json.JSONDecodeError, urllib.error.HTTPError) as exc:
                error = exc
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 10))
        raise RuntimeError(f"judge failed after {self.retries} attempts: {error}")


def validate_judge_output(
    case: dict[str, Any],
    parsed: dict[str, Any],
    criteria_to_score: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, str]:
    source_criteria = (
        case["rubric"]["checklist"]
        if criteria_to_score is None
        else criteria_to_score
    )
    expected_criteria = {
        item["id"]: item
        for item in source_criteria
    }
    rows = parsed.get("checklist")
    if not isinstance(rows, list):
        rows = parsed.get("criteria")
    if not isinstance(rows, list):
        rows = parsed.get("scores")
    if not isinstance(rows, list) and isinstance(parsed.get("criteria_scores"), dict):
        rows = [
            {"id": criterion_id, **value}
            for criterion_id, value in parsed["criteria_scores"].items()
            if isinstance(value, dict)
        ]
    if (
        not isinstance(rows, list)
        and len(expected_criteria) == 1
        and (parsed.get("id") or parsed.get("criterion_id")) in expected_criteria
    ):
        rows = [parsed]
    if not isinstance(rows, list):
        direct_rows = []
        for criterion_id in expected_criteria:
            value = parsed.get(criterion_id)
            if isinstance(value, dict):
                direct_rows.append({"id": criterion_id, **value})
        rows = direct_rows
    if not isinstance(rows, list):
        raise ValueError("judge checklist must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if isinstance(row, dict) and not row.get("id") and row.get("criterion_id"):
            row = {"id": row["criterion_id"], **row}
        if not isinstance(row, dict) or row.get("id") not in expected_criteria:
            continue
        criterion_id = str(row["id"])
        if criterion_id in seen:
            continue
        raw_value = row.get("value")
        if isinstance(raw_value, bool):
            raw_value = int(raw_value)
        if raw_value not in (0, 1):
            raise ValueError(f"judge checklist value must be 0 or 1: {criterion_id}")
        value = int(raw_value)
        normalized.append(
            {
                "id": criterion_id,
                "value": value,
                "reason": clip(
                    row.get("reason")
                    or row.get("explanation")
                    or row.get("reasoning"),
                    800,
                ),
                "answer_evidence": clip(row.get("answer_evidence"), 800),
                "trace_evidence": clip(row.get("trace_evidence"), 800),
                "source": "llm_judge",
            }
        )
        seen.add(criterion_id)
    missing = set(expected_criteria) - seen
    if missing:
        raise ValueError(f"judge missing criteria: {sorted(missing)}")
    confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.8))))
    comment = parsed.get("overall_comment") or parsed.get("summary") or ""
    return normalized, [], confidence, clip(comment, 1200)


def judge_criteria_batch(
    judge: DeepSeekJudge,
    case: dict[str, Any],
    criteria_batch: list[dict[str, Any]],
    submission: dict[str, Any],
    evidence_matrix: dict[str, Any],
    validation_report: dict[str, Any],
    diagnostics: dict[str, Any],
    tool_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, str, list[dict[str, Any]]]:
    messages = build_judge_messages(
        case,
        criteria_batch,
        submission,
        evidence_matrix,
        validation_report,
        diagnostics,
        tool_summary,
    )
    validation_error: Exception | None = None
    for shape_attempt in range(1, 4):
        try:
            parsed, metadata = judge.complete(messages)
            rows, critical, confidence, comment = validate_judge_output(
                case,
                parsed,
                criteria_batch,
            )
            metadata["shape_attempt"] = shape_attempt
            metadata["criteria_count"] = len(criteria_batch)
            return rows, critical, confidence, comment, [metadata]
        except (TypeError, ValueError, RuntimeError) as exc:
            validation_error = exc
            if shape_attempt < 3:
                expected_ids = [item["id"] for item in criteria_batch]
                messages = [
                    *messages,
                    {
                        "role": "user",
                        "content": (
                            "上一次输出未通过结构校验。请只重新输出本批次结果，"
                            f"并且必须逐项包含以下全部ID且不得改名：{expected_ids}。"
                            f"校验错误：{exc}"
                        ),
                    },
                ]
                time.sleep(shape_attempt * 2)

    if len(criteria_batch) == 1:
        raise RuntimeError(f"judge output validation failed: {validation_error}")

    midpoint = len(criteria_batch) // 2
    left = judge_criteria_batch(
        judge,
        case,
        criteria_batch[:midpoint],
        submission,
        evidence_matrix,
        validation_report,
        diagnostics,
        tool_summary,
    )
    right = judge_criteria_batch(
        judge,
        case,
        criteria_batch[midpoint:],
        submission,
        evidence_matrix,
        validation_report,
        diagnostics,
        tool_summary,
    )
    confidence = (
        left[2] * midpoint + right[2] * (len(criteria_batch) - midpoint)
    ) / len(criteria_batch)
    comment = clip("；".join(item for item in (left[3], right[3]) if item), 1200)
    return (
        left[0] + right[0],
        left[1] + right[1],
        confidence,
        comment,
        left[4] + right[4],
    )


def selected_for_consistency_audit(group: str, task_id: str, criterion_id: str) -> bool:
    material = f"{JUDGE_AUDIT_SELECTION_SEED}:{group}:{task_id}:{criterion_id}".encode()
    bucket = int.from_bytes(hashlib.sha256(material).digest()[:8], "big") / 2**64
    return bucket < JUDGE_AUDIT_SAMPLE_RATE


def merge_consistency_votes(
    initial_rows: list[dict[str, Any]],
    repeated_runs: list[list[dict[str, Any]]],
) -> tuple[dict[str, Any], dict[str, int], list[str]]:
    initial_by_id = {row["id"]: row for row in initial_rows}
    repeated_by_run = [{row["id"]: row for row in rows} for rows in repeated_runs]
    disagreements: list[str] = []
    majority_values: dict[str, int] = {}
    tied_ids: list[str] = []
    audited_ids = sorted(repeated_by_run[0]) if repeated_by_run else []
    agreements = 0
    for criterion_id in audited_ids:
        values = [int(initial_by_id[criterion_id]["value"])] + [
            int(run[criterion_id]["value"]) for run in repeated_by_run
        ]
        if len(set(values)) == 1:
            agreements += 1
        else:
            disagreements.append(criterion_id)
        ones = sum(values)
        zeros = len(values) - ones
        if ones == zeros:
            tied_ids.append(criterion_id)
        else:
            majority_values[criterion_id] = 1 if ones > zeros else 0
    metadata = {
        "sampled_count": len(audited_ids),
        "agreement_count": agreements,
        "agreement_rate": round(agreements / len(audited_ids), 6) if audited_ids else None,
        "disagreement_ids": disagreements,
        "tied_ids": tied_ids,
    }
    return metadata, majority_values, tied_ids


def grade_one(
    judge: DeepSeekJudge,
    case: dict[str, Any],
    group: str,
    existing_record_ids: set[str],
    dataset_id: str,
    rubric_version: str,
) -> dict[str, Any]:
    task_id = case["id"]
    base = RUN_ROOT / group / task_id
    workspace = base / "workspace"
    run_result = load_json(base / "run_result.json", {}) or {}
    submission = load_json(workspace / "final_submission.json", {}) or {}
    receipt = load_json(workspace / "submission_receipt.json", {}) or {}
    evidence_matrix = load_json(workspace / "work" / "evidence_matrix.json", {}) or {}
    validation_report = load_json(workspace / "work" / "validation_report.json", {}) or {}
    diagnostics = deterministic_diagnostics(
        case,
        submission,
        receipt,
        run_result,
        existing_record_ids,
    )
    deterministic_rows = [
        row
        for criterion in case["rubric"]["checklist"]
        if (row := deterministic_criterion(criterion, diagnostics)) is not None
    ]
    criteria_to_score = [
        criterion
        for criterion in case["rubric"]["checklist"]
        if criterion["evaluation_mode"] != "deterministic"
    ]
    missing_submission = receipt.get("status") != "accepted" or not submission
    judge_meta: dict[str, Any] = {}
    if missing_submission:
        llm_rows = [
            {
                "id": criterion["id"],
                "value": 0,
                "reason": "任务未形成被接受的最终提交",
                "answer_evidence": "",
                "trace_evidence": "run_result/submission_receipt",
                "source": "terminal_rule",
            }
            for criterion in criteria_to_score
        ]
        judge_critical: list[dict[str, Any]] = []
        confidence = 1.0
        comment = "未提交任务，Rubric得分为0。"
    else:
        tool_summary = summarize_tools(workspace / "traces" / "tool_calls.jsonl")
        llm_rows = []
        judge_critical = []
        batch_confidences: list[float] = []
        batch_comments: list[str] = []
        batch_metadata: list[dict[str, Any]] = []
        total_usage: Counter[str] = Counter()

        for start in range(0, len(criteria_to_score), JUDGE_CHECKLIST_BATCH_SIZE):
            criteria_batch = criteria_to_score[start : start + JUDGE_CHECKLIST_BATCH_SIZE]
            rows, critical, batch_confidence, batch_comment, metadata_rows = judge_criteria_batch(
                judge,
                case,
                criteria_batch,
                submission,
                evidence_matrix,
                validation_report,
                diagnostics,
                tool_summary,
            )

            llm_rows.extend(rows)
            judge_critical.extend(critical)
            batch_confidences.append(batch_confidence)
            if batch_comment:
                batch_comments.append(batch_comment)
            batch_metadata.extend(metadata_rows)
            for metadata in metadata_rows:
                for name, value in metadata.get("usage", {}).items():
                    if isinstance(value, (int, float)):
                        total_usage[name] += value

        audit_criteria = [
            criterion
            for criterion in criteria_to_score
            if selected_for_consistency_audit(group, task_id, criterion["id"])
        ]
        repeated_runs: list[list[dict[str, Any]]] = []
        audit_metadata: list[dict[str, Any]] = []
        for _repeat in range(1, JUDGE_AUDIT_REPEAT_COUNT):
            repeated_rows: list[dict[str, Any]] = []
            for start in range(0, len(audit_criteria), JUDGE_CHECKLIST_BATCH_SIZE):
                criteria_batch = audit_criteria[start : start + JUDGE_CHECKLIST_BATCH_SIZE]
                rows, _critical, _confidence, _comment, metadata_rows = judge_criteria_batch(
                    judge,
                    case,
                    criteria_batch,
                    submission,
                    evidence_matrix,
                    validation_report,
                    diagnostics,
                    tool_summary,
                )
                repeated_rows.extend(rows)
                audit_metadata.extend(metadata_rows)
                for metadata in metadata_rows:
                    for name, value in metadata.get("usage", {}).items():
                        if isinstance(value, (int, float)):
                            total_usage[name] += value
            repeated_runs.append(repeated_rows)

        consistency, majority_values, tied_ids = merge_consistency_votes(
            llm_rows,
            repeated_runs,
        )
        tiebreak_rows: list[dict[str, Any]] = []
        if tied_ids and JUDGE_AUDIT_TIEBREAKER:
            definitions_by_id = {criterion["id"]: criterion for criterion in audit_criteria}
            tied_criteria = [definitions_by_id[criterion_id] for criterion_id in tied_ids]
            for start in range(0, len(tied_criteria), JUDGE_CHECKLIST_BATCH_SIZE):
                criteria_batch = tied_criteria[start : start + JUDGE_CHECKLIST_BATCH_SIZE]
                rows, _critical, _confidence, _comment, metadata_rows = judge_criteria_batch(
                    judge,
                    case,
                    criteria_batch,
                    submission,
                    evidence_matrix,
                    validation_report,
                    diagnostics,
                    tool_summary,
                )
                tiebreak_rows.extend(rows)
                audit_metadata.extend(metadata_rows)
                for metadata in metadata_rows:
                    for name, value in metadata.get("usage", {}).items():
                        if isinstance(value, (int, float)):
                            total_usage[name] += value
            majority_values.update({row["id"]: int(row["value"]) for row in tiebreak_rows})
        rows_by_id = {row["id"]: row for row in llm_rows}
        repeated_by_id = {
            row["id"]: row
            for repeated in repeated_runs
            for row in repeated
        }
        tiebreak_by_id = {row["id"]: row for row in tiebreak_rows}
        for criterion_id, value in majority_values.items():
            selected = tiebreak_by_id.get(criterion_id) or repeated_by_id.get(criterion_id)
            if selected is not None and int(rows_by_id[criterion_id]["value"]) != value:
                rows_by_id[criterion_id] = {
                    **selected,
                    "value": value,
                    "source": "llm_judge_consensus",
                }
        llm_rows = [rows_by_id[row["id"]] for row in llm_rows]
        consistency["tiebreak_count"] = len(tiebreak_rows)
        consistency["repeat_count"] = JUDGE_AUDIT_REPEAT_COUNT
        consistency["batches"] = audit_metadata

        confidence = (
            sum(batch_confidences) / len(batch_confidences)
            if batch_confidences
            else 1.0
        )
        comment = clip("；".join(batch_comments), 1200)
        judge_meta = {
            "model": judge.model,
            "usage": dict(total_usage),
            "batch_count": len(batch_metadata),
            "batches": batch_metadata,
            "consistency_audit": consistency,
        }
        parsed = {
            "checklist": llm_rows,
            "overall_comment": comment,
            "confidence": confidence,
        }
    criteria_by_id = {row["id"]: row for row in deterministic_rows}
    criteria_by_id.update({row["id"]: row for row in llm_rows})
    criteria = [criteria_by_id[item["id"]] for item in case["rubric"]["checklist"]]
    passed_count, total_count, final_score = checklist_pass_rate(criteria)
    critical_failures, score_cap = evaluate_critical_failures(case, diagnostics)
    result = {
        "group": group,
        "dataset_id": dataset_id,
        "rubric_version": rubric_version,
        "task_id": task_id,
        "case_family": case["case_family"],
        "category": case["category"],
        "graded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "checklist_passed": passed_count,
        "checklist_total": total_count,
        "checklist_pass_rate": final_score,
        "checklist": criteria,
        "critical_failures": critical_failures,
        "score_cap": score_cap,
        "diagnostics": diagnostics,
        "judge": {
            "status": "not_required" if missing_submission else "ok",
            "confidence": confidence,
            "overall_comment": comment,
            **judge_meta,
        },
        "run_path": base.relative_to(ROOT).as_posix(),
    }
    destination = GRADE_ROOT / group
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f"{task_id}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not missing_submission:
        (destination / f"{task_id}.judge-output.json").write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return result


def load_existing_grades() -> dict[tuple[str, str], dict[str, Any]]:
    existing: dict[tuple[str, str], dict[str, Any]] = {}
    if not GRADES_PATH.exists():
        return existing
    for row in load_jsonl(GRADES_PATH):
        if row.get("group") and row.get("task_id"):
            existing[(str(row["group"]), str(row["task_id"]))] = row
    return existing


def write_grades(rows: list[dict[str, Any]]) -> None:
    rows.sort(key=lambda item: (GROUPS.index(item["group"]), item["task_id"]))
    GRADES_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grade GATE5 case-by-case Rubrics")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--group", action="append", choices=GROUPS)
    parser.add_argument("--task-id", action="append")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--only-errors", action="store_true")
    parser.add_argument("--reapply-rules", action="store_true")
    return parser.parse_args()


def reapply_rules(
    cases: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    updated = []
    for row in rows:
        case = cases[row["task_id"]]
        raw_judge_path = (
            GRADE_ROOT
            / row["group"]
            / f"{row['task_id']}.judge-output.json"
        )
        if raw_judge_path.exists():
            raw_judge = load_json(raw_judge_path, {}) or {}
            judge_criteria_ids = {
                str(item.get("id") or item.get("criterion_id"))
                for item in (
                    raw_judge.get("checklist")
                    or raw_judge.get("criteria")
                    or raw_judge.get("scores")
                    or []
                )
                if isinstance(item, dict)
            }
            if isinstance(raw_judge.get("criteria_scores"), dict):
                judge_criteria_ids |= set(raw_judge["criteria_scores"])
            judge_criteria_ids |= {
                item["id"]
                for item in case["rubric"]["checklist"]
                if isinstance(raw_judge.get(item["id"]), dict)
            }
            criteria_to_score = [
                item
                for item in case["rubric"]["checklist"]
                if item["id"] in judge_criteria_ids
            ]
            validate_judge_output(
                case,
                raw_judge,
                criteria_to_score,
            )
        passed_count, total_count, pass_rate = checklist_pass_rate(row.get("checklist", []))
        row.pop("case_score_raw", None)
        critical_failures, score_cap = evaluate_critical_failures(
            case,
            row.get("diagnostics", {}),
        )
        row["critical_failures"] = critical_failures
        row["score_cap"] = score_cap
        row["checklist_passed"] = passed_count
        row["checklist_total"] = total_count
        row["checklist_pass_rate"] = pass_rate
        row.pop("case_score", None)
        row.pop("passed", None)
        row.pop("required_check_failures", None)
        destination = GRADE_ROOT / row["group"] / f"{row['task_id']}.json"
        destination.write_text(
            json.dumps(row, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        updated.append(row)
    write_grades(updated)
    return updated


def main() -> int:
    args = parse_args()
    if not os.environ.get("LLM_API_KEY"):
        # PowerShell processes opened before the user-level variable was set do
        # not inherit it. The launcher can mirror it into this process.
        user_key = os.environ.get("LLM_API_KEY_USER")
        if user_key:
            os.environ["LLM_API_KEY"] = user_key
    dataset = load_json(CASES_PATH)
    cases = {case["id"]: case for case in dataset["cases"]}
    if args.reapply_rules:
        rows = list(load_existing_grades().values())
        expected_grade_count = len(GROUPS) * len(cases)
        if len(rows) != expected_grade_count:
            raise RuntimeError(
                f"expected {expected_grade_count} existing grades, found {len(rows)}"
            )
        reapply_rules(cases, rows)
        print(f"Reapplied deterministic caps to {len(rows)} grades.")
        return 0
    selected_groups = tuple(args.group or GROUPS)
    selected_tasks = set(args.task_id or cases)
    unknown = selected_tasks - set(cases)
    if unknown:
        raise ValueError(f"unknown task IDs: {sorted(unknown)}")
    existing = load_existing_grades()
    pending: list[tuple[str, str]] = []
    for group in selected_groups:
        for task_id in cases:
            if task_id not in selected_tasks:
                continue
            old = existing.get((group, task_id))
            if old and not args.only_errors and not args.reset:
                continue
            if old and args.only_errors and old.get("judge", {}).get("status") != "error":
                continue
            pending.append((group, task_id))
    if not pending:
        print("No pending GATE5 grades.")
        return 0
    judge = DeepSeekJudge()
    record_ids = valid_record_ids()
    print(f"Grading {len(pending)} tasks with {args.workers} workers...")
    completed = dict(existing)
    errors: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        future_map = {
            pool.submit(
                grade_one,
                judge,
                cases[task_id],
                group,
                record_ids,
                str(dataset["dataset_id"]),
                str(dataset["rubric_version"]),
            ): (group, task_id)
            for group, task_id in pending
        }
        for future in as_completed(future_map):
            group, task_id = future_map[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "group": group,
                    "task_id": task_id,
                    "case_family": cases[task_id]["case_family"],
                    "graded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "checklist_passed": 0,
                    "checklist_total": len(cases[task_id]["rubric"]["checklist"]),
                    "checklist_pass_rate": 0.0,
                    "judge": {"status": "error", "error": clip(exc, 2000)},
                }
                errors.append(result)
                print(f"ERROR {group}/{task_id}: {exc}", file=sys.stderr, flush=True)
            else:
                print(
                    f"OK {group}/{task_id} checklist_hit_rate={result['checklist_pass_rate']:.1f}",
                    flush=True,
                )
            completed[(group, task_id)] = result
            write_grades(list(completed.values()))
    print(f"Completed={len(pending) - len(errors)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
