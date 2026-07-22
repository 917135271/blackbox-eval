from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data" / "formal_case_rubric" / "cases.json"
DEFAULT_EVALS = ROOT / "data" / "formal_case_rubric" / "evals.json"
FORMAL_DB = ROOT / "data" / "formal_case_rubric" / "expense_formal.db"
CORPUS_DIR = ROOT / "data" / "corpus"
EXPECTED_FAMILIES = {
    "policy_and_version": 3,
    "record_audit": 3,
    "full_year_audit": 3,
    "clean_trap": 3,
    "retrieval_and_report": 3,
}
EXPECTED_CASE_COUNT = sum(EXPECTED_FAMILIES.values())
SUPPORTED_DETERMINISTIC_RULES = {
    "expected-record-present",
    "no-unexpected-records",
    "anomaly-rule-type-exact",
    "anomaly-count-exact",
    "anomaly-type-count-exact",
    "no-anomaly-ids",
}

TRAVEL_LIMITS = {
    "E1": {"A": 450, "B": 380, "C": 300},
    "M1": {"A": 650, "B": 550, "C": 450},
    "D1": {"A": 850, "B": 700, "C": 600},
    "X1": {"A": 1100, "B": 900, "C": 750},
}
LOCAL_TRANSPORT_LIMITS = {"A": 120, "B": 100, "C": 80}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_case(case: dict[str, Any], errors: list[str]) -> None:
    case_id = str(case.get("id", "<missing>"))
    rubric = case.get("rubric") or {}
    checklist = rubric.get("checklist") or []
    require(rubric.get("scoring_method") == "binary_checklist", f"{case_id}: scoring_method must be binary_checklist", errors)
    require(rubric.get("item_result_values") == [0, 1], f"{case_id}: item results must be exactly 0/1", errors)
    require(rubric.get("normalization") == "equal_item_ratio", f"{case_id}: checklist items must be equally weighted", errors)
    require("pass_score" not in rubric, f"{case_id}: case-level pass threshold is not allowed", errors)
    require(len(checklist) >= 6, f"{case_id}: at least six atomic checklist items required", errors)
    require(
        all("points" not in item and "weight" not in item for item in checklist),
        f"{case_id}: checklist items must not contain points or weights",
        errors,
    )
    item_ids = [item.get("id") for item in checklist]
    require(len(item_ids) == len(set(item_ids)), f"{case_id}: duplicate checklist item ids", errors)
    require("submission" in item_ids, f"{case_id}: submission check is required", errors)
    for item in checklist:
        item_id = item.get("id", "<missing>")
        require(
            "required_for_case_pass" not in item,
            f"{case_id}/{item_id}: case-level required checks are not allowed",
            errors,
        )
        require(item.get("expected") not in (None, "", [], {}), f"{case_id}/{item_id}: expected must be case-specific", errors)
        require(bool(item.get("check")), f"{case_id}/{item_id}: check text required", errors)
        require(bool(item.get("pass_condition")), f"{case_id}/{item_id}: pass condition required", errors)
        require(bool(item.get("fail_condition")), f"{case_id}/{item_id}: fail condition required", errors)
        require(
            item.get("fail_condition") == f"未完全满足通过条件：{item.get('pass_condition')}",
            f"{case_id}/{item_id}: binary failure must be the complement of pass condition",
            errors,
        )
        require(bool(item.get("evidence_sources")), f"{case_id}/{item_id}: evidence sources required", errors)
        if item.get("deterministic_rule"):
            require(
                item.get("evaluation_mode") == "deterministic",
                f"{case_id}/{item_id}: deterministic_rule requires deterministic mode",
                errors,
            )
        require(
            item.get("deterministic_rule") != "record-ids-unique",
            f"{case_id}/{item_id}: record_ids uniqueness is already enforced by the result Schema",
            errors,
        )
        if item.get("evaluation_mode") == "deterministic":
            deterministic_rule = item.get("deterministic_rule")
            require(
                item_id == "submission" or deterministic_rule in SUPPORTED_DETERMINISTIC_RULES,
                f"{case_id}/{item_id}: deterministic item has no supported executable rule",
                errors,
            )
        rubric_text = json.dumps(
            {
                "check": item.get("check"),
                "expected": item.get("expected"),
                "pass_condition": item.get("pass_condition"),
                "fail_condition": item.get("fail_condition"),
            },
            ensure_ascii=False,
        )
        require(
            re.search(r"\b(?:DUP|SPLIT|OVERSTD|BUDGET|OVERDUE)-\d{3}\b", rubric_text) is None,
            f"{case_id}/{item_id}: rubric must not require hidden internal anomaly labels",
            errors,
        )
    refs = [str(ref) for ref in case.get("ground_truth_refs", [])]
    require(
        not any(re.search(r"(?:费用报销管理办法-6\.[1-4]|预算管理办法-4\.1)", ref) for ref in refs),
        f"{case_id}: legacy logical policy reference remains",
        errors,
    )
    for citation in case.get("expected_output", {}).get("required_citations", []):
        doc_id = str(citation.get("doc_id", ""))
        clause_no = str(citation.get("clause_no", ""))
        require(f"document:{doc_id}" in refs, f"{case_id}: document reference missing for {doc_id}", errors)
        require(
            f"clause:{doc_id}#{clause_no}" in refs,
            f"{case_id}: clause reference missing for {doc_id}#{clause_no}",
            errors,
        )


