import json

budgets = {
    "D001": 230395.17, "D002": 107785.42, "D003": 109772.07,
    "D004": 264890.39, "D005": 278540.94, "D006": 340961.75,
}
dept_names = {
    "D001": "投资银行部", "D002": "固定收益部", "D003": "财富管理部",
    "D004": "研究所", "D005": "机构业务部", "D006": "运营管理部",
}

# Load all data files
all_records = []
for i in range(1, 11):
    try:
        with open(f"/workspace/work/dept_data_{i}.json") as f:
            data = json.load(f)
            if "records" in data:
                all_records.extend(data["records"])
    except:
        pass

dept_records = {}
for r in all_records:
    did = r["department_id"]
    dept_records.setdefault(did, []).append(r)

for did in ["D001", "D002", "D003", "D004", "D005", "D006"]:
    recs = sorted(dept_records.get(did, []), key=lambda r: (r["reimburse_date"], r["record_id"]))
    cum = 0.0
    cross = None
    for r in recs:
        cum += r["amount"]
        if cross is None and cum > budgets[did]:
            cross = r
    print(f"{did} {dept_names[did]}: budget={budgets[did]}, total={cum:.2f}, crossover={cross['record_id'] if cross else 'NONE'}, date={cross['reimburse_date'] if cross else 'N/A'}, amount={cross['amount']:.2f if cross else 0}")
