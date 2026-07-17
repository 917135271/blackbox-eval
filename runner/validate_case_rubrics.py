from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data" / "formal_case_rubric" / "cases.json"
DEFAULT_EVALS = ROOT / "data" / "formal_case_rubric" / "evals.json"
EXPECTED_FAMILIES = {
    "policy_and_version": 3,
    "record_audit": 3,
    "full_year_audit": 3,
    "clean_trap": 3,
    "retrieval_and_report": 3,
}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_case(case: dict[str, Any], errors: list[str]) -> None:
    case_id = str(case.get("id", "<missing>"))
    rubric = case.get("rubric") or {}
    criteria = rubric.get("criteria") or []
    require(rubric.get("max_score") == 100, f"{case_id}: max_score must be 100", errors)
    require(rubric.get("pass_score") == 70, f"{case_id}: pass_score must be 70", errors)
    require(len(criteria) >= 4, f"{case_id}: at least four criteria required", errors)
    weights = [item.get("weight") for item in criteria]
    require(all(isinstance(weight, int) and weight > 0 for weight in weights), f"{case_id}: criterion weights must be positive integers", errors)
    require(sum(weight for weight in weights if isinstance(weight, int)) == 100, f"{case_id}: criterion weights must sum to 100", errors)
    criterion_ids = [item.get("id") for item in criteria]
    require(len(criterion_ids) == len(set(criterion_ids)), f"{case_id}: duplicate criterion ids", errors)
    for item in criteria:
        criterion_id = item.get("id", "<missing>")
        require(item.get("expected") not in (None, "", [], {}), f"{case_id}/{criterion_id}: expected must be case-specific", errors)
        anchors = item.get("anchors") or {}
        require(all(anchors.get(name) for name in ("full", "partial", "zero")), f"{case_id}/{criterion_id}: full/partial/zero anchors required", errors)
        require(bool(item.get("evidence_sources")), f"{case_id}/{criterion_id}: evidence sources required", errors)
    for failure in rubric.get("critical_failures") or []:
        cap = failure.get("score_cap")
        require(isinstance(cap, int) and 0 <= cap <= 100, f"{case_id}: invalid critical failure cap", errors)
        require(bool(failure.get("condition")), f"{case_id}: critical failure condition required", errors)


def validate(cases_path: Path, evals_path: Path) -> dict[str, Any]:
    dataset = json.loads(cases_path.read_text(encoding="utf-8"))
    evals = json.loads(evals_path.read_text(encoding="utf-8"))
    cases = dataset.get("cases") or []
    errors: list[str] = []
    require(dataset.get("case_count") == 15, "dataset case_count must be 15", errors)
    require(len(cases) == 15, "cases must contain 15 items", errors)
    require(len(evals) == 15, "evals must contain 15 items", errors)

    case_ids = [case.get("id") for case in cases]
    eval_ids = [task.get("id") for task in evals]
    require(len(case_ids) == len(set(case_ids)), "case ids must be unique", errors)
    require(case_ids == eval_ids, "cases and evals must use identical ordered ids", errors)
    family_counts = Counter(case.get("case_family") for case in cases)
    require(dict(family_counts) == EXPECTED_FAMILIES, f"case family counts must be {EXPECTED_FAMILIES}, got {dict(family_counts)}", errors)
    require(dataset.get("case_family_counts") == dict(sorted(EXPECTED_FAMILIES.items())), "case_family_counts manifest mismatch", errors)

    source_tasks = {
        task["id"]: task
        for task in json.loads((ROOT / "data" / "evals.json").read_text(encoding="utf-8"))
    }
    for index, case in enumerate(cases):
        validate_case(case, errors)
        source = source_tasks.get(case.get("source_task_id"))
        require(source is not None, f"{case.get('id')}: source task missing", errors)
        if source:
            require(source.get("category") != "ground_truth_lookup", f"{case.get('id')}: ground_truth_lookup must not enter formal set", errors)
            require(case.get("prompt") == source["prompt_variants"]["precise"], f"{case.get('id')}: prompt drift from source", errors)
        task = evals[index]
        require(task.get("scoring", {}).get("type") == "case_rubric", f"{case.get('id')}: eval scoring must reference case rubric", errors)
        require(task.get("prompt_variants") == {"precise": case.get("prompt")}, f"{case.get('id')}: runnable prompt mismatch", errors)

    if errors:
        raise ValueError("\n".join(errors))
    return {
        "status": "pass",
        "dataset_id": dataset["dataset_id"],
        "case_count": len(cases),
        "criterion_count": sum(len(case["rubric"]["criteria"]) for case in cases),
        "family_counts": dict(family_counts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the formal case-by-case rubric dataset.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--evals", type=Path, default=DEFAULT_EVALS)
    args = parser.parse_args()
    print(json.dumps(validate(args.cases, args.evals), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
