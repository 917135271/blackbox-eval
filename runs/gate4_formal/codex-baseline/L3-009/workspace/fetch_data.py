import json, sqlite3, subprocess, sys

db = sqlite3.connect('/workspace/audit.db')
db.execute('''CREATE TABLE IF NOT EXISTS expenses (
    record_id TEXT PRIMARY KEY,
    employee_id TEXT,
    department_id TEXT,
    expense_date TEXT,
    reimburse_date TEXT,
    expense_type TEXT,
    amount REAL,
    invoice_no TEXT,
    status TEXT,
    reason TEXT,
    special_approval INTEGER DEFAULT 0
)''')
db.execute('''CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT,
    invoice_no TEXT,
    vendor_name TEXT,
    invoice_date TEXT,
    amount REAL,
    expense_type TEXT,
    usage_count INTEGER,
    record_ids TEXT
)''')
db.commit()

# Fetch all expenses
for page in range(1, 44):
    result = subprocess.run(
        ['codex-cli', 'mcp', 'call', 'expense_query', 'list_expenses',
         json.dumps({"page": page, "page_size": 100, "sort_desc": False, "order_by": "record_id"})],
        capture_output=True, text=True, cwd='/workspace', timeout=60
    )
    try:
        data = json.loads(result.stdout)
        recs = data.get('records', [])
        for r in recs:
            db.execute('''INSERT OR REPLACE INTO expenses VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (r['record_id'], r['employee_id'], r['department_id'],
                 r['expense_date'], r['reimburse_date'], r['expense_type'],
                 r['amount'], r['invoice_no'], r['status'], r.get('reason',''), 0))
        print(f"Page {page}: {len(recs)} records")
    except Exception as e:
        print(f"Page {page} error: {e}")

db.commit()
print(f"Total: {db.execute('SELECT COUNT(*) FROM expenses').fetchone()[0]}")
