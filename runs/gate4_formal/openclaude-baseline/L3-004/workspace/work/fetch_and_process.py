import json, sys

# Budget data from summarize_department_budgets
budgets = {
    "D001": {"name": "投资银行部", "annual_budget": 230395.17},
    "D002": {"name": "固定收益部", "annual_budget": 107785.42},
    "D003": {"name": "财富管理部", "annual_budget": 109772.07},
    "D004": {"name": "研究所", "annual_budget": 264890.39},
    "D005": {"name": "机构业务部", "annual_budget": 278540.94},
    "D006": {"name": "运营管理部", "annual_budget": 340961.75},
}

# We'll process the data and output the tipping point for each dept
print("Script ready. Will process MCP data.")
