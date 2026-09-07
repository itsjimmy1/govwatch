# GovWatch

Factual, sourced numbers on Australian government. What Parliament passes, what it taxes,
and how each member votes. Every figure links to the public record it came from.

Read [PLAN.md](PLAN.md) for scope and the published gate. [STATUS.md](STATUS.md) is the log.

## Run it

```sh
python3 fetch.py      # pull live data into data/*.json
python3 check.py      # refuse obviously wrong data
python3 -m http.server 8000   # then open http://localhost:8000
```

No build step, no dependencies. `fetch.py` and `check.py` are stdlib-only.

## How it fits together

| File | Does |
|---|---|
| `fetch.py` | Pulls live public data into `data/*.json`. Stdlib only. |
| `check.py` | Range and shape checks. CI runs it before deploy and fails the build. |
| `data/legislation.json` | Generated. Do not edit; `fetch.py` overwrites it. |
| `data/taxes.json` | Curated by hand. Each entry carries its own source URL. |
| `*.html`, `style.css`, `chart.js` | The site. Charts are hand-rolled SVG, no chart library. |
| `.github/workflows/pages.yml` | Daily refresh, data check, deploy to GitHub Pages. |

## Gotchas found the hard way

- The legislation.gov.au OData API **rejects any page over 100 rows**. `fetch.py` pages
  with `$skip`.
- Its OData syntax needs `(`, `)`, `,` and `$` left unescaped, so `urlencode` breaks it.
  `fetch.py` builds the query string by hand.
- python.org Python builds on macOS ship **no CA bundle**, so `urllib` fails TLS
  verification locally. `fetch.py` falls back to `/etc/ssl/cert.pem`. CI is unaffected.

## Adding to the tax timeline

Append to `data/taxes.json`. Every entry needs `year`, `name`, `action`
(`introduced` or `abolished`), `pm`, `party`, `note` and a working `source` URL.
`check.py` fails the build if any of those is missing. Notes are factual and under
about 25 words; no adjectives of approval or disapproval.
