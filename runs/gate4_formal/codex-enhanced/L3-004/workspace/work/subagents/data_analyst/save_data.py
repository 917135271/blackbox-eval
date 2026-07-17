import json, os

# Initialize accumulator
data = {}
path = "/workspace/work/subagents/data_analyst/_records_raw.json"
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)

# Budget summary (confirmed)
budget_summary = {
    "departments": {
        "D001": {"name": "投资银行部", "annual_budget": 230395.17, "used_amount": 363614.58, "remaining": -133219.41, "usage_rate": 1.5782, "record_count": 525},
        "D002": {"name": "固定收益部", "annual_budget": 107785.42, "used_amount": 164928.12, "remaining": -57142.70, "usage_rate": 1.5302, "record_count": 254},
        "D003": {"name": "财富管理部", "annual_budget": 109772.07, "used_amount": 174150.67, "remaining": -64378.60, "usage_rate": 1.5865, "record_count": 249},
        "D004": {"name": "研究所", "annual_budget": 264890.39, "used_amount": 408832.95, "remaining": -143942.56, "usage_rate": 1.5434, "record_count": 611},
        "D005": {"name": "机构业务部", "annual_budget": 278540.94, "used_amount": 433442.76, "remaining": -154901.82, "usage_rate": 1.5561, "record_count": 616},
        "D006": {"name": "运营管理部", "annual_budget": 340961.75, "used_amount": 530241.29, "remaining": -189279.54, "usage_rate": 1.5551, "record_count": 833},
        "D007": {"name": "信息技术部", "annual_budget": 301500.00, "used_amount": 252588.38, "remaining": 48911.62, "usage_rate": 0.8378, "record_count": 342},
        "D008": {"name": "合规风控部", "annual_budget": 381600.00, "used_amount": 297095.29, "remaining": 84504.71, "usage_rate": 0.7786, "record_count": 376},
        "D009": {"name": "财务管理部", "annual_budget": 191300.00, "used_amount": 159294.06, "remaining": 32005.94, "usage_rate": 0.8327, "record_count": 253},
        "D010": {"name": "人力资源部", "annual_budget": 164500.00, "used_amount": 139536.39, "remaining": 24963.61, "usage_rate": 0.8482, "record_count": 181},
    }
}

data["budget_summary"] = budget_summary

with open(path, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved budget summary. Pages retrieved so far:")
for dept in ["D001","D002","D003","D004","D005","D006"]:
    pages = data.get("pages", {}).get(dept, [])
    print(f"  {dept}: {len(pages)} pages ({sum(len(p) for p in pages)} records)")
