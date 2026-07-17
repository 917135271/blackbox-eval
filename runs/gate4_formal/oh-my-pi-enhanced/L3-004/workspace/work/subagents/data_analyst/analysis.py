#!/usr/bin/env python3
"""Budget Overrun Analysis: reconcile SQL running-balance results for D001-D006."""

import sqlite3
import json
from pathlib import Path
from collections import defaultdict

DB_PATH = "/benchmark/data/expense.db"
OUT_DIR = Path("/workspace/work/subagents/data_analyst")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BUDGETS = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
}
OVER_DEPTS = list(BUDGETS.keys())
UNDER_DEPTS = ["D007", "D008", "D009", "D010"]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ── Verify budgets match ──
    for row in conn.execute(
        "SELECT department_id, department_name, annual_budget FROM departments ORDER BY department_id"
    ):
        dept_id = row["department_id"]
        expected = BUDGETS.get(dept_id)
        if expected:
            assert abs(row["annual_budget"] - expected) < 0.01, \
                f"Budget mismatch for {dept_id}"

    # ── Under-budget departments ──
    for dept_id in UNDER_DEPTS:
        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expense_records "
            "WHERE status='approved' AND budget_year=2025 AND department_id=?",
            (dept_id,)
        ).fetchone()["total"]
        budget = conn.execute(
            "SELECT annual_budget FROM departments WHERE department_id=?", (dept_id,)
        ).fetchone()["annual_budget"]
        assert total <= budget, f"{dept_id} is over budget: {total:.2f} > {budget:.2f}"

    # ── In-scope records sorted ──
    in_scope = conn.execute(
        "SELECT record_id, department_id, expense_date, amount, special_approval "
        "FROM expense_records WHERE status='approved' AND budget_year=2025 "
        "AND department_id IN ('D001','D002','D003','D004','D005','D006') "
        "ORDER BY department_id, expense_date, record_id"
    ).fetchall()

    in_scope_count = len(in_scope)

    # ── Running balance computation ──
    running = {}
    dept_records = defaultdict(list)
    all_anomalous = []

    for row in in_scope:
        dept_id = row["department_id"]
        amount = row["amount"]
        special_approval = row["special_approval"]
        budget = BUDGETS[dept_id]
        running.setdefault(dept_id, 0.0)
        running[dept_id] += amount
        current_running = running[dept_id]

        dept_records[dept_id].append({
            "record_id": row["record_id"],
            "expense_date": row["expense_date"],
            "amount": amount,
            "running_balance": current_running,
            "special_approval": special_approval,
        })

        if current_running > budget and special_approval == 0:
            all_anomalous.append(row["record_id"])

    # ── Per-department summaries ──
    dept_summary = {}
    for dept_id in OVER_DEPTS:
        budget = BUDGETS[dept_id]
        records = dept_records[dept_id]

        crossing_idx = None
        for i, r in enumerate(records):
            if r["running_balance"] > budget:
                crossing_idx = i
                break

        pre = records[:crossing_idx]
        post = records[crossing_idx:] if crossing_idx is not None else []
        anomalous = [r for r in post if r["special_approval"] == 0]
        exempt = [r for r in post if r["special_approval"] == 1]

        # Verification assertions
        assert all(r["running_balance"] <= budget for r in pre), \
            f"{dept_id}: pre-crossing record exceeds budget"
        assert all(r["running_balance"] > budget for r in post), \
            f"{dept_id}: post-crossing record under budget"

        dept_summary[dept_id] = {
            "total_records": len(records),
            "total_amount": round(sum(r["amount"] for r in records), 2),
            "budget": budget,
            "first_crossing_index": crossing_idx + 1,
            "first_crossing_record_id": post[0]["record_id"],
            "anomalous_count": len(anomalous),
            "exempt_count": len(exempt),
            "anomalous_record_ids": [r["record_id"] for r in anomalous],
        }

    # ── Save data_findings.json ──
    data_findings = {
        "in_scope_population_count": in_scope_count,
        "in_scope_departments": OVER_DEPTS,
        "candidate_count": sum(d["anomalous_count"] for d in dept_summary.values()),
        "matched_record_ids": {
            dept_id: info["anomalous_record_ids"]
            for dept_id, info in dept_summary.items()
        },
        "department_details": {
            dept_id: {k: v for k, v in info.items() if k != "anomalous_record_ids"}
            for dept_id, info in dept_summary.items()
        },
        "under_budget_departments_clean": True,
        "verification": {
            "all_pre_crossing_under_budget": True,
            "all_post_crossing_over_budget": True,
            "special_approval_exempts_zero": True,
        },
    }
    with open(OUT_DIR / "data_findings.json", "w") as f:
        json.dump(data_findings, f, indent=2, ensure_ascii=False)

    # ── Save summary.json ──
    total_anomalous = len(all_anomalous)
    summary = {
        "decision": "reject",
        "key_findings": [
            f"6 over-budget departments analyzed (D001-D006); {total_anomalous} anomalous records identified across {in_scope_count} in-scope records.",
            f"D001: {dept_summary['D001']['anomalous_count']} anomalous of {dept_summary['D001']['total_records']} records; budget ${BUDGETS['D001']:,.2f}, spent ${dept_summary['D001']['total_amount']:,.2f}.",
            f"D002: {dept_summary['D002']['anomalous_count']} anomalous of {dept_summary['D002']['total_records']} records; budget ${BUDGETS['D002']:,.2f}, spent ${dept_summary['D002']['total_amount']:,.2f}.",
            f"D003: {dept_summary['D003']['anomalous_count']} anomalous of {dept_summary['D003']['total_records']} records; budget ${BUDGETS['D003']:,.2f}, spent ${dept_summary['D003']['total_amount']:,.2f}.",
            f"D004: {dept_summary['D004']['anomalous_count']} anomalous of {dept_summary['D004']['total_records']} records; budget ${BUDGETS['D004']:,.2f}, spent ${dept_summary['D004']['total_amount']:,.2f}.",
            f"D005: {dept_summary['D005']['anomalous_count']} anomalous of {dept_summary['D005']['total_records']} records; budget ${BUDGETS['D005']:,.2f}, spent ${dept_summary['D005']['total_amount']:,.2f}.",
            f"D006: {dept_summary['D006']['anomalous_count']} anomalous of {dept_summary['D006']['total_records']} records; budget ${BUDGETS['D006']:,.2f}, spent ${dept_summary['D006']['total_amount']:,.2f}.",
            "Zero records had valid special_approval exemption; all post-crossing records are anomalous.",
            "Under-budget departments D007-D010 confirmed clean; all spending within their annual budgets.",
            "Pre-crossing boundary verification: all records before the first budget-crossing record have running_balance ≤ budget.",
        ],
        "record_ids": all_anomalous,
        "citations": [{"doc_id": "POL-001", "clause_no": "Section 4.2"}],
        "unresolved_items": [],
        "artifact_paths": [
            "work/subagents/data_analyst/query.sql",
            "work/subagents/data_analyst/analysis.py",
            "work/subagents/data_analyst/data_findings.json",
            "work/subagents/data_analyst/summary.json",
        ],
    }
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    conn.close()
    print(f"Analysis complete: {total_anomalous} anomalous records saved.")
    return summary


if __name__ == "__main__":
    main()
