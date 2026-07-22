import json
import subprocess
import sys

# Use the ExpenseQuery Python module if available
sys.path.insert(0, '/benchmark')
sys.path.insert(0, '/benchmark/data')

# Let's try importing the backend
try:
    from expense_query_backend import get_all_expenses, get_department_budgets, get_reused_invoices, get_delay_records
    print("Module loaded successfully")
except Exception as e:
    print(f"Import error: {e}")
    # Try alternate paths
    import os
    for root, dirs, files in os.walk('/benchmark'):
        for f in files:
            if f.endswith('.py') and 'expense' in f.lower():
                print(f"Found: {os.path.join(root, f)}")
