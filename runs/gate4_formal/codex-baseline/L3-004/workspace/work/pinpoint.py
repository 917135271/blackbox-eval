import json, sys

# Budgets and pre-cross-over cumulative
# Computed from monthly summaries
dept_info = {
    "D001": {"budget": 230395.17, "cum_before": 209942.78, "cross_month": "2025-09"},
    "D002": {"budget": 107785.42, "cum_before": 91862.20, "cross_month": "2025-08"},
    "D003": {"budget": 109772.07, "cum_before": 103057.98, "cross_month": "2025-08"},
    "D004": {"budget": 264890.39, "cum_before": 258452.98, "cross_month": "2025-09"},
    "D005": {"budget": 278540.94, "cum_before": 277846.79, "cross_month": "2025-09"},
    "D006": {"budget": 340961.75, "cum_before": 333733.75, "cross_month": "2025-09"},
}

print(json.dumps(dept_info, indent=2))
