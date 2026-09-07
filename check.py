#!/usr/bin/env python3
"""Refuse to ship data that is obviously wrong. Run by CI before deploy."""
import hashlib
import json
import os
import re
import sys
from datetime import date

FAIL = []


def want(ok, msg):
    if not ok:
        FAIL.append(msg)


def stamp_assets():
    """Point every page at style.css and chart.js by content hash.

    Without this, a visitor who loaded an older build keeps its CSS until their
    cache expires, which once left corrected pages showing withdrawn colours.
    """
    digest = {name: hashlib.sha256(open(name, "rb").read()).hexdigest()[:8]
              for name in ("style.css", "chart.js")}
    for page in ("index.html", "taxes.html", "patterns.html", "states.html",
                 "votes.html", "sources.html"):
        text = original = open(page).read()
        for name, h in digest.items():
            text = re.sub(rf"{re.escape(name)}(\?v=[0-9a-f]+)?", f"{name}?v={h}", text)
        if text != original:
            open(page, "w").write(text)
    print(f"stamped assets: {digest}")


def mount_points():
    """Every chart or table mount a page declares must be filled by that page's script.

    The per-capita section once shipped as an empty white box: an edit targeting an
    unstamped asset path matched nothing, the code was never written, and no error
    was raised anywhere. An empty mount is invisible until a reader sees a blank panel.
    """
    for page in ("index.html", "taxes.html", "patterns.html", "states.html",
                 "votes.html", "sources.html"):
        text = open(page).read()
        script = "".join(re.findall(r"<script[^>]*>(.*?)</script>", text, re.S))
        for mount in re.findall(r'id="([a-z0-9-]*(?:chart|table|tiles|legend|src))"', text):
            want(mount in script,
                 f"{page} declares #{mount} but its script never fills it")


def main():
    stamp_assets()
    mount_points()
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
        want(r["action"] in ("introduced", "abolished", "changed"), f"bad action on {r['name']}")
        want(1901 <= r["year"] <= date.today().year, f"bad year on {r['name']}: {r['year']}")
        want(r["source"].startswith("https://"), f"no source URL on {r['name']} ({r['year']})")
        want(len(r["note"]) > 10, f"missing note on {r['name']}")
        want(r["pm"] and r["party"], f"missing government on {r['name']}")
        want(r["kind"] in ("tax", "rate", "state", "reform"), f"bad kind on {r['name']}")
    counted = [r for r in e if r["kind"] == "tax"]
    standing = sum(1 if r["action"] == "introduced" else -1 for r in counted)
    want(0 < standing < 60, f"running tax count ends at {standing}, which cannot be right")
    want(len(counted) >= 30, f"only {len(counted)} countable tax entries")
    want(all(r["action"] != "changed" for r in counted),
         "a 'changed' entry is tagged kind 'tax', so it would move the count")
    intro = {r["name"] for r in counted if r["action"] == "introduced"}
    ended = {r["name"] for r in counted if r["action"] == "abolished"}
    for name in sorted(intro - ended):
        r = next(x for x in counted if x["name"] == name)
        want(r.get("still_levied") is True or
             (r.get("still_levied") is False and r.get("pending")),
             f"{name!r} is introduced with no abolition entry, so the site implies it is "
             f"still levied. Set still_levied true, or set it false with a pending note "
             f"saying what is unsourced, or add an abolition entry.")

    names = {(r["name"], r["action"], r["year"]) for r in e}
    want(len(names) == len(e), "duplicate entries in the tax timeline")

    fam = tax.get("party_families", {})
    want(fam.get("map") and fam.get("rule"), "party_families missing its map or its rule")
    for p in {r["party"] for r in e}:
        want(p in fam.get("map", {}), f"party {p!r} has no lineage grouping")

    if os.path.exists("data/governments.json"):
        g = json.load(open("data/governments.json"))["governments"]
        want(len(g) > 25, f"only {len(g)} governments listed since 1901")
        want(g[0]["start"].startswith("1901"), "government list does not start at Federation")
        want(sum(1 for x in g if x["end"] is None) == 1,
             "exactly one government should be current")
        for x in g:
            want(x["party"] in fam.get("map", {}),
                 f"governing party {x['party']!r} has no lineage grouping, so the "
                 f"Acts chart would colour it as Other")
        for a, b in zip(g, g[1:]):
            want(a["end"] and a["end"] <= b["start"],
                 f"governments overlap: {a['pm']} ends {a['end']}, {b['pm']} starts {b['start']}")

    pc = json.load(open("data/states_percapita.json"))
    want({x["code"] for x in pc["jurisdictions"]} ==
         {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"},
         "per-capita data is missing a jurisdiction")
    for x in pc["jurisdictions"]:
        want(1000 < x["latest"] < 20000,
             f"{x['code']} tax per person {x['latest']} is not believable")
        want(len(x["by_fy"]) >= 4, f"{x['code']} has only {len(x['by_fy'])} years")
    want(pc["benchmarks"].get("Commonwealth"), "per-capita data lost its Commonwealth row")

    if os.path.exists("data/states.json"):
        st = json.load(open("data/states.json"))
        warn = st.get("comparability_warnings", [])
        want(len(warn) >= 5,
             "states.json must carry the caveats that stop the table reading as like-for-like")
        # A caveat that describes an older version of the data is worse than none:
        # it tells the reader the numbers in front of them do not exist.
        blob = " ".join(warn).lower()
        filled = {j["code"] for j in st["jurisdictions"]
                  if all(j[f].get("source") for f in
                         ("land_tax", "transfer_duty_750k", "vehicle_duty_40k",
                          "insurance_duty"))}
        for code, word in (("SA", "only payroll tax is sourced"),
                           ("NT", "left empty rather than filled")):
            want(not (code in filled and word in blob),
                 f"a caveat still says {code} data is missing, but every {code} cell "
                 f"now has a source")
        # The failure this catches is a caveat describing the comparison itself as
        # covering six jurisdictions. "The other six" is a different, correct claim.
        n = len(st["jurisdictions"])
        for phrase in ("comparing the six", "across the six", "the six compares",
                       "for six jurisdictions", "six of the eight are"):
            want(phrase not in blob,
                 f"a caveat describes the comparison as covering six jurisdictions; "
                 f"there are {n}")
        codes = {x["code"] for x in st["jurisdictions"]}
        want(codes == {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"},
             f"expected all eight jurisdictions, got {sorted(codes)}")
        for x in st["jurisdictions"]:
            for field in ("payroll_tax", "land_tax", "transfer_duty_750k",
                          "vehicle_duty_40k", "insurance_duty"):
                blk = x.get(field)
                want(blk is not None, f"{x['code']} missing {field}")
                if blk:
                    has_value = any(v is not None for k, v in blk.items()
                                    if k not in ("source", "note", "surcharge"))
                    src = blk.get("source") or ""
                    want(src.startswith("https://") or not has_value,
                         f"{x['code']} {field} has a value with no source URL")
                    want(has_value or blk.get("note"),
                         f"{x['code']} {field} is empty with no note saying why")
                    # Every cell now has a source. An empty one is a regression, not
                    # a gap, unless its note explains an absent tax rather than a
                    # failure to read one.
                    want(src.startswith("https://"),
                         f"{x['code']} {field} lost its source URL")

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
