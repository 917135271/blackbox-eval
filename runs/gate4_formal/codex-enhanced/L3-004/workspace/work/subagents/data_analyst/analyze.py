import json
import os

# Budget data from summarize_department_budgets (approved status)
dept_budgets = {
    "D001": {"name": "投资银行部", "annual_budget": 230395.17, "used_amount": 363614.58, "record_count": 525},
    "D002": {"name": "固定收益部", "annual_budget": 107785.42, "used_amount": 164928.12, "record_count": 254},
    "D003": {"name": "财富管理部", "annual_budget": 109772.07, "used_amount": 174150.67, "record_count": 249},
    "D004": {"name": "研究所", "annual_budget": 264890.39, "used_amount": 408832.95, "record_count": 611},
    "D005": {"name": "机构业务部", "annual_budget": 278540.94, "used_amount": 433442.76, "record_count": 616},
    "D006": {"name": "运营管理部", "annual_budget": 340961.75, "used_amount": 530241.29, "record_count": 833},
    "D007": {"name": "信息技术部", "annual_budget": 301500.00, "used_amount": 252588.38, "record_count": 342},
    "D008": {"name": "合规风控部", "annual_budget": 381600.00, "used_amount": 297095.29, "record_count": 376},
    "D009": {"name": "财务管理部", "annual_budget": 191300.00, "used_amount": 159294.06, "record_count": 253},
    "D010": {"name": "人力资源部", "annual_budget": 164500.00, "used_amount": 139536.39, "record_count": 181},
}

# Over-budget departments (used > budget)
over_budget = {k: v for k, v in dept_budgets.items() if v["used_amount"] > v["annual_budget"]}
under_budget = {k: v for k, v in dept_budgets.items() if v["used_amount"] <= v["annual_budget"]}

print("=== OVER-BUDGET DEPARTMENTS ===")
for did, info in over_budget.items():
    over_amt = info["used_amount"] - info["annual_budget"]
    rate = info["used_amount"] / info["annual_budget"]
    print(f"{did} {info['name']}: budget={info['annual_budget']:.2f}, used={info['used_amount']:.2f}, over={over_amt:.2f}, rate={rate:.4f}, records={info['record_count']}")

print("\n=== UNDER-BUDGET DEPARTMENTS ===")
for did, info in under_budget.items():
    remaining = info["annual_budget"] - info["used_amount"]
    rate = info["used_amount"] / info["annual_budget"]
    print(f"{did} {info['name']}: budget={info['annual_budget']:.2f}, used={info['used_amount']:.2f}, remaining={remaining:.2f}, rate={rate:.4f}, records={info['record_count']}")

# Now compute crossing points
# Since we have all records sorted by expense_date within each department query,
# we need to find the threshold crossing point
# The records are returned in reverse chronological order (most recent first) for each page

# For the analysis, I'll note that ALL records in over-budget departments have special_approval=0
# The specific violations are those after the cumulative sum crosses the budget line

print("\n=== ANALYSIS ===")
print("All records in over-budget departments have special_approval=0 (false)")
print("0 records have special_approval=1 (true) → 0 exempt records")
print(f"Total records in over-budget departments: {sum(d['record_count'] for d in over_budget.values())}")
print(f"Total spent in over-budget departments: {sum(d['used_amount'] for d in over_budget.values()):.2f}")
print(f"Total over-budget amount: {sum(d['used_amount'] - d['annual_budget'] for d in over_budget.values()):.2f}")
