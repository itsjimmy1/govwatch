#!/usr/bin/env python3
"""Pull live public data into data/*.json. Stdlib only.

Each output file carries `fetched` (UTC date) and `source` (the URL a reader
can check). Nothing here interprets the numbers; it only moves them.
"""
import csv, io, json, os, re, ssl, sys, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone

LEG = "https://api.prod.legislation.gov.au/v1/titles"
ABS_PERCAP = ("https://www.abs.gov.au/statistics/economy/government/"
              "taxation-revenue-australia/2024-25/55060DO002_202425.xlsx")
AOFM = "https://www.aofm.gov.au/sites/default/files/2025-05-29/stock_ags.csv"
BUDGET_T2 = "https://budget.gov.au/content/bp1/download/bp1_s5-online_t2.csv"
# aofm.gov.au's edge silently hangs, never responding, on any User-Agent string
# containing a URL. "GovWatch/0.1" works; "GovWatch/0.1 (+https://...)" times out.
# Keep the contact address out of this header.
UA = {"User-Agent": "GovWatch/0.1", "Accept": "*/*", "Accept-Encoding": "identity"}
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def ssl_context():
    """python.org builds on macOS ship no CA bundle; fall back to the system one."""
    ctx = ssl.create_default_context()
    if not ctx.get_ca_certs() and os.path.exists("/etc/ssl/cert.pem"):
        ctx.load_verify_locations("/etc/ssl/cert.pem")
    return ctx


CTX = ssl_context()


def get(url, params):
    # OData needs (), $ and , left alone; only spaces and quotes need escaping.
    safe = "()$,/'"
    q = "&".join(k + "=" + urllib.parse.quote(str(v), safe=safe)
                 for k, v in params.items())
    req = urllib.request.Request(f"{url}?{q}", headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        return json.load(r)


def count(odata_filter):
    """Number of titles matching an OData filter."""
    return get(LEG, {"$filter": odata_filter, "$count": "true", "$top": 0})["@odata.count"]


def acts_per_year():
    """Acts made each year since 1901, from the register's own groupby.

    The API caps a page at 100 rows, so page through with $skip.
    """
    rows, skip = {}, 0
    while True:
        d = get(LEG, {
            "$apply": "filter(collection eq 'Act')/groupby((year),aggregate($count as n))",
            "$top": 100, "$skip": skip,
        })
        page = d.get("value", [])
        if not page:
            break
        for v in page:
            if v.get("year") and 1901 <= int(v["year"]) <= int(TODAY[:4]):
                rows[int(v["year"])] = int(v["n"])
        skip += len(page)
        if len(page) < 100:
            break
    assert len(rows) > 100, f"expected a row per year since 1901, got {len(rows)}"
    return [{"year": y, "acts": rows[y]} for y in sorted(rows)]


def raw(url):
    """Fetch a URL as text. budget.gov.au serves an HTML catch-all page with a 200
    for any path that does not exist, so callers must check what came back."""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        return r.read().decode("utf-8-sig")


def rows(url, expect_header):
    text = raw(url)
    assert not text.lstrip().startswith("<"), f"{url} returned HTML, not CSV"
    r = list(csv.reader(io.StringIO(text)))
    assert expect_header in r[0][0] or any(expect_header in c for c in r[0]), \
        f"{url} header changed: {r[0][:3]}"
    return r


def debt():
    """Commonwealth Government Securities on issue, face value, by financial year."""
    r = rows(AOFM, "Face Value")
    out = [{"fy": a, "face_value_bn": float(b)} for a, b in (x[:2] for x in r[1:]) if b]
    return out


def receipts():
    """Commonwealth receipts as a share of GDP. Budget Paper 1, table 2 of statement 5.

    Rows after the last actual year are Budget estimates and are marked as such,
    because publishing a forecast as though it were history is exactly the spin
    this site exists to cut through.
    """
    r = rows(BUDGET_T2, "Total tax receipts")
    head = r[0]
    i_tax = head.index("Total tax receipts (%)")
    i_all = head.index("Total receipts (%)")
    out = []
    for row in r[1:]:
        if not row or not row[0]:
            continue
        fy = row[0].strip()
        est = "(est)" in fy
        out.append({
            "fy": fy.replace(" (est)", ""),
            "estimate": est,
            "tax_pct_gdp": float(row[i_tax]),
            "receipts_pct_gdp": float(row[i_all]),
        })
    return out


def xlsx_sheet(data, table):
    """Read one sheet of an ABS workbook with the stdlib.

    ABS data downloads are XLSX only, and these sheets are flat enough that
    zipfile plus a regex beats taking on a dependency. Sheet order does not
    reliably match table numbers, so resolve the name through the rels file.
    """
    z = zipfile.ZipFile(io.BytesIO(data))
    wb = z.read("xl/workbook.xml").decode()
    rels = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                           z.read("xl/_rels/workbook.xml.rels").decode()))
    sheets = dict((n, rels[r]) for n, r in
                  re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb))
    assert table in sheets, f"{table} not in {sorted(sheets)}"
    strings = [
        "".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))
        for si in re.findall(r"<si>(.*?)</si>",
                             z.read("xl/sharedStrings.xml").decode(), re.S)
    ]
    rows = []
    xml = z.read("xl/" + sheets[table].lstrip("/")).decode()
    for _, body in re.findall(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', xml, re.S):
        cells = {}
        # Empty cells are omitted entirely, so index by column letter, never position.
        for ref, attrs, inner in re.findall(r'<c r="([A-Z]+)\d+"([^>]*)>(.*?)</c>',
                                            body, re.S):
            v = re.search(r"<v>(.*?)</v>", inner)
            if not v:
                continue
            val = v.group(1)
            cells[ref] = strings[int(val)] if 't="s"' in attrs else val
        rows.append(cells)
    return rows


def state_tax_per_capita():
    """State and local taxation revenue per person, by jurisdiction.

    ABS 5506.0 table 4 publishes this already divided, using mean population over
    the year. Recomputing it from a point-in-time population would disagree with
    the published figure by about one per cent.
    """
    rows = xlsx_sheet(urllib.request.urlopen(
        urllib.request.Request(ABS_PERCAP, headers=UA), timeout=90, context=CTX).read(),
        "Table_4")
    header = next(r for r in rows
                  if sum(1 for v in r.values() if re.fullmatch(r"20\d\d-\d\d", str(v))) >= 3)
    years = {c: v for c, v in header.items() if re.fullmatch(r"20\d\d-\d\d", str(v))}
    cols = sorted(years)
    # The header labels one fewer column than the data carries. The unlabelled first
    # data column is the year before the earliest label.
    prev = chr(ord(cols[0]) - 1)
    y0 = int(years[cols[0]][:4]) - 1
    labels = {prev: f"{y0}-{str(y0 + 1)[2:]}", **years}

    NAMES = {"New South Wales": "NSW", "Victoria": "VIC", "Queensland": "QLD",
             "South Australia": "SA", "Western Australia": "WA", "Tasmania": "TAS",
             "Northern Territory": "NT", "Australian Capital Territory": "ACT"}
    BENCH = ("Average", "Commonwealth", "All Australia")
    out, extra = [], {}
    for r in rows:
        name = r.get("A")
        if name not in NAMES and name not in BENCH:
            continue
        series = {}
        for c, fy in labels.items():
            if c in r:
                try:
                    series[fy] = round(float(r[c]), 1)
                except ValueError:
                    pass
        if not series:
            continue
        if name in NAMES:
            out.append({"code": NAMES[name], "name": name, "by_fy": series,
                        "latest": series[labels[cols[-1]]]})
        else:
            extra[name] = series
    assert len(out) == 8, f"expected eight jurisdictions, got {len(out)}"
    return out, extra, labels[cols[-1]]


def write(name, payload):
    payload["fetched"] = TODAY
    path = f"data/{name}.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {path}")


