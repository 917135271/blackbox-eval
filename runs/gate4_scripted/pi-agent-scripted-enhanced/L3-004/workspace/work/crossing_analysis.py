import json

# Budget data
budgets = {
    "D001": {"name": "投资银行部", "budget": 230395.17},
    "D002": {"name": "固定收益部", "budget": 107785.42},
    "D003": {"name": "财富管理部", "budget": 109772.07},
    "D004": {"name": "研究所", "budget": 264890.39},
    "D005": {"name": "机构业务部", "budget": 278540.94},
    "D006": {"name": "运营管理部", "budget": 340961.75},
}

print("Ready for crossing analysis")
print("Budgets:", json.dumps(budgets, indent=2, ensure_ascii=False))
