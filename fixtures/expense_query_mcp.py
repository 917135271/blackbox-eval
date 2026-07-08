from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "expense.db"
PAGE_SIZE = 50


def db_path() -> Path:
    return Path(os.environ.get("EVAL_EXPENSE_DB", str(DEFAULT_DB_PATH)))


def readonly_conn() -> sqlite3.Connection:
    path = db_path()
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def log_path() -> Path | None:
    raw = os.environ.get("EVAL_TASK_LOG")
    if not raw:
        return None
    path = Path(raw)
    if path.suffix:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    path.mkdir(parents=True, exist_ok=True)
    return path / "tool_calls.jsonl"


def preview(value: Any) -> Any:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(text) <= 1200:
        return value
    return {"preview": text[:1200], "truncated": True}


def write_log(tool_name: str, arguments: dict[str, Any], result: Any, error: str | None = None) -> None:
    path = log_path()
    if path is None:
        return
    event = {
        "ts": time.time(),
        "server": "expense_query_mcp",
        "tool": tool_name,
        "arguments": arguments,
        "ok": error is None,
        "error": error,
        "result_preview": result if error else preview(result),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def list_expenses(
    employee_id: str | None = None,
    department_id: str | None = None,
    expense_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    page: int = 1,
) -> dict[str, Any]:
    """List reimbursement records with optional filters and fixed 50-row pages."""
    page = max(1, int(page or 1))
    where = []
    params: list[Any] = []
    filters = {
        "employee_id": employee_id,
        "department_id": department_id,
        "expense_type": expense_type,
    }
    for column, value in filters.items():
        if value:
            where.append(f"r.{column} = ?")
            params.append(value)
    if date_from:
        where.append("r.expense_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("r.expense_date <= ?")
        params.append(date_to)
    if min_amount is not None:
        where.append("r.amount >= ?")
        params.append(float(min_amount))
    if max_amount is not None:
        where.append("r.amount <= ?")
        params.append(float(max_amount))
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    offset = (page - 1) * PAGE_SIZE
    with readonly_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM expense_records r{where_sql}", params).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT r.record_id, r.record_no, r.employee_id, e.employee_name, r.department_id,
                   d.department_name, r.expense_date, r.reimburse_date, r.expense_type,
                   r.amount, r.reason, i.invoice_no, r.status
            FROM expense_records r
            JOIN employees e ON e.employee_id = r.employee_id
            JOIN departments d ON d.department_id = r.department_id
            JOIN invoices i ON i.invoice_id = r.invoice_id
            {where_sql}
            ORDER BY r.expense_date, r.record_id
            LIMIT ? OFFSET ?
            """,
            params + [PAGE_SIZE, offset],
        ).fetchall()
    return {
        "page": page,
        "page_size": PAGE_SIZE,
        "total": int(total),
        "has_next": offset + PAGE_SIZE < total,
        "records": rows_to_dicts(rows),
    }


def get_expense_detail(record_id: str) -> dict[str, Any]:
    """Return one reimbursement record with linked invoice, employee, department, and approvals."""
    with readonly_conn() as conn:
        record = conn.execute(
            """
            SELECT r.*, e.employee_name, e.employee_level, e.position_role, d.department_name, d.annual_budget,
                   i.invoice_no, i.vendor_name, i.invoice_date, i.amount AS invoice_amount
            FROM expense_records r
            JOIN employees e ON e.employee_id = r.employee_id
            JOIN departments d ON d.department_id = r.department_id
            JOIN invoices i ON i.invoice_id = r.invoice_id
            WHERE r.record_id = ?
            """,
            (record_id,),
        ).fetchone()
        approvals = conn.execute(
            """
            SELECT approval_id, tier_id, approver_employee_id, approver_role, approved_at, approval_status
            FROM approvals
            WHERE record_id = ?
            ORDER BY approval_id
            """,
            (record_id,),
        ).fetchall()
    return {"record": dict(record) if record else None, "approvals": rows_to_dicts(approvals)}


def find_invoice_usage(invoice_no: str) -> dict[str, Any]:
    """Find reimbursement records that use a given invoice number."""
    with readonly_conn() as conn:
        rows = conn.execute(
            """
            SELECT r.record_id, r.record_no, r.employee_id, e.employee_name, r.department_id,
                   r.expense_date, r.reimburse_date, r.expense_type, r.amount, i.invoice_no
            FROM invoices i
            JOIN expense_records r ON r.invoice_id = i.invoice_id
            JOIN employees e ON e.employee_id = r.employee_id
            WHERE i.invoice_no = ?
            ORDER BY r.expense_date, r.record_id
            """,
            (invoice_no,),
        ).fetchall()
    return {"invoice_no": invoice_no, "usage_count": len(rows), "records": rows_to_dicts(rows)}


def list_employees(department_id: str | None = None) -> dict[str, Any]:
    """List employees, optionally filtered by department."""
    params: list[Any] = []
    where_sql = ""
    if department_id:
        where_sql = "WHERE e.department_id = ?"
        params.append(department_id)
    with readonly_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT e.employee_id, e.employee_name, e.employee_level, e.department_id,
                   d.department_name, e.position_role, e.hire_date
            FROM employees e
            JOIN departments d ON d.department_id = e.department_id
            {where_sql}
            ORDER BY e.employee_id
            """,
            params,
        ).fetchall()
    return {"department_id": department_id, "employees": rows_to_dicts(rows)}


def get_employee(employee_id: str) -> dict[str, Any]:
    """Return one employee with level, department, role, and hire date."""
    with readonly_conn() as conn:
        row = conn.execute(
            """
            SELECT e.employee_id, e.employee_name, e.employee_level, e.department_id,
                   d.department_name, e.position_role, e.hire_date
            FROM employees e
            JOIN departments d ON d.department_id = e.department_id
            WHERE e.employee_id = ?
            """,
            (employee_id,),
        ).fetchone()
    return {"employee": dict(row) if row else None}


def get_department_budget(department_id: str) -> dict[str, Any]:
    """Return one department budget and approved reimbursement cumulative amount."""
    with readonly_conn() as conn:
        department = conn.execute(
            """
            SELECT department_id, department_name, annual_budget, manager_employee_id
            FROM departments
            WHERE department_id = ?
            """,
            (department_id,),
        ).fetchone()
        total = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS cumulative_amount, COUNT(*) AS record_count
            FROM expense_records
            WHERE department_id = ? AND status = 'approved'
            """,
            (department_id,),
        ).fetchone()
    return {
        "department": dict(department) if department else None,
        "cumulative_amount": float(total["cumulative_amount"]),
        "record_count": int(total["record_count"]),
    }


def list_approvals(record_id: str) -> dict[str, Any]:
    """List approval chain rows for one reimbursement record."""
    with readonly_conn() as conn:
        rows = conn.execute(
            """
            SELECT approval_id, record_id, tier_id, approver_employee_id, approver_role, approved_at, approval_status
            FROM approvals
            WHERE record_id = ?
            ORDER BY approval_id
            """,
            (record_id,),
        ).fetchall()
    return {"record_id": record_id, "approvals": rows_to_dicts(rows)}


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_expenses": list_expenses,
    "get_expense_detail": get_expense_detail,
    "find_invoice_usage": find_invoice_usage,
    "list_employees": list_employees,
    "get_employee": get_employee,
    "get_department_budget": get_department_budget,
    "list_approvals": list_approvals,
}


TOOL_SCHEMAS = [
    {
        "name": "list_expenses",
        "description": list_expenses.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
                "department_id": {"type": "string"},
                "expense_type": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
                "min_amount": {"type": "number"},
                "max_amount": {"type": "number"},
                "page": {"type": "integer", "minimum": 1, "default": 1},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_expense_detail",
        "description": get_expense_detail.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"record_id": {"type": "string"}},
            "required": ["record_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "find_invoice_usage",
        "description": find_invoice_usage.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"invoice_no": {"type": "string"}},
            "required": ["invoice_no"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_employees",
        "description": list_employees.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"department_id": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_employee",
        "description": get_employee.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"employee_id": {"type": "string"}},
            "required": ["employee_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_department_budget",
        "description": get_department_budget.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"department_id": {"type": "string"}},
            "required": ["department_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_approvals",
        "description": list_approvals.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"record_id": {"type": "string"}},
            "required": ["record_id"],
            "additionalProperties": False,
        },
    },
]


def ensure_tool_schema_descriptions() -> None:
    for tool in TOOL_SCHEMAS:
        tool["description"] = tool.get("description") or f"Call {tool['name']}."
        properties = tool.get("inputSchema", {}).get("properties", {})
        for param_name, param_schema in properties.items():
            param_schema.setdefault("description", f"{param_name} parameter for {tool['name']}.")


ensure_tool_schema_descriptions()


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    arguments = arguments or {}
    try:
        result = TOOLS[name](**arguments)
        write_log(name, arguments, result)
        return result
    except Exception as exc:
        write_log(name, arguments, None, error=str(exc))
        raise


def handle_rpc(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "expense_query_mcp", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": TOOL_SCHEMAS}
        elif method == "tools/call":
            params = request.get("params", {})
            result_obj = call_tool(params["name"], params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(result_obj, ensure_ascii=False)}], "isError": False}
        elif method == "notifications/initialized":
            return None
        else:
            raise ValueError(f"unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


def serve_stdio() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        response = handle_rpc(json.loads(line))
        if response is not None:
            print(json.dumps(response, ensure_ascii=True), flush=True)


def self_test() -> dict[str, Any]:
    expenses = call_tool("list_expenses", {"page": 1, "max_amount": 500})
    record_id = expenses["records"][0]["record_id"]
    detail = call_tool("get_expense_detail", {"record_id": record_id})
    invoice_no = detail["record"]["invoice_no"]
    invoice_usage = call_tool("find_invoice_usage", {"invoice_no": invoice_no})
    employees = call_tool("list_employees", {"department_id": detail["record"]["department_id"]})
    employee = call_tool("get_employee", {"employee_id": detail["record"]["employee_id"]})
    budget = call_tool("get_department_budget", {"department_id": detail["record"]["department_id"]})
    approvals = call_tool("list_approvals", {"record_id": record_id})
    return {
        "list_expenses": {"total": expenses["total"], "returned": len(expenses["records"]), "sample_record": record_id},
        "get_expense_detail": detail,
        "find_invoice_usage": invoice_usage,
        "list_employees": {"count": len(employees["employees"]), "department_id": detail["record"]["department_id"]},
        "get_employee": employee,
        "get_department_budget": budget,
        "list_approvals": approvals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
    else:
        serve_stdio()


if __name__ == "__main__":
    main()
