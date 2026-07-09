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
MAX_PAGE_SIZE = 500

EXPENSE_ORDER_COLUMNS = {
    "record_id": "r.record_id",
    "expense_date": "r.expense_date",
    "reimburse_date": "r.reimburse_date",
    "amount": "r.amount",
    "employee_id": "r.employee_id",
    "department_id": "r.department_id",
    "expense_type": "r.expense_type",
}

INVOICE_ORDER_COLUMNS = {
    "invoice_no": "i.invoice_no",
    "invoice_date": "i.invoice_date",
    "amount": "i.amount",
    "usage_count": "usage_count",
}

SUMMARY_GROUP_COLUMNS = {
    "employee_id": "r.employee_id",
    "department_id": "r.department_id",
    "expense_type": "r.expense_type",
    "city_tier": "r.city_tier",
    "status": "r.status",
    "budget_year": "r.budget_year",
    "month": "substr(r.expense_date, 1, 7)",
}


def db_path() -> Path:
    path = Path(os.environ.get("EVAL_EXPENSE_DB", str(DEFAULT_DB_PATH)))
    return path if path.is_absolute() else PROJECT_ROOT / path


def readonly_conn() -> sqlite3.Connection:
    path = db_path()
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def page_size_or_default(page_size: int | None) -> int:
    return max(1, min(int(page_size or PAGE_SIZE), MAX_PAGE_SIZE))


