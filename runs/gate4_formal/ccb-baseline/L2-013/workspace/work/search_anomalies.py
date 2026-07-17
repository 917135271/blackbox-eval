import json
import subprocess
import sys

# We can call MCP tools via the system
# Let me use a simpler approach: just search with different queries

# First, let me try to paginate the expenses with search queries
# Let's try different record IDs that might be near R004223
print("Searching for records related to R004223...")

# Records near R004223 in the ID space
near_ids = ["R004221", "R004222", "R004224", "R004225", "R004220"]
for rid in near_ids:
    print(f"Checking {rid}")

