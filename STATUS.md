# Status

Loop log. Newest at top. One line per increment: date, what shipped, what's next.

- 2026-09-08 — Patterns and States both pass review and are live. Five review rounds on the
  two pages; every blocker was a mobile chart or table defect invisible at desktop width.
  Second gate closed. Next: an OpenAustralia key for votes, then state legislation.
- 2026-09-08 — All eight jurisdictions now sourced. SA and NT block automated requests at
  the edge regardless of user agent, so a real browser read them. Found an error of mine on
  the way: NT has a 6.5% payroll rate above $100m Australia-wide wages from 1 July 2026 that
  the page omitted. Also fixed the states page shipping its headline section as an empty box;
  check.py now fails on an unfilled chart mount. Final review running.
- 2026-09-08 — Added Patterns and States. Patterns cuts the tax timeline by party, lineage
  and decade and colours Acts per year by government, using a new sourced list of all 39
  ministries. States carries ABS tax per person for all eight jurisdictions plus rate tables
  for six; SA and NT revenue sites return 403 to automated requests. Review of both pages
  running. Next: SA and NT rates via a real browser.
- 2026-09-08 — Third review returned SHIP. All eight round-two defects verified fixed, no
  new blockers, zero console errors, keyboard access works. Cleared five non-blocking nits
  including cache-busting, which was leaving withdrawn colours in visitors' caches.
  Published gate fully closed. Next: an OpenAustralia key to unblock the votes page.
- 2026-09-08 — Second review passed all seven earlier defects but blocked on a new one:
  red "introduced" and green "abolished" pills encoded a good/bad judgement the site
  promises not to make. Pills neutralised, plus seven smaller fixes. Third review running.
- 2026-09-08 — Review found the headline tax count false. Corrected: 17 federal taxes are
  levied today, not 19. Bank Notes Tax ended 1945, War-time Profits Tax 1950, entertainments
  tax ran twice (1916-33, 1942-53), the crude oil levy was never abolished, and 1942 was the
  Commonwealth taking over income tax rather than adding one. Added the 2024 global minimum
  tax and the 2026 Division 296 tax, so the timeline reaches 2026. Next: second review pass.
- 2026-09-08 — MVP live at https://itsjimmy1.github.io/govwatch/ . Four pages, three live
  data sources, 53 sourced tax entries, CI green, daily refresh armed. Eight review defects
  fixed. Next: independent review of the live URL, then a votes API key.
- 2026-09-07 — plan written, repo created. Next: scaffold site + fetch.py + Pages deploy.
