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
| `check.py` | Range and shape checks, plus it stamps `style.css` and `chart.js` with a content hash in every page. CI runs it before deploy and fails the build. |
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

## Four rules the build enforces

- **An introduced tax must resolve.** If a `kind: "tax"` entry is introduced with no
  matching abolition, `check.py` fails unless the entry sets `still_levied`. The site
  once claimed nineteen taxes stood when seventeen did, purely because three old taxes
  had no repeal row. Never satisfy the guard by guessing: the Crude Oil Production Levy
  looked like the same bug and turned out to still be levied.
- **Assets are cache-busted.** `check.py` rewrites every `style.css` and `chart.js`
  reference to `?v=<content hash>`. A corrected page is useless if the browser keeps the
  old stylesheet. **This rewrites the HTML on disk**, so an edit anchored on a bare
  `./chart.js` will match nothing and fail silently. Anchor on something else, or assert
  the anchor exists first.
- **Every mount gets filled.** A page that declares `id="x-chart"` must reference it in
  its own script. The states page once shipped its headline section as a blank white box
  because a silent no-op edit dropped the code and nothing errored.
- **Caveats cannot outlive the data.** The state caveats once said South Australian and
  Northern Territory figures were missing, sitting directly above those figures. The check
  fails if a caveat says data is absent for a jurisdiction whose cells all carry sources.

## Adding to the tax timeline

Append to `data/taxes.json`. Every entry needs `year`, `name`, `action`
(`introduced` or `abolished`), `pm`, `party`, `note` and a working `source` URL.
`check.py` fails the build if any of those is missing. Notes are factual and under
about 25 words; no adjectives of approval or disapproval.
