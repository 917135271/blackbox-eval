import json, subprocess

# Department budgets from summarize_department_budgets
budgets = {
    "D001": {"name": "投资银行部", "budget": 230395.17, "used": 363614.58},
    "D002": {"name": "固定收益部", "budget": 107785.42, "used": 164928.12},
    "D003": {"name": "财富管理部", "budget": 109772.07, "used": 174150.67},
    "D004": {"name": "研究所", "budget": 264890.39, "used": 408832.95},
    "D005": {"name": "机构业务部", "budget": 278540.94, "used": 433442.76},
    "D006": {"name": "运营管理部", "budget": 340961.75, "used": 530241.29},
    "D007": {"name": "信息技术部", "budget": 301500.00, "used": 252588.38},
    "D008": {"name": "合规风控部", "budget": 381600.00, "used": 297095.29},
    "D009": {"name": "财务管理部", "budget": 191300.00, "used": 159294.06},
    "D010": {"name": "人力资源部", "budget": 164500.00, "used": 139536.39},
}

# Over-budget departments
over_budget = {k:v for k,v in budgets.items() if v["used"] > v["budget"]}
for d, info in over_budget.items():
    print(f"{d} {info['name']}: budget={info['budget']:.2f}, used={info['used']:.2f}, over={info['used']-info['budget']:.2f}")

print("\n--- Summary ---")
print(f"6 departments over budget: D001, D002, D003, D004, D005, D006")
