#!/usr/bin/env python3
"""Checks the column rules before any data is sampled.

Every text column in every table the sampler copies must have exactly one rule:
  identity  copied in clear; kept in the restricted area and hashed in silver
  keep      copied as it is
  empty     not copied; the column arrives empty

Run from the repository root or through `make check-rules`. Exits with 1 if anything is wrong.
"""
import csv
import re
import sys
from pathlib import Path

POC = Path(__file__).resolve().parent.parent
REPO = POC.parent
RULES = POC / "source-sample" / "column-rules.csv"
TABLES = POC / "source-sample" / "sample-tables.csv"
PROJECT = POC / "transform" / "dbt_project.yml"
ALLOWED = {"identity", "keep", "empty"}
MUST_BE_EMPTY = re.compile(r"secret|password|private_key|consumer_key|token", re.I)


def latest_inventory() -> Path:
    folders = sorted(p for p in (REPO / "explorer" / "snapshots").iterdir() if (p / "columns.csv").exists())
    if not folders:
        sys.exit("No inventory found under explorer/snapshots. Run `lake-explorer inventory` first.")
    return folders[-1] / "columns.csv"


def personal_data_fields() -> set[str]:
    """Field names listed under vars: personal_data: in dbt_project.yml."""
    fields, inside = set(), False
    for line in PROJECT.read_text().splitlines():
        if re.match(r"\s*personal_data:\s*$", line):
            inside = True
            continue
        if inside:
            found = re.match(r"\s+(\w+):\s*\{\s*treatment:", line)
            if found:
                fields.add(found.group(1))
            elif line.strip() and not line.strip().startswith("#"):
                break
    return fields


def main() -> int:
    inventory = latest_inventory()
    text_columns: dict[tuple[str, str], list[str]] = {}
    known_tables = set()
    for row in csv.DictReader(inventory.open()):
        key = (row["source"], row["table"])
        known_tables.add(key)
        if row["type"] == "string":
            text_columns.setdefault(key, []).append(row["column"])

    wanted = [(r["source"], r["table"]) for r in csv.DictReader(TABLES.open())]
    rules: dict[tuple[str, str, str], dict] = {}
    problems: list[str] = []
    for line, row in enumerate(csv.DictReader(RULES.open()), start=2):
        key = (row["source"], row["table"], row["column"])
        if key in rules:
            problems.append(f"line {line}: {'.'.join(key)} has more than one rule")
        rules[key] = row
        if row["rule"] not in ALLOWED:
            problems.append(f"line {line}: {'.'.join(key)} has rule '{row['rule']}'; use identity, keep or empty")
        if MUST_BE_EMPTY.search(row["column"]) and row["rule"] != "empty":
            problems.append(f"line {line}: {'.'.join(key)} looks like a credential and must be empty")

    fields = personal_data_fields()
    for key, row in rules.items():
        name = ".".join(key)
        if row["rule"] == "identity":
            if not row["maps_to"]:
                problems.append(f"{name} is identity but maps_to is blank")
            elif row["maps_to"] not in fields:
                problems.append(f"{name} maps to '{row['maps_to']}', which is not in the personal data list")
        elif row["maps_to"]:
            problems.append(f"{name} is '{row['rule']}' but has maps_to filled in")

    for table in wanted:
        if table not in known_tables:
            problems.append(f"{'.'.join(table)} is in sample-tables.csv but not in the inventory")
            continue
        for column in text_columns.get(table, []):
            if (*table, column) not in rules:
                problems.append(f"{'.'.join(table)}.{column} is a text column with no rule")
    for source, table, column in rules:
        if (source, table) not in wanted:
            problems.append(f"{source}.{table}.{column} has a rule but its table is not in sample-tables.csv")
        elif column not in text_columns.get((source, table), []):
            problems.append(f"{source}.{table}.{column} has a rule but is not a text column in the inventory")

    counts = {rule: sum(1 for r in rules.values() if r["rule"] == rule) for rule in sorted(ALLOWED)}
    print(f"Inventory: {inventory.relative_to(REPO)}")
    print(f"Tables: {len(wanted)}   Rules: {len(rules)}   " + "   ".join(f"{k}: {v}" for k, v in counts.items()))
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Every text column has a rule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
