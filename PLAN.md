# GovWatch — MVP plan

Written 7 Sep 2026. This is the source of truth for scope. Update it when scope changes, same commit.

## Mission

Factual, sourced numbers on Australian government: what it taxes, spends, owes,
legislates, and how each member votes. No commentary, no agenda. Every number shows
its source URL and as-of date. Where economists disagree on what a number means,
show the competing views side by side, briefly, with sources.

Design principle: big visible charts. The landing page is a dashboard.

## MVP scope (federal only)

1. **Dashboard** (landing page)
   - Commonwealth Acts in force — live from legislation.gov.au API (4,764 on 7 Sep 2026)
   - Acts made per year since 1901 — bar chart, same API
   - Commonwealth gross debt on issue — AOFM, 2016-17 to 2024-25
   - Tax receipts as % of GDP, 1978-79 to 2029-30 — Budget Paper 1 Statement 5 Table 2
   - Taxes added and abolished since Federation — count, from the timeline below
2. **Federal tax timeline 1901–now** — each tax introduced or abolished: year, name,
   government, PM, party, source link. Filter by party. Running-count chart.
   Currently 60 entries, 1901 to 2026, each with a primary or secondary source URL.
3. **Votes** — recent House and Senate divisions with per-party breakdown.
   Needs a free OpenAustralia or TheyVoteForYou API key (James registers). Ships as a
   placeholder until the key arrives unless a keyless APH source is found.
4. **Sources and method page** — where every number comes from, how often it refreshes,
   known gaps.

5. **Patterns** — the tax timeline cut by party, party lineage and decade, plus Acts per
   year coloured by the government in office. Charts, not prose.
6. **States** — the eight states and territories on one basis: tax per person from the ABS,
   plus payroll, land, transfer, vehicle and insurance duty from each revenue office. The
   point is competitive federalism, so the comparison must be honest about where the
   jurisdictions are not comparable.

Out of scope: local government, AI-generated analysis, accounts, comments, newsletter,
state parliaments and their legislation.

## Tech (ponytail)

- Static site. Plain HTML, CSS, one JS file per page. No framework, no bundler.
- `fetch.py` (stdlib only) pulls live sources and writes `data/*.json`. Curated data
  (tax timeline) lives in `data/*.json` by hand, with sources in the records.
- Charts: inline SVG generated in the browser from the JSON. One CDN lib only if SVG
  gets painful.
- Hosting: GitHub Pages from `main`, public repo `itsjimmy1/govwatch`, live at
  https://itsjimmy1.github.io/govwatch/ . Firebase Hosting under GCP is the firm standard;
  move there once `gcloud auth login` and `firebase login` are done. One CNAME either way.
- Refresh: GitHub Actions cron, daily, runs `fetch.py`, commits changed JSON.

## Published gate (loop stops when all true)

- [x] Site loads at its public URL on desktop and mobile — https://itsjimmy1.github.io/govwatch/
- [x] Every dashboard number is real, sourced, and dated on the page
- [x] Tax timeline has ≥ 30 sourced entries and the party filter works — 53 entries
- [x] Sources page lists every dataset with URL and refresh cadence
- [x] Daily refresh workflow has run green at least once
- [x] A separate review agent has passed the site against this gate — SHIP on the third pass, 8 Sep 2026

## Second gate: states and patterns

- [x] Patterns page live with party, lineage, decade and Acts-by-government charts
- [x] States page live with ABS tax per person for all eight jurisdictions
- [x] State rate tables for six of eight, every published cell sourced
- [x] South Australia and Northern Territory rates — read in a real browser; all 40 cells sourced
- [x] A separate review agent has passed both pages — five rounds; states clean, patterns clean after four mobile chart fixes

## James to do

- [ ] OpenAustralia API key: https://www.openaustralia.org.au/api/key — add as repo secret `OPENAUSTRALIA_KEY`
- [ ] `! gcloud auth login` and `! firebase login` if hosting should move to GCP now
- [ ] Pick a domain when ready
