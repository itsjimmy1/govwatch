#!/usr/bin/env python3
"""Pull live public data into data/*.json. Stdlib only.

Each output file carries `fetched` (UTC date) and `source` (the URL a reader
can check). Nothing here interprets the numbers; it only moves them.
"""
import json, os, ssl, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

LEG = "https://api.prod.legislation.gov.au/v1/titles"
UA = {"User-Agent": "GovWatch/0.1 (+https://github.com/itsjimmy1/govwatch)"}
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


if __name__ == "__main__":
    sys.exit(main())
