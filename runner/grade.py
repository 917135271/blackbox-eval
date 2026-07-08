from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from gate2_candidate_check import ROOT, load_eval_config


ALLOWED_JUDGE_FAILURE_LAYERS = {
    "fact_miss",
    "citation_miss",
    "record_id_miss",
    "reasoning_or_retrieval_error",
    "rubric_miss",
    "no_anomaly_false_positive",
    "timeout",
    "judge_error",
}


def normalize(text: Any) -> str:
    raw = "" if text is None else str(text)
    return re.sub(r"[\s,，。；;：:、（）()《》<>【】\[\]\"'`]+", "", raw).lower()


def load_tasks(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    with Path(config["paths"]["evals"]).open("r", encoding="utf-8") as handle:
        return {task["id"]: task for task in json.load(handle)}


def load_ground_truth(config: dict[str, Any]) -> dict[str, Any]:
    ground_truth_path = config.get("paths", {}).get("ground_truth")
    if not ground_truth_path:
        return {}
    path = Path(ground_truth_path)
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def scoring_kind(scoring: dict[str, Any]) -> str | None:
    kind = scoring.get("kind")
    if kind is None and scoring.get("type") == "llm_rubric":
        kind = "llm_rubric"
    return kind


def doc_refs(task: dict[str, Any]) -> list[str]:
    refs = []
    for ref in task.get("ground_truth_refs") or []:
        if isinstance(ref, str) and ref.startswith("document:"):
            refs.append(ref.split(":", 1)[1])
    return refs


def fact_hits(expected_facts: list[str], answer_json: dict[str, Any], final_text: str) -> list[dict[str, Any]]:
    answer_text = " ".join(
        [
            str(answer_json.get("answer", "")),
            json.dumps(answer_json.get("citations", []), ensure_ascii=False),
            final_text,
        ]
    )
    normalized_answer = normalize(answer_text)
    hits = []
    for fact in expected_facts:
        normalized_fact = normalize(fact)
        hit = normalized_fact in normalized_answer
        if not hit:
            numbers = re.findall(r"\d+(?:\.\d+)?", fact)
            words = [part for part in re.split(r"\d+(?:\.\d+)?", normalize(fact)) if len(part) >= 2]
            number_ok = all(number in normalized_answer for number in numbers)
            word_ok = sum(1 for word in words if word in normalized_answer) >= max(1, len(words) // 2)
            hit = number_ok and word_ok
        if not hit:
            numbers = re.findall(r"\d+(?:\.\d+)?", fact)
            number_ok = all(number in normalized_answer for number in numbers)
            expected_chars = {char for char in normalize(fact) if "\u4e00" <= char <= "\u9fff"}
            if expected_chars:
                overlap = sum(1 for char in expected_chars if char in normalized_answer) / len(expected_chars)
                min_overlap = 0.6 if numbers else 0.8
                hit = number_ok and overlap >= min_overlap
        hits.append({"fact": fact, "hit": hit})
    return hits


def citation_ok(task: dict[str, Any], answer_json: dict[str, Any]) -> bool:
    citations = answer_json.get("citations")
    if not isinstance(citations, list) or not citations:
        return False
    expected_docs = set(doc_refs(task))
    if not expected_docs:
        return True
    cited_docs = {str(item.get("doc_id", "")) for item in citations if isinstance(item, dict)}
    return bool(expected_docs & cited_docs)


def base_grade_fields(result: dict[str, Any], task: dict[str, Any], run_path: Path) -> dict[str, Any]:
    scoring = task.get("scoring") or {}
    return {
        "candidate": result.get("candidate"),
        "task_id": result.get("task_id"),
        "level": result.get("level"),
        "category": result.get("category"),
        "variant": result.get("variant"),
        "run_path": str(run_path.relative_to(ROOT)),
        "format_failure": bool(result.get("format_failure")),
        "timeout": bool(result.get("timeout")),
        "exit_code": result.get("exit_code"),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "tool_calls_count": result.get("tool_calls_count"),
        "workdir_diff_empty": result.get("workdir_diff_empty"),
        "kind": scoring_kind(scoring),
    }


def rule_grade_result(result: dict[str, Any], task: dict[str, Any], run_path: Path) -> dict[str, Any]:
    scoring = task.get("scoring") or {}
    kind = scoring_kind(scoring)
    answer_json = result.get("answer_json") if isinstance(result.get("answer_json"), dict) else None
    base = base_grade_fields(result, task, run_path)
    if answer_json is None:
        return {**base, "score": 0.0, "failure_layer": "format_failure"}

    predicted_ids = answer_json.get("anomaly_ids", [])
    if not isinstance(predicted_ids, list):
        predicted_ids = []
    predicted_set = {str(item) for item in predicted_ids}

    if kind in {"anomaly_id_set", "no_anomaly"}:
        expected_set = {str(item) for item in scoring.get("expected_anomaly_ids", [])}
        true_positive = len(predicted_set & expected_set)
        precision = true_positive / len(predicted_set) if predicted_set else (1.0 if not expected_set else 0.0)
        recall = true_positive / len(expected_set) if expected_set else (1.0 if not predicted_set else 0.0)
        score = 1.0 if predicted_set == expected_set else 0.0
        failure_layer = None if score == 1.0 else "reasoning_or_retrieval_error"
        return {
            **base,
            "score": score,
            "expected_anomaly_ids": sorted(expected_set),
            "predicted_anomaly_ids": sorted(predicted_set),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "failure_layer": failure_layer,
        }

    if kind == "record_id_set":
        expected_set = {str(item) for item in scoring.get("expected_anomaly_ids", [])}
        expected_records = [str(item) for item in scoring.get("expected_record_ids", [])]
        answer_text = " ".join(
            [
                str(answer_json.get("answer", "")),
                json.dumps(answer_json.get("citations", []), ensure_ascii=False),
                result.get("final_text", ""),
            ]
        )
        normalized_answer = normalize(answer_text)
        record_hits = [
            {"record_id": record_id, "hit": normalize(record_id) in normalized_answer}
            for record_id in expected_records
        ]
        records_ok = all(item["hit"] for item in record_hits)
        true_positive = len(predicted_set & expected_set)
        precision = true_positive / len(predicted_set) if predicted_set else (1.0 if not expected_set else 0.0)
        recall = true_positive / len(expected_set) if expected_set else (1.0 if not predicted_set else 0.0)
        anomaly_ok = predicted_set == expected_set
        score = 1.0 if anomaly_ok and records_ok else 0.0
        if score == 1.0:
            failure_layer = None
        elif not anomaly_ok:
            failure_layer = "reasoning_or_retrieval_error"
        else:
            failure_layer = "record_id_miss"
        return {
            **base,
            "score": score,
            "expected_anomaly_ids": sorted(expected_set),
            "predicted_anomaly_ids": sorted(predicted_set),
            "expected_record_ids": expected_records,
            "record_hits": record_hits,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "failure_layer": failure_layer,
        }

    if kind == "expected_facts":
        hits = fact_hits(scoring.get("expected_facts", []), answer_json, result.get("final_text", ""))
        facts_ok = all(item["hit"] for item in hits)
        cites_ok = citation_ok(task, answer_json)
        score = 1.0 if facts_ok and cites_ok else 0.0
        if score == 1.0:
            failure_layer = None
        elif not facts_ok:
            failure_layer = "fact_miss"
        else:
            failure_layer = "citation_miss"
        return {
            **base,
            "score": score,
            "fact_hits": hits,
            "citation_ok": cites_ok,
            "failure_layer": failure_layer,
        }

    if kind == "llm_rubric":
        hits = fact_hits(scoring.get("rubric_assertions", []), answer_json, result.get("final_text", ""))
        assertions_ok = all(item["hit"] for item in hits)
        score = 1.0 if assertions_ok else 0.0
        return {
            **base,
            "score": score,
            "rubric_hits": hits,
            "failure_layer": None if score == 1.0 else "rubric_miss",
        }

    return {**base, "score": 0.0, "failure_layer": "unsupported_scoring_kind"}


def selected_truth_items(ground_truth: dict[str, Any], ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    selected: dict[str, list[dict[str, Any]]] = {"anomalies": [], "traps": []}
    for group in ("anomalies", "traps"):
        for item in ground_truth.get(group) or []:
            if str(item.get("anomaly_id")) in ids:
                selected[group].append(item)
    return selected


def build_truth_context(task: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, Any]:
    scoring = task.get("scoring") or {}
    ids = {str(item) for item in scoring.get("expected_anomaly_ids", [])}
    for ref in task.get("ground_truth_refs") or []:
        if isinstance(ref, str) and ref.startswith("ground_truth:"):
            ids.add(ref.split(":", 1)[1])
    selected = selected_truth_items(ground_truth, ids)
    return {
        "meta": ground_truth.get("meta", {}),
        "scoring": scoring,
        "ground_truth_refs": task.get("ground_truth_refs") or [],
        "referenced_ground_truth": selected,
    }


def truncate_text(text: Any, max_chars: int) -> str:
    raw = "" if text is None else str(text)
    if len(raw) <= max_chars:
        return raw
    head = raw[: max_chars // 2]
    tail = raw[-max_chars // 2 :]
    return f"{head}\n\n...[truncated {len(raw) - max_chars} chars]...\n\n{tail}"


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    for block in reversed(blocks):
        try:
            parsed = json.loads(block.strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("judge response did not contain a JSON object")


class LLMJudge:
    def __init__(self, config: dict[str, Any]) -> None:
        model_config = config.get("model") or {}
        judge_config = config.get("judge") or {}
        self.mode = str(judge_config.get("mode", "rule"))
        self.base_url = str(judge_config.get("base_url") or model_config.get("base_url", "")).rstrip("/")
        self.model = str(judge_config.get("model") or model_config.get("model", ""))
        self.api_key_env = str(judge_config.get("api_key_env") or model_config.get("api_key_env", "LLM_API_KEY"))
        self.api_key = os.environ.get(self.api_key_env, "")
        self.temperature = float(judge_config.get("temperature", 0))
        self.max_tokens = int(judge_config.get("max_tokens", 1200))
        self.timeout_seconds = int(judge_config.get("timeout_seconds", 90))
        self.retries = int(judge_config.get("retries", 2))
        self.final_text_max_chars = int(judge_config.get("final_text_max_chars", 12000))
        self.require_parseable_json = bool(judge_config.get("require_parseable_json", False))
        if not self.base_url or not self.model:
            raise RuntimeError("judge.base_url and judge.model must be configured for LLM judge mode")
        if not self.api_key:
            raise RuntimeError(f"missing environment variable {self.api_key_env} for LLM judge")

    def grade(
        self,
        *,
        result: dict[str, Any],
        task: dict[str, Any],
        rule_grade: dict[str, Any],
        ground_truth: dict[str, Any],
    ) -> dict[str, Any]:
        if result.get("timeout"):
            return {
                "score": 0.0,
                "failure_layer": "timeout",
                "judge_reason": "candidate run timed out; no complete answer to judge",
                "judge_confidence": 1.0,
                "judge_missing": [],
                "judge_extra": [],
                "judge_raw": None,
            }

        messages = self.build_messages(result=result, task=task, rule_grade=rule_grade, ground_truth=ground_truth)
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                raw = self.chat_completion(messages)
                parsed = parse_json_object(raw)
                return self.normalize_judge_output(parsed, raw)
            except Exception as exc:  # noqa: BLE001 - keep grading batch moving after retries.
                last_error = exc
                if attempt < self.retries:
                    time.sleep(1.5 * (attempt + 1))
        return {
            "score": 0.0,
            "failure_layer": "judge_error",
            "judge_reason": f"judge call failed: {last_error}",
            "judge_confidence": 0.0,
            "judge_missing": [],
            "judge_extra": [],
            "judge_raw": None,
        }

    def build_messages(
        self,
        *,
        result: dict[str, Any],
        task: dict[str, Any],
        rule_grade: dict[str, Any],
        ground_truth: dict[str, Any],
    ) -> list[dict[str, str]]:
        variant = str(result.get("variant") or "precise")
        prompt_variants = task.get("prompt_variants") or {}
        task_prompt = prompt_variants.get(variant) or prompt_variants.get("precise") or ""
        answer_json = result.get("answer_json") if isinstance(result.get("answer_json"), dict) else None
        context = {
            "task": {
                "id": task.get("id"),
                "level": task.get("level"),
                "category": task.get("category"),
                "variant": variant,
                "prompt": task_prompt,
            },
            "expected": build_truth_context(task, ground_truth),
            "candidate_response": {
                "format_failure": bool(result.get("format_failure")),
                "parse_error": result.get("parse_error"),
                "answer_json": answer_json,
                "final_text": truncate_text(result.get("final_text", ""), self.final_text_max_chars),
            },
            "machine_diagnostics": {
                "tool_calls_count": result.get("tool_calls_count"),
                "exit_code": result.get("exit_code"),
                "workdir_diff_empty": result.get("workdir_diff_empty"),
                "rule_score_for_reference_only": rule_grade.get("score"),
                "rule_failure_layer_for_reference_only": rule_grade.get("failure_layer"),
            },
        }
        system = (
            "You are a strict but fair evaluator for a synthetic audit-agent benchmark. "
            "Judge only from the supplied task, expected ground truth, and candidate response. "
            "Do not reward tool effort by itself. Do not reveal chain-of-thought; give a concise reason."
        )
        user = (
            "请对候选 agent 的回答做语义判卷。\n"
            "判卷原则:\n"
            "1. anomaly_id_set/no_anomaly: 判断候选是否识别了同一个标准异常集合。若候选没有写标准异常ID, "
            "但明确给出了正确规则、正确记录集合,可视为语义命中; 若混入无关异常或把干净陷阱计为异常,判错。\n"
            "2. record_id_set: 必须覆盖期望 record_id, 且不能用无关记录替代。\n"
            "3. expected_facts: 关键事实必须语义完整; citation 应支持答案,但不要求逐字相同。\n"
            "4. llm_rubric: 逐条判断 rubric_assertions 是否满足。\n"
            "5. format_failure 只作为诊断信号; 本次 score 主要衡量内容语义是否正确。\n\n"
            "只返回一个 JSON 对象,不要 Markdown,字段必须为:\n"
            "{\n"
            '  "pass": true/false,\n'
            '  "score": 0 或 1,\n'
            '  "failure_layer": null 或 "fact_miss" 或 "citation_miss" 或 "record_id_miss" 或 '
            '"reasoning_or_retrieval_error" 或 "rubric_miss" 或 "no_anomaly_false_positive",\n'
            '  "reason": "一句话说明判定依据",\n'
            '  "missing": ["缺失点"],\n'
            '  "extra": ["多报或错误点"],\n'
            '  "confidence": 0到1之间的数字\n'
            "}\n\n"
            "判卷上下文如下:\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def chat_completion(self, messages: list[dict[str, str]]) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body[:500]}") from exc
        choices = response_data.get("choices")
        if not choices:
            raise RuntimeError(f"judge response missing choices: {response_data}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"judge response missing content: {response_data}")
        return content.strip()

    def normalize_judge_output(self, parsed: dict[str, Any], raw: str) -> dict[str, Any]:
        raw_pass = parsed.get("pass")
        raw_score = parsed.get("score")
        try:
            numeric_score = float(raw_score)
        except (TypeError, ValueError):
            numeric_score = 1.0 if raw_pass is True else 0.0
        score = 1.0 if numeric_score >= 0.5 or raw_pass is True else 0.0
        failure_layer = parsed.get("failure_layer")
        if score == 1.0:
            failure_layer = None
        elif failure_layer not in ALLOWED_JUDGE_FAILURE_LAYERS:
            failure_layer = "reasoning_or_retrieval_error"
        confidence = parsed.get("confidence")
        try:
            confidence_value = round(float(confidence), 4)
        except (TypeError, ValueError):
            confidence_value = None
        missing = parsed.get("missing") if isinstance(parsed.get("missing"), list) else []
        extra = parsed.get("extra") if isinstance(parsed.get("extra"), list) else []
        return {
            "score": score,
            "failure_layer": failure_layer,
            "judge_reason": str(parsed.get("reason", "")).strip(),
            "judge_confidence": confidence_value,
            "judge_missing": [str(item) for item in missing],
            "judge_extra": [str(item) for item in extra],
            "judge_raw": raw,
        }


def grade_result(
    result: dict[str, Any],
    task: dict[str, Any],
    run_path: Path,
    *,
    judge: LLMJudge | None = None,
    ground_truth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rule_grade = rule_grade_result(result, task, run_path)
    if judge is None:
        return {**rule_grade, "judge_mode": "rule"}

    judge_grade = judge.grade(
        result=result,
        task=task,
        rule_grade=rule_grade,
        ground_truth=ground_truth or {},
    )
    output = {
        **rule_grade,
        "rule_score": rule_grade.get("score"),
        "rule_failure_layer": rule_grade.get("failure_layer"),
        "score": judge_grade["score"],
        "failure_layer": judge_grade["failure_layer"],
        "judge_mode": "llm",
        "judge_model": judge.model,
        "judge_require_parseable_json": judge.require_parseable_json,
        "judge_reason": judge_grade.get("judge_reason"),
        "judge_confidence": judge_grade.get("judge_confidence"),
        "judge_missing": judge_grade.get("judge_missing"),
        "judge_extra": judge_grade.get("judge_extra"),
        "judge_raw": judge_grade.get("judge_raw"),
    }
    if judge.require_parseable_json and output.get("format_failure"):
        output["score"] = 0.0
        output["failure_layer"] = "format_failure"
    return output


def iter_results(run_root: Path, candidate: str | None) -> list[Path]:
    pattern = f"{candidate}/*/result.json" if candidate else "*/*/result.json"
    return sorted(run_root.glob(pattern))


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade blackbox eval results.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--candidate", default=None)
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--judge-mode", choices=["rule", "llm"], default=None)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--only-judge-errors", action="store_true")
    parser.add_argument("--output-name", default="grades.jsonl")
    args = parser.parse_args()

    config = load_eval_config()
    judge_mode = args.judge_mode or str((config.get("judge") or {}).get("mode", "rule"))
    judge = LLMJudge(config) if judge_mode == "llm" else None
    ground_truth = load_ground_truth(config) if judge is not None else {}
    workers = args.workers
    if workers is None:
        workers = int((config.get("judge") or {}).get("workers", 1)) if judge is not None else 1

    run_root = Path(config["paths"]["runs_dir"]) / args.run_id
    tasks = load_tasks(config)
    grades_path = run_root / args.output_name
    task_filter = set(args.task_id)
    existing_rows: list[dict[str, Any]] = []
    existing_judge_error_paths: set[str] = set()
    if args.only_judge_errors:
        if not grades_path.exists():
            raise SystemExit(f"--only-judge-errors requires existing {grades_path}")
        existing_rows = [
            json.loads(line)
            for line in grades_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        existing_judge_error_paths = {
            str(row.get("run_path"))
            for row in existing_rows
            if row.get("failure_layer") == "judge_error"
        }
    result_paths = []
    for result_path in iter_results(run_root, args.candidate):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        task_id = result["task_id"]
        if task_filter and task_id not in task_filter:
            continue
        relative_run_path = str(result_path.parent.relative_to(ROOT))
        if args.only_judge_errors and relative_run_path not in existing_judge_error_paths:
            continue
        result_paths.append(result_path)
        if args.limit is not None and len(result_paths) >= args.limit:
            break

    def grade_path(index_and_path: tuple[int, Path]) -> tuple[int, dict[str, Any]]:
        index, result_path = index_and_path
        result = json.loads(result_path.read_text(encoding="utf-8"))
        task_id = result["task_id"]
        grade = grade_result(
            result,
            tasks[task_id],
            result_path.parent,
            judge=judge,
            ground_truth=ground_truth,
        )
        return index, grade

    rows_by_index: list[dict[str, Any] | None] = [None] * len(result_paths)
    if workers > 1 and len(result_paths) > 1:
        completed = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(grade_path, item)
                for item in enumerate(result_paths)
            ]
            for future in as_completed(futures):
                index, row = future.result()
                rows_by_index[index] = row
                completed += 1
                if completed % 10 == 0 or completed == len(result_paths):
                    print(f"graded {completed}/{len(result_paths)}", flush=True)
    else:
        for item in enumerate(result_paths):
            index, row = grade_path(item)
            rows_by_index[index] = row
            print(f"graded {index + 1}/{len(result_paths)}", flush=True)

    rows = [row for row in rows_by_index if row is not None]
    if args.only_judge_errors:
        by_run_path = {str(row.get("run_path")): row for row in rows}
        rows = [
            by_run_path.get(str(existing_row.get("run_path")), existing_row)
            for existing_row in existing_rows
        ]
    grades_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(grades_path)
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
