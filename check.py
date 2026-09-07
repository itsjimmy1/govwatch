#!/usr/bin/env python3
"""Refuse to ship data that is obviously wrong. Run by CI before deploy."""
import json
import sys
from datetime import date

FAIL = []


def want(ok, msg):
    if not ok:
        FAIL.append(msg)


def main():
    leg = json.load(open("data/legislation.json"))
    want(3000 < leg["acts_in_force"] < 9000,
         f"acts_in_force {leg['acts_in_force']} outside a believable range")
    want(leg["acts_total"] > leg["acts_in_force"],
         "more Acts in force than have ever been made")
    want(10000 < leg["instruments_in_force"] < 60000,
         f"instruments_in_force {leg['instruments_in_force']} outside a believable range")
    years = [r["year"] for r in leg["by_year"]]
    want(len(years) > 110, f"only {len(years)} years of Acts data")
    want(years == sorted(set(years)), "by_year has gaps out of order or duplicates")
    want(min(years) == 1901, f"Acts data starts at {min(years)}, not Federation")
    want(all(r["acts"] > 0 for r in leg["by_year"]), "a year reports zero Acts")

    debt = json.load(open("data/debt.json"))
    want(len(debt["by_fy"]) >= 5, "debt series too short")
    want(300 < debt["latest_bn"] < 3000,
         f"debt {debt['latest_bn']}b outside a believable range")
    want(all(r["face_value_bn"] > 0 for r in debt["by_fy"]), "a debt year is zero or negative")

    rec = json.load(open("data/receipts.json"))
    want(len(rec["by_fy"]) >= 40, "receipts series too short")
    want(15 < rec["latest_actual_tax_pct_gdp"] < 35,
         f"tax share {rec['latest_actual_tax_pct_gdp']}% of GDP is not believable")
    want(any(r["estimate"] for r in rec["by_fy"]), "no year flagged as a Budget estimate")
    want(all(0 < r["tax_pct_gdp"] < r["receipts_pct_gdp"] + 0.01 for r in rec["by_fy"]),
         "a year reports more tax receipts than total receipts")

    tax = json.load(open("data/taxes.json"))
    e = tax["entries"]
    want(len(e) >= 30, f"tax timeline has only {len(e)} entries, gate needs 30")
    for r in e:
        want(r["action"] in ("introduced", "abolished"), f"bad action on {r['name']}")
        want(1901 <= r["year"] <= date.today().year, f"bad year on {r['name']}: {r['year']}")
        want(r["source"].startswith("https://"), f"no source URL on {r['name']} ({r['year']})")
        want(len(r["note"]) > 10, f"missing note on {r['name']}")
        want(r["pm"] and r["party"], f"missing government on {r['name']}")
        want(r["kind"] in ("tax", "rate", "state"), f"bad kind on {r['name']}")
    counted = [r for r in e if r["kind"] == "tax"]
    standing = sum(1 if r["action"] == "introduced" else -1 for r in counted)
    want(0 < standing < 60, f"running tax count ends at {standing}, which cannot be right")
    want(len(counted) >= 30, f"only {len(counted)} countable tax entries")
    names = {(r["name"], r["action"], r["year"]) for r in e}
    want(len(names) == len(e), "duplicate entries in the tax timeline")

    if FAIL:
        print("DATA CHECK FAILED:", file=sys.stderr)
        for f in FAIL:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"data check passed: {leg['acts_in_force']} Acts in force, "
          f"{len(e)} tax entries, debt {debt['latest_bn']}b, "
          f"tax {rec['latest_actual_tax_pct_gdp']}% of GDP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
