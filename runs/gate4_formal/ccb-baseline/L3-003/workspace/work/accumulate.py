#!/usr/bin/env python3
"""Accumulates expense records from MCP page responses."""
import json
import sys
import os

WORK_DIR = "/workspace/work"
ALL_RECORDS = os.path.join(WORK_DIR, "all_records.json")
ALL_INVOICES = os.path.join(WORK_DIR, "all_invoices.json")

def accumulate(output_file, records):
    existing = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing = []
    existing.extend(records)
    with open(output_file, 'w') as f:
        json.dump(existing, f, ensure_ascii=False)
    return len(existing)

def main():
    mode = sys.argv[1]  # records or invoices

    if mode == "records":
        output_file = ALL_RECORDS
    elif mode == "invoices":
        output_file = ALL_INVOICES
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)

    # Read JSON from stdin
    data = json.load(sys.stdin)
    records = data.get("records", [])

    if not records:
        print("No records found in input")
        sys.exit(1)

    total = accumulate(output_file, records)
    print(f"Accumulated {len(records)} records, total now: {total}")

if __name__ == "__main__":
    main()
