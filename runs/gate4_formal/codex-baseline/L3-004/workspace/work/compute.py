import json

# Department budgets
budgets = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
    "D007": 301500.00,
    "D008": 381600.00,
    "D009": 191300.00,
    "D010": 164500.00,
}

# Monthly data from summarize_expenses (all rows)
monthly = [
    {"department_id":"D006","month":"2025-12","record_count":117,"total_amount":77754.87},
    {"department_id":"D005","month":"2025-12","record_count":99,"total_amount":72371.46},
    {"department_id":"D001","month":"2025-12","record_count":85,"total_amount":60393.59},
    {"department_id":"D004","month":"2025-12","record_count":98,"total_amount":59968.97},
    {"department_id":"D005","month":"2025-03","record_count":75,"total_amount":57973.11},
    {"department_id":"D006","month":"2025-03","record_count":78,"total_amount":53721.76},
    {"department_id":"D006","month":"2025-04","record_count":65,"total_amount":49822.95},
    {"department_id":"D004","month":"2025-03","record_count":58,"total_amount":47347.40},
    {"department_id":"D006","month":"2025-08","record_count":53,"total_amount":45786.27},
    {"department_id":"D006","month":"2025-09","record_count":62,"total_amount":45343.40},
    {"department_id":"D004","month":"2025-06","record_count":58,"total_amount":44386.08},
    {"department_id":"D001","month":"2025-03","record_count":49,"total_amount":42626.88},
    {"department_id":"D008","month":"2025-03","record_count":48,"total_amount":41387.32},
    {"department_id":"D006","month":"2025-05","record_count":68,"total_amount":40870.08},
    {"department_id":"D006","month":"2025-06","record_count":72,"total_amount":40407.27},
    {"department_id":"D001","month":"2025-11","record_count":55,"total_amount":40356.31},
    {"department_id":"D006","month":"2025-01","record_count":64,"total_amount":39605.79},
    {"department_id":"D005","month":"2025-06","record_count":44,"total_amount":38725.49},
    {"department_id":"D001","month":"2025-01","record_count":47,"total_amount":38344.08},
    {"department_id":"D004","month":"2025-11","record_count":61,"total_amount":37428.15},
    {"department_id":"D006","month":"2025-11","record_count":92,"total_amount":37427.74},
    {"department_id":"D005","month":"2025-08","record_count":35,"total_amount":37145.53},
    {"department_id":"D006","month":"2025-10","record_count":54,"total_amount":35981.53},
    {"department_id":"D008","month":"2025-12","record_count":42,"total_amount":35182.78},
    {"department_id":"D004","month":"2025-07","record_count":47,"total_amount":35104.98},
    {"department_id":"D005","month":"2025-01","record_count":38,"total_amount":34696.05},
    {"department_id":"D006","month":"2025-02","record_count":51,"total_amount":34269.35},
    {"department_id":"D007","month":"2025-09","record_count":37,"total_amount":33153.36},
    {"department_id":"D005","month":"2025-11","record_count":58,"total_amount":33145.99},
    {"department_id":"D001","month":"2025-04","record_count":37,"total_amount":32447.08},
    {"department_id":"D007","month":"2025-01","record_count":39,"total_amount":32414.25},
    {"department_id":"D004","month":"2025-01","record_count":47,"total_amount":30390.75},
    {"department_id":"D005","month":"2025-02","record_count":39,"total_amount":30343.93},
    {"department_id":"D005","month":"2025-09","record_count":30,"total_amount":29930.44},
    {"department_id":"D004","month":"2025-04","record_count":35,"total_amount":29081.42},
    {"department_id":"D005","month":"2025-10","record_count":44,"total_amount":28936.93},
    {"department_id":"D006","month":"2025-07","record_count":57,"total_amount":27974.94},
    {"department_id":"D004","month":"2025-09","record_count":34,"total_amount":27689.09},
    {"department_id":"D004","month":"2025-08","record_count":33,"total_amount":26494.47},
    {"department_id":"D001","month":"2025-07","record_count":30,"total_amount":25908.86},
    {"department_id":"D001","month":"2025-09","record_count":25,"total_amount":24226.82},
    {"department_id":"D008","month":"2025-06","record_count":31,"total_amount":23183.77},
    {"department_id":"D005","month":"2025-07","record_count":34,"total_amount":22507.67},
    {"department_id":"D001","month":"2025-05","record_count":24,"total_amount":22143.93},
    {"department_id":"D001","month":"2025-06","record_count":25,"total_amount":21544.99},
    {"department_id":"D008","month":"2025-01","record_count":29,"total_amount":21510.34},
    {"department_id":"D003","month":"2025-05","record_count":24,"total_amount":20544.75},
    {"department_id":"D008","month":"2025-07","record_count":32,"total_amount":19936.06},
    {"department_id":"D008","month":"2025-08","record_count":28,"total_amount":19779.46},
    {"department_id":"D005","month":"2025-04","record_count":24,"total_amount":19752.98},
    {"department_id":"D008","month":"2025-05","record_count":21,"total_amount":19690.16},
    {"department_id":"D010","month":"2025-03","record_count":13,"total_amount":19441.27},
    {"department_id":"D004","month":"2025-02","record_count":29,"total_amount":19438.18},
    {"department_id":"D008","month":"2025-11","record_count":26,"total_amount":19382.04},
    {"department_id":"D009","month":"2025-03","record_count":22,"total_amount":19335.46},
    {"department_id":"D007","month":"2025-11","record_count":29,"total_amount":18507.96},
    {"department_id":"D007","month":"2025-04","record_count":25,"total_amount":18391.05},
    {"department_id":"D003","month":"2025-01","record_count":23,"total_amount":17606.70},
    {"department_id":"D004","month":"2025-10","record_count":21,"total_amount":17563.15},
    {"department_id":"D008","month":"2025-10","record_count":20,"total_amount":17537.13},
    {"department_id":"D008","month":"2025-02","record_count":22,"total_amount":17497.76},
    {"department_id":"D003","month":"2025-03","record_count":15,"total_amount":17300.28},
    {"department_id":"D008","month":"2025-09","record_count":32,"total_amount":17128.19},
    {"department_id":"D005","month":"2025-05","record_count":17,"total_amount":16682.02},
    {"department_id":"D001","month":"2025-10","record_count":22,"total_amount":16371.12},
    {"department_id":"D003","month":"2025-11","record_count":23,"total_amount":16244.17},
    {"department_id":"D009","month":"2025-05","record_count":20,"total_amount":15809.09},
    {"department_id":"D007","month":"2025-08","record_count":17,"total_amount":15443.05},
    {"department_id":"D007","month":"2025-10","record_count":22,"total_amount":15263.23},
    {"department_id":"D010","month":"2025-06","record_count":14,"total_amount":14957.02},
    {"department_id":"D009","month":"2025-04","record_count":19,"total_amount":14937.12},
    {"department_id":"D003","month":"2025-12","record_count":18,"total_amount":14916.76},
    {"department_id":"D007","month":"2025-07","record_count":26,"total_amount":14901.73},
    {"department_id":"D010","month":"2025-12","record_count":20,"total_amount":14898.92},
    {"department_id":"D002","month":"2025-03","record_count":19,"total_amount":14703.78},
    {"department_id":"D002","month":"2025-12","record_count":22,"total_amount":14701.54},
    {"department_id":"D003","month":"2025-09","record_count":18,"total_amount":14411.77},
    {"department_id":"D007","month":"2025-12","record_count":18,"total_amount":14312.70},
    {"department_id":"D001","month":"2025-08","record_count":28,"total_amount":14187.70},
    {"department_id":"D001","month":"2025-02","record_count":24,"total_amount":14045.86},
    {"department_id":"D010","month":"2025-10","record_count":15,"total_amount":13885.78},
    {"department_id":"D003","month":"2025-02","record_count":11,"total_amount":13600.80},
    {"department_id":"D008","month":"2025-04","record_count":25,"total_amount":13191.71},
    {"department_id":"D002","month":"2025-01","record_count":19,"total_amount":12890.42},
    {"department_id":"D010","month":"2025-08","record_count":14,"total_amount":12718.85},
    {"department_id":"D002","month":"2025-07","record_count":23,"total_amount":12560.68},
    {"department_id":"D003","month":"2025-10","record_count":20,"total_amount":12383.12},
    {"department_id":"D009","month":"2025-06","record_count":20,"total_amount":11898.58},
    {"department_id":"D002","month":"2025-06","record_count":22,"total_amount":11855.36},
    {"department_id":"D002","month":"2025-09","record_count":21,"total_amount":11699.20},
    {"department_id":"D003","month":"2025-07","record_count":22,"total_amount":11286.00},
    {"department_id":"D009","month":"2025-10","record_count":23,"total_amount":11105.91},
    {"department_id":"D009","month":"2025-08","record_count":15,"total_amount":10806.09},
    {"department_id":"D003","month":"2025-08","record_count":20,"total_amount":10417.79},
    {"department_id":"D007","month":"2025-02","record_count":15,"total_amount":10076.27},
    {"department_id":"D002","month":"2025-02","record_count":14,"total_amount":10064.14},
    {"department_id":"D010","month":"2025-05","record_count":15,"total_amount":9406.64},
    {"department_id":"D010","month":"2025-04","record_count":11,"total_amount":9373.15},
    {"department_id":"D002","month":"2025-04","record_count":21,"total_amount":8654.53},
    {"department_id":"D010","month":"2025-02","record_count":9,"total_amount":8463.75},
    {"department_id":"D002","month":"2025-05","record_count":10,"total_amount":8448.14},
    {"department_id":"D010","month":"2025-01","record_count":13,"total_amount":8237.72},
    {"department_id":"D010","month":"2025-07","record_count":11,"total_amount":8205.45},
    {"department_id":"D010","month":"2025-11","record_count":18,"total_amount":8165.98},
    {"department_id":"D010","month":"2025-09","record_count":13,"total_amount":8076.23},
    {"department_id":"D009","month":"2025-07","record_count":16,"total_amount":7916.88},
    {"department_id":"D003","month":"2025-06","record_count":13,"total_amount":7028.40},
    {"department_id":"D002","month":"2025-11","record_count":15,"total_amount":6368.90},
    {"department_id":"D009","month":"2025-01","record_count":19,"total_amount":6100.72},
    {"department_id":"D009","month":"2025-09","record_count":15,"total_amount":5882.94},
    {"department_id":"D009","month":"2025-02","record_count":13,"total_amount":5215.15},
    {"department_id":"D003","month":"2025-04","record_count":18,"total_amount":4995.86},
]