def add_expense_filters(
    where: list[str],
    params: list[Any],
    *,
    employee_id: str | None = None,
    department_id: str | None = None,
    expense_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    special_approval: bool | None = None,
) -> None:
    filters = {
        "employee_id": employee_id,
        "department_id": department_id,
        "expense_type": expense_type,
        "status": status,
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
    if special_approval is not None:
        where.append("r.special_approval = ?")
        params.append(1 if special_approval else 0)


def safe_order(column: str | None, columns: dict[str, str], default: str, sort_desc: bool = False) -> str:
    sql_column = columns.get(str(column or ""), columns[default])
    direction = "DESC" if sort_desc else "ASC"
    return f"{sql_column} {direction}"


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
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    special_approval: bool | None = None,
    page: int = 1,
    page_size: int | None = None,
    order_by: str = "expense_date",
    sort_desc: bool = False,
) -> dict[str, Any]:
    """List reimbursement records with optional filters, paging, and safe sorting."""
    page = max(1, int(page or 1))
    page_size_value = page_size_or_default(page_size)
    where = []
    params: list[Any] = []
    add_expense_filters(
        where,
        params,
        employee_id=employee_id,
        department_id=department_id,
        expense_type=expense_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        special_approval=special_approval,
    )
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    offset = (page - 1) * page_size_value
    order_sql = safe_order(order_by, EXPENSE_ORDER_COLUMNS, "expense_date", bool(sort_desc))
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
            ORDER BY {order_sql}, r.record_id
            LIMIT ? OFFSET ?
            """,
            params + [page_size_value, offset],
        ).fetchall()
    return {
        "page": page,
        "page_size": page_size_value,
        "total": int(total),
        "has_next": offset + page_size_value < total,
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


def list_invoices(
    invoice_no: str | None = None,
    expense_type: str | None = None,
    vendor_name_contains: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    min_usage_count: int | None = None,
    page: int = 1,
    page_size: int | None = None,
    order_by: str = "invoice_date",
    sort_desc: bool = False,
) -> dict[str, Any]:
    """List invoice facts with usage counts and linked reimbursement record IDs."""
    page = max(1, int(page or 1))
    page_size_value = page_size_or_default(page_size)
    where = []
    params: list[Any] = []
    if invoice_no:
        where.append("i.invoice_no = ?")
        params.append(invoice_no)
    if expense_type:
        where.append("i.expense_type = ?")
        params.append(expense_type)
    if vendor_name_contains:
        where.append("i.vendor_name LIKE ?")
        params.append(f"%{vendor_name_contains}%")
    if date_from:
        where.append("i.invoice_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("i.invoice_date <= ?")
        params.append(date_to)
    if min_amount is not None:
        where.append("i.amount >= ?")
        params.append(float(min_amount))
    if max_amount is not None:
        where.append("i.amount <= ?")
        params.append(float(max_amount))
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    having_sql = ""
    having_params: list[Any] = []
    if min_usage_count is not None:
        having_sql = " HAVING COUNT(r.record_id) >= ?"
        having_params.append(max(1, int(min_usage_count)))
    order_sql = safe_order(order_by, INVOICE_ORDER_COLUMNS, "invoice_date", bool(sort_desc))
    offset = (page - 1) * page_size_value
    with readonly_conn() as conn:
        total = conn.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT i.invoice_id
                FROM invoices i
                LEFT JOIN expense_records r ON r.invoice_id = i.invoice_id
                {where_sql}
                GROUP BY i.invoice_id
                {having_sql}
            ) counted
            """,
            params + having_params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT i.invoice_id, i.invoice_no, i.vendor_name, i.invoice_date, i.amount,
                   i.expense_type, COUNT(r.record_id) AS usage_count,
                   GROUP_CONCAT(r.record_id) AS record_ids
            FROM invoices i
            LEFT JOIN expense_records r ON r.invoice_id = i.invoice_id
            {where_sql}
            GROUP BY i.invoice_id
            {having_sql}
            ORDER BY {order_sql}, i.invoice_no
            LIMIT ? OFFSET ?
            """,
            params + having_params + [page_size_value, offset],
        ).fetchall()
    invoices = []
    for row in rows:
        item = dict(row)
        raw_ids = item.get("record_ids") or ""
        item["record_ids"] = [part for part in str(raw_ids).split(",") if part]
        invoices.append(item)
    return {
        "page": page,
        "page_size": page_size_value,
        "total": int(total),
        "has_next": offset + page_size_value < total,
        "invoices": invoices,
    }


def find_reused_invoices(
    min_usage_count: int = 2,
    page: int = 1,
    page_size: int | None = None,
) -> dict[str, Any]:
    """List invoices used by at least min_usage_count reimbursement records."""
    return list_invoices(
        min_usage_count=max(2, int(min_usage_count or 2)),
        page=page,
        page_size=page_size,
        order_by="usage_count",
        sort_desc=True,
    )


def summarize_expenses(
    group_by: str = "department_id",
    employee_id: str | None = None,
    department_id: str | None = None,
    expense_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    special_approval: bool | None = None,
    limit: int = 100,
    sort_by: str = "total_amount",
    sort_desc: bool = True,
) -> dict[str, Any]:
    """Summarize reimbursement records by safe dimensions such as department, employee, type, or month."""
    requested = [part.strip() for part in str(group_by or "department_id").split(",") if part.strip()]
    requested = requested[:3] or ["department_id"]
    invalid = [field for field in requested if field not in SUMMARY_GROUP_COLUMNS]
    if invalid:
        raise ValueError(f"unsupported group_by fields: {', '.join(invalid)}")
    select_parts = [f"{SUMMARY_GROUP_COLUMNS[field]} AS {field}" for field in requested]
    group_sql = ", ".join(SUMMARY_GROUP_COLUMNS[field] for field in requested)
    where: list[str] = []
    params: list[Any] = []
    add_expense_filters(
        where,
        params,
        employee_id=employee_id,
        department_id=department_id,
        expense_type=expense_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        special_approval=special_approval,
    )
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    sort_columns = {
        "total_amount": "total_amount",
        "record_count": "record_count",
        "avg_amount": "avg_amount",
        "max_amount": "max_amount",
    }
    order_sql = safe_order(sort_by, sort_columns, "total_amount", bool(sort_desc))
    limit_value = max(1, min(int(limit or 100), 500))
    with readonly_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT {", ".join(select_parts)}, COUNT(*) AS record_count,
                   ROUND(SUM(r.amount), 2) AS total_amount,
                   ROUND(AVG(r.amount), 2) AS avg_amount,
                   ROUND(MAX(r.amount), 2) AS max_amount,
                   ROUND(MIN(r.amount), 2) AS min_amount
            FROM expense_records r
            {where_sql}
            GROUP BY {group_sql}
            ORDER BY {order_sql}
            LIMIT ?
            """,
            params + [limit_value],
        ).fetchall()
    return {"group_by": requested, "limit": limit_value, "rows": rows_to_dicts(rows)}


