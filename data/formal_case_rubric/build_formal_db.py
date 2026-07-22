from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "expense.db"
OUTPUT = Path(__file__).with_name("expense_formal.db")

GENERIC_REASONS = {
    "travel_lodging": "项目现场住宿费",
    "local_transport": "市内业务交通费",
    "training_fee": "外部专业培训课程费",
    "business_entertainment": "客户交流活动招待费",
    "office_supplies": "项目资料及办公耗材采购",
    "communication": "业务通讯费",
}

GENERIC_VENDORS = {
    "travel_lodging": "安程酒店管理有限公司",
    "local_transport": "城际出行服务有限公司",
    "training_fee": "知行培训服务有限公司",
    "business_entertainment": "嘉禾餐饮服务有限公司",
    "office_supplies": "华文办公服务有限公司",
    "communication": "联讯通信服务有限公司",
}

FORMAL_REASON_OVERRIDES = {
    "R004239": "客户甲产品方案交流招待费",
    "R004240": "客户乙投行业务沟通招待费",
}

BUSINESS_CODEBOOK = [
    ("employee_level", "E1", "员工级"),
    ("employee_level", "M1", "经理级"),
    ("employee_level", "D1", "部门负责人级"),
    ("employee_level", "X1", "高管级"),
    ("city_tier", "A", "一类城市"),
    ("city_tier", "B", "二类城市"),
    ("city_tier", "C", "三类城市"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_database(destination: Path) -> None:
    shutil.copy2(SOURCE, destination)
    with closing(sqlite3.connect(destination)) as connection:
        rows = connection.execute(
            """
            SELECT record_id, expense_type, reason, invoice_id
            FROM expense_records
            WHERE record_id BETWEEN 'R004201' AND 'R004240'
            ORDER BY record_id
            """
        ).fetchall()
        for record_id, expense_type, reason, invoice_id in rows:
            clean_reason = str(reason)
            if clean_reason.startswith("重复发票注入样本:"):
                clean_reason = clean_reason.split(":", 1)[1]
            elif "注入样本" in clean_reason or clean_reason.startswith("陷阱样本:"):
                clean_reason = GENERIC_REASONS[str(expense_type)]
            clean_reason = FORMAL_REASON_OVERRIDES.get(str(record_id), clean_reason)
            connection.execute(
                "UPDATE expense_records SET reason = ? WHERE record_id = ?",
                (clean_reason, record_id),
            )
            vendor = GENERIC_VENDORS.get(str(expense_type))
            if vendor:
                connection.execute(
                    """
                    UPDATE invoices
                    SET vendor_name = ?
                    WHERE invoice_id = ? AND vendor_name LIKE '%注入%'
                    """,
                    (vendor, invoice_id),
                )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS business_codebook (
                field_name TEXT NOT NULL,
                code TEXT NOT NULL,
                display_name TEXT NOT NULL,
                PRIMARY KEY (field_name, code)
            )
            """
        )
        connection.execute("DELETE FROM business_codebook")
        connection.executemany(
            "INSERT INTO business_codebook(field_name, code, display_name) VALUES (?, ?, ?)",
            BUSINESS_CODEBOOK,
        )
        connection.commit()


def validate_database(path: Path) -> None:
    with closing(sqlite3.connect(SOURCE)) as source_connection, closing(
        sqlite3.connect(path)
    ) as connection:
        source_count = source_connection.execute("SELECT COUNT(*) FROM expense_records").fetchone()[0]
        output_count = connection.execute("SELECT COUNT(*) FROM expense_records").fetchone()[0]
        if source_count != output_count:
            raise ValueError(f"record count changed: source={source_count}, formal={output_count}")
        leaked_reasons = connection.execute(
            "SELECT COUNT(*) FROM expense_records WHERE reason LIKE '%注入%' OR reason LIKE '%陷阱样本%'"
        ).fetchone()[0]
        leaked_vendors = connection.execute(
            "SELECT COUNT(*) FROM invoices WHERE vendor_name LIKE '%注入%'"
        ).fetchone()[0]
        if leaked_reasons or leaked_vendors:
            raise ValueError(
                f"answer-label leakage remains: reasons={leaked_reasons}, vendors={leaked_vendors}"
            )
        boundary_reasons = dict(
            connection.execute(
                "SELECT record_id, reason FROM expense_records WHERE record_id IN ('R004239', 'R004240')"
            ).fetchall()
        )
        if boundary_reasons != FORMAL_REASON_OVERRIDES:
            raise ValueError("TRAP-005 business contexts are not distinct and reproducible")
        codebook_rows = connection.execute(
            "SELECT field_name, code, display_name FROM business_codebook ORDER BY field_name, code"
        ).fetchall()
        if codebook_rows != sorted(BUSINESS_CODEBOOK):
            raise ValueError("business codebook is incomplete or inconsistent")
        for table, excluded in {
            "expense_records": {"reason"},
            "invoices": {"vendor_name"},
            "employees": set(),
            "departments": set(),
            "approvals": set(),
        }.items():
            columns = [
                row[1]
                for row in source_connection.execute(f"PRAGMA table_info({table})")
                if row[1] not in excluded
            ]
            projection = ", ".join(columns)
            source_rows = source_connection.execute(
                f"SELECT {projection} FROM {table} ORDER BY 1"
            ).fetchall()
            formal_rows = connection.execute(
                f"SELECT {projection} FROM {table} ORDER BY 1"
            ).fetchall()
            if source_rows != formal_rows:
                raise ValueError(f"business fields changed outside the sanitization scope: {table}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the answer-label-free formal expense database.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit(f"missing generated database: {OUTPUT}")
        # Keep verification databases outside the repository. On Windows,
        # workspace indexers can briefly lock newly-created SQLite files and
        # make TemporaryDirectory cleanup fail even after SQLite has closed.
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / OUTPUT.name
            sanitize_database(candidate)
            validate_database(candidate)
            if sha256(candidate) != sha256(OUTPUT):
                raise SystemExit(f"stale generated database: {OUTPUT}")
        validate_database(OUTPUT)
        print(f"formal database check passed: {OUTPUT} sha256={sha256(OUTPUT)}")
        return 0
    sanitize_database(OUTPUT)
    validate_database(OUTPUT)
    print(f"formal database built: {OUTPUT} sha256={sha256(OUTPUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
