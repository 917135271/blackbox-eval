import json, subprocess, sys

# Search for trap-related records by looking at the tail end of the data
# We know there are records with "陷阱" in their reason
# Let's try to find them using the MCP tools

# First, let's list records with special_approval
print("Searching for trap/injection samples...")

