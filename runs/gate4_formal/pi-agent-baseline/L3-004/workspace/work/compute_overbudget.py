import json

# Department budgets
budgets = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
}

# We need to load saved expense data from files
# The data was saved during API calls - let me check what files exist
import os
import glob
files = glob.glob("/workspace/work/*.json")
for f in files:
    print(f)
