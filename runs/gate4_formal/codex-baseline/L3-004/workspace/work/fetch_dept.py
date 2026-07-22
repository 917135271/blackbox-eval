import json

# Department budgets from summarize_department_budgets
depts = {
    "D001": {"name": "投资银行部", "budget": 230395.17},
    "D002": {"name": "固定收益部", "budget": 107785.42},
    "D003": {"name": "财富管理部", "budget": 109772.07},
    "D004": {"name": "研究所", "budget": 264890.39},
    "D005": {"name": "机构业务部", "budget": 278540.94},
    "D006": {"name": "运营管理部", "budget": 340961.75},
}

# Save the query parameters we'll use
print(json.dumps(depts, ensure_ascii=False, indent=2))
