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
   - Commonwealth gross debt on issue — AOFM
   - Tax receipts and payments as % of GDP, time series — Budget papers / ABS GFS
   - Taxes added and abolished since Federation — count, from the timeline below
2. **Federal tax timeline 1901–now** — each tax introduced or abolished: year, name,
   government, PM, party, source link. Filter by party. Running-count chart.
   Minimum 30 entries, each with a primary or secondary source URL.
3. **Votes** — recent House and Senate divisions with per-party breakdown.
   Needs a free OpenAustralia or TheyVoteForYou API key (James registers). Ships as a
   placeholder until the key arrives unless a keyless APH source is found.
4. **Sources and method page** — where every number comes from, how often it refreshes,
   known gaps.

Out of scope for MVP: states, local government, AI-generated analysis, accounts,
comments, newsletter.

## Tech (ponytail)

- Static site. Plain HTML, CSS, one JS file per page. No framework, no bundler.
- `fetch.py` (stdlib only) pulls live sources and writes `data/*.json`. Curated data
  (tax timeline) lives in `data/*.json` by hand, with sources in the records.
- Charts: inline SVG generated in the browser from the JSON. One CDN lib only if SVG
  gets painful.
- Hosting: GitHub Pages from `main`, public repo `itsjimmy1/govwatch`. URL is unlisted
  until a domain is chosen. Firebase Hosting under GCP is the firm standard; move there
  once `gcloud auth login` and `firebase login` are done. One CNAME either way.
- Refresh: GitHub Actions cron, daily, runs `fetch.py`, commits changed JSON.

## Published gate (loop stops when all true)

- [ ] Site loads at its public URL on desktop and mobile
- [ ] Every dashboard number is real, sourced, and dated on the page
- [ ] Tax timeline has ≥ 30 sourced entries and the party filter works
- [ ] Sources page lists every dataset with URL and refresh cadence
- [ ] Daily refresh workflow has run green at least once
- [ ] A separate review agent has passed the site against this gate

## James to do

- [ ] OpenAustralia API key: https://www.openaustralia.org.au/api/key — add as repo secret `OPENAUSTRALIA_KEY`
- [ ] `! gcloud auth login` and `! firebase login` if hosting should move to GCP now
- [ ] Pick a domain when ready