def summarize_department_budgets(status: str = "approved") -> dict[str, Any]:
    """Return all departments with annual budget, used amount, remaining amount, and usage rate."""
    with readonly_conn() as conn:
        rows = conn.execute(
            """
            SELECT d.department_id, d.department_name, d.annual_budget, d.manager_employee_id,
                   COALESCE(SUM(CASE WHEN r.status = ? THEN r.amount ELSE 0 END), 0) AS used_amount,
                   COUNT(CASE WHEN r.status = ? THEN 1 END) AS record_count
            FROM departments d
            LEFT JOIN expense_records r ON r.department_id = d.department_id
            GROUP BY d.department_id
            ORDER BY used_amount DESC, d.department_id
            """,
            (status, status),
        ).fetchall()
    departments = []
    for row in rows:
        item = dict(row)
        annual_budget = float(item["annual_budget"])
        used_amount = float(item["used_amount"])
        item["used_amount"] = round(used_amount, 2)
        item["remaining_amount"] = round(annual_budget - used_amount, 2)
        item["usage_rate"] = round(used_amount / annual_budget, 4) if annual_budget else None
        departments.append(item)
    return {"status": status, "departments": departments}


def list_records_by_reimburse_delay(
    min_delay_days: int = 0,
    max_delay_days: int | None = None,
    page: int = 1,
    page_size: int | None = None,
) -> dict[str, Any]:
    """List reimbursement records ordered by days between expense_date and reimburse_date."""
    page = max(1, int(page or 1))
    page_size_value = page_size_or_default(page_size)
    where = ["julianday(r.reimburse_date) - julianday(r.expense_date) >= ?"]
    params: list[Any] = [int(min_delay_days or 0)]
    if max_delay_days is not None:
        where.append("julianday(r.reimburse_date) - julianday(r.expense_date) <= ?")
        params.append(int(max_delay_days))
    where_sql = " WHERE " + " AND ".join(where)
    offset = (page - 1) * page_size_value
    with readonly_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM expense_records r{where_sql}", params).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT r.record_id, r.record_no, r.employee_id, e.employee_name, r.department_id,
                   d.department_name, r.expense_date, r.reimburse_date,
                   CAST(julianday(r.reimburse_date) - julianday(r.expense_date) AS INTEGER) AS delay_days,
                   r.expense_type, r.amount, r.status, i.invoice_no
            FROM expense_records r
            JOIN employees e ON e.employee_id = r.employee_id
            JOIN departments d ON d.department_id = r.department_id
            JOIN invoices i ON i.invoice_id = r.invoice_id
            {where_sql}
            ORDER BY delay_days DESC, r.record_id
            LIMIT ? OFFSET ?
            """,
            params + [page_size_value, offset],
        ).fetchall()
    return {
        "page": page,
        "page_size": page_size_value,
        "total": int(total),
        "has_next": offset + page_size_value < total,
        "records": rows_to_dicts(rows),
    }


def list_records_missing_approval(
    required_role: str,
    min_amount: float | None = None,
    max_amount: float | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int | None = None,
) -> dict[str, Any]:
    """List records that do not have an approval row for the required approver role."""
    page = max(1, int(page or 1))
    page_size_value = page_size_or_default(page_size)
    where: list[str] = []
    params: list[Any] = []
    add_expense_filters(
        where,
        params,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
    )
    where.append(
        """
        NOT EXISTS (
            SELECT 1 FROM approvals a
            WHERE a.record_id = r.record_id AND a.approver_role = ?
        )
        """
    )
    params.append(required_role)
    where_sql = " WHERE " + " AND ".join(where)
    offset = (page - 1) * page_size_value
    with readonly_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM expense_records r{where_sql}", params).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT r.record_id, r.record_no, r.employee_id, e.employee_name, r.department_id,
                   d.department_name, r.expense_date, r.reimburse_date, r.expense_type,
                   r.amount, r.status, i.invoice_no
            FROM expense_records r
            JOIN employees e ON e.employee_id = r.employee_id
            JOIN departments d ON d.department_id = r.department_id
            JOIN invoices i ON i.invoice_id = r.invoice_id
            {where_sql}
            ORDER BY r.amount DESC, r.record_id
            LIMIT ? OFFSET ?
            """,
            params + [page_size_value, offset],
        ).fetchall()
    return {
        "required_role": required_role,
        "page": page,
        "page_size": page_size_value,
        "total": int(total),
        "has_next": offset + page_size_value < total,
        "records": rows_to_dicts(rows),
    }


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
    "list_invoices": list_invoices,
    "find_reused_invoices": find_reused_invoices,
    "summarize_expenses": summarize_expenses,
    "summarize_department_budgets": summarize_department_budgets,
    "list_records_by_reimburse_delay": list_records_by_reimburse_delay,
    "list_records_missing_approval": list_records_missing_approval,
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
                "status": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
                "min_amount": {"type": "number"},
                "max_amount": {"type": "number"},
                "special_approval": {"type": "boolean"},
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
                "order_by": {
                    "type": "string",
                    "enum": ["record_id", "expense_date", "reimburse_date", "amount", "employee_id", "department_id", "expense_type"],
                    "default": "expense_date",
                },
                "sort_desc": {"type": "boolean", "default": False},
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
        "name": "list_invoices",
        "description": list_invoices.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "invoice_no": {"type": "string"},
                "expense_type": {"type": "string"},
                "vendor_name_contains": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
                "min_amount": {"type": "number"},
                "max_amount": {"type": "number"},
                "min_usage_count": {"type": "integer", "minimum": 1},
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
                "order_by": {
                    "type": "string",
                    "enum": ["invoice_no", "invoice_date", "amount", "usage_count"],
                    "default": "invoice_date",
                },
                "sort_desc": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "find_reused_invoices",
        "description": find_reused_invoices.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_usage_count": {"type": "integer", "minimum": 2, "default": 2},
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "summarize_expenses",
        "description": summarize_expenses.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "description": "Comma-separated safe dimensions: employee_id, department_id, expense_type, city_tier, status, budget_year, month.",
                    "default": "department_id",
                },
                "employee_id": {"type": "string"},
                "department_id": {"type": "string"},
                "expense_type": {"type": "string"},
                "status": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
                "min_amount": {"type": "number"},
                "max_amount": {"type": "number"},
                "special_approval": {"type": "boolean"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100},
                "sort_by": {
                    "type": "string",
                    "enum": ["total_amount", "record_count", "avg_amount", "max_amount"],
                    "default": "total_amount",
                },
                "sort_desc": {"type": "boolean", "default": True},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "summarize_department_budgets",
        "description": summarize_department_budgets.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"status": {"type": "string", "default": "approved"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "list_records_by_reimburse_delay",
        "description": list_records_by_reimburse_delay.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_delay_days": {"type": "integer", "minimum": 0, "default": 0},
                "max_delay_days": {"type": "integer", "minimum": 0},
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "list_records_missing_approval",
        "description": list_records_missing_approval.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "required_role": {"type": "string"},
                "min_amount": {"type": "number"},
                "max_amount": {"type": "number"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
            },
            "required": ["required_role"],
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
    invoices = call_tool("list_invoices", {"page": 1, "page_size": 3, "order_by": "usage_count", "sort_desc": True})
    reused = call_tool("find_reused_invoices", {"page": 1, "page_size": 3})
    summary = call_tool("summarize_expenses", {"group_by": "department_id,expense_type", "limit": 3})
    budgets = call_tool("summarize_department_budgets", {})
    delayed = call_tool("list_records_by_reimburse_delay", {"min_delay_days": 60, "page": 1, "page_size": 3})
    missing_approval = call_tool("list_records_missing_approval", {"required_role": "部门总经理", "min_amount": 3000, "page_size": 3})
    employees = call_tool("list_employees", {"department_id": detail["record"]["department_id"]})
    employee = call_tool("get_employee", {"employee_id": detail["record"]["employee_id"]})
    budget = call_tool("get_department_budget", {"department_id": detail["record"]["department_id"]})
    approvals = call_tool("list_approvals", {"record_id": record_id})
    return {
        "list_expenses": {"total": expenses["total"], "returned": len(expenses["records"]), "sample_record": record_id},
        "get_expense_detail": detail,
        "find_invoice_usage": invoice_usage,
        "list_invoices": {"total": invoices["total"], "returned": len(invoices["invoices"])},
        "find_reused_invoices": {"total": reused["total"], "returned": len(reused["invoices"])},
        "summarize_expenses": summary,
        "summarize_department_budgets": {"count": len(budgets["departments"]), "top": budgets["departments"][0]},
        "list_records_by_reimburse_delay": {"total": delayed["total"], "returned": len(delayed["records"])},
        "list_records_missing_approval": {"total": missing_approval["total"], "returned": len(missing_approval["records"])},
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
