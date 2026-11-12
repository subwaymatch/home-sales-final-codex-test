#!/usr/bin/env python3
"""Independently calculate report answers and default interactive views."""
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median

CSV = Path(__file__).resolve().parents[1] / "data/college_town_home_sales.csv"
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def city(r):
    return f"{r['city']}, {r['state']}"


def valid(r):
    return 10_000 <= int(r["sale_price"]) <= 5_000_000


def grouped(rows, key):
    out = defaultdict(list)
    for row in rows:
        out[key(row)].append(row)
    return out


with CSV.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
cities = grouped(rows, city)
campuses = grouped(rows, lambda r: r["university"])

# Q1: valid-price city medians.
q1 = {c: {"median": median(int(r["sale_price"]) for r in rs if valid(r)),
          "sales": sum(valid(r) for r in rs)} for c, rs in cities.items()}

# Q2: explicitly all rows, as the question requires.
q2 = {}
for c, rs in cities.items():
    prices = [int(r["sale_price"]) for r in rs]
    m, med = mean(prices), median(prices)
    q2[c] = {"mean": m, "median": med, "gap_pct": 100 * (m - med) / med}

# Q3: city rankings by means on all rows and valid prices.
def mean_ranks(only_valid):
    values = {c: mean(int(r["sale_price"]) for r in rs if not only_valid or valid(r))
              for c, rs in cities.items()}
    return {c: rank for rank, (c, _) in
            enumerate(sorted(values.items(), key=lambda item: -item[1]), 1)}


all_ranks, valid_ranks = mean_ranks(False), mean_ranks(True)
q3 = {c: {"all_rows": all_ranks[c], "valid_prices": valid_ranks[c]}
      for c in cities}

# Q4: valid-price median sale prices by campus area and sale year.
q4 = {}
for campus, rs in campuses.items():
    medians = {year: median(int(r["sale_price"]) for r in rs
                            if valid(r) and r["sale_date"].startswith(str(year)))
               for year in (2024, 2025)}
    q4[campus] = {"2024": medians[2024], "2025": medians[2025],
                  "change_pct": 100 * (medians[2025] - medians[2024]) / medians[2024]}

# Q5: valid prices and both DOM dates; a missing date is excluded, never zero.
q5 = {}
for campus, rs in campuses.items():
    days = [(date.fromisoformat(r["contract_date"]) - date.fromisoformat(r["list_date"])).days
            for r in rs if valid(r) and r["list_date"] and r["contract_date"]]
    q5[campus] = {"median_days": median(days), "rows": len(days)}

# Q6: valid prices and positive annual tax below the sale price.
q6 = {}
for campus, rs in campuses.items():
    ratios = [100 * float(r["tax_annual_amount"]) / int(r["sale_price"])
              for r in rs if valid(r) and r["tax_annual_amount"]
              and 0 < float(r["tax_annual_amount"]) < int(r["sale_price"])]
    q6[campus] = {"median_pct": median(ratios), "rows": len(ratios)}

# Q7–Q10 use the initial controls in index.html.
q7_beds = min(int(r["beds"]) for r in rows)
q7 = {}
for c, rs in cities.items():
    prices = [int(r["sale_price"]) for r in rs if valid(r) and int(r["beds"]) == q7_beds]
    if prices:
        q7[c] = {"median": median(prices), "sales": len(prices)}

q8 = {}
for c, rs in cities.items():
    days = [(date.fromisoformat(r["contract_date"]) - date.fromisoformat(r["list_date"])).days
            for r in rs if valid(r) and 10_000 <= int(r["sale_price"]) <= 5_000_000
            and r["list_date"] and r["contract_date"]]
    if days:
        q8[c] = {"median_days": median(days), "sales_used": len(days)}

q9_city = sorted(cities)[0]
q9_year = sorted({r["sale_date"][:4] for r in rows if r["sale_date"]})[0]
q9_counts = {m: 0 for m in MONTHS}
for r in rows:
    if city(r) == q9_city and r["sale_date"].startswith(q9_year):
        q9_counts[MONTHS[int(r["sale_date"][5:7]) - 1]] += 1

q10_campus, q10_budget, q10_beds = sorted(campuses)[0], 500_000, 2
q10_miles = [float(r["miles_to_campus"]) for r in campuses[q10_campus]
             if valid(r) and int(r["sale_price"]) <= q10_budget
             and int(r["beds"]) >= q10_beds]
q10 = {"campus": q10_campus, "budget": q10_budget, "minimum_beds": q10_beds,
       "median_miles": median(q10_miles) if q10_miles else None, "sales": len(q10_miles)}

print(json.dumps({"row_count": len(rows), "Q1": q1, "Q2": q2, "Q3": q3,
                  "Q4": q4, "Q5": q5, "Q6": q6,
                  "Q7": {"bedrooms": q7_beds, "cities": q7},
                  "Q8": {"price_range": [10_000, 5_000_000], "cities": q8},
                  "Q9": {"city": q9_city, "year": q9_year, "months": q9_counts},
                  "Q10": q10}, indent=2))