def main():
    src = "https://api.prod.legislation.gov.au/v1/titles"
    write("legislation", {
        "source": src,
        "source_name": "Federal Register of Legislation (legislation.gov.au) OData API",
        "acts_in_force": count("collection eq 'Act' and isInForce eq true"),
        "acts_total": count("collection eq 'Act'"),
        "titles_total": count("collection eq 'Act' or collection eq 'LegislativeInstrument'"),
        "instruments_in_force": count(
            "collection eq 'LegislativeInstrument' and isInForce eq true"),
        "by_year": acts_per_year(),
    })

    d = debt()
    write("debt", {
        "source": AOFM,
        "source_name": ("Australian Office of Financial Management, AGS on issue "
                        "(face value, general government sector)"),
        "note": ("Face value of Australian Government Securities on issue at 30 June. "
                 "AOFM cites the Final Budget Outcome, Table B.5. This is gross debt; "
                 "it is not net debt and it excludes state borrowing."),
        "latest_fy": d[-1]["fy"],
        "latest_bn": d[-1]["face_value_bn"],
        "by_fy": d,
    })

    per_capita, extra, latest_fy = state_tax_per_capita()
    write("states_percapita", {
        "source": ABS_PERCAP,
        "source_name": ("Australian Bureau of Statistics, Taxation Revenue, Australia "
                        "2024-25, table 4: taxation revenue per capita"),
        "note": ("State and local government taxation per person. ABS divides by mean "
                 "population over the year. Commonwealth taxation is shown separately "
                 "and is levied on everyone regardless of where they live."),
        "latest_fy": latest_fy,
        "jurisdictions": sorted(per_capita, key=lambda x: x["latest"]),
        "benchmarks": extra,
    })

    rc = receipts()
    actual = [r for r in rc if not r["estimate"]]
    write("receipts", {
        "source": BUDGET_T2,
        "source_name": ("Australian Government Budget Paper No. 1, Statement 5, "
                        "Table 2: receipts as a share of GDP"),
        "note": ("Commonwealth receipts only. State and local taxation is not included, "
                 "so this understates the total tax take across all governments. "
                 "Years marked as estimates are Budget forecasts, not outcomes."),
        "latest_actual_fy": actual[-1]["fy"],
        "latest_actual_tax_pct_gdp": actual[-1]["tax_pct_gdp"],
        "by_fy": rc,
    })


if __name__ == "__main__":
    sys.exit(main())
