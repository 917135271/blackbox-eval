import json, sys

# Data we've already collected
budgets = {
    "D001": {"name": "投资银行部", "budget": 230395.17, "cumulative": 363614.58},
    "D002": {"name": "固定收益部", "budget": 107785.42, "cumulative": 164928.12},
    "D003": {"name": "财富管理部", "budget": 109772.07, "cumulative": 174150.67},
    "D004": {"name": "研究所", "budget": 264890.39, "cumulative": 408832.95},
    "D005": {"name": "机构业务部", "budget": 278540.94, "cumulative": 433442.76},
    "D006": {"name": "运营管理部", "budget": 340961.75, "cumulative": 530241.29},
    "D007": {"name": "信息技术部", "budget": 301500.00, "cumulative": 252588.38},
    "D008": {"name": "合规风控部", "budget": 381600.00, "cumulative": 297095.29},
    "D009": {"name": "财务管理部", "budget": 191300.00, "cumulative": 159294.06},
    "D010": {"name": "人力资源部", "budget": 164500.00, "cumulative": 139536.39},
}

print("=== BUDGET OVERRUN DEPARTMENTS ===")
for did, d in budgets.items():
    if d["cumulative"] > d["budget"]:
        print(f"{did} {d['name']}: budget={d['budget']}, cumulative={d['cumulative']}, over={d['cumulative']-d['budget']:.2f}")

# Duplicate invoices
dupes = [
    {"invoice": "FP202500000002", "records": ["R000002", "R004201"], "amount": 423.79, "type": "office_supplies"},
    {"invoice": "FP202500000005", "records": ["R000005", "R004202"], "amount": 88.83, "type": "local_transport"},
    {"invoice": "FP202500000020", "records": ["R000020", "R004203"], "amount": 669.50, "type": "travel_lodging"},
    {"invoice": "FP202500000028", "records": ["R000028", "R004204"], "amount": 165.58, "type": "communication"},
    {"invoice": "FP202500000037", "records": ["R000037", "R004205"], "amount": 84.72, "type": "local_transport"},
    {"invoice": "FP202500000055", "records": ["R000055", "R004206"], "amount": 999.76, "type": "business_entertainment"},
]

print("\n=== DUPLICATE INVOICES ===")
for d in dupes:
    print(f"  {d['invoice']}: {d['records']} ({d['type']}, {d['amount']})")

