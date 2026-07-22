import json, os, sys
sys.path.insert(0, '/benchmark')
from tools.expense_query_tool import ExpenseQueryTool

tool = ExpenseQueryTool()

all_records = []
page = 1
while True:
    result = tool.list_expenses(page=page, page_size=100)
    records = result.get("records", [])
    if not records:
        break
    all_records.extend(records)
    if not result.get("has_next", False):
        break
    page += 1

# Save to file
with open("/workspace/work/all_expenses.json", "w") as f:
    json.dump(all_records, f, ensure_ascii=False)

print(f"Total records fetched: {len(all_records)}")
