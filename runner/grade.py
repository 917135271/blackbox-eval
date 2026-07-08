from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from gate2_candidate_check import ROOT, load_eval_config


def normalize(text: Any) -> str:
    raw = "" if text is None else str(text)
    return re.sub(r"[\s,，。；;：:、（）()《》<>【】\[\]\"'`]+", "", raw).lower()


def load_tasks(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    with Path(config["paths"]["evals"]).open("r", encoding="utf-8") as handle:
        return {task["id"]: task for task in json.load(handle)}


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


def grade_result(result: dict[str, Any], task: dict[str, Any], run_path: Path) -> dict[str, Any]:
    scoring = task.get("scoring") or {}
    kind = scoring.get("kind")
    if kind is None and scoring.get("type") == "llm_rubric":
        kind = "llm_rubric"
    answer_json = result.get("answer_json") if isinstance(result.get("answer_json"), dict) else None
    base = {
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
        "kind": kind,
    }
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


def iter_results(run_root: Path, candidate: str | None) -> list[Path]:
    pattern = f"{candidate}/*/result.json" if candidate else "*/*/result.json"
    return sorted(run_root.glob(pattern))


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade deterministic blackbox eval results.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--candidate", default=None)
    args = parser.parse_args()

    config = load_eval_config()
    run_root = Path(config["paths"]["runs_dir"]) / args.run_id
    tasks = load_tasks(config)
    grades_path = run_root / "grades.jsonl"
    rows = []
    for result_path in iter_results(run_root, args.candidate):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        task_id = result["task_id"]
        grade = grade_result(result, tasks[task_id], result_path.parent)
        rows.append(grade)
    grades_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(grades_path)
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
