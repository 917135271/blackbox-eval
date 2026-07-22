import json

budgets = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
}

dept_names = {
    "D001": "投资银行部",
    "D002": "固定收益部",
    "D003": "财富管理部",
    "D004": "研究所",
    "D005": "机构业务部",
    "D006": "运营管理部",
}

# Load data from saved JSON files
# I'll create a combined file from the API output
import os

# Check if we have saved data
data_files = {}
for dept in budgets:
    fname = f"/workspace/work/dept_{dept}.json"
    if os.path.exists(fname):
        with open(fname) as f:
            data_files[dept] = json.load(f)

print("Data files found:", list(data_files.keys()))
