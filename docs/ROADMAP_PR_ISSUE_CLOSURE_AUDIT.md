# 活動暨售票雷達｜正式治理 Roadmap、PR、Issue 稽核

> **2026-10-27 P30-L9-I ibon 39961 source/title drift adjudication — Native CI PASS, CURRENT MATCH REVIEW ONLY**
>
> - **Authority and frozen three Repo main:** Source `main@fc4f963247d68eed29425808cc14e7250f312d05`, Preview `main@03e515d65e827d5ed67fe341d079907a96bf784a`, ShowNews `main@85fed3e85ff5deff479a85b8d692aa9e6d2bdcad`, all untouched. [Source Draft PR #46](https://github.com/easonliu714/event_scraper_public/pull/46) branch `feat/eventradar-p30-l9i-ibon-39961-identity-audit@ca60d3182172ad7f824fbcb5a2a6c9189fecc74b`, exact base [L9-H Draft PR #45](https://github.com/easonliu714/event_scraper_public/pull/45) `56d309a9d4d895c7adfb525723c6e2a9c4abd2cb`. Exactly three add-only files: `scripts/p30_l9i_ibon_39961_identity.mjs`, `tests/p30/test_l9i_ibon_39961_identity.mjs`, `.github/workflows/eventradar_p30_l9i_ibon_39961_identity.yml`; protected main Pages/runtime Git blob and exact source scope checked by native CI. No merge, deploy, source main edits, Golden, Writer, schedule, notifier or retiring repos.
> - **Actual [Native GitHub Actions Run 40524765567](https://github.com/easonliu714/event_scraper_public/actions/runs/40524765567)**, job `122261189909`, completed/success, **30/30** mocked URL/ID/source/ambiguity/current-versus-prior-title/HTTP403/WAF/no-release tests PASS. Independently downloaded and SHA-verified exact **L9-H Run 40516301527 Artifact `12740505389`** (`39961` prior CURRENT `HOLD_TITLE_MISMATCH`, source report SHA `e8a5e392e3f80ce6504df88c2564506b32d476204c01c5de139869dfd5b7965b`) and **L9-F Run 40494326021 Artifact `12729277485`** (historical title parity PASS, source report SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`), cross-check same exact official `ActivityInfo/Details/39961` URL and event ID; no source title fabricated from ID-only L9-H report.
> - **Only TWO new normal Chromium top-level official page navigations:** `https://ticket.ibon.com.tw/Index/entertainment` HTTP200, **exact one same-card official numeric ID `39961` event-title candidate**; `https://ticket.ibon.com.tw/ActivityInfo/Details/39961` HTTP200, three bounded visible heading elements and one title matching current official listing. In this new capture **`currentSourceParity=true`**, **`historicTitleStillObserved=true`**, **`driftObserved=false`**, final bounded decision `REVIEW_ONLY_NO_RELEASE / CURRENT_LIST_DETAIL_PARITY_REVIEW_ONLY`. This is a new point-in-time source re-match, not proof that the L9-H earlier mismatch did not happen or that its underlying cause (dynamic loading, title formatting/alternation, site update) is resolved. Preserve previous `39961` mismatch HOLD journal and keep drift/stability root cause **UNEXPLAINED/REVIEW**; current observed title parity may be counted as a new source check but cannot clear identity-reliability governance on its own.
> - **[L9-I sealed Artifact 12744025880](https://github.com/easonliu714/event_scraper_public/actions/runs/40524765567/artifacts/12744025880)**, name `eventradar-p30-l9i-ibon-39961-drift-readonly`, ZIP `sha256:19a6d802733d36bedaf164db8cdcbd0cdca25422eff7f01841f44af3ad696243`, 1889 bytes, GitHub readback/unexpired. Contains `ibon_39961_identity_adjudication.json`, `manifest.json`, `SHA256SUMS.txt`; runner SHA check PASS. No full HTML, screenshot, cookies, network bodies or private tokens stored.
> - **Gate closure:** `L9I_NATIVE_CI=PASS`, `L9I_30_OFFLINE_CONTRACTS=PASS`, `L9I_TWO_PINNED_SOURCE_SHA=PASS`, `L9I_NEW_LIST_39961_TITLE=PASS_REVIEW_ONLY`, `L9I_NEW_DETAIL_39961_TITLE=PASS_REVIEW_ONLY`, `L9I_INTERMITTENT_HISTORICAL_MISMATCH=OPEN_REVIEW`, `FORMAL_EVENT_DATE_PRICE_STOCK=UNKNOWN`, `GOLDEN_WRITER_PUBLISHER_SCHEDULER_NOTIFIER_MERGE=HARD_HOLD`, `RELEASE=HARD_HOLD_NO_PUBLICATION`. No event/date/sale/admission/voucher role promoted and no multi-session split. Original Android 44 USER_ATTESTED_PASS, L8 new core UI USER_ATTESTED_PASS preserved. L9-A ten release blockers and source-wide 19-platform completeness still HOLD.
> - **Next P30-L9-J:** design bounded repeated independent normal public ibon same-ID `39961` list/detail parity checks with source-run SHA and fail-closed ambiguity / rendering-completeness signals, to measure *stability* rather than merely recapture another PASS. In parallel plan only explicit source-bound `EVENT_PERIOD` value structure of the four currently stable IDs; never globally scrape dates or auto-enable Writer/deploy. Governance remains only two canonical documents on Docs Draft PR #8, unmerged Source main.
>

> **2026-10-27 P30-L9-H two-artifact SHA-pinned ibon DOM hierarchy NATIVE CI PASS — 4/5 CURRENT TITLE, 1/5 IDENTITY DRIFT HOLD**
>
> - **Authority:** Source `main@fc4f963247d68eed29425808cc14e7250f312d05`, Preview `main@03e515d65e827d5ed67fe341d079907a96bf784a`, ShowNews `main@85fed3e85ff5deff479a85b8d692aa9e6d2bdcad` all unchanged. [Source Draft PR #45](https://github.com/easonliu714/event_scraper_public/pull/45), head `56d309a9d4d895c7adfb525723c6e2a9c4abd2cb`, exact base [Draft PR #44](https://github.com/easonliu714/event_scraper_public/pull/44) head `07cc3ce1743a56d2bc60213d345f27672cef97d5`, three ADD-only paths `scripts/p30_l9h_ibon_local_dom_hierarchy.mjs`, `tests/p30/test_l9h_ibon_local_dom_hierarchy.mjs`, `.github/workflows/eventradar_p30_l9h_ibon_local_dom.yml`. Native Source main protected `docs/data.json`, `docs/index.html`, `docs/manifest.json`, `scraper.py` exact Git blob gate PASS. No PR merge, published JSON changes, App Writer/Scheduler/Notifier, deletion, or repo decommission.
> - **Native CI successful source of truth:** [Run 40516301527](https://github.com/easonliu714/event_scraper_public/actions/runs/40516301527), Job `122230984614`, completed/success at exact PR #45 head; **36/36** fully offline positive/negative source-ID, price/date/role, local-only DOM and fail-closed browser tests PASS. Independently downloaded exact [L9-G Artifact 12738140163](https://github.com/easonliu714/event_scraper_public/actions/runs/40511115223/artifacts/12738140163) ZIP `sha256:769a138757c35711c9b55332e169966fdc0c4a4bd2ffb70166a304610fb3ba42`, decoded typed structural report file SHA `a1736d4b4c0148c9e74eccbe9b4c1f3ab05b6ee3f94c306bac210df1e08b7a42`; and exact [L9-F Artifact 12729277485](https://github.com/easonliu714/event_scraper_public/actions/runs/40494326021/artifacts/12729277485) ZIP `sha256:811e1b133c253f3cde33c31a203a9ed4bfbfab7418822a9b3a59c00fdd9cf884`, original source title report file SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`. Independently validated both SHA256SUMS/manifest then cross-bound original list title, source official URL, five ID and previously verified title-parity markers. No source titles reconstructed from L9-G ID-only artifact.
> - **Five NEW normal public ibon detail browser visits (same known IDs, not five new candidates):** `39575` HTTP200/title parity PASS, `39878` HTTP200/title parity PASS, `39907` HTTP200/title parity PASS, **`39961` HTTP200/`HOLD_TITLE_MISMATCH` CURRENT**, `39978` HTTP200/title parity PASS. Current title parity **4/5**, one current identity mismatch. Previous L9-F/L9-G *historic* 5/5 at their capture times remains historically PASS and ibon cumulatively 6/22 prior sampled title matches remains a historical fact, NOT a claim of current simultaneous parity. For `39961`, no field value inspection/acceptance can be trusted until new source/response identity adjudication. NEVER silently carry its former title PASS into current data.
> - **New DOM hierarchy findings:** five pages show one `EVENT_PERIOD` label with tag `h3`, immediate parent `div`, 0 associated images, and **no allowed direct label-next-element, parent-next-element, or same-parent-direct-text date value relation**. All five `labelCount=1`; for four currently matching titles `reviewPairs=0`, `rejections=0`, one mismatched title skips any field probes. `locallyBoundReviewPairs=0`, `rejectedOrHoldPairs=0`, `formalFieldPromotions=0`, `ticketStatus=UNKNOWN`, `goldenAccepted=0`, `published=false`. This is an explicit source-bound-structure limitation, not proof activities contain no dates; no whole-body date scavenging or role mixing, and no session splitting.
> - **[Sealed Artifact ID 12740505389](https://github.com/easonliu714/event_scraper_public/actions/runs/40516301527/artifacts/12740505389)** name `eventradar-p30-l9h-ibon-local-dom-hierarchy`, ZIP `sha256:2c4672a2b0be4f323d638455865bdf19becaed3615babdf7b6526f9b6da3c048`, 2,137 bytes, unexpired GitHub readback; contains `ibon_local_dom_hierarchy.json`, `manifest.json`, `SHA256SUMS.txt` with full runner SHA verification. Raw HTML, screenshots, cookies, private browser state and network bodies not stored.
> - **CI recovery history preserved:** initial Run `40514885666` CANCELLED due Chromium `--with-deps` install hanging (no website visits); Run `40515905716` FAILED on second Artifact token literal `Bad credentials` after **36/36 offline PASS**; workflow-only fixes switched to normal Chromium install, single CI active and corrected `github.token`; final run `40516301527` PASS. Do not mistake the failed runs for source-identity conclusions.
> - **L9-H closure:** `PARENT_L9F_L9G_SHA_AND_ID_CROSS_BIND=PASS`, `36_OFFLINE_NEGATIVES=PASS`, `NORMAL_FIVE_DETAIL_DIAGNOSTIC=PASS`, `CURRENT_TITLE_PARITY=4/5`, `IBON_39961_SOURCE_IDENTITY=HOLD`, `VALID_LOCAL_DATE_VALUE=0`, `FORMAL_PRICE_DATE_GOLDEN=HOLD`, `GOLDEN_WRITER_PUBLISHER_SCHEDULER_MERGE=HARD_HOLD`, `L8_ANDROID_FULL_E2E=HOLD_PARTIAL`, `RELEASE=HARD_HOLD_NO_PUBLICATION`. Preserve original 44 USER_ATTESTED Android PASS, L8 new core UI PASS.
> - **Next P30-L9-I recommendation:** strict current-source `39961` title/heading drift adjudication (fresh browser source detail and canonical site list card, bounded DOM diagnostics, independent SHA), and only then assess current first-party date structures; maintain four other known IDs and avoid multiplying redundant five-detail fetches. Do not promote fields, merge, deploy Pages, activate Cloud Scheduler PR #1 or retire Preview/ShowNews. The two governance docs remain **Docs Draft PR #8 only**, not main.
>

> **2026-10-27 P30-L9-H native CI recovery journal — current run queued, do not treat Gate as PASS yet**
>
> - Source Draft [PR #45](https://github.com/easonliu714/event_scraper_public/pull/45) now HEAD `56d309a9d4d895c7adfb525723c6e2a9c4abd2cb` versus L9-G frozen BASE `07cc3ce1743a56d2bc60213d345f27672cef97d5`. First native [Run 40514885666](https://github.com/easonliu714/event_scraper_public/actions/runs/40514885666) stuck at OS Chromium `--with-deps` installation and was **CANCELLED** when new workflow took over (no public site visits). Second [Run 40515905716](https://github.com/easonliu714/event_scraper_public/actions/runs/40515905716) verified exact three-file scope / browser installation / **36 of 36 offline tests PASS** and original L9-G Artifact SHA, then **FAILED** at second L9-F artifact download because workflow still had one literal `TOKEN_PLACEHOLDER`; fixed to exact `github.token` in subsequent workflow-only commit. These are CI plumbing issues, not source parser successful Gate evidence.
> - Third repaired [Run 40516301527](https://github.com/easonliu714/event_scraper_public/actions/runs/40516301527) is QUEUED at latest check. Only it (or a later exact HEAD run) may establish `L9H_NATIVE_CI=PASS`, fresh five detail browser evidence and resulting Artifact SHA; source Title+DOM dual SHA check and source role fidelity must precede any conclusion. All production Writer/Scheduler/Notifier/Publisher, Golden, merges and original Android 44 remain unchanged; release `HARD_HOLD_NO_PUBLICATION`.
>

> **2026-10-27 P30-L9-H checkpoint — implementation submitted, native CI PENDING (do not promote to PASS until completed)**
>
> - Exact frozen Source main `fc4f963247d68eed29425808cc14e7250f312d05`; [Source Draft PR #45](https://github.com/easonliu714/event_scraper_public/pull/45) head `21d935e94236ef5a0becd13a0e7fd2496d5f3362`, stacked on [L9-G Draft PR #44](https://github.com/easonliu714/event_scraper_public/pull/44) base `07cc3ce1743a56d2bc60213d345f27672cef97d5`. Exactly three additive source/test/workflow files, protected Pages and runtime SHA enforced in CI.
> - Key contract correction: L9-G reports Event ID and title-match flags but not original source titles; L9-H **must** download both exact SHA-sealed L9-F Artifact `12729277485` and L9-G Artifact `12738140163`, independently check SHA256SUMS/manifests, and cross-bind original L9-F source titles + five official IDs before any fresh DOM hierarchy inspection. No invented title reconstruction. Target official IDs `39575,39878,39907,39961,39978`.
> - CI [Run 40514885666](https://github.com/easonliu714/event_scraper_public/actions/runs/40514885666) initially in-progress at governance checkpoint; no completion or Artifact asserted here. Offline 36 positive-negative safety cases submitted, not yet CI-attested at this note. Examine `LABEL_NEXT_ELEMENT`, `LABEL_PARENT_NEXT_ELEMENT`, `SAME_PARENT_TEXT_AFTER_LABEL`, bounded image metadata, and explicit date/price role conflicts; no global page date scraping, formal field promotions, Writer/Publisher, merge, scheduler or retirement. Release remains `HARD_HOLD_NO_PUBLICATION` until independent follow-up CI readback. Prior L9-G PASS and Android UAT PASS preserved.
>

> **2026-10-27 SRC-P30-L9-G rendered ibon detail structure diagnostics — native CI PASS / actual field binding HOLD**
>
> - **GitHub source authority:** frozen Source main `fc4f963247d68eed29425808cc14e7250f312d05`, Preview main `03e515d65e827d5ed67fe341d079907a96bf784a`, ShowNews main `85fed3e85ff5deff479a85b8d692aa9e6d2bdcad`; no mutation to any main. [Draft Source PR #44](https://github.com/easonliu714/event_scraper_public/pull/44) `feat/eventradar-p30-l9g-ibon-rendered-field-structure@07cc3ce1743a56d2bc60213d345f27672cef97d5`, exact Base previous [Draft PR #43](https://github.com/easonliu714/event_scraper_public/pull/43) `d85504773108281099ec0654c5c772de243f910c`. Exactly three add-only paths: `scripts/p30_l9g_ibon_rendered_field_structure.mjs`, `tests/p30/test_l9g_ibon_rendered_field_structure.mjs`, `.github/workflows/eventradar_p30_l9g_rendered_structure.yml`; native CI frozen Source Pages/`docs/data.json`/`scraper.py` Git blob fingerprints PASS. One small revision on new L9G script adds log-only refusal reasons, **does not alter previous Gates**.
> - **Native CI official result:** [Run 40511115223](https://github.com/easonliu714/event_scraper_public/actions/runs/40511115223), Job `122212973983`, completed/success, **32/32** offline positive/negative source/title/role/price/session/binding tests PASS, sealed exact upstream [L9-F Run 40494326021 Artifact 12729277485](https://github.com/easonliu714/event_scraper_public/actions/runs/40494326021/artifacts/12729277485) SHA256 `811e1b133c253f3cde33c31a203a9ed4bfbfab7418822a9b3a59c00fdd9cf884` checked, parsed L9F source report SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`. Five **new normal public browser detail navigations** over exact prior title-parity official ibon IDs `39575,39878,39907,39961,39978`; all HTTP200 and all `DETAIL_TITLE_PARITY_PASS`.
> - **Measured actual HTML DOM structure, not invented field results:** each of 5 detail pages has **0 table/tr/th/td and 0 dl/dt/dd**, and many `strong` and `b` tags; exactly **one** detected EVENT_PERIOD label node and one same-parent `LOCAL_SIBLING` pair per page. All five refuse with **`REJECT_MISSING_DATE_TIME`**; log-only typed refusal `{role:EVENT_PERIOD, quality:REJECT_MISSING_DATE_TIME, structure:LOCAL_SIBLING}`. Hence `sourceTitleParityCount=5`, `eligibleReviewPairs=0`, `rejectedOrHoldPairs=5`, `formalFieldPromotions=0`, `goldenAccepted=0`; **the adjacent text is not a validated activity date, and zero field pairs does not mean the source has no dates/venue/price**. No generic PAGE BODY date search, no guessing sale→event conversion or adding session records.
> - **Final evidence artifact:** [Run 40511115223 Artifact 12738140163](https://github.com/easonliu714/event_scraper_public/actions/runs/40511115223/artifacts/12738140163) `eventradar-p30-l9g-ibon-rendered-structure-readonly`, ZIP `sha256:769a138757c35711c9b55332e169966fdc0c4a4bd2ffb70166a304610fb3ba42`, 2054 bytes, GitHub independently read back and unexpired. Contains `rendered_field_structure.json`, `manifest.json`, `SHA256SUMS.txt`; SHA checked by native runner, no raw HTML/cookies/network bodies persisted.
> - **Gate status:** `L9G_NATIVE_CI=PASS`, `L9G_32_OFFLINE_NEGATIVES=PASS`, `L9G_SOURCE_ARTIFACT_SHA=PASS`, `L9G_5_NEW_RENDERED_DETAILS=PASS`, `L9G_EXPLICIT_FIELD_ROLE_DIAGNOSTICS=PASS`, `L9G_DATE_BINDING=HOLD_5_REJECT_MISSING_DATE_TIME`; `GOLDEN/WRITER/PUBLISHER/SCHEDULER/NOTIFIER/MERGE=HARD_HOLD`, `RELEASE=HARD_HOLD_NO_PUBLICATION`, `19_PLATFORM_COMPLETENESS=HOLD`, `PRODUCTION_ROLLBACK=UNTESTED`. Historical user-attested 44 Android PASS, new L8 Android core UI PASS and 6/22 ibon cumulative sampled title parity are preserved; no Android retest required.
> - **Next P30-L9-H:** restrict to *public rendered details of the same five known IDs*, inspect **bounded DOM hierarchy/element relations** around the one `EVENT_PERIOD` label (e.g. nested children / separate subnodes / image-backed content) without page-global date scavenging, raw HTML or private data retention. Only if explicit same-section field association is evidenced may a role-specific review parser be proposed; no field Golden or production promotion until independent verification. Both governance files remain authoritative **only on Docs Draft PR #8**, unmerged Source main.
>

> **2026-10-27 P30-L9-F five FRESH ibon official detail identity samples — native CI PASS / field evidence HOLD / release HARD_HOLD**
>
> - **GitHub authority**: source `main@fc4f963247d68eed29425808cc14e7250f312d05` remains unmodified. [Source Draft PR #43](https://github.com/easonliu714/event_scraper_public/pull/43), `feat/eventradar-p30-l9f-ibon-detail-role-audit@d85504773108281099ec0654c5c772de243f910c`, Base L9-E [Draft PR #42](https://github.com/easonliu714/event_scraper_public/pull/42) exact `63a079c1bee7111b1ef7b04431607d9845fe3b9f`. Exactly three additive paths: `scripts/p30_l9f_ibon_detail_role_review.mjs`, `tests/p30/test_l9f_ibon_detail_role_review.mjs`, `.github/workflows/eventradar_p30_l9f_ibon_detail.yml`. GitHub CI verifies frozen `docs/data.json`, `docs/index.html`, `docs/manifest.json`, `scraper.py` blobs; zero merges or production changes.
> - **[Native GitHub Actions Run 40494326021](https://github.com/easonliu714/event_scraper_public/actions/runs/40494326021)** job `122155815270`: exact-source three-additions/SHA gate PASS, Chromium normal Playwright 1.55.0, 30/30 offline positive-negative URL/ID/source/role/price/session and false-Golden tests PASS. SHA verified exact L9-E [Run 40449476633](https://github.com/easonliu714/event_scraper_public/actions/runs/40449476633) source Artifact `12709568132`: `22` **new browser-rendered candidate IDs**, exactly 1 prior sampled detail title parity, source report SHA `d24a41262f362fc749c14c48a74dd5e85d27007d634309be6c72f30a8f1fc9ee`.
> - **Five NEW public ibon official detail browser visits, no new list crawling:** bounded unreviewed IDs `39575`, `39878`, `39907`, `39961`, `39978`, each HTTP200 and `DETAIL_TITLE_PARITY_PASS`. Therefore cumulative *sampled title parity* = previous 1 + current 5 = **6 of 22 source candidates**; remaining **16 have NO detail parity evidence**. Title parity alone does NOT validate dates, venue, sale/registration/admission/voucher roles, ticket availability, category, parent/child event or multi-session identity. No Golden classification.
> - **Strict field-label evidence result:** `additionalRoleEvidenceCount=0`, `additionalRejectedEvidenceCount=0`: the bounded rendered DOM parser only accepts explicitly adjacent `th/td`, `dt/dd`, or single-line `label: value` from the same node; **zero** accepted role pairs observed among five matched details. This is not proof fields are absent from ibon UI; it is a parser coverage limitation and must not be converted into UNKNOWN being official no-date. `formalDate=null`, `formalPrice=null`, `ticketStatus=UNKNOWN` for every sampled candidate. Explicitly reject `PRICE/資訊`, cross-role EVENT vs SALE/REGISTRATION/ADMISSION and synthetic extra session splits; no dates or price filled.
> - **[L9-F evidence Artifact 12729277485](https://github.com/easonliu714/event_scraper_public/actions/runs/40494326021/artifacts/12729277485)** `eventradar-p30-l9f-ibon-detail-roles-review-only` ZIP `sha256:811e1b133c253f3cde33c31a203a9ed4bfbfab7418822a9b3a59c00fdd9cf884`, size 1842 bytes, SHA256 sealed `detail_role_review.json` + `manifest.json` + `SHA256SUMS.txt`; artifact GitHub readback. `additionalSampleSize=5`, `additionalTitleParity=5`, `additionalRoleEvidenceCount=0`, `additionalRejectedEvidenceCount=0`, `formalFieldPromotions=0`, `sessionSplits=0`, `goldenAccepted=0`, `published=false`, `writerExecuted=schedulerExecuted=notifierExecuted=mergeExecuted=false`; release `HARD_HOLD_NO_PUBLICATION`.
> - **Gate status:** `L9F_SOURCE_PINNED_SHA=PASS`, `L9F_FIVE_DETAILS_TITLE_PARITY=PASS`, `L9F_NEGATIVES_30=PASS`, `L9F_EVIDENCE_SHA=PASS`; **HOLD** `L9F_DETAIL_FIELD_LABEL_PARSER_COVERAGE_0`, `16_OF_22_DETAIL_NOT_VERIFIED`, `L8_FULL_ANDROID_E2E_PARTIAL`, `19_PLATFORM_COMPLETENESS`, `GOLDEN_WRITER_PUBLISHER`, `PRODUCTION_ROLLBACK_UNTESTED`. The original user-attested Android 44 and isolated L8 Android core UI PASS are preserved without regression.
> - **Next P30-L9-G:** bounded ibon *rendered detail structure* investigation, inspecting public semantic label/value adjacency or HTML document text segmentation without saving raw HTML/cookies or guessing undocumented APIs. Use *source-bound*, per-element labels and role negatives; sample only known official IDs and retain REVIEW_ONLY. Do not auto-promote date/price/ticket roles or change formal `docs/data.json`; keep GitHub PRs Draft/Unmerged and Source PR #1 Cloud Scheduler HIGH_RISK_HOLD. Governance documents updated only in [Docs Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8), NOT in main.
>

> **2026-10-27 P30-L9-E normal public Chromium ibon rendering — NATIVE CI PASS, 22 NEW BOUND CANDIDATES / 1 SAMPLED DETAIL PASS; FORMAL RELEASE HARD_HOLD**
>
> - **Exact repository authority:** Source `main@fc4f963247d68eed29425808cc14e7250f312d05` unchanged; [Source Draft PR #42](https://github.com/easonliu714/event_scraper_public/pull/42) `feat/eventradar-p30-l9e-ibon-browser-render@63a079c1bee7111b1ef7b04431607d9845fe3b9f`, Base [Draft PR #41](https://github.com/easonliu714/event_scraper_public/pull/41) exact `8836dc29a6dcf4baaabed08102ffb1b7fbed6bc3`. CI-confirmed three-file ADD ONLY: `scripts/p30_l9e_ibon_browser_render.mjs`, `tests/p30/test_l9e_ibon_browser_render.mjs`, `.github/workflows/eventradar_p30_l9e_ibon_browser.yml`. Immutable `docs/data.json`, `docs/index.html`, `scraper.py`, `docs/manifest.json` Git blob checks PASS. No PR merge, Pages release, App/API/DB Writer or scheduler activation.
> - **Actual [GitHub Actions Run 40449476633](https://github.com/easonliu714/event_scraper_public/actions/runs/40449476633) completed/success**, Job `122008564226` completed/success; frozen Git scope PASS; Playwright `1.55.0` normal unmodified headless Chromium successfully installed; **30/30** offline positive/negative URL/ID/origin/DOM/field/Chrome mocked contracts PASS before new browser navigation. CI then performed **exactly 2 new official ibon public top-level browser navigations** (not L9-D archived JSON or historical 44). Browser normally loads required first-party and external resources; this is not bot stealth, CAPTCHA bypass, login, checkout or undocumented API query, and no raw HTML/cookies/network bodies archived.
> - **New source UI evidence:** `https://ticket.ibon.com.tw/Index/entertainment` HTTP200 after normal JavaScript rendering produced **67 anchors, visible text 1690 chars, 16 script elements, 22 distinct strictly canonical numeric ibon `ActivityInfo/Details/ID` candidates with same-card public titles (REVIEW ONLY)**. Browser recorded 64 resource requests on that page (54 first-party, 10 other origins; first-party responses 53 HTTP200, zero HTTP403, one other), not 64 separately checked event GETs. `https://ticket.ibon.com.tw/Home/MoreResult?inATAPID=105&inATAPWebType=entertainment` HTTP200 after rendering produced **34 anchors, visible text 509 chars, 16 scripts but 0 identity-bound event candidates**, thus remains `HOLD_HTTP200_RENDERED_NO_BOUND_EVENT_ID`; 38 resource requests (30 first-party, 8 other). Normal browser detail sampling **one** canonical ibon numeric ID produced `DETAIL_TITLE_PARITY_PASS`. Of 22 list candidates, **21 have no detail title parity proof**. The prior L9-D **HTTP-only** 0 candidate observation remains historically true and is now specifically explained by rendering dependency, not rewritten as past success.
> - **[L9-E sealed Artifact 12709568132](https://github.com/easonliu714/event_scraper_public/actions/runs/40449476633/artifacts/12709568132)**, name `eventradar-p30-l9e-ibon-chromium-readonly-evidence`, ZIP SHA256 `866c8b935d47fe391a4fdf8f69eae2a33664d67b6ef0650707a594993a2ccfef`, size 3020 B, unexpired at independent GitHub readback. Contains `ibon_browser_render_diagnostics.json`, `manifest.json`, `SHA256SUMS.txt`, SHA checked by GitHub Runner. Artifact stores safe numeric official event URLs/titles, per-list aggregate DOM/HTTP network statistics and sampled title parity; no persisted cookies, complete page HTML, source JS, request bodies or private tokens.
> - **L9-E Gate closure:** `BROWSER_RUNTIME=PASS`, `TWO_OFFICIAL_RENDERED_LISTS=PASS`, `INDEX_ENTERTAINMENT_BOUND_LIST_22=PASS_REVIEW_ONLY`, `MORE_RESULT_BOUND_LIST_0=HOLD`, `ONE_DETAIL_TITLE_PARITY=PASS`, `OTHER_21_DETAIL_IDENTITIES=HOLD`, `FULL_19_PLATFORM_COVERAGE=HOLD`, `FORMAL_DATE_PRICE_SALE_REGISTRATION_TICKET=UNKNOWN`, `L8_ANDROID_FULL_E2E=HOLD_PARTIAL`, `PRODUCTION_ROLLBACK=UNTESTED`, `RELEASE=HARD_HOLD_NO_PUBLICATION`. `goldenAccepted=0`, `formalFieldPromotions=0`, `published=false`, Writer/Scheduler/Notifier/auto-merge/delete disabled. Original 44 Android USER_ATTESTED_PASS and L8 new Android CORE_UI_USER_ATTESTED_PASS retained.
> - **Next proposed isolated P30-L9-F:** version/sha-pin these 22 **new** candidate identities; take a bounded 3–5 additional source-detail sample under the same normal public browsing contract, record event/show/entry/sale/registration/voucher date roles independently, reject title mismatches and generic PRICE/資訊, never infer live ticket status; produce independent evidence and review-only output. Do not merge PR #42, write `docs/data.json`, enable PR #1 HIGH_RISK_HOLD/Cloud Scheduler or retire Preview/ShowNews. Both governance documents remain **Docs Draft PR #8 only**, not merged to main.
>

> **2026-10-27 P30-L9-D ibon fresh public DOM / JSON-LD diagnostic native CI PASS; LIST=0 remains HOLD**
>
> - **Authoritative GitHub snapshot:** Source `main@fc4f963247d68eed29425808cc14e7250f312d05` unchanged; [new Source Draft PR #41](https://github.com/easonliu714/event_scraper_public/pull/41) `feat/eventradar-p30-l9d-ibon-public-dom-diagnostics@8836dc29a6dcf4baaabed08102ffb1b7fbed6bc3`, direct Base [L9-C Draft PR #40](https://github.com/easonliu714/event_scraper_public/pull/40) `ae469b52e7b7b7f16dda1eeab584be8e16d63f50`. Exactly THREE new paths: `scripts/p30_l9d_ibon_public_dom.py`, `tests/p30/test_l9d_ibon_dom.py`, `.github/workflows/eventradar_p30_l9d_ibon_dom.yml`; protected main Pages/runtime blobs unchanged, no rewrite of previously accepted Android 44.
> - **[Native GitHub Actions Run 40447833667](https://github.com/easonliu714/event_scraper_public/actions/runs/40447833667) completed/success**, Job `122003220447` completed/success; parent SHA/scope gate PASS, **28/28** mocked positive/negative source-ID, strict host, same-object JSON-LD Event and JSON hydration, no arbitrary JS execution, malformed JSON/oversize limits, no WAF bypass, output confinement tests PASS. Then **2 genuinely new public HTTPS GETs**, only the two previously approved ibon list URLs, at most 1 detail fetch if a numeric ID candidate exists (no candidate, so detail `NOT_ATTEMPTED_NO_SOURCE_ID`). This run has fresh origin `L9D_NEW_PUBLIC_HTTP`, not historical L7-C or L9-C JSON copy.
> - **Actual real ibon HTTP/DOM observations:** `Index/entertainment` HTTP200 and `Home/MoreResult?inATAPID=105&inATAPWebType=entertainment` HTTP200. Each returns **0 HTML anchors, 0 directly bound activity IDs, 0 JSON/DOM event candidates**, with visible text length **8** and **11 script elements** (5 first-party script src, 2 other-host script src, 4 non-JSON inline scripts). No embedded JSON-LD Event evidence, no observed fetch/axios inline hint, no WAF/captcha text signal. `malformedJsonCount=0` but no script JSON activity payload existed. **These observations are characteristics of the fresh returned HTML only; do not claim complete JS-rendered browser results, hidden APIs, cancellations or an empty event inventory.** The two pages share these counts, not independently proven identical byte content.
> - **[Sealed Artifact 12708438784](https://github.com/easonliu714/event_scraper_public/actions/runs/40447833667/artifacts/12708438784)**, `eventradar-p30-l9d-ibon-public-dom-evidence`, ZIP digest `sha256:e4ec2a8a849abbfaabd76aea7b5117cbed0bd8f04d5f86ae1f47083241c5fb9a`, 1852 B, present / unexpired at readback. `fresh_ibon_dom_diagnostics.json`, `manifest.json`, `SHA256SUMS.txt` included; runner confirms SHA matches. Only bounded public HTTP metadata, source body SHA, DOM counts and candidate provenance are persisted, **no raw HTML**, third-party JS not downloaded or executed.
> - **Gate status:** `L9D_NATIVE_CI=PASS`, `L9D_28_NEGATIVES=PASS`, `L9D_ACTUAL_2_PUBLIC_HTTPS=PASS`, `L9D_SHA_SEAL=PASS`; `IBON_LIST_IDENTITY=HOLD_0`, `IBON_DETAIL_NOT_ATTEMPTED`, `IBON_RENDERED_DOM_NOT_OBSERVED`, `FULL_19_PLATFORM_COVERAGE=HOLD`, `L8_ANDROID_FULL_E2E=HOLD_PARTIAL`, `PRODUCTION_ROLLBACK=UNTESTED`, `RELEASE=HARD_HOLD_NO_PUBLICATION`. Golden/Writer/Publisher/Scheduler/Notifier/auto merge and delete all zero, PR #1 HIGH_RISK_HOLD unchanged.
> - **Next P30-L9-E** isolated bounded *normal public browser rendering* evidence for the two official ibon entries (no account, stealth, proxy rotation, CAPTCHA bypass, login, checkout or unapproved source URL). Inspect rendered DOM and officially loaded links, record requests/status without extracting private credentials. Only if exact public link/title/ID evidence is observed, consider a separate safe adapter change; keep missing fields UNKNOWN and no publisher. Original Android 44 USER_ATTESTED_PASS and new L8 Android CORE_UI_USER_ATTESTED_PASS remain retained; no new Android testing requested. Two official governance files updated on **Draft PR #8 only**, not merged to main.
>

> **2026-10-27 P30-L9-C REAL FRESH FOUR OFFICIAL ADAPTERS Native CI PASS — partial source coverage HOLD**
>
> - **Current source authority:** Source `main@fc4f963247d68eed29425808cc14e7250f312d05` unchanged; [New Draft PR #40](https://github.com/easonliu714/event_scraper_public/pull/40) `feat/eventradar-p30-l9c-four-official-fresh-adapters@ae469b52e7b7b7f16dda1eeab584be8e16d63f50`, exact BASE [Draft PR #39](https://github.com/easonliu714/event_scraper_public/pull/39) `b1f831f985074e5011950403823bb1b4c41d16b4` (L9-B PASS). Exactly **three new files**: `scripts/p30_l9c_four_source_fresh.py`, `tests/p30/test_l9c_four_source_fresh.py`, `.github/workflows/eventradar_p30_l9c_four_fresh.yml`. Frozen formal `docs/data.json`, `docs/index.html`, `docs/manifest.json`, `scraper.py` blob identities independently native CI PASS. No merger, official app/API/DB writer, Pages publishing, notifier, scheduler, repository deletion or retirement.
> - **Actual [Native GitHub Actions Run 40443838700](https://github.com/easonliu714/event_scraper_public/actions/runs/40443838700) completed/success**, Job `121990249999` completed/success, exact frozen parent/three-file scope and **25/25** fully mocked source-ID/host/redirect/unknown-field negative tests PASS, followed by **8 actual fresh public HTTPS GETs** (NOT historical L7-B cache, not old `docs/data.json`). New source snapshots are diagnostic only: **CKSMH 1 list HTTP200 + one detail HTTP200, 5 actId-bound official link candidates, one detail title matched**; **TWTC 1 list HTTP200 + one detail HTTP200, 40 official exhibition table candidates (capped at 40), one sampled detail title matched**; **FamiTicket 1 list HTTP200 + one detail HTTP200, 40 official card candidates (capped at 40), one sampled detail title matched**; **ibon two separate official list entry HTTP200 but 0 parsed candidates, no detail attempted, remains HOLD**. Totals 4 platforms checked, 4 HTTP200 list entries counted per platform (5 list GETs), 3 nonempty platform lists, **85 bounded candidate rows**, 3 sampled detail title-bound observations, 8 total actual GETs. Each row remains unverified; no all-row detail proof.
> - **[Source evidence Artifact 12707735836](https://github.com/easonliu714/event_scraper_public/actions/runs/40443838700/artifacts/12707735836)** named `eventradar-p30-l9c-four-official-fresh-adapter-evidence` ZIP `sha256:74940280bf4df32821b39557b1b52a959ef1c2735709964efc673c889c4399da`, 10,272 bytes (not expired at readback); contents `fresh_four_source_diagnostics.json`, `manifest.json`, `SHA256SUMS.txt`; native SHA seal PASS. Includes current per-platform HTTP status, source URLs, candidate title/ID, bounded list/detail status and raw REVIEW ONLY date or venue hints. **No raw HTML archived; no field Golden/date/price/ticket promotion**; formal `goldenAccepted=0`, `formalDatePriceTicketPromotions=0`, `published=false`, `releaseState=HARD_HOLD_NO_PUBLICATION`, `fullPlatformCoverageVerified=false`.
> - **Delta vs L7-B:** generic L7-B CKSMH list=0 and TWTC list=0 are overcome by L9-C same-official-URL specialized card/table parsers, not by copied historic JSON; FamiTicket list 40 retains list-positive with one new title match; ibon two HTML shells still require separate diagnosis. LIST success is not verified dates, ticket status, series/multi-session mapping or complete coverage. Production rollback rehearsal remains unexecuted; previous L9-A ten blockers and L9-B `PRICE/資訊` rejection still valid.
> - **Next P30-L9-D:** narrowly investigate ibon official JS shell and `MoreResult` markup under authorized public page reading (no anti-bot evasion); instrument typed response/DOM diagnostics and consider source-appropriate nonbypass rendering only, plus fidelity checks for CKSMH/TWTC/Fami list-role and detail time semantics. Maintain all existing Android `44 USER_ATTESTED_PASS` and L8 new preview `CORE_UI_USER_ATTESTED_PASS`, full Android E2E still partial HOLD. No Writer/Publisher/Scheduler/cloud PR #1 activation, merging or decommissioning. Docs PR #8 still Draft/unmerged to main.
>

> **2026-10-27 P30-L9-B field quality negatives + SYNTHETIC reversible rollback native CI PASS — NO RELEASE**
>
> - **Verified GitHub authority:** frozen Source main `fc4f963247d68eed29425808cc14e7250f312d05`; [Source Draft PR #39](https://github.com/easonliu714/event_scraper_public/pull/39) `feat/eventradar-p30-l9b-field-quality-rollback-lab@b1f831f985074e5011950403823bb1b4c41d16b4`, BASE [PR #38](https://github.com/easonliu714/event_scraper_public/pull/38) exact `d35c3b78f09bcbeeb4da79ea3b6014330798ebfa` (L9A PASS). Precise 3-file ADD ONLY: `scripts/p30_l9b_field_quality_rollback.mjs`, `tests/p30/test_l9b_field_quality_rollback.mjs`, `.github/workflows/eventradar_p30_l9b_field_quality_rollback.yml`. Main formal source/Pages blobs frozen with native SHA gate; no change to three Repo main, no merge and no App/DB writes.
> - **Actual [Native GitHub Actions Run 40442853866](https://github.com/easonliu714/event_scraper_public/actions/runs/40442853866) completed/success**, Job `121987038725` successful: **30/30** positive-negative offline tests; exact 3 SHA-sealed upstream Artifacts — L7B fresh Run `40353636708`, L7C isolated Android Run `40436642012`, L9A HARD_HOLD Run `40439742917` — internal `sha256sum -c`, L7B JSON Schema Draft 2020-12, source run/identity equality, expected 19 platform/264 candidates/5 detail parity/259 pending/10 mandatory release Holds. This L9B run makes **zero new public HTTP requests**; no current official adapter claims from archived HTML (raw response HTML is not preserved).
> - **Actual field label review**: twelve source snippets assessed under **source label observed, not verified**: `VENUE_TEXT_REVIEW_ONLY=6`, `PRICE_TOKEN_REVIEW_ONLY=2`, `REJECT_GENERIC_NON_PRICE=2` (UDN / Event Go `PRICE/資訊` examples), `TIME_ROLE_TOKEN_REVIEW_ONLY=2`; formal field promotions **0**. Rejects missing numeric currency token, date-only PRICE, cross-role SALE/ADMISSION/EVENT_PERIOD confusion, forced Golden or injected source URL/role changes. Even numeric price tokens remain `REVIEW_ONLY`, not verified actual ticket prices or ticket statuses.
> - **19-source gap ledger**: CKSMH `Query.list.ctr` needs actId card binding; TWTC `exhibition?p=home` requires table and `exhibition_more.aspx?id` source identity; ibon requires constrained JS-rendered official detail identity; FamiTicket Home source list/detail binding remains HOLD; other list0/HTTP403 statuses are not evidence of cancellations. These are **adapter proposals, not completed fresh fixes**. L7B: HTTP_OK 16/19, LIST-positive 12/19, detail-title parity 5/12.
> - **Isolated rollback**: temporary copied bytes intentionally corrupted and restored; exact SHA256 parity `070a4a6eb3c0fc8a0ebccee44ed8f0016c9a31d9aa3872a2801a8497a58bf59e`, temp files cleared, `simulationOnly=true`, `productionRollbackVerified=false`, `realProductionFileOpened=false`. **Does not prove production rollback** and neither enables deployment nor counts as user permission for any Writer/Publisher.
> - **[Artifact 12707416716](https://github.com/easonliu714/event_scraper_public/actions/runs/40442853866/artifacts/12707416716)** `eventradar-p30-l9b-quality-synthetic-rollback`, actual ZIP `sha256:3906b4e9689987429040ce9508fc88e4dbb0491199fd5984e55fb469065114d0`, 6,070 B, contains `field_quality_review.json`, `platform_adapter_gaps.json`, `rollback_simulation.json`, `manifest.json`, `SHA256SUMS.txt`; independently read back from latest CI and internal SHA reported PASS.
> - **Gate closure**: `L9B_NATIVE_CI=PASS`, `L9B_30_OFFLINE_TESTS=PASS`, `L9B_3_UPSTREAM_SHA=PASS`, `L9B_REVIEW_ONLY_FIELD_REJECTION=PASS`, `L9B_SYNTHETIC_ROLLBACK=PASS`; **HOLD** `L9B_FRESH_ADAPTER_REPAIRS_NOT_PROVEN`, `L8_FULL_ANDROID_E2E_PARTIAL`, `PRODUCTION_ROLLBACK_UNTESTED`, `RELEASE_HARD_HOLD_NO_PUBLICATION`, `FULL_19_PLATFORM_COVERAGE_UNPROVEN`. Preserve original 44 Android USER_ATTESTED_PASS and L8 new preview CORE_UI_USER_ATTESTED_PASS. Next isolated **P30-L9-C**: bounded *actual fresh* CKSMH/TWTC/ibon/Fami source-specific acquisition; parse HTTP → source list → detail bound identity then typed fields, independent negative fixtures; no WAF bypass, Writer or release until separate CI/evidence Gate.
>

> **2026-10-27 P30-L9-A READ-ONLY formal release blocker matrix Native CI PASS; production still HARD_HOLD**
>
> - **Authority and scope:** Source `main@fc4f963247d68eed29425808cc14e7250f312d05` unchanged; Source new [Draft PR #38](https://github.com/easonliu714/event_scraper_public/pull/38) `feat/eventradar-p30-l9a-readonly-release-matrix@d35c3b78f09bcbeeb4da79ea3b6014330798ebfa`, BASE L7-C [Draft PR #37](https://github.com/easonliu714/event_scraper_public/pull/37) exact `4668dab1c7061e9d752da0cdfcd58a004e1459f1`. Exact THREE add-only paths: `scripts/p30_l9a_release_blockers.mjs`, `tests/p30/test_l9a_release_blockers.mjs`, `.github/workflows/eventradar_p30_l9a_release_blockers.yml`. Immutable `scraper.py`, `docs/data.json`, `docs/index.html`, `docs/manifest.json` blob gates native CI PASS. No merge, scheduler, notification, publisher, writer, delete/hide or Pages changes.
> - **Actual [GitHub Actions Run 40439742917](https://github.com/easonliu714/event_scraper_public/actions/runs/40439742917) completed/success**, Job `121976963857` completed/success: 26/26 positive-negative offline synthetic cases; independently download exact L7-B Run `40353636708` fresh HTTP artifact and exact L7-C Run `40436642012` isolated Android preview artifact, read-back both internal `SHA256SUMS.txt`, Draft 2020-12 JSON Schema and SHA-bound lineage. Input 19 platforms, 34 actual upstream GETs, HTTP_OK=16, LIST-positive=12, 264 list candidates, 12 sampled details of which five title-parity, 259 unproven preview rows; L9A itself performs **0 fresh HTTP**. Native CI emits `release_blocker_matrix.json` + `manifest.json`, SHA-sealed.
> - **[Artifact ID 12705887127](https://github.com/easonliu714/event_scraper_public/actions/runs/40439742917/artifacts/12705887127)**, `eventradar-p30-l9a-readonly-release-hold`, ZIP digest `sha256:a576ddb077342920659288392cbaf66cfcb4e24665cf5eb0a6b4e6f123c54aa3`, archive length 2766 B, GitHub independently read-back and unexpired. Output `releaseState=HARD_HOLD_NO_PUBLICATION`, `blockerCount=10`, `readyToDeploy=false`, `readyToMerge=false`, `readyToEnableWriter=false`, `readyToStartScheduler=false`, `readyToRetireRepos=false`. **CI success is proof of correct release DENIAL, not deployment approval.**
> - **Ten explicit blockers:** (1) no user release approval; (2) L8 Android full E2E partial (the user approved progress only); (3) 7/19 no parsed list; (4) 7/12 sampled detail title mismatch, 259 preview records unproven; (5) formal date/price/sales/registration/ticket/categorization review only; (6) non-numeric `PRICE/資訊` false-positive candidate snippets, must not promote; (7) source identity/duplicate/parent-child/show-session verification; (8) rollback rehearsals and independent restore SHA; (9) Golden/Writer/Scheduler/Notifier security and Source PR #1 HIGH_RISK_HOLD; (10) Preview/ShowNews retirement not signed off. `GOLDEN_ACCEPTED=0`, `APP_DATA_PUBLISHED=false`, original 44 Android USER_ATTESTED_PASS unchanged.
> - **Next executable work:** P30-L9-B isolated field-quality/official-detail parity negatives and release/rollback simulation only; specifically reject `PRICE/資訊`, audit source-first CKSMH/TWTC/ibon/Fami JS/table selectors and per-platform HOLD. NO permission to merge PR #38, publish data or retire existing repos. Docs-only updates are on [Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8), not merged to `main`.
>

> **2026-10-27 P30-L8/G5K Android real-device SCOPE-LIMITED UAT — CORE_UI_PASS; FULL_E2E_HOLD**
>
> - **User-provided native Android evidence** (same-device Chrome + Termux localhost `127.0.0.1:8766/index.html`): artifact ZIP `sha256:a524f40fd46cff6ad60046c314e70eaa44499fcddab035956ae16d25cadde3b6` PASS, internal `index.html` / `preview-data.json` / `README.txt` each `sha256sum -c SHA256SUMS.txt` OK. This matches [L7-C sealed Artifact 12704885384](https://github.com/easonliu714/event_scraper_public/actions/runs/40436642012/artifacts/12704885384), CI [40436642012](https://github.com/easonliu714/event_scraper_public/actions/runs/40436642012) completed/success. Screenshots show mobile page, quality-tier default 5, totals `264/5/259`, Event Go platform filter displaying exactly 1, responsive cards, safe scrollable modal, detailed labels for Event Go, UDN, iNDIEVOX and 華山1914, and `UNKNOWN/未核實/非 Golden` kept. This is **USER_ATTESTED_ANDROID_CORE_UI_PASS** (no requirement to revalidate historical accepted 44).
> - **Not independently attested on screenshots:** actual typed-keyword search, all 5 candidate modals individually, external HTTPS links' *navigation outcomes*, full 259 review-only UI and browser back navigation. Therefore `L8_G5K_FULL_E2E=HOLD_PARTIAL_EVIDENCE`, `L8_ANDROID_SCOPE_PASS=CORE_UI_ONLY`. The user explicitly authorized progression, NOT production promotion or GitHub merge. No contradictory inference from CI alone.
> - **Quality observation (non-blocking for isolated preview; blocking for formal field promotion):** UDN/Event Go `PRICE` evidence includes generic `資訊` rather than parseable amount; reject promotion to price/Golden and add meaningful-price/field-role negative tests in subsequent source quality Gate. Other observed snippets (e.g., individual EVENT_PERIOD vs SALE_PERIOD in iNDIEVOX) remain review-only until independently verified. `DATE/PRICE/TICKET/REGISTRATION/SALE/GOLDEN` remain NULL/UNKNOWN, no Writer/Publisher/auto-hide, no changes to published JSON or Pages.
> - **Roadmap:** Continue isolated `P30-L9-A` read-only release-readiness blocker matrix and reversible deployment/rollback design with **hard HOLD** on unverified formal fields, 7 unverified detail title-parity, 19-platform incomplete coverage, partial L8 E2E, and no merge/publish approval. Do not enable production Writer, Scheduler, PR #1 or retire Preview/ShowNews repos. `P30-L9-B` can only be considered after every blocking criterion has evidence. Existing Source main `fc4f963247d68eed29425808cc14e7250f312d05`, [L7-C Draft PR #37](https://github.com/easonliu714/event_scraper_public/pull/37) `4668dab1c7061e9d752da0cdfcd58a004e1459f1`, governance [Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8) remain unmerged.
>

> **2026-10-27 SRC-P30-L7-C isolated fresh mobile preview native CI PASS — NEXT P30-L8/G5K Android real-device UAT**
>
> - **Source authority independently read back**: Source main `fc4f963247d68eed29425808cc14e7250f312d05` unchanged; [Source Draft PR #37](https://github.com/easonliu714/event_scraper_public/pull/37) Open/Draft/Unmerged, HEAD `4668dab1c7061e9d752da0cdfcd58a004e1459f1`, BASE L7-B [PR #36](https://github.com/easonliu714/event_scraper_public/pull/36) exact `e680456f0033e528fb25da61a4b3b6e35aa22447`. Original already accepted Android 44=CKSMH5+TWTC39 remains historical USER_ATTESTED_PASS, not retested. New PR #37 contains only four additions (three existing source/test files + user-uploaded `.github/workflows/eventradar_p30_l7c_preview.yml`), no production main files or GitHub Pages changes; docs PR #8 remains Draft.
> - **Prior HOLD resolved**: L7-C workflow was missing at PR #37 `1f76f00173d3ec96d88f9b11f65bd995e020bd45`, direct GitHub workflow-creation request had been blocked; user explicitly uploaded workflow through the branch web UI. HEAD advanced to `4668dab1c7061e9d752da0cdfcd58a004e1459f1` and the named dedicated push-only CI ran. Preserve historical WIP/HOLD entry below as true at the earlier HEAD, but it is **superseded by this CI result**. Do NOT say PR merged or publish production.
> - **[Native GitHub Actions Run 40436642012](https://github.com/easonliu714/event_scraper_public/actions/runs/40436642012)**: completed/success, Job `121966765821` completed/success; exact frozen Pages/source blobs and only four added paths; 18/18 offline positive/negative tests; inline mobile JS syntax check; downloads exact L7-B real-new-HTTP Artifact from Run `40353636708` (not L7-A 12 historical), verifies upstream SHA256SUMS and Draft2020-12 JSON Schema; parent metrics `actualFreshHTTPRequests=34`, 19 platform entries, HTTP200=16, list-positive=12, list-candidates=264, detail HTTP200=12/12, title identity parity=5/12, label snippets=12 REVIEW_REQUIRED. This CI performs **zero** new public site HTTP requests; transforms the immutable fresh upstream evidence and preserves the provenance.
> - **[Sealed mobile preview Artifact 12704885384](https://github.com/easonliu714/event_scraper_public/actions/runs/40436642012/artifacts/12704885384)**, name `eventradar-p30-l7c-isolated-android-preview`, size `27705` bytes, ZIP `sha256:a524f40fd46cff6ad60046c314e70eaa44499fcddab035956ae16d25cadde3b6`, uploaded and current (not expired at read-back). Its internal `index.html`, `preview-data.json`, `README.txt`, `SHA256SUMS.txt` are checked by the job. `264` new list **candidates**, of which `5` have **DETAIL_TITLE_PARITY_PASS** and remaining `259` are list-only/detail-HOLD (NOT 259 proved false events). Detailed title parity is NOT formal activity-date, event identity beyond list/detail, price, ticket-state, category, full-platform or Golden approval.
> - **L7-C terminal Gate:** `L7C_CODE_SCOPE=PASS`, `L7C_18_TESTS=PASS`, `L7C_NATIVE_CI=PASS`, `L7C_PARENT_2020_12_SCHEMA_SHA=PASS`, `L7C_ISOLATED_ANDROID_PREVIEW_ARTIFACT_SHA=PASS`, `L7C_REAL_DEVICE_UAT=NOT_RUN`; `GOLDEN_ACCEPTED=0`, `APP_DATA_PUBLISHED=false`, Writer/Scheduler/Notifier/Merge/Hide/Delete=zero/DORMANT. **NEXT: P30-L8 G5K Android SAME-DEVICE LOOPBACK smoke of only new isolated bundle**, verify 5 visible default, 264 total, 259 pending, search/filter/modal/close, verified-vs-unknown evidence/date roles, external official URLs, no text overlap, and offline browser JS. Do not regress or retest previous 44 historic Android PASS; no deployment/repo retirement or PR merge authorization.
>

> **2026-10-26 L7-C isolated preview WIP/HOLD — safety-gated CI publication**
>
> - Source [Draft PR #37](https://github.com/easonliu714/event_scraper_public/pull/37), `feat/eventradar-p30-l7c-isolated-preview@1f76f00173d3ec96d88f9b11f65bd995e020bd45`, direct base L7-B successful [Draft PR #36](https://github.com/easonliu714/event_scraper_public/pull/36) `e680456f0033e528fb25da61a4b3b6e35aa22447`. Exactly **three** new files currently committed: `scripts/p30_l7c_isolated_preview.mjs`, `scripts/p30_l7c_isolated_index.html`, `tests/p30/test_l7c_isolated_preview.mjs`. Proposed separate read-only native CI workflow write was **blocked by platform safety enforcement**; must not bypass or report success. **L7-C CI = HOLD, L7-C Artifact = NONE, Android new-candidate UAT = NOT_READY.** No production writer, no merge or deployment.
> - Implementation candidate converts only immutable L7B *fresh* Artifact Run `40353636708` data to an isolated responsive mobile review UI with three quality tiers (5 detail-title parity, remaining 259 need review). It displays all formal dates, ticket status, price and sale/registration as unknown; provides original links and review-only labeled evidence; StrollTimes remains a third-party article. Until an authorized CI packaging route independently validates SHA and can publish the isolated Artifact, no device-testing request. Original 44 Android USER_ATTESTED_PASS untouched.
> - **Next executable Gate**: L7-C native CI or equivalent authorized provenance+SHA packaging publication review; exact parent Artifact id `12665097220` digest `8ad3a6c8d0b3259ef9187830a33455365a8ff4c7bc30061653345d74cef758c6`, validate three-file WIP source, add/verify safe workflow through approved path, produce isolated `index.html + preview-data.json + README.txt + SHA256SUMS.txt`. Then L8 G5K new-candidate Android loopback UAT, without retesting historical 44. Source main still frozen; PRs #35/#36/#37 and Docs #8 remain Draft/Unmerged.
>

> **2026-10-26 P30-L7-B FINAL latest fresh portal-correction CI read-back — PASS MINIMUM CHAIN / HOLD FULL COVERAGE**
>
> - **Newest Source functional authority:** [Draft PR #36](https://github.com/easonliu714/event_scraper_public/pull/36) `feat/eventradar-p30-l7b-fresh-acquisition@e680456f0033e528fb25da61a4b3b6e35aa22447`, direct base [Draft PR #35](https://github.com/easonliu714/event_scraper_public/pull/35) `17d189c5615cdd58db3ea0e7e1ea9472a5ab1cc8`. Exactly four added files, no main/production/Android changes. This entry **supersedes the pending CI note below**.
> - **[Final native GitHub CI Run 40353636708](https://github.com/easonliu714/event_scraper_public/actions/runs/40353636708) completed/success**, 34/34 offline positive/negative, 2020-12 JSON schema, immutable Android/main blobs, strict four-file scope, SHA sealed outputs. **34 actual new HTTPS GETs**, 19 sources checked, **16/19 HTTP_OK**, **12/19 LIST-positive**, **264 list candidates**, **12/12 sampled detail HTTP_OK**, **5/12 detail-title identity pass** (7/12 HOLD), **12 role label evidence snippets REVIEW_REQUIRED**. Source candidate event count=264, NOT number of independently validated events.
> - **[Artifact 12665097220](https://github.com/easonliu714/event_scraper_public/actions/runs/40353636708/artifacts/12665097220)** name `eventradar-p30-l7b-fresh-http-list-detail`, actual ZIP digest `sha256:8ad3a6c8d0b3259ef9187830a33455365a8ff4c7bc30061653345d74cef758c6`. Contents: `fresh_candidate.json`, `platform_diagnostics.json`, `manifest.json`, `SHA256SUMS.txt`. Independent GitHub Run/Job/Artifact digest read-back success.
> - **Delta from first fresh run:** FamiTicket official `/Home` list 0→40, CKSMH official `Query.list.ctr` HTTP 404→200 but list remains 0 with current generic parser; TWTC official `/exhibition?p=home` HTTP200/list0 remains 0 because table needs bounded platform-specific parser; ibon official `/Index/entertainment` HTTP200/list0 remains 0 (JS shell/selector under review). KKTIX, 拓元, BeClass 403: no anti-bot bypass and no inferred cancellation. **L7-B PASS means at least one complete fresh HTTP/List/Detail identity chain, not full platform coverage or correctness of all 264 candidates.** L7-C must display all rows as review candidates with strict tier labels and official links, no silent promotion. L8 G5K Android new-candidate UAT only after isolated preview.
> - **HOLD** 7 unproven detail titles, all formal dates/prices/sale or registration times/ticket status/official category, 19-platform completeness, cross-platform dedup, live Writer, Golden, production JSON/PWA, Scheduler, notifier, merging and repo retirement. Existing Android 44 PASS remains unchanged. PR #36 Draft/Unmerged and Docs PR #8 Draft/Unmerged.
>

> **2026-10-26 SRC-P30-L7-B bounded actual FRESH HTTP/list/detail Gate — Native initial PASS, four official-entry repairs under final CI read-back**
>
> - **Authority**: frozen Source main `fc4f963247d68eed29425808cc14e7250f312d05`; Preview main `03e515d65e827d5ed67fe341d079907a96bf784a`; ShowNews main `85fed3e85ff5deff479a85b8d692aa9e6d2bdcad`. Accepted Android 44 source events = 5 CKSMH+39 TWTC, USER_ATTESTED_PASS unchanged. Historical L7-A Source PR #35 `17d189c5615cdd58db3ea0e7e1ea9472a5ab1cc8`, direct Run `40333136396` completed/success, Artifact `12655660899` SHA256 `35eb9d9f604b24ce639ef7693c8aaf60758dc4b252487f0f6138bc846100c1e4` retained.
> - **New Source Draft PR #36** <https://github.com/easonliu714/event_scraper_public/pull/36>, base PR #35 branch, not main, Open/Draft/Unmerged. EXACT FOUR additive files: `scripts/p30_l7b_fresh_acquisition.py`, `tests/p30/test_l7b_fresh_acquisition.py`, `schemas/p30_l7b_fresh_candidates.schema.json`, `.github/workflows/eventradar_p30_l7b_fresh.yml`. Live one-shot 19 public HTTPS entries, one list GET per platform plus at most one bounded detail sample, no retries/bypass, same-site redirects only, per-stage false-positive protection, strict field roles with review-only label snippets, zero production writes/cron/notifications. `docs/data.json`, `docs/index.html`, `scraper.py`, `docs/manifest.json` frozen blobs unchanged.
> - **First actual native CI** <https://github.com/easonliu714/event_scraper_public/actions/runs/40353068648> completed/success HEAD `5e132dbc881b75aae124833110969084940c2b6d`, 34/34 offline negative tests, schema 2020-12, SHA manifest, actual new HTTP GET **33**, HTTP 15/19 PASS, LIST nonzero 11/19, **223 isolated list candidates**, 11/11 sampled detail HTTP 200, **5 identity-title parity PASS**, 12 role-labeled field evidence snippets REVIEW_REQUIRED. Artifact <https://github.com/easonliu714/event_scraper_public/actions/runs/40353068648/artifacts/12665121626> digest `sha256:280ecd745e87919e6f711bbe4251d185c63c46021b1557d93f2ae4a4ac36de6c`. These 223 are **not** Golden, 5 parity PASS do not verify 223 real event dates/fields, and 12 label observations are not formal field promotion.
> - **HTTP/list follow-up**: first-run 403 KKTIX/拓元/BeClass; 404 CKSMH historical landing; 200-but-empty FamiTicket/ibon/TWTC; title parity HOLD for six other sampled detail records. Precisely restore four separately audited official entrypoints: FamiTicket `/Home` (L3BA), ibon `/Index/entertainment` (L3BB), TWTC `/exhibition?p=home` (L3A), CKSMH `/mocweb/reg/CKSMH/Query.list.ctr` (L4B). This is a fresh URL correction, not importing historical event JSON; final follow-up HEAD at this entry `e680456f0033e528fb25da61a4b3b6e35aa22447` has native workflow pending, **not yet claimed PASS**. All 403/404/JS/list0 continue per-platform HOLD, not cancellation/expiry/delete.
> - **Controlled state**: `candidateOrigin=L7B_ACTUAL_NEW_PUBLIC_HTTP` only for real CI GET, synthetic unit runs explicitly `L7B_SYNTHETIC_TEST_INJECTION_NOT_FRESH` and `actualFreshHTTPRequests=0`. Output `fresh_candidate.json`, `platform_diagnostics.json`, `manifest.json` and `SHA256SUMS.txt` in Actions Artifact only. `GOLDEN_ACCEPTED=0`, `APP_DATA_PUBLISHED=false`, `SOURCE_RUNTIME=DORMANT`, Writer/Scheduler/Notifier, dedup/auto-hide/delete = zero. Official event dates, registration, sale, admission and voucher validity remain **separate REVIEW_REQUIRED evidence**, formal date/price/ticketStatus NULL/UNKNOWN. **No Android retest requested until L7-C isolated preview and L8 G5K**, preserve historical 44 Android PASS. Next L7-C schema candidate consolidation, conservative 19-platform coverage HOLD accounting + isolated PWA preview; L8 Android/PWA UAT; L9/10 still locked.
>


> **2026-10-26 SRC-P30-L7-A schema-validated twelve pinned sample JSON Gate Run 40333136396（最新）**
>
> - **GitHub Authoritative Baseline**：Source `main@fc4f963247d68eed29425808cc14e7250f312d05`，上游 [Draft PR #34](https://github.com/easonliu714/event_scraper_public/pull/34) `c42ee0f4125bf94c0c948a08e60cce677887e324`，其原生 [CI 40331119770](https://github.com/easonliu714/event_scraper_public/actions/runs/40331119770) completed/success（34/34、6 StrollTimes aggregator article IDs＋4 FamiTicket official ticket IDs＋2 ibon ticket IDs＝12、66 pairs/44 cross-platform、兩條第一手 reference 但無 confirmed cross-platform duplicates、NieR 2 show sessions 屬同一 ticket event）。Source main 三正式 Blob `docs/data.json`、`docs/index.html`、`scraper.py` SHA frozen；歷史 Android **44=5 CKSMH+39 TWTC USER_ATTESTED_PASS** 保留，不需要重測。
> - **新增 [Source Draft PR #35](https://github.com/easonliu714/event_scraper_public/pull/35)** `feat/eventradar-p30-l7a-isolated-snapshot@17d189c5615cdd58db3ea0e7e1ea9472a5ab1cc8`，base exact PR #34 HEAD，唯一四新增檔 `scripts/p30_l7a_isolated_candidate_json.mjs`、`schemas/p30_l7a_isolated_candidates.schema.json`（正式 Draft 2020-12 JSON Schema）、`tests/p30/test_l7a_isolated_candidate_json.mjs`、`.github/workflows/eventradar_p30_l7a_snapshot.yml`。native workflow 使用 SHA locked 原生 [L6B Run 40331119770](https://github.com/easonliu714/event_scraper_public/actions/runs/40331119770) 上游 Artifact，先 `sha256sum -c SHA256SUMS.txt`，**全程純離線**把上游 12 source-event identities → `candidate_sample.json`、66 個未核准 pair → `relationships_review.json`，並輸出 `manifest.json`，runId 為來源輸入 SHA256 決定，不會因操作次數／工作環境改變。
> - **實際 [GitHub Actions Run 40333136396](https://github.com/easonliu714/event_scraper_public/actions/runs/40333136396) completed/success**：30/30 離線正反向 tests，原 main Git Blob 與 PR #34 parent SHA/四新增檔 exact Guard，上游 L6B Artifact 含 E1/E2/FamiTicket/ibon/NieR lineage SHA，輸出文件完整性 manifest sha256，JSON Schema 2020-12 `jsonschema.Draft202012Validator`、日期角色/活動場次約束與 12/66 關係全部 PASS。固定 `run_id=P30-L7A-SNAPSHOT-e1e8b58812dc5b6d`，來源 JSON SHA256 `e1e8b58812dc5b6ddee5ae9630bd6929f96bf470bcfd04637a0a2463aba687e4`。GitHub Artifact [12655660899](https://github.com/easonliu714/event_scraper_public/actions/runs/40333136396/artifacts/12655660899) `eventradar-p30-l7a-isolated-sample-json`、ZIP digest `sha256:35eb9d9f604b24ce639ef7693c8aaf60758dc4b252487f0f6138bc846100c1e4`、expires `2026-11-09T13:44:01Z`。
> - **資料品質不可誤述**：`candidateOrigin=L7A_PINNED_HISTORICAL_EVIDENCE_NOT_FRESH`、`collectionMode=IMMUTABLE_UPSTREAM_ARTIFACT_TRANSFORM_OFFLINE`、`actualFreshHTTPRequests=0`、`evidenceAsOfUTC=null`、`fullPlatformCoverageVerified=false`、`sampledSourceOnly=true`。這不是 19 平台 fresh 全量爬取，也不是 Android/PWA 現正營運資料。碧潭 2026-10-17～12-13 **官方行事曆日期只在 `sourceDateEvidence`，正式 `dateStart/dateEnd=null`**；NieR 台北兩場 2027-02-20T18:00／02-21T14:00 **只在單一 ibon 候選的 `showSessionEvidence`，不可膨脹成新活動，也不可猜時區或追加場公告 timestamp**；RUNIDRE 第三個 ibon show 僅保留 sessionCount 不憑空補齊製作方核實的時分。來源 title keyword 只做 categoryHint，正式 `category=待分類`，所有 `price/venue/dateStart/dateEnd=null`、`ticketStatus=UNKNOWN`。舊平台尚未核實的活動不憑對話記憶產生新候選。
> - **Governance Gate**：`P30_L7A_PINNED_L6B_SHA=PASS`、`P30_L7A_ISOLATED_12_CANDIDATES=PASS`、`P30_L7A_RELATIONSHIPS_66_UNMERGED=PASS`、`P30_L7A_SCHEMA_2020_12=PASS`、`P30_L7A_FRESH_HTTP_DATA=HOLD_NOT_PERFORMED`、`P30_L7A_ANDROID_PREVIEW=HOLD_NOT_CREATED`；`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`、`PRODUCTION_WRITER/NOTIFIER/SCHEDULER=0`。PR #35 仍 Draft／未合併。
> - **下一個 P30-L7-B Fresh HTTP Gate（必要）**：不能沿用舊 `docs/data.json`、L5/L6 Artifact 或 12 筆 snapshot 假充現況；先依 L2–L5 已核實的平台/URL 及各自限制做**新的有界 HTTP 回應取樣**，以 **HTTP status → list → detail → date/venue/price/ticket role → source lineage → isolated versioned JSON** 逐級 Gate。允許部分欄位 UNKNOWN 與官方連結優先，但絕不以 HTTP200 推導「購票中」；失敗/429/403/HOLD 保留證據而不自動下架。若需要更完整候選與 Android E2E，先完成 L7-B 保守審核與 L7-C isolated PWA mock preview，才進 L8 G5K 手機實機 Gate；不重做歷史 44 UAT。正式 Publisher/Writer、PR Merge、通知、排程和三 Repo 退役仍 LOCKED；治理兩份文件**此時只更新在 [Docs Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8)**、**未 Merge 到 Source main**。
>


> **2026-10-26 P30-L6-B G5J four-pinned-artifact cross-platform event identity Gate（最新）**
>
> - **啟動時 GitHub Authority**：Source `main@fc4f963247d68eed29425808cc14e7250f312d05`、[Source Draft PR #33](https://github.com/easonliu714/event_scraper_public/pull/33) `774e2de11580ed961658d6a6254b34ae4ded57c7` 和其直接 [CI Run 40324420431](https://github.com/easonliu714/event_scraper_public/actions/runs/40324420431) completed/success（6 StrollTimes 文章身分、15 內部比對、7 provenance edges、零 merge）已完成讀回。正式 `docs/data.json`、`docs/index.html`、`scraper.py` 的 frozen main Blob、既有 Android **44=5 CKSMH+39 TWTC USER_ATTESTED_PASS** 仍 unchanged。
> - 新 [Source Draft PR #34](https://github.com/easonliu714/event_scraper_public/pull/34) `feat/eventradar-p30-l6b-cross-platform-identity@c42ee0f4125bf94c0c948a08e60cce677887e324`，base PR #33 frozen HEAD，只新增精確三檔 `scripts/p30_l6b_g5j_cross_platform_identity.mjs`、`tests/p30/test_l6b_g5j_cross_platform_identity.mjs`、`.github/workflows/eventradar_p30_l6b_g5j.yml`。GitHub Native CI **純離線**讀取四個 previously PASS/immutable SHA-sealed Artifacts：L6A **Run 40324420431** `dedup_classification_review.json`（6 StrollTimes aggregator-only），FamiTicket L5D **Run 40312137162** `role_evidence.json`（4 distinct exact-title official ticket detail），ibon L5A **Run 40301911354** `session_candidates.json`（2 個官方 ticket event URLs，3 個 show time 但不是 3 筆獨立活動），NieR original producer L5C **Run 40305582187** `cross_source_review.json`（二個 NieR 台北場次與原製作方 itinerary 相符）。各自 `sha256sum -c SHA256SUMS.txt`，只產生 isolated `cross_platform_review.json`，不碰外部網站。
> - 實測結構：**12 筆 source-event identifiers（6 StrollTimes＋4 FamiTicket＋2 ibon）**、全組合 **66 對候選（44 對 cross-platform、22 對 within-platform）**、**兩條第一手參照證據：碧潭 StrollTimes article → 新北市政府官方 event calendar；NieR ibon 活動 → AWR/SQUARE ENIX original producer 兩場巡演**。其中 `ibonShows=3` 只屬 **2 筆官方票務 event IDs**；NieR 2/20 18:00 + 2/21 14:00 為同活動不同 show sessions，不能當作兩筆不同活動，開場/售票期間也不能替代開演時間。Bitan 第一手官方展期 10/17～12/13 只保留 `referenceTimeRange`，正式 `eventDateStart/eventDateEnd=null`。其他 23 篇 StrollTimes 官方同一性尚未核實，不將 title/date/venue/year likeness 當作 verified duplication。
> - 首輪 [CI 40330918202](https://github.com/easonliu714/event_scraper_public/actions/runs/40330918202) **FAIL**，34 個 offline test 33 通過、1 失敗：synthetic fixture 漏填 Bitan 的 review-only `referenceOfficialPeriod`，已精準修補測試資料（無改動主線或任何正式欄位）。**最後正式 [Run 40331119770](https://github.com/easonliu714/event_scraper_public/actions/runs/40331119770) completed/success**：34/34 positive/negative，Source main+parent SHA/精確三新檔，four independent input manifests，12 event-source records、66 pairs（44 cross）、2 origin edges、3 source-bound ibon sampled show times、零自動合併／隱藏／刪除／欄位升級、輸出 Artifact SHA256 皆 PASS。驗證產物 [Artifact 12654907565](https://github.com/easonliu714/event_scraper_public/actions/runs/40331119770/artifacts/12654907565) 名稱 `eventradar-p30-l6b-g5j-cross-platform-identity`、ZIP SHA256 `2dd2e49145c6e250a36efc3ba6371892c611436eaf15d3061ed7d999a1eec506`、expires `2026-11-09T13:30:25Z`。
> - **Gate 定義**：`P30_L6B_FOUR_UPSTREAM_SHA_MANIFESTS=PASS`、`P30_L6B_EXACT_EVENT_IDENTITY_12_AND_PAIRS_66=PASS`、`P30_L6B_NIER_TWO_SHOWS_ONE_TICKET_EVENT=PASS`、`P30_L6B_ORIGIN_REFERENCES_2=PASS`、`P30_L6B_CROSS_PLATFORM_VERIFIED_DUPLICATE_PAIRS=0_HOLD_NOT_PROVEN`、`P30_L6B_UNVERIFIED_PARENT_CHILD_LINKS=HOLD`、`GOLDEN_ACCEPTED=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`。**66 組審核不代表 66 組全部已證實互不重複；沒有證據一律保留分開，不能自動認定無關。**
> - **下一 Gate P30-L7-A 新資料隔離 JSON**：把本輪多來源來源身分與 L5 系列已核實欄位做 versioned `run_id`／`source_url`／`source_role`／`evidenceLineage`／`dateRole`／`qualityState` 的唯讀 snapshot-to-candidate 轉換；嚴格區分官方原始活動「review-only」日期與售票／報名／兌換日期。**此 Gate 不能重新使用過時 `docs/data.json` 當 fresh input，亦不得將 12 個來源 ID 當作全平台 19 個來源完整活動數。** L7 經 isolated candidate schema 與比例抽樣驗證後才進 L8 Android/PWA 實機預覽；原 Android 44 user-attested PASS 不重跑，正式 Writer/通知/排程/Repo 整併維持 LOCKED。兩份正式治理文件僅在 [Docs Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8)，未合併 main，所有 source 功能 PR #33/#34 仍 Draft。
>


> **2026-10-26 P30-L6-A G5J six classification hints and fifteen source pairs Gate（最新 GitHub Authority）**
>
> - 啟動本 Gate 先核對 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`、Source [Draft PR #32](https://github.com/easonliu714/event_scraper_public/pull/32) `7057990d9e698302fa60e933b7579492b8969620`，其直接 [CI 40318751941](https://github.com/easonliu714/event_scraper_public/actions/runs/40318751941) completed/success（27/27、六篇 StrollTimes Article HTTP200、2 H1 match + 3 編輯副標題/1 series-subevent review、**6 list-card-to-article edges + Bitan 1 government corroboration edge，0 merge**）；原 44 Android UAT PASS（5 CKSMH+39 TWTC）及正式 `docs/data.json`、`docs/index.html`、`scraper.py` Blob/Source main SHA 全程 unchanged。
> - 新 [Source Draft PR #33](https://github.com/easonliu714/event_scraper_public/pull/33) `feat/eventradar-p30-l6a-reversible-dedup@774e2de11580ed961658d6a6254b34ae4ded57c7`，base exact PR #32 HEAD，**只新增** `scripts/p30_l6a_g5j_reversible_dedup.mjs`、`tests/p30/test_l6a_g5j_reversible_dedup.mjs`、`.github/workflows/eventradar_p30_l6a_g5j.yml`。此 Gate **純離線、不再請求任何活動網站**，GitHub CI 透過 Actions download-artifact 只下載 exact upstream L5-E3 **Run 40318751941** 的 SHA sealed graph artifact，再 `sha256sum -c` 檢查 `identity_graph_review.json`、E1 lineage、E2 Bitan government 來源歷程、E3 六 nodes/七 edges/四 review notes、官方 blob SHA/三新增檔 scope。
> - `dedup_classification_review.json` 精確產生 **6 條 StrollTimes 聚合文章分類提示**、全部 **15 組兩兩候選身分比對**、**7 條可逆來源證據關係**。Bitan 1 筆獨立新北市政府行事曆原始資料有 `referenceOfficialUrl` 與 `referenceOfficialPeriod=["2026-10-17","2026-12-13"]`，**但 `dateStart/dateEnd=null`、不算正式欄位提升**；其餘五筆未核定第一手主辦。分類提示只由標題的明確 keyword 判定，結果：新竹市萬聖節／桃園眷村文化節／香山濕地藝術季／新北濕地藝術季／晴空季 5 筆 `文化節慶` 提示；碧潭小王子 1 筆 `藝文展覽` 提示；六筆全標 `officialCategoryVerified=false`。標題、場地、日期、場次、主辦等**任何單一相似特徵都不足以認定為同一場活動**，15 對全部 `KEEP_SEPARATE_PENDING_EVIDENCE`、`mergeAllowed=false`，不能直接從相同 StrollTimes 文章 URL 判跨平台活動重複。
> - [GitHub Actions Run 40324420431](https://github.com/easonliu714/event_scraper_public/actions/runs/40324420431) **completed/success**：**30/30** 離線 G5J negative+source spoofing/官方欄位竄改與範圍 guard tests、parent SHA manifest、6 classification hints/15 pairs/7 edges、JSON/ZIP SHA Gate 全 PASS；證據 [Artifact 12651050317](https://github.com/easonliu714/event_scraper_public/actions/runs/40324420431/artifacts/12651050317) `eventradar-p30-l6a-g5j-reversible-dedup` archive digest `sha256:8ad284d56998949a4cff44f094c3dcbace17e1c96cba257824c77abc3850f06d`，expiring約 `2026-11-09`。正式管理 Gate 仍 `automaticMergeCount=0`、`automaticHideCount=0`、`deleteCount=0`、`formalFieldPromotionCount=0`、`GOLDEN_ACCEPTED=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`；**CI 成功≠15 對均已證實互不相干，也不代表聚合候選已 Golden**。
> - **下一 Gate P30-L6-B G5J**：使用各平台 first-party URL/EventID/場次／版本／日期與主辦證據逐級對照，建立跨平台獨立活動與子場次的**可審計負向矩陣及候選配對**，不得以標題相似度直接合併；候選僅審核隔離。接著 **P30-L7 fresh isolated candidate JSON（run_id、schema、source URL 和 evidence lineage）→ P30-L8 Android/PWA 新候選實機 E2E**。原 Android 44 筆 PASS 保留；PR #33 和治理 [PR #8](https://github.com/easonliu714/event_scraper_public/pull/8) 仍 Draft/未合併，正式 writer/通知/排程/多 Repo 退役一律 LOCKED。
>


> **2026-10-26 P30-L5-E3 StrollTimes reversible article-title and parent/subevent Gate final（最新治理快照）**
>
> - **啟動 Authority／Anti-Drift**：Source `main@fc4f963247d68eed29425808cc14e7250f312d05`；E1 Source [Draft PR #30](https://github.com/easonliu714/event_scraper_public/pull/30) `ae2c2bdd014fdb9df2cb7d05781d6347d92848b5`、CI `40314650154`（24 list／6 articles／2 H1 exact／3 social credits）；E2 [Draft PR #31](https://github.com/easonliu714/event_scraper_public/pull/31) `f0b07bf4ad45ed9e833d6825c4c119097c698694`、CI `40315847664`（**碧潭 1 件**新北市政府觀旅行事曆原始身份與日期 2026-10-17～12-13、獨立 10/14 市政新聞）全部原 Gate PASS 不回退。Android **44=5 CKSMH+39 TWTC USER_ATTESTED_PASS** 保留；正式 `docs/data.json`、`docs/index.html`、`scraper.py` Blob 仍凍結，無部署／Merge／舊 Repo 退役。
> - 新 [Source Draft PR #32](https://github.com/easonliu714/event_scraper_public/pull/32) `feat/eventradar-p30-l5e3-article-identity-graph@7057990d9e698302fa60e933b7579492b8969620`，堆疊 PR #31 exact frozen HEAD。僅新增三檔 `scripts/p30_l5e3_strolltimes_identity_graph.mjs`、`tests/p30/test_l5e3_strolltimes_identity_graph.mjs`、`.github/workflows/eventradar_p30_l5e3_title_graph.yml`。原生 CI 分別下載 pin **E1 Run 40314650154**＋**E2 Run 40315847664** 的兩組 artifact 並 `sha256sum -c`，只以 6 個既有 StrollTimes canonical article URLs 進行公開 stock Chromium **6 個 bounded HTML navigation**（300 限額請求），重新讀回真正 H1、不跟隨外部來源、不登入／不購票／不自動合併。
> - **六個來源 H1 真實比較（GitHub Runner）**：新竹萬聖節「2026新竹市萬聖節（10/16~10/31）」、碧潭小王子「碧潭地景裝置展 遇見小王子漫遊碧潭間（10/17~12/13）」＝既有 **2/6 aggregator H1 title identity PASS**，括號 MM/DD 是**聚合站展示日期，不能代替官方日期**。其他四篇需比對：① 首頁「2026桃園眷村文化節 龜山眷村故事館場次」 vs 文章「2026桃園眷村文化節：四大場域一村一家人！…（10/9~11/8）」→ `TITLE_OVERLAP_RELATIONSHIP_REVIEW`，含 series/venue subevent 不確定，不建正式 parent-child 關聯；② 「2026香山濕地藝術季」 vs H1 同名加「：踏走一道波痕8件作品！…（10/2~11/1）」；③ 「2026新北濕地藝術季 《萌芽之境》」 vs H1 同名加「：新海二期人工濕地20週年！…（10/3~11/8）」；④ 「2026晴空季」 vs H1 同名加「：打開七萬坪神祕軍事禁地…（8/1~11/15）」；後三筆新分類為 `EDITORIAL_HEADLINE_EXTENSION_REVIEW`，不再誤標 `DISJOINT_TITLE_IDENTITY_HOLD`，但也**不自動當作同一主辦活動**。
> - Graph 輸出 `identity_graph_review.json` 的 **6 條** `AGGREGATOR_LIST_CARD_POINTS_TO_SAME_ARTICLE` 只證明首頁卡片與同一篇聚合 URL 的索引，**不是跨活動去重**；第 **7 條** `ONE_EVENT_OFFICIAL_GOV_CALENDAR_CORROBORATED` 僅沿用 E2 的碧潭政府行事曆 FIRST PARTY review-only 來源。四個 H1 差異會產生 `notesRequiringReview[]`，`confirmedParentChildEventEdges=0`、`automaticDedupMergeCount=0`、`all23OthersOriginalSourcesVerified=false`。**E3 禁止用標題相似度直接刪除或合併活動。**
> - CI 修補／版次：初始 [Run 40318305159](https://github.com/easonliu714/event_scraper_public/actions/runs/40318305159) 25/25 PASS、六頁 real H1，但「晴空季」過短標題被保守中文重疊門檻誤列 disjoint；追加 colon/subtitle 明確角色後，中途 `40318609216` 的 27 案測試因舊的「無冒號測試樣本」預期分類不一致而 **FAIL（未通過）**；修正測試契約後，**唯一最終 Gate 是 [Run 40318751941](https://github.com/easonliu714/event_scraper_public/actions/runs/40318751941) completed/success**：**27/27** 離線 negative/parity tests、兩個 sealed E1/E2 upstream、來源 main runtime frozen SHA、3 added paths、6/6 真正文章 HTTP200、2 exact H1、4 separate review roles、7 reversible graph edges、0 forced merges/fields、ZIP SHA Gate 全部 PASS。Artifact [12647638215](https://github.com/easonliu714/event_scraper_public/actions/runs/40318751941/artifacts/12647638215) 名稱 `eventradar-p30-l5e3-strolltimes-identity-graph`，digest `sha256:a412483fe6e8ecc53e088baadec21020464ee9ab82b545c424a6d93c35df9596`，expires `2026-11-09T11:56:51Z`。
> - **Gate 分級／正式資料仍鎖**：`L5E3_E1_E2_GOV_PIN_SHA=PASS`、`L5E3_ARTICLE_REOBSERVATION_6/6=PASS`、`L5E3_GRAPH_REVERSIBILITY=PASS`、`L5E3_PARENT_CHILD_FIRST_PARTY_PROOF=HOLD`、`L5E3_ORIGINAL_OFFICIAL_IDENTITY_FOR_OTHER_23=HOLD`；`GOLDEN_ACCEPTED=0`、`FORMAL_DATE_PROMOTION=0`、`APP_DATA_PUBLISHED=false`、`AUTO_HIDDEN=0`、`SOURCE_RUNTIME=DORMANT`。兩份治理文件的更新仍僅在 [治理 Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8)，**尚未 Merge 到 main**。
> - **下一個可直接開發 Gate：P30-L6-A（G5J）保守可逆去重／分類模型**。輸入應沿用 E1/E2/E3 pin SHA 的**隔離**候選與 7 個 evidence edges，對 `same-article-URL`、`first-party-calendar-reference`、`maybe-parent/subevent`、`edition/venue/session` 分開打分，但 **0 auto delete/merge**，未有第一手來源不得將 StrollTimes 24 篇當作官方活動。再作 L6-B 與 P30-L7 isolated fresh JSON、P30-L8 Android/PWA 新候選實機 Gate；不重跑已驗收 44 筆 Android，不提前啟動 writer、通知、排程或其他 repo 退役。
>


> **2026-10-26 SRC-P30-L5-E StrollTimes citation lineage and BItan government corroboration（最新實際 GitHub Gate）**
>
> - **開發 Authority**：開始本 Gate 讀回 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`，上一階段 Source [Draft PR #29](https://github.com/easonliu714/event_scraper_public/pull/29) `f960d0bd91d4ca38df17f0ecb2c053fd7a0299f6`／CI `40312137162`（FamiTicket 4/4 detail、TPBL 三 role、其餘展期 UNKNOWN）PASS；原 P30-L4-C Android **44=5 CKSMH+39 TWTC USER_ATTESTED_PASS** 保留。PWA 正式 `docs/data.json`、`docs/index.html`、`scraper.py` 與 main SHA 全程 unchanged；本 Gate 不合併任何 PR，不啟動 writer、通知、排程，不刪除其他 Repository。
> - **P30-L5-E1 Source Draft [PR #30](https://github.com/easonliu714/event_scraper_public/pull/30)** `feat/eventradar-p30-l5e-strolltimes-source-lineage@ae2c2bdd014fdb9df2cb7d05781d6347d92848b5`（stack PR #29 frozen HEAD）：精確新增 `scripts/p30_l5e_strolltimes_source_lineage.mjs`、`tests/p30/test_l5e_strolltimes_source_lineage.mjs`、`.github/workflows/eventradar_p30_l5e_strolltimes_lineage.yml`。以標準 public Chromium 1 StrollTimes 首頁 + 6 同站文章（限 7 navigations、300 allowed resource requests、無私有 API／外站跟隨／登入／購票／stealth），**只讀文章 H2/H3「資料來源」到下一標題之間的帶出處連結**，分開 Facebook/Instagram、政府網站、票務網站、地圖與其他 URL；不把 map、相關文章、社群帳號的 link identity 冒充官方原始活動。首輪 [CI 40314277123](https://github.com/easonliu714/event_scraper_public/actions/runs/40314277123) 離線 23/23 PASS，線上 24 list、6 samples、2 H1 identity + 3 credits，但舊 CI 要求 6/6 H1、且小 request budget 導致後兩篇未完成，**FAIL**；改為 300 request budget、4/6 H1 差異保守 HOLD（首頁的子場域標題可能不等於正文上層活動；禁止 fuzzy），最終 **[Run 40314650154](https://github.com/easonliu714/event_scraper_public/actions/runs/40314650154) completed/success**：**23/23 tests、24 list、6/6 HTTP200、2/6 exact H1、3 條「資料來源」出處連結**（新竹萬聖節：新竹火車站旅遊服務中心 Facebook 貼文；碧潭小王子：新北旅客、新北市新店區公所 Facebook 貼文）。此 Success = **診斷／出處擷取 PASS**，四篇 title mismatch 及所有 social account authenticity、same-event 官方原文仍 HOLD。Artifact [12645714192](https://github.com/easonliu714/event_scraper_public/actions/runs/40314650154/artifacts/12645714192) ZIP digest `sha256:aeb7d368f20924e9025e49e0bed631c570410b8228e2e83ede047c1ebf02c65e`，expires `2026-11-09T11:23:49Z`，內有 lineage JSON/README/SHA manifest。
> - **P30-L5-E2 Source Draft [PR #31](https://github.com/easonliu714/event_scraper_public/pull/31)** `feat/eventradar-p30-l5e2-bitan-government@f0b07bf4ad45ed9e833d6825c4c119097c698694`（stack PR #30 frozen HEAD）：只新增 `scripts/p30_l5e2_bitan_government.py`、`tests/p30/test_l5e2_bitan_government.py`、`.github/workflows/eventradar_p30_l5e2_bitan_gov.yml`；下載 **E1 Run 40314650154** 的 SHA-sealed parent Artifact，嚴格驗 `https://strolltimes.com/events/new-taipei/261016084730/` 已 matched aggregator H1、原 originalOfficialUrl=NULL / zero Golden，再固定 2 個第一手政府 HTTPS URL 每個最多 GET 一次、無 redirects：新北市政府觀光旅遊局 [官方活動行事曆](https://newtaipei.travel/zh-tw/calendar/detail/4058)（官方活動名稱、**活動日期 2026-10-17 ～ 2026-12-13**、**新北市新店區碧潭風景區**、**主辦單位「觀光旅遊局」**）及 [新北市政府原始市政新聞](https://www.ntpc.gov.tw/ch/home.jsp?dataserno=66daa0e44fad9dd95b5b7e5ece1bf28d&id=e8ca970cde5c00e1)（**發佈日期 2026-10-14**、發布單位觀光旅遊局、相同小王子／碧潭活動）。**新聞 10/14 是 NEWS_PUBLICATION_DATE_NOT_EVENT_START**，不能與 10/17 開展日混用。起初 `40315539098`／`40315699923`／`40315801195` 因測試函式名稱包含空白 SyntaxError 而失敗，逐一正規化全部 20 test method，**最後 [Run 40315847664](https://github.com/easonliu714/event_scraper_public/actions/runs/40315847664) completed/success**：20/20 offline、政府 URL HTTP200/200、2 官網原始內容同活動、Gregorian 完整日期、發布日期獨立角色、前 Gate SHA、正式資料 Blob/路徑 Gate、ZIP SHA 皆 PASS。Artifact [12646961925](https://github.com/easonliu714/event_scraper_public/actions/runs/40315847664/artifacts/12646961925)，digest `sha256:a5c34c0fefce372cede0ac2c0e5e9d3b3b107d5073f9b880c86de9d57ff3aad6`，expires `2026-11-09T11:32:53Z`。
> - **定義清楚**：`STROLLTIMES_LIST=24_AGGREGATOR_ONLY`、`L5E1_SIX_ARTICLES_CAPTURED=PASS`、`L5E1_EXACT_H1=2_PASS_4_HOLD`、`L5E1_SOCIAL_SOURCE_CREDITS=3_LINKS_ACCOUNT_AUTHENTICITY_HOLD`、`L5E2_BITAN_FIRST_PARTY_GOV_EVENT_IDENTITY=1_PASS_REVIEW_ONLY`、`REMAINING_23_FIRST_PARTY_IDENTITIES=NOT_VERIFIED`。碧潭第一手官方日期及地點是**隔離來源證據，不是正式 JSON 的 dateStart/dateEnd**。全部新 Gate `GOLDEN_ACCEPTED=0`、`FORMAL_FIELD_PROMOTION=0`、`APP_DATA_PUBLISHED=false`、`AUTO_HIDDEN=0`、`SOURCE_RUNTIME=DORMANT`，網站中看見日期也不能自行推斷即時票況／持續無變更。
> - **下一步 P30-L5-E3／L6**：以來源-first、有明確官方活動 ID 與日期角色、父活動 vs 子活動的可逆 graph 邊關係，優先將餘下 23 StrollTimes 聚合文章做「原官網 URL／官方身分／日期／場次」逐步比對，無證據仍保留聚合提示；結束 L5 後啟動 **L6 G5J 保守可逆去重及分類、L7 全新隔離候選 JSON、L8 G5K Android／PWA 新增資料實機 UAT**。原 44 筆 Android PASS 不重測，NieR 原始追加場公告發佈時間仍 HOLD；所有功能 PR #30/#31 和治理 [PR #8](https://github.com/easonliu714/event_scraper_public/pull/8) 皆 Draft、未合併 main。
>


> **2026-10-26 P30-L5-D1 FamiTicket four-source details and real TPBL venue series sales roles Gate（最新）**
>
> - Source 權威 `main@fc4f963247d68eed29425808cc14e7250f312d05` 仍 frozen。前序 [Source Draft PR #28](https://github.com/easonliu714/event_scraper_public/pull/28) `16bb4bda029e8eee3951396d9031aac14576ad74`、CI `40305582187`（NieR 製作方 2/2 台北場次來源核對 PASS，但追加場原始 timestamp HOLD）與 Android 已驗收 **44=5 CKSMH+39 TWTC** 一律保留。FamiTicket 前序清單 47 僅是 list candidates，不能代表 47 筆 details 已經 Golden。
> - 新 [Source Draft PR #29](https://github.com/easonliu714/event_scraper_public/pull/29) `feat/eventradar-p30-l5d-famiticket-fields@f960d0bd91d4ca38df17f0ecb2c053fd7a0299f6`，base PR #28 frozen SHA，**僅新增 3 檔**：`scripts/p30_l5d_famiticket_field_roles.mjs`、`tests/p30/test_l5d_famiticket_field_roles.mjs`、`.github/workflows/eventradar_p30_l5d_famiticket_fields.yml`。使用未修改 Playwright Chromium、固定官方 `www.famiticket.com.tw/Home` **1 次首頁 + 最多 4 個不同 opaque-ID 詳情**；卡片的 `img alt`／heading/title/text 各自 exact，比對同一來源 URL，禁止 fuzzy merge、登入、購票、CAPTCHA/WAF 繞過、stealth、猜非公開 API、排程、正式 PWA/JSON、通知或自動下架。無重試、160 approved requests 上限、任何資料寫入只限隔離 Artifact。
> - 實際官方樣本：**2026 ITF 台灣國際旅展**、**臺中市立美術館「蠍子與青蛙：國巨基金會典藏展早鳥非預約」**、**2026 駁二動漫祭－同人誌創作展**、**TPBL 高雄全家海神 26–27 主場例行賽**。四頁 **4/4 HTTPS 200、4/4 list-detail exact heading PASS**，但前 3 頁本次擷取主要是票券/入場/購票說明，不能據此認定展期。第四筆官方 TPBL 的欄位格式是 emoji-prefixed `🔱比賽地點：K-ARENA 高雄巨蛋（高雄市左營區博愛二路757號）`、`🔱開放場次：26-27 賽季例行賽主場賽事`、`🔱預售票全面販售時間：10/8(四) 中午12:00 至比賽當日上午11:00`。已將它們明確分別定為 `VENUE_LABEL_ONLY`、`SERIES_DESCRIPTOR_NOT_EVENT_TIME`、`SALE_WINDOW_NOT_EVENT`，**只有 3 個 raw-role observations，均未提升為正式場地/活動日期/售票狀態**；賽季「26-27」與預售「10/8」不可猜成 2026/10/08 正式比賽日。票券兌換地點另列 `VOUCHER_REDEMPTION_LOCATION_NOT_EVENT_VENUE`，避免把兌換處當比賽場地。
> - 首版 [CI 40311603836](https://github.com/easonliu714/event_scraper_public/actions/runs/40311603836) 22/22 PASS、4/4 details title verified，但標籤角色=0（既有 inline label parser 不支援 emoji/TPBL 用語），後續新增 bounded diagnostic hints（只記少量公開欄位摘要），查出真實語法；中間 `40312029180`、`40312086929` 是 enum 更新前 CI ASSERT FAIL，**不得當成 PASS**。修正 emoji labels、系列場次與票務期限/場地角色、補 5 個回歸案例，再強制 CI 要求實測 3 種 role。**最終 [GitHub Actions Run 40312137162](https://github.com/easonliu714/event_scraper_public/actions/runs/40312137162) completed/success**：27/27 offline positive-negative、4/4 官方 title、3 raw role、Parent HEAD＋正式 `docs/data.json`／`docs/index.html`／`scraper.py` Blob parity、SHA manifesto 均 PASS。Artifact [12643879532](https://github.com/easonliu714/event_scraper_public/actions/runs/40312137162/artifacts/12643879532) `eventradar-p30-l5d-famiticket-field-roles`，ZIP digest `sha256:3489998d4869e979f9e7496f3abfa2ada17b4dc8369437b813950993b3635563`，expires `2026-11-09T11:04:34Z`。
> - Gate 分層：`P30_L5D_FAMITICKET_FOUR_DISTINCT_PUBLIC_DETAIL_IDENTITIES=PASS`、`P30_L5D_TPBL_THREE_ROLE_RAW_EVIDENCE=PASS`、`P30_L5D_OTHER_THREE_EVENT_TIME_COMPLETENESS=UNKNOWN/HOLD`、`P30_L5D_FORMAL_FIELD_PROMOTION=0`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`；原先 47 list 仍未全面逐筆審核。所有 Source PR #19–#29 仍 Draft/未 Merge，治理兩份檔案**只在 Docs Draft [PR #8](https://github.com/easonliu714/event_scraper_public/pull/8)**，尚不是 main 合併狀態。
> - **下一優先 P30-L5-E：StrollTimes 24 聚合文章 → 原主辦／售票方官方可追溯 URL lineage**，嚴禁把第三方日期/票況自動升級 Golden；同時對 FamiTicket 有明確官方時間證據的活動做少量更深入欄位語義核對（若沒有標示展期，PWA 保留「日期未確認／以官方來源為準」），繼續 L6 G5J 可逆跨來源去重及分類、L7 fresh isolated JSON、L8 G5K Android 真機 E2E。NieR 追加場原始公告發布時間仍 HOLD，禁止反覆搜尋當成證據。
>


> **2026-10-26 P30-L5-C NieR original producer cross-source Gate CI 40305582187（最新）**
>
> - GitHub 開發權威於此 Gate 開始確認 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`，L5B [Draft PR #27](https://github.com/easonliu714/event_scraper_public/pull/27) `bd0612ee49d992cd0c4c8843ba6b0a09dd39f90d`、CI `40303622151` completed/success（2 筆 ibon 源詳情、NieR 2 個開演場次、RUNIDRE 1 場仍屬原始 review-only），Android L4C USER_ATTESTED_PASS 44 筆（5 CKSMH、39 TWTC）全部保留。原正式 `docs/data.json`、`docs/index.html`、`scraper.py` 三個 Blob 的 CI SHA 與 frozen main 未更動；既有多個 PR 仍 Draft，禁止未授權合併或發布。
> - 新 [Source Draft PR #28](https://github.com/easonliu714/event_scraper_public/pull/28) `feat/eventradar-p30-l5c-nier-producer-source@16bb4bda029e8eee3951396d9031aac14576ad74`，**精確三新增檔** `scripts/p30_l5c_nier_producer_lineage.py`、`tests/p30/test_l5c_nier_producer_lineage.py`、`.github/workflows/eventradar_p30_l5c_nier_producer.yml`，base PR #27 frozen HEAD。Native CI 下載**特定 Run 40303622151** 的前階段 SHA sealed `change_notice_review.json`，驗證原本 ibon 2 件來源及 NieR 活動 `https://ticket.ibon.com.tw/ActivityInfo/Details/39974`、2/20 18:00 與 2/21 14:00 兩個角色和上游 zero-writer/zero-Golden，再對**固定公開 HTTPS allowlist** 做最多三次限量 GET：AWR Music/SQUARE ENIX NieR official production [tour](https://www.nierconcert.com/12026)、[Taipei 2/21 individual page](https://www.nierconcert.com/12026/taipei-2)、非主辦／非正式售票商的二手票券整理 [itix2go](https://itix2go.com/guest/program/detail/ncrp0)。以 Taipei city + 正確西元日期/星期 + 開演時間 + TICC venue **同一清單區塊綁定**，避免官網在 Bangkok 條目誤出現 TICC 場館字串而跨城市認錯。期間無登入、購票、WAF 繞過、私有 API、通知、排程、正式 JSON 或 PWA 操作。
> - 第一輪原生 CI `40305164107` test Python method 名稱含空白造成 SyntaxError，修後第二輪 `40305340307` 20/20 offline PASS 且首次實測 producer 2/2 身分成功；再因 Python requests 可能以 ISO-8859-1 解碼繁體中文 HTML，修成從原始 bytes+HTML UTF-8 解碼，避免第三方「加場售票時間」亂碼。**最終正式 [Run 40305582187](https://github.com/easonliu714/event_scraper_public/actions/runs/40305582187) completed/success**：20/20 安全與來源負例，正式 repo SHA/Scope、pin 前階段 Artifact SHA、GitHub real HTTPS 200/200/200，原始製作方場次 2/20 `18:00`、2/21 `14:00` **2/2 與 ibon 既有 L5B 來源時段精確吻合**，官方製作方 2/21 詳情可獨立驗證同日同時同場館。GitHub Artifact [12642720340](https://github.com/easonliu714/event_scraper_public/actions/runs/40305582187/artifacts/12642720340) ZIP digest `sha256:d9456d4f9aab96c80d11a75a68c4b25a6a3be2758e245eb8dd5b16cee8050360`、預計 `2026-11-09T10:12:46Z` 到期；四檔 `cross_source_review.json`、`parent_change_notice_review.json`、`README.txt`、`SHA256SUMS.txt` 完整 SHA Gate PASS。
> - **公告／銷售關鍵邊界**：NieR 2/21 出現在製作方第一手巡演清單／獨立活動頁，故可以標示 `OFFICIAL_PRODUCER_TOUR_TWO_TAIPEI_SHOW_STARTS_CORROBORATED`；但**原始「追加場」公告的發布時間及歷次更新版本沒有可驗證的第一手 timestamp URL**，不得補猜為 10/21。第三方二手票券整理頁目前有 `加場售票時間 2026/10/21 12:00`，但此「賣方／轉售平台日期」不等於主辦／官方售票公告，不能用於售票開賣判定；之前公開快照曾顯示製作方 2/21 頁面 `On Sale Oct. 21 9AM (UTC+8)`，**最終 GitHub Runner 現行 producer/detail HTML 已抓不到足以比較的售票時刻，因此最終機器判定為 `NO_COMPARABLE_SALE_TIMES_OBSERVED`，不能宣稱當前 09/12 差異已核實**。更不能將任一銷售日期誤判成 2027/02/21 演出時間。
> - Gate 分級：`P30_L5C_PRIOR_IBON_IDENTITY_AND_SHA=PASS`、`P30_L5C_PRODUCER_TWO_INDEPENDENT_EVENT_SESSIONS=PASS`、`P30_L5C_ADDITIONAL_SHOW_ORIGINAL_PUBLICATION_TIMESTAMP=HOLD`、`P30_L5C_SALE_TIME_CURRENT_PRIMARY_VS_SECONDARY=HOLD_INSUFFICIENT_COMPARABLE_EVIDENCE`、`P30_L5C_FORMAL_DATA_PROMOTION=0`。所有新候選維持 `dateStart/dateEnd=NULL`、`ticketStatus=UNKNOWN`、`price=NULL`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`。Source PR #28 仍 Draft，治理文件更新位於 [Docs Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8)，**不是已 merge 的 main**。
> - 下一個 P30-L5-D：若能安全找到主辦第一手**日期標示明確的追加場異動公告**才解除公告 timestamp HOLD；否則不再無限查詢，保留 producer tour 的兩場演出時間為 L6-L7 review-only 來源候選；進一步 FamiTicket 47 清單中合理比例的詳細資料有標籤抽樣和 StrollTimes 24 聚合文章到原主辦 URL 可追溯性，接著 L6 G5J 跨平台去重/可逆分類、L7 fresh isolated candidate JSON、L8 G5K Android／PWA。使用者先前 44 筆 Android UAT PASS 不重做。不可在主資料發布／Merge／通知與 repo 退役前跳過治理授權。
>


> **2026-10-26 P30-L5-B ibon two-detail notice parity CI 40303622151（最新）**
>
> - GitHub 權威再次確認 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`，P30-L5-A Source [Draft PR #26](https://github.com/easonliu714/event_scraper_public/pull/26) `b7e16cb39fc187cea927cf1521ee972d621f8a2a`、CI `40301911354` completed/success 22/22、ibon 原始官方詳情 2 筆／3 個活動開演候選、Android L4-C 已驗收 44（5 CKSMH＋39 TWTC）全部保留；未合併任何功能 PR 或更改正式 JSON/PWA。
> - 新 [Source Draft PR #27](https://github.com/easonliu714/event_scraper_public/pull/27) `feat/eventradar-p30-l5b-ibon-change-notice@bd0612ee49d992cd0c4c8843ba6b0a09dd39f90d`，base PR #26 frozen HEAD，精確三新增檔：`scripts/p30_l5b_ibon_change_notice.mjs`、`tests/p30/test_l5b_ibon_change_notice.mjs`、`.github/workflows/eventradar_p30_l5b_ibon_notices.yml`。原生 GitHub Actions 下載 L5-A **同一成功 Run 40301911354** 的 SHA256SUMS 已封存 Artifact，先驗證 `session_candidates.json` 的 2 個官方詳細頁 ID／3 個原始活動開演角色／DORMANT 與零正式寫入，再使用**未修改 Chromium** 只對原 2 個 numeric-ID `https://ticket.ibon.com.tw/ActivityInfo/Details/<ID>` 官方頁做各 1 次公開 GET（至多 2 導覽、120 官方站內請求），不再任意尋找其他事件、不登入、購票、繞過驗證碼或存取非公開 API。
> - **最終 [Run 40303622151](https://github.com/easonliu714/event_scraper_public/actions/runs/40303622151) completed/success**：20/20 正反向測試、frozen 父 HEAD + 正式 `docs/data.json`、`docs/index.html`、`scraper.py` SHA/路徑範圍 Guard、來源 Artifact 完整 SHA、自站 2/2 HTTPS200/detail exact title、**先前 L5-A 的 3/3 開演時間仍一致**、包含聆聽／入場與真實活動時間分欄邊界、輸出 JSON/ZIP SHA PASS。RUNIDRE detail 官方取樣場次相符，`NO_EXPLICIT_NOTICE_SECTION_CAPTURED_UNKNOWN` **只表示限定 DOM 範圍未找到明確公告，不是已核定「無異動」**。NieR Orchestra Concert 兩個場次相符，但公告區塊取樣得到 **`ADDITIONAL_SESSION_SIGNAL_REVIEW`（追加場）**，另外場次段內有「追加場」標記；這不等於獨立主辦方公告、也不能視為已核准追加場或可販售票券，需 `ORGANISER_CONFIRMATION_HOLD`。
> - Artifact [12640444559](https://github.com/easonliu714/event_scraper_public/actions/runs/40303622151/artifacts/12640444559) `eventradar-p30-l5b-ibon-change-notice`，ZIP digest `sha256:c1863e7c3024f6b6e329bdce71206ec931bf3d8077c6ee69d256e62e9082a7da`，expires `2026-11-09T09:58:10Z`，包含 `change_notice_review.json`、`parent_session_candidates.json`、`README.txt`、`SHA256SUMS.txt`。所有跨來源官方身份與公告核准仍 **HOLD**，不能將 `20/20 CI PASS` 解讀成「主辦同意／活動無異動／23 件詳情完整」。
> - Gate 分級：`P30_L5B_PINNED_SOURCE_SHA=PASS`、`P30_L5B_SAMPLED_EVENT_START_PARITY=PASS_3_OF_3`、`P30_L5B_NOTICE_SCOPE_AUDIT=PASS`、`P30_L5B_NIER_ADDITIONAL_SHOW_ORGANISER_CONFIRMATION=HOLD`、`P30_L5B_RUNIDRE_NO_CHANGE_PROVEN=FALSE`。正式 `dateStart/dateEnd=NULL`、`ticketStatus=UNKNOWN`、`price=NULL`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`、`FIELD_PROMOTION=0`。
> - **下一 Gate P30-L5-C**：核對 NieR 追加場原主辦／票務公告的可追溯 URL、發布／更新時間、時間區與原先場次之差異；對 RUNIDRE 若無最新公告只能保持未知，不能以「頁面無 notice」代表不延期。若來源內有可核准公告才建立可逆、隔離候選欄位升級，仍禁止正式 Writer。並行 FamiTicket 47 項清單詳細欄位有限抽樣，以及 StrollTimes 24 篇聚合文章的原始主辦 URL lineage；再執行 L6 G5J 去重/分類 → L7 fresh isolated JSON → L8 G5K Android/PWA。兩份治理文件**只在 Docs Draft PR #8**，尚非 main 已合併基線；PR #27 保持 Draft，不合併。
>


> **2026-10-26 P30-L5-A ibon 活動開演與入場時間語義 Gate PASS（最新）**
>
> - 最新讀回 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`，前序 P30-L4-D3 Source [Draft PR #25](https://github.com/easonliu714/event_scraper_public/pull/25) `622a52221d6fded07d0829486f3877835e372da40`、CI `40299649653` PASS（FamiTicket 一筆 public Chromium 官方詳情），P30-L4-D2 ibon 詳情兩筆 HTTP200／2/2 exact title，和 P30-L4-C Android **44=5 CKSMH+39 TWTC USER_ATTESTED_PASS** 全部保留不重驗。沒有 Merge、不改正式 `docs/data.json`、`docs/index.html`、`scraper.py`。
> - 新 [Source Draft PR #26](https://github.com/easonliu714/event_scraper_public/pull/26) `feat/eventradar-p30-l5a-ibon-sessions@b7e16cb39fc187cea927cf1521ee972d621f8a2a`，堆疊 PR #25 **frozen HEAD**。精確新增三檔：`scripts/p30_l5a_ibon_session_roles.mjs`、`tests/p30/test_l5a_ibon_session_roles.mjs`、`.github/workflows/eventradar_p30_l5a_ibon_sessions.yml`；復用 L4-D2 bounded public ibon stock Chromium 1 清單 + 2 個 numeric-ID 的官方詳情，L5-A 解析器**不再新增網路請求**、僅讀取同 CI 產出的 `diagnostics.json`；產物寫於 `p30-l5a-output/`，禁止正式 Pages writer／登入／購票／驗證碼繞過／私有 API。
> - 最終 native [GitHub Actions Run 40301911354](https://github.com/easonliu714/event_scraper_public/actions/runs/40301911354) **completed/success**：22/22 offline positive+negative role tests、SHA/正式 Blob/三新增檔 source guard、ibon list HTTPS200/**23 候選**、2/2 detail HTTPS200 與 exact list-detail heading、2 個 labeled event-time blocks，成功從官方詳情解出 **3 個 eventStartLocal＋3 個 admissionStartLocal**：RUNIDRE 台北 `2026-12-19T17:00` 開演／`16:00` 開場；NieR Orchestra Concert `2027-02-20T18:00` 開演／`17:00` 開放入場及追加場 `2027-02-21T14:00` 開演／`13:00` 開放入場。**RUNIDRE 來源有明確「台灣時間」標記才標記 `Asia/Taipei`；NieR 兩場的擷取段落無明確時區，保留 `sourceTimeZone=NULL`／`NOT_EXPLICIT_IN_CAPTURED_BLOCK`，不可補猜。**
> - 前段 CI `40301598471`、`40301869923` 測試 HOLD：來源 `heading` 截長度後與 `rawExcerpt` 多餘空白的文字比較不一致、負例預期 enum 名稱未同步；已 fail-closed 修復為雙方先空白正規化及正式 `HOLD_EVENT_TIME_HEADING`，**唯一最後 Gate 判定以成功 Run `40301911354` 為準**。週幾標示與西元真實日期必須一致、invalid dates／日期截斷／售票期間／報名期間／票券有效期／取消延期／開場晚於開演／HTTP/標題身分不符／URL 換站或重複／原證據 SHA 語義錯配都不得認定為場次。
> - [Artifact 12640209144](https://github.com/easonliu714/event_scraper_public/actions/runs/40301911354/artifacts/12640209144) `eventradar-p30-l5a-ibon-session-role-evidence` archive SHA256 `7346e93f1ec066a6d9209f1237530c7e3e1a8fce7ed93fcf8fc8c08d6fe17b97`，expires `2026-11-09T09:45:17Z`，`input_diagnostics.json`、`session_candidates.json`、`README.txt`、`SHA256SUMS.txt`；全部 native SHA Gate PASS。注意 23 ibon 是**清單候選**，活動場次語義只核對其中 2 件，不能將 3 場當作 3 個新獨立活動或推定 23 件完整。
> - **保持鎖定**：`proposedSessions[]` **REVIEW_ONLY**，`dateStart/dateEnd=NULL`、`fieldPromotionCount=0`、`sourceTimeZone` 僅依明確原文、`ticketStatus=UNKNOWN`、`price=NULL`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`。PR #23/#24/#25/#26 都是 Draft/未合併；兩份治理文件僅由 Docs [Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8) 更新，仍**不是已合併 main**。
> - **下一個 Gate P30-L5-B**：在 ibon 相同原始來源的 *延期公告、活動時間、開場、售票、票券使用期限* 做變更通知角色與多場次一致性檢查，且需確認主辦／公告證據後才許新隔離候選對外顯示精準日期；同步對 FamiTicket 47 清單詳情做有證據、有限抽樣欄位 QA，StrollTimes 24 僅聚合文章需逐筆 lineage 到主辦官方，然後才啟動 L6 G5J 可逆去重分類、L7 fresh isolated JSON、L8 G5K Android/PWA 真機驗證。已通過的 Android 44 不重跑，19 平台 Golden 和正式 writer 都不能先行放行。
>


> **2026-10-26 P30-L4-D3 FamiTicket Chromium official detail identity（最新）**
>
> - 接續本日 P30-L4-D1 / L4-D2，不回退既有 44 Android USER_ATTESTED_PASS、FamiTicket list 47、ibon rendered list 23／2 個明確來源時間證據、StrollTimes 24 篇聚合文章。Source `main@fc4f963247d68eed29425808cc14e7250f312d05`、`docs/data.json`、`docs/index.html`、`scraper.py` 仍 frozen/未發布。本次新 [Draft PR #25](https://github.com/easonliu714/event_scraper_public/pull/25) `feat/eventradar-p30-l4d3-fami-public-browser` base Source PR #24 完成 HEAD `ca9ab41c930296c4c9c74a329454466f55a6e611`，只新增 `scripts/p30_l4d3_famiticket_browser.mjs`、`tests/p30/test_l4d3_famiticket_browser.mjs`、`.github/workflows/eventradar_p30_l4d3_fami_browser.yml`。只用未修改 Chromium 單次 FamiTicket `/Home` 和**以唯一 opaque 詳情 URL 綁定的** 2026 ITF 台灣國際旅展單一 public detail，禁止登入／購票／驗證碼繞過／私人 API 猜測。
> - 初版 CI `40299320318` / `40299497551` 14/14 offline PASS，但標的活動 `HOLD_LIST_EXACT_UNIQUE_IDENTITY`。**實際原因已確認**：FamiTicket 2026 ITF 多處重複首頁卡片的官方標題在 `img alt`，連結 `textContent` 可能只有「展覽」或是空字串；原 selector `heading||label||text||alt` 受先遇到的分類文字影響。修成獨立比較四個欄位任一 **exact title** 並依 canonical 同一 opaque URL 去重（如有不同 URL 仍 HOLD），新增兩個來源實例的正反向 regression；未放寬一般 fuzzy matching。
> - **最終 Source PR #25 HEAD `622a5221d6fded07d0829486f3877835e372da40`**，native [GitHub Actions Run 40299649653](https://github.com/easonliu714/event_scraper_public/actions/runs/40299649653) **completed/success，16/16 offline、安全 scope／Blob Gate PASS**。官方 FamiTicket homepage **HTTP200，Chromium DOM 231 anchors**；ITF 唯一 same-ID 連結綁定 PASS；官方 detail **HTTP200、1 個精確匹配 H1/H2/H3/H4 標題、頁面文字含 ITF 名稱**；檔案 SHA manifest PASS。隔離證據 [Artifact 12639478214](https://github.com/easonliu714/event_scraper_public/actions/runs/40299649653/artifacts/12639478214)，archive SHA256 `aff6a0e169bc972b8632cb62930b63dd92ad6cc82d5c50680f66a0f94bbb3732`，expires `2026-11-09T09:27:59Z`。這次證明 public Chromium **一筆**詳情可正確顯示／綁定，**不能倒推整批 47 件、不同 Runner/日期都穩定**；過去 P30-L4-D1 requests 同 URL 0/2 headings 的變異列為待進一步查明，並非活動失效。
> - `P30_L4D3_FAMITICKET_ONE_BROWSER_DETAIL_IDENTITY=PASS`，`P30_L4D1_FAMITICKET_RAW_HTTP_DETAIL_STABILITY=HOLD`，`P30_L5_FAMITICKET_DATE_ROLE/PRICE/TICKET_STATUS=OPEN`。`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`。PR #23/#24/#25 皆 Draft/未合併，兩份治理 docs 只存在 [PR #8](https://github.com/easonliu714/event_scraper_public/pull/8) Draft、尚未 main merge。
> - 下一 Gate **P30-L5**：針對 ibon 現有 2 件的官方「活動時間」原始證據，建構可稽核日期／開場／開演／多場次與售票／報名／票券有效期角色，保護已發現 19→1、20→02 的 date token 回歸；FamiTicket Chromium 詳情欄位進一步小樣本擷取（不得以首頁卡片 MM/DD 當已確認年與活動），StrollTimes 只可作聚合線索，須綁原始主辦／票務出處後才能放入候選整併。再進入 L6 可逆去重/分類 → L7 isolated JSON → L8 Android 實機，**不必重做已通過的 44 Android UAT**。
>


> **2026-10-26 P30-L4-D1 FamiTicket / L4-D2 ibon source detail Gate（最新正式治理追蹤，PR #8 Draft）**
>
> - **版次前提**：直接讀回 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`；Source P30-L3-B-C PR #22 `e7e13c845d042b4a0b13cc98bdd51ba03d836fa8` 及 CI `40295191261` PASS（StrollTimes 24 聚合文章）保留不回退；P30-L4-C Android 8770 **USER_ATTESTED_PASS**（44=5 CKSMH+39 TWTC）保留。所有新 Gate 是基於 Source P30 stacked Draft PR、不改正式 main/Android 44/Pages/原正式 JSON。
> - 新 [Source Draft PR #23](https://github.com/easonliu714/event_scraper_public/pull/23) **P30-L4-D1 FamiTicket 官方詳情穩定性＋時間語義**，`feat/eventradar-p30-l4d-fami-detail-stability@6ae9fcdf42686474489d7df48d944bd70b89a431`，僅新增 `scripts/p30_l4d1_famiticket_detail_roles.py`、`tests/p30/test_l4d1_famiticket_detail_roles.py`、`.github/workflows/eventradar_p30_l4d1_famiticket.yml`。19/19 offline tests：活動／演出／展覽日期區分售票期間、報名期間、票券使用期限，否定無年份、無標籤、無效日、不同標題、HTTP 200 空頁等案例。真實官方 `/Home` **HTTP200、47 筆清單**，綁定唯一 2026 ITF 台灣國際旅展詳情、**同一 URL 分開 2 次 HTTPS 200 GET，但 0/2 次取得 exact detail title**，故 `HTTP_LIST_AND_DIAGNOSTIC=PASS`、`FAMITICKET_DETAIL_IDENTITY_STABILITY=HOLD_TWO_RESPONSES_WITHOUT_TITLE`；不可自動判為活動失效或補日期。GitHub [Run 40297130466](https://github.com/easonliu714/event_scraper_public/actions/runs/40297130466) completed/success **只表示測試／證據捕捉成功**，Artifact [12638935938](https://github.com/easonliu714/event_scraper_public/actions/runs/40297130466/artifacts/12638935938)，archive SHA256 `1776bd53e34b37091c95977c774695a2857181727ec851ec1d0a6813799ea53e`。需下個 L4-D3 以標準公開 Chromium 檢查 FamiTicket 詳情 JS 渲染與相同 ID 身分，繼續保持 fail-closed、禁止繞過登入/驗證碼或自動購票。
> - 新 [Source Draft PR #24](https://github.com/easonliu714/event_scraper_public/pull/24) **P30-L4-D2 ibon 官方詳情與角色原始證據**，`feat/eventradar-p30-l4d2-ibon-detail-evidence@ca9ab41c930296c4c9c74a329454466f55a6e611`，堆疊 PR #23 HEAD，僅新增 `scripts/p30_l4d2_ibon_detail_roles.mjs`、`tests/p30/test_l4d2_ibon_detail_roles.mjs`、`.github/workflows/eventradar_p30_l4d2_ibon_detail.yml`。標準 public Chromium 官方娛樂入口 1 次 + 兩個綁定清單 ID 的 `/ActivityInfo/Details/<numericId>` 詳情，不登入、不點購票、不用非公開 API，範圍只讀。最終 [GitHub CI Run 40298499664](https://github.com/easonliu714/event_scraper_public/actions/runs/40298499664) **completed/success：19/19 offline、清單 HTTPS 200 仍 23 unique、兩筆詳情 2/2 HTTP200 且 H1/H2 exact list title、各自 1 組明確活動時間 block**；例如 `【活動時間（台灣時間）】2026年12月19日 開演17:00` 及 `日期/時間｜2027.02.20 18:00／2027.02.21 14:00（追加場）`。這是有標籤的原始時間**可核對證據**，尚未證明剩餘 21 筆詳情及跨來源延期／售票真實性。Artifact [12638968553](https://github.com/easonliu714/event_scraper_public/actions/runs/40298499664/artifacts/12638968553)，archive SHA256 `e52c2e430ad40d6b6ff65258fd89fca160927487ffd140588a49dda58086358c`，到期 `2026-11-09T09:18:51Z`；四檔 SHA256 manifest GitHub PASS。
> - ibon 修正歷程重要：初次 `scheduleBlockEvidence` full-year token regex 把 `2026年12月19日` 錯裁為 `2026-12-01`，把 `2027.02.20` 錯裁為 `2027-02-02`；PR #24 後續以**月份／日期長 token 優先並檢查右端 digit 邊界**修復。此錯值從未提升至 `dateStart/dateEnd` 或正式 JSON；最後 19/19 regression + 實際 CI 兩筆證據已校正為 **2026-12-19、2027-02-20、2027-02-21**。舊 CI 40298177737 為測試失敗修復歷史，**最終版只認 40298499664**。
> - **明確 Gate 分級**：`FAMITICKET_47_LIST_PASS`、`FAMITICKET_2X_DETAIL_IDENTITY_HOLD`；`IBON_23_LIST_PASS`、`IBON_2_DETAIL_TITLE_IDENTITIES_PASS`、`IBON_2_LABELED_RAW_EVENT_TIME_BLOCKS_PASS`；`ALL_23_EVENT_DATES_VERIFIED=FALSE`。對所有新來源仍 `dateStart/End=NULL`、`ticketStatus=UNKNOWN`、`price=NULL`、`GOLDEN_ACCEPTED=0`、`APP_DATA_PUBLISHED=false`、`AUTO_HIDDEN=0`、`SOURCE_RUNTIME=DORMANT`。兩份治理文件更新**只存在 [PR #8](https://github.com/easonliu714/event_scraper_public/pull/8) Draft，未合併 main**；PR #23/#24 亦 Draft/未合併。
> - **下階段 Roadmap**：L4-D3 FamiTicket 在標準瀏覽器公開資料中修復不穩定 detail identity（如果同樣空白則明確 HOLD，無需不停重試），L5-B ibon 兩種有標籤真實活動時間的日期/場次/售票期間嚴格角色 QA、取樣擴張和可逆欄位候選；同時 StrollTimes **仍為第三方聚合**，須找原主辦／售票來源，不可直接移入正式活動庫；再依序 L6 可逆去重/分類（G5J）→ L7 isolated fresh JSON → L8 Android/PWA 實機 UAT（G5K）→ 逐項授權正式 Writer/單 Repo 收斂。目前不需使用者再次測試已通過的 44 Android 候選。
>


> **2026-10-26 P30-L3-B-C StrollTimes 聚合清單 24 筆與 1 篇聚合文章 Gate PASS（最新）**
>
> - GitHub authority：Source `main@fc4f963247d68eed29425808cc14e7250f312d05` 未修改；前序 P30-L4-C Android 8770 USER_ATTESTED_PASS（44=5 CKSMH+39 TWTC）保留，FamiTicket L3-B-A 47 list、ibon L3-B-B2 23 rendered list / CI success 均不退回、不重跑。PR #8（文件）、#21（ibon）保持 Draft，無 Merge、無正式 JSON 修改。
> - StrollTimes 現行 `https://strolltimes.com/` 展示全台活動；自站「關於我們」稱**獨立編輯整理活動**，有自己的 `/events/<county>/<numericArticleId>/` 文章，而非活動主辦或售票機構，故其內容不能自動核定官方場次、票價、票況或可否報名；外部連結也必須另核對主辦身分。
> - 新 [Source Draft PR #22](https://github.com/easonliu714/event_scraper_public/pull/22) `feat/eventradar-p30-l3bc-strolltimes-aggregation` 堆疊 PR #21 frozen HEAD `6fa959de1613458505fec8d9813d9916be5cfcd7`；精確三新增檔 `scripts/p30_l3bc_strolltimes.mjs`、`tests/p30/test_l3bc_strolltimes.mjs`、`.github/workflows/eventradar_p30_l3bc_strolltimes.yml`。Native CI 限制原生 Chromium 公開頁面 1 homepage + 1 same-host article；不登入、不繞過驗證碼、無 stealth、攔截第三方請求／圖片媒體等非必要資源、最高 100 allowlisted requests。禁止 Pages writer、通知、排程、Golden、資料刪除。
> - 初始 CI `40294549909` 有 1/10 負例失敗（「查看更多」被當文章名稱），修正後 HTTP200 取得 24 unique list URLs；另一項 `ARTICLE_TITLE_HOLD` 查出首頁「2026新竹市萬聖節」與文章 H1「2026新竹市萬聖節（10/16~10/31）」差異，改成**只允許尾端單純 MM/DD～MM/DD 日期展示註記**的相同活動身分核對，絕不把該字串當官方日期證據，不能模糊替換其他活動。
> - **最終 Source PR #22 HEAD `e7e13c845d042b4a0b13cc98bdd51ba03d836fa8`**，[GitHub Actions Run 40295191261](https://github.com/easonliu714/event_scraper_public/actions/runs/40295191261) **completed/success**：11/11 Node provenance/security 正反測試、Source main docs Blob Guard、GitHub 原生 browser homepage HTTP200、DOM anchors 113、**24 筆 aggregator article 身分去重候選**、sample 同站文章 HTTP200 + bounded H1 title match PASS；62 allowed asset requests、11 external blocked、4,059 image/font/media requests blocked、24 JS pageerrors（外部／被攔截資源可能造成、需後續關注，但本次已取得穩定清單）。所有欄位 `dateStart/End=NULL`、`price=NULL`、`ticketStatus=UNKNOWN`、`category=待分類`、`originalOfficialUrl=NULL`，無一被認列 first-party Golden。
> - 只讀證據 GitHub [Artifact 12638155320](https://github.com/easonliu714/event_scraper_public/actions/runs/40295191261/artifacts/12638155320) `eventradar-p30-l3bc-strolltimes-aggregation`，zip SHA256 `e2d973d1e0faf03de78d8ed86abc292333f85d9112dd74033d6562e4b9e538c1`，expires `2026-11-09T08:52:01Z`，內含 `candidate.json`、`diagnostics.json`、`README.txt`、`SHA256SUMS.txt`；各檔 SHA in CI PASS。之前 Run 40294702951 清單成功但 article H1 HOLD，只作改進歷史，**非最終結果**。
> - 判定：`P30_L3BC_STROLLTIMES_AGGREGATOR_LIST=PASS_24`、`P30_L3BC_ONE_AGGREGATOR_ARTICLE_IDENTITY=PASS`，但 `P30_L3BC_PRIMARY_ORGANISER_SOURCE=OPEN_NOT_VERIFIED`、`P30_L3BC_DATE_PRICE_TICKET_CLASSIFICATION=UNKNOWN`、`P30_L3BC_ANDROID_UAT=NOT_REQUIRED_YET`。不得把 24 筆 StrollTimes 作為 24 筆新增官方活動；先對照 FamiTicket／ibon／政府／主辦原始來源並執行來源 lineage 和可逆去重。現有 Android 44 筆未更動。
> - 下一優先：`P30-L4/L5` 分層來源品質（FamiTicket 詳情穩定性、ibon detail 官方身份；StrollTimes 聚合→原始活動來源的可追溯證據、真正活動日期與報名／票券使用期間角色）→ `P30-L6` 分類及跨平台保守去重 → `P30-L7/L8` 新隔離 JSON、Android/PWA 實機驗證。19 平台 Golden、正式 Data Writer、Pages、通知與 ShowNews/Preview repo 退役皆 LOCKED。兩份治理變更僅在 Docs Draft PR #8，**尚未合併 main**。
>


> **2026-10-26 P30-L3-B-B ibon JS Browser 23 official link candidates CI PASS（本次最新 Gate）**
>
> - GitHub 權威讀回：Source `main@fc4f963247d68eed29425808cc14e7250f312d05` 未變；原使用者已驗收 **P30-L4-C Android 8770 USER_ATTESTED_PASS** 與 P30-L3-B-A **FamiTicket LIST=47** 全保留。FamiTicket Source PR #19 HEAD `17acb05b8da6066883113e91d68e852ba3db080f` 仍 Draft。正式 `docs/data.json`、`docs/index.html`、`scraper.py` Blob parity 無修改。其它 Source PR 未經授權不 Merge。
> - ibon 原 L1 `/Activity/Index` HTTP200/LIST0。新 Source [Draft PR #20](https://github.com/easonliu714/event_scraper_public/pull/20) `feat/eventradar-p30-l3bb-ibon-official` 堆疊 PR #19 HEAD，三檔新增：`scripts/p30_l3bb_ibon.py`、`tests/p30/test_l3bb_ibon.py`、`.github/workflows/eventradar_p30_l3bb_ibon.yml`；標準 requests 只做官方 `https://ticket.ibon.com.tw/Index/entertainment`、`/Home/MoreResult?inATAPID=105&inATAPWebType=entertainment` 限定最多兩個 GET，1 詳情抽樣（本次因無清單未執行）。最終 HEAD `54d65d382ab30b5d864f1841fc6a12452895b927`，Runner [40291426723](https://github.com/easonliu714/event_scraper_public/actions/runs/40291426723) 13/13 Offline PASS、官方 HTTPS **200/200**，但兩頁皆為 **同樣 5766-byte／title=ibon售票系統／11 scripts／8 visible characters／0 anchors／0 candidates**，因此 `HTTP_DIAGNOSTIC_PASS / HTTP_RAW_LIST_HOLD`。CI 故意以非零值結束，**不得稱為清單 PASS**；證據 Artifact `12635408987` 保留。
> - 為區分正常 JavaScript SPA 與無效來源，後續新 [Draft PR #21](https://github.com/easonliu714/event_scraper_public/pull/21) `feat/eventradar-p30-l3bb-ibon-browser` 堆疊 PR #20 HEAD，三新檔 `scripts/p30_l3bb_ibon_browser.mjs`、`tests/p30/test_l3bb_ibon_browser.mjs`、`.github/workflows/eventradar_p30_l3bb2_ibon_browser.yml`。原生 Chromium（無 stealth/登入/驗證碼/購票）僅開啟上述官方娛樂入口 **1 次**，JavaScript 正常渲染；allowlist 僅 ibon HTTPS 子網域、最高 90 請求、攔截非官方/圖片媒體字型等資源。無任何已發布 JSON/PWA Writer/通知/排程操作。
> - Source PR #21 HEAD `6fa959de1613458505fec8d9813d9916be5cfcd7`，正式 GitHub Actions **[Run 40292155453](https://github.com/easonliu714/event_scraper_public/actions/runs/40292155453) completed/success**，7/7 JavaScript negative tests、Scope/Source 原始 Blob Guard、Standard Chromium **HTTP 200、DOM 70 anchors、活動 ID 綁定後 23 筆去重官方清單候選**；網路 23 allowlisted requests、4 external blocked、41 passive resources blocked、0 request budget exceed、0 page JS errors。Artifact **[12635589126](https://github.com/easonliu714/event_scraper_public/actions/runs/40292155453/artifacts/12635589126)**，zip SHA256 `072e04c06be546f8b0a1f0fb382c6c6a414d6711f583354cb558909db93961a5`，expires 2026-11-09T08:26:01Z，SHA256 manifest CI PASS。
> - Gate 判定：`P30_L3BB_IBON_HTTP_RESPONSE_DIAGNOSTIC=PASS`、`P30_L3BB_IBON_BROWSER_RENDERED_LIST=PASS_23_CANDIDATES`、`P30_L3BB_IBON_DETAIL_SOURCE_IDENTITY=OPEN`、`P30_L3BB_IBON_DATE_PRICE_TICKET_CLASSIFICATION=UNKNOWN`、`ANDROID_UAT_NOT_REQUIRED_YET`。這不是 ibon 全目錄、真實開賣、Golden 或正式 PWA 可發布驗收。**未將 23 ibon 疊入已通過 44 Android 候選**，也未自動下架任何活動。
> - 下一級優先順序：P30-L3-B-C StrollTimes（聚合來源辨別原始活動 URL）→ P30-L4/L5 FamiTicket+ibon 逐筆詳情來源身分、日期/期間/票況分欄 → P30-L6 可靠分類與可逆去重（G5J）→ P30-L7/L8 新隔離 JSON + Android/PWA E2E（G5K）。所有 19 平台 Golden/正式 Writer、PWA Pages、通知、排程、兩外 Repo 退役仍 LOCKED。
>


> **2026-10-26 P30-L4-C Android UAT PASS → P30-L3-B-A FamiTicket official list recovery（latest）**
>
> - 使用者 2026-10-26 提交 Chrome Android local `127.0.0.1:8770` 真機截圖，明確回報「驗證項目皆通過，可進入下一個階段」。畫面證據包含 44 候選、台北世貿 39 筆、CKSMH「自由花蕊」常設展僅清單期間、系列講座 PartII 六場**真正活動時間**/每場**報名期間**獨立分欄/場地逐場列示，且上一版錯把報名視為活動時間的問題不再重現。據此記錄 `P30_L4C_ANDROID_REAL_UAT=USER_ATTESTED_PASS`，綁定 Source PR #18 HEAD `2656c43fc1fa4486fcbd8be641531e4d15220104`、CI [Run 40287542387](https://github.com/easonliu714/event_scraper_public/actions/runs/40287542387)、Android Artifact `12634941609`。回條涵蓋手機畫面所示功能，不等於 19 平台 Golden/正式 PWA Scope/offline/install 整合。
> - 依治理樹續接先前 HTTP200/LIST0 平台的 `P30-L3-B`，先選 FamiTicket（L3-B-A），不再重做 CKSMH/TWTC Android Gate。官方 FamiTicket 首頁 `https://www.famiticket.com.tw/Home` 現有活動清單及 `/Home/Activity/Info/<opaque-id>` 詳情；舊 P30-L1 `/Home/Activity/Search/242` HTTP200/LIST0 為固定入口/HTML 選取缺口，不可推斷平台無活動。
> - Source 新 [Draft PR #19](https://github.com/easonliu714/event_scraper_public/pull/19) `feat/eventradar-p30-l3b-famiticket-official` base P30-L4-C frozen HEAD；只新增 `scripts/p30_l3b_a_famiticket.py`、`tests/p30/test_l3b_a_famiticket.py`、`.github/workflows/eventradar_p30_l3b_a_famiticket.yml`。嚴格官方 HTTPS host/path/redirect、單一 `/Home` GET＋最多一筆 detail GET、HTML byte cap、無重試、12 項負例測試。這 47 筆清單候選的票況不可自動轉為售票中；每筆 `dateStart/dateEnd=NULL`、`price=NULL`、`ticketStatus=UNKNOWN`、`category=待分類`、`rawScheduleRole=UNCLASSIFIED_LISTING_TEXT`，禁止將預售／票券使用期限誤標活動時間。
> - GitHub Actions **最終 [Run 40289865032](https://github.com/easonliu714/event_scraper_public/actions/runs/40289865032)** `completed/success`、12/12 offline、官方首頁 HTTP200、**47 筆去重候選**、2026 ITF 台灣國際旅展一筆詳情 HTTP200 且官方標題精確吻合，三檔 manifest SHA OK。最新 Source PR #19 HEAD **`17acb05b8da6066883113e91d68e852ba3db080f`**。證據 [Artifact 12636240385](https://github.com/easonliu714/event_scraper_public/actions/runs/40289865032/artifacts/12636240385) digest `sha256:dd91b3e5baaabb32def605bdd474ae6f92e1e909ec937b4e3141445dbb399113`，expires 2026-11-09T08:05:32Z。之前 Run 40289507643 一次精確詳情 PASS，但 Run 40289673663 同一 HTTPS 詳情 HTTP200 卻未出現標題，顯示**詳情模板/回應不穩定**；L3-B-A 只宣稱 `LIST_RECOVERED_PASS`，`DETAIL_HTTP_SAMPLED_PASS` 及 `DETAIL_STABILITY_HOLD`，不宣稱 47/47 詳情已查證。
> - 下個 P30-L3-B-B 必須優先排查 ibon：原 `ticket.ibon.com.tw/Activity/Index` HTTP200/LIST0；核對官方變更後網址、是否伺服端活動卡或 JS/AJAX 動態，使用 public-only/限流/單次 GET 的真實證據，未能合法取得則 HOLD 而非偽造。後續 L3-B-C StrollTimes，須考量它是活動整理/聚合網站，不能自動當原始主辦方官方日期或票況。全部完成後，再跑 L4/L5 日期角色與取樣詳情、L6 可逆類別/去重、L7 isolated candidate、L8 Android PWA Gate。尚未把這新 47 筆疊上舊 44 筆 Android/正式 JSON。
> - 全程 `GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`，Source `main@fc4f963247d68eed29425808cc14e7250f312d05` 不動，PR #8/#18/#19 Draft 未合併；不得修改正式 Pages/PWA、通知、排程、Writer 或退役 ShowNews/Preview Repository。
>


> **2026-10-26 P30-L4-C Android date-role semantics post real-device feedback**
>
> - 使用者提交 P30-L4-B Android `127.0.0.1:8769` 實機截圖，表明「實機驗證基本上都通過」，但指出部分多場次活動（自由花蕊系列講座等）把**報名期間誤標示為活動日期**。只核准本次畫面範圍的清單／詳情／標題／場地／摘要回歸結果，新增 `L4B_DATE_ROLE_SEMANTICS_FOLLOWUP`；不得把該 UAT 當成完整 Golden/19 平台/正式上線通過。
> - 直接源端原因：舊 P30-L4-B `SESSION_RE.findall(section)` 抓取所有完整時間區間，混淆官網「場次：實際講座日期/時間」與同區塊「報 名 期 間：開始～結束」。actId 61021「自由花蕊系列講座 Part II：自己的房間」原誤顯示從 2026/10/16 到 2027/01/16；實際第一場 2026/11/07 14:00～16:00，10/16 11:30 為該場報名起始。actId 61024「《民主大冒險》圖文書新書分享會」實際活動從 2026/11/04 起，10/01 是首場報名起始。官網 `自由花蕊(免費參觀)` actId 51331 為**另一筆常設展活動**，官方清單 2025/11/24～2030/12/31；目前既無證據宣稱「每天開放」亦不能自行認定此整段是報名期間。
> - 新 [Source Draft PR #18](https://github.com/easonliu714/event_scraper_public/pull/18) `feat/eventradar-p30-l4c-session-registration-roles` 堆疊在 PR #17 已實測版本 `d79de853c007ac965d02b56cc2e556f8ad5f1bff`；四路徑（新增 `scripts/p30_l4c_cksmh_semantic_roles.py`、`tests/p30/test_l4c_cksmh_semantic_roles.py`、`.github/workflows/eventradar_p30_l4c_semantic_roles.yml`，僅修改隔離版 `scripts/p30_l7a_smoke_index.html`）。首次 CI `40287370407` offline 有 3 failed fixtures（FULL_RANGE date year 被 heading HHMM partial match；無角色標籤時應 FAIL CLOSED），修補後最終 HEAD `2656c43fc1fa4486fcbd8be641531e4d15220104` 完整 PASS；舊失敗 CI 是修補歷史，非正式 Gate PASS。
> - **最終 CI [Run 40287542387](https://github.com/easonliu714/event_scraper_public/actions/runs/40287542387)** `completed/success`，12/12 positive/negative tests、JS syntax、父 P30-L4-B 44 筆 Artifact SHA、五筆 CKSMH 來源 HTTPS HTTP200、來源 actId/title match、39 筆 TWTC data exact parity、候選資料 SHA bundle。取回 **10 組真正活動場次**（61004=1、61024=2、61026=1、61021=6）、**8 組報名時間窗**（61024=2、61021=6）、保留 51331 **OFFICIAL_LIST_PERIOD_UNCLASSIFIED** 而不宣稱開放／報名時間。實際場次 `dateStart/dateEnd` 與 `registrationWindows`／`sessions[].registration` 分離，單場次場地逐一保留，不再拼成錯誤活動區間；活動資訊未驗證者不臆測。
> - **下一個 Android 實機 UAT（尚未回報）**：隔離 Artifact [12634941609](https://github.com/easonliu714/event_scraper_public/actions/runs/40287542387/artifacts/12634941609) `eventradar-p30-l4c-semantic-android`，archive digest `sha256:d9cd41ffb7c0eaebf1be066e2a5dbcb380f59d3f0366da2ed183261414d3abd1`，expires `2026-11-09T07:43:49Z`；Android 本機 `127.0.0.1:8770`。優先驗證 61021 / 61024 真正場次時間與報名期間分欄、51331 官方清單期間但非每日場次、金融科技展延期與 39 筆世貿未回歸、44/5/39。
> - `P30_L4C_OFFICIAL_AND_CI=PASS`、`P30_L4C_ANDROID_REAL_UAT=WAITING_USER`。PR #18 與治理 PR #8 均 Draft/未 Merge；Source `main@fc4f963247d68eed29425808cc14e7250f312d05` 不動，`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`SOURCE_RUNTIME=DORMANT`，正式 PWA /通知/排程/Writer/三 Repo 退役未授權。
>


> **2026-10-26 P30-L4-B 最終 Android 類型標籤修補及 Artifact 鎖定**
>
> - 先前 PR #17 的 CI Run `40284806144` PASS，但新增顯示語義修正：`OFFICIAL_LIST_ACTID_BOUND_DATE_RANGE` 顯示 **「官方清單期間：YYYY-MM-DD～YYYY-MM-DD（實際開放以官方為準）」**，與詳情 `OFFICIAL_SINGLE_SESSION`、`OFFICIAL_MULTIPLE_SESSIONS_BOUNDS` 分開；`CKSMH_LIST_DATE_WITH_DETAIL_TITLE_CONFIRMED` source label 不再顯示機器碼。新 PR #17 HEAD **`d79de853c007ac965d02b56cc2e556f8ad5f1bff`**，只修改同一隔離 HTML，不觸碰正式 PWA。
> - 最終而且唯一供 Android 實機驗收的 Run **[40285154986](https://github.com/easonliu714/event_scraper_public/actions/runs/40285154986)** `completed/success`：14/14 synthetic tests、JS syntax、五筆詳情 HTTP200 + 五筆 actId 清單綁定、5/5 dates、3/5 unambiguous venues、5/5 summary、2 multi-session，44 Id parity、39 TWTC row exact parity、所有父證據 SHA 與 Android 四檔 `sha256sum -c` PASS。**最終 Artifact [12633104025](https://github.com/easonliu714/event_scraper_public/actions/runs/40285154986/artifacts/12633104025)**，archive `sha256:84e73813897dfe1b43a731552e3af7ade7e342d0bf68f7a8b49d546114847b70`，2026-11-09T07:20:29Z 到期。**舊 Artifact 12633399655 僅作為歷史，不得視為最終交付。**
> - 下一步：Android `127.0.0.1:8769` 真機驗證，使用者尚未回報；`P30_L4B_ANDROID_UAT=WAITING_USER`。舊已驗證 L7-D、世貿 FinTech、前兩輪 Android PASS 保留，`APP_DATA_PUBLISHED=false`，全部 PR 仍 Draft 未合併。
>


> **2026-10-26 P30-L4-B CKSMH 五活動詳情全數日期回填 Android UAT READY（正式候選，不是 Golden）**
>
> - 使用者提供 P30-L7-D Android `127.0.0.1:8768` 與世貿/聯卡中心兩官方頁的實機畫面，明確判定世貿科技展修補 PASS；因此接受 `P30_L7D_ANDROID_FINTECH_USER_SCREENSHOT_PASS`，但未取得整個 ZIP 的 Termux stdout，不擴張為全 19 平台或正式 PWA PASS。新缺口：中正紀念堂 5 筆原本只有 `LIST_ONLY`，官網已可見唐獎榮耀展 `2026/09/01 09:00～2026/10/30 18:00`／中央通廊與活動內容。
> - Source 新 [Draft PR #17](https://github.com/easonliu714/event_scraper_public/pull/17) `feat/eventradar-p30-l4b-cksmh-details` 堆疊在已接受 L7-D PR #16 HEAD `c18e3aa0b73039cd98f1c4107c6fe342611b16eb`；最終 Branch HEAD `688161678093d1a48159c30abc9807b63c59e36a`。僅四個異動路徑：新增 `scripts/p30_l4b_cksmh_details.py`、`tests/p30/test_l4b_cksmh_details.py`、`.github/workflows/eventradar_p30_l4b_cksmh_details.yml`，修改**隔離候選** `scripts/p30_l7a_smoke_index.html`。原 Source `docs/data.json` / `docs/index.html` / `scraper.py` Blob parity 保持。
> - 正式 GitHub Actions [Run 40284806144](https://github.com/easonliu714/event_scraper_public/actions/runs/40284806144) **completed/success**：14/14 Python 離線正反向測試、Node JS syntax、父 L7-D Artifact SHA、來源不可變 ID、四路徑差異、最後 ZIP SHA256 PASS。來源的 **五筆 CKSMH 詳情 HTTP 200 / 5 筆標題身分精確匹配**，官方清單 `/mocweb/reg/CKSMH/Query.list.ctr` 亦 HTTP 200 且 **5/5 actId+title exact-bound**；欄位改善：**日期 5/5、確定單一場地 3/5、官方摘要 5/5、多場次 2/5**。缺單一場地的兩筆保留「多場次：各場次地點請依官方明細確認」而非猜測。
> - CKSMH ActivityID `61004` 唐獎榮耀展已核對：2026/09/01～2026/10/30，場次時間 09:00～18:00，場地「中央通廊」，成功移除尾端無關的「圖片說明」圖片替代文字。ActivityID `51331`「自由花蕊（免費參觀）」的官網**詳情本身沒有場次日期**，故只在其活動 ID、標題同時匹配官方清單時，才按 `OFFICIAL_LIST_ACTID_BOUND_DATE_RANGE` 補入 `2025/11/24～2030/12/31`；應注意此為官方清單範圍，不等於每天均有獨立場次、實時開放或 Golden。
> - 複合 UAT candidate **44 原始身份不變，39 筆台北世貿資料完全 unchanged**（含先前 38 筆完整日期、金融科技展原訂 10/23～24、暫定改期 12/18～19、confirmed NULL），5 筆 CKSMH 才依證據回填。新 Android 8769 最終 ZIP [Artifact 12633399655](https://github.com/easonliu714/event_scraper_public/actions/runs/40284806144/artifacts/12633399655) archive digest `sha256:40a3095f845d07c14fd690ac27cd0ea66ed42d6bb78b75afc3415af14a18c641`，expires 2026-11-09T07:17:08Z；其它較早 Run 僅作開發驗證歷史，**以 Run 40284806144 唯一 ZIP 實測**。
> - Gate 判定：`P30_L4B_CKSMH_DETAIL_LIVE_HTTP=PASS_5_OF_5`、`P30_L4B_CKSMH_DATE_CANDIDATES=PASS_5_OF_5`、`P30_L4B_ANDROID_PACKAGE_CI=PASS`，但 `P30_L4B_ANDROID_UAT=WAITING_USER`；下個需使用者 Android Termux `sha256sum -c SHA256SUMS.txt`，執行 loopback `python -m http.server 8769 --bind 127.0.0.1`，驗證真機 5/39、日期、摘要、官方場次、場地註記、搜尋/詳情/外連和先前金融科技展資訊未回歸。
> - 治理護欄持續：PR #17 Draft 未合併、Source main 不動、`GOLDEN_ACCEPTED=0`、`APP_DATA_PUBLISHED=false`、`AUTO_HIDDEN=0`、`SOURCE_RUNTIME=DORMANT`；G5J/G5K 正式 19 平台、Pages/PWA writer、通知、排程、其餘 Repo 退役保持 OPEN/LOCKED，沒有自動聲稱結案。
>


> **2026-10-26 P30-L7-D 三官方 HTTPS 來源修復並達 Android 可驗證（PR #16 Draft）**
>
> - PR #15 L7-C 原本在 GitHub Runner 存取大會公告 `www.fintechtaipei.tw/Announcement/19` 時遭 `SSLError`，因 fail-closed 維持歷史 HOLD，未關閉 TLS verify、未迴避 WAF、未擅自宣稱日期已確定。2026-10-26 改建獨立 **[Source PR #16](https://github.com/easonliu714/event_scraper_public/pull/16)**（stacked on 使用者已驗收 L7-B PR #14 HEAD `05b30b9d8e57848edf6190b37d3b9fa8f1f58257`；僅四個範圍異動：增 `scripts/p30_l7d_official_fallback.py`、`tests/p30/test_l7d_official_fallback.py`、`.github/workflows/eventradar_p30_l7d_official_fallback.yml`，改**隔離** `scripts/p30_l7a_smoke_index.html`）。
> - L7-D 改用可信正式機構公開 HTTPS 證據：(A) `https://twtc.com.tw/exhibition_more.aspx?id=28255&p=home` 原訂 `2026-10-23～24`；(B) `https://www.tfsr.org.tw/information/187` 台灣金融服務業聯合總會確認延期，最終時間月底前公告；(C) `https://www.nccc.com.tw/wps/wcm/connect/zh/home/AboutNCCC/News/200261021-1` 財團法人聯合信用卡處理中心 10/21 公告延期至 `2026-12-18～19`。注意非 `www` 聯卡中心入口在較早診斷有 `NETWORK_ERROR`，改使用**真實官方 canonical www URL**，不得忽略 TLS 驗證。
> - 最終 CI Run [40281136558](https://github.com/easonliu714/event_scraper_public/actions/runs/40281136558) **completed/success**：三來源 `HTTP_OK 200` 全部成立；13/13 offline 正反測試、Node JS syntax、來源字串核對、舊 L7-B 44 筆父 Artifact SHA、原始 Source Pages 三 Blob、四檔差異 gate、五檔 SHA256（index、data、roles、diagnostics、README）全部 PASS。JSON 報告：`ORIGINAL 2026-10-23～24`、`TENTATIVE 2026-12-18～19`、`CONFIRMED=NULL`。該狀態代表 **官方機構公布的預計改期，與金融總會仍待正式確認的聲明相容**；不能由聯卡中心單一公告直接升級成完整 Golden 或正式售票日期。
> - 所有其他 43 筆活動身份與欄位不變；`44 IDs`、TWTC `38` 個先前官方詳情時間候選不變、五筆 CKSMH 不變、一筆 FinTech 顯示延期與獨立原訂/預定欄位。HTML 標籤與官方連結符合 XSS / URL 安全界線。**唯一 Android L7-D 最終候選 ZIP**：[Artifact 12632108815](https://github.com/easonliu714/event_scraper_public/actions/runs/40281136558/artifacts/12632108815)，archive SHA256 `a4a4cea091867b65d648273bb4420e943aaf264e750497459bbda2d1b5dbf3a6`，2026-11-09T06:40:23Z 到期。此前 L7-D CI Run `40280982817` 成功但聯卡中心仍無回應，非最後 Android 交付包。
> - Gate 狀態：`P30_L7D_OFFICIAL_3_SOURCE_CI=PASS`、`P30_L7D_ANDROID_PACKAGE=PASS`、`P30_L7D_ANDROID_REAL_UAT=WAITING_USER`。使用者先前 L7-A 7/7 與 L7-B 實機截圖 PASS 均保留。Source `main@fc4f963247d68eed29425808cc14e7250f312d05` 以及歷史正式 `docs/data.json`、`scraper.py`、`docs/index.html` 未改。PR #15 維持 Draft/HOLD、PR #16 為 Draft 未併入 main；`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`G5J/G5K=OPEN`，不得自行關閉或退役其他兩個 Repo。
>


> **2026-10-26 P30-L7-C FINTECH POSTPONEMENT ROLE ROOT CAUSE／使用者 L7-B 真機回報**
>
> - 使用者已提供 P30-L7-B Android `127.0.0.1:8767` 截圖並表示此階段驗證皆符合預期：完整年份日期（電器空調影音大展 2026/11/06～11/09、展昭世界貓咪博覽會 2026/10/08～10/11 等）、39/44 TWTC 畫面與金融科技展延期提示皆可見。記錄 `P30_L7B_ANDROID_USER_SCREENSHOT_ATTESTED_PASS`；依回報範圍認列，不擴張為全平台 Golden 或正式 G5K。
> - 唯一原先 `LIST_DETAIL_PERIOD_CONFLICT` 不是 TWTC HTML 格式差異：官方詳情 `https://twtc.com.tw/exhibition_more.aspx?id=28255&p=home` 確實在標準「展出日期」欄顯示 **原訂 2026/10/23～10/24**，但 `https://twtc.com.tw/exhibition?p=home` 的該筆表格列改成 **延期未定**。P30-L4-A `raw_period_matches()` 遇「延期未定」直接回 False 並阻止把已失效日期寫成活動生效日期；守門合理，但原訂日期 role 被遺漏。
> - 大會公告 `https://www.fintechtaipei.tw/Announcement/19`（2026/10/20）稱「預定延期至 12/18～12/19，確切調整時間將於 10 月底前公告」。應建模 `originalDate=2026-10-23/24`、`tentativeDate=2026-12-18/19`、`confirmedDate=NULL`、`status=POSTPONED_PENDING_FINAL_CONFIRMATION`，保留原定/暫定之來源連結與時間語義，**不得把暫定當正式確認或改成有效售票日期**。
> - 新 Source [PR #15](https://github.com/easonliu714/event_scraper_public/pull/15) Draft stacked on PR #14，分支 `feat/eventradar-p30-l7c-postpone-dateroles`；11/11 離線日期角色／HTTP allowlist／負例測試 PASS。Run [40275813585](https://github.com/easonliu714/event_scraper_public/actions/runs/40275813585) **completed/failure = CORRECT HOLD**：TWTC 官方詳情 `HTTP_OK`，但大會公告在 GitHub Runner `NETWORK_ERROR: SSLError`，依 Fail-Closed 不產生新 Android candidate、不將日程寫入任何正式 JSON。保留只含診斷之 Artifact [12630675096](https://github.com/easonliu714/event_scraper_public/actions/runs/40275813585/artifacts/12630675096)。**絕不可關閉 TLS 驗證、代理繞過或假冒 HTTP 200 將 HOLD 當 PASS**。
> - 下一個 L7-C Gate：以安全可讀的官方 HTTPS（或後續官方正式確認更新）補足第二來源真實證據；SSL 未解前 PR #15 DRAFT/HOLD，使用者已 PASS 的 PR #14 SHA `05b30b9d8e57848edf6190b37d3b9fa8f1f58257` 與 PR #12 7/7 均不回退。正式 PWA/Golden/通知/排程/發版/其他 Repo 退役繼續 LOCKED。
>


> **2026-10-26 P30-L4-A / L7-B 實際 CI 結案證據（只有候選 Gate PASS；Android L7-B 尚未實測）**
>
> - P30-L4-A GitHub [PR #13](https://github.com/easonliu714/event_scraper_public/pull/13) HEAD `b1651e6faf41d48eed8c42ef13e8aae91dc19702`，Run [40273199767](https://github.com/easonliu714/event_scraper_public/actions/runs/40273199767) **SUCCESS**，13/13 離線測試 PASS。原始 TWTC 39 筆候選的 39 個官方詳情皆受控 GET，經 Event ID、官方標題、完整 YYYY/MM/DD、清單 MM/DD 對照，**38 筆 DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE、1 筆 LIST_DETAIL_PERIOD_CONFLICT**。唯一 HOLD 為「2026台北金融科技展【展覽延期】」，原清單 `延期未定`，不得擅自發布活動日期。L4-A 來源證據 Artifact `12629371018`，非 Golden。
> - 新 P30-L7-B GitHub [PR #14](https://github.com/easonliu714/event_scraper_public/pull/14) HEAD `05b30b9d8e57848edf6190b37d3b9fa8f1f58257`，base 為 **先前使用者已驗收的 PR #12 HEAD** `76171eae8352818721a5480d18a1cc4c0e283ccc`，不同分支、不改原 PR #12。4 條精確異動：新增 `scripts/p30_l7b_date_overlay.py`、`tests/p30/test_l7b_date_overlay.py`、`.github/workflows/eventradar_p30_l7b_date_uat.yml`；修改候選 UI `scripts/p30_l7a_smoke_index.html`（顯示完整年份、將技術狀態翻譯為使用者易懂文字、延展活動顯示「展覽延期／日期未定」）。
> - L7-B native Actions 最終 Run [40273949404](https://github.com/easonliu714/event_scraper_public/actions/runs/40273949404) **SUCCESS**，10/10 離線負例、Node JS syntax、舊 L7-A Immutable SHA、L4-A evidence lineage、44 筆活動 ID parity、**38 完整日期＋1 延期 HOLD**、正式 Git Blob、SHA manifest 四檔一致全部 PASS。最終唯一 Android UAT ZIP Artifact [12628754512](https://github.com/easonliu714/event_scraper_public/actions/runs/40273949404/artifacts/12628754512)，Archive digest `sha256:4fc3929bc642089d821e1a1a1bbd8535358572c6ebbf36cca170576bb728988f`，2026-11-09T05:23:32Z 到期。前一個 L7-B Run 40273848296 僅保留 CI 歷史，非最終交付。
> - **Gate 判定**：`P30_L4A_SOURCE_DATE_EVIDENCE=PASS_38_OF_39`、`P30_L7B_ANDROID_BUILD_CI=PASS`、`P30_L7B_ANDROID_UAT=WAITING_USER`；舊 `P30_L7A_ANDROID_LOCAL_SMOKE=USER_ATTESTED_PASS_7_OF_7` 不回退；`R3C_O3_GOLDEN_ACCEPTED=0`、`G5J=OPEN`、`G5K_FORMAL_LIVE_19_PLATFORM=OPEN`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`。新資料未進 main Pages；PR #13/#14 保持 Draft，禁止未授權合併。
> - Android 下一步：下載唯一 Artifact `12628754512`，在手機 Termux 相同目錄 `sha256sum -c SHA256SUMS.txt`、`python -m http.server 8767 --bind 127.0.0.1`，Chrome 開 `http://127.0.0.1:8767/`；驗證完整年份與展覽延期、總 44 與來源 5/39、其餘來源/類別/官方連結、無回歸。回報前不得宣稱 P30-L7-B Android 真機 PASS。
>


> **2026-10-26 P30-L4-A 官方詳情完整年份修復：使用者 Android 截圖揭示的資料缺口**
>
> - 使用者實機截圖顯示：L7-A 7/7 UI Smoke PASS 同時，TWTC 部分活動仍顯示「11/06～11/09（年份待核對）」，但同一活動官方詳情清楚列「展出日期：2026/11/06～2026/11/09」，另有「2026展昭世界貓咪博覽會」2026/10/08～10/11 等樣本。這是**資料解析覆蓋缺口**，不是 UI 無法顯示年份；舊 L3-A/PR #11 只抽查第一筆詳情，L7-A 因而僅有部分完整日期。
> - 新 Source PR #13：https://github.com/easonliu714/event_scraper_public/pull/13；L4-A Draft 分支堆疊於 L3-A PR #11 HEAD a63baf94baa46853381d3e791c9b1ff62b771b09，恰好新增三檔：scripts/p30_l4a_twtc_detail_dates.py、tests/p30/test_l4a_twtc_detail_dates.py、.github/workflows/eventradar_p30_l4a_twtc_details.yml。固定以 GitHub Run 40270383643 下載既有 39 筆 L3-A Artifact，按官方詳情 ID／HTML 標題／清單 MM/DD 三重身分證據核對後才採納完整年份展期；不得由現在年份、活動名稱年份或其他來源推測。
> - 安全限制：最多 40 筆官方詳情（本次固定 39 筆）、無重試、每次至少 1.5 秒、僅 twtc.com.tw/exhibition_more.aspx 公開 HTTPS、總預算 240 秒、無正式資料／頁面／通知／排程寫入。CI PASS 僅表示可生成日期候選證據，非 Golden、非發布，也非正式多來源全面取得。
> - **下一個 L7-B Gate** 須引用 L4-A 成功 Artifact 與已完成 L7-A 的 44 筆固定資料，在隔離分支以可溯源日期回填重建 Android Smoke；不能修改或使舊 PR #12 已通過的 7/7 Android 驗收失效。保留 G5K 全平台正式 UAT、G5J 可逆有效性、Golden 與來源缺口 OPEN。
>


> **2026-10-26 P30-L7-A Android USER-ATTESTED 7/7 PASS（正式使用者回條；候選本機 Smoke）**
>
> - 使用者於本對話親自回報：**(1)** 首頁候選 44 筆，**(2)** 中正紀念堂 5 筆、台北世貿 39 筆來源篩選，**(3)** 關鍵字搜尋與類別篩選，**(4)** 詳情開關與版面無重疊，**(5)** 未知日期/票價/票況正確提示，**(6)** 官方來源連結能開啟。依原始測試表七項計數：首頁44、CKSMH5、TWTC39、搜尋類別、詳情UI、未知欄位、官方連結 **7/7 PASS**。
> - 驗收身分綁定 PR #12 `76171eae8352818721a5480d18a1cc4c0e283ccc`、CI Run `40271164263` completed/success、Android 專用 Artifact `12628147623`。使用者結果足以將 `P30_L7A_ANDROID_LOCAL_SMOKE=USER_ATTESTED_PASS`；原 Termux 指令逐行輸出與手機完整 Console 未另行提供，不擴張為整站 Golden 或正式 End-to-End。
> - **不變之 HOLD**：`R3C_O3_GOLDEN_ACCEPTED=0`、`G5J_VALIDITY=OPEN`、`G5K_FORMAL_LIVE_19_PLATFORM_UAT=OPEN`、`SOURCE_RUNTIME=DORMANT`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`。PR #8 / #12 仍 Draft，不 Merge、不覆蓋原始 Pages JSON；後續工作轉至 P30-L3-B 三個 HTTP 200 / LIST=0 平台（FamiTicket、ibon、StrollTimes），保持其他 Gate frozen。
>


> **P30-L7-A Android SHA Manifest 2026-10-26 最終可實機回條**：PR #12 修復了 ZIP 內 `SHA256SUMS.txt` 的可攜式相對路徑（原驗證包 SHA manifest 不應被視為 Android 最終交付）；新 HEAD `76171eae8352818721a5480d18a1cc4c0e283ccc`，Actions [40271164263](https://github.com/easonliu714/event_scraper_public/actions/runs/40271164263) Job `121404074474` **SUCCESS**，真實 candidate 44 筆；CI 在 Artifact 打包前實際 `cd p30-smoke && sha256sum -c SHA256SUMS.txt` 三檔 `index.html: OK` / `data.json: OK` / `README.txt: OK`。**唯一要交付 Android 的最終包**：[Artifact 12628147623](https://github.com/easonliu714/event_scraper_public/actions/runs/40271164263/artifacts/12628147623)，Archive digest `sha256:da198b4c6700dd6d824380f429a324c6421e896933f42f4e679c001d0026ed73`，到期 2026-11-09T04:51:14Z。先前 Run 40270957865 僅保留 CI 歷史，不作 Android 最終下載來源。**ANDROID_UAT=WAITING_USER_LOCAL**、`PUBLISHED=false`、正式 main 未改。
>


> **P30-L7-A Android 本機候選驗證 Gate 2026-10-26｜READY FOR USER SMOKE TEST（不是 Golden／正式 G5K）**
>
> - 新 Source [PR #11](https://github.com/easonliu714/event_scraper_public/pull/11)（L3-A TWTC，base P30-L1 PR #7，3 新增檔）Head `a63baf94baa46853381d3e791c9b1ff62b771b09`；Run [40270383643](https://github.com/easonliu714/event_scraper_public/actions/runs/40270383643) **SUCCESS**，11/11 離線測試 PASS，官方 `https://twtc.com.tw/exhibition?p=home` HTTP 200，**39 個展覽清單候選**，詳情抽樣 `DETAIL_DATE_CANDIDATE`（僅一筆，非 Golden）。Artifact `12628056468`。
> - 新 Source [PR #12](https://github.com/easonliu714/event_scraper_public/pull/12)（L7-A，從正式 `main@fc4f963247d68eed29425808cc14e7250f312d05` 建獨立 Docs/PWA 未發布分支，4 新增檔），HEAD `93b0ea012c537ddc8f6a679ef7266cc5a405396d`；Run [40270957865](https://github.com/easonliu714/event_scraper_public/actions/runs/40270957865) **SUCCESS**，8/8 離線資料合約測試、Node JS 語法檢查、原始 `docs/data.json` / `docs/index.html` / `scraper.py` Blob parity PASS。
> - L7-A Actions 僅唯讀下載 CKSMH Run `40269917573` 與 TWTC Run `40270383643` 已完成 Artifact，**5 + 39 = 44** 筆去重後、來源綁定之最新受控候選 JSON（僅兩來源單次抽樣，不是 19 平台全部活動）。用此候選資料打包靜態 `index.html`、`data.json`、`README.txt`、`SHA256SUMS.txt` 至 Artifact [12629030170](https://github.com/easonliu714/event_scraper_public/actions/runs/40270957865/artifacts/12629030170)，2026-11-09T04:48:45Z 到期。下載只讀，不上傳 `docs/`、不更新正式 PWA。
> - Android Smoke 必須由使用者於同支手機 Termux 解壓 Artifact、`sha256sum -c SHA256SUMS.txt`，透過 `python -m http.server 8766 --bind 127.0.0.1` 後在瀏覽器開 `http://127.0.0.1:8766/`；檢查 44 筆、來源/類別/關鍵字篩選、詳情視窗/關閉、官方連結、未知日期/票況與手機版面、Console 無錯。**實機未回報前 UAT=NOT_ATTESTED**；取得真機 PASS 也僅為兩來源候選 Smoke，不能取代 R3C-O3/G5J/G5K 正式內容驗證。
> - 新 19 平台來源品質 L2～L6 仍 OPEN；除 CKSMH、TWTC 外不宣稱其它網站品質已修正。Source PR #1 Cloud HIGH_RISK_HOLD，PR #7/#9/#10/#11/#12 均未授權 Merge/Ready，Source main 不變。其他兩 Repo 仍保留，資料/排程/通知/正式部署依舊 LOCKED。
> - **下一關卡**：Android 候選 smoke UAT 回條；同時持續 L3-B FamiTicket/ibon/StrollTimes HTTP200/LIST0 診斷、L4/L5 Golden/日期角色；將本 PR #8 的兩份治理文件經審查/核准 Merge main 後，才可宣稱正式治理 main 已同步。
>

> **2026-10-26 L2-B CKSMH 實際來源驗證（PR #10 Draft；未併 main）**：GitHub Run [40269917573](https://github.com/easonliu714/event_scraper_public/actions/runs/40269917573) `completed/success`；Job `121400294421` 全 Steps SUCCESS；11/11 離線測試 PASS。中正紀念堂官方 `https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr` HTTP 200 並解析 **5 筆活動清單候選**；`https://event.culture.tw/CKSMH` HTTP 200 但直接活動 anchor 候選 0；取樣第一筆詳情 HTTP 200（**不代表日期/身份 Golden**）。Runner output 只保存 candidate+diagnostics Artifact `12627554765`，不寫正式資料。PR #10 HEAD `da451c9537a05ba23db094533cc9887f7db8b6bc`，堆疊於 PR #9，三檔隔離變更、正式原有 JSON/UI/Runtime Blob parity 保持。L2-B **CKSMH 來源回應與有限清單可達性 PASS**，L4 內容正確性仍 OPEN。原 404 路徑不得再作為唯一來源。
>

> **L2-B 入口候選（2026-10-26）：** 已由官方公開網站的網頁索引檢視確認中正紀念堂活動可經 `https://event.culture.tw/CKSMH` 與 `https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr` 存取活動資料；原 L1 使用的 `https://event.culture.tw/mocweb/reg/CKSMH/` 曾返回 HTTP 404。上述為**合法公開候選入口**，尚未以既有 GitHub Python Runner 在相同環境重驗，故 **L2-B 候選／NOT_GATED**，不是已修復或已寫入 Parser。禁止把 404 當成全部活動失效。參考：`https://event.culture.tw/CKSMH`（官方站）、`https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr`（官方活動查詢頁）。
>

> **SRC-P30-L2-A 2026-10-26 CI 完成（候選分支 PASS；PR #9 仍 Draft）**
>
> - Source PR [#9](https://github.com/easonliu714/event_scraper_public/pull/9) 為**堆疊 PR**：`feat/eventradar-p30-l2a-offline-triage@7fd14010f5dbc3ef383919ee67eb21283904afe2` → PR #7 `feat/eventradar-p30-live-diagnostic@959324cb3bad8f56fb411b7cfb6de2a294f18850`；僅三新增檔，未改正式 Source、UI、JSON、通知、排程及部署，未合併。
> - 原生 Actions Run [40266605126](https://github.com/easonliu714/event_scraper_public/actions/runs/40266605126) `completed/success`，Job `121390275278` 所有階段 SUCCESS；9/9 offline unittest PASS；以 GitHub Actions 唯讀下載既有 L1 Artifact `12600795314`，`diagnostics.json` SHA256 `91a08e022ee080a3435229eb6393d656c97104d78c3a46a07b31a2423be3e4ff`；重播驗證 19 / 15 HTTP_OK / 11 LIST 非空 / 338 候選，L2 HTTP=4、L3 清單空=4、L4 可取詳情候選=11。
> - 確切源端 HTTP（**2026-10-25 L1 單次觀測，不代表今天即時狀態**）：KKTIX **403**、拓元售票 **403**、BeClass **403**、中正紀念堂 **404**；FamiTicket / ibon / 台北世貿 / StrollTimes 均 **HTTP 200 但清單 0**。HTTP 403 非活動無效證據，404 亦不能直接證明來源下架。
> - PR #9 Artifact `eventradar-p30-l2a-offline-triage` ID `12626960522`（2026-11-09 到期），報告只含來源觀察/分層/雜湊，`NO_NEW_HTTP=true`、`APP_DATA_PUBLISHED=false`，不構成 Golden 或正式功能啟用。
> - **下一工作 P30-L2-B**：只以已公開官方入口核對中正紀念堂 404 的實際路徑；其餘 403 按 BLOCKED 保留，逐平台可用證據再決定替代合法公開清單，禁止繞過門檻。接 P30-L3 四個 HTTP 200/清單 0 的可重播 HTML/JSON 負例。PR #9 的 CI PASS 與 PR #7 的 live diagnostic PASS 不等於其他來源品質 PASS，更不等於可合併、正式上線或刪除舊庫。
>

> **2026-10-26 SRC-P30 L2-A 治理增量（仍為 PR #8 Draft；未進 main）**
>
> - 本輪 GitHub 重新核對：Source main `fc4f963247d68eed29425808cc14e7250f312d05`、Preview main `03e515d65e827d5ed67fe341d079907a96bf784a`、Legacy ShowNews main `85fed3e85ff5deff479a85b8d692aa9e6d2bdcad`；唯一最後保留 Repo 已由使用者明定為 `easonliu714/event_scraper_public`，其他兩庫只作來源證據及將來受控退役。
> - Source PR #6、#7、#8 皆仍 OPEN/DRAFT/UNMERGED，Source PR #1 高風險 HOLD、#2 原生 CI PASS 但程式仍 DORMANT。PR #6 獨立 CI Run `40195542386` SUCCESS；PR #7 單次 Run `40196442965` SUCCESS；#8 為 Docs-only Draft，P29 在其上的 skipped 並非 P30 L2 CI 成功。
> - 從 PR #7 實際 Job `121178174230` 的 2026-10-25 Runner log 獨立讀回：19 平台中 15 HTTP_OK、4 HTTP_ERROR；11 平台有非空清單、8 平台無清單；338 個限量候選；11/11 取樣詳情 HTTP_OK（**不是欄位 Golden**）。
> - HTTP_ERROR 平台：**KKTIX／拓元售票／BeClass／中正紀念堂**。HTTP_OK 卻 LIST=0：**FamiTicket／ibon／台北世貿／StrollTimes**。L2-A 應先對四個 HTTP_ERROR 逐筆取 **真正狀態碼／轉址**，不可單以 `HTTP_ERROR` 推定為 403 或站方封鎖；L3 優先處理另外四個 LIST_EMPTY／JS_RENDERED，不可把 HTTP 200 當成有活動清單。
> - 本輪決定：優先序固定 `HTTP accessible → valid LIST → DETAIL identity → field evidence → classification → fresh candidate JSON → isolated PWA UAT → authorized publish → repository retirement`。不把歷史 Source 8,436／Preview 9,850 當作新發布資料，亦不得直接刪除、改寫現行 Pages JSON。
> - **L2-A 必須以同一份 Run Artifact `12600795314` / `diagnostics.json` 取來源證據**（必要時再進行受控、限流、同平台目的明確的 GET）；下階段產物為版本化 source inventory 與 offline fixtures/test，先改善真實回應再改善 selector。將現有成功來源視為可繼續開發的候選，不因其他來源 BLOCKED 中止全局。
> - 退役原有 Preview/ShowNews Repo 尚未授權；必須先核實外部 Pages/Render、舊網址、manifest/PWA scope、rollback。任何正式資料 Writer、schedule、通知、Auto-Hide、Merge/ReadyForReview 均維持 LOCKED。
>


> **最新增量提案｜2026-10-25 P30 即時來源品質 Roadmap（Docs-only Draft；尚未合併 main）**
>
> 此章是以 GitHub 即時讀回及使用者最新要求編製的「後續治理變更候選」。原下方 SRC-P29 候選、P25/P26 等字樣都是歷史時點描述，**不代表目前 P29 未完成**。此章經獨立文件 PR 合併後方成為 main 上最新正式進度；未合併前 Source main 仍以舊正文加上 GitHub 遠端事實解讀。原文逐位元組保留。
>
> 最新已核對權威：Source main `fc4f963247d68eed29425808cc14e7250f312d05`；Preview main `03e515d65e827d5ed67fe341d079907a96bf784a`；ShowNews main `85fed3e85ff5deff479a85b8d692aa9e6d2bdcad`。
>
> **業務要求調整**：Source `docs/data.json` 歷史 8,436 筆與 Preview `data.json` 歷史 9,850 筆均不作為下一次 PWA 候選活動清單；優先重新取得現時官方來源資料，以「HTTP 回應成功 → 有效活動清單 → 詳情成功 → 重要欄位可信」分段改善。不得因「可忽略舊 JSON」直接刪除 Git 歷史、覆蓋現有 Pages 資料或啟動單一正式 Writer；舊檔刪除/入口切換另設可復歸發布 Gate。

## SRC-P29 完成／SRC-P30 最新決策：2026-10-25 增量狀態

| 物件 | 即時核對的身分及 Gate | 決策 |
| --- | --- | --- |
| SRC-P1～P28（含 Android Gates） | 既有承接快照及實機驗證證據 PASS | 凍結保留，不重跑；不得以新對話推翻 |
| SRC-P29 | Source PR #5、Preview PR #2 已 MERGED；各 main 為上方兩個固定 SHA | COMPLETE，不重跑 |
| P20 Source PR #2 | OPEN/DRAFT，HEAD `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0`；原生 `source-offline` check SUCCESS，Run `40156884831` | 程式仍 DORMANT，未授權 Merge |
| P20 Preview PR #1 | OPEN/DRAFT，HEAD `b55b3673088b6df7bfe51f04d8d82b8e7616324f`；原生 `ui-offline` check SUCCESS，Run `40156894950` | UI Android/Synthetic 驗收歷史保留，未授權 Merge |
| Source PR #1 | OPEN/DRAFT，HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee` | Cloud Scheduler / writer HIGH-RISK HOLD |
| SRC-P30 PR #6 | OPEN/DRAFT，HEAD `1402df1bd32a1fafaa6b1842c54b796f977ea2c7`；隔離舊 9,850 筆快照 CI `40195542386` SUCCESS | **歷史驗證保留，但已被最新「重新抓取優先」業務決策取代**；不得 Merge |
| SRC-P30 PR #7 | OPEN/DRAFT，HEAD `959324cb3bad8f56fb411b7cfb6de2a294f18850`；一次性 Runner `40196442965` completed/success | **P30-L1 診斷工具 Gate PASS；各來源品質尚未 PASS；未進正式 Runtime** |
| P30 首輪結果 | 19 平台取樣；15 HTTP OK；11 平台有清單候選；338 筆新清單候選；11 筆詳情抽樣 HTTP OK | 僅 **診斷與候選資料**，不是完整抓取／官方 Golden／可發布資料 |
| Source P29 workflow 在 P30 PR | 對 P30 PR #6/#7 為 SKIPPED（非白名單中的 P20 工作） | 合乎原限制；不得以 skipped 當作 P30 CI PASS 或 P29 Gate 失效 |

### 最新授權範圍與證據語義

- `CODE_EXISTS` ≠ `CI_SUCCESS` ≠ `HTTP_OK` ≠ `LIST_EXTRACTED` ≠ `DETAIL_EXTRACTED` ≠ `FIELD_VERIFIED` ≠ `GOLDEN_ACCEPTED` ≠ `ANDROID_UAT_PASS` ≠ `PUBLISHED`。
- 首輪 P30-L1 使用僅讀、一次性、限流的 19 平台清單入口與最多每平台 1 筆詳情抽樣；輸出 GitHub Run Artifact `eventradar-p30-fresh-diagnostic`（Run `40196442965`；Artifact ID `12600795314`，保留期間依 Actions 實際顯示）；`candidate.json` 和 `diagnostics.json` 不進 `docs/data.json`。
- 來源 HTML 200 不保證 JavaScript 動態清單可解析；403、429、404、轉址異常等必須獨立呈現，不能重試繞過網站限制。2026-10-25 的 338 筆為限額抽樣清單；**不得以 338 判定全面覆蓋率或事件真實性**。
- 使用者容許部分日期、票價、地點、描述未解析時**顯示官方連結 + 明確缺值／以官方為準**，但不得猜測或把售票日期、清單日期直接當活動場次日期；未知票況一律 UNKNOWN。
- 維持 `SOURCE_RUNTIME=DORMANT`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`；禁止自動隱藏、正式爬蟲寫入、通知、排程、未核准發版。

### SRC-P30 多階層後續 Gate Roadmap（新工作優先序）

```text
EventRadar Taiwan / SRC-P30 SOURCE-FIRST ROADMAP
├── P1～P29 [歷史 PASS / FROZEN; 不重做]
├── P30-L1 即時診斷基線 [TOOL/ONE-SHOT RUN PASS; SOURCE QUALITY STILL OPEN]
│   ├── GitHub 唯讀權威、P20 PR HEAD、既有 Pages/data Blob [PASS]
│   ├── HTTP → 清單 → 詳情 → 欄位分層觀察 [RUN 40196442965 SUCCESS]
│   └── 19 平台 / 15 HTTP OK / 11 有清單 / 338 候選 / 11 詳情 HTTP OK [非 Golden]
├── P30-L2 可達性與安全來源入口 [NEXT / OPEN]
│   ├── L2-A HTTP 403/404/429/Timeout/Redirect/Content-Type 與現行 URL 分類
│   ├── L2-B 只更正官方公開入口/允許的轉址與網站已公開的清單來源；不能繞過限制
│   └── L2-C 每平台固定官方 URL、HTTP 成功/失敗證據、HTML fixture、變更前後差異
├── P30-L3 活動清單可靠取得 [OPEN]
│   ├── HTTP 200 但 0 筆：診斷 JS 渲染、入口與選擇器飄移，不宣稱 PASS
│   ├── 逐平台 URL 白名單、活動明細連結驗證、標題非雜訊、去重、分頁上限
│   └── 平台未通過可顯式 DEFERRED；可用平台不得被不良來源污染
├── P30-L4 詳情成功與來源身分 [OPEN]
│   ├── 每平台先抽樣，將 HTTP、Event URL／canonical／JSON-LD 身分分離
│   ├── 多場次、集合頁、轉址、缺詳情、票種/資格特殊頁以 HOLD/UNKNOWN 表示
│   └── 經個別來源 Gate 後再受控擴大詳情範圍，禁止無上限全站抓取
├── P30-L5 欄位解析品質 [OPEN]
│   ├── title / canonical official_url / event date vs sales window / location / price / description
│   ├── confidence + evidence source + parsed role + missing reason，避免推測
│   └── UI 顯示摘要與「以官方為準」；缺部分欄位不強迫丟棄有用活動
├── P30-L6 分類、去重、有效性 [OPEN; 映射 G5J]
│   ├── 來源特定類別與非活動判定、URL/活動身分去重、多場次分流
│   ├── ACTIVE / EXPIRED / NON_EVENT / SOURCE_GONE / UNCERTAIN 可逆狀態
│   └── 403/404 或單次失效不可自動下架；AUTO_HIDDEN=0 直到正式授權
├── P30-L7 新鮮候選 JSON 資料契約／官方 Golden [OPEN; 映射 R3C-O3]
│   ├── 新 run_id、取得時點、來源網址、品質報告、SHA、JSON schema、覆蓋統計
│   ├── 只存隔離 Artifact / candidate 路徑；舊 8436/9850 不混入新集
│   └── 人工官方 Golden 签認另行 Gate；缺證據明確 HOLD
├── P30-L8 隔離 PWA / Android 真實 UAT [OPEN; 映射 G5K]
│   ├── 資料欄位/篩選/詳細頁 UI、來源與未知欄位清楚標示
│   ├── 先隔離 URL 與保護正式路徑，再核准部署/Android 真機比對
│   └── 原 P20 Android Gate 繼續有效，但不能代替「新資料」的 G5K 驗收
├── P30-L9 正式發布／單一 Writer [LOCKED]
│   ├── R3C-O3、G5J、G5K、Rollback、PR review、來源合法性/權限條件
│   └── 經另外授權才可資料替換、Schedule、通知、正式 Pages 切換
└── P30-L10 三 Repo 收斂 [LOCKED; 原 P30-G2～G4]
    ├── Source 為唯一程式/CI/治理/資料/PWA 權威；ShowNews 純函式擇優搬移
    └── Preview / ShowNews 外部 Render 或其他部署依賴查明、轉址/安裝/回復核實後
        另行授權才可 Archive；永不在本 Gate 自動 Delete Repo
```

### 分段驗收判定（可量測，但沒有捏造達成率）

| 層級 | 每平台最小證據／候選 PASS 準則 | 未通過時 |
| --- | --- | --- |
| L2 HTTP | 來源/取得時點、原始與最終 URL、HTTP code、HTML 型別、redirect 與 byte digest；阻擋不偽裝成功 | BLOCKED/HOLD + 原因 |
| L3 清單 | 來源身分合法、活動 URL/title 有值、規則不吸入導覽雜訊、URL 去重且有合成負例 | LIST_EMPTY/SELECTOR_HOLD |
| L4 詳情 | 有一組以上可複驗的官方詳情樣本及身分綁定；多場次/集合頁單獨分類 | DETAIL_UNKNOWN/HOLD |
| L5 欄位 | 核心欄位逐一標來源證據、角色/時間語義及未知狀態；不推定售票中 | FIELD_PARTIAL/UNKNOWN |
| L6 有效性 | 可逆 ledger、負向測試；無官方證據不自動下架 | UNCERTAIN（保留顯示/待查） |
| L7 JSON | 每輪完整 JSON schema、唯一 URL、來源溯源、候選 vs Golden 隔離、SHA/統計 | DATA_HOLD |
| L8 PWA | Synthetic + 瀏覽器 + 真機 UI／路徑/存取權限驗收；未核准不能上 Pages 正式入口 | UAT_HOLD |
| L9 發布 | 人工 Golden、G5J/G5K、單 writer、復歸和變更授權全到位 | RELEASE_LOCKED |

**下個具體任務：START P30-L2-A。** 不再重跑成功的 19 平台原樣一次性診斷；基於 Run `40196442965` 的 `diagnostics.json` 做「HTTP 非 200 優先，HTTP 200 卻無清單次之」定點修正。先建立可重播的 HTML/HTTP 正負案例與來源白名單表，分開記錄穩定來源和網站限制；未取得可用合法存取途徑的平台維持 HOLD，不妨礙其他平台的受控進度。

**後續協作規範**：每輪以 GitHub 最新三 Repo HEAD → 兩治理 MD 最新章節 → Open PR/Actions/Check Run → 現有 Artifact → 最小必要 Diff 為序；Remote main 校驗、Docs-only/Code-only 變更分流、Draft PR、獨立 Read-back；未另授權不得 Merge、Ready for Review、清除舊 JSON、正式寫入/發布/通知/封存 Repo。以上數字均為 2026-10-25 診斷時點，不是今日持續即時狀態。

---


> **SRC-P29 受控 PR CI 候選｜2026-10-25（Asia/Taipei）**
>
> 本段為新 CI 分支上的候選；未合併前不取代 main 正式治理權威。P24／P25／P26 以下歷史全文保留。
> 最新遠端唯讀核對：Source main `63eb062295757983cf51c2ccc51d9ba039391e93`；Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`。
> SRC-P27 已由 Source PR #4 一般 Merge Commit 完成；SRC-P28 Android PASS 依使用者交接保留。本輪再次讀回 P20 兩個 HEAD 與當時 API 所報 Merge SHA，Check runs 均為 0，仍為 NOT_ATTESTED。
> SRC-P1～P28 不重啟。方案 B：原生 `pull_request` CI；不發布 P28 外部 Commit Status 候選。

### SRC-P29 實作與驗收邊界

- Source 新增 `.github/workflows/eventradar_source_p29_pr_ci.yml`；Preview 新增 `.github/workflows/eventradar_preview_p29_pr_ci.yml`，各從上述 main 建立獨立 `ci/eventradar-<source|preview>-pr-ci-p29` 分支與 Draft PR。
- 沿用 P22/P23 Source Python AST + 兩組離線 parser suite、Preview 九個合成角色/escaping/modal/JS 語法測試；不改應用函數或測試內容。移除已過期的 P22 remote main SHA 斷言，保留原始 P20 父 commit、精確五新增/單一 index Diff 與固定 P20 HEAD。
- 唯一事件：`pull_request`，base `main`，types `opened/synchronize/reopened`。唯一 token 權限 `contents: read`；checkout 不保留憑證；每 PR concurrency、10 分鐘 timeout、標準 `ubuntu-latest`。只允許同 Repo 指定 P20 PR 或 P29 bootstrap 分支；Source PR #1 不執行此 job。
- 分別輸出觸發 PR HEAD、event base SHA、GitHub 合成 Merge SHA、workflow SHA 與被測 P20 HEAD。Check Run 的 `head_sha` 必須由 GitHub API 獨立讀回，禁止從 checkout ref 推定。
- P29 Draft PR 的 native CI（若觸發）只證明該 P29 PR 工作流程可執行；其固定 P20 測試不等於既有 P20 PR 的原生 Check。遠端 Run/Job/Check 結論須以實際讀回為準，目前本文件不預先宣稱成功。
- `pull_request` 從事件關聯的 Merge ref 取得 workflow，並非所有 PR Workflow 都必須先存在 default branch。獨立 P29 PR 不會為既有 P20 PR 自動補發事件。在保持 P20 HEAD/五檔/單檔不變的路線下，須另行授權把 CI Workflow 合併 main，再對既有 P20 PR 觸發允許的事件並讀回證據；本輪不合併、不開關既有 PR。
- Source PR #1 `26888422e48634d9729d2deea67b7996a5d1e4ee` 維持 Open/Draft/Unmerged、Cloud Scheduler/writer HIGH_RISK_HOLD；Source PR #2 `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0` 與 Preview PR #1 `b55b3673088b6df7bfe51f04d8d82b8e7616324f` 維持原 HEAD、Draft 與精確 Diff。
- 禁止活動網站抓取、JSON 寫入、正式部署、通知、排程與自動合併。維持 `GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 APP_DATA_PUBLISHED=false SOURCE_RUNTIME=DORMANT`。R3C-O3 Golden、G5J、G5K 另案 OPEN/HOLD。
- 下一階段：審查 P29 Draft PR 與原生 CI 證據，另行取得 main 合併與既有 P20 事件觸發授權；此 CI 階段不需要 Android 實機驗證。

來源：[GitHub workflow 事件解析](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows)、[pull_request 語義](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)。

---

> **權威快照：2026-10-24（Asia/Taipei），SRC-P25 Merge 已驗證。** Source Repo `main` = `a8d21d2e6aa056a13d5eb9de3d32920d11d4f740`；[Docs PR #3](https://github.com/easonliu714/event_scraper_public/pull/3) 已 `MERGED`，Merge Commit 同上，雙 Parent 為 `6004754f90d551cdb0cdb91a3e04b42c04f45f48` 與 `145189c19e2a58207fc1dc77ca558cb347e7bcca`。下文保留 P24 合併前原始快照作歷史證據，不得用歷史 `GOVERNANCE_MAIN_MERGED=false` 覆蓋本章。
> **此 P26 增量的發布界線：** Source main 上 P25 文件已是正式治理權威；本 P26 頂部更正須經獨立 Docs-only Draft PR 審查及另行核准 Merge 後，才能取代 `main` 內容。未經合併不得宣稱 P26 已在 main 生效。
> **業務發布狀態：** `SOURCE_RUNTIME=DORMANT`、`P20_PR_HEAD_DIRECT_CI=NOT_ATTESTED`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`。

## 最新治理判定（P25 Merge 後，P26 增量候選）

| 權威物件 | 固定基準／狀態 | 治理結論 |
|---|---|---|
| Source main | `a8d21d2e6aa056a13d5eb9de3d32920d11d4f740` | 已合併 P24 PR #3，新增精確兩份治理 MD，無程式/資料/Workflow 改動 |
| Source PR #3 | `MERGED`，HEAD `145189c19e2a58207fc1dc77ca558cb347e7bcca` | 文件合併 Gate SRC-P25 PASS，不再 `ready/merge` |
| Source PR #1 | `OPEN/DRAFT`，HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`，34 檔 | Cloud Scheduler / writer **HIGH-RISK HOLD**，不得合併 |
| Source PR #2 | `OPEN/DRAFT`，HEAD `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0`，五個新增檔 | Source-only DORMANT，尚未接 Runtime |
| Preview main | `a8cde084ab5581736d86094d8cdcc2cdc9963000` | 不修改靜態資料與現有 PWA |
| Preview PR #1 | `OPEN/DRAFT`，HEAD `b55b3673088b6df7bfe51f04d8d82b8e7616324f`，僅 `index.html` | 九卡片/九詳情 Android UAT PASS，尚未正式 Merge |
| P23 Source Runner | [Run #40094208387](https://github.com/easonliu714/event_scraper_public/actions/runs/40094208387) SUCCESS | 治理分支固定 P20 HEAD 測試 PASS |
| P23 Preview Runner | [Run #40094214324](https://github.com/easonliu714/eventradar-pwa-preview/actions/runs/40094214324) SUCCESS | 治理分支固定 P20 HEAD 測試 PASS |
| P20 兩個 PR HEAD Checks | GitHub 各 0 個 Check runs | **NOT_ATTESTED**，不能以 P23 branch run 替代 |
| GitHub 獨立 Open Issues | 最後查核 0（排除 Issues API 中的 PR） | 無證據可關閉任何獨立 Issue |

### 後續 Roadmap（不重啟已完成 Gate）

```text
EventRadar / 活動暨售票雷達
├── SRC-P1～P24: Android／GitHub 各 Gate PASS，禁止重跑或重新發布
├── SRC-P25: PR #3 已解除 Draft、一般 Merge Commit、雙 Parent 與兩檔獨立 SHA 讀回 PASS
├── SRC-P26: 只修正兩份 main 治理 MD 的「最新頂部狀態」，Docs-only Draft PR，未合併前為候選
├── P20 PR HEAD 直接 CI Check: OPEN／NOT_ATTESTED（與 P23 分支 Runner PASS 分開）
├── R3C-O3: Golden 官方內容人工覆核：HOLD；GOLDEN_ACCEPTED=0
├── G5J: 活動有效性判定：OPEN／HOLD，須保留可逆性與來源證據
├── G5K: 真實候選資料隔離 E2E + Android UAT：OPEN／HOLD
└── Cloud Scheduler／資料寫入／通知／正式網站 Merge/Publish：LOCKED，需獨立授權
```

**讀取規則：** 此章為截至 SRC-P25 的最新權威事實；以下 P24 歷史正文因原樣封存而仍含「尚未合併／未建立」字樣，僅反映當時狀態。每輪必須先對照 GitHub 最新 main HEAD 與 PR/CI，不得因對話切換而回退至 P24 或重跑 P1～P25。

---

## 歷史封存：SRC-P24 文件治理 Draft PR 編製時點（原文逐位元組保留）

# 活動暨售票雷達｜正式治理 Roadmap、PR、Issue 稽核（SRC-P24 候選）

> **最新快照：2026-10-24，Asia/Taipei。** 本文件為 SRC-P24 **文件治理 Draft PR 候選**，只有在經核准合併至 Source Repo `main` 並獨立讀回後，才成為該路徑的正式 main 治理權威。歷史附錄包含各時點的「待驗、未建立」文字，**不得覆蓋本章最新狀態**。
> **發佈分類**：`GOVERNANCE_DOC_PR=true`（若 P24 PR 已建立）；`GOVERNANCE_MAIN_MERGED=false`；`APP_DATA_PUBLISHED=false`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`。

## P24 現行唯一讀取入口與權威矩陣（發布前凍結）

| 對象 | 已驗證之 SHA / Run / 狀態 | 允許的下一步 |
|---|---|---|
| Source `easonliu714/event_scraper_public/main` | `6004754f90d551cdb0cdb91a3e04b42c04f45f48`，原 8 檔 | 維持不變；治理文件從此 main 建新 Draft PR |
| Preview `easonliu714/eventradar-pwa-preview/main` | `a8cde084ab5581736d86094d8cdcc2cdc9963000` | 維持不變 |
| Source 原 PR #1 | [PR #1](https://github.com/easonliu714/event_scraper_public/pull/1)，Draft / Open / Unmerged，HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`，34 檔 | **Cloud HIGH-RISK HOLD**：Schedule、`contents:write`、`commit_data.sh` 不得合併或啟用 |
| Source P20 PR #2 | [PR #2](https://github.com/easonliu714/event_scraper_public/pull/2)，Draft / Open / Unmerged，HEAD `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0`，精確 5 新增檔 | Source `show_news.py` / `event_details.py` 仍 **DORMANT**；只測試不啟用 |
| Preview P20 PR #1 | [PR #1](https://github.com/easonliu714/eventradar-pwa-preview/pull/1)，Draft / Open / Unmerged，HEAD `b55b3673088b6df7bfe51f04d8d82b8e7616324f`，僅 `index.html` | 9/9 Synthetic UAT 已 PASS；未部署正式 UI |
| Source CI 治理分支 | `ci/eventradar-source-ci-p22`，HEAD `a50bfd25ff07293430f511ff8f1275b8fa37267d` | 單一唯讀 workflow，Runner [40094208387](https://github.com/easonliu714/event_scraper_public/actions/runs/40094208387) **completed/success** |
| Preview CI 治理分支 | `ci/eventradar-preview-ci-p22`，HEAD `0c894a3626fc644cfcace7365238a2abba6a8079` | 單一唯讀 workflow，Runner [40094214324](https://github.com/easonliu714/eventradar-pwa-preview/actions/runs/40094214324) **completed/success** |
| P20 PR HEAD 對應 Check runs | Source 0／Preview 0（P23 後查核） | **NOT ATTESTED**；CI 治理分支 Push PASS 不能冒稱 P20 PR 自身 CI PASS |
| SRC-P1～P22 | Android 各階段已驗證結果保留；P18 V100 歷史 HOLD 由 V101 修復 PASS | 不重跑已通過 Gates |
| SRC-P23 | Android Stage/Publish/Verify PASS，GitHub Remote Run/Job/Steps 獨立讀回雙 SUCCESS | 已結案；不重複發布或重跑 Runner |
| Independent GitHub Issues | 最後查核沒有獨立 Open Issue；GitHub Issues API 含 Pull Requests，須排除 `pull_request` | 不捏造 Issue 或自行關閉 |
| 正式 9,850 筆快照 | Preview `data.json` SHA256 `ef39c6be44a3f26c30bc3ce13f41548d1bd6b6408af8e872eb55fff360fea43b`（歷史固定快照） | 禁止改寫；舊 G5C/G5D 8,233/1,617 只是 2026-10-23 快照 |

### Roadmap 優先序（多層）

```text
EventRadar（SRC-P23 Cloud CI 已真實 PASS；正式業務資料未發布）
├── 已完成且凍結 [ANDROID PASS]
│   ├── P1–P13 多平台/BeClass 解析、來源角色候選與 G5H 回歸
│   ├── P14–P15 隔離 UI 九筆列表＋九筆詳情 Synthetic UAT
│   ├── P16–P19 Source five-file / Preview index-only 候選與隔離 Patch
│   ├── P20 雙獨立 Draft PR 建立／HEAD／Changed Files 讀回
│   ├── P21–P22 唯讀 CI 及 push-only 觸發設計 Android Gate
│   └── P23 雙 CI 治理分支 Runner/Job/Steps 真實 SUCCESS
├── P24 GitHub 治理文件正式化 [DOCS-ONLY DRAFT PR，尚未合併]
│   ├── [本次] 唯一 Source Repo docs 下兩份 Markdown，以 main 為基底
│   ├── [本次] exact-two-add、non-force、PR Draft、SHA + PR 讀回
│   └── [下階段] 獨立審核文件，另行授權合併 main 後才是正式權威
├── P25 P20 PR HEAD 直接 CI Check [OPEN，獨立 Release Gate]
│   └── 須另行設計 default branch 的 PR workflow，不能用 P23 的 branch push CHECK 充數
├── R3C Golden / G5J 有效性引擎 [HOLD / OPEN]
│   ├── R3C-O1 8 URL 一次性 GET、6 HTML + 2 redirect；禁止重新抓取
│   ├── R3C-O2 離線 Android PASS；O3 人工證據缺口／Golden 待簽認
│   └── G5J ACTIVE/EXPIRED/NON_EVENT/SOURCE_GONE/UNCERTAIN 等可逆判定尚未實施正式決策
├── G5K 候選真實 data.json 隔離 E2E / Android 實際資料 UAT [OPEN/HOLD]
└── 合併/發布/Cloud Scheduler/通知 [LOCKED；獨立授權]
```

### PR／Issue Close 決策（2026-10-24）

- Source PR #1／#2 與 Preview PR #1 **KEEP OPEN/DRAFT**。無任何 PR Merge／Close 授權或證據；原 Source PR #1 含 Cloud writer 風險，不能放行。
- P24 docs-only 新 Draft PR（若建立）應保持 Open/Draft，不因文件 Runner PASS 而直接合併。所有舊分支與多 Gate 證據仍保留。
- 應以 GitHub `issues` 排除 pull_request 資料取得真正 Issue 數；截至此核對沒有獨立 Open Issue 可結案。內部 Roadmap 待辦不是 GitHub Issue。
- `GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`、`P20_PR_HEAD_DIRECT_CHECKS=NOT_ATTESTED`。

### 本文件的證據、更新流程與漂移封鎖

1. 先讀 GitHub Source/Preview main、PR1/PR2/Preview PR1、P23 兩份 Actions run 和本路徑兩份治理 MD 的**最新正式 main 版本**；若尚未合併，本文件只屬 Draft 候選，不宣稱 main 已同步。
2. 每輪附上 GitHub SHA、Android frozen Gate、實際 changed paths、Run ID、CI Check 所屬 Commit、業務 Golden 與正式發布狀態；不以候選等同正式上線。
3. 重大差異一律 HOLD：禁止 reset、force push、改 PR1、寫 data.json、活動 GET、排程或通知；若要合併文件另行取得核准。
4. 以下原始歷史章節保留以供稽核，內含早期「待驗／未建立／未發布」等語句，皆只反映**當時**狀態，不可覆蓋 P24 當前摘要。

---

## 歷史治理紀錄（Append-only，按原始編製時點保留）

# EventRadar Taiwan — ROADMAP / PR / ISSUE CLOSURE AUDIT

> 盤點日期：**2026-10-24（Asia/Taipei）**  
> 專案：`easonliu714/event_scraper_public`（正式來源）、`easonliu714/eventradar-pwa-preview`（隔離預覽）  
> 狀態：**治理基線候選／本機正式格式 MD 已編製；尚未提交 GitHub**。本文件的 SHA 是盤點時點證據，後續每輪須重新即時核對。  
> 性質：GitHub API READONLY、對話內 Termux 真實實機輸出、既有 Toolkit SHA 鎖定與程式檢視；**沒有進行 GitHub Issue/PR 關閉、Commit、Push、Merge、排程啟用、資料寫入或 PWA 發布**。  
> 來源限制：使用者上傳的兩份 `SPC_System_*.md` **僅參考治理文件的組織方式**，SPC 的 PR/Issue/PG/ETL 與 EventRadar 完全不同，不混用。

## 0. 權威與證據層級

| 權威對象 | 2026-10-24 GitHub 即時讀回 | 結論 |
|---|---|---|
| 正式來源 `main` | `6004754f90d551cdb0cdb91a3e04b42c04f45f48` | 與承接基準相同；不准自行變更 |
| PR #1 | [EventRadar V44.2 - Restore Cloud Scheduler](https://github.com/easonliu714/event_scraper_public/pull/1) | **open / Draft / merged=false** |
| PR #1 head branch | `fix/event-radar-v44-cloud-20261023` | `26888422e48634d9729d2deea67b7996a5d1e4ee` |
| PR #1 base | `main` | `6004754f90d551cdb0cdb91a3e04b42c04f45f48` |
| PR #1 GitHub 比較 | ahead=11，behind=0；changed paths=34 | 不是已合併／已發布 |
| G5H parser | `event_details.py` Git blob `ed425662b4f2ce2032a0fa0c3e83075842f30767` | PR source 已具備；主線尚未採用 |
| V44 runtime source | `show_news.py` Git blob `7f4b5dd4de53fc6de1acb59c64d54ea9a2e9e89f` | 真正 PR runner，非 `scraper.py` |
| 獨立 PWA 測試站 `main` | `a8cde084ab5581736d86094d8cdcc2cdc9963000` | 獨立預覽已發布，非正式來源發布 |
| 獨立 PWA `index.html` | Git blob `c11c65322444a309ab04751887f670b25fe8cf6f` | 真正的**測試** UI 權威 |
| 獨立 PWA `data.json` | Git blob `c64a72bafd32f1248c53acd83279a33eaca4c41b` | 凍結快照；SHA256 見下 |

**狀態詞不可互換**：`CODE`（原始碼存在）、`CI-PASS`（特定 HEAD workflow success）、`ANDROID-PASS`（Termux 特定 Gate 及快照）、`DATA-CANDIDATE`（解析推定）、`GOLDEN-PASS`（獨立官方內容與人工確認）、`PUBLISHED`（有授權且部署讀回）、`HOLD`（缺證據/權限）、`NOT-PROVEN`（尚未充分驗證）。

## 1. 主 Roadmap 多層樹（防重啟）

```text
EventRadar Taiwan / 台灣活動暨售票雷達
├── G1–G4 雲端採集／PR 試跑／獨立 PWA 架設 [HISTORIC PASS；不重做]
│   ├── PR1 Python 唯讀雲端驗證、G4B 來源證據、Live Dry Run [CI-PASS]
│   ├── 獨立 `eventradar-pwa-preview`；原始 9,850 筆快照 [PASS]
│   └── 真正欄位正確性、官方內容最新狀態 [NOT-PROVEN]
├── G5A–G5D 保守可見性治理 [ANDROID PASS；依 2026-10-23 快照]
│   ├── G5A Node.js 24 相容性／候選資料分析 [PASS]
│   ├── G5B 來源有效性與標題－欄位衝突 [PASS]
│   ├── G5C 1,482 筆保守隱藏，保留衝突/未知 [PASS]
│   └── G5D Event Go 完整過期日期區間加隱藏 135 [PASS]
│       └── 原始 9,850；當日顯示 8,233；總隱藏 1,617 [FROZEN]
├── G5E–G5G 來源及環境一致性 [PASS；不代表內容正確]
│   ├── G5E 官方 11/11 來源探測完成 [PASS]
│   ├── G5F Termux Wi-Fi/5G、GitHub Actions 網路 A/B [PASS]
│   └── G5G 11 組解析欄位 parity；G5H 解析器 FIELD_DIFFERENCES=0 [PASS]
├── G5H / R1 解析器來源歸屬與 Blob 綁定 [PASS]
│   ├── 多 JSON-LD Event、來源不明、純網址解析修復 [PASS]
│   ├── parser Blob `ed425662...` [PINNED]
│   └── PR #1 目前 HEAD 六條 Actions [6/6 CI-PASS]
├── G5I 日期標準化與來源 Golden [階段性]
│   ├── G5I V1.0.1 日期候選 9,850 分類／35 正反向 [ANDROID PASS]
│   ├── G5I-R2 標題完整起訖日期覆蓋層／45 Fixtures [ANDROID PASS]
│   │   ├── 松山文創 57、TixFun 68；嚴格候選 125（寬鬆 126）
│   │   ├── 結束日早於 10/23：77；未早於：48；嚴格拒絕：1
│   │   └── AUTO_HIDDEN=0，G5C/G5D 顯示量未改 [PASS]
│   ├── G5I-R3A V1.0.1 官方取證 [ANDROID PASS；V1.0.0 的 tzdata HOLD 已修復]
│   │   ├── 4 平台 × 2 URL，手動 opt-in 8 HTTPS GET [PASS]
│   │   ├── HTTP 200 但內容未確認 6；Redirect uncertain 2
│   │   └── 不保留原始 HTML；Golden 尚待人工／獨立證據
│   ├── G5I-R3B V1.0.0 既有回條唯讀檢核 [ANDROID PASS；本輪新增]
│   │   ├── 95 來源/狀態 fixtures + 9 日期防誤判案例 [PASS]
│   │   ├── 8 回條 SHA/來源 lineage [PASS]
│   │   ├── DATE_SIGNAL_REVIEW=2；NO_VERIFIABLE_EVENT_DATE_SIGNAL=4
│   │   ├── ACCESS_UNCERTAIN=2；GOLDEN_ACCEPTED=0 [GOLDEN HOLD]
│   │   └── 9850 / 8233 / HTTP=0 / AUTO_HIDDEN=0 [PASS]
│   └── G5I-R3C 獨立官方來源 Golden 身分／日期確認 [OFFLINE ANDROID PASS; OFFICIAL GOLDEN HOLD]
│       ├── OPENTIX 最後場次與真正 endDate（多場次不可誤取前一場）
│       ├── BeClass 民國年課程活動日 ≠ 報名截止日
│       ├── ACCUPASS 活動起迄日 ≠ 售票/報名期間
│       └── KidsClub 歷史文案/可預約課程；無固定結束日須保留未知
├── G5J 有效性／下架證據引擎 [OPEN / NOT BUILT AS FORMAL DECISION]
│   ├── ACTIVE / EXPIRED / NON_EVENT / SOURCE_GONE
│   ├── ACCESS_UNCERTAIN / DATE_CONFLICT / DATE_UNKNOWN
│   └── reason + source identity + dated evidence + reversible exclusion [NOT-PROVEN]
├── G5K 候選 data.json → 隔離 PWA QA [OPEN; NO CURRENT AUTHORIZATION]
│   ├── Source QA、Golden、欄位 parity、資料品質 coverage [HOLD]
│   ├── 隔離候選 data.json + 手機 UI/UAT [NOT-STARTED]
│   └── 不覆蓋正式 `data.json`／不破壞舊 9,850 快照
└── 正式發布 Gate [LOCKED]
    ├── 來源/解析/候選資料驗收；回復/反向/漂移 Gate
    ├── 已授權 PR merge、正式 main 發布及唯一 Actions writer
    ├── 排程／通知另行授權，手機不得與 Actions 雙寫
    └── 長期有效展覽、多場次避免誤藏、實際 PWA 驗收
```

**歷史日期固定**：`2026-10-23` 的 9,850／8,233／1,617 為快照重播驗收，不能作為任意未來日期的即時結果。G5I 的日期分類、G5I-R2 review queue 目前**沒有**寫入正式 PWA 的顯示決策。

## 2. G5I 實機證據固定數據

| 分類（G5I V1.0.1） | 全筆 | 當時顯示 |
|---|---:|---:|
| CURRENT_OR_FUTURE_CANDIDATE | 1,028 | 1,028 |
| DATE_CONFLICT_REVIEW | 66 | 62 |
| DATE_UNKNOWN | 6,548 | 6,511 |
| HISTORIC_YEAR_REVIEW | 2 | 2 |
| PAST_CANDIDATE_REVIEW | 1,727 | 154 |
| SALE_DATE_REVIEW | 110 | 107 |
| TITLE_DAY_REVIEW | 369 | 369 |
| **總計** | **9,850** | **8,233** |

- 原始預覽 `data.json` **檔案 SHA256**：`ef39c6be44a3f26c30bc3ce13f41548d1bd6b6408af8e872eb55fff360fea43b`。檔案 SHA256 ≠ Git blob SHA。
- R2：`LOOSE=126, STRICT=125, PAST=77, CURRENT=48, REJECTED=1, UNKNOWN_AFTER_OVERLAY=6423, AUTO_HIDDEN=0`。
- R3A：實際 8 官方 GET，`HTTP_200_CONTENT_NOT_YET_VALIDATED=6, REDIRECT_UNCERTAIN=2`。
- **最新 R3B Android**：`reviewed=8, DATE_SIGNAL_REVIEW=2, NO_VERIFIABLE_EVENT_DATE_SIGNAL=4, ACCESS_UNCERTAIN=2, GOLDEN_ACCEPTED=0, SOURCE_HTTP=0, AUTO_HIDDEN=0, published=false`。
- R3B 上游證據 SHA：R3A targets `0b50cc9e2eacccd01d1ed1421c4de9df17a653e7488f8cb96fda218b14a3eb71`；R3A preflight summary `ef61787cb717454d22ed790363356942c37e348c86c92f2d809272b8e37d7c6a`；R3A probe summary `af621461b13ce432fb57164e9fce65ba1e1138be47e9c1527f8de42b95589ea9`；R3A receipts `501f26a178776c0fe3843047dca897bf69676619db2a226690148e6743f2150c`。
- **R3B 已 PASS，正式 Golden 狀態仍 HOLD**。不要誤認「兩筆有日期訊號」=「兩筆正式可信活動日期」。

## 3. Pull Requests — 全量與 Close 決策

GitHub `GET /pulls?state=all`：**總數 1，Open=1，Closed=0，Merged=0**。GitHub compare：ahead=11／behind=0／changed paths=34。

| PR | 狀態 | 類型/內容 | Close / Merge 建議 |
|---|---|---|---|
| [#1 — EventRadar V44.2 - Restore Cloud Scheduler](https://github.com/easonliu714/event_scraper_public/pull/1) | **OPEN/DRAFT** | 新增 `show_news.py`、`event_details.py`、source probes、read-only PR CI、排程候選、發布 guard | **KEEP OPEN/DRAFT；不得 Close/Merge/Ready。** G5I-R3C、G5J、G5K、資料 UAT 與授權前皆非完成。 |

- 原 PR 說明仍停留於 `Termux offline tests: 40/40 PASS` 等早期 V44 描述，**已落後** G5I-R3B；未經授權不得擅自更新 PR metadata。可在未來獲准的治理文件 PR 中精確補充階段與證據。
- PR #1 目前新增的正式 cloud workflow 定義含 `schedule`、`workflow_dispatch`、`contents:write`、`scripts/commit_data.sh`；**只存在 Draft PR 的新增檔，不等於 default `main` 已啟用排程或發布**。
- PR 的 `scripts/commit_data.sh` 擬將 `docs/data.json` commit/push 回 main；這是正式發布 writer 候選，尚未授權啟用。
- 11 commits／34 paths 的累積 diff 不等於 34 項未完成任務；要以現有 Gates／資料品質驗收檢查，避免另起 V44 新分支。

## 4. 六條最新 CI：同一 PR HEAD 的確認

`HEAD=26888422e48634d9729d2deea67b7996a5d1e4ee`，全部為 **2026-10-23 UTC** 的 `pull_request` workflow，均 `completed/success`。這是該 HEAD 的 CI 結果，不是 R3B Termux Gate 在 GitHub 上的 CI。

| Workflow | Run ID／連結 | 結果 |
|---|---|---|
| Read Only Python Gate | [39954059586](https://github.com/easonliu714/event_scraper_public/actions/runs/39954059586) | SUCCESS |
| G4B Source Evidence | [39954059427](https://github.com/easonliu714/event_scraper_public/actions/runs/39954059427) | SUCCESS |
| G5F Network A/B | [39954059511](https://github.com/easonliu714/event_scraper_public/actions/runs/39954059511) | SUCCESS |
| G5G Field Parity | [39954059636](https://github.com/easonliu714/event_scraper_public/actions/runs/39954059636) | SUCCESS |
| Live Dry Run (NO Publish) | [39954059580](https://github.com/easonliu714/event_scraper_public/actions/runs/39954059580) | SUCCESS |
| PWA Preview Snapshot (NO Publish) | [39954059661](https://github.com/easonliu714/event_scraper_public/actions/runs/39954059661) | SUCCESS |

提醒：先前其他 HEAD 曾有 G5G failure，後續在**目前 HEAD** 的 G5H-R1 Blob 綁定修復後 success；歷史 failure 不需重演。

## 5. Open Issues 全量與疑似可 Close 專案項目

| Repository | GitHub `/issues?state=all` 原始回傳 | 獨立 Open Issue | 獨立 Closed Issue | 可直接 Close |
|---|---:|---:|---:|---|
| `event_scraper_public` | 1（其實是 PR #1，具 `pull_request` 屬性） | **0** | **0** | **0** |
| `eventradar-pwa-preview` | 0 | **0** | **0** | **0** |

**結論：沒有「漏關的 GitHub Issues」可關閉**；也不能把 PR #1 當成完成 Issue 關閉。**有未完成 Roadmap 工作，但尚未建立相應 GitHub Issues**。不得虛構 Issue #2、#3 或自行建立/關閉，除非另經治理與使用者授權。

### Roadmap Backlog（文件工作項，**不是** GitHub Issue 編號）

| 內部 ID | 狀態 | Owner/現有元件 | 下一項可證明的 DoD | 建議 |
|---|---|---|---|---|
| ER-R3C | IN PROGRESS / OPEN | R3A 8 GET receipts + R3B 8 review receipts | 獨立保存、來源歸屬、日期語意、場次身分、人工作業簽認；Golden 明確接受或 HOLD | KEEP |
| ER-VAL | OPEN | G5C/G5D client filters、G5I reviews | 7 種 status、可逆 reason/provenance、非活動/下架充分證據，避免 403/redirect 誤下架 | KEEP |
| ER-DATA | OPEN | `show_news.py` / `event_details.py` / snapshot exporter | 每來源 title/date/location/price/desc/URL 覆蓋與真值 Golden parity | KEEP |
| ER-PWA | OPEN | `eventradar-pwa-preview` | 經授權另產出候選 JSON、UI 手機 UAT、邊界／回復驗證 | KEEP |
| ER-RELEASE | LOCKED | PR #1 + `commit_data.sh` | 來源/Golden/資料 Gate、PR review、單一 writer、正式授權與回復演練 | KEEP |
| ER-GOV | OPEN | 本次兩份治理 MD | 核准僅文件 GitHub 發布 Gate，遠端 commit + 檔案 SHA readback | KEEP（不阻斷 R3C 唯讀） |

不要因 Gate 局部 PASS 把父任務 ER-VAL、ER-DATA、ER-RELEASE 當作已完成；也不要為既有搜尋 UI、爬蟲、排程另開一套平行系統。

## 6. 最重要的 Release 風險與防重工 Crosswalk

| 問題／需求 | 既有擁有者 | 已有能力 | 尚欠缺 | 禁止的重工／誤判 |
|---|---|---|---|---|
| 活動來源與詳情 | `show_news.py`, `event_details.py` | 多來源 fetcher、JSON-LD/DOM、G5H 修復 | 每平台官方 Golden 真值 | 不重寫 `scraper.py`／第二套 parser；先找 source handler |
| 標題日期及活動結束日 | G5I、R2、R3A、R3B | 日期 review queue、正反向 fixtures、真實 8 回條 | R3C 獨立內容保存與人工日期核准 | 不把報名截止/售票日當 endDate，不把 review 當下架 |
| PWA 搜尋與 UI | preview `index.html` | 搜尋、篩選、清單、詳情、localStorage | 資料品質與正式切換 UAT | 不重建 PWA／不 patch 來源 `docs/index.html` 當作已改測試 UI |
| 無效活動隱藏 | `event_visibility.js`, `eventgo_period_gate.js` | G5C + G5D 可逆顯示過濾 | G5J 官方證據層 | 不再做另一套客戶端過濾器覆蓋現有邏輯 |
| 資料儲存 | PR `docs/data.json`、preview `data.json` | JSON 靜態快照 + artifact + localStorage | 來源證據 lineage 與候選 release | 不擅自導入 PostgreSQL/SQLite/新 API DB |
| 雲端執行 | PR workflow／`run_show_news.sh` | CI Dry Run、single-writer 設計 | 審核後主線正式部署 | 不讓手機與 Actions 同時寫 `docs/data.json` |
| 推播 | Telegram/Termux + Preview notification stubs | 明確 opt-in、防雙通道 | 真實告警需求/權限/演練 | 不自行開通知或手機 daemon |

### 反向 Gate 一律 Fail-Closed

1. 主線／PR／Preview HEAD、解析器 Blob、本地 working tree 或原始快照 SHA 不一致 → `HOLD_AUTHORITY_DRIFT`，先精確比對，不 reset／force push。
2. 日期缺失、民國／西元語意不明、OPENTIX 多場次未完整覆蓋、來源重新導向或臨時 HTTP 403/404/429/503 → 只能 `REVIEW/UNCERTAIN`，不可判失效並隱藏。
3. HTTP 200、JSON-LD `Event` 存在、Cloud FIELD_DIFFERENCES=0、CI success → 分別不是「官方內容正確／Golden 核准／可 Merge」證明。
4. R3A／R3B receipt 只能作為觀測證據：官方 HTML 未保留，僅有 SHA 無法事後獨立驗真內容。
5. Android Termux 路徑固定 `~/eventradar`、`~/eventradar_toolkit/gates/`、`~/eventradar_preview_site`；嚴禁操作 `~/my_project`。

## 7. 本次 Close Decision / Next Task

- **可直接 close 的 PR：0；Issue：0。未做任何寫入。**
- **應保留的 PR：#1，OPEN/DRAFT；不得自行 Merge／Ready／Close。**
- **最新已通過 Gate：G5I-R3B V1.0.0，Android PASS，2026-10-23 凍結快照；R3B `golden_accepted=0`。**
- **下一個 Gate：G5I-R3C 獨立官方 Golden 日期／場次／來源身分驗證，唯讀且需限定來源、保存可審計證據**。須用原 8 筆 ID/SHA 對位，不重新運行 G1～R3B，不再手動重跑 R3A `--probe-once`；必要的新 GET 僅在當 Gate 設計與授權後執行。
- **文件發布治理**：本次產生 `docs/ROADMAP_PR_ISSUE_CLOSURE_AUDIT.md` 與 `docs/UI_API_DB_FEATURE_ARCHITECTURE_TREE.md` 的本地候選；未獲明確 GitHub publication 授權，且尚未獨立文件 Gate／讀回，因此目前**不宣稱已成為 Repo 正式權威**。未來 docs-only commit 應獨立隔離分支、限定 exact two paths、不得混入來源 PR #1 功能，發布後遠端讀回檔案 SHA 和 PR 狀態。

## 8. 官方連結與更新協定

- GitHub 原始來源：[Repo](https://github.com/easonliu714/event_scraper_public)、[Draft PR #1](https://github.com/easonliu714/event_scraper_public/pull/1)、[Actions](https://github.com/easonliu714/event_scraper_public/actions)、[Issues](https://github.com/easonliu714/event_scraper_public/issues)。
- 預覽來源：[Repo](https://github.com/easonliu714/eventradar-pwa-preview)、[測試站](https://easonliu714.github.io/eventradar-pwa-preview/)。
- 每輪以 GitHub **live** 頭版及兩份治理 MD 的**最新經發布遠端版本**為權威；未發布前以本輪 MD 候選加上 GitHub live／Android 原始證據交叉驗證，不假冒已在 Repo。
- 每輪更新欄位：`GATE | BASE_BRANCH/HEAD | PR_DRAFT/HEAD | PREVIEW_HEAD | PARSER_BLOB | LOCAL_BRANCH/HEAD/CLEAN | EXACT_CHANGED_PATHS | FIXTURE_SHA | CI_RUNS | ANDROID_EVIDENCE_SHA | USER_AUTH_SCOPE | PASS/HOLD | NEXT_GATE`。

## 9. 2026-10-24 R3C Android 實測增量（OFFLINE PASS / GOLDEN HOLD）

- R3C V1.0.0 正反向 synthetic Golden contract 與 Android authority/lineage 驗證已經 Termux 實測 PASS；**不等於官方 Golden PASS**。
- R3A upstream 四個凍結 SHA 已於 Termux readback PASS；R3B 實際 8 筆與八筆 URL SHA/platform/identity 對位均 PASS。
- `GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`PUBLISHED=false`；R3C 本輪不新增官方 GET。
- 本文件在 GitHub 中仍屬**尚未發布候選**；須獨立 docs-only exact-two-file PR、非強制發佈與內容 SHA readback，且不得觸及 PR #1 / main / PWA。

## 10. 2026-10-24 R3C Evidence Audit 正式實測回條（最新優先）

> 更新來源：使用者 2026-10-24 Android Termux 原始 Console；不得將這份文字紀錄誤當成 GitHub main 已發布、完整原始 HTML 或獨立人工 Golden 簽認。

- 使用既有 `g5i_r3c_golden_v100`，下載包 SHA256：`fb1b2264703202dbff4dc4ea56604688ddcdf060772bbd1e8fba74c17809364d`。
- `--selftest`：`PASS R3C_SYNTHETIC_SOURCE_EVENT_DATE_CONTRACT POSITIVE=4 NEGATIVE=26`；合成測試不等於官方真值。
- `--preflight`：`PASS R3C_ANDROID_LOCAL_SOURCE_PREVIEW_CLEAN_BLOB_DATA_SHA`、`PASS R3C_GITHUB_MAIN_PR_DRAFT_PREVIEW_PINNED_SHA_READBACK`。
- `--audit-evidence`：`PASS R3C_R3A_4_PINNED_SOURCE_EVIDENCE_SHA`、`PASS R3C_R3B_FROZEN_9850_8233_EIGHT_2_4_2_AND_ZERO_PUBLISH_GATES`、`PASS R3C_8_TARGET_URL_SHA_PLATFORM_AND_ID_LINEAGE`、`PASS R3C_OFFLINE_AUDIT_CREATE_ONLY evidence=2026-10-23_r3c_offline`。
- Termux `R3C_AUDIT_EXIT_CODE=0`。`HOLD R3C_OFFICIAL_GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 PUBLISHED=false` 是預期且強制保留的業務安全結論。
- Gate 決議：**G5I-R3C OFFLINE/LINKAGE ANDROID PASS；G5I-R3C OFFICIAL GOLDEN HOLD**。R3A/R3B 舊 Gate 與 2026-10-23 的 9850/8233/1617 快照保持不變。未有任何新官方 GET、真正 HTML 固定內容與人工獨立接受。
- 下一個工作：G5I-R3C 官方原始來源固定證據與獨立簽認（原 8 筆，必須單獨取得限定 GET 授權）；此後才到 G5J → G5K → 正式發布 Gate。
- GitHub `event_scraper_public/main=6004754f90d551cdb0cdb91a3e04b42c04f45f48`、Draft PR #1 `head=26888422e48634d9729d2deea67b7996a5d1e4ee`、PWA preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`：R3C Android Gate 已讀回符合基線，遠端亦於本輪確認不漂移。
- **治理文件 GitHub 發布仍 HOLD**：GitHub integration 嘗試建立隔離 docs-only 分支 `docs/eventradar-governance-r3c-20261024` 時回覆 HTTP 403 `Resource not accessible by integration`，故**未建立分支、未 Commit、未 Push、未開 PR #2、未修改 main**。必須在取得具寫入權限的授權通道後，再做 exact-two-docs-only publication 與遠端讀回；不得假裝已發布。


## 11. 2026-10-24 R3C-O1 獨立官方原始內容取證 Gate（本地候選，未 GitHub 發布）

- 使用者於 2026-10-24 明確核准「僅 R3A 原八筆官方來源、每 URL 最多一次 HTTPS GET、總計最多八次、不重試、不跨站重新導向、保留原始內容 SHA 與可稽核證據」的新取證工作；**不授權 Git commit/push/merge、正式 data.json/PWA、排程、下架或自動 Golden 簽認**。
- 新建獨立 `g5i_r3c_official_raw_v100` Termux Toolkit，與已 PASS 的 `g5i_r3c_golden_v100` 完全分離。新工具使用 R3C 凍結來源、2026-10-23 R3A/R3B 上游 SHA 和 R3C 離線 lineage，沒有重新執行歷史 R3A 網路 probe。
- 工具設計：Android + GitHub 權威 PRECHECK、八目標 SHA / URL / 平台 / 活動身份精確綁定、官方公共 DNS 限制、禁 proxy/redirect、HTTPS 驗證、單次 GET、16 秒逾時、2 MiB body 上限、create-only one-shot 預留 Ledger、0600 原始 bytes / SHA、純候選日期訊號、來源人工作業簽認仍 HOLD。
- **截至本文件編製時，只完成本機合成／模擬離線 QA；Android 實際新取證尚未執行，官方 GET 次數本工具 = 0。** 本機 QA 不等於 Android Gate，不等於 Golden 接受。
- 下一步先由 Android Termux 執行 Toolkit `--selftest`、`--preflight`，檢查 8 URL 精確且版次未漂移，再以 `--capture --authorize-exact-eight-gets` 實機一次性取證，執行 `--verify` 讀回；若無法取得原始內容或來源衝突則 HOLD，不重試。
- GitHub docs-only 治理發布因 integration 403 仍 HOLD；這兩份檔案為候選更新，不得視為已正式發布。後續 G5J → G5K → 正式發布不提前啟用。

## 12. 2026-10-24 R3C-O1 V1.0.0 Android Preflight HOLD → V1.0.1 修復候選

- 使用者 Termux 回報：V1.0.0 Toolkit package SHA、13 正向 + 19 反向、Mock GET 整合 5/5、Android Root/HEAD/Clean、GitHub main/PR Draft/preview SHA 皆 PASS。
- 唯一實機阻塞：`HOLD R3C_O1_R3A_TARGET_URL_NOT_STORED:cannot_reconstruct_hash`（R3A targets 只有 URL SHA；舊取證入口錯誤要求原始 URL 明文）；正式 O1 GET **0，沒有執行 capture**。
- V1.0.1 新候選：用 R3A/R3B SHA 鎖定回條及 SHA 鎖定 Preview data.json (`9850` 歷史快照) **精確 SHA** 還原八筆 URL；無法唯一對應必須 HOLD，不能人工猜網址或重跑舊 Gate。
- V1.0.1 引入 V100 attempt ledger 存在性保護，任何舊版已開始 GET 必須 HOLD，不准跨版本重試；新證據採獨立 create-only 路徑。
- 本地 V1.0.1 Toolkit QA 不能代替 Android 實機 PASS；官方 Golden=0、auto-hidden=0、published=false；兩份治理 MD 仍**尚未 GitHub 發布**（先前 403）。

## 2026-10-24 Android R3C-O1 V1.0.1 capture completion — new append-only evidence

User-provided Android Console independently reports `PASS R3C_O1_EXACT_EIGHT_ATTEMPT_RECEIPTS_CREATE_ONLY` and `PASS R3C_O1_EIGHT_ATTEMPT_AND_RAW_SHA_READBACK`. Exactly 8/8 one-shot HTTPS GETs: ACCUPASS 2 × 200, BeClass 2 × 302 no-redirect, KidsClub 2 × 200, OPENTIX 2 × 200. Six HTML bodies were captured with SHA readback; two BeClass remain uncertain, do not follow redirect. `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`. **Never execute `--capture` again for these eight URLs**. The following R3C-O2 fixture/date role analysis is designed as a local Toolkit but **not yet Android verified**. Keep next Roadmap G5I-R3C (Golden independent review) → G5J → G5K → authorized release. These are uncommitted candidate governance documents; GitHub publication remained blocked by 403. Source main, PR #1 Draft, Preview main remain frozen.

## 2026-10-24 R3C-O2 Android 實機結案暨 O3 待審 Gate（追加條目，優先於先前候選描述）

- 使用者於 2026-10-24 回報 Termux：`PASS R3C_O2_EXACT_PACKAGE_SHA`、`POSITIVE=22 NEGATIVE=14`、`PASS R3C_O2_O1_FROZEN_8_RECEIPTS_6_RAW_SHA_2_302_REDIRECTS`、`PASS R3C_O2_EVIDENCE_CREATE_ONLY`、`PASS R3C_O2_INDEPENDENT_OFFLINE_READBACK`、`PASS R3C_O2_ANDROID_AUDIT_AND_READBACK`。**O2 Offline/Lineage ANDROID PASS**。
- O1 八筆一次性 GET：6 × HTTP200（ACCUPASS/KidsClub/OPENTIX 各兩筆）、2 × HTTP302（BeClass 兩筆且未跟隨）；六份 raw HTML SHA 已通過 O2 獨立讀回，禁止再次 `--capture`。
- R3C Official Golden 仍 `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`；HTTP/日期訊號不等於事件真值、過期/有效與可報名證據。
- 下一子 Gate `R3C-O3` 為**不執行官方網站 GET**的八筆人工簽認前缺口矩陣，受限於已 SHA 綁定的 O2 審核回條；**本機 QA 並非 Android PASS**。後續僅在 Golden 真值核定後依 Roadmap 進入 G5J、G5K。
- 本輪 GitHub 讀回：source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`、PR #1 OPEN/DRAFT HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`、preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`，未修改。兩份治理文件為本地候選，GitHub 上傳仍因原 403 而 HOLD，未發布／無分支／無 PR #2。


## 2026-10-24 R3C-O3 Android 實機 PASS → O4 Source Semantic Gate 本地候選

> 此段落為本輪從 Android 原始 Console 得到的正式實機回條；兩份 MD **尚未**經 GitHub docs-only Draft PR 發布。前面章節可能仍記述 O3 待驗，以本較新的實機結果為準。

- Android Termux O3 V1.0.0：ZIP bytes SHA256 `b53ab5a49304bdb425770e0262721691a9931d1a375a6d47f9dd46ab0729d641`、Toolkit 成員 SHA、`POSITIVE=15 NEGATIVE=16`、`PASS R3C_O3_O2_O1_ANDROID_GITHUB_INDEPENDENT_SHA_READBACK`、`PASS R3C_O3_REVIEW_MATRIX_CREATE_ONLY`、`PASS R3C_O3_INDEPENDENT_RECOMPUTE_SHA_READBACK`、`PASS R3C_O3_ANDROID_AUDIT_AND_READBACK`。O3 Offline/Lineage **ANDROID PASS**。
- 已封存 8/8：ACCUPASS #1/#2 HTTP200 活動日候選 2026-10-24 與 2026-11-15；BeClass #3/#4 HTTP302 `ACCESS_UNCERTAIN`；KidsClub #5/#6 HTTP200 僅弱候選 `2027-12-31`；OPENTIX #7/#8 HTTP200 多個 Event/Offers 日期重疊，`session_candidate_days=[]`，無法推定最終演出結束日。
- 日期僅為 O2/O3 來源日期訊號，尚未證明與單一官方 Event 身分、時區、完整場次或訂票資格相符，絕不可宣稱 2026/10/24 或 2027/12/31 等日期是正式活動最後期限。
- 新 `G5I-R3C-O4` 提案：**唯讀同一已封存 HTML 中 JSON-LD Event 節點／subEvent／offers 身分與起訖對位**；對 `url`/`@id` 只做 exact URL SHA 比對。強制 Golden/HIDE/PUBLISHED 保持 `0/0/false`；本輪 Toolkit 本機合成 QA 尚不等於 Android Gate。
- O4 只能呼叫已鎖定 O3 `--verify`，繼續串接 O2/O1/GitHub readback；**不允許官方活動新 GET、不允許重跑 O1 capture**。未經逐筆獨立人工簽認，仍不能前進到 G5J 日期有效性決策或正式發布。
- Roadmap 順序不變：G5I-R3C Golden 審查 → G5J 有效性及下架證據 → G5K 候選 JSON／隔離 PWA UAT → 正式資料及發布 Gate。
- 2026-10-24 再次實際核對：Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`；PR1 Open Draft HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`；PWA Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`；G5H parser Blob `ed425662b4f2ce2032a0fa0c3e83075842f30767`。GitHub main 下仍無兩份治理 MD；先前 `create_branch` 收到 403，**沒有建立 docs-only 分支／Commit／Push／PR**，不得誤稱已發布。


## 2026-10-24 R3C-O4 Android PASS → O5 身分缺口診斷候選（最新優先）

- Android 原始 Console 證實 O4 V1.0.0：`POSITIVE=24 NEGATIVE=16`、`PASS R3C_O4_O3_O2_O1_ANDROID_GITHUB_SHA_CHAIN_READBACK`、`PASS R3C_O4_EXACT_EIGHT_6_RAW_SHA_2_302_AND_JSONLD_ROLE_CHECK`、`PASS R3C_O4_EVIDENCE_CREATE_ONLY`、`PASS R3C_O4_INDEPENDENT_RECOMPUTE_SHA_READBACK`、`PASS R3C_O4_ANDROID_AUDIT_AND_READBACK`。O4 **Android PASS**。
- O4 真實八筆：ACCUPASS #1/#2 各 1 個 Event 節點（2026-10-24～10-24／2026-10-24～11-15），OPENTIX #7 有 2 個 Event（2026-10-01～10-31／2026-11-01～11-30）、#8 有 8 個 Event（多日期候選），KidsClub #5/#6 JSON-LD Event 0，BeClass #3/#4 HTTP 302。六筆 HTTP 200 中 **所有 JSON-LD Event `url/@id` 對原始 URL SHA 精確匹配均未建立**；單靠日期字串不得接受 Golden。
- Next `R3C-O5` 只診斷**來源 URL 與 JSON-LD / canonical / og:url 的差異種類**，使用 O1 固定 URL SHA 已核准還原方法，及 O4/O3/O2/O1 既有 SHA Readback。沒有官方新 GET、沒有真正 Golden 核准、沒有發布。O5 本機 QA 即使 PASS 亦**不能**在未有 Termux 結果前標 Android PASS。
- 保留 `GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`PUBLISHED=false`；O1 `--capture` **永久不得重跑**。Roadmap 不變：R3C 人工來源真值審查 → G5J → G5K → 正式資料與 GitHub 發布 Gate。
- GitHub 治理兩份 MD 仍**尚未**發布；先前 create_branch 403。正式 Source main／Draft PR #1／Preview main 均保持凍結，禁止繞過權限。


## 2026-10-24 R3C-O5 Android 實機回報與 R3C-O6 轉人工審查

- **R3C-O5 Android PASS**：`--selftest`、`--preflight`、`--audit`、`--verify`；15 正向／6 反向、11/11 合成整合，來源八筆與 O1→O4/GitHub 鎖定鏈均通過，Create-Only 與獨立重新計算讀回 PASS。
- O5 真實結果：ACCUPASS 2 + OPENTIX 2 = `PAGE_CANONICAL_ONLY_EVENT_ID_MISSING`；KIDSCLUB 2 = `NO_JSONLD_EVENT_NODE`；BECLASS 2 = `ACCESS_UNCERTAIN_NO_BODY`（HTTP 302）。**全部 Golden HOLD**。
- 決策：停止新增重複日期/URL SHA 診斷 Gate。下一個必要交付是 **R3C-O6 人工簽認本地參考包（PREP ONLY）**，將已封存 HTML 的 Event 名稱、起訖、售票期限、canonical/og:url 與原目標 URL 於手機本機對照，另產生不含網址/標題/HTML 的可分享摘要與空白人工簽認模板。
- O6 僅讀 O1→O5，真實取證不得重跑，禁止額外網站 GET、Commit/Push/Merge、PWA/data.json 寫入、排程、自動隱藏。`GOLDEN_ACCEPTED=0`，且 O6 **不提供核准入口**。
- 遠端 GitHub source main、Draft PR #1 HEAD、Preview main 持續採固定 SHA 驗證；本輪遠端讀回與既有凍結值一致。Android O6 結果 **尚未驗證**。
- GitHub 治理文件發布仍 `HOLD_PERMISSION_403`，當前均為 Toolkit 隨附的**本地候選**，不是 repo 已 Commit 的權威文件。
- O6 完成後才由獨立人工核對決定是否有足夠活動身分、完整最後場次與明確時區來源；如不足則持續 HOLD，**不再疊加同型 Gate**。


## 2026-10-24 R3C-O6 V1.0.1 Preflight Hotfix — publication HOLD

- Android O5 V1.0.0: PASS, all previous O1-O5 evidence retained; no official-site GET was repeated.
- O6 V1.0.0: package and synthetic selftest PASS, **Android preflight HOLD O5_SOURCE_SHA_DRIFT**.
- Root cause verified against the exact O5 V1.0.0 ZIP: O6's O5 script pin contained only 55 lowercase hex characters; actual O5 source SHA256 is `41dd38dbf22ffd5db3aa0c43d919f03fef4d4a8a1ef580005dade23a603e5fdd`.
- V1.0.1: isolated local toolkit; corrected O5 authority pin; SHA-format guard and tamper regression QA. **Android V1.0.1 pending**, cannot declare O6 accepted or published.
- `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`. Source/main, PR1, PWA/data.json and Android O5 are frozen.
- Both governance documents remain **local candidate files**; GitHub publication is **HOLD** after integration write access returned 403. No GitHub SHA or version is claimed for these docs.
- Next: V1.0.1 Android preflight/build/verify; then human independent review of eight original cases; no additional HTTP until separately justified.


## 2026-10-24 R3C-O6 Android PASS 與手機人工查核增量（最新；LOCAL CANDIDATE / NOT PUBLISHED）

- **執行證據（由使用者 Termux Console 提供）**：O6 V1.0.1 `--selftest`、`--preflight`、`--build`、`--verify` 全部 PASS；`R3C_O6_O5_TO_O1_VERIFIED_SHA_CHAIN_EIGHT_SOURCE_IDS` PASS；`R3C_O6_INDEPENDENT_OFFLINE_EVIDENCE_READBACK` PASS；人工包已建立。O6 V1.0.0 因 SHA 常數錯誤 HOLD，V1.0.1 修復後實機 PASS。先前 O1～O5 Android PASS 不重跑。
- **人工查核資料**：2026-10-24 使用者手機截圖 7 張（僅在對話中供查核，不隨治理文件公開附檔）；來源 #1 ACCUPASS、#8 OPENTIX。這是獨立畫面佐證，**不是已授權的 Golden 正式接受或發布**。
- **#1 ACCUPASS**：`https://www.accupass.com/event/2610040452086680116600`，漫才 Open Mic：City Pleasure，2026-10-24 20:00～21:30 UTC+8；手機活動主頁、描述、選票頁與 O1 JSON-LD 日期相符；地點台北市中山區南京東路三段109巷16號 B1；畫面顯示「全票 10/24 NT$250」、可調整票數及「立即報名」。判定 `HUMAN_SCREEN_DATE_CORROBORATED`；**購票最終成功、售完/未售完、整體票況及截止均未證明**。購票頁倒數是流程計時，不得當成官方活動/售票截止。
- **#8 OPENTIX**：`https://www.opentix.life/event/1606114530117398530` 是「衛武營主辦節目免費身障票專區」，跨場館（音樂廳、表演廳、戲劇院）、跨節目、多場次的**資格限定票券集合頁**，不是單一一般民眾節目。2026-10-31 19:00《風箱間的四季》在該特殊入口顯示「完售」；2026-11-15 19:00 賽門．拉圖爵士與巴伐利亞廣播交響樂團亦為列表中的另一個節目。前者的一般節目頁 `https://www.opentix.life/event/2050494429271105537`；後者的一般節目頁 `https://www.opentix.life/event/2047561986406621185`，由公開 OPENTIX 頁面交叉查核。這些 URL 是**相關獨立節目頁**，不是可在未經額外對位證據下直接合併資料列的同一活動 ID。
- **審核結論**：#1 的**日期／頁面名稱**已有人工畫面佐證；#8 的**集合頁分類及跨節目性質**已有人工畫面佐證。其餘 #2～#7 保留前序 HOLD；#3/#4 BECLASS 302 保留 `ACCESS_UNCERTAIN`。`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`PUBLISHED=false`，沒有自動下架、正式資料更新、排程或 GitHub 發布。
- **權威 GitHub readback**：Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`；Draft PR #1 HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`（Open / Draft）；Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`。使用者 O6 Console 包含 Android SHA/clean lineage PASS，對話本身不能獨立持續查詢手機的即時工作樹。
- **發布界線**：此附錄僅更新候選治理檔。正式 repo main/PR #1/PWA/data.json 全部未修改；此前 GitHub 寫入整合 403，`DOCS_PUBLICATION=HOLD_PERMISSION_403`。需另行以 docs-only、exact-file、獨立遠端 readback 發布，禁止宣稱本檔已在 GitHub main。

### G5J / G5K 決策補充（規格提案；NOT IMPLEMENTED）

1. 日期真值（`event_start`, `event_end`, `event_timezone`, `date_evidence`）與即時票況（`ticket_availability`, `ticket_status_observed_at`, `ticket_scope`）分離。活動有正確日期不等於仍可買票；「立即報名」不保證購票成功；HTTP 200/JSON-LD/`offers.validThrough` 不可單獨觸發下架。
2. `ticket_availability=UNKNOWN` 為合法預設；PWA 可顯示「查看官方最新票況」並開啟對應原始官方網址，**不需強制提供售完／截止狀態**。若明確觀察到「完售」，只能記錄**該票種／該場次／該網路入口／觀察時點**，不得擴大成所有場次或一般民眾票券皆售完。
3. `SPECIAL_ELIGIBILITY_TICKET_PORTAL` 應與 `SINGLE_PERFORMANCE`/`MULTI_PERFORMANCE_EVENT` 分類區隔；#8 跨場館集合頁不可拿 11/28 當整個專區的永久有效期，不能使用 NT$0 推論一般民眾免費。一般節目頁僅為候選交叉參考，建立每一場次的正確映射後才能處理去重。
4. **下一步**：不再新增同型 SHA/日期診斷 Gate。用已有人工作業證據填寫簽認模板，將 #1 的日期證據與 #8 類型證據送人工獨立核准；依 G5J → G5K 既有 Roadmap 檢查可逆顯示、標籤與連結 UAT。人工核准／正式 data.json/PWA/排程/merge 必須各自獲得既定授權。


## 2026-10-24 SRC-P1 活動平台資料擷取改善（候選、尚未 Android 驗證及 GitHub 發布）

- 使用者於 2026-10-24 授權將 **各平台資訊取得品質** 調整為近期 P0 第一優先；保留既定 Roadmap `G5I → G5J → G5K → 發布`，SRC-P1 是 G5I/來源品質的新增實作支線，不代表啟動 G5J 自動失效決策。
- 來源固定：Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`；PR #1 Draft HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`；Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`；Parser Git blob `ed425662b4f2ce2032a0fa0c3e83075842f30767`。
- 真實代碼檢查：`show_news.py` 是運作程式，`event_details.py` 是既有 parser；禁止建立平行爬蟲、第二 parser、新資料庫。
- SRC-P1 候選：`fetch_accupass_events_list()` 增加同平台絕對網址精確辨識；`fetch_text()` 修正 UTF-8 ignore 破壞 Big5 的風險；`fetch_opentix_events_list()` 為特殊資格集合標識來源角色；`fetch_kidsclub_events_list()` 將課程／商品列表保留為未核驗目錄；`extract_event_details_simple()` 與 `parse_detail()` 只增加來源角色及 `ticket_availability=UNKNOWN`，阻止特殊資格專區以其中場次日期推定整站過期。
- 本次只交付 **隔離候選完整程式與 diff**、正反向 QA、Termux preflight；不修改 Android Source Git 工作樹、不 Stage/Commit/Push/Merge、不重跑 O1 的八筆 GET、不改 PWA/data.json/排程。Android 實機未回報前 **SRC-P1=HOLD（候選）**。
- 後續階段：逐平台取得方式與欄位缺漏率比較（OPENTIX、ACCUPASS、BeClass、KidsClub → KKTIX、拓元、FamiTicket、TixFun 等），用限制筆數、限定來源的 Wi-Fi/行動網路對照作補充證據；HTTP 200/302/售完按鈕不直接當成 Golden 或活動有效性。
- 治理文件依然是 **GitHub 尚未發布的本地候選**；既有 403 寫入限制未解除，不能聲稱已發布。


## 2026-10-24 SRC-P1 / SRC-P2 取得能力品質波次

- **SRC-P1 Android PASS**：本輪 Termux 執行實際出現 `PASS SRC_P1_TWO_FULL_CANDIDATE_SOURCE_FILES_CREATE_ONLY`、`PASS SRC_P1_EXISTING_EVENT_DETAILS_AND_G5H_UNITTEST_DISCOVERY`、`PASS SRC_P1_INDEPENDENT_RECOMPUTE_PATCH_SHA_READBACK`、`SRC_P1_REAL_WORKTREE_CHANGED=0`；9,850 筆凍結資料欄位存在率已建立。此項 **不是**已部署或現場欄位改善率。
- **P0 優先**：BeClass 4,472 筆日期僅 1、ACCUPASS 733 筆四核心欄位皆 0、OPENTIX 2,535 筆日期 1,551；台北世貿 586 筆日期／地點／票價皆 0。須以取得品質而非反覆日期 SHA Gate 排優先。
- **NEXT SRC-P2**：已完成獨立 Toolkit，先 O1 六份封存 HTML 解析 A/B，再獨立旗標限 4 個官方列表入口各一次 GET（ACCUPASS/OPENTIX/BeClass/KidsClub），不得重抓 O1 原八筆；GitHub/PWA 不修改。Android 結果尚待真實執行，**不許提前標記 PASS**。
- 後續：依 SRC-P2 A/B 實際取得改善與回歸情況，最小範圍修正 SRC-P1 侯選，然後完成各平台來源欄位真值 / 人工簽認。**G5J → G5K → 發布**方向不改。
- 治理文件仍為候選，GitHub 因先前 integration 403 無法發布；不可宣稱已提交 main 或生成 Draft PR。


## 2026-10-24 SRC-P2 Android 實機 PASS 與 SRC-P3 續作（候選文件，未上傳 GitHub）

- SRC-P1：完整候選源碼與 9,850 筆存在率基線，Android selftest/preflight/build/verify PASS；未修改工作樹。
- SRC-P2：Wi-Fi 真實四個官方列表 GET（ACCUPASS=200、OPENTIX=200、BECLASS=302、KIDSCLUB=200）與封存證據讀回 PASS；兩個來源解析器對 O1 六份 HTML 的 date/location/price/description 存在率未改善。
- SRC-P2 用戶證據：四筆一次性 GET Ledger 與三份 raw HTML 已保存，**禁止再次執行 capture-live**。三筆 HTTP200 ≠ 已驗證來源內容；BeClass 302 ≠ 零活動。
- SRC-P3：只讀 SRC-P2 封存 HTML 與 P1 候選程式的來源 URL／DOM 選擇器差距矩陣，不重新 GET、不修改正式 main/Draft PR/PWA/data.json。利用實機真實列表結果優先排序 platform fetch 函數修復。
- Android 本地 Git Branch／HEAD／Clean 由 SRC-P2 原本的唯讀權威入口重新驗證；GitHub 遠端來源 HEAD 仍需每輪重新核對。
- Golden=0、AutoHidden=0、Published=false；下架證據 G5J 與 PWA UAT G5K 不提前發布。
- GitHub 對 docs-only 建分支先前回覆 403，兩份治理 MD 仍為**未發布候選**；不得宣稱已成為 Repo 權威。

## 2026-10-24 SRC-P3 Android PASS → SRC-P4 詳頁取得功能修復（候選／未發布）

- 使用者 Android 回條已驗證 `PASS SRC_P3_ANDROID_AUDIT_AND_READBACK`，含 Wi-Fi 列表封存證據 SHA 讀回；**SRC-P1／P2／P3 不重做**。P2 的四個一次性 GET Ledger 已使用，不得再次執行 `--capture-live`。
- SRC-P3 真實列表分析：ACCUPASS 50 個活動錨點、舊版/嚴格候選皆 25 筆（增量 0）；OPENTIX 1,081 個嚴格候選、3 個特殊資格文字連結；BeClass 302（不能視為 0 筆）；KidsClub 12 張有價商品卡片。只代表該列表快照的 HTML 結構，未證實全部活動與票況。
- **P0 新順序：ACCUPASS 詳頁來源時間／身分／欄位 → OPENTIX 一般售票與特殊資格跨節目集合 → BeClass 302 轉址及網路環境契約 → KidsClub 課程日曆。** 不再擴寫沒有證據增量的 ACCUPASS 列表 Selector。
- SRC-P4 V1.0.0：以原凍結 PR SHA、SRC-P1 完整候選及 O1 六份封存 HTML 為實際入口，**新增 ACCUPASS 同一 Event 節點 ISO 開始／結束時間候選**與 **OPENTIX 特殊資格頁多節目時間清單候選**。`event_details.py`/`show_news.py` 仍是唯一正式目標，P4 僅在 Toolkit 內建立兩份完整候選檔與 Diff，不更動工作樹；採官方來源身分拒絕錯配、未知時區提示、多節目不得設定整頁 expiry。
- P4 以 O1 原八筆 SHA 證據進行 P1 vs P4 解析 A/B，保存各平台 date/location/price/description **存在率及新增時間候選計數**；不得把候選時間當作活動有效性已驗證或宣稱 733 筆歷史資料已修復。缺乏增量必須如實填 0。
- **狀態：SRC-P4 本機 QA 為候選；Android `--preflight/--build/--verify` 未回報前 HOLD。** `GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`PUBLISHED=false`，不允許更新正式 main、PR #1、Preview、`data.json`、排程。
- GitHub 兩份治理文件仍為「本地候選」；先前 docs-only 建分支回覆 403，未獲成功 GitHub 發布證據前不得標記已在 Repo。以遠端 HEAD／Android 自有本地分支、HEAD、Clean 的每輪實測為準。
- 後續依 P4 內容 A/B 實際改善決定下一個最小功能修補，不重複 SRC-P1～P3 已通過 Gate；原 Roadmap G5I → G5J → G5K → 發布不變。


---

## 2026-10-24 SRC-P4 Android PASS → SRC-P5 BeClass mobile one-GET diagnosis (unpublished candidate)

- SRC-P4 Termux `--build` / `--verify` PASS; P1→P4 ACCUPASS complete timestamps 0→2, OPENTIX special collection session candidates 0→8; core Date/Location/Price/Description unchanged, BeClass stays 302, KidsClub still unknown. Candidate only, source tree unchanged.
- SRC-P5 is scoped to P2's **exact same BeClass ShowRegist listing URL**, cellular user-attested once (not a P2 retry), to compare response status and redacted Location. Must verify P2 Wi-Fi receipt SHA and GitHub/local frozen HEAD first, then create-only attempt prior to GET. No redirects, retry, cookies or challenge bypass.
- If 200, record only candidate rid-link count, not activity truth; if 302, retain ACCESS_UNCERTAIN. Do not assume mobile transport from the script, rely on user network-setting confirmation.
- Golden=0, auto_hidden=0, published=false. No production data, PWA, main, or Draft PR #1 mutation. Two governance documents remain local candidates: GitHub docs-only publication was previously blocked by 403, no branch/commit/push.
- Following P5: use actual redirect evidence to repair `fetch_beclass_events_list()` / `extract_event_details_simple()` in **candidate code**, then test on pinned samples and only request further live retrieval if necessary.

## 2026-10-24 SRC-P5 Android PASS and SRC-P6 development (local candidate; NOT GITHUB PUBLISHED)

- SRC-P5 Termux mobile-data user-attested one GET passed, HTTP 302 with same-host redirect. P5 readback PASS, no redirect followed, no retry. Wi-Fi P2 also 302. No evidence supports mobile data improving outcome. Do NOT re-run any P5 or P2 capture or delete ledgers.
- The P5 `Location` SHA256 `06083d838c53488587c26aedaff42f4372de5fb7d75cf107de1e1213a46f888d` matches exactly `https://www.beclass.com/m/default.php?name=ShowList&op=ShowRegist&od=&page=1`. Path SHA independently matches `/m/default.php`. This is mobile canonicalization evidence; it does NOT demonstrate a functional 200 response or BeClass source correctness.
- Actual `show_news.py` BeClass list request uses aiohttp with default redirect behavior; an explicit no-redirect 302 capture cannot by itself prove a crawler outage. SRC-P6 extends the **existing** BeClass function with strict same-host one-hop redirect and official `rid` filtering, candidate-only explicit activity date; no commit/push, no production repair or data.json changes.
- SRC-P6 only proposes optional a single GET of the SHA-bound mobile landing (no original URL GET), once, after preflight and new authorization flag. Raw public HTML remains Android-private, creates receipt+SHA, never approved as Golden without human review.
- PRIORITY P0 platform source acquisition: review SRC-P6 mobile listing, then identify actual BeClass detail field layout to improve 4472 historical rows through bounded candidate-only enrichment. OPENTIX multi-program/ACCUPASS datetime candidates in SRC-P4 remain Android PASS, not deployed; KidsClub still awaiting date extraction.
- Two governance MD files are local candidates because GitHub writes are 403. Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`, PR #1 Draft `26888422e48634d9729d2deea67b7996a5d1e4ee`, Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`, read-only verified in this turn. Golden=0, auto-hidden=0, published=false. Do not close or merge PR without separate approval.

## 2026-10-24 SRC-P6 Android PASS → SRC-P7 BeClass RID functional remediation (local, NOT GitHub published)

- SRC-P6 Android `--build`, `--verify`, one-shot Wi-Fi `--capture-mobile-listing`, `--verify-live`: PASS. SHA-verified HTTP200, raw 19,745 bytes SHA `834196a704703eef935a6d4c62375fb1d1510a2bcad3b7dc5a2671550dd99631`; 20 `rid=` anchors, but `strict_distinct_rid_urls=0` and no verified title. All prior P1–P6 Android PASS retained; do not rerun captures or replace attempt ledgers.
- Root discrepancy: SRC-P6 `beclass_rid_url()` accepts only strict direct `/rid=<16..28 hex>` while live mobile HTML has 20 apparent rid anchors. Exact shapes of raw hrefs must be derived **offline** from the private P6 snapshot; don't assume all are real events.
- SRC-P7 reconstructs a full *candidate* `show_news.py` with source-safe BeClass rid canonicalization, same-card title heuristics and source-role conservative handling. Reads exactly the P6 sealed HTML locally, compares normalized/titled candidate counts to P6 0; emits sanitized aggregates, full candidate, diff and SHA-verifiable output. Never exports raw HTML/URLs/titles. No HTTP GET, no source worktree write, no official data/PWA change, no Golden approvals, no auto hide.
- If candidate counts are zero, preserve HOLD and use aggregated href shape classification to fix exact false-negative. A positive count is parsing coverage only and is NOT correctness or Golden acceptance. Next: subject to real result, address BeClass detail-date extraction and bounded update/UAT, OPENTIX & KidsClub remain P0 source quality tasks.
- GitHub authority remains source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`, PR #1 Draft `26888422e48634d9729d2deea67b7996a5d1e4ee`, preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000` as checked this turn. Governance docs are local candidate; GitHub write 403 HOLD. No merge/close/push/commit/deploy.

### 2026-10-24 SRC-P7 Android evidence + SRC-P8 gate
- SRC-P7 user-reported Android `--selftest`/`--preflight`/`--build`/`--verify` PASS; P6 immutable HTTP200 19,745-byte HTML, 20 `RID_PATH_MOBILE` anchors; old 0, P7 safe-canonical 20/20, attributed title 20/20. **No Golden acceptance**. Preserve P1–P7/O1–O6 PASS.
- SRC-P8 next: exact BeClass detail date/location field-role function patch inside existing `show_news.py`, offline evidence then optional user-executed two exact mobile detail GETs with immutable ledger. Do not rerun P6 listing or accept all 4,472 historical rows; no stock guess, no auto-hide, no data/PWA writes.
- State: P8 is *candidate*, awaiting Android verification and human date/identity review. Remote GitHub governing MD publication continues HOLD (known connector 403); this bundled copy is not remote authority.


### 2026-10-24 SRC-P8 V1.0.1 定點修復候選（Android 待驗）
- V100 Android Selftest／Preflight PASS，Build 因 P8 使用過時 V43 detail tail `HOLD SRC_P8_P7_DETAIL_COMMIT_ANCHOR_DRIFT`。之前 SRC-P1～P7 Android PASS 均保留；P8 兩筆官方 GET 尚未執行。
- V101 嚴格鎖定現有 P1/P4 全函數尾端，保留特殊資格、票況 UNKNOWN、KidsClub 課程類別與 P4 時間來源保護；使用新版 Create-Only 證據目錄，無 GitHub、PWA、data.json 寫入。
- 僅本地治理文件候選；GitHub docs-only publication HOLD，必須獨立讀回。Golden=0、auto-hidden=0、published=false。


## SRC-P8 V1.0.2 — Two-target plan serialization repair (2026-10-24; local candidate only)

- **Accepted Android V101**: package/preflight/build/verify PASS; capture HOLD `SRC_P8_TARGET_PLAN_MISSING` before live ledger creation and before either GET. V100 remained build HOLD. All P1–P7 Android PASS retained.
- **Root cause**: `select_targets()` already returns exactly original P6 listing ordinal indices 0 and 10; V101 `offline_files()` filtered `enumerate(targets,1)` using `i in (1,11)`, resulting in only one target in `read_only_plan.json`. In V102, serialize both selected SHA-bound targets as final ordinals 1,2 without re-filtering.
- **Defensive gates**: exact `make_plan` contract, two distinct target hashes, full plan regeneration during offline verify, old V101 live-ledger stop gate prior to V102 GET, and regression with twenty RID-shaped anchors plus mock live capture, pre-ledger tamper checks and no second request.
- **Boundaries**: one new V102 candidate and two bounded HTTPS GETs only after user executes authorized capture; no automatic retry, redirect, login, batch backfill, Golden acceptance, auto hide, worktree changes, GitHub write, PWA or data.json write.
- **Status**: V102 local toolkit QA pending/current; Android outcome not yet known. GitHub governance publication HOLD 403; this is not a GitHub published document.

### 2026-10-24 SRC-P8 V102 Android PASS / SRC-P9 offline field-role candidate
- User Android SRC-P8 V102 Selftest/Preflight/Build/Verify PASS, two exact HTTPS GETs HTTP200/HTTP200, private HTML and SHA independent readback PASS. Two titles present, explicit event-date candidates 1/2, explicit location candidates 0/2. Do not repeat these GETs or invalidate earlier P1-P7/O1-O6 passes.
- SRC-P9 next: use ONLY the two private P8 SHA-pinned HTMLs to compare P8 and enhanced bounded DOM role parsing for BeClass date/location. Create full existing `show_news.py` candidate and byte-exact diff; keep form/input/registration stock/date excluded and conservative hold on conflicting values. No network, public data writes, side-effect, PR merge or PWA update. No assumption about actual improvement until Android AB.
- Status before Android verification: P9 local candidate / Android pending; Golden=0, Auto-hidden=0, Published=false. Remote GitHub governance docs remain unpublished because connector 403, do not assert publication.

## 2026-10-24 SRC-P9 Android PASS → SRC-P10 source-only integration candidate (LOCAL, UNPUBLISHED)

- SRC-P9 user's real Termux `--selftest/--preflight/--build/--verify` **PASS**, no new GET. Same SHA-locked P8 V102 two HTTP200 private HTML: date presence **1/2 → 1/2**, location presence **0/2 → 1/2**, titles **2/2**. Page 2 location conflicts (`CONFLICTING_LOCATION_LABELS_HOLD`): do NOT choose either candidate. Page 1 no explicit event date. None is Golden. Preserve P1–P9 passes and original P8 GET Ledger.
- SRC-P10 single PR1-source-bound integration candidate: full `show_news.py` from accepted P9 and full `event_details.py` from accepted P4, exactly two files. Recompute all original blobs, upstream scripts and frozen Android receipts; run real existing G5H regression tests in isolated temp, PR1-exact patch application check in temp, and byte-exact independent readback. **No new website GET, no working-tree changes, no GitHub writes, no PWA data mutation.**
- Integration candidate is not merged and not a user's acceptance of release. PR #1 remains **OPEN/DRAFT** (not Ready, no merge/close), and default main and preview are frozen. Two governance docs remain *local candidate versions*, not GitHub authority until explicit publication + remote readback. No current permission to alter GitHub or schedule.
- Remaining **P0 acquisition**: BeClass dates missing on some detail layouts; conflict-safe location identity review; 4,472 frozen historical rows not backfilled; ACCUPASS/P4 datetime candidates need source identity+UAT; OPENTIX multi-program separation; KidsClub session calendar extraction. **P0 data quality UAT and bounded candidate-only enrichment** should follow successful integration Gate before G5J/G5K publication.
- Gate states `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`. 9,850 baseline is frozen presence-only data, not live completeness.

## 2026-10-24 SRC-P10 Android 實機 PASS / SRC-P11 UAT 候選（本地增量；未上傳 GitHub）

- SRC-P10 實機：兩檔整合 SHA `show_news.py=3eb32f9df50b55a2aa34515f36fa718f72d0097071a2068086d18ba5ddca8fb6`、`event_details.py=2cac084b2ad0ed28baf1e98388e3686746d83d06e2403f586e85ee1484d38595`；原 PR #1 Blob／完整 Diff `git apply --check`、G5H Regression、獨立重算皆 **ANDROID PASS**。PR #1 仍 Draft，實際業務資料未寫入。
- SRC-P9 真實兩份 HTML 的 A/B：日期 1/2→1/2，地點 0/2→1/2；第 2 筆 `CONFLICTING_LOCATION_LABELS_HOLD`。SRC-P7 列表 20/20 RID 安全正規化／標題；仍非 Golden。
- SRC-P11 **新任務：人工來源 UAT 取證候選**。Android 私有來源核對單與可回傳遮蔽摘要分開儲存，保持 `GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 PUBLISHED=false`。兩筆樣本不得外推修補 4,472 筆 BeClass 資料。
- 管治約束：本文件本地候選版不等於 GitHub 正式治理基線；Github 文檔發布原 403 HOLD、主源 HEAD 與 PR #1 不得未授權變更；保留既有通過 Gates。


## 2026-10-24 SRC-P11 Android PASS + 真人 BeClass 官網畫面 UAT：候選欄位與多選項展示策略（本地增量）

- SRC-P11 user Termux Package/Selftest/Preflight/Build/Verify/Private Review **PASS**；`HOLD HUMAN_FIELD_SIGNOFF_REQUIRED` 是業務真值標記，非程式 Gate 失敗。保留 `GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 PUBLISHED=false`，既有 P1～P10 Android PASS 全不重跑。
- 本輪使用者提供兩筆對應 BeClass 官網頁面截圖：A `課程日期` 明確顯示民國115/10/31 09:00–12:00，P11 解析 UNKNOWN 為**漏抓**；A 有課程實體地址、同頁還有視訊選項。B 頁首日期 2026-10-26、說明另列 10/25/10/26，屬可能多日活動而非必然錯誤；有活動場域文字，P11 地點標籤歧義僅代表**不能自動寫入唯一地址**。兩頁標題身分對位。票價具條件（A 課程費用、B 一般遊客 vs 住宿參加）。僅記錄公開活動內容與彙總，不收錄截圖中的付款/個資。
- 使用者決策：活動雷達是**來源導流與摘要**，應允許不完整、多場次、多地點、不同票種價；且 UI 以既有免責位置修改成「活動資訊僅供參考，請以官方網站及主辦單位最新公告為準」。仍須防止已知錯誤、缺資料誤隱藏、售票/報名期限充當活動日、特殊資格免費價當一般售價。
- 此次判定為 `HUMAN_SCREEN_CORROBORATED` **不代表 Golden Ledger 正式完成**；P11 的人工核對紀錄和自動 Golden acceptance 分開。新增本地政策文件 `SRC_P11_UAT_DISPLAY_POLICY.md`，作 P12 Preview UI 候選與來源語意 UAT 依據；**不授權** GitHub 寫入、改正式 data.json、Merge PR、開通知或大批次回補。
- 下一順序：P12 既有 Preview `index.html` 文案+安全缺值呈現候選 → Source P10 既有函數補課程日期和多選項來源角色 → 受控隔離 UI/data UAT → G5J/G5K。避免再造相同 Gate。


## 2026-10-24 SRC-P12 UI／來源日期角色實作候選（待 Android 實機驗收）

- 使用者已同意實作 P11 所提務實活動呈現規則。P11 技術 Android PASS、使用者官方頁截圖佐證 A「課程日期 115/10/31」，B「主標示 10/26、內文另列 10/25/10/26」；**本輪不自動 GOLDEN**。
- SRC-P12 V100 是**Create-Only 離線候選**，預計生成 `candidate_source/show_news.py`、原 SHA 不變的 `event_details.py`、`candidate_preview/index.html` 和兩個 Diff、紅acted A/B。需 Android Selftest/Preflight/Build/Verify 才可標記 ANDROID PASS。
- PWA 原第116行 `.disclaimer` 原位改成官方公告優先；詳情 Modal 新增完整說明，缺值標示改成「日期／地點／票價請見官方」，並可選擇支援明確 `display_roles` 的 MULTI_SESSION、MULTI_LOCATION、HYBRID、CONDITIONAL_PRICE（現行 `data.json` 無此 schema，不加欄位）。
- P10 已凍結 `show_news.py SHA256 3eb32f9df50b55a2aa34515f36fa718f72d0097071a2068086d18ba5ddca8fb6`、`event_details.py SHA256 2cac084b2ad0ed28baf1e98388e3686746d83d06e2403f586e85ee1484d38595`；P12 只在同一 `beclass_detail_roles()` 增加 `課程日期`／`上課日期` 民國年，保留原 P9 日期／地點判定和 B 競爭地點 HOLD。多日與條件費用不轉單一覆寫值。
- **不覆寫** `~/eventradar`、`~/eventradar_preview_site`、9,850 筆正式 data.json、雲端 Actions，不能解除 PR #1 Draft、合併或自行發布。正式治理 MD GitHub 403 HOLD 未解除；本文件是 ZIP 候選。
- 若新的 HTML A/B date/location 未改善，也只標示零增量；不得宣稱真值通過。下一步依 P12 A/B 做隔離 UI UAT、資料角色 schema 審查，再行 G5J/G5K。
- 保留 P1–P11 Android PASS，SRC-P8 V100/V101 的歷史 HOLD。`GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 PUBLISHED=false`。


## 2026-10-24 — SRC-P12 Android PASS / SRC-P13 candidate (local, not GitHub published)

- SRC-P12 Android: `--selftest`, `--preflight`, `--build`, `--verify` PASS; PWA display contract candidate PASS. First BeClass class-date **still UNKNOWN**, so course-date capture improvement HOLD. Second date remains present, conflicting venue remains HOLD. `GOLDEN=0 AUTO_HIDDEN=0 PUBLISHED=false`.
- SRC-P13 V1.0.0: bounded BeClass adjacent DOM label/date parser **candidate**, based on exact P12 `show_news.py` SHA `1c2eded2999cb28ce8e635d360e80bfb84841a4150311c34e62b49e2e5a8e155`. P12 Preview SHA `802168998ad83d1155e8c010f83205b3229722e2b7bf60ceb6b35aafdf36137a` immutable; parser `event_details.py` SHA `2cac084b2ad0ed28baf1e98388e3686746d83d06e2403f586e85ee1484d38595` immutable.
- SRC-P13 requires offline Android AB on P11's two previously archived official details; no new HTTP GET or historic data overwrite; no new branch or PR merge. Real AB may show zero gain, and must not be mislabeled PASS for source quality.
- Pending: UI isolated preview/manual UAT, PR source review/authorization, two governance docs official GitHub publication (previous 403), then G5J/G5K. Previously passed Android Gates remain frozen.

## 2026-10-24 SRC-P13 → P14 addendum (本地候選，尚未發布 GitHub)

- SRC-P13 Android 依使用者 Console: package/Selftest/Preflight/Build/Verify PASS；在相同封存兩份 BeClass 詳情 HTML 中，日期候選 `1/2 → 2/2`、標題及地點角色沒有退化、第二筆地點衝突繼續 HOLD。
- SRC-P12 Android: PWA 免責／缺值／多選項呈現候選 Build/Verify PASS；實際畫面 UAT 尚未完成，故 SRC-P14 用隔離九筆**完全虛構資料**進行 UI 測試。
- SRC-P14 范圍: 真正 P12/P13 未變更 `index.html` + frozen G5C/G5D JS + 9 synthetic cases，僅執行本機 localhost 靜態 HTTP Server；無正式 9,850 筆、無 PR push/merge、無 Cloud Actions 或業務資料變更。
- SRC-P14 機器 QA PASS 不代表人眼畫面已 PASS。Android 人工觀察記錄另立 UAT，不可自動 Golden 批准。
- 唯一正式權威仍應是 GitHub 主治理文件；本文件尚未提交，不能宣稱 GitHub governance 更新完成。2026-10-24 HEAD: Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`、Draft PR #1 head `26888422e48634d9729d2deea67b7996a5d1e4ee`、Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`。
- G5J 有效性引擎仍 OPEN；G5K 真正候選資料 UAT/發布仍 HOLD。SRC-P14 只滿足先行之「純合成 UI 功能驗收」，不得表述為整套 G5K PASS。


## 2026-10-24 SRC-P14 實機列表驗收與 SRC-P15 卡片摘要候選（本地治理增量，未發布）

- SRC-P14 Android：Toolkit Selftest/Preflight/Build/Verify PASS；`127.0.0.1:18766` `index.html`、G5C/G5D JS、9 筆合成 `data.json` HTTP 200；畫面顯示 9/9 虛構活動、免責與卡片。`favicon.ico` 404 不屬於資料功能故障。
- SRC-P14 詳情視窗逐一 UAT **尚未完成**，不得宣稱 9/9 互動 PASS。現有卡片缺值仍為 `詳內文`，列為確定 UI 改善。
- SRC-P15：使用與 SRC-P14 相同 9 筆**虛構**資料、相同 P12/P13 候選 UI；只改列表卡片摘要為三行日期、地點、票價，完全採用 `referenceFieldText()` 角色契約、HTML escape，減少簡略卡片誤導。
- 正式 9,850 筆 `data.json`、GitHub Source/Preview、排程及通知不變；Draft PR #1 未 merge；Golden=0、Auto hidden=0、Published=false。
- 下一 Gate：SRC-P15 Android 獨立列表與詳情互動 UAT（port 18767），再進入 GitHub PR 來源功能收斂與 G5J/G5K 隔離資料策略。

## 2026-10-24 SRC-P15 Android 九案詳情 PASS → SRC-P16 三檔整合 PR 審查候選（本地未發布）

- SRC-P15 使用者回傳 9 張 Android Chrome modal 截圖；與之前 9 筆列表／卡片截圖共同形成 **9/9 合成 UI 視覺 UAT PASS**。一值、缺值、多場次、多場地、條件票價、安全官網按鈕停用及免責文字均依設計顯示。合成 UAT **不是**真實來源 UAT／發布。
- SRC-P13 真實封存 BeClass 兩筆日期候選 1/2→2/2；P9 地點 0/2→1/2，另一筆 conflict HOLD。P7 20 個手機版 RID 可正規化且標題歸屬；4,472 歷史資料未變。`GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 PUBLISHED=false`。
- SRC-P16 next: SHA-bind P13 full `show_news.py`, unchanged `event_details.py`, P15 full Preview `index.html`；產出三個 **對原始凍結 Git Blob** 的 patch、隔離 `git apply --check` 和 G5H 回歸報告；Android 實機未報結果前不可標記 P16 Android PASS。
- GitHub Connector 2026-10-24 讀回 Source `main@6004754f90d551cdb0cdb91a3e04b42c04f45f48`、PR #1 **Open/Draft** `26888422e48634d9729d2deea67b7996a5d1e4ee`，Preview `main@a8cde084ab5581736d86094d8cdcc2cdc9963000`。Source/Preview repo 的**獨立 Issues 查詢未回傳結果**，不是全部 closed 的認證，不創造 Issue。
- SRC-P16 即便 PASS 也只表示「三檔可審查候選／P15 合成 UI PASS」；正式 Source/Preview PR 和治理文件 GitHub 發布仍 `HOLD`，PR #1 Cloud Scheduler 不解除 Draft，不合併／不執行部署／排程／通知。G5J、G5K **OPEN**。

- PR #1 GitHub `list_pr_changed_filenames` 本輪讀回涵蓋 7 項 workflow 與 `scripts/commit_data.sh`、來源/解析器、測試等；不能把 SRC-P16 來源 patch 的 PASS 當作 Cloud Scheduler/整份 PR 合併權限。

## 2026-10-24 — SRC-P16 實機 PASS 與 SRC-P17 分流審查候選（尚未 GitHub 發布）

- 使用者回報 SRC-P16 Android Package/Selftest/Preflight/Build/Verify/G5H/Git Apply/SHA READBACK 全 PASS。候選檔 SHA256：`show_news.py=32efcdc02d16791213973bb14ee61811522eaee83f4cdb2387d492477ec41ccd`、`event_details.py=2cac084b2ad0ed28baf1e98388e3686746d83d06e2403f586e85ee1484d38595`、`index.html=da73c977d72c71e9d102c2b267574775c4738def782755380fcaa771793082be`。
- GitHub 即時核對：Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`；PR #1 Open/Draft/Unmerged HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`；Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`；PR #1 changed files **34**，其中 7 項 `.github/workflows/`。Issues 查詢沒有獨立 Issue；不得因此宣稱沒有 OPEN 任務。
- 讀回 PR1 的 `.github/workflows/event_radar.yml` 含 `schedule`, `workflow_dispatch`, `contents: write`, `scripts/run_show_news.sh --once`, `scripts/commit_data.sh`；`scripts/commit_data.sh` 含 `git push origin HEAD:main`。Cloud Scheduler 是另一路高風險 HOLD，不隨 P16 解析修補直接 Merge。
- SRC-P17 本地候選：讀取上述凍結工作樹與 P16 SHA，輸出 `risk_matrix`, `release_routes`, `PR_ISSUE_CLOSURE_AUDIT`, `NEXT_TASK`，**Android 尚待驗證**。規畫 A Source 兩檔獨立 Draft PR、B Preview `index.html` 獨立 Draft PR、C Cloud Scheduler 繼續 HOLD、D 治理文件分支 PR、E G5J/G5K 真實資料 UAT。
- `GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 PUBLISHED=false`；不修改正式 `data.json`、主線、PWA、通知與 Actions。這份 MD 尚在 Toolkit 中，非 GitHub Authority。

**防錯基底補充**：P16 的 source Diff 為 `PR1 HEAD -> P13 Candidate`，不代表對 `main` 可直接套用。新 Source-only Draft PR 須從 frozen `main` 出發，精確重建必要依賴與測試，避免把 PR1 34 檔及 Cloud Scheduler 帶入；該步驟維持 HOLD，下一 Gate SRC-P18 優先完成。


## SRC-P18 main-based source-only additive PR preparation (2026-10-24; local candidate, NOT GITHUB-PUBLISHED)

- SRC-P17 Android PASS: main `6004754f...`, PR1 Draft `26888422...`, PR1 changed 34 all-added files and 9 risk-target blob audit PASS.
- NEW finding: Source main contains only eight legacy paths; no `show_news.py`, no `event_details.py`, no G5H tests. PR1 HEAD added 34 paths.
- SRC-P18 is a main-based **dormant five-path new-file patch** (`show_news.py`, `event_details.py`, `requirements-actions.txt`, two `test_event_details*.py`); do not add workflows/commit_data, do not change scraper.py/docs/data.json.
- P16 source SHAs pinned; Android P18 result PENDING. Source-only Draft PR creation requires separate authorization/working GitHub write credential, CI and readback. PR #1 stays Draft/unmerged; Preview UI independent. G5J/G5K, 4472 BeClass historical repair and official Golden all HOLD.


### SRC-P18 V1.0.1 — fresh evidence parent bootstrap correction (2026-10-24)

- V100 Android selftest/preflight/five-file main additive patch/G5H PASS; BUILD HOLD `EVIDENCE_PARENT_BAD` before writing output due to missing extracted `evidence/` directory. No source Git write or website GET.
- V101 corrects create-only bootstrap only for `evidence/` and adds missing-parent/symlink/path-traversal/re-entry negatives. New output root; do not alter V100 evidence. V101 Android BUILD/VERIFY remains **pending** until host results.
- Existing SRC-P1–P17 and Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`, PR #1 Draft `26888422e48634d9729d2deea67b7996a5d1e4ee`, Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000` unchanged subject to fresh independent readback. Governance text candidate local-only; GitHub not published.
- `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`, Source-only five files DORMANT; G5J/G5K remain OPEN/HOLD.


## 2026-10-24 SRC-P18 V101 Android PASS / SRC-P19 同步審查

- SRC-P18 V101 的五檔 main-based source-only additive candidate，Android 端 exact eight + PR1 thirty-four + SHA + G5H + independent readback 均 PASS。SOURCE_STATUS=ADDITIVE_DORMANT_NOT_WIRED_TO_MAIN_RUNTIME。
- SRC-P19 目的：只讀驗證 Source-only 與 Preview index.html 兩條獨立 Draft PR 發布就緒性與安全約束；不得藉由執行 Gate 建立分支／PR／Commit／Push／Merge，也不得修改正式資料。
- PR #1 Open/Draft/Unmerged，仍包含高風險 schedule/workflow/commit_data.sh，維持 HOLD；PWA 測試 P15 九卡片及九詳情人工 UAT PASS。
- GitHub 兩份正式治理 MD 尚無遠端發布證據，所有本地增量仍是候選。
- G5J/G5K，Golden=0，自動隱藏=0，正式發布=false。


## 2026-10-24 SRC-P20 授權與 GitHub 403 最新增量（本地候選）

- **SRC-P19 Android 已 PASS**：Source 五檔新增／Preview 單檔修改的兩條獨立 Patch，`git apply --check`、重建與 SHA 讀回通過；PR 未建立。
- 使用者於本輪明確授權：兩個 Repo 由已驗收 Patch 各建立一條獨立分支、一個非強制 Commit、一個 Draft PR，完成遠端 SHA／檔案白名單讀回；**不得 Merge、解除 Draft、改 `main`、改原 PR #1、發布資料、啟用雲端排程、通知或正式 PWA**。
- 已立即重新唯讀核對：Source `main@6004754f90d551cdb0cdb91a3e04b42c04f45f48`、PR1 Draft HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`、Preview `main@a8cde084ab5581736d86094d8cdcc2cdc9963000`；當時目標分支不存在。
- GitHub Connector 分別執行 Source/Preview `create_branch` **均回傳 HTTP 403 `Resource not accessible by integration`**；**尚未建立任何新遠端分支、Commit、Draft PR**。雖 GitHub Repository permissions 顯示 push=true，並非該 App 可實際建立 Git ref。
- 已準備 SRC-P20 單 ZIP Termux 受控替代路徑：`--preflight / --stage / --publish / --pr / --verify`。僅以 P19 已通過的實機證據資料 `source_pr/0001_source_only_main.patch` 與 `preview_pr/0001_preview_ui_main.patch` 為來源，隔離 Clone，雙分支非強制 Push，使用 `gh pr create --draft`，要求逐條遠端 HEAD、base、六檔及狀態讀回。
- SRC-P20 **本機 Toolkit QA** 不得標為 Android 遠端發布 PASS。依使用者後續 Console 和 GitHub PR/CI 讀回更新。Cloud Scheduler/`commit_data.sh` 維持 HIGH_RISK_HOLD；G5J/G5K 與 Golden、4,472 筆歷史回補依舊 HOLD。
- 本份治理 MD 僅在 ZIP 中更新，尚未上傳 GitHub，必須遵循獨立治理文件發布流程。


---

## SRC-P20/P21 正式進度增補（2026-10-24）

> 本文件仍為 **GitHub 未發布的治理候選**；下列 P20 進度已完成 Android 和 GitHub 獨立讀回，但此 MD 不等同遠端 main 文件。

- Source PR #2 `https://github.com/easonliu714/event_scraper_public/pull/2`，Open / Draft / Unmerged，HEAD `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0`，BASE `6004754f90d551cdb0cdb91a3e04b42c04f45f48`；**僅五個新增檔案**，source runtime `DORMANT`。
- Preview PR #1 `https://github.com/easonliu714/eventradar-pwa-preview/pull/1`，Open / Draft / Unmerged，HEAD `b55b3673088b6df7bfe51f04d8d82b8e7616324f`，BASE `a8cde084ab5581736d86094d8cdcc2cdc9963000`；**僅 `index.html`**。
- 原 Source PR #1：Open / Draft / Unmerged，HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`，涉及 34 檔、Actions 排程及 `commit_data.sh`，**HIGH_RISK_HOLD，禁止解除 Draft／合併**。
- SRC-P19 雙 PR 發布前 Readiness Android PASS；SRC-P20 實際建立兩個非強制 Push 分支與 Draft PR，GitHub 獨立讀回五檔／一檔白名單 PASS；Source main、Preview main 未改動。
- SRC-P21：只讀 CI candidate Toolkit；Source Python AST + G5H offline suites、Preview Node 9 synthetic role cases/escaping。**Workflow 沒有寫入遠端，CI 尚無 Check runs／成功證據，維持 CI HOLD**。
- 兩條工作流僅可後續經新授權獨立路線出版；不得在 P20 PR 改動六檔白名單，亦不得啟用 schedule／通知／正式爬蟲。
- BeClass 真實封存兩份日期候選 2/2，地點衝突 HOLD；9,850 正式 data.json 與 4,472 筆 BeClass 歷史沒有批次回補；G5J/G5K OPEN/HOLD。
- `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`。


## 2026-10-24 SRC-P21 Android PASS / SRC-P22 isolated-branch CI correction (LOCAL CANDIDATE ONLY)

- SRC-P20 Source PR #2 (main-based 5 added, HEAD `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0`) and Preview PR #1 (index.html only, HEAD `b55b3673088b6df7bfe51f04d8d82b8e7616324f`) are Open/Draft/Unmerged. Original Source PR #1 is Open/Draft/HOLD.
- SRC-P21 Android Selftest, Negative QA, Preflight, Build, Verify PASS. Two workflow candidates are NOT published; Check runs 0 for P20 heads.
- SRC-P22 is a local **candidate** introducing a separate `push`-only CI governance branch route; it checks out exact P20 HEADs without modifying P20 five/one file lists. Workflow branch CI successful runs do **not** automatically become P20 PR HEAD checks.
- No extra remote branch/PR/Commit or CI run currently asserted from P22. Explicit separate authorization required for governance Workflow publication and any merge to default branch. Source dormant; `GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 PUBLISHED=false`; G5J/G5K HOLD.

---
## SRC-P23 CI 治理分支發佈授權與實際狀態（2026-10-24）
- 使用者已明確授權：Source `ci/eventradar-source-ci-p22` 和 Preview `ci/eventradar-preview-ci-p22` 各新增**一份**已通過 P22 Android SHA 的唯讀 Workflow，各一個非強制 Push；讀回 GitHub Actions Run/Job/Steps，禁止 main/資料/排程/通知/PR1/P20 PR 修改。
- P22 Android 已 PASS：Source Workflow SHA256 `28f2527ac5d23788ff1c1a2789d43c9536c2a7ed4449c3d0cb00264d976d4313`；Preview SHA256 `2176ce6ed3cdf1d91fcaddf962b597e0f948dec3a6d76d95835c8e6941bfe652`。
- GitHub Connector 連線實際兩次 create_branch 都回覆 HTTP 403 `Resource not accessible by integration`，**不是來源 SHA 飄移**；因此本 P23 以受控 Termux GitHub CLI/Git 權限續作，遠端發佈結果以 Android 及 GitHub Runner 獨立讀回為準。
- 在新的 SRC-P23 Android Publish/Verify PASS 前，`CI_BRANCHES_CREATED=UNKNOWN/NOT_YET_VERIFIED`、`CI_RUNNER_PASS=UNPROVEN`。P20 PR HEAD Source `4c2c9ec93ae90410230a074e09b2aa853b7bfcf0`、Preview `b55b3673088b6df7bfe51f04d8d82b8e7616324f` 必須保持不變。
- 已建的 Source PR #2（五檔）與 Preview PR #1（一檔）仍 Draft，不合併；Source 原 PR #1 仍 34 檔 Draft/HOLD。CI 治理分支 Run 成功只是對固定 P20 HEAD 的測試，不等同 PR HEAD 的 Check run 成功。
- `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`；正式 Github 治理文件尚未發布，此次內容只屬 Toolkit 候選，仍不得冒稱已遠端同步。
