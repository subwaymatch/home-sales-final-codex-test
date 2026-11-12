#!/usr/bin/env python3
"""Independent standard-library calculation of the report's fixed answers."""
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median

CSV = Path(__file__).resolve().parents[1] / "data/college_town_home_sales.csv"


def city(r):
    return f"{r['city']}, {r['state']}"


def valid(r):
    return 10_000 <= int(r["sale_price"]) <= 5_000_000


def groupby(rows, key):
    result = defaultdict(list)
    for row in rows:
        result[key(row)].append(row)
    return result


with CSV.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
cities = groupby(rows, city)
campuses = groupby(rows, lambda r: r["university"])

q1 = {c: median(int(r["sale_price"]) for r in rs if valid(r)) for c, rs in cities.items()}
q2 = {}
for c, rs in cities.items():
    prices = [int(r["sale_price"]) for r in rs]
    q2[c] = {"mean": mean(prices), "median": median(prices),
             "gap_pct": 100 * (mean(prices) - median(prices)) / median(prices)}

def rankings(filter_valid):
    vals = {}
    for c, rs in cities.items():
        prices = [int(r["sale_price"]) for r in rs if not filter_valid or valid(r)]
        vals[c] = mean(prices)
    return {c: rank for rank, (c, _) in enumerate(sorted(vals.items(), key=lambda x: -x[1]), 1)}

rank_all, rank_valid = rankings(False), rankings(True)
q3 = {c: (rank_all[c], rank_valid[c]) for c in cities}

q4 = {}
for campus, rs in campuses.items():
    ys = {y: median(int(r["sale_price"]) for r in rs
                    if valid(r) and r["sale_date"].startswith(str(y))) for y in (2024, 2025)}
    q4[campus] = {"2024": ys[2024], "2025": ys[2025],
                  "change_pct": 100 * (ys[2025] - ys[2024]) / ys[2024]}

q5 = {}
for campus, rs in campuses.items():
    days = [(date.fromisoformat(r["contract_date"]) - date.fromisoformat(r["list_date"])).days
            for r in rs if r["list_date"] and r["contract_date"]]
    q5[campus] = {"median_days": median(days), "rows": len(days)}

q6 = {}
for campus, rs in campuses.items():
    ratios = [100 * float(r["tax_annual_amount"]) / int(r["sale_price"])
              for r in rs if valid(r) and r["tax_annual_amount"]
              and 0 < float(r["tax_annual_amount"]) < int(r["sale_price"])]
    q6[campus] = {"median_pct": median(ratios), "rows": len(ratios)}

print(json.dumps({"rows": len(rows), "Q1": q1, "Q2": q2,
                  "Q3_ranks": q3, "Q4": q4, "Q5": q5, "Q6": q6}, indent=2))
