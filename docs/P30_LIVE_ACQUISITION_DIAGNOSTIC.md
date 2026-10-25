# SRC-P30 Live Acquisition Diagnostic — candidate only

This **supersedes the historical 9,850-row snapshot migration as the intended P30 direction**. Source main and Preview main old JSON remain archived in Git history, but are **not imported** into fresh candidate output or treated as an up-to-date truth source.

## Stage contracts (per platform)

1. **HTTP**: HTTPS response code, content type, final URL, redirects, bounded bytes, response digest; `403/429` is blocked rather than PASS. No credentials or anti-bot bypass.
2. **List**: extract links matching the platform's allowed URL patterns, titles and exact URLs. HTTP 200 with zero candidates is `LIST_EMPTY_OR_JS_RENDERED`, not list PASS.
3. **Detail**: at most one public detail page sampled per platform in the first run. The pure `event_details.parse_detail()` module is obtained from the **frozen Source PR #2 HEAD** `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0`; its business PR is not merged.
4. **Fields**: count candidate date/location/price/description evidence independently. Do not infer ticket availability or official Golden from titles, historical snapshots, response 200, or one detail page.

## Artifacts and safeguards

- `candidate.json`: fresh, source-URL-keyed, bounded listing candidates with optional detail fields; partial coverage by design, **not** a complete live catalog or Golden.
- `diagnostics.json`: platform HTTP/list/detail/field matrix, elapsed run evidence and status.
- GitHub Actions workflow runs **once on the controlled P30 branch push**, executes offline negative cases before network, and uploads both JSON files as downloadable run artifacts. No Pages deployment or Git commits of candidate events.
- No `show_news.py`, `scraper.py`, Telegram, LINE, service, schedule, database, `docs/data.json` write or notification is invoked.
- User-specified improvement order: **HTTP reachability → valid list → detail pages → field extraction**, not maximizing total count at the cost of fidelity.
- If any platform fails, record the exact failure and continue; a successful diagnostic Action is not a claim that all sources are working.
- `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `APP_DATA_PUBLISHED=false`, `SOURCE_RUNTIME=DORMANT`. All data is candidate-only.
- Retain the existing P29 success evidence and P20 PR heads. Keep P30 historical snapshot PR #6 as unmerged; do not assume it is current production intent.

## Follow-on QA gates

- **P30-L1**: current one-shot HTTP/list/detail candidate run + evidence.
- **P30-L2**: optimize blocked/empty platform selectors one platform at a time, with frozen HTML fixtures and negative tests.
- **P30-L3**: field evidence roles, multi-session/price/identity and unknowns; official manual Golden remains independent.
- **P30-L4**: isolated PWA with current candidate JSON, check schema and Android UAT (needs release gate and explicit authorization).
- **P30-L5**: only after actual approvals, consider old JSON retirement, single-writer cloud automation and repo consolidation.

