# I'll compute cumulative from the data I already have
# Quick verification using the monthly summary

budgets = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
}

# Monthly data extracted from the API call
# D001 months: For each month, I have the total
d001_monthly = {
    "2025-01": 38344.08, "2025-02": 14045.86, "2025-03": 42626.88,
    "2025-04": 32447.08, "2025-05": 27353.69, "2025-06": 17684.88,
    "2025-07": 23252.61, "2025-08": 14187.70, "2025-09": 29410.90,
}
# D001 cumulative by end of Aug = 209942.78, budget = 230395.17, diff = 20452.39
# So in September, cum reaches 209942.78 + X where X accumulates
# Need to find which Sept record pushes past 20452.39 from remaining.

# Let me just process all the data. I'll save data files.
print("Processing...")
