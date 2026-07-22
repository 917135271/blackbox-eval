import json, sqlite3, subprocess, sys

db = sqlite3.connect('/workspace/audit.db')
db.executescript('''
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS approvals;

CREATE TABLE expenses (
    record_id TEXT PRIMARY KEY,
    record_no TEXT,
    employee_id TEXT,
    employee_name TEXT,
    department_id TEXT,
    department_name TEXT,
    expense_date TEXT,
    reimburse_date TEXT,
    expense_type TEXT,
    amount REAL,
    reason TEXT,
    invoice_no TEXT,
    status TEXT,
    special_approval INTEGER DEFAULT 0
);

CREATE TABLE invoices (
    invoice_no TEXT PRIMARY KEY,
    vendor_name TEXT,
    invoice_date TEXT,
    amount REAL,
    expense_type TEXT,
    usage_count INTEGER,
    record_ids TEXT
);

CREATE TABLE employees (
    employee_id TEXT PRIMARY KEY,
    employee_name TEXT,
    department_id TEXT,
    role TEXT,
    level TEXT,
    hire_date TEXT
);

CREATE TABLE approvals (
    record_id TEXT,
    approver_id TEXT,
    approver_name TEXT,
    approver_role TEXT,
    action TEXT,
    comment TEXT
);
''')

# Load all expenses
total = 0
for page in range(1, 44):
    result = subprocess.run(
        ['codex-cli', 'mcp', 'call', 'expense_query', 'list_expenses',
         json.dumps({"page": page, "page_size": 100, "order_by": "record_id", "sort_desc": False})],
        capture_output=True, text=True, cwd='/workspace', timeout=60
    )
    try:
        data = json.loads(result.stdout)
        recs = data.get('records', data.get('data', []))
        # Try different formats
        if isinstance(data, dict) and 'result' in data:
            inner = json.loads(data['result'])
            recs = inner.get('records', [])
    except:
        recs = []
    for r in recs:
        db.execute('''INSERT OR REPLACE INTO expenses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (r['record_id'], r.get('record_no',''), r['employee_id'], r.get('employee_name',''),
             r['department_id'], r.get('department_name',''),
             r['expense_date'], r['reimburse_date'], r['expense_type'],
             r['amount'], r.get('reason',''), r['invoice_no'], r.get('status',''),
             r.get('special_approval', 0)))
    total += len(recs)
    print(f"Page {page}: {len(recs)} records (total so far: {total})")

db.commit()
print(f"Total expenses: {db.execute('SELECT COUNT(*) FROM expenses').fetchone()[0]}")
db.close()