def _group_record_sets(rows: list[sqlite3.Row], key: str) -> list[list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(str(row["record_id"]))
    return [sorted(record_ids) for record_ids in grouped.values() if len(record_ids) > 1]


def recompute_semantic_ground_truth(db_path: Path) -> dict[str, Any]:
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        expense_rows = connection.execute(
            """
            SELECT e.*, emp.employee_level
            FROM expense_records e
            JOIN employees emp ON emp.employee_id = e.employee_id
            WHERE e.status = 'approved'
            """
        ).fetchall()

        duplicate_groups = _group_record_sets(expense_rows, "invoice_id")

        by_employee_type: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
        for row in expense_rows:
            by_employee_type[(str(row["employee_id"]), str(row["expense_type"]))].append(row)
        split_groups: set[tuple[str, ...]] = set()
        for rows in by_employee_type.values():
            rows.sort(key=lambda row: (str(row["expense_date"]), str(row["record_id"])))
            for index, first in enumerate(rows):
                start = dt.date.fromisoformat(str(first["expense_date"]))
                window = []
                for row in rows[index:]:
                    current = dt.date.fromisoformat(str(row["expense_date"]))
                    if (current - start).days > 7:
                        break
                    window.append(row)
                if len(window) >= 2 and sum(float(row["amount"]) for row in window) >= 10000:
                    split_groups.add(tuple(str(row["record_id"]) for row in window))

        direct_overstandard: list[str] = []
        for row in expense_rows:
            if int(row["special_approval"]):
                continue
            amount = float(row["amount"])
            expense_type = str(row["expense_type"])
            exceeded = False
            if expense_type == "office_supplies":
                exceeded = amount > 600
            elif expense_type == "communication":
                exceeded = amount > 300
            elif expense_type == "training_fee":
                exceeded = amount > 3500
            elif expense_type == "business_entertainment":
                participants = int(row["participants"] or 0)
                exceeded = amount > 5000 or bool(participants and amount / participants > 300)
            elif expense_type == "travel_lodging" and row["nights"] and row["city_tier"]:
                nightly = TRAVEL_LIMITS[str(row["employee_level"])][str(row["city_tier"])]
                exceeded = amount > nightly * int(row["nights"])
            elif expense_type == "local_transport" and row["days"] and row["city_tier"]:
                daily = LOCAL_TRANSPORT_LIMITS[str(row["city_tier"])]
                exceeded = amount > daily * int(row["days"])
            if exceeded:
                direct_overstandard.append(str(row["record_id"]))

        overdue = sorted(
            str(row["record_id"])
            for row in expense_rows
            if (
                dt.date.fromisoformat(str(row["reimburse_date"]))
                - dt.date.fromisoformat(str(row["expense_date"]))
            ).days
            > 60
        )

        budgets = {
            str(row["department_id"]): float(row["annual_budget"])
            for row in connection.execute("SELECT department_id, annual_budget FROM departments")
        }
        by_department: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in expense_rows:
            if int(row["budget_year"]) == 2025:
                by_department[str(row["department_id"])].append(row)
        budget_crossings: list[str] = []
        budget_crossing_groups: list[dict[str, Any]] = []
        for department_id, rows in by_department.items():
            rows.sort(key=lambda row: (str(row["reimburse_date"]), str(row["record_id"])))
            cumulative = 0.0
            for row in rows:
                cumulative += float(row["amount"])
                if cumulative > budgets[department_id]:
                    if not int(row["special_approval"]):
                        record_id = str(row["record_id"])
                        budget_crossings.append(record_id)
                        budget_crossing_groups.append(
                            {
                                "rule_type": "BUDGET",
                                "record_ids": [record_id],
                                "department_id": department_id,
                            }
                        )
                    break

        return {
            "duplicate_groups": sorted(duplicate_groups),
            "duplicate_records": sorted(record_id for group in duplicate_groups for record_id in group),
            "split_groups": sorted([list(group) for group in split_groups]),
            "direct_overstandard_records": sorted(direct_overstandard),
            "budget_crossing_records": sorted(budget_crossings),
            "budget_crossing_groups": sorted(
                budget_crossing_groups, key=lambda group: str(group["department_id"])
            ),
            "overdue_records": overdue,
        }


def validate_semantics(cases: list[dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    require(FORMAL_DB.exists(), f"formal database missing: {FORMAL_DB}", errors)
    if not FORMAL_DB.exists():
        return {}
    facts = recompute_semantic_ground_truth(FORMAL_DB)
    case_map = {str(case["id"]): case for case in cases}

    expected_sets = {
        "L3-001": facts["duplicate_records"],
        "L3-003": facts["direct_overstandard_records"],
        "L3-004": facts["budget_crossing_records"],
        "L3-009": sorted(
            {
                *facts["duplicate_records"],
                *(record_id for group in facts["split_groups"] for record_id in group),
                *facts["direct_overstandard_records"],
                *facts["budget_crossing_records"],
                *facts["overdue_records"],
            }
        ),
    }
    for case_id, recomputed in expected_sets.items():
        frozen = sorted(case_map[case_id]["expected_output"]["expected_record_ids"])
        require(frozen == recomputed, f"{case_id}: frozen record_ids differ from database recomputation", errors)

    expected_groups = {
        "L3-001": [
            {"rule_type": "DUP", "record_ids": group}
            for group in facts["duplicate_groups"]
        ],
        "L3-003": [
            {"rule_type": "OVERSTD", "record_ids": [record_id]}
            for record_id in facts["direct_overstandard_records"]
        ],
        "L3-004": facts["budget_crossing_groups"],
    }
    for case_id, recomputed in expected_groups.items():
        frozen = case_map[case_id]["expected_output"].get("expected_finding_groups")
        require(
            frozen == recomputed,
            f"{case_id}: finding-to-record mapping differs from database recomputation",
            errors,
        )

    require(
        sorted(case_map["L2-003"]["expected_output"]["expected_record_ids"])
        in facts["duplicate_groups"],
        "L2-003: record pair is not a duplicate-invoice group",
        errors,
    )
    require(
        sorted(case_map["L2-008"]["expected_output"]["expected_record_ids"])
        in facts["split_groups"],
        "L2-008: record set is not a qualifying 7-day split group",
        errors,
    )
    require(
        case_map["L2-013"]["expected_output"]["expected_record_ids"]
        == ["R004223"]
        and "R004223" in facts["direct_overstandard_records"],
        "L2-013: training overstandard record is not reproducible",
        errors,
    )

    finding_count = (
        len(facts["duplicate_groups"])
        + len(facts["split_groups"])
        + len(facts["direct_overstandard_records"])
        + len(facts["budget_crossing_records"])
        + len(facts["overdue_records"])
    )
    require(
        finding_count == case_map["L3-009"]["expected_output"]["expected_anomaly_count"],
        f"L3-009: expected count does not match recomputation ({finding_count})",
        errors,
    )
    finding_counts_by_type = {
        "DUP": len(facts["duplicate_groups"]),
        "SPLIT": len(facts["split_groups"]),
        "OVERSTD": len(facts["direct_overstandard_records"]),
        "BUDGET": len(facts["budget_crossing_records"]),
        "OVERDUE": len(facts["overdue_records"]),
    }
    require(
        case_map["L3-009"]["expected_output"].get("expected_findings_by_type")
        == finding_counts_by_type,
        "L3-009: per-rule finding counts do not match database recomputation",
        errors,
    )
    excluded = set(case_map["L3-009"]["expected_output"]["excluded_record_ids"])
    anomaly_records = {
        *facts["duplicate_records"],
        *(record_id for group in facts["split_groups"] for record_id in group),
        *facts["direct_overstandard_records"],
        *facts["budget_crossing_records"],
        *facts["overdue_records"],
    }
    require(not excluded & anomaly_records, "L3-009: excluded clean records overlap recomputed anomalies", errors)

    with sqlite3.connect(FORMAL_DB) as connection:
        existing_records = {str(row[0]) for row in connection.execute("SELECT record_id FROM expense_records")}
        trap_003 = connection.execute(
            "SELECT expense_date, amount FROM expense_records WHERE record_id IN ('R004236', 'R004237') ORDER BY record_id"
        ).fetchall()
        trap_005 = connection.execute(
            "SELECT expense_date, amount, participants, reason FROM expense_records WHERE record_id IN ('R004239', 'R004240') ORDER BY record_id"
        ).fetchall()
    require(len(trap_003) == 2, "TRAP-003: formal database records are incomplete", errors)
    if len(trap_003) == 2:
        gap = (
            dt.date.fromisoformat(str(trap_003[1][0]))
            - dt.date.fromisoformat(str(trap_003[0][0]))
        ).days
        require(gap == 8, f"TRAP-003: expected 8-day gap, got {gap}", errors)
        require(sum(float(row[1]) for row in trap_003) == 10400, "TRAP-003: expected total amount 10400", errors)
    require(len(trap_005) == 2, "TRAP-005: formal database records are incomplete", errors)
    if len(trap_005) == 2:
        gap = (
            dt.date.fromisoformat(str(trap_005[1][0]))
            - dt.date.fromisoformat(str(trap_005[0][0]))
        ).days
        reasons = [str(row[3]) for row in trap_005]
        require(gap == 1, f"TRAP-005: expected 1-day gap, got {gap}", errors)
        require(reasons[0] != reasons[1], "TRAP-005: business contexts must be distinct", errors)
        require(
            [float(row[1]) for row in trap_005] == [540.0, 545.0]
            and [int(row[2]) for row in trap_005] == [3, 3],
            "TRAP-005: amounts or participant counts differ from rubric facts",
            errors,
        )
    for case in cases:
        case_id = str(case["id"])
        for record_id in case.get("expected_output", {}).get("expected_record_ids", []):
            require(record_id in existing_records, f"{case_id}: unknown expected record_id {record_id}", errors)
        for citation in case.get("expected_output", {}).get("required_citations", []):
            doc_id = str(citation.get("doc_id", ""))
            require((CORPUS_DIR / doc_id).exists(), f"{case_id}: citation document missing: {doc_id}", errors)
    return facts


def validate(cases_path: Path, evals_path: Path) -> dict[str, Any]:
    dataset = json.loads(cases_path.read_text(encoding="utf-8"))
    evals = json.loads(evals_path.read_text(encoding="utf-8"))
    cases = dataset.get("cases") or []
    errors: list[str] = []
    require(dataset.get("dataset_id") == "securities-expense-audit-formal-15-v7", "dataset_id must be securities-expense-audit-formal-15-v7", errors)
    require(dataset.get("rubric_version") == "atomic-binary-checklist-v5", "rubric_version must be atomic-binary-checklist-v5", errors)
    require(
        dataset.get("case_count") == EXPECTED_CASE_COUNT,
        f"dataset case_count must be {EXPECTED_CASE_COUNT}",
        errors,
    )
    require(
        len(cases) == EXPECTED_CASE_COUNT,
        f"cases must contain {EXPECTED_CASE_COUNT} items",
        errors,
    )
    require(
        len(evals) == EXPECTED_CASE_COUNT,
        f"evals must contain {EXPECTED_CASE_COUNT} items",
        errors,
    )

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
            source_prompt = source["prompt_variants"]["precise"]
            if case.get("prompt") != source_prompt:
                require(case.get("source_prompt") == source_prompt, f"{case.get('id')}: changed prompt must preserve source_prompt", errors)
                require(bool(case.get("prompt_change_reason")), f"{case.get('id')}: changed prompt requires prompt_change_reason", errors)
        if case.get("case_family") == "clean_trap":
            for record_id in case.get("expected_output", {}).get("expected_record_ids", []):
                require(record_id in case.get("prompt", ""), f"{case.get('id')}: trap prompt must expose {record_id}", errors)
        task = evals[index]
        require(task.get("scoring", {}).get("type") == "case_rubric", f"{case.get('id')}: eval scoring must reference case rubric", errors)
        require(task.get("prompt_variants") == {"precise": case.get("prompt")}, f"{case.get('id')}: runnable prompt mismatch", errors)

    semantic_facts = validate_semantics(cases, errors)

    if errors:
        raise ValueError("\n".join(errors))
    return {
        "status": "pass",
        "dataset_id": dataset["dataset_id"],
        "case_count": len(cases),
        "checklist_item_count": sum(len(case["rubric"]["checklist"]) for case in cases),
        "family_counts": dict(family_counts),
        "semantic_recomputation": {
            "duplicate_findings": len(semantic_facts.get("duplicate_groups", [])),
            "split_findings": len(semantic_facts.get("split_groups", [])),
            "direct_overstandard_findings": len(semantic_facts.get("direct_overstandard_records", [])),
            "budget_findings": len(semantic_facts.get("budget_crossing_records", [])),
            "overdue_findings": len(semantic_facts.get("overdue_records", [])),
        },
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
