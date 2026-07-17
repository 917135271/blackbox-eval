from __future__ import annotations

import argparse
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


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gate4_formal"
CASES_PATH = ROOT / "data" / "formal_case_rubric" / "cases.json"
DB_PATH = ROOT / "data" / "expense.db"
GRADE_ROOT = RUN_ROOT / "gate5_judge"
GRADES_PATH = RUN_ROOT / "gate5_grades.jsonl"
GROUPS = (
    "ccb-baseline",
    "ccb-enhanced",
    "codex-baseline",
    "codex-enhanced",
    "openclaude-baseline",
    "openclaude-enhanced",
    "opencode-baseline",
    "opencode-enhanced",
    "oh-my-pi-baseline",
    "oh-my-pi-enhanced",
)
TYPE_ALIASES = {
    "DUP": ("DUP", "REUSE", "REPEAT", "重复"),
    "SPLIT": ("SPLIT", "SPL", "拆分"),
    "OVERSTD": ("OVERSTD", "STD", "EXCESS", "OVERSTANDARD", "超标准"),
    "BUDGET": ("BUDGET", "BUD", "OVER_BUDGET", "OVERBUDGET", "超预算"),
    "OVERDUE": ("OVERDUE", "LATE", "DELAY", "TIM", "超期"),
}
POLICY_REFERENCE_GUIDANCE = {
    "费用报销管理办法-6.1": "这是评测规则编号，不是正文第六条第一款；对应现行费用报销管理办法第十条（同一发票最多报销1次）。",
    "费用报销管理办法-6.2": "这是评测规则编号，不是正文第六条第二款；对应现行费用报销管理办法第十一条（7天内拆分规避审批）。",
    "费用报销管理办法-6.3": "这是评测规则编号，不是正文第六条第三款；对应现行费用报销管理办法第十二条，并结合费用类型对应的差旅、培训、招待、办公通讯标准。",
    "费用报销管理办法-6.4": "这是评测规则编号，不是正文第六条第四款；对应现行费用报销管理办法第七条（60天报销期限）。",
    "预算管理办法-4.1": "这是评测规则编号，不是正文第四条第一款；对应现行费用报销管理办法第十三条和预算管理办法第三条。",
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
    expected_records = [str(item) for item in expected.get("expected_record_ids", [])]
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
    weight = float(criterion["weight"])
    if criterion["evaluation_mode"] != "deterministic":
        return None
    if criterion_id == "submission":
        ratio = 1.0 if diagnostics["submission_accepted"] and diagnostics["schema_valid"] else 0.0
        reason = "统一提交已接受且Schema有效" if ratio else "未形成被接受的统一提交"
    elif criterion_id in {"anomaly-id", "all-anomaly-ids"}:
        ratio = float(diagnostics["anomaly_metrics"]["f1"])
        reason = (
            "按异常类型和数量规范化后的F1="
            f"{ratio:.3f}；不因候选未猜中隐藏内部编号而扣分"
        )
    elif criterion_id in {"record-set", "all-record-ids", "record-scope"}:
        metrics = diagnostics.get("record_metrics")
        ratio = float(metrics["f1"]) if metrics else 0.0
        reason = f"record_ids集合F1={ratio:.3f}"
    elif criterion_id == "no-unsupported-output":
        ratio = 1.0 if not diagnostics["actual_anomaly_ids"] else 0.0
        reason = "未提交实质异常" if ratio else "无异常题提交了实质异常"
    elif criterion_id == "trap-control":
        ratio = 1.0 if not diagnostics["trap_tokens_in_conclusion"] else 0.0
        reason = (
            "未将TRAP记录计为异常"
            if ratio
            else f"结论包含TRAP项：{diagnostics['trap_tokens_in_conclusion']}"
        )
    else:
        return None
    return {
        "id": criterion_id,
        "score": round(weight * ratio, 3),
        "reason": reason,
        "answer_evidence": "",
        "trace_evidence": "规则程序计算",
        "source": "rule",
    }


def build_judge_messages(
    case: dict[str, Any],
    criteria_to_score: list[dict[str, Any]],
    submission: dict[str, Any],
    evidence_matrix: dict[str, Any],
    validation_report: dict[str, Any],
    diagnostics: dict[str, Any],
    tool_summary: dict[str, Any],
) -> list[dict[str, str]]:
    system = """你是证券费用审计评测的严格判卷员。你必须只依据给定的冻结Rubric、候选最终提交和轨迹摘要逐项评分。
要求：
1. 每个评分点得分范围为0到该项weight，可给小数；严格遵守full/partial/zero锚点。
2. 不得因文风、篇幅或候选异常ID命名不同而扣分，只评价事实、范围、制度、证据和推理。
3. 工具调用过并不自动代表结论正确；候选自写的evidence_matrix也不能替代事实核验。
4. 对关键错误逐项判断。数据库不存在record_id由规则诊断确定；“无关记录”“部分扫描冒充完整”“废止制度作为现行依据”等结合答案和轨迹判断。
5. answer_evidence和trace_evidence必须简短引用可核查内容，不得输出思维链。
6. 部分客观评分点是规则程序判为未满分后提交复核的。你可以维持规则扣分，也可以依据题意和证据推翻规则负判；你的得分为最终得分。
只输出一个JSON对象，不要Markdown。"""
    payload = {
        "case": {
            "id": case["id"],
            "prompt": case["prompt"],
            "case_family": case["case_family"],
            "expected_output": case["expected_output"],
            "criteria_to_score": criteria_to_score,
            "critical_failures": case["rubric"]["critical_failures"],
            "policy_reference_guidance": POLICY_REFERENCE_GUIDANCE,
        },
        "candidate_submission": submission,
        "candidate_evidence_matrix": evidence_matrix,
        "candidate_validation_report": validation_report,
        "rule_diagnostics": diagnostics,
        "tool_trace_summary": tool_summary,
        "required_output": {
            "criteria": [
                {
                    "id": "criterion id",
                    "score": "0..criterion weight",
                    "reason": "Chinese concise reason",
                    "answer_evidence": "Chinese concise evidence",
                    "trace_evidence": "Chinese concise evidence",
                }
            ],
            "critical_failures": [
                {
                    "id": "critical failure id",
                    "triggered": False,
                    "reason": "Chinese concise reason",
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
        self.base_url = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
        self.model = os.environ.get("LLM_MODEL_NAME", "deepseek-v4-pro")
        self.api_key = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        self.timeout = 180
        self.max_tokens = 8192
        self.retries = 4
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
        for attempt in range(1, self.retries + 1):
            try:
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
                    raise RuntimeError("judge response has empty content")
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("judge JSON root must be object")
                return parsed, {
                    "model": self.model,
                    "usage": raw_response.get("usage", {}),
                    "finish_reason": choices[0].get("finish_reason"),
                    "attempt": attempt,
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
        case["rubric"]["criteria"]
        if criteria_to_score is None
        else criteria_to_score
    )
    expected_criteria = {
        item["id"]: item
        for item in source_criteria
    }
    rows = parsed.get("criteria")
    if not isinstance(rows, list):
        rows = parsed.get("scores")
    if not isinstance(rows, list) and isinstance(parsed.get("criteria_scores"), dict):
        rows = [
            {"id": criterion_id, **value}
            for criterion_id, value in parsed["criteria_scores"].items()
            if isinstance(value, dict)
        ]
    if not isinstance(rows, list):
        direct_rows = []
        for criterion_id in expected_criteria:
            value = parsed.get(criterion_id)
            if isinstance(value, dict):
                direct_rows.append({"id": criterion_id, **value})
        rows = direct_rows
    if not isinstance(rows, list):
        raise ValueError("judge criteria must be a list")
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
        weight = float(expected_criteria[criterion_id]["weight"])
        score = max(0.0, min(weight, float(row.get("score", 0))))
        normalized.append(
            {
                "id": criterion_id,
                "score": round(score, 3),
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
    critical_rows = parsed.get("critical_failures", [])
    if not isinstance(critical_rows, list):
        critical_rows = []
    critical_by_id = {
        str(row.get("id")): row
        for row in critical_rows
        if isinstance(row, dict)
    }
    normalized_critical = []
    for item in case["rubric"]["critical_failures"]:
        judge_row = critical_by_id.get(item["id"], {})
        normalized_critical.append(
            {
                "id": item["id"],
                "triggered": bool(judge_row.get("triggered")),
                "reason": clip(
                    judge_row.get("reason") or judge_row.get("description"),
                    800,
                ),
                "score_cap": item["score_cap"],
                "source": "llm_judge",
            }
        )
    confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.8))))
    comment = parsed.get("overall_comment") or parsed.get("summary") or ""
    return normalized, normalized_critical, confidence, clip(comment, 1200)


def machine_critical_failures(
    case: dict[str, Any],
    diagnostics: dict[str, Any],
) -> list[dict[str, Any]]:
    definitions = {item["id"]: item for item in case["rubric"]["critical_failures"]}
    triggered: dict[str, str] = {}
    if diagnostics["unknown_record_ids"]:
        triggered["fabricated-record-id"] = (
            "提交数据库中不存在的record_id: "
            + ", ".join(diagnostics["unknown_record_ids"][:10])
        )
    record_metrics = diagnostics.get("record_metrics")
    actual_records = diagnostics.get("actual_record_ids", [])
    if (
        isinstance(record_metrics, dict)
        and actual_records
        and (
            float(record_metrics.get("precision", 0)) == 0
            or (
                float(record_metrics.get("precision", 0)) < 0.1
                and int(record_metrics.get("extra_count", 0)) >= 10
            )
        )
    ):
        triggered["fabricated-record-id"] = (
            "提交记录与本题目标集合完全错位，或存在大规模无关记录范围膨胀"
        )
    if diagnostics["trap_false_positive"]:
        triggered["trap-false-positive"] = "无异常/陷阱题提交了实质异常ID"
    if diagnostics["trap_tokens_in_conclusion"]:
        triggered["trap-included-as-anomaly"] = (
            "结论包含TRAP项: " + ", ".join(diagnostics["trap_tokens_in_conclusion"])
        )
    return [
        {
            "id": failure_id,
            "triggered": True,
            "reason": reason,
            "score_cap": definitions[failure_id]["score_cap"],
            "source": "rule",
        }
        for failure_id, reason in triggered.items()
        if failure_id in definitions
    ]


def merge_critical_failures(
    machine: list[dict[str, Any]],
    judge: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = {item["id"]: item for item in machine}
    for item in judge:
        merged[item["id"]] = item
    return list(merged.values())


def grade_one(
    judge: DeepSeekJudge,
    case: dict[str, Any],
    group: str,
    existing_record_ids: set[str],
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
        for criterion in case["rubric"]["criteria"]
        if (row := deterministic_criterion(criterion, diagnostics)) is not None
    ]
    deterministic_by_id = {row["id"]: row for row in deterministic_rows}
    criteria_to_score = [
        criterion
        for criterion in case["rubric"]["criteria"]
        if criterion["evaluation_mode"] != "deterministic"
        or (
            criterion["id"] in deterministic_by_id
            and float(deterministic_by_id[criterion["id"]]["score"])
            < float(criterion["weight"])
        )
    ]
    missing_submission = receipt.get("status") != "accepted" or not submission
    judge_meta: dict[str, Any] = {}
    if missing_submission:
        llm_rows = [
            {
                "id": criterion["id"],
                "score": 0.0,
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
        messages = build_judge_messages(
            case,
            criteria_to_score,
            submission,
            evidence_matrix,
            validation_report,
            diagnostics,
            tool_summary,
        )
        validation_error: Exception | None = None
        for shape_attempt in range(1, 4):
            try:
                parsed, judge_meta = judge.complete(messages)
                llm_rows, judge_critical, confidence, comment = validate_judge_output(
                    case,
                    parsed,
                    criteria_to_score,
                )
                judge_meta["shape_attempt"] = shape_attempt
                break
            except (TypeError, ValueError, RuntimeError) as exc:
                validation_error = exc
                if shape_attempt < 3:
                    time.sleep(shape_attempt * 2)
        else:
            raise RuntimeError(f"judge output validation failed: {validation_error}")
    criteria_by_id = {row["id"]: row for row in deterministic_rows}
    criteria_by_id.update({row["id"]: row for row in llm_rows})
    criteria = [criteria_by_id[item["id"]] for item in case["rubric"]["criteria"]]
    raw_score = round(sum(float(item["score"]) for item in criteria), 3)
    critical = merge_critical_failures(
        machine_critical_failures(case, diagnostics),
        judge_critical,
    )
    active_caps = [
        int(item["score_cap"])
        for item in critical
        if item.get("triggered")
    ]
    final_score = min([raw_score, *active_caps]) if active_caps else raw_score
    result = {
        "group": group,
        "task_id": task_id,
        "case_family": case["case_family"],
        "category": case["category"],
        "graded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "case_score_raw": raw_score,
        "case_score": round(final_score, 3),
        "passed": final_score >= float(case["rubric"]["pass_score"]),
        "criteria": criteria,
        "critical_failures": critical,
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
    parser.add_argument("--rejudge-rule-failures", action="store_true")
    return parser.parse_args()


def reapply_rules(
    cases: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    updated = []
    for row in rows:
        case = cases[row["task_id"]]
        machine = machine_critical_failures(case, row.get("diagnostics", {}))
        raw_judge_path = (
            GRADE_ROOT
            / row["group"]
            / f"{row['task_id']}.judge-output.json"
        )
        judge_critical: list[dict[str, Any]] = []
        if raw_judge_path.exists():
            raw_judge = load_json(raw_judge_path, {}) or {}
            judge_criteria_ids = {
                str(item.get("id") or item.get("criterion_id"))
                for item in (
                    raw_judge.get("criteria")
                    or raw_judge.get("scores")
                    or []
                )
                if isinstance(item, dict)
            }
            if isinstance(raw_judge.get("criteria_scores"), dict):
                judge_criteria_ids |= set(raw_judge["criteria_scores"])
            judge_criteria_ids |= {
                item["id"]
                for item in case["rubric"]["criteria"]
                if isinstance(raw_judge.get(item["id"]), dict)
            }
            criteria_to_score = [
                item
                for item in case["rubric"]["criteria"]
                if item["id"] in judge_criteria_ids
            ]
            _, judge_critical, _, _ = validate_judge_output(
                case,
                raw_judge,
                criteria_to_score,
            )
        row["critical_failures"] = merge_critical_failures(
            machine,
            judge_critical,
        )
        raw_score = round(
            sum(float(item.get("score", 0)) for item in row.get("criteria", [])),
            3,
        )
        caps = [
            int(item["score_cap"])
            for item in row["critical_failures"]
            if item.get("triggered")
        ]
        row["case_score_raw"] = raw_score
        row["case_score"] = round(min([raw_score, *caps]) if caps else raw_score, 3)
        row["passed"] = row["case_score"] >= float(case["rubric"]["pass_score"])
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
        if len(rows) != len(GROUPS) * len(cases):
            raise RuntimeError(f"expected 150 existing grades, found {len(rows)}")
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
            if old and args.rejudge_rule_failures:
                criteria_by_id = {
                    item["id"]: item
                    for item in old.get("criteria", [])
                }
                has_rule_failure = any(
                    item.get("source") == "rule"
                    and float(item.get("score", 0))
                    < float(
                        next(
                            criterion["weight"]
                            for criterion in cases[task_id]["rubric"]["criteria"]
                            if criterion["id"] == item["id"]
                        )
                    )
                    for item in criteria_by_id.values()
                )
                if not has_rule_failure:
                    continue
            elif old and not args.only_errors and not args.reset:
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
            pool.submit(grade_one, judge, cases[task_id], group, record_ids): (group, task_id)
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
                    "case_score": 0.0,
                    "passed": False,
                    "judge": {"status": "error", "error": clip(exc, 2000)},
                }
                errors.append(result)
                print(f"ERROR {group}/{task_id}: {exc}", file=sys.stderr, flush=True)
            else:
                print(
                    f"OK {group}/{task_id} score={result['case_score']:.1f}",
                    flush=True,
                )
            completed[(group, task_id)] = result
            write_grades(list(completed.values()))
    print(f"Completed={len(pending) - len(errors)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