# Also need missing months. The response was limited to 120, so some months may be missing.
# Let me compute what we have and identify gaps.

# Group by department and month
from collections import defaultdict
dept_monthly = defaultdict(dict)
for row in monthly:
    dept_monthly[row["department_id"]][row["month"]] = row["total_amount"]

# All months
months = [f"2025-{m:02d}" for m in range(1, 13)]
over_budget_depts = ["D001", "D002", "D003", "D004", "D005", "D006"]

print("=== CUMULATIVE ANALYSIS ===")
for dept in over_budget_depts:
    budget = budgets[dept]
    cum = 0
    found_month = None
    for m in months:
        amt = dept_monthly[dept].get(m, 0)
        cum_before = cum
        cum += amt
        if cum_before <= budget and cum > budget and found_month is None:
            found_month = m
            print(f"{dept}: budget={budget:.2f}, crossed at month={m}, cum_before={cum_before:.2f}, cum_after={cum:.2f}, month_amount={amt:.2f}")
    print(f"  Final cum: {cum:.2f}, total months with data: {len(dept_monthly[dept])}")

# Check for missing months
print("\n=== MISSING MONTHS ===")
for dept in over_budget_depts:
    missing = [m for m in months if m not in dept_monthly[dept]]
    if missing:
        print(f"{dept}: missing {missing}")
