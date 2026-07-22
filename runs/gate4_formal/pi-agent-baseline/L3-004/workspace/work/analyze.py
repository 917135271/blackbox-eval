import json
import sys

# Budget data from summarize_department_budgets
budgets = {
    "D001": {"name": "投资银行部", "budget": 230395.17},
    "D002": {"name": "固定收益部", "budget": 107785.42},
    "D003": {"name": "财富管理部", "budget": 109772.07},
    "D004": {"name": "研究所", "budget": 264890.39},
    "D005": {"name": "机构业务部", "budget": 278540.94},
    "D006": {"name": "运营管理部", "budget": 340961.75},
    "D007": {"name": "信息技术部", "budget": 301500.00},
    "D008": {"name": "合规风控部", "budget": 381600.00},
    "D009": {"name": "财务管理部", "budget": 191300.00},
    "D010": {"name": "人力资源部", "budget": 164500.00},
}

# Each department file needs to be read. Let's load from files.
# For now, let me just process what I have.

print("Budgets loaded:", file=sys.stderr)
for dept_id, info in budgets.items():
    print(f"  {dept_id} ({info['name']}): {info['budget']:.2f}", file=sys.stderr)

# Over-budget departments: D001, D002, D003, D004, D005, D006
# We need to save data and compute

# I'll save the expense data to a file and process it
print("Ready to process", file=sys.stderr)
