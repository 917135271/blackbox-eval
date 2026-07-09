from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"


def rpc_request(request_id: int, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    request = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        request["params"] = params
    return request


def run_server(script: Path, log_dir: Path, tool_calls: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    requests = [
        rpc_request(1, "initialize", {"clientInfo": {"name": "gate1_manual_check", "version": "0.1.0"}}),
        rpc_request(2, "tools/list"),
    ]
    next_id = 3
    for name, arguments in tool_calls:
        requests.append(rpc_request(next_id, "tools/call", {"name": name, "arguments": arguments}))
        next_id += 1

    env = os.environ.copy()
    env["EVAL_TASK_LOG"] = str(log_dir)
    env["PYTHONIOENCODING"] = "utf-8"
    stdin = "\n".join(json.dumps(item, ensure_ascii=False) for item in requests) + "\n"
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=stdin,
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )
    responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0:
        raise RuntimeError(f"{script.name} failed: {proc.stderr}")
    if len(responses) != len(requests):
        raise RuntimeError(f"{script.name} returned {len(responses)} responses for {len(requests)} requests")
    return responses


def decode_tool_response(response: dict[str, Any]) -> dict[str, Any]:
    if "error" in response:
        return {"ok": False, "error": response["error"]}
    result = response["result"]
    if "content" in result:
        text = result["content"][0]["text"]
        return {"ok": True, "result": json.loads(text)}
    return {"ok": True, "result": result}


def summarize(server: str, responses: list[dict[str, Any]], tool_names: list[str]) -> list[str]:
    lines = [f"## {server}", ""]
    init = decode_tool_response(responses[0])
    tools_list = decode_tool_response(responses[1])
    lines.append(f"- initialize: {'ok' if init['ok'] else 'failed'}")
    lines.append(f"- tools/list count: {len(tools_list['result']['tools'])}")
    for name, response in zip(tool_names, responses[2:]):
        decoded = decode_tool_response(response)
        status = "ok" if decoded["ok"] else "failed"
        lines.append(f"- {name}: {status}")
    lines.append("")
    return lines


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in [
        OUTPUT_DIR / "gate1_policy_logs",
        OUTPUT_DIR / "gate1_expense_logs",
        OUTPUT_DIR / "gate1_policy_rpc_results.json",
        OUTPUT_DIR / "gate1_expense_rpc_results.json",
        OUTPUT_DIR / "gate1_fixture_check.md",
    ]:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    policy_calls = [
        ("list_policy_docs", {}),
        ("search_policy", {"query": "部门总经理 审批 10000", "top_k": 3}),
        ("get_policy_doc", {"doc_id": "03_authorization_management.md"}),
        ("get_policy_excerpt", {"doc_id": "03_authorization_management.md", "query": "10000 部门总经理", "max_chars": 500}),
    ]
    expense_calls = [
        ("list_expenses", {"page": 1, "max_amount": 500}),
        ("get_expense_detail", {"record_id": "R000002"}),
        ("find_invoice_usage", {"invoice_no": "FP202500000002"}),
        ("list_invoices", {"page": 1, "page_size": 3, "order_by": "usage_count", "sort_desc": True}),
        ("find_reused_invoices", {"page": 1, "page_size": 3}),
        ("summarize_expenses", {"group_by": "department_id,expense_type", "limit": 3}),
        ("summarize_department_budgets", {}),
        ("list_records_by_reimburse_delay", {"min_delay_days": 60, "page": 1, "page_size": 3}),
        ("list_records_missing_approval", {"required_role": "部门总经理", "min_amount": 3000, "page_size": 3}),
        ("list_employees", {"department_id": "D001"}),
        ("get_employee", {"employee_id": "E0001"}),
        ("get_department_budget", {"department_id": "D001"}),
        ("list_approvals", {"record_id": "R000002"}),
    ]

    policy_responses = run_server(ROOT / "fixtures" / "policy_query_mcp.py", OUTPUT_DIR / "gate1_policy_logs", policy_calls)
    expense_responses = run_server(ROOT / "fixtures" / "expense_query_mcp.py", OUTPUT_DIR / "gate1_expense_logs", expense_calls)

    (OUTPUT_DIR / "gate1_policy_rpc_results.json").write_text(
        json.dumps(policy_responses, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "gate1_expense_rpc_results.json").write_text(
        json.dumps(expense_responses, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = ["# GATE 1 Fixture Manual Check", ""]
    lines.extend(summarize("policy_query_mcp", policy_responses, [name for name, _ in policy_calls]))
    lines.extend(summarize("expense_query_mcp", expense_responses, [name for name, _ in expense_calls]))
    lines.extend(
        [
            "## Log Files",
            "",
            "- `output/gate1_policy_logs/tool_calls.jsonl`",
            "- `output/gate1_expense_logs/tool_calls.jsonl`",
            "- `output/gate1_policy_rpc_results.json`",
            "- `output/gate1_expense_rpc_results.json`",
            "",
        ]
    )
    report = "\n".join(lines)
    (OUTPUT_DIR / "gate1_fixture_check.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
