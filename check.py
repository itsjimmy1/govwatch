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

    tax = json.load(open("data/taxes.json"))
    e = tax["entries"]
    want(len(e) >= 30, f"tax timeline has only {len(e)} entries, gate needs 30")
    for r in e:
        want(r["action"] in ("introduced", "abolished"), f"bad action on {r['name']}")
        want(1901 <= r["year"] <= date.today().year, f"bad year on {r['name']}: {r['year']}")
        want(r["source"].startswith("https://"), f"no source URL on {r['name']} ({r['year']})")
        want(len(r["note"]) > 10, f"missing note on {r['name']}")
        want(r["pm"] and r["party"], f"missing government on {r['name']}")
    names = {(r["name"], r["action"], r["year"]) for r in e}
    want(len(names) == len(e), "duplicate entries in the tax timeline")

    if FAIL:
        print("DATA CHECK FAILED:", file=sys.stderr)
        for f in FAIL:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"data check passed: {leg['acts_in_force']} Acts in force, {len(e)} tax entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
