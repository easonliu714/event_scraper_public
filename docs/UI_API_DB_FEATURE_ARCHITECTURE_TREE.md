# 活動暨售票雷達｜UI／API／資料儲存／CI 功能架構樹

> **2026-10-29 P30-L9-X 寬宏原始 parser 同次來源階段對照 — 10 URL-pattern → 10 selector → 10 PRODUCT_ID → 10 anchor text，尚非活動驗證**
> ```text
> Formal Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PR51 published snapshot]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> └─ Pages #40683700243 SUCCESS [NO NEW DEPLOY]
> L9-W Draft PR62 @9bc37d326ee6e1b698e36061f8323e0894c98ad6
> └─ L9-X Draft PR63 @b90a6af4f6bb2bab4a6570a025e7068cd1c69093 [UNMERGED]
>    ├─ scripts/p30_l9x_kham_original_parser_parity.py [one Chromium navigation; BeautifulSoup static/rendered]
>    │  ├─ exact frozen scraper.py blob 98eddeafb497718c51aa81c6a150e9a5e1e687a8
>    │  ├─ static 44 anchors / broad UTK0201 10 / original selector 10
>    │  ├─ original PRODUCT_ID gate PASS 10 / unique 10 / anchor text nonempty 10
>    │  ├─ rendered three passive snapshots each 10/10/10 pre-event stages
>    │  └─ create_event_obj NOT EXECUTED; identity/fields/Golden/publish all 0
>    ├─ tests/p30/test_l9x_kham_original_parser_parity.py [36/36 offline PASS]
>    └─ .github/workflows/eventradar_p30_l9x_kham_original_parser_parity.yml
>       └─ native CI #40784134457 SUCCESS -> Artifact #12858063173
>          └─ ZIP SHA256 c259d931c6c8b9c3b2bb8f5e398e6675231202fd718e136cf9c185d9bd6a4c5f
> Formal status Draft PR53 [CI FAIL/security-blocked, UNMERGED]
> Formal fields UNKNOWN / Golden 0 / Publish 0 / HARD_HOLD_NO_PUBLICATION
> ```
> - **Interpretation:** 2026-10-29 07:00 Taiwan current Kham original selector and PRODUCT_ID gate do not explain the earlier L7-B 2026-10-26 generic zero. Cross-time page drift, the remaining `create_event_obj` title/noise stage, and other category behavior remain unresolved. Do not equate 10 links with 10 verified events. Next P30-L9-Y targets exact post-selector title/noise filter and event-object boundary under bounded source evidence; no main/Pages/production mutation.
>

> **2026-10-29 P30-L9-W 寬宏清單邊界：當前 static/rendered URL-pattern 10；歷史 generic list=0，尚非 parser 根因證明**
>
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PR51 snapshot]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> └─ Pages run 40683700243 SUCCESS [NO NEW DEPLOY]
> L9-V Draft PR61 @46dd6ddade398603cca4fc6f8dbb8f644ce64d3c
> └─ L9-W Draft PR62 @9bc37d326ee6e1b698e36061f8323e0894c98ad6 [UNMERGED]
>    ├─ scripts/p30_l9w_kham_list_boundary.mjs
>    │  ├─ SHA-pinned L7-B + formal status, one normal Chromium official category navigation
>    │  ├─ HTTP200, redirects0, static 44 anchors / 10 unique same-host UTK0201-pattern
>    │  ├─ rendered four snapshots 10/10/10/10; ready interactive→interactive→complete→complete
>    │  ├─ review CURRENT link presence vs HISTORIC 0; no parser root-cause assertion
>    │  └─ no raw source persistence, detail identity 0, fields 0, Golden 0, publish 0
>    ├─ tests/p30/test_l9w_kham_list_boundary.mjs [39/39 offline PASS]
>    └─ .github/workflows/eventradar_p30_l9w_kham_list_boundary.yml
>       └─ exact-head CI #40775864493 SUCCESS -> Artifact #12854207689
>          └─ ZIP SHA256 2ba90bf6d5e080443b5e01309ae877f3057f9915082b9c3b303c130f0051fa61
> Formal status Draft PR53 [CI FAIL/security-blocked, UNMERGED]
> Formal fields UNKNOWN / Golden 0 / Publish 0 / HARD_HOLD_NO_PUBLICATION
> ```
> - **Interpretation:** Current 10 URL-pattern matches are not 10 confirmed events. The L7-B 2026-10-26 generic zero and 2026-10-29 current 10 were observed at different times; neither a static-parser bug nor JS-only source is proven. Next L9-X: bounded same-session original generic parser vs structural anchor/card/title association, then exact ID/detail parity if justified. Preserve ibon 39961 historic mismatch OPEN and CKSMH 5/TWTC 39 Android USER_ATTESTED_PASS + L8 UI PASS.
>


> **2026-10-29 P30-L9-V — 19-platform SHA-pinned HTTP/list blocker classification, one safe BeClass probe**
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PR51 published]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> └─ Pages Run 40683700243 SUCCESS [NO NEW DEPLOY]
> L9-U Draft PR60 @2b26e27bee40f3bff7dc08b1a3fec1c1a9f5d96d
> └─ L9-V Draft PR61 @46dd6ddade398603cca4fc6f8dbb8f644ce64d3c [UNMERGED]
>    ├─ scripts/p30_l9v_19source_blocker_triage.py [SHA-pinned original L7B report + published status]
>    │  ├─ 3 HTTP403 (KKTIX/拓元/BeClass); 1 HTTP200 zero generic (寬宏)
>    │  ├─ 3 HTTP200 zero but separate source adapters (ibon/TWTC/CKSMH)
>    │  ├─ 7 list-positive detail identity HOLD; 5 list-positive field role HOLD
>    │  ├─ BeClass one bounded public GET => HTTP403, 0 redirect follows, 0 retries
>    │  └─ no raw URLs/HTML/cookies; no current root-cause claim for other 18 sources
>    ├─ tests/p30/test_l9v_19source_blocker_triage.py [34/34 offline]
>    └─ .github/workflows/eventradar_p30_l9v_19source_blocker_triage.yml
>       └─ CI Run 40768439655 SUCCESS -> Artifact 12852485007
>          └─ ZIP SHA256 4bf89a060381e1fd1093bc4a24c3878d7ee41a4c99fa01bfdec23f7035d07a06
> Formal status Draft PR53 [CI FAIL/security blocked, UNMERGED]
> Formal fields UNKNOWN / Golden 0 / Publish 0 / HARD_HOLD_NO_PUBLICATION
> ```
> - Historical 19-platform evidence is not a live 19-platform E2E assertion. L7-B Artifact 12665097220 digest `8ad3a6c8d0b3259ef9187830a33455365a8ff4c7bc30061653345d74cef758c6` and report SHA `e07c01a5d36ab0c950c45fb26e5fdd270103b4013bbf62a00c48291fee5f595a` verified. One new BeClass 403 observation does not resolve earlier 302. Next L9-W: focus 寬宏 public list=0 parser boundary, or BeClass normal public redirect discrepancy. Keep ibon 39961 historic mismatch OPEN, original Android 44 USER_ATTESTED_PASS and L8 UI PASS, Docs Draft PR8 sole canonical authority; no publication.



> **2026-10-29 P30-L9-U ibon 39961 exact list/detail heading identity — native CI 46/46 PASS, historical mismatch OPEN**
>
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PUBLISHED PR51]
> └─ Pages #40683700243 SUCCESS [NO NEW DEPLOY]
> L9-T Draft PR59 @7923ede339b219a2264127f4163eb6d75e31a66b
> └─ L9-U Draft PR60 @2b26e27bee40f3bff7dc08b1a3fec1c1a9f5d96d [UNMERGED]
>    ├─ scripts/p30_l9u_ibon_39961_heading_identity.mjs
>    │  ├─ pinned L9-K cross-window report + L9-H historic mismatch, both SHA checked
>    │  ├─ one normal public list + one exact detail navigation, HTTP200/200
>    │  ├─ exact 39961 same-card list title 1; no ambiguous same-ID candidate
>    │  ├─ twelve passive H1/H2 observations / 500ms; first complete/match index1
>    │  ├─ stable current H1/H2 match tail; historic L9-H mismatch remains OPEN
>    │  └─ no raw title/HTML/links/cookies/screenshots persisted; fields 0
>    ├─ tests/p30/test_l9u_ibon_39961_heading_identity.mjs [46/46 PASS]
>    └─ .github/workflows/eventradar_p30_l9u_ibon_39961_heading_identity.yml
>       └─ native CI #40759836065 SUCCESS, Artifact 12846208917
>          └─ ZIP SHA256 2144b4f1b8d2837a626690e914a28c65d4c4864aa25a18b7cf86506ae07fcfd2
> Formal PWA status Draft PR53 [CI FAIL/security-blocked, UNMERGED]
> Formal fields UNKNOWN / Golden 0 / Publish 0 / HARD_HOLD_NO_PUBLICATION
> ```
> - Current 39961 source title alignment is **REVIEW ONLY** and does not explain the prior L9-H `HOLD_TITLE_MISMATCH`; formal identity is not certified. K report SHA `87eef831253a7dea00f53100ea7f0b5c914d6b9cfa62b63906d8d1a846af50a9`, H report SHA `e8a5e392e3f80ce6504df88c2564506b32d476204c01c5de139869dfd5b7965b` verified. Next L9-V prioritizes 19-platform 403/302/0 HTTP/list blocker matrix, no redundant short-window 39961 retry. Docs canonical only on Draft PR8. Existing CKSMH 5/TWTC 39 Android USER_ATTESTED_PASS, L8 Core UI PASS, and formal status visual screenshots retained; no 19-source E2E claim.
>

> **2026-10-29 P30-L9-T ibon 39907 exact heading readiness — native CI 32/32 PASS, field HOLD**
>
> Formal PWA Source main fbf4ca02b91159f2423caf3d79fb0ca4bb747069 UNCHANGED; docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 IMMUTABLE; docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 PUBLISHED PR51; Pages #40683700243 SUCCESS, NO NEW DEPLOY.
>
> - L9-S Draft PR58 HEAD cf8250a16d9e59df8957e82000fa8ef5e02ae230 -> **L9-T Draft PR59 HEAD 7923ede339b219a2264127f4163eb6d75e31a66b**, unmerged.
> - scripts/p30_l9t_ibon_39907_heading_states.mjs: one normal public Chromium navigation to ibon 39907; twelve passive 500ms snapshots. Distinguishes complete + no headings, complete + H3/H4-only, complete + H1/H2 nonmatch candidate. Actual HTTP200, document complete index1, exact title index3, two pre-match complete H3/H4-only states, zero nonmatching H1/H2 candidates, stable matched final three. Decision HOLD_TRANSIENT_HEADING_ABSENCE.
> - tests/p30/test_l9t_ibon_39907_heading_states.mjs: 32/32 deterministic fail-closed tests PASS.
> - .github/workflows/eventradar_p30_l9t_ibon_39907_heading_states.yml: first CI #40749594278 FAIL due to token env typo, corrected in isolated branch; final exact-head CI #40749692079 SUCCESS, Artifact 12842508760 ZIP SHA256 f1f99035f316b61adc2d208a844e349ae5312ddc173d0b1cdc14b29abd324fcd; parent L9-S report SHA 337668d7b805e4102f69cf9faa6da73cdf34e4ac54f4add8a45c66b39083e0a2 and original L9-F report SHA 81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4 independently checked.
> - No raw source text/HTML/links/cookies/screenshots persisted. Fields 0 / Golden 0 / publication 0 / HARD_HOLD_NO_PUBLICATION. Docs canonical only on Draft PR8, NOT main; formal status Draft PR53 remains CI FAIL/security-blocked and unmerged. Existing CKSMH 5/TWTC 39 Android PASS, L8 Core UI PASS and 11 formal PWA screenshots retained without full 19-source E2E claims. Next L9-U: bounded exact ID/title H1/H2 evidence for historical ibon 39961 or first unresolved source identity.


> **2026-10-29 P30-L9-S three-source title readiness — native CI 30/30 PASS; 39907 complete-state nonmatch HOLD**
>
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PUBLISHED PR51]
> └─ Pages deploy #40683700243 SUCCESS [NO NEW DEPLOY]
> L9-R Draft PR57 @3f473d6b377650cf15b84e83d2481f8790347cac
> └─ L9-S Draft PR58 @cf8250a16d9e59df8957e82000fa8ef5e02ae230 [UNMERGED]
>    ├─ scripts/p30_l9s_ibon_three_title_readiness.mjs
>    │  ├─ 3 SHA-pinned ibon IDs 39575/39907/39978, one normal navigation each
>    │  ├─ 8 passive title/readyState snapshots at 600ms per ID
>    │  ├─ complete-state unmatched candidate vs stable matched tail
>    │  └─ no click, title/date text, HTML, links, screenshots or cookies persisted
>    ├─ tests/p30/test_l9s_ibon_three_title_readiness.mjs [30/30 PASS]
>    └─ .github/workflows/eventradar_p30_l9s_ibon_three_title_readiness.yml
>       └─ Native CI #40740745592 SUCCESS, Artifact 12838189367
>          ├─ 39575: HTTP200, title first index2, complete first index3, REVIEW only
>          ├─ 39907: HTTP200, complete first index1, title first index2,
>          │         one complete-state nonmatch, HOLD_COMPLETE_NONMATCH_BEFORE_STABLE_TAIL
>          ├─ 39978: HTTP200, complete/title first index1, REVIEW only
>          └─ formal fields 0, Golden 0, Publish 0, HARD_HOLD_NO_PUBLICATION
> Docs Draft PR8 only [NOT MAIN]
> Formal PWA status Draft PR53 [CI FAIL / security-blocked / UNMERGED]
> ```
> - L9-S native job `123001351188` passed exact three ADD-only path gate, 30 deterministic tests, parent R/F exact-head artifact SHA, and independent report SHA readback. Artifact ZIP SHA256 `3b53e69770add8a1c30324e7276ee7d931caf158b53b5c354213c5c074a0c169`, R report SHA `ef8a897497a789061141d1fd44116b4b268f38107e087b84085ecadbe287b838`, original F report SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`. `document.readyState=complete` is not sufficient for correct source title identity (39907). Stable title tail is REVIEW, not Golden. Next L9-T: independently disambiguate 39907 completed-document no-exact-title state (heading absent vs nonmatching candidate unresolved) vs delayed SPA hydration; no proof of wrong-event title. Existing CKSMH 5/TWTC 39/L8 Core Android PASS and 11 formal PWA screenshots retained without full E2E claims.
>

> **2026-10-29 P30-L9-R exact-head title readiness — ibon 39878 delayed heading proven, no field promotion**
>
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PUBLISHED PR51]
> └─ Pages deploy #40683700243 SUCCESS [NO NEW DEPLOY]
> L9-Q Draft PR56 @59152fb83cb396924a6935f36681fac7fb0079f9
> └─ L9-R Draft PR57 @3f473d6b377650cf15b84e83d2481f8790347cac [UNMERGED]
>    ├─ scripts/p30_l9r_ibon_title_state.mjs [39878, 8 passive snapshots, 650ms]
>    │  ├─ no raw title text, HTML, links, dates, screenshots or click persistence
>    │  ├─ absent/not-ready vs exact heading match vs stable unmatched H1/H2 candidate
>    │  └─ snapshot 2 first complete and exact match, tail 3 stable exact matches
>    ├─ tests/p30/test_l9r_ibon_title_state.mjs [36/36 fail-closed]
>    └─ .github/workflows/eventradar_p30_l9r_ibon_title_state.yml
>       └─ CI #40731815454 SUCCESS, artifact 12835237400
>          ├─ first two CI runs FAILED missing test exports; corrected in Draft branch
>          ├─ source HTTP200, nonmatch after complete 0, no stable wrong-title proof
>          └─ formal fields 0, Golden 0, Writer 0, Publish 0, HARD HOLD
> Governance Docs Draft PR #8 only [NOT MAIN]
> Formal PWA status Draft PR #53 [CI FAIL/security-blocked; UNMERGED]
> ```
> - Parent Q report SHA `235d7bc2ef20d6550da12da7bc6aee4d212fa0dcf6821936d7446df802108c1d`; original F report SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`; new artifact ZIP `sha256:cce75aa2bd82d4a695b58019db8e6c0cee5e703052039f3cb80210dfa70df96a`. L9-R proves transient title hydration in the latest bounded capture, **not** that all prior mismatches were timing-related. No date/price/session/SALE field Golden; no source production modification or new PWA deploy. Next L9-S: apply strict title readiness to bounded source samples while preserving fail-closed publication boundary.
>


> **2026-10-28 P30-L9-Q ibon 39878 passive hydration/identity Gate — native 36/36 PASS; fields HOLD**
>
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PR51 PUBLISHED]
> └─ Pages build/deploy #40683700243 SUCCESS [NO NEW DEPLOY]
> L9-P Draft PR55 @158b13cf3d45b9e1fe377bda4182a4da5e5864c8
> └─ L9-Q Draft PR56 @59152fb83cb396924a6935f36681fac7fb0079f9 [UNMERGED]
>    ├─ scripts/p30_l9q_ibon_hydration.mjs [one official 39878 page, six passive snapshots at 700ms]
>    │  ├─ per-snapshot exact source title parity boolean + DOM readyState
>    │  ├─ direct H3 活動日期 count, immediate sibling control counts, direct text presence boolean
>    │  └─ first-label index, hydration transition, last-three topology stability
>    ├─ tests/p30/test_l9q_ibon_hydration.mjs [36/36 fail-closed contracts]
>    └─ .github/workflows/eventradar_p30_l9q_ibon_hydration.yml
>       └─ CI #40721117824 SUCCESS, artifact 12829898767
>          ├─ HTTP200; H3 absent snapshot 0 -> first present snapshot 1
>          ├─ last-three local topology stable; widget controls remain untyped
>          ├─ titleAll=false and allReadyComplete=false -> identity/timing HOLD
>          └─ accepted fields 0, Golden 0, Publisher/Writer 0, HARD_HOLD
> Governance Docs Draft PR #8 only [NOT MAIN]
> Formal PWA status Draft PR53 [CI FAIL, security-blocked, UNMERGED]
> ```
> - Exact-head CI #40721117824 job 122931962543 SUCCESS, parent L9-P ZIP digest `24fbff9dc7d6a2723731a7968e4e13a8740dc1d1cb766ed86f089ddba4cb3f03`, parent report SHA `4c6a920d23c3f47bbee07fc102513d002fda62eeed69715beb4d63aae40188c3`, L9-F source SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`, new Artifact ZIP SHA `0e07aec0a6c8a0524457c58e782906d799e3a7f773d084e876bcf1aaddd3ab48`. `titleAll=false` alone does not prove wrong event; missing/not-ready heading is possible. Next L9-R isolates title hydration versus mismatch with no raw text persistence. No date/price/field promotions, Golden, event publication, new PWA deployment or release from HOLD.
>


> **2026-10-28 P30-L9-P ibon interactive widget topology — native 36/36 PASS, formal source-field extraction still HOLD**
>
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> ├─ docs/platform_status.json blob e19ca37c4c80c10b7278d0813b8ff1047535d124 [PUBLISHED PR51]
> ├─ docs/platform-status.html [Owner Android visual PASS; no new deployment]
> └─ GitHub Pages native deployment 40683700243 SUCCESS
> L9-O Source Draft PR54 @96748095bbe8084d302bf74b3a7c0aa119039ca2
> └─ L9-P Source Draft PR55 @158b13cf3d45b9e1fe377bda4182a4da5e5864c8 [UNMERGED]
>    ├─ scripts/p30_l9p_ibon_control_types.mjs [four exact official details, 2 passive DOM snapshots]
>    │  ├─ label: direct H3 活動日期 only; nextElementSibling controls only
>    │  ├─ anchor/button/form/input/select/role-button counts, no URL/text/date extraction
>    │  └─ compare source-title identity + control type/count drift across snapshots
>    ├─ tests/p30/test_l9p_ibon_control_types.mjs [36/36 fail-closed]
>    └─ .github/workflows/eventradar_p30_l9p_ibon_control_types.yml
>       └─ Run 40711541169 SUCCESS, artifact 12826851317
>          ├─ all four HTTP200, 4/4 title both snapshots
>          ├─ 39575/39907/39978: stable 2 button + 2 input controls
>          ├─ 39878: first H3 label missing -> second H3 with 2 button + 2 input
>          ├─ 3/4 control topology stable; 1/4 same-page hydration drift
>          └─ 0 accepted dates/prices/fields, 0 Golden, 0 publishing, HARD HOLD
> Formal PWA status Draft PR53 [UNMERGED; old test CI FAIL and safety write blocker]
> ```
> - Source L9-O report SHA256 `767900155ebf408886db68d8c89d4fd9a1e2044994bbf7c560ac7e7d91e14d32` and original L9-F SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4` verified from exact pinned GitHub artifacts; L9-P artifact ZIP digest `24fbff9dc7d6a2723731a7968e4e13a8740dc1d1cb766ed86f089ddba4cb3f03`. Source P30-L9-P Run `40711541169` completed SUCCESS; CI 36/36. The two-button/two-input widget is **not** typed date evidence. No click, no purchase, no screenshot, no raw HTML, no link URL, no source text persisted.
> - Next P30-L9-Q: passive hydration-ready stabilization and exact source-bound label/value role diagnostics; do not infer date from interactive widget or force fields Golden. Historic 44 Android user PASS, L8 Core UI PASS retained. Governance docs only on Draft PR #8; main has unchanged official status page. No new main merge or Event Writer/Scheduler/Notifier/Golden activation.
>

> **2026-10-28 P30-L9-O source UI topology — four current interactive label HOLD, native CI PASS**
>
> ```text
> Formal PWA main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/data.json blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4 [IMMUTABLE]
> ├─ docs/platform_status.json [published PR51 snapshot; 19 platforms; Owner Android visual PASS]
> └─ docs/platform-status.html [published PR51, not PR53 draft]
> L9-N Draft PR52 @768e2ee1d6982b3e690c48d98d0be0f4e16a6944
> └─ L9-O Draft PR54 @96748095bbe8084d302bf74b3a7c0aa119039ca2
>    ├─ scripts/p30_l9o_ibon_label_topology.mjs [normal Chromium, 4 exact detail IDs, H3 vs L9-M selector]
>    ├─ tests/p30/test_l9o_ibon_label_topology.mjs [29/29 negative contracts]
>    └─ .github/workflows/eventradar_p30_l9o_ibon_label_topology.yml
>       └─ CI Run 40702378377 SUCCESS -> Artifact 12820574944
>          ├─ 4/4 HTTP200 + exact title heading parity (including ID 39575)
>          ├─ 4/4 H3 活動日期 local labels; L9-M selector also 4/4
>          ├─ 4/4 adjacent region HOLD_INTERACTIVE_LOCAL
>          └─ 0 formal fields / Golden / Writer / Publish; release HARD_HOLD
> Formal PWA status Draft PR53 @4381c01d3132634a8ec6535abddedcfeaaffcb40
> └─ CI 40686748311 FAILURE: ibon field status vs existing exact-contract assertion
>    └─ required test extension write blocked by platform safety; NO BYPASS, NO MERGE
> ```
> - L9-O native Run `40702378377` exact-head SHA, 29/29 offline tests, four live details and independent SHA readback PASS. Evidence ZIP SHA256 `c0f03e2448ae90388f113164388a254808656d5f274a75e2eaad66c2a530b8d3`. L9-N parent report SHA `2033f232423a212698d94e023042656407e93e8d16bfe62f42252613a2071024`, parent ZIP metadata SHA verified. Earlier L9-N 3/4 titles + zero labels remains historical; later L9-O 4/4 titles + four H3 labels shows time-varying observations, not a proven selector bug or formal fix. All four adjacent label regions contain interactive controls and remain unbound, not dates. The next L9-P should inspect control type and local source role without activation, with deterministic negative tests; no source field promotion.
>

> **2026-10-28 P30-L9-N and formal Android status-page visual confirmation — new source diagnostics CI PASS, public status update DRAFT HOLD**
>
> ```text
> Formal PWA Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [UNCHANGED]
> ├─ docs/platform_status.json [current published PR #51 snapshot; 19 platform cards / 264 list candidates]
> ├─ docs/platform-status.html [current published PR #51; Android 11 screenshot VISUAL USER_PASS]
> └─ docs/data.json [unchanged blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4]
> Source L9-M Draft PR #50 @4597385dbf216dc358c3e432e6ccc560caf9f1f2
> └─ L9-N Draft PR #52 @768e2ee1d6982b3e690c48d98d0be0f4e16a6944 [UNMERGED]
>    ├─ scripts/p30_l9n_ibon_local_root_cause.mjs [4 official details / direct h3 local]
>    ├─ tests/p30/test_l9n_ibon_local_root_cause.mjs [22/22 offline]
>    └─ .github/workflows/eventradar_p30_l9n_ibon_root_causes.yml
>       └─ Native Run 40686039228 SUCCESS -> Artifact 12814702732
> Formal PWA Refresh Draft PR #53 @4381c01d3132634a8ec6535abddedcfeaaffcb40 [HOLD]
> ├─ docs/platform_status.json [records L9-M 4/4 historical, L9-N current 3/4 and zero accepted fields]
> └─ docs/platform-status.html [human Chinese stage labels, raw codes expandable]
> ```
> - The latest L9-N actual HTTP200 title matches **3 of 4**; ID `39575` source title mismatch, other 3 current matches but zero recognized local date labels. No `EVENT_PERIOD` value read from the source; all formal price/date/session/ticket status unknown, Golden 0. Earlier L9-M 4 of 4 title matches and four AMBIGUOUS_OR_INTERACTIVE remain valid as historical observations only, not continuous proof. Artifact ZIP SHA256 `a049545092f6a508791f3a12b5c05395de7b4eb975efbb3d9b8813319ec1a5c9`, native CI Run `40686039228` completed SUCCESS, 22/22 offline negatives.
> - Formal status PWA owner Android visual 11 screenshots PASS as user attestation only. Draft #53 must remain unmerged because required test extension linking status JSON to new L9-N SHA was blocked by platform security; do not bypass the block. The deployed PR #51 Source main formal PWA status still valid as its dated snapshot. EventRadar hourly sole scheduled Writer enabled for safe future Gate work, Pokémon Sleep tasks not touched, no release from HOLD without Owner and evidence.
>

> **2026-10-28 P30-STATUS official PWA status-only public diagnostics architecture — Pages deployment SUCCESS, event-feed immutable**
>
> ```text
> Source main@fbf4ca02b91159f2423caf3d79fb0ca4bb747069 [NEW after USER-authorized status-only PR #51]
> ├─ docs/data.json [UNMODIFIED Git Blob 7fc4fe32567a57fd504483eeb9a8b9e10b568ea4]
> ├─ docs/index.html [single new header anchor → platform-status.html; prior fetch(data.json) unchanged]
> ├─ docs/platform_status.json [19 individual platform status rows; L7B SHA provenance + overlays]
> │  ├─ baseline: 2026-10-26 15:53:41 UTC, 19 attempts, 16 HTTP200 / 3 403, 264 list candidates
> │  ├─ per-source: HTTP → LIST → DETAIL → FIELD ROLES → Android → EVENT PUBLISH
> │  ├─ CKSMH: 5 independent activity/Android PASS; TWTC: 39 Android PASS / 38 date candidates / 1 postponed conflict
> │  ├─ ibon: normal Chromium 22 distinct list candidates; 39961 drift review; L9-M 4 titles parity and 0 field promotions
> │  └─ all status fields evidence-only; counts from different Gates NOT summed; event publication HARD_HOLD
> ├─ docs/platform-status.html [mobile responsive; loads ./platform_status.json with no-store]
> │  ├─ per-platform card, search and stage filters, GitHub evidence links, explicit timestamps
> │  ├─ safe DOM textContent / no HTML injection, site links only to github.com
> │  └─ read-only, no notifications, background scheduler, login, checkout or event feed rewrites
> ├─ tests/p30/test_public_platform_status_readonly.py [19/19 count/identity checks against 3 real artifacts]
> └─ .github/workflows/eventradar_public_platform_status.yml [source-only read permissions]
>    └─ CI 40683470517 SUCCESS + PR CI 40683520120 SUCCESS
>       └─ GitHub Pages Build/Deploy Run 40683700243 SUCCESS
> ```
> - PR #51 status-only merged as requested; independent readback Source main new HEAD `fbf4ca02b91159f2423caf3d79fb0ca4bb747069`, `docs/platform_status.json` Git blob `e19ca37c4c80c10b7278d0813b8ff1047535d124`, `docs/platform-status.html` Git blob `63264fb19991123aceb929a17427e7ef10313a12`, index Git blob `d752332f4d4e8074fef9ceb56d12560caf25b8df`, `docs/data.json` unchanged. Actual external GitHub Pages HTTP and mobile screenshot verification not available to assistant at this checkpoint; user front-end inspection remains PENDING, but Pages native deploy SUCCESS.
> - P30-L9-M source-specific detail diagnostic remains separate Draft PR #50, no main merge; four ibon HTTP200/title 4/4, local pair reason `AMBIGUOUS_OR_INTERACTIVE` 4/4, accepted role value 0. Status publication must NEVER be conflated with event Golden/PWA candidate publication. Only previously attested Android 44 (CKSMH 5/TWTC 39) plus L8 core-preview UAT are PASS; site-specific Android for remaining 17 platforms NOT tested/attested.
> - Two canonical governance files continue exclusively on Docs Draft PR #8. Source main now has read-only progress page, not governance doc updates. Do not change Writer/Notifier/Scheduler, do not merge stalled source PRs, do not retire Preview/ShowNews; event feed release remains `HARD_HOLD_NO_PUBLICATION`.
>

> **2026-10-28 P30-L9-L source-only four official ibon details semantic review architecture — CI PASS / field evidence 0**
>
> ```text
> Source main@fc4f963247d [unchanged]
> └─ L9-K Draft PR #48 @ 30aa18a9fbe4dc7b46f9b4b2cf41a51b70f0b11a [already PASS, no rework]
>    └─ L9-L Draft PR #49 @ 627a8175b1095c42d878219d95935357457d35e5
>       ├─ scripts/p30_l9l_ibon_four_field_semantics.mjs [normal public Chromium, 4 IDs]
>       │  ├─ L9-F Run 40494326021 Artifact 12729277485 pinned SHA
>       │  ├─ ids 39575/39878/39907/39978, strict official URL/source title parity
>       │  ├─ typed EVENT/SALE/ADMISSION/REGISTRATION/VOUCHER/VENUE/PRICE/SESSION
>       │  ├─ only DIRECT_SIBLING / LOCAL_PARENT / SAME_NODE source-binding
>       │  └─ ibon_four_field_semantics.json + manifest.json + SHA256SUMS.txt
>       ├─ tests/p30/test_l9l_ibon_four_field_semantics.mjs [30/30 negatives]
>       └─ .github/workflows/eventradar_p30_l9l_ibon_four_fields.yml [readonly push]
>          └─ GitHub Actions Run 40681114004 → Artifact 12812317856
> ```
> - Native [Run 40681114004](https://github.com/easonliu714/event_scraper_public/actions/runs/40681114004) Job `122791739707` success, exact 3 add-only paths and formal Pages/runtime Git blob SHA PASS, 30/30 offline tests, actual pinned source L9-F JSON SHA256 `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`. Four new ibon public detail HTTP200/title parity PASS, one recognized label and one rejected role per page, **0 accepted field pairs**. Formal date/price/ticket/venue/event session remain NULL/UNKNOWN and no role or session promotion.
> - [SHA Artifact 12812317856](https://github.com/easonliu714/event_scraper_public/actions/runs/40681114004/artifacts/12812317856) ZIP `a4b2716566504c0f0c8fbffc364b632e10483b2a47d3d44055f2d7326cdc74de` (1654 B), read-only semantic report + SHA. `HARD_HOLD_NO_PUBLICATION`, Writer/Publisher/Scheduler/Notifier/merges/retirement prohibited, Android 44 original PASS, L8 core UI PASS and L9-K 39961 historic mismatch HOLD preserved. Next L9-M should diagnose *why* local sibling is rejected without promoting unbound global body dates; update only these two governance docs in Docs Draft PR #8.
>

> **2026-10-28 P30-L9-K official ibon 39961 cross-window source identity assurance architecture — native PASS 3/3 across 2 time windows, RELEASE HARD HOLD**
>
> ```text
> event_scraper_public Source main@fc4f963247d [immutable Pages/data/runtime]
> └─ L9-J Source Draft PR #47 @ 727aea8aa673b29cd4a589c0a9ca68836fac4b92
>    └─ L9-K Source Draft PR #48 @ 30aa18a9fbe4dc7b46f9b4b2cf41a51b70f0b11a
>       ├─ scripts/p30_l9k_ibon_39961_cross_window.mjs [readonly]
>       │  ├─ pinned L9-J Run 40619619643 Artifact 12786507149 [2/2 current short-window PASS]
>       │  ├─ pinned L9-H Run 40516301527 Artifact 12740505389 [prior 39961 mismatch]
>       │  ├─ provenance(): double SHA and historical mismatch mandatory
>       │  ├─ minimumWindow(): >=4 hours after latest upstream sample before ANY public fetch
>       │  ├─ capture(): one NEW ephemeral standard Chromium official list + exact 39961 detail
>       │  ├─ crossWindowDecision(): compare 3 captures over 2 time windows
>       │  └─ ibon_39961_cross_window.json + SHA manifest (no production writes)
>       ├─ tests/p30/test_l9k_ibon_39961_cross_window.mjs [30/30 fail-closed]
>       └─ .github/workflows/eventradar_p30_l9k_ibon_cross_window.yml [read-only push]
>          └─ Actions Run 40673236521 -> Artifact 12809656497
> ```
> - **GitHub native source evidence:** [Run 40673236521](https://github.com/easonliu714/event_scraper_public/actions/runs/40673236521) job `122765043788` completed SUCCESS at `30aa18a9fbe4dc7b46f9b4b2cf41a51b70f0b11a`; exact 3 source ADD-only files and official Pages/`docs/data.json`/`scraper.py` SHA gates PASS, 30/30 offline tests PASS; upstream SHA-pinned report `27bb5cf2450d1aed03e51c0954a3b785acc88d94518787ff3f12861fa1f88159` (L9-J) and `e8a5e392e3f80ce6504df88c2564506b32d476204c01c5de139869dfd5b7965b` (L9-H) independently validated with GitHub Artifacts + SHA256SUMS + manifests. Initial [Run 40673115086](https://github.com/easonliu714/event_scraper_public/actions/runs/40673115086) failed before any new website request due missing test helper `sha` export; only L9-K script repaired, final native CI PASS.
> - **Current first-party UI fact:** Last L9-J sampled `2026-10-28T02:13:51.393Z`; new L9-K `2026-10-28T10:35:05.675Z` (**8.354h gap**). One new normal browser process and 2 public top-level navigations: ibon `Index/entertainment` HTTP200 with one directly bound canonical numeric `39961` list card, ibon `ActivityInfo/Details/39961` HTTP200 with 3 detail headings and exact source/list-title agreement. Cumulative **3 of 3 source title matches across 2 observation windows** yields `CROSS_WINDOW_THREE_MATCHES_REVIEW_ONLY`. Historical L9-H `HOLD_TITLE_MISMATCH` must remain `OPEN_UNEXPLAINED`, `formalIdentityCertified=false` and `formalReleaseEligible=false`; do not treat finite-time reproducibility as permanent official activity identity validity.
> - **Sealed [Artifact 12809656497](https://github.com/easonliu714/event_scraper_public/actions/runs/40673236521/artifacts/12809656497)** name `eventradar-p30-l9k-ibon-39961-cross-window-readonly`, ZIP `sha256:c20ac82e7bd0c5a8e87530bbe126a81741fae2776058dd9394a8291c737118de`, 2416 bytes. `ibon_39961_cross_window.json` + `manifest.json` + `SHA256SUMS.txt` verified by native CI; no full HTML/screenshots/cookies/network bodies, no custom anti-bot behaviors, no credential use beyond GitHub artifact readonly token.
> - **UI/API/DB boundary — releaseState=HARD_HOLD_NO_PUBLICATION:** `formalEventDate=null`, `formalPrice=null`, `ticketStatus=UNKNOWN`, `formalFieldPromotions=0`, `goldenAccepted=0`, `published=false`; `Writer/Scheduler/Notifier/Publisher/mergeExecuted=false`, no change to Source main, Preview main, ShowNews main, data.json, App, API, DB, Android. Original 44 Android USER_ATTESTED_PASS and L8 new core UI USER_ATTESTED_PASS preserved. P30-L9-A ten mandatory release blockers still active, 19-source completeness not established.
> - **Next P30-L9-L:** isolate the four previously matched ibon detail IDs `39575,39878,39907,39978` for **official label-to-date/venue/price/SESSION semantic binding evidence**. Use bounded visual/text DOM structures with correct EVENT vs SALE vs ADMISSION vs REGISTRATION vs VOUCHER period roles, no undocumented API guessing, no whole-page date regex, no automatic Golden/Writer promotion. Keep 39961 intermittent mismatch under review instead of scheduling unapproved automated monitoring; two authoritative governance docs continue on Docs Draft PR #8 only.
>

> **2026-10-28 SRC-P30-L9-J ibon 39961 independent source repeatability architecture — CI PASS 2/2 SAME RUN, past mismatch held**
>
> ```text
> Source main@fc4f963247d [unchanged / Pages/runtime/data protected]
> └─ L9-I Source Draft PR #46 @ ca60d3182172ad7f824fbcb5a2a6c9189fecc74b
>    └─ L9-J Source Draft PR #47 @ 727aea8aa673b29cd4a589c0a9ca68836fac4b92
>       ├─ scripts/p30_l9j_ibon_39961_repeatability.mjs
>       │  ├─ L9-I Run 40524765567 Artifact 12744025880 [last point-in-time 39961 title parity]
>       │  ├─ L9-H Run 40516301527 Artifact 12740505389 [prior 39961 TITLE_MISMATCH]
>       │  ├─ validateParents() exact original title/event ID/source report SHA
>       │  ├─ capture() two ephemeral normal browser instances (not one shared context)
>       │  │  ├─ 1 official ibon Index/entertainment per round, numeric same-card ID 39961
>       │  │  └─ 1 exact ibon ActivityInfo/Details/39961 per round, bounded headings
>       │  ├─ 8-second minimum gap; individual UTC timestamps, HTTP and HOLD reasons
>       │  ├─ grade() 2/2 match still REVIEW_ONLY; historical mismatch mandatory
>       │  └─ ibon_39961_repeatability.json + manifest.json + SHA256SUMS.txt
>       ├─ tests/p30/test_l9j_ibon_39961_repeatability.mjs [30/30 offline negatives]
>       └─ .github/workflows/eventradar_p30_l9j_ibon_39961_repeat.yml
>          └─ native Run 40619619643 -> Artifact 12786507149 [SHA PASS]
> ```
> - **Actual native source Gate:** [Run 40619619643](https://github.com/easonliu714/event_scraper_public/actions/runs/40619619643) Job `122590202592` completed SUCCESS at Source Draft PR #47 head `727aea8aa673b29cd4a589c0a9ca68836fac4b92`, exact 3 additive paths / Git blob freeze / 30 offline tests PASS, source reports SHA `73eaec24fbe591d5bd39e2ba4704f5d0693e45f802d57fd4b9ecf013d6cd44fb` (L9-I) and `e8a5e392e3f80ce6504df88c2564506b32d476204c01c5de139869dfd5b7965b` (L9-H) independently SHA-verified with manifests. Run #1 initial `40619506719` FAILED on missing exported source constants before browser access; repaired through new script only and successful second run, no change to prior Gates.
> - **Observed first-party public DOM:** Round 1 `2026-10-28T02:13:33.400Z` to `02:13:38.431Z`; Round 2 `02:13:46.435Z` to `02:13:51.393Z`, **two separate Chromium processes, four top-level list/detail navigations**. Each round list HTTP200/exactly one official numeric source ID title, detail HTTP200/three headings, source same-card title equals official detail heading and original title. Thus `sameRunTitleMatches=2/2`, `currentTwoRoundObservation=TWO_SEPARATE_BROWSER_MATCHES_REVIEW_ONLY`. This is short-window reproducibility, not evidence that L9-H mismatch was false or cause fixed. Explicit `historicalMismatchRetained=true`, `unexplainedPriorMismatch=true`, `formalIdentityReleaseEligible=false` and overall `HARD_HOLD_NO_PUBLICATION`.
> - **[Artifact 12786507149](https://github.com/easonliu714/event_scraper_public/actions/runs/40619619643/artifacts/12786507149)** ZIP SHA256 `20a8e664f3431cf6f6a90267577cdc455915350ba6784d02a4694a01a9d25348`, 2218 bytes, source report + Manifest + SHA256SUMS native sealed. Stores bounded official URLs, titles, per-round times, HTTP and quality only; no full HTML, images, cookies, network bodies, JS bundles, private tokens, no independent verified formal event date, price, ticket status or multi-session split. `formalFieldPromotions=0`, `goldenAccepted=0`, Writer/Scheduler/Notifier/Publisher/merge 0, protected Pages/API/DB/preview untouched.
> - **Next L9-K data assurance:** use a distinct later time-window source-only Gate to compare 39961 with these pinned rounds, enforce regression/mismatch HOLD and no automatic schedule. Separately work on clearly source-bound event period parsing for the four unaffected official IDs. Historical Android 44 USER_ATTESTED_PASS, L8 new core Android PASS and L9-A ten release blockers unchanged. Both canonical governance docs remain Docs Draft PR #8, not merged to Source main.
>

> **2026-10-27 SRC-P30-L9-I ibon 39961 official source/title drift comparison architecture — native CI PASS, historical instability OPEN**
>
> ```text
> event_scraper_public Source main@fc4f963247d [frozen, formal app/Pages data immutable]
> └─ L9-H Draft PR #45 @ 56d309a9d4d895c7adfb525723c6e2a9c4abd2cb
>    └─ L9-I Draft PR #46 @ ca60d3182172ad7f824fbcb5a2a6c9189fecc74b
>       ├─ scripts/p30_l9i_ibon_39961_identity.mjs
>       │  ├─ sha-pin L9-H Run 40516301527 Artifact 12740505389 [prior 39961 mismatch]
>       │  ├─ sha-pin L9-F Run 40494326021 Artifact 12729277485 [historical source title]
>       │  ├─ exact numeric event ID + official canonical URL / single ID uniqueness
>       │  ├─ normal Chromium current Index/entertainment same-card list title
>       │  ├─ normal Chromium current ActivityInfo/Details/39961 bounded headings
>       │  ├─ adjudicate(): MISSING/FOREIGN/403/WAF/AMBIGUOUS/MISMATCH→HOLD
>       │  ├─ matched current list+detail titles => REVIEW_ONLY_NO_RELEASE
>       │  └─ ibon_39961_identity_adjudication.json + SHA manifest
>       ├─ tests/p30/test_l9i_ibon_39961_identity.mjs [30/30 offline]
>       └─ .github/workflows/eventradar_p30_l9i_ibon_39961_identity.yml [read-only push]
>          └─ Native GitHub Actions Run 40524765567 → Artifact 12744025880
> ```
> - **Native verification** [Run 40524765567](https://github.com/easonliu714/event_scraper_public/actions/runs/40524765567) completed/success (Job `122261189909`) at exact L9-I head, exact 3-file additive scope, protected Source Pages/runtime SHA, 30/30 positive-negative contracts, dual upstream source digest `e8a5e392e3f80ce6504df88c2564506b32d476204c01c5de139869dfd5b7965b` (L9-H) and `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4` (L9-F) both validated with SHA256SUMS + manifest.
> - **Actual 39961 current UI evidence:** official Index/entertainment list HTTP200, exactly one canonical ID `39961` same-card event title candidate; official /ActivityInfo/Details/39961 HTTP200, 3 bounded detail headings, current-source same-ID list/detail title parity `true`. Original title also observed `true`, `driftObserved=false`. Decision `REVIEW_ONLY_NO_RELEASE / CURRENT_LIST_DETAIL_PARITY_REVIEW_ONLY`. This does **not erase** L9-H prior point-in-time `HOLD_TITLE_MISMATCH`; intermittent source/rendering/root cause is still unproven and formal identity reliability remains held. Count each source capture separately, not an eternal 39961 PASS.
> - **[Artifact 12744025880](https://github.com/easonliu714/event_scraper_public/actions/runs/40524765567/artifacts/12744025880)** ZIP `sha256:19a6d802733d36bedaf164db8cdcbd0cdca25422eff7f01841f44af3ad696243` (1,889 B), contains isolated identity adjudication JSON, manifest, SHA256SUMS; GitHub runner verifies SHA. No raw HTML/screenshots, login/cookies, private source or network bodies stored.
> - **API / DB / formal UI boundary:** L9-I only fetches public list + exact detail, does not write to `docs/data.json`, DB, API, PWA, Scheduler, Writer, notifier or Golden; `formalFieldPromotions=0`, `ticketStatus=UNKNOWN`, `goldenAccepted=0`, `releaseState=HARD_HOLD_NO_PUBLICATION`; preserve historical Android 44 PASS, L8 core UI PASS and P30-L9-A ten release blockers. Next L9-J should test *repeatability* of exact same-ID list/detail matching under separate bounded current renders and retain disagreements as HOLD, not assume an improved DOM selector fixes a transient identity problem. Both formal governance files remain exclusively on Draft PR #8.
>

> **2026-10-27 SRC-P30-L9-H dual-source official ibon local DOM hierarchical-binding architecture — native CI PASS, one current ID mismatch**
>
> ```text
> event_scraper_public Source main@fc4f963247d [unchanged]
> └─ L9-G Source Draft PR #44 @ 07cc3ce1743a56d2bc60213d345f27672cef97d5
>    └─ L9-H Source Draft PR #45 @ 56d309a9d4d895c7adfb525723c6e2a9c4abd2cb
>       ├─ scripts/p30_l9h_ibon_local_dom_hierarchy.mjs [NO WRITE / NO GLOBAL DATE SEARCH]
>       │  ├─ L9-G Run 40511115223 Artifact 12738140163 [structure + verified ID]
>       │  ├─ L9-F Run 40494326021 Artifact 12729277485 [original title + ID]
>       │  ├─ parentProof(): SHA+manifest+five official URL/ID/title cross-contract
>       │  ├─ inspectLocalDom(): bounded only local label next-element/parent next-element/direct text
>       │  ├─ reviewNeighbor(): DATE vs SALE vs ADMISSION vs REGISTRATION vs VOUCHER vs PRICE
>       │  ├─ assessStructure(): role conflict, generic PRICE/資訊, image counts, no global dates
>       │  └─ ibon_local_dom_hierarchy.json + manifest.json [SHA sealed]
>       ├─ tests/p30/test_l9h_ibon_local_dom_hierarchy.mjs [36/36 positive-negative]
>       └─ .github/workflows/eventradar_p30_l9h_ibon_local_dom.yml [push-only READ]
>          └─ final native Run 40516301527 -> Artifact 12740505389
> ```
> - **Actual CI:** [Run 40516301527](https://github.com/easonliu714/event_scraper_public/actions/runs/40516301527) completed/success, Job `122230984614`, exact three-add-only SHA boundary and **36/36** mocked negative/positive contracts, two independently SHA-sealed upstream artifact source reports verified. L9-G source report SHA `a1736d4b4c0148c9e74eccbe9b4c1f3ab05b6ee3f94c306bac210df1e08b7a42`, L9-F title report SHA `81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4`. Source-only `main` production runtime/Pages blob fingerprints unchanged.
> - **Five live ibon detail pages:** IDs `39575,39878,39907,39961,39978` HTTP200. **Current title parity 4/5**; `39961` is **CURRENT_TITLE_MISMATCH_HOLD** despite prior historical detail match, so current labels/field values from that record cannot be trusted. Each page has `EVENT_PERIOD` `h3` label parent `div`, but **zero** safe immediate local-value relationships, `locallyBoundReviewPairs=0`, `rejectedOrHoldPairs=0`; DOM label presence does not prove readable or valid activity dates. All formal `dateStart/dateEnd/venue/price/saleWindow/registrationPeriod/voucherValidity=null/UNKNOWN`, ticket status UNKNOWN, session splitting 0, Golden 0, writer/publisher/scheduler/notifier/merge disabled, full platform coverage/production rollback still HOLD.
> - **Artifact** [12740505389](https://github.com/easonliu714/event_scraper_public/actions/runs/40516301527/artifacts/12740505389), ZIP SHA256 `2c4672a2b0be4f323d638455865bdf19becaed3615babdf7b6526f9b6da3c048`, 2137 bytes, SHA checked by native CI, no raw HTML/screenshots/cookies/network-body archive. Failures retained: prior Run `40514885666` cancelled at OS deps; `40515905716` failed on token placeholder after offline PASS; final `40516301527` succeeded after workflow-only fixes. Earlier 44 Android user PASS and new L8 core UI PASS unchanged.
> - **Next P30-L9-I:** isolate single `39961` current source-list/detail title-drift adjudication before any further field semantic promotions or Android preview refresh. Review other four source-bound dates only with explicit local DOM association, not global page regex. Formal release remains `HARD_HOLD_NO_PUBLICATION`; governance is in Docs Draft PR #8, not Source main.
>

> **2026-10-27 L9-H CI dependency correction and pending native rerun**
>
> - The L9-H dual-source identity architecture requires both L9-G structural Artifact `12738140163` and L9-F original title Artifact `12729277485`; original L9-G typed JSON does not include source titles, so IDs alone cannot establish current title parity. Source Draft PR #45 head `56d309a9d4d895c7adfb525723c6e2a9c4abd2cb`. Native Run `40514885666` CANCELLED at Chromium OS dependencies, Run `40515905716` failed on a literal authentication placeholder in second artifact download **after 36/36 tests PASS**; repaired workflow `github.token` and Run `40516301527` queued. No field evidence yet from this Gate. All source and Pages main fingerprints remain unchanged and formal release `HARD_HOLD_NO_PUBLICATION`.
>

> **2026-10-27 P30-L9-H source cross-binding + local DOM probe architecture checkpoint — CI RUNNING**
>
> ```text
> Source main@fc4f963247d [FROZEN]
> └─ L9-G Draft PR #44 @ 07cc3ce1743a56d2bc60213d345f27672cef97d5
>    └─ L9-H Draft PR #45 @ 21d935e94236ef5a0becd13a0e7fd2496d5f3362
>       ├─ scripts/p30_l9h_ibon_local_dom_hierarchy.mjs [dual SHA source: L9G structure + L9F original titles]
>       ├─ tests/p30/test_l9h_ibon_local_dom_hierarchy.mjs [36 offline tests, pending native CI]
>       └─ .github/workflows/eventradar_p30_l9h_ibon_local_dom.yml
>          └─ Run 40514885666 in progress at this checkpoint
> ```
> - Does NOT use L9-G ID-only report to recreate event titles: read both exact upstream GitHub Artifacts and cross-check SHA manifest / five source IDs / L9-F title / L9-G prior detail parity, then new normal Chromium public detail DOM neighbors. Persist limited label-bound snippets, relation type and image counts, not raw HTML/cookies/network bodies, no unbound whole-body dates. All accepted candidates are `REVIEW_ONLY` and `formalFieldPromoted=false`; `HARD_HOLD_NO_PUBLICATION`. No formal Pages/DB/API/Writer/Scheduler/Android changes. This WIP is not a CI result; supersede only after fresh native CI completion.
>

> **2026-10-27 P30-L9-G ibon detail DOM hierarchy evidence — native CI PASS, no verified role values**
>
> ```text
> event_scraper_public Source main@fc4f963247d [frozen, production blobs immutable]
> └─ Source Draft PR #43 L9-F @ d85504773108281099ec0654c5c772de243f910c
>    └─ Source Draft PR #44 L9-G @ 07cc3ce1743a56d2bc60213d345f27672cef97d5
>       ├─ scripts/p30_l9g_ibon_rendered_field_structure.mjs
>       │  ├─ exact L9F Artifact 12729277485 source SHA and five title-parity IDs
>       │  ├─ normal ephemeral Playwright Chromium five public details
>       │  ├─ bounded DOM probes th/td, dt/dd, same-parent sibling, leaf label: value
>       │  ├─ typed roles EVENT/ADMISSION/SALE/REGISTRATION/VOUCHER/PRICE/VENUE/SESSION
>       │  ├─ reject EVENT_PERIOD neighbor without time token; reject generic PRICE/資訊
>       │  └─ rendered_field_structure.json + manifest.json [SHA sealed]
>       ├─ tests/p30/test_l9g_ibon_rendered_field_structure.mjs [32/32 offline]
>       └─ .github/workflows/eventradar_p30_l9g_rendered_structure.yml
>          └─ GitHub Run 40511115223 → Artifact 12738140163
> ```
> - **Source evidence and architecture effect:** [Run 40511115223](https://github.com/easonliu714/event_scraper_public/actions/runs/40511115223) completed/success, Job `122212973983`, actual normal Chromium each of five ibon Event IDs `39575/39878/39907/39961/39978`: HTTP200, strict official title parity PASS. DOM structures: no `table/tr/th/td` and no `dl/dt/dd`, extensive `strong`/`b` elements; each page yielded exactly 1 recognized `EVENT_PERIOD` label and same-parent sibling probe with `REJECT_MISSING_DATE_TIME`. Total 5 source title parity, 5 rejected label/value associations, **zero accepted review pairs and zero formal promotions**. Do not assert activities lack true show dates or that another section is safe to parse. Original 6/22 ibon cumulative sampled title-parity figure remains unchanged because these are the *same previously verified five*, not five additional distinct activities.
> - **Artifact** [12738140163](https://github.com/easonliu714/event_scraper_public/actions/runs/40511115223/artifacts/12738140163), ZIP SHA256 `769a138757c35711c9b55332e169966fdc0c4a4bd2ffb70166a304610fb3ba42` (2054 bytes), JSON+SHA manifest, verified and unexpired. No raw page HTML, screenshots, cookies, request bodies or private browser state stored. Both source input SHA and output SHA verified by native Actions.
> - **Data gate:** all official `dateStart/dateEnd/price/registrationPeriod/saleWindow/voucherValidity/venue` remain NULL/UNKNOWN, `ticketStatus=UNKNOWN`, `goldenAccepted=0`, `published=false`, Writer/Scheduler/Notifier/merge disabled, `releaseState=HARD_HOLD_NO_PUBLICATION`; no official Pages/data.json/API/DB writes. Prior Android original 44 user attestations and L8 new core UI PASS remain intact. Next **P30-L9-H** bounded DOM section-neighbor/child structure discovery of existing five titles before writing any role parser; avoids global text dates, cross-role promotion and false "price" parsing.
> - Governance remains in two canonical documents on Docs Draft PR #8 only; no production main merge/Preview/ShowNews retirement.
>

> **2026-10-27 SRC-P30-L9-F SHA-pinned ibon real detail/role review architecture — five matches, zero eligible field pairs**
>
> ```text
> Source main@fc4f963247d [unchanged]
> └─ L9-E Draft PR #42 @ 63a079c1bee7111b1ef7b04431607d9845fe3b9f [22 new rendered ibon candidate IDs]
>    └─ L9-F Draft PR #43 @ d85504773108281099ec0654c5c772de243f910c
>       ├─ scripts/p30_l9f_ibon_detail_role_review.mjs
>       │  ├─ validateSource(): SHA-pinned exact 22 candidate IDs + 1 prior parity
>       │  ├─ chooseAdditional(): deterministic 5 distinct untested numeric ibon IDs
>       │  ├─ Chromium normal public detail: exact source URL/ID/title parity, no login/checkout
>       │  ├─ DOM: same-row th/td, adjacent dt/dd, direct label: value only
>       │  ├─ classifyField(): EVENT vs ENTRY vs SALE vs REGISTRATION vs VOUCHER
>       │  ├─ PRICE/資訊 reject, SESSION review-only/no extra records
>       │  └─ detail_role_review.json + manifest.json [SHA sealed]
>       ├─ tests/p30/test_l9f_ibon_detail_role_review.mjs [30/30 negative-positive]
>       └─ .github/workflows/eventradar_p30_l9f_ibon_detail.yml [readonly push CI]
>          └─ Actions Run 40494326021 -> Artifact 12729277485
> ```
> - **Native source proof:** [Run 40494326021](https://github.com/easonliu714/event_scraper_public/actions/runs/40494326021), job `122155815270`, 30/30 offline tests PASS; pinned [L9-E Artifact 12709568132](https://github.com/easonliu714/event_scraper_public/actions/runs/40449476633/artifacts/12709568132) source JSON SHA256 `d24a41262f362fc749c14c48a74dd5e85d27007d634309be6c72f30a8f1fc9ee`. New official ibon detail ID `39575,39878,39907,39961,39978` all HTTP200 and exact title parity. Total tested `6/22`, `16/22` remain without sampled detail. [Artifact 12729277485](https://github.com/easonliu714/event_scraper_public/actions/runs/40494326021/artifacts/12729277485) ZIP SHA256 `811e1b133c253f3cde33c31a203a9ed4bfbfab7418822a9b3a59c00fdd9cf884`, 1842 B; internal JSON/Manifest/SHA256SUMS sealed.
> - **Crucial UI/semantics observation:** current strictly typed label/value DOM extractor yielded **0 eligible adjacent role evidence pairs**, **0 rejected pairs** across five matched rendered pages. This is a **source parser structure limitation**, NOT evidence that ibon events have no dates/tickets/venues. Do not infer the global body date as EVENT_PERIOD, do not promote sale/registration/admission to event-show dates, do not confuse multi-session times with new event IDs. Formal `dateStart/price/salePeriod/registrationPeriod/voucherValidity=null`, `ticketStatus=UNKNOWN`, field promotion 0, Golden 0, Writer/Scheduler/Notifier/Publisher and merge 0.
> - **Next P30-L9-G:** bounded noninteractive normal public-browser DOM layout diagnostic for those five known IDs; identify source-labeled date/price/venue roles or clear HOLD when no bound pairs, add negative fixtures and independent SHA. Avoid raw HTML, personal tokens, arbitrary endpoint guessing, WAF bypass. Main Pages/runtime and original 44 Android PASS plus L8 new core UI PASS remain unchanged; L9-A ten release blockers still mandatory. Two formal governance documents only under Draft PR #8, unmerged.
>

> **2026-10-27 P30-L9-E ibon live browser rendering architecture — 22 REVIEW candidates, native CI PASS**
>
> ```text
> Source main@fc4f963247d [FROZEN, no formal Pages/data/runtime mutation]
> └─ L9-D Source Draft PR #41 @ 8836dc29a6dcf4baaabed08102ffb1b7fbed6bc3 [HTTP-only ibon HTML 200/list0 verified]
>    └─ L9-E Source Draft PR #42 @ 63a079c1bee7111b1ef7b04431607d9845fe3b9f
>       ├─ scripts/p30_l9e_ibon_browser_render.mjs
>       │  ├─ Chromium Playwright 1.55.0: normal, nonstealth public browser, ephemeral context
>       │  ├─ exactly 2 official ibon list navigations, normal first/third-party page resources
>       │  ├─ rendered DOM anchors + same-card heading to canonical numeric activity ID
>       │  ├─ 22 list candidate IDs, sample 1 exact official detail title-parity
>       │  └─ no raw HTML, cookies, request bodies, headless stealth, WAF bypass or publisher
>       ├─ tests/p30/test_l9e_ibon_browser_render.mjs [30/30 mocked positive-negatives]
>       └─ .github/workflows/eventradar_p30_l9e_ibon_browser.yml [push-only contents:read]
>          └─ Actions Run 40449476633 -> Artifact 12709568132 [SHA-sealed]
> ```
> - **Verified run** [40449476633](https://github.com/easonliu714/event_scraper_public/actions/runs/40449476633) completed/success, Job `122008564226` completed/success, immutable L9-D parent and exact three new files source guard, Playwright normal Chromium installed, 30/30 tests PASS. First public `/Index/entertainment` rendered HTTP200 with 67 anchors, 16 script elements, body text 1690 chars and **22** same-card/numeric ibon official detail URL candidates. 64 page resource requests observed, 54 first-party; these are browser resources, **not 64 sampled details**. Second official `/Home/MoreResult?inATAPID=105&inATAPWebType=entertainment` rendered HTTP200 with 34 anchors, 16 scripts, body text 509 chars, **0** bounded event candidates, remains HOLD. 38 page resource requests, 30 first-party. One bounded detail sample `DETAIL_TITLE_PARITY_PASS`, other 21 untested. Artifact [12709568132](https://github.com/easonliu714/event_scraper_public/actions/runs/40449476633/artifacts/12709568132) ZIP SHA256 `866c8b935d47fe391a4fdf8f69eae2a33664d67b6ef0650707a594993a2ccfef` (3020 bytes), contains report JSON, Manifest and SHA256SUMS; independent GitHub readback.
> - **Semantics:** `RENDERED_SOURCE_CANDIDATES_REVIEW_ONLY` is SOURCE/URL/TITLE candidate not guaranteed active event, published schedule, exact multi-session identity or real-time stock. `DETAIL_TITLE_PARITY_PASS` for only one means title agreement not Golden. All candidates have `formalDate=null`, `formalPrice=null`, `ticketStatus=UNKNOWN`, `goldenVerified=false`, `published=false`. No field roles promoted. Original L9-D 0 candidate is for **unrendered raw HTML** and is retained as historically accurate; no prior Gate reimplementation.
> - **Isolation boundary:** L9-E normal browser may request official and standard third-party page scripts as part of rendering, but deliberately records only aggregate source/network data, canonical public event URLs/titles, no arbitrary API endpoint guesses or activity transactions, no cookies, full DOM, logged-in session or private tokens; never changes `docs/data.json`, published PWA, API, DB, scheduler, notifier, Writer, source main or historic Android 44 user PASS. Release remains `HARD_HOLD_NO_PUBLICATION`, L8 core Android PASS with full E2E pending, L9-A ten blockers still active.
> - **Next isolated P30-L9-F:** SHA-pin L9E fresh report and sample **3–5** further official detail pages via approved normal browser, strict identity parity, date-role and PRICE meaningful-token review-only evidence, fail closed on 403/WAF/mismatch, output evidence-only JSON. Do not grant Golden/Publisher/Cloud Scheduler PR #1 or retire repositories; two governance docs live solely on Draft PR #8, not main.
>

> **2026-10-27 SRC-P30-L9-D ibon public fresh DOM diagnostic architecture — CI PASS / zero list**
>
> ```text
> Source main@fc4f963247d (unchanged, protected formal Pages/source blobs)
> └─ L9-C Source Draft PR #40 @ ae469b52e7b7b7f16dda1eeab584be8e16d63f50 [native PASS]
>    └─ L9-D Source Draft PR #41 @ 8836dc29a6dcf4baaabed08102ffb1b7fbed6bc3
>       ├─ scripts/p30_l9d_ibon_public_dom.py [NEW public HTTP only]
>       │  ├─ audited ibon.LISTS: Index/entertainment and Home/MoreResult
>       │  ├─ GET: same-host redirects/HTTPS, <=2 list + 1 strict detail if ID candidate
>       │  ├─ analyze(): direct anchor, JSON-LD Event, same-object public JSON hydration
>       │  ├─ DOM script counts/malformed JSON/body text/render hints, no JS execution
>       │  └─ fresh_ibon_dom_diagnostics.json + manifest.json [SHA sealed]
>       ├─ tests/p30/test_l9d_ibon_dom.py [28/28 mock negatives]
>       └─ .github/workflows/eventradar_p30_l9d_ibon_dom.yml [push only/read only]
>          └─ Run 40447833667 → Artifact 12708438784 [SHA sealed]
> ```
> - **Native result:** [Actions Run 40447833667](https://github.com/easonliu714/event_scraper_public/actions/runs/40447833667) completed/success, Job `122003220447` complete success, exact 3 new paths and source/Pages integrity gate, 28/28 offline tests and **2 new actual HTTPS GETs**. [Artifact 12708438784](https://github.com/easonliu714/event_scraper_public/actions/runs/40447833667/artifacts/12708438784) ZIP SHA256 `e4ec2a8a849abbfaabd76aea7b5117cbed0bd8f04d5f86ae1f47083241c5fb9a`, 1852 B, unexpired/read back; internal manifest and SHA checks PASS.
> - **Actual ibon response architecture:** both official list URLs returned `HTTP_OK/200`, **0 anchors, 0 direct activity IDs, 0 JSON-LD / hydration candidates, visible text length=8, scripts=11** (5 official script source tags, 2 other-host scripts, 4 non-JSON inline scripts). No first-party JS bundle content fetched, no JS runtime executed, so **DO NOT CLAIM hidden API identified or ibon no activities**. L9-C `ibon=HTTP200/list0` remains valid and more precisely diagnosed as `HOLD_PUBLIC_HTML_NO_BOUND_EVENT_ID`. This makes full browser-rendered DOM evidence the next falsifiable dependency, not speculation about cancellation.
> - **Boundaries:** `candidateOrigin=L9D_NEW_PUBLIC_HTTP`, `actualFreshHTTPRequests=2`, `formalFieldPromotions=goldenAccepted=0`, `published=false`, `releaseState=HARD_HOLD_NO_PUBLICATION`; no auto merge/hide/delete, source runtime/Writer/Scheduler/Notifier untouched. Report stores safe HTTP/page SHA and DOM counts only, no raw HTML or downloaded remote third-party scripts, no credentials, no browser automation, no WAF evasion. Any future candidate needs official same-card/same-object identity and detail verification before even REVIEW ONLY field evidence; formal dates/ticket status/price remain NULL/UNKNOWN.
> - **Next P30-L9-E:** regular public-browser rendering in strict read-only isolated CI without anti-bot/login/stealth, capture only DOM safe evidence and bounded link/title roles; if site blocks/returns empty, HOLD. History: 44 Android USER_ATTESTED_PASS, L8 new Android CORE_UI_USER_ATTESTED_PASS unchanged; L9A ten release blockers retained. Formal two governance documents remain exclusively Docs Draft PR #8, not main.
>

> **2026-10-27 SRC-P30-L9-C fresh four-official-adapter architecture — read-only live HTTP/list/detail native CI PASS**
>
> ```text
> event_scraper_public main@fc4f963247d [unchanged; formal docs/data.json/Pages/runtime frozen]
> └─ Source PR #39 L9-B @ b1f831f985074e5011950403823bb1b4c41d16b4 [PASS/HARD_HOLD]
>    └─ Source Draft PR #40 L9-C @ ae469b52e7b7b7f16dda1eeab584be8e16d63f50
>       ├─ scripts/p30_l9c_four_source_fresh.py [new public HTTPS; NO writer]
>       │  ├─ CKSMH Query.list.ctr -> official actId-bound anchors -> 1 detail.sample
>       │  ├─ TWTC exhibition?p=home -> official table rows -> exhibition_more.aspx?id
>       │  ├─ ibon Index/entertainment + Home/MoreResult -> numeric activity ID links (0 currently)
>       │  └─ FamiTicket Home -> official card /Home/Activity/Info IDs -> detail.sample
>       ├─ tests/p30/test_l9c_four_source_fresh.py [25/25 mocked URL/ID/semantic negatives]
>       └─ .github/workflows/eventradar_p30_l9c_four_fresh.yml
>          └─ read-only native CI 40443838700 -> artifact 12707735836 [sha256 sealed]
> ```
> - **Actual native evidence** [Run 40443838700](https://github.com/easonliu714/event_scraper_public/actions/runs/40443838700) completed/success; per-source fresh GET **8 total**; CKSMH 5 current actId candidates/detail title 1/1 match, TWTC 40 capped current exhibition table/detail title 1/1 match, FamiTicket 40 capped card candidates/detail title 1/1 match, ibon two official HTTP200 list GET/0 candidates/detail NOT_ATTEMPTED `HOLD_LIST_ZERO_OR_HTTP`. Source list-positive 3/4, new candidate count 85; these 85 are NOT verified events nor formal field records; 3 title matches prove only sampled source/detail title parity. Internal per-platform HTTP source URLs, source role, current list/detail quality and SHA are in [Artifact 12707735836](https://github.com/easonliu714/event_scraper_public/actions/runs/40443838700/artifacts/12707735836), ZIP digest `74940280bf4df32821b39557b1b52a959ef1c2735709964efc673c889c4399da` (10,272 B).
> - **Identity and field gates:** cksmh_list enforces `actId` official host/path, TWTC table requires recognized bounded exhibition period and canonical `exhibition_more.aspx?id`; ibon canonicalizes official ActivityInfo/Details numeric IDs and rejects outbound domain, FamiTicket admits official query-free opaque detail IDs. No title similarity auto-merge. Raw exhibition periods/venues are `REVIEW_ONLY`; event date/show time/entry/registration/sale/voucher validity/price/ticket status remain unavailable for promotion. No formal date/price/ticket promotions, Golden/Writer/Publisher/Scheduler/Notifier or current Android/data.json changes.
> - **Roadmap and HOLD:** ibon HTTP200/list0 current (JS-specific extraction needed), CKSMH/TWTC/Fami limited detail sampling and capped lists, full 19 platform freshness/accuracy not proven, full L8 Android E2E and production rollback pending; `releaseState=HARD_HOLD_NO_PUBLICATION`. Previous 44 Android user-accepted events and new L8 core UI PASS preserved. Next L9-D is no-bypass official ibon response/DOM diagnostic and source-tier fidelity; not production schedule/writer activation. Both governance documents remain in Draft PR #8 (not main).
>

> **2026-10-27 P30-L9-B source-quality / synthetic rollback architecture — native CI PASS / publication DENIED**
>
> ```text
> Source main@fc4f963247d [FROZEN]
> └─ L9-A Source Draft PR #38 @ d35c3b78f09bcbeeb4da79ea3b6014330798ebfa [release HARD HOLD, CI PASS]
>    └─ L9-B Source Draft PR #39 @ b1f831f985074e5011950403823bb1b4c41d16b4
>       ├─ scripts/p30_l9b_field_quality_rollback.mjs [NO HTTP, immutable artifacts only]
>       │  ├─ L7-B fresh_candidate.json + platform_diagnostics.json [34 upstream HTTP, NOT NEW]
>       │  ├─ L7-C preview-data.json [264/5/259, prior Android core UAT]
>       │  ├─ L9-A release_blocker_matrix.json [10 mandatory HOLD]
>       │  ├─ labelQuality(e) → PRICE/資訊 REJECT; currency/venue/date REVIEW_ONLY
>       │  ├─ review(inputs) → 12 source evidence labels + 19 platform adapter HOLD rows
>       │  ├─ syntheticRollback(isolatedCopy) → tamper then restore SHA parity
>       │  └─ build(inputs, isolatedOutput) → quality/gap/rollback JSON + SHA manifest
>       ├─ tests/p30/test_l9b_field_quality_rollback.mjs [30/30 negative-positive]
>       └─ .github/workflows/eventradar_p30_l9b_field_quality_rollback.yml
>          ├─ Exact L9-A parent, no formal source/Pages/blob changes; three-file add-only
>          ├─ SHA256SUMS and JSON Schema 2020-12 for L7-B/C/L9-A pinned source artifacts
>          └─ Run 40442853866 -> Artifact 12707416716 [HARD HOLD]
> ```
> - **Independent native GitHub result** [Run 40442853866](https://github.com/easonliu714/event_scraper_public/actions/runs/40442853866) completed/success with all 30 positive-negative tests, SHA/Schema parent lineage, 12 actual field labels, report hash, synthetic restore. [Artifact 12707416716](https://github.com/easonliu714/event_scraper_public/actions/runs/40442853866/artifacts/12707416716) ZIP SHA256 `3906b4e9689987429040ce9508fc88e4dbb0491199fd5984e55fb469065114d0`, 6,070 bytes.
> - **Actual quality states:** `VENUE_TEXT_REVIEW_ONLY=6`, `PRICE_TOKEN_REVIEW_ONLY=2`, `REJECT_GENERIC_NON_PRICE=2`, `TIME_ROLE_TOKEN_REVIEW_ONLY=2`. All `formalFieldPromoted=false`. Valid-looking evidence is still not source-level Golden; raw authoritative dates, identity, current ticket availability and classification remain HOLD/UNKNOWN. No newly issued public HTTP requests or platform-specific actual fresh extraction in L9-B. Adapter focus: CKSMH actId + TWTC table + ibon JS + FamiTicket detail title.
> - **Rollback definition boundary:** malicious *synthetic* temporary file changes then copied-baseline exact byte restore, restored SHA `070a4a6eb3c0fc8a0ebccee44ed8f0016c9a31d9aa3872a2801a8497a58bf59e`; copies removed. `productionRollbackVerified=false`. Real writer, recovery rehearsal of deployed Pages and three-repository migration/retirement are not implemented. `releaseState=HARD_HOLD_NO_PUBLICATION`, Cloud Scheduler PR #1 HIGH_RISK_HOLD, Source PRs unmerged. User's original 44 Android UAT PASS and L8 preview CORE_UI_PASS are preserved.
> - **Next P30-L9-C** bounded *new* source-specific HTTPS acquisition and parser effectiveness under exact SHA-sealed output, no bypass, no formal DATA.JSON / PWA / API / DB update until separate quality/release gates; all platform zero-lists remain HOLD absent explicit verified evidence. Governance two documents only in [Docs Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8), not source main.
>

> **2026-10-27 SRC-P30-L9-A immutable evidence-to-release-blocker architecture — 26/26 native CI PASS, RELEASE HARD_HOLD**
>
> ```text
> event_scraper_public: production main fc4f963247d (FROZEN)
> └─ L7-C Source Draft PR #37 @ 4668dab1c7061e9d752da0cdfcd58a004e1459f1 (CI & Android CORE UI PASS)
>    └─ L9-A Source Draft PR #38 @ d35c3b78f09bcbeeb4da79ea3b6014330798ebfa
>       ├─ scripts/p30_l9a_release_blockers.mjs [NO NETWORK / NO APP WRITES]
>       │  ├─ exact L7-B fresh_candidate.json + platform_diagnostics.json
>       │  ├─ exact L7-C preview-data.json
>       │  ├─ SHA/identity/type/role/candidate/date/ticket/full-coverage validation
>       │  └─ release_blocker_matrix.json + manifest.json (HARD_HOLD_NO_PUBLICATION)
>       ├─ tests/p30/test_l9a_release_blockers.mjs [26/26 positive/negative]
>       └─ .github/workflows/eventradar_p30_l9a_release_blockers.yml [push-only read permissions]
>          ├─ download exact L7-B fresh Artifact Run 40353636708 [SHA/Schema]
>          ├─ download exact L7-C Android Artifact Run 40436642012 [SHA]
>          └─ Native CI 40439742917 -> Artifact 12705887127 [SHA sealed]
> ```
> - CI <https://github.com/easonliu714/event_scraper_public/actions/runs/40439742917> completed/success and Job `121976963857` all steps PASS. Artifact <https://github.com/easonliu714/event_scraper_public/actions/runs/40439742917/artifacts/12705887127> ZIP SHA256 `a576ddb077342920659288392cbaf66cfcb4e24665cf5eb0a6b4e6f123c54aa3`, 2766 bytes. Exact three added files vs L7C parent; frozen runtime/Pages blobs; READONLY.
> - `evaluate(fresh,diag,preview,raw)`: strong source SHA, run ID, typed source and 264↔5↔259 identities; reject any formal date/price/ticket promotion or cross-source title/URL drift; 10 mandatory blockers. `build(paths,out)`: destination confined to isolated workspace, output blocker JSON + SHA manifest; `releaseState=HARD_HOLD_NO_PUBLICATION`, `readyToMerge=false`, `readyToDeploy=false`, `readyToEnableWriter=false`, `readyToStartScheduler=false`, `readyToRetireRepos=false`, `approvedActions=[]`. **This is a proven deny Gate, not formal release readiness.**
> - Android L8 user evidence remains `CORE_UI_PASS`/full E2E incomplete; original 44 user-attested PASS preserved. `PRICE/資訊` candidate snippets flagged invalid for numeric price promotion; source official date/price/venue/sale/registration/ticket data still UNVERIFIED/UNKNOWN. No production Publisher, Golden, database migration, Scheduler PR #1, notifications, repository closure or merges. Next L9-B may run isolated field quality negatives/rollback rehearsal planning, never auto-publish. Governance lives in Draft PR #8, not main.
>

> **2026-10-27 P30-L8/G5K Android loopback UAT core PASS with bounded real-device evidence**
>
> - Termux SHA256 verified `eventradar-p30-l7c-isolated-android-preview.zip` equals official sealed Artifact ZIP `a524f40fd46cff6ad60046c314e70eaa44499fcddab035956ae16d25cadde3b6`; inner `index.html`, `preview-data.json`, `README.txt` all passed `sha256sum -c SHA256SUMS.txt`. Original official Source `main@fc4f963247d68eed29425808cc14e7250f312d05`, Docs-only Draft PR #8, source Draft PR #37 unchanged at start.
> - Observed via provided Android screenshots: same-phone Chrome on `http://127.0.0.1:8766/index.html`, 264 total/5 detail title parity/259 review-only summary, default five cards, Event Go platform filter exactly one card, modal content and controls for four sampled cards (Event Go, UDN, iNDIEVOX, 華山1914), event/venue/price/ticket/date roles kept as labeled source evidence only; responsive screen no obvious overprint. Mark `ANDROID_L8_CORE_UI_USER_ATTESTED_PASS`. Do not claim keyword typing, five individual modal interactions, actual source HTTP navigation or all 259 rows user-verified; `ANDROID_L8_FULL_E2E_HOLD_PARTIAL_EVIDENCE`.
> - Formal field promotion prohibited: review snippet `PRICE/資訊` on Event Go/UDN is ambiguous, not a numeric price; UI labels `UNKNOWN`, `未核實`, `非 Golden` correctly disclose uncertainty. User-authorized next isolated Gate is **P30-L9-A read-only Release Blocker Matrix**, with explicit blocker statuses and SHA-sealed diagnostics, no Writer, Publisher, PR merge, repo retirement or Cloud Scheduler. Historical Android original 44 remain USER_ATTESTED_PASS.
>

> **2026-10-27 SRC-P30-L7-C isolated Android review UI CI PASS — architecture authority update**
>
> ```text
> event_scraper_public (main fc4f963247d; UNCHANGED)
> └─ L7-B Source PR #36 @ e680456f0033e528fb25da61a4b3b6e35aa22447 [native CI PASS]
>    └─ L7-C Source Draft PR #37 @ 4668dab1c7061e9d752da0cdfcd58a004e1459f1
>       ├─ scripts/p30_l7c_isolated_preview.mjs   [source SHA typed parent -> pure data converter]
>       ├─ scripts/p30_l7c_isolated_index.html    [mobile safe DOM UI/search/platform/quality/modal/official URL]
>       ├─ tests/p30/test_l7c_isolated_preview.mjs [18/18 CI positive-negative]
>       └─ .github/workflows/eventradar_p30_l7c_preview.yml [user-uploaded, native push CI PASS]
>          └─ pinned L7-B Run 40353636708 fresh evidence + SHA/2020-12 schema
>             -> L7-C isolated index.html + preview-data.json + README.txt + SHA256SUMS.txt
>                artifact 12704885384 SHA256 a524f40fd46cff6ad60046c314e70eaa44499fcddab035956ae16d25cadde3b6
> ```
> - **Gate provenance:** dedicated [GitHub Actions Run 40436642012](https://github.com/easonliu714/event_scraper_public/actions/runs/40436642012), completed/success, Job `121966765821` all steps success, exact frozen parent and four-add-only diff, 18 offline negatives PASS, HTML inline JavaScript syntax PASS, inherited source Artifacts sealed/read-back. The formerly blocked workflow publication is now resolved through user web upload; retain prior WIP/HOLD snapshot as historical evidence but mark it superseded. Docs governance still only [Draft PR #8](https://github.com/easonliu714/event_scraper_public/pull/8), no main merge.
> - **UI and DATA:** upstream collection used **34 real GETs** over 19 public platforms: 16 HTTP OK, 12 list-positive, 264 **candidate** source IDs; only 5 of 12 sampled details pass title parity. L7-C performs **zero additional fresh site HTTP** and uses only L7-B immutable inputs, `candidateOrigin=L7C_PINNED_NEW_HTTP_ARTIFACT_PREVIEW_NOT_A_NEW_CRAWL`. Preview data counts: total 264, detail-title-parity tier 5, list-only/title-identity-HOLD 259. Search/platform/quality filter and modal original official/third-party link; external source from allowlisted HTTPS, no Javascript HTML injection or production fetch. `dateStart/dateEnd/venue/price/registrationPeriod/saleWindow/voucherValidity=null`, `ticketStatus=UNKNOWN`, no automatic merges, field Golden promotion, data writer, notifier or cloud scheduler.
> - **Next P30-L8 G5K:** isolated same-phone Android loopback UAT **not yet performed**, requiring final Artifact SHA and internal SHA256SUMS before testing, verify category/tier behavior, five trusted detail-title-parity only (not fully official event/price verification), 259 explicitly pending, relative link/UNKNOWN text, no text overlap and normal modal close/HTTPS source navigation. Historic 44 Android records remain USER_ATTESTED_PASS without re-test. L9 controlled Writer/Publisher and L10 repository retirement remain LOCKED.
>

> **2026-10-26 L7-C new candidate mobile preview source tree: WIP / CI HOLD**
>
> ```text
> Source [Draft PR #37, head 1f76f00173d3ec96d88f9b11f65bd995e020bd45]
> ├─ scripts/p30_l7c_isolated_preview.mjs     [candidate; immutable L7B evidence input, no HTTP]
> ├─ scripts/p30_l7c_isolated_index.html      [candidate; responsive review-tier UI; safe DOM]
> └─ tests/p30/test_l7c_isolated_preview.mjs  [candidate; 18 unexecuted in native CI]
> Native L7-C GitHub Actions workflow: NOT PUBLISHED / platform safety write BLOCKED
> Artifact: NONE; SHA read-back: NONE; Android UAT: NOT STARTED
> ```
> - Exact L7B parent Draft PR #36 `e680456f0033e528fb25da61a4b3b6e35aa22447` remains **PASS** under [Run 40353636708](https://github.com/easonliu714/event_scraper_public/actions/runs/40353636708) (19-source actual GET, 16 HTTP OK, 12 list-positive, 264 candidates, 12 detail GET, five title-parity, 12 labeled review snippets). Intended L7-C source is only the SHA-sealed [Artifact 12665097220](https://github.com/easonliu714/event_scraper_public/actions/runs/40353636708/artifacts/12665097220), never L7-A historical JSON or production docs/data.json.
> - Proposed UI defaults to 5 detail-title parity candidates and marks 259 others list-only/title-HOLD, official links only, formal event dates/sale/registration/voucher/price/ticketStatus UNKNOWN, third-party StrollTimes never first-party. This is **source design only, not live E2E proof**. Workflow publication requires a permitted authorized route; do not circumvent security blockers, merge PR or request new Android UAT until actual CI, artifact SHA and independent read-back PASS. Prior Android accepted 44 preserved.
>

> **2026-10-26 P30-L7-B final live-source topology and quality tier summary (supersedes pending entry below)**
>
> - Source [PR #36](https://github.com/easonliu714/event_scraper_public/pull/36) Draft HEAD `e680456f0033e528fb25da61a4b3b6e35aa22447`, base PR #35 `17d189c5615cdd58db3ea0e7e1ea9472a5ab1cc8`; Native [Run 40353636708](https://github.com/easonliu714/event_scraper_public/actions/runs/40353636708) completed/success, 34/34 offline, exact four added paths, SHA and JSON Schema PASS; [Artifact 12665097220](https://github.com/easonliu714/event_scraper_public/actions/runs/40353636708/artifacts/12665097220) ZIP `sha256:8ad3a6c8d0b3259ef9187830a33455365a8ff4c7bc30061653345d74cef758c6`.
> - **Real source stage counts:** fresh HTTP requests=34; 19 platform entries; HTTP_OK=16 (3 HTTP_403), LIST_POSITIVE=12, LIST_CANDIDATES=264 (unreviewed), DETAIL_HTTP_OK=12/12, DETAIL_TITLE_PARITY=5/12, FIELDS_LABELED_REVIEW_ONLY=12 snippets. Only five detail-source title parity matches; all 264 are not automatically verified events. None of the five are promoted to Golden; `fullPlatformCoverageVerified=false`.
> - **Stage-level source holds:** ACCUPASS 25 list-only, OPENTIX 40 list/1 parity, UDN 6 list/1 parity, FamiTicket 40 list-only, 年代 28 list-only, TixFun 24 list-only, Event Go 38 list/1 parity, 華山 7 list/1 parity, 松山 1 list-only, KidsClub 33 list-only, iNDIEVOX 19 list/1 parity, StrollTimes 3 aggregator-only/list; CKSMH/TWTC/ibon HTTP200 but generic LIST0, 寬宏 HTTP200/list0, KKTIX/拓元/BeClass HTTP403. Every stage failure remains a specific HOLD, never silently interpreted as expired/removed events.
> - **Data-to-UI contract for next L7-C:** default detail-confirmed tier [5 current candidates] vs list-only/mismatch [259 candidates] clearly separated; third-party StrollTimes cannot be rebranded as official organiser; no date/price/ticket-status inference; official platform link only if URL provenance checked. A new isolated file-based preview must not replace `docs/index.html`, `docs/data.json` or P20 preview; user-attested Android 44 unchanged. L8 Android test is only of **new** isolated candidate UI.
>

> **2026-10-26 SRC-P30-L7-B fresh acquisition architecture — isolated Source Draft PR #36**
>
> ```text
> event_scraper_public [source only; main unchanged]
> └─ feat/eventradar-p30-l7b-fresh-acquisition [PR #36 Draft on PR #35]
>    ├─ scripts/p30_l7b_fresh_acquisition.py
>    │  ├─ nineteen named public HTTPS list-entry configurations [no old JSON input]
>    │  ├─ get_page -> 403/404/429/redirect/timeout/oversize/content-SHA evidence
>    │  ├─ parse_list -> conservative canonical host + event URL + title + stable ID
>    │  ├─ detail sample <=1/platform -> HTTP + exact source URL + title parity
>    │  ├─ labeled EVENT_PERIOD / ADMISSION_TIME / REGISTRATION_PERIOD /
>    │  │  SALE_PERIOD / VOUCHER_VALIDITY / VENUE / PRICE only as REVIEW_REQUIRED
>    │  └─ emit isolated fresh_candidate.json + platform_diagnostics.json + manifest.json
>    ├─ tests/p30/test_l7b_fresh_acquisition.py [34 mocked positive/negative cases]
>    ├─ schemas/p30_l7b_fresh_candidates.schema.json [Draft 2020-12, freshness guard]
>    └─ .github/workflows/eventradar_p30_l7b_fresh.yml [push-only, read-only, SHA seal]
> ```
> - **Immutable boundaries:** PR #36 base PR #35 at `17d189c5615cdd58db3ea0e7e1ea9472a5ab1cc8`, main `fc4f963247d68eed29425808cc14e7250f312d05`, exact four additions verified by native CI; no replacement of historical offline L7A 12-node + 66-edge snapshot, no use of `docs/data.json` or old L1 response for new data. All three existing Repo main/Android original 44 preserved.
> - **LIVE run 40353068648 completed/success** at first HEAD `5e132dbc881b75aae124833110969084940c2b6d`: actual fresh HTTP 33, 19 configured sources, 15 HTTP 200, 11 nonempty parsed list groups, 223 list-identity *candidates*, 11 HTTP 200 sampled details, only 5 conservative title parity passes and 12 extracted role-labeled review-only snippets. Artifact 12665121626 SHA256 `280ecd745e87919e6f711bbe4251d185c63c46021b1557d93f2ae4a4ac36de6c`. Success is only **minimum actual HTTP → LIST → identity-matched DETAIL chain**; full 19-platform coverage is false and no event metadata Golden promoted.
> - **Four known source-entry corrections now on same PR #36** HEAD `e680456f0033e528fb25da61a4b3b6e35aa22447` pending subsequent CI: FamiTicket `/Home` official portal, ibon `/Index/entertainment` official JS shell, TWTC `/exhibition?p=home` official exhibition listing, CKSMH `/Query.list.ctr` official cultural activity list. These routes came from prior source parser Gated code, but **each must still make a new GET**; live CI pending, no false claim of success. Other platforms remain per-source HOLD when 403, no list or detail title mismatch; no bypass.
> - **Source JSON:** `candidateOrigin=L7B_ACTUAL_NEW_PUBLIC_HTTP`, `collectedAtUTC`, `actualFreshHTTPRequests`, `sourcePlatform`, `sourceRole`, `sourceUrl`, `listEvidence`, `detailHttp`, `detailTitle`, `detailIdentityVerified`, `fieldEvidence[{role,label,observedValue,sourceUrl,verification:REVIEW_REQUIRED}]`. Formal `dateStart/dateEnd/eventTimeZone/venue/price/registrationPeriod/saleWindow/voucherValidity=null`, `ticketStatus=UNKNOWN`, `category=待分類`, `mergeAllowed=goldenVerified=published=false`. Unit mock explicitly `candidateOrigin=L7B_SYNTHETIC_TEST_INJECTION_NOT_FRESH`, fresh count zero, must fail LIVE schema acceptance. Label observations must not conflate registration/sale/admission/show periods.
> - **Next layer:** P30-L7-C current-source isolated JSON quality review + separated preview UI → L8 G5K new-source Android E2E. L9 Writer/Publisher/rollback and L10 consolidation remain HOLD until explicit approval; Cloud Scheduler PR #1 remains HIGH_RISK_HOLD. Two governance files only on docs Draft PR #8, never silently promoted to main.
>


> **2026-10-26 SRC-P30-L7-A source pinned sample to schema 2020-12 candidate JSON architecture**
>
> - **功能隔離**：[Source Draft PR #35](https://github.com/easonliu714/event_scraper_public/pull/35) `feat/eventradar-p30-l7a-isolated-snapshot@17d189c5615cdd58db3ea0e7e1ea9472a5ab1cc8`，base L6B PR #34 `c42ee0f4125bf94c0c948a08e60cce677887e324`，四新檔：`scripts/p30_l7a_isolated_candidate_json.mjs`、`schemas/p30_l7a_isolated_candidates.schema.json`、`tests/p30/test_l7a_isolated_candidate_json.mjs`、`.github/workflows/eventradar_p30_l7a_snapshot.yml`。**No network**：原生 Github Actions 下載 L6B Run `40331119770` exact SHA-sealed archive → `cross_platform_review.json` → `checkParent()` source URL / identity / 12 records / 66 pair / 2 reference / 3 ibon show roles → `transform()` → isolated `candidate_sample.json` + `relationships_review.json` + `manifest.json` → schema Draft 2020-12 validation＋SHA manifest＋ZIP artifact；任何 `docs/` production data path 目的地 fail-closed。
> - `candidate_sample.json` **root schema**：`{kind:"EVENTRADAR_P30_L7A_ISOLATED_SAMPLE_CANDIDATES_V1",schemaVersion:"1.0.0",runId:"P30-L7A-SNAPSHOT-<inputSha16>",candidateOrigin:"L7A_PINNED_HISTORICAL_EVIDENCE_NOT_FRESH",actualFreshHTTPRequests:0,evidenceAsOfUTC:null,fullPlatformCoverageVerified:false,sampledSourceOnly:true,sourceParentKind,sourceParentRunId:40331119770,sourceParentSHA256,candidateCount:12,platformBreakdown:{StrollTimes:6,FamiTicket:4,ibon:2},candidateEventRecords[12],...GOLDEN/WRITER/PUBLISHED:false}`。每筆 `candidateEventRecords[]` 具有 `candidateId=er7a_<sha256(platform+\n+url).slice(0,24)>`、`runId`、`sourcePlatform`、`sourceRole`、`sourceUrl`、`officialLinkUrl`、`firstPartyReferenceUrl`、`qualityState`、`qualityFlags`、`sourceDateEvidence[]`、`showSessionEvidence[]`、`candidateSessionCount`、`sourceLineage[]`、`categoryHint`、正式 `category:"待分類"`／`dateStart/dateEnd/eventTimeZone/venue/price/registrationPeriod/saleWindow/voucherValidity:null`、`ticketStatus:"UNKNOWN"`、`goldenVerified:false`／`published:false`／`mergeAllowed:false`。
> - **欄位角色邊界**：Bitan `GOV_OFFICIAL_CALENDAR` `sourceDateEvidence[{dateRole:"OFFICIAL_EVENT_PERIOD_REVIEW_ONLY",value:["2026-10-17","2026-12-13"]}]` **不提升正式 dateStart/dateEnd**；NieR 官方製作方 2/20 18:00、2/21 14:00 `showSessionEvidence[2]`（`isEventRecord:false`、原加場公告發佈時間仍 HOLD），`candidateSessionCount=2` **仍只有一筆 ibon source event**；RUNIDRE 的第三場只有未核實的 count，不偽造原製作方 show evidence。其餘 10 筆沒有可核定日期維持 NULL。StrollTimes article 官方身分只確立碧潭一條 government reference，其餘仍保留原 `sourceUrl` 和 `qualityState=AGGREGATOR_ARTICLE_OFFICIALITY_HOLD`。
> - `relationships_review.json` 是**獨立** 66 個兩兩身分審核（其中跨平台 44），每組 `{a:candidateId,b:candidateId,relationship:"UNPROVEN_DO_NOT_MERGE",reviewStatus:"REQUIRES_INDEPENDENT_FIRST_PARTY_SAME_EVENT_PROOF",mergeAllowed:false,deleteAllowed:false,hideAllowed:false}`，不與公開活動清單混在一起。 `manifest.json` 將 upstream source SHA、產物檔 SHA 和 deterministic runId 做 parity；不同執行時間的同一來源得到相同 runId/源 ID，避免假裝即時新 crawl。
> - [GitHub Run 40333136396](https://github.com/easonliu714/event_scraper_public/actions/runs/40333136396) completed/success，30/30 Node negative tests、SHA pinned exact input、正式 main blob scope、2020-12 JSON schema `jsonschema.FormatChecker`、12/66 及角色區隔語義 Gate、輸出 SHA 全 PASS。實際 `runId=P30-L7A-SNAPSHOT-e1e8b58812dc5b6d`，input SHA `e1e8b58812dc5b6ddee5ae9630bd6929f96bf470bcfd04637a0a2463aba687e4`；封存 [Artifact 12655660899](https://github.com/easonliu714/event_scraper_public/actions/runs/40333136396/artifacts/12655660899) ZIP digest `sha256:35eb9d9f604b24ce639ef7693c8aaf60758dc4b252487f0f6138bc846100c1e4`。Source main `fc4f963247d68eed29425808cc14e7250f312d05`、Android 原 44 USER_ATTESTED_PASS、正式 PWA/JSON/通知/排程完全不動，PR #35／治理 [PR #8](https://github.com/easonliu714/event_scraper_public/pull/8) 仍 Draft。
> - **下階段層級**：`P30-L7-B bounded FRESH actual HTTP/list/detail source evidence` → `P30-L7-C isolated current candidate JSON + independent preview (explicit origin/freshness status)` → `P30-L8 G5K Android/PWA new-source real-device UAT`。新 HTTP 之前絕不稱 12 個 historical sample 為 19 平台全量 fresh data，無法查證日期／票況時保留 UNKNOWN 與官方連結；未授權不得 merge、publish、開 notifier/cron 或 retire other repos。
>


> **2026-10-26 P30-L6-B cross-platform source event, show/session and two origin references architecture**
>
> - Source Draft [PR #34](https://github.com/easonliu714/event_scraper_public/pull/34) 在上階段 L6A [PR #33](https://github.com/easonliu714/event_scraper_public/pull/33) frozen HEAD `774e2de11580ed961658d6a6254b34ae4ded57c7` 新增 `scripts/p30_l6b_g5j_cross_platform_identity.mjs`、`tests/p30/test_l6b_g5j_cross_platform_identity.mjs`、`.github/workflows/eventradar_p30_l6b_g5j.yml`。唯一資料輸入為 4 組 sealed GitHub Actions Artifacts (L6A Run `40324420431`、FamiTicket L5D Run `40312137162`、ibon L5A Run `40301911354`、NieR original producer L5C Run `40305582187`)：`SHA256SUMS.txt` 驗證 → `verifyInputs({g5j,fami,ibon,nier})` Source URL/role/eventID/HTTP/title/date/officiality → `reconcile()` 12 source-event records＋66 pairs＋2 first-party provenance edges → isolated `cross_platform_review.json`。**本 Gate 不接網路、不讀正式 DB、無 web/publish API 操作**。
> - `candidateRecords[12]`: `6 THIRD_PARTY_AGGREGATOR_ONLY`＋`4 FamiTicket OFFICIAL_TICKET_DETAIL_EXACT_TITLE`＋`2 ibon OFFICIAL_TICKET_DETAIL_EXACT_TITLE`，每個有 `{platform,eventUrl,title,provenance,referenceFirstPartyUrl,referenceTimeRange,verifiedSourceEventId,sessionCount,unverifiedSessionCount,categoryHint,categoryVerified:false,eventDateStart:null,eventDateEnd:null,ticketStatus:"UNKNOWN",price:null,mergeAllowed:false,published:false}`。NieR ibon **2 show sessions ≠ 2 independent event IDs**；原 ibon 2 events／3 raw show candidates 納入來源身分，不把「開放入場」「售票日期」「場次追加公告」當作獨立活動或 Golden。FamiTicket 4/4 來源標題與 URL 經比對，但三筆展覽實際展期不足維持 UNKNOWN。
> - `examinedPairs[66]`: 44 跨平台＋22 同平台，每條記錄 `{a,b,platforms,crossPlatform,titleEqualityObservation,organiserIdentityParity:"NOT_PROVEN_BOTH_SIDES",primarySourceEventIdParity:"NOT_PROVEN_BOTH_SIDES",activityEditionParity:"NOT_PROVEN",venueIdentityParity:"NOT_PROVEN_BOTH_SIDES",eventDateRoleParity:"NOT_PROVEN_BOTH_SIDES",showSessionIdentityParity:"NOT_PROVEN",action:"RETAIN_SEPARATELY_REVIEW_ONLY",automaticMergeAllowed:false,automaticHideAllowed:false,deleteAllowed:false,duplicateAccepted:false}`。 `firstPartyReferenceEdges[2]` 僅 Bitan governor calendar 與 NieR original producer tour；其存在**不代表任何兩個跨平台來源活動已證實重複**。明確限制欄位未確認時不能判定同一活動、主辦、版次、場館或 session。
> - Final [GitHub Actions 40331119770](https://github.com/easonliu714/event_scraper_public/actions/runs/40331119770) completed/success，34/34 negative tests、四份 upstream SHA manifest、formal runtime Source Blob/PR parent identity、12/66/44/22/2 schema、零 publication/merge/hide/delete/fieldDate/category upgrade、output SHA sealed [Artifact 12654907565](https://github.com/easonliu714/event_scraper_public/actions/runs/40331119770/artifacts/12654907565) ZIP digest `sha256:2dd2e49145c6e250a36efc3ba6371892c611436eaf15d3061ed7d999a1eec506` PASS。最終 Source PR #34 HEAD `c42ee0f4125bf94c0c948a08e60cce677887e324`，Source main `fc4f963247d68eed29425808cc14e7250f312d05`、Android 44 user-attested PASS 完全未改；首輪 CI `40330918202` fixture 漏 Bitan official period 而 FAIL，已修正，不能回報最初 FAIL 為 PASS。
> - **下一階段 P30-L7-A** 建立可驗證的新隔離 JSON candidate schema：來源鍵 `platform+officialSourceUrl`、`run_id`、`sourceRole`、`fieldEvidence`、`eventDateRole`、`sourceQuality`；把 `same-event match`、`same-article`、`parent-child`、`show-session` 四種不同邊標籤保持分開。先只對已核實的受限樣本做 smoke，L7-B 才逐步擴展全新 19 平台 current HTTP/list/details 的新數據集；沒有新的 HTTP 讀回不能假稱全新資料。最後 P30-L8 提供真正可實機 Android/PWA 預覽包，在此之前保持正式 Writer、Golden、通知與 Repo 退役 LOCKED。
>


> **2026-10-26 P30-L6-A G5J reversible six-node fifteen-pair classification architecture**
>
> - Source [Draft PR #33](https://github.com/easonliu714/event_scraper_public/pull/33)（base L5-E3 PR #32 frozen HEAD `7057990d9e698302fa60e933b7579492b8969620`），新三檔 `scripts/p30_l6a_g5j_reversible_dedup.mjs`、`tests/p30/test_l6a_g5j_reversible_dedup.mjs`、`.github/workflows/eventradar_p30_l6a_g5j.yml`。單向資料流 `L5E3 sealed identity_graph_review.json`（含 E1/E2 父來源 artifact SHA）→ `verifyGraph()`（schema、六 canonical article URLs、7 exact typed edges、Bitan first-party proof 僅 1 個、4 H1 drift review notes、零正式升級）→ `classificationHint()` 與 `pairEvidence()` → `buildReview()` → isolated `dedup_classification_review.json`；**Node pure offline, zero network/site fetch and zero formal DB/PWA writes**。
> - `reviewedCandidates[6]` 含 `{id,homepageCardTitle,observedArticleH1,sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",provenance,provenanceRank,identityReview,relationshipRisk,categoryHint,categoryEvidence,classificationReason,officialCategoryVerified:false,referenceOfficialUrl,referenceOfficialPeriod,dateStart:null,dateEnd:null,venue:null,ticketStatus:"UNKNOWN",price:null,mergedWith:[],autoMergeAllowed:false,autoHideAllowed:false,deleteAllowed:false,goldenVerified:false,published:false}`。分類來源只有標題 keyword，5 `文化節慶`、1 `藝文展覽` **PROVISIONAL**，不是官方驗證；Bitan 的政府原始活動期間只存在 `referenceOfficialPeriod`，不自動升級 `dateStart/dateEnd`。
> - `reviewPairs[15]` 含兩個不同 article URL、`titleRelationship`、`sharedTitleEvidence`、`primarySourceCrossIdentity/organiserSame/venueSame/dateOrSessionSame/editionSame:"NOT_PROVEN"`、`relationship:"UNKNOWN_NOT_MERGED"`、`proposedAction:"KEEP_SEPARATE_PENDING_EVIDENCE"`、`mergeAllowed:false`、`autoHideAllowed:false`、`deleteAllowed:false`。`sourceEvidenceEdges[7]` 只保留 E3 6 個 `AGGREGATOR_LIST_CARD_POINTS_TO_SAME_ARTICLE` 和 1 個 `ONE_EVENT_OFFICIAL_GOV_CALENDAR_CORROBORATED`（Bitan），不得轉換成正式事件合併。來源證據 `provenanceRank` 是「來源成熟度」而非重複概率。
> - 原生 [Run 40324420431](https://github.com/easonliu714/event_scraper_public/actions/runs/40324420431) **30/30 test + input SHA + Source production Blob + 6/15/7 schema + sealed artifact PASS**，[Artifact 12651050317](https://github.com/easonliu714/event_scraper_public/actions/runs/40324420431/artifacts/12651050317) digest `sha256:8ad284d56998949a4cff44f094c3dcbace17e1c96cba257824c77abc3850f06d`。PR #33 HEAD `774e2de11580ed961658d6a6254b34ae4ded57c7`；Source `main@fc4f963247d68eed29425808cc14e7250f312d05`、Android 44 original PASS、formal `docs/data.json`/PWA remains untouched。下階段 L6-B first-party cross-platform EventID／edition／time／session 類型區隔＋negatives，再進 L7 isolated fresh JSON → L8 Android E2E，禁止自動合併、下架、發布。
>


> **2026-10-26 P30-L5-E3 title relationship graph and no automatic parent/subevent merge**
>
> - Source [Draft PR #32](https://github.com/easonliu714/event_scraper_public/pull/32) `feat/eventradar-p30-l5e3-article-identity-graph@7057990d9e698302fa60e933b7579492b8969620`（stack E2 PR #31 HEAD `f0b07bf4ad45ed9e833d6825c4c119097c698694`）三新增檔 `scripts/p30_l5e3_strolltimes_identity_graph.mjs`、`tests/p30/test_l5e3_strolltimes_identity_graph.mjs`、`.github/workflows/eventradar_p30_l5e3_title_graph.yml`。E1 [Run 40314650154](https://github.com/easonliu714/event_scraper_public/actions/runs/40314650154) `lineage_evidence.json`＋E2 [Run 40315847664](https://github.com/easonliu714/event_scraper_public/actions/runs/40315847664) `independent_gov_event_review.json` 兩個 parent schema/資料版次 SHA Gate→6 個 exact StrollTimes article URLs stock Chromium re-observe H1→`lexicalIdentity()`→`graphFromEvidence()`→隔離 `identity_graph_review.json`，沒有外站爬取、服務啟用、官方寫入或通知。
> - 重要 schema：`nodes[]:{id:<canonicalAggregatorArticleUrl>,homepageCardTitle,articleH1,priorE1TitleStatus,currentTitleState,titleOverlapEvidence,officialGovernmentProof,mergeAllowed:false,sourceEventDateStart:null,sourceEventDateEnd:null,ticketStatus:"UNKNOWN",price:null,goldenVerified:false,published:false}`；`edges[0..5]:{kind:"AGGREGATOR_LIST_CARD_POINTS_TO_SAME_ARTICLE",from:"strolltimes-home-card:<url>",to:<url>,mergeAllowed:false,originalOrganiserProven:false}`＋第七條僅碧潭 `ONE_EVENT_OFFICIAL_GOV_CALENDAR_CORROBORATED`（`reviewOnlyOfficialEventPeriod=["2026-10-17","2026-12-13"]`，E2 first party calendar URL），絕不將卡片相同 article URL 作跨活動 `DELETE/MERGE`。
> - 標題分類：`AGGREGATOR_TITLE_IDENTITY_MATCH`（只允許原標題完全一致或合法結尾括號 MM/DD 展示時間後綴）；`EDITORIAL_HEADLINE_EXTENSION_REVIEW`（原標題加冒號／副標，例如香山濕地藝術季、新北濕地藝術季、**2026晴空季**，且 `parentChildRelationship="EDITORIAL_SUBTITLE_RELATIONSHIP_NOT_PROVEN"`）；`TITLE_OVERLAP_RELATIONSHIP_REVIEW`（共有至少 5 個實質中文字、可能同系列但不同子活動，例如「桃園眷村文化節」vs「龜山眷村故事館場次」）；`DISJOINT_TITLE_IDENTITY_HOLD`／`HTTP_OR_REDIRECT_HOLD`。這些都僅形成 **review notes**，`mergeAllowed=false`，任何年份或短城市字串都不足以確認同一場活動。
> - Gate 真實 GitHub [Run 40318751941](https://github.com/easonliu714/event_scraper_public/actions/runs/40318751941) completed/success，27/27 test、6 個公開文章 200、2 H1 original matched、3 editorial/1 series-overlap review、0 confirmed parent/subevent、0 auto merge、1 government event reference、2 parent SHA、正式 `docs/data.json`／`docs/index.html`／`scraper.py` identity Gate、isolated SHA manifest 皆 PASS；Artifact [12647638215](https://github.com/easonliu714/event_scraper_public/actions/runs/40318751941/artifacts/12647638215) digest `sha256:a412483fe6e8ecc53e088baadec21020464ee9ab82b545c424a6d93c35df9596`。E3 的 6 個重新讀回頁面不等於 StrollTimes 24 篇皆有原始官方來源；僅碧潭 1 個 FIRST-PARTY REVIEW evidence，`originalOfficialEventUrl`、正式日期／票況維持未升級。
> - **下一系統演進 P30-L6-A → L6-B G5J**：使用 graph data 執行純離線、可逆、人工可審計的「活動同一性」與「多場次／多場域／同年份不同屆」分類，將 same-aggregator-article-URL 與 independent FIRST PARTY edge 及 potential parent/subevent 依證據強度分開；未證明的活動關係 **一定 0 auto merge / 0 auto hide / 0 delete**。後續 P30-L7 隔離 fresh JSON / P30-L8 新資料 Android UAT，正式 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`、Android 44 UAT、正式 PWA、服務與 Writer 全程維持原狀，PR #32 和治理 PR #8 Draft 未合併。
>


> **2026-10-26 P30-L5-E StrollTimes source section graph and BItan organiser government first-party evidence**
>
> - Source Draft [PR #30](https://github.com/easonliu714/event_scraper_public/pull/30) from PR #29 `f960d0bd91d4ca38df17f0ecb2c053fd7a0299f6`: 3 new files `scripts/p30_l5e_strolltimes_source_lineage.mjs`, `tests/p30/test_l5e_strolltimes_source_lineage.mjs`, `.github/workflows/eventradar_p30_l5e_strolltimes_lineage.yml`. Stage DIL/source schema `StrollTimes homepage candidate {title,aggregatorUrl,originalOfficialUrl:null}` → (bound detail `H1`) → explicit `資料來源` H2/H3 header-to-next-header hyperlink region → `credits[]:{url,anchorLabel,sourceSection:"資料來源",role,linkedEventTitleIndependentlyMatched:false,organiserAccountAuthenticityVerified:false,originalOfficialEventDetailVerified:false}`; Google map `VENUE_MAP_NOT_EVENT_SOURCE`, Facebook `ATTRIBUTED_SOCIAL_POST_ACCOUNT_NOT_VERIFIED`, official ticket site `TICKET_SITE_EVENT_IDENTITY_NOT_VERIFIED`, .gov.tw `GOV_INSTITUTION_WEBSITE_EVENT_IDENTITY_NOT_VERIFIED`, unknown exterior `OTHER_REFERENCED_WEBSITE_IDENTITY_NOT_VERIFIED`. Only credits section, never arbitrary navigation/social/maps links. Browser only visits StrollTimes pages (1 homepage + six article), no external source follows; false article H1 matches do not collect sources. CI [40314650154](https://github.com/easonliu714/event_scraper_public/actions/runs/40314650154) PASS 23/23 tests, 24 list, 6 HTTP200 details, 2 exact H1, 3 attributable Facebook URLs; four parent-/child-article H1 identity HOLD; Artifact 12645714192 digest `sha256:aeb7d368f20924e9025e49e0bed631c570410b8228e2e83ede047c1ebf02c65e`. PR #30 HEAD `ae2c2bdd014fdb9df2cb7d05781d6347d92848b5`; previous first run CI FAIL due strict 6/6 H1 and earlier budget, preserving historical failures.
> - Source Draft [PR #31](https://github.com/easonliu714/event_scraper_public/pull/31) from PR #30: 3 new files `scripts/p30_l5e2_bitan_government.py`, `tests/p30/test_l5e2_bitan_government.py`, `.github/workflows/eventradar_p30_l5e2_bitan_gov.yml`. Isolated `E1 lineage_evidence.json` (pinned SHA via GitHub Actions Run 40314650154) → exact StrollTimes BItan aggregator article `/events/new-taipei/261016084730/` H1 identity → government first-party [calendar](https://newtaipei.travel/zh-tw/calendar/detail/4058) + official [municipal newsroom](https://www.ntpc.gov.tw/ch/home.jsp?dataserno=66daa0e44fad9dd95b5b7e5ece1bf28d&id=e8ca970cde5c00e1), each limited one HTML HTTP request, same official event date/location/organizer. `independent_gov_event_review.json` stores `{reviewOnlyOfficialEventUrl, reviewOnlyOfficialEventPeriod:["2026-10-17","2026-12-13"], primaryOfficialCalendar:{identity:"OFFICIAL_EVENT_TITLE_BOUND",dateRole:"OFFICIAL_ORGANISER_EVENT_PERIOD",organiser:"新北市政府觀光旅遊局",venueEvidence:"新北市新店區碧潭風景區",completeIdentity:true},secondaryGovernmentNews:{publishedAtDate:"2026-10-14",dateRole:"NEWS_PUBLICATION_DATE_NOT_EVENT_START"},officialFirstPartyIndependentEventIdentityCount:1,strolltimesOriginalFacebookCreditsUnverified:true,allOtherAggregatorArticlesVerified:false,finalDatePromotionCount:0,dateStart:null,dateEnd:null,ticketStatus:"UNKNOWN",price:null,goldenAccepted:false,published:false,writerExecuted:false}`. Government news publication is NOT an event date.
> - Final native [CI 40315847664](https://github.com/easonliu714/event_scraper_public/actions/runs/40315847664) completed/success, 20/20 offline, E1 Artifact manifest, GET 200/200 original govt source, exact city venue and organiser, bounded multi-source calendar date, all original Pages runtime blob identities, SHA [Artifact 12646961925](https://github.com/easonliu714/event_scraper_public/actions/runs/40315847664/artifacts/12646961925) digest `sha256:a5c34c0fefce372cede0ac2c0e5e9d3b3b107d5073f9b880c86de9d57ff3aad6` PASS. Source PR #31 HEAD `f0b07bf4ad45ed9e833d6825c4c119097c698694`; Source main `fc4f963247d68eed29425808cc14e7250f312d05` and 44 accepted Android records remain unchanged. First-party identity success is only **one specific BItan article**; remaining 23 source identities and 4 sampled H1 nonexact are HOLD; no official JSON writer, notifications, scheduler, repo retirement, automatic consolidation.
> - Next architecture implementation: `P30-L5-E3` source-link to official detail same-event proof with identity/dateRole/organiser role and explicit `parent_event` vs `subevent` edges for aggregator title variants; `P30-L6 G5J` reversible dedup/classification, `P30-L7` isolated new JSON, `P30-L8 G5K` Android PWA real-candidate smoke. Do not turn a source-credited Facebook post into verified organiser account, or a calendar post date into official activity period.
>


> **2026-10-26 P30-L5-D1 FamiTicket four public detail samples and emoji-labelled TPBL roles architecture**
>
> - Source [Draft PR #29](https://github.com/easonliu714/event_scraper_public/pull/29)：`scripts/p30_l5d_famiticket_field_roles.mjs`（獨立公開 Chromium readonly）、`tests/p30/test_l5d_famiticket_field_roles.mjs`（27 positive-negative fixtures）、`.github/workflows/eventradar_p30_l5d_famiticket_fields.yml`（native scoped CI，精確三新檔、Parent PR #28 frozen SHA、正式 Blob Guard）。`findDetailCards()` 比較首頁 heading/alt/title/anchor-text 對官方 `/Home/Activity/Info/<opaque-id>` 一對一 URL，最先必須找到唯一精確的 2026 ITF，再取最多 3 個其他不同活動。首頁 + 4 詳情共至多 5 次導覽／160 ibon 以外的 FamiTicket/CDN 核准請求上限，禁止其他 Host、登入、購票、非公開 API、CAPTCHA 繞過、PWA 或 Data Writer。
> - `roleFields()` 只採用官方詳情 DOM 上明確 `label：value` 或 **下一行**的白名單角色，emoji `🔱`／`🌊` 項目要保留 label role；四位數西元年合法日期 token、有完整日數邊界（19 不能截成 1；20 不能截成 02），禁止由 title 年份、系列「26-27」與「10/8」月日片段猜測活動日期。新 taxonomy：`EVENT_TIME_LABEL_ONLY`、`VENUE_LABEL_ONLY`、`SERIES_DESCRIPTOR_NOT_EVENT_TIME`、`ADMISSION_NOT_EVENT_START`、`SALE_WINDOW_NOT_EVENT`、`REGISTRATION_WINDOW_NOT_EVENT`、`VOUCHER_VALIDITY_NOT_EVENT`、`VOUCHER_REDEMPTION_LOCATION_NOT_EVENT_VENUE`。僅輸出 `LABELED_RAW_EVIDENCE_UNPROMOTED` 和 bounded excerpt，部分欄位未出現保持 UNKNOWN/HOLD。
> - `role_evidence.json.detailSamples[]` 為 `{listTitle,officialUrl,detailHttp,observedUrl,identity,fields[],fieldHintLines[],structuredFieldPairs[],dateStart:null,dateEnd:null,venue:null,ticketStatus:"UNKNOWN",price:null,category:"待分類",fieldPromotionCount:0,goldenVerified:false,published:false}`。必須清單/detail exact title 才允許擷取欄位 raw evidence，所有 field `officialEventDateAccepted=false`；頁面購票鈕、票券有效/兌換、銷售期間不是實時售票狀態或展覽/比賽日。
> - 實測 [GitHub Actions Run 40312137162](https://github.com/easonliu714/event_scraper_public/actions/runs/40312137162) completed/success：FamiTicket 官網首頁 HTTPS200、**4/4 different actual detail HTTP200、4/4 exact title**（ITF、臺中市美術館典藏展、駁二動漫祭、高雄全家海神主場）。TPBL 官方「🔱比賽地點／🔱開放場次／🔱預售票全面販售時間」得到三種分離 role，另三筆展覽/動漫詳情此抽樣未取得安全可解析的真正展期，不能硬補。27/27 tests/官方 production SHA/manifest PASS，Artifact [12643879532](https://github.com/easonliu714/event_scraper_public/actions/runs/40312137162/artifacts/12643879532) digest `sha256:3489998d4869e979f9e7496f3abfa2ada17b4dc8369437b813950993b3635563`。PR #29 HEAD `f960d0bd91d4ca38df17f0ecb2c053fd7a0299f6`；Source `main@fc4f963247d68eed29425808cc14e7250f312d05`／已驗證 Android 44/正式 JSON/正式 PWA 不動。
> - 依系統層次接續 `P30-L5-E StrollTimes aggregator first-party source lineage` → `P30-L6 G5J conservative reversible category/dedup` → `P30-L7 new isolated candidate JSON` → `P30-L8 G5K Android/PWA smoke/UAT`；未完成原始來源的 StrollTimes 頁面和缺展期的 FamiTicket 詳情只顯示官方連結／未知欄位，絕不憑「購票須知」推論最新售票狀態。
>


> **2026-10-26 P30-L5-C producer tour independent source lineage and sale timestamp HOLD architecture**
>
> - SRC [Draft PR #28](https://github.com/easonliu714/event_scraper_public/pull/28) `scripts/p30_l5c_nier_producer_lineage.py` 為獨立 readonly Python `requests + BeautifulSoup` source provenance Gate，先要求 Source parent `kind=EVENTRADAR_P30_L5B_IBON_CHANGE_NOTICE_CROSSCHECK_NOT_GOLDEN`、2 官方 numeric-ID、NieR `ActivityInfo/Details/39974`、`2027-02-20T18:00`／`2027-02-21T14:00` 精確來源場次、原 `notice.isNoChangesProven=false`、DORMANT/zero writer，再限定 HTTPS `www.nierconcert.com/12026`、`www.nierconcert.com/12026/taipei-2` 與二手轉售資料 `itix2go.com/guest/program/detail/ncrp0` 各最多一次 GET，禁 redirects/foreign/private APIs、限制 response content type/size、網路失敗不 retry。三類角色 `PRODUCER_TOUR_LIST`、`PRODUCER_EVENT_DETAIL`、`THIRD_PARTY_TICKET_RESALE_LISTING` 嚴格分開，不能把二手平台的售票時間升級為 organiser 政策。
> - `producer_schedule()` 以**同一 Taipei, Taiwan 區塊**、英文完整年月日與 6PM/2PM、TICC venue 檢查原始製作方兩個場次，排除 Bangkok、其他城市/同 venue 偽陽性。`producer_added_event()` 驗 2/21 第一手活動頁的相同城市/日期/時間/場館/NieR title，並把 `announcementPublishedAt=null` 和 `announcementPublishTimeVerified=false` 設為硬契約；節目表上有新增場次，不代表已找到「加演公告初次發布的時間戳」。
> - `secondary_sale()` 對 `itix2go.com` 只保留 `THIRD_PARTY_TICKET_RESALE_LISTING` 銷售整理角色，本次從 UTF-8 byte-decoded HTML 抽到 `2026-10-21T12:00` 加場售票整理文字；目前 producer live `On Sale Oct 21 09:00 UTC+8` 文字未在 GitHub Runner 現行頁面被抽取，屬 `NO_COMPARABLE_SALE_TIMES_OBSERVED`，不得宣稱現行 09 vs 12 已確認衝突或售票中。外部摘要先前曾顯示 09AM，不等於正式現在回應。票務／有效期／報名日期仍不能替代活動時間。
> - 下游 `cross_source_review.json` 以 `status=PRODUCER_TWO_TAIPEI_SESSIONS_CORROBORATED_REVIEW_ONLY`、`producerOriginalTwoStartsSame=true`、`producerSessionCount=2`、`announcementPublicationTimestamp=null`、`additionalShowAnnouncementIndependentlyVerified=false`、`organiserChangeApproval=NOT_VERIFIED`、`dateStart/dateEnd=null`、`ticketStatus=UNKNOWN`、`price=null`、`formalFieldPromotionCount=0`、`goldenAccepted=false`、`published=false` 輸出。即使兩個 show dates 由 original producer 官網確認，也先保留在 isolation／可逆證據，不動 Android 已驗收 44 筆及正式 Pages。
> - Native CI [Run 40305582187](https://github.com/easonliu714/event_scraper_public/actions/runs/40305582187) Success、20/20 offline origin and fake-event tests、frozen PR #27 Head `bd0612ee49d992cd0c4c8843ba6b0a09dd39f90d`、精確三新增檔 `scripts/p30_l5c_nier_producer_lineage.py`、`tests/p30/test_l5c_nier_producer_lineage.py`、`.github/workflows/eventradar_p30_l5c_nier_producer.yml`、前 Gate Artifact SHA、3 個 public HTTP200、producer 2/2 Taipei start crosscheck、isolated [Artifact 12642720340](https://github.com/easonliu714/event_scraper_public/actions/runs/40305582187/artifacts/12642720340) digest `sha256:d9456d4f9aab96c80d11a75a68c4b25a6a3be2758e245eb8dd5b16cee8050360` 皆 PASS。PR #28 HEAD `16bb4bda029e8eee3951396d9031aac14576ad74`；正式 Source `main@fc4f963247d68eed29425808cc14e7250f312d05`、`docs/data.json`、`docs/index.html`、`scraper.py` 不動。下一功能 P30-L5-D FamiTicket small sample official field roles + NieR timestamp evidence HOLD / StrollTimes first-party lineage，再接 L6 可逆去重、L7 fresh candidate、L8 Android E2E。
>


> **2026-10-26 P30-L5-B ibon change notice source-bound review-only architecture**
>
> - 在 Source [Draft PR #27](https://github.com/easonliu714/event_scraper_public/pull/27) 新增 `scripts/p30_l5b_ibon_change_notice.mjs`（公共官網 2 detail bounded Chromium/readonly）、`tests/p30/test_l5b_ibon_change_notice.mjs`（20 positive/negative）、`.github/workflows/eventradar_p30_l5b_ibon_notices.yml`（native pinned CI）。基於既有 PR #26 L5A 實際回應 Run `40301911354` Artifact SHA manifest；驗證上游 `kind=EVENTRADAR_P30_L5A_IBON_SESSION_ROLE_REVIEW_ONLY`、2 個來源 URL/標題、3 個 `eventStartLocal`、sourceRuntime DORMANT 和零正式日期／票價／售票／Golden promotion。不同 URL、HTTP403、非原標題或跨平台站點都 fail-closed。
> - 資料路徑：`L5A session_candidates.json` → `P30-L5B pinned-parent SHA` → official bounded `ActivityInfo/Details/<numericId>` × 2 → `scheduleBlockEvidence()`／`decodeActivityBlock()` 對照 3 個開演時間 → `scopedNotice()` 對明確 `最新演出相關資訊／公告` 及其他合法 heading 區塊擷取 → `change_notice_review.json`。不探查私人 API／購票、正式 JSON/DB/PWA、排程或通知，所有輸出 isolating SHA archive only。
> - 每筆 `details[]`：`{officialUrl,listTitle,httpStatus,scheduleParity,originalSampleEventStarts,currentSampleEventStarts,timezoneStillUnprovenForSomeSessions,notice:{state,sections,signals,isNoChangesProven:false},scheduleInlineAdditionEvidence,organiserChangeApproval:"NOT_VERIFIED",liveTicketAvailability:"UNKNOWN",dateStart:null,dateEnd:null,ticketStatus:"UNKNOWN",price:null,goldenVerified:false,published:false}`。Notice taxonomy：`EVENT_CANCELLATION_SIGNAL_REVIEW`、`EVENT_POSTPONEMENT_SIGNAL_REVIEW`、`ADDITIONAL_SESSION_SIGNAL_REVIEW`、`SALE_CHANGE_ONLY_NOT_EVENT_TIME`、`AMBIGUOUS_CHANGE_WORD_HOLD`；**公告缺失 ≠ NO_CHANGE_PROVEN**；時間段「追加場」只能是 `ADDITIONAL_SESSION_MARKER_IN_SCHEDULE_NOT_AN_INDEPENDENT_CHANGE_NOTICE`，不直接取得主辦認可；任何變更旗標都不得自動更改票況、延期或上下架。
> - GitHub [Run 40303622151](https://github.com/easonliu714/event_scraper_public/actions/runs/40303622151) 20/20 offline negative PASS、2/2 exact ibon official HTTP200、3/3 時間與 L5A 抽樣 parity PASS、RUNIDRE limited notice unknown、NieR `ADDITIONAL_SESSION_SIGNAL_REVIEW` → organiser follow-up HOLD、SHA Artifact `12640444559`（digest `sha256:c1863e7c3024f6b6e329bdce71206ec931bf3d8077c6ee69d256e62e9082a7da`）PASS。Source PR #27 HEAD `bd0612ee49d992cd0c4c8843ba6b0a09dd39f90d`、Source main `fc4f963247d68eed29425808cc14e7250f312d05` 不動；原 Android 44 user-attested PASS 及正式 PWA/JSON/RUNTIME unchanged。
> - 下個 `P30-L5-C` 專注辦理單位官方 change-notice source identity / publication timestamp / additional-session effective date / change resolution，保留未知時區不猜，無證據一律 HOLD。FamiTicket 需擴展官方 detail role QA；StrollTimes 必須追到第一手主辦者再分層，不得直接 Golden。經 L6/L7 隔離候選整併後，才提供新的 Android L8 實機包。
>


> **2026-10-26 P30-L5-A ibon explicit event start versus admission role evidence architecture**
>
> - Source 新 [Draft PR #26](https://github.com/easonliu714/event_scraper_public/pull/26)，基於 P30-L4-D3 PR #25 frozen HEAD `622a52221d6fded07d0829486f3877835e372da40`，**只新增** `scripts/p30_l5a_ibon_session_roles.mjs`、`tests/p30/test_l5a_ibon_session_roles.mjs`、`.github/workflows/eventradar_p30_l5a_ibon_sessions.yml`。Node 純離線轉換 `L4D2 diagnostics.json`（CI 內先用既有公眾 ibon official Chromium 1 list + 2 detail bounded fetch），強制檢查來源 `kind`、`OFFICIAL_TICKET_PLATFORM`、HTTP200、同源 numeric-ID URL `requestedOfficialUrl===responseUrl`、兩筆 exact heading、上游 `RAW_UNPROMOTED_EVIDENCE`/observed full-year date parity、DORMANT/未發布／零 Golden／零 notifier/writer；只輸出 review-only `session_candidates.json`。
> - `samples[].proposedSessions[]` 結構：`{eventDate,eventStartLocal,admissionStartLocal,sourceTimeZone,sourceTimeZoneStatus,dateRole:"OFFICIAL_DETAIL_EVENT_START_CANDIDATE",admissionRole:"OFFICIAL_DETAIL_ADMISSION_TIME_CANDIDATE",admissionIsNotEventStart:true,proposedOnly:true,verifiedAgainstOrganiser:false,verifiedAgainstChangeNotices:false,approvalState:"REQUIRES_L5_CROSS_EVIDENCE_REVIEW"}`。這與 `samples[].dateStart=null,dateEnd=null,saleWindow=null,registrationWindow=null,voucherValidity=null,ticketStatus="UNKNOWN",price=null,goldenVerified=false` 分層，任何 source `入場時間` 不得成為開演時間、來源售票/報名/使用期限不可成為活動期間。
> - 日期解析限 YYYY 年完整數字，月/日長 token 優先、真實西元曆驗證、官方括號星期標記相符、原文取消/改期/延期標記 fail-closed，同場入場不得晚於開演（跨午夜除非明確證據）、同活動場次不能重複。Taiwan zone 只允許當活動時間 block 本身標註 `台灣時間`：一筆 RUNIDRE `2026-12-19 16:00/17:00` 標示 Asia/Taipei，NieR 二場 `2027-02-20 17:00/18:00` 及 `2027-02-21 13:00/14:00` 因擷取文字未明確時區，皆 `sourceTimeZone=null`。時間僅為同頁原文語義證據，**尚未查驗後續官方延期/主辦異動**。
> - 最終 native [CI 40301911354](https://github.com/easonliu714/event_scraper_public/actions/runs/40301911354) completed/success：22/22 parser/provenance/negative tests、ibon list 23／real details 2／true event-start candidates 3／admission-time candidates 3／explicit timezone only one／SHA archive [12640209144](https://github.com/easonliu714/event_scraper_public/actions/runs/40301911354/artifacts/12640209144) PASS。PR #26 HEAD `b7e16cb39fc187cea927cf1521ee972d621f8a2a`，Source main `fc4f963247d68eed29425808cc14e7250f312d05` unchanged, 44 accepted Android events/正式 Pages/JSON unchanged。下階段 L5-B 變更公告 lineage 和場次 role → L6 跨來源去重 → L7 isolated fresh JSON → L8 Android UAT；StrollTimes third-party aggregator NOT_GOLDEN / FamiTicket 0/2 raw title hold + 1/1 public Chromium exact title preserved。
>


> **2026-10-26 P30-L4-D3 FamiTicket official rendered detail exact image-alt identity**
>
> - 新 Source [Draft PR #25](https://github.com/easonliu714/event_scraper_public/pull/25) `scripts/p30_l4d3_famiticket_browser.mjs` 以 Chrome/Playwright 原生 public browser 只開 `https://www.famiticket.com.tw/Home` 一次並限同站 opaque-ID `/Home/Activity/Info/<id>` detail 一次，不使用登入、購票、stealth、繞過驗證碼、非公開 API 或任意外網轉址。清單 DOM 231 anchors；同標題「2026 ITF 台灣國際旅展」在 `img alt`，分類 `textContent` 有時是「展覽」。四種可見標題欄位各自做 **exact title equality**，以 URL 去重後必須只有一個活動 ID；不能因標題相似而合併不同活動。詳細頁 Chromium HTTP 200、H1/H2/H3/H4 取得唯一相符標題，與純 requests 之前連續兩次 200 卻無標題的變異分別記錄，不能直接宣稱 47 筆品質全證實。
> - Source PR #25 final `622a5221d6fded07d0829486f3877835e372da40`；native [CI Run 40299649653](https://github.com/easonliu714/event_scraper_public/actions/runs/40299649653) Success、16/16 offline guard tests、parent Source PR #24 frozen SHA、正式 `docs/data.json`/`docs/index.html`/`scraper.py` blob identity、三新增檔路徑精確、real public HTTP + exact title、diagnostic/SHA PASS。Artifact 12639478214。新 `detail` 診斷欄位 `eventDateStart=null,eventDateEnd=null,price=null,ticketStatus=UNKNOWN,fieldPromotion=0,goldenVerified=false`，即使詳情標題可見也絕不推測活動日期/票務。
> - 下個 Source 層 L5：FamiTicket 進一步有限抽樣官方詳情中有角色標籤的時間／場地／票券期限，ibon 目前 2 件標準官方 DOM 取得的 event-time blocks 規範化並與開場時間/多場次/售票時間分離，StrollTimes `sourceRole=THIRD_PARTY_EVENT_AGGREGATOR` 維持無原官方證據不進 Golden。原 44 Android UAT 不變、Source `main@fc4f963247d68eed29425808cc14e7250f312d05` 未動，未開啟正式 PWA/Writer/通知/排程。
>


> **2026-10-26 P30-L4-D1 / L4-D2 official detail role and stability architecture**
>
> - 新 Source [PR #23](https://github.com/easonliu714/event_scraper_public/pull/23) `scripts/p30_l4d1_famiticket_detail_roles.py`：匯入已驗證 `p30_l3b_a_famiticket.py` 限定 HTTPS list/detail 函式，單次首頁 JSON 標題／opaque URL 身分綁定，分隔兩次 public official detail GET。每次保存 HTTPS status、SHA256/byte、headings exact identity、明確標籤角色 `EVENT_OCCURRENCE_EVIDENCE` vs `SALE_WINDOW_NOT_EVENT`／`REGISTRATION_WINDOW_NOT_EVENT`／`VOUCHER_VALIDITY_NOT_EVENT`；嚴格四位西元年與合法日期，所有解析結果僅 `UNPROMOTED_ROLE_ONLY`。CI 40297130466 19/19 offline PASS，首頁 47、兩次詳情 HTTP200 但皆無標題，**資料品質必須 HOLD**（非平台無活動或付款狀態）。`docs/data.json`、`docs/index.html`、`scraper.py` 仍 immutable。
> - 新 Source [PR #24](https://github.com/easonliu714/event_scraper_public/pull/24) `scripts/p30_l4d2_ibon_detail_roles.mjs` 匯入既有 `p30_l3bb_ibon_browser.mjs` 官方 domain/URL/link identity，使用 stock Chromium 渲染清單並只開 **2 筆清單出現過且 numeric ID 唯一**的 ibon 官方頁。DOM `h1/h2/h3` 精確相符才取 `roleEvidence` 與 `scheduleBlockEvidence[]`，雙型態 `【活動時間（台灣時間）】` 後相鄰欄位、`日期/時間｜YYYY.MM.DD HH:MM …`；僅有原始 `observedFullYearDates`／`rawExcerpt`，禁止將 `售票時間`、`使用期限` 或一般敘述數字推定為活動日期。**JS `fullDate` regex 已加 (?!\d) 防止 19→1、20→02 的前綴誤讀**，以 19 個 offline tests 封鎖回歸。兩筆正式 HTTP200／2/2 exact 標題、帶標籤 event-time 分別有 2026-12-19 和 2027-02-20/21 原始日期證據：最後 CI [40298499664](https://github.com/easonliu714/event_scraper_public/actions/runs/40298499664) PASS；Artifact 12638968553。
> - schema `sample_candidates.json` 仍為 `{platform,title,officialUrl,dateStart:null,dateEnd:null,dateRole:"UNKNOWN",price:null,ticketStatus:"UNKNOWN",detailIdentity:"EXACT_LIST_DETAIL_HEADING",eventTimeVerified:false,goldenVerified:false,published:false}`；`diagnostics.json` 可有帶標籤的 `scheduleBlockEvidence`，但**診斷 evidence 不等於 accepted event schedule**，尚無欄位升級。所有新 Gate scope 僅新增 source/test/workflow 3 檔，Source main `fc4f963247d68eed29425808cc14e7250f312d05` 及 Android 44 PASS、StrollTimes aggregator originalOfficialUrl=NULL 不動。資料作業寫入、通知、排程及正式 PWA 上線仍 LOCKED。
> - 下個可實作：`P30-L4-D3` FamiTicket public browser detail identity recovery，再依 `P30-L5-B` ibon annotated date/registration/sale/timezone/session consolidation 和 `P30-L6` source lineage + conservative G5J 去重，最後 `P30-L7/8` isolated fresh JSON + Android smoke。不得重跑已驗收 CKSMH/TWTC 的 44 Android UAT，除非新候選確有合併和回歸必要。
>


> **2026-10-26 P30-L3-B-C StrollTimes third-party sourceRole tree**
>
> - SRC `scripts/p30_l3bc_strolltimes.mjs`（Source [Draft PR #22](https://github.com/easonliu714/event_scraper_public/pull/22)）獨立 public Chromium 1x homepage `https://strolltimes.com/` + 1x same-host `/events/<city>/<12–18-digit-id>/` article；HTTPS exact hosts、limited CDN、only 100 allowed requests、no stealth/login/verification bypass/purchase/API guessing/persisted session. `tests/p30/test_l3bc_strolltimes.mjs` 11 cases for URI/CTA/role/title/provenance. CI `.github/workflows/eventradar_p30_l3bc_strolltimes.yml` GitHub-specific immutable three-file diff and production blobs; **never changes `docs/data.json`**.
> - Immutable candidate schema sample: `{ platform: "StrollTimes", title, aggregatorUrl, originalOfficialUrl: null, originalOfficialIdentityState: "NOT_VERIFIED", sourceRole: "THIRD_PARTY_EVENT_AGGREGATOR", sourceLevel: "AGGREGATOR_LIST_IDENTITY_ONLY", dateStart: null, dateEnd: null, dateRole: "UNKNOWN_NEEDS_ORGANISER_VERIFICATION", price: null, ticketStatus: "UNKNOWN", classification: "待分類", goldenVerified: false, published: false }`. **Aggregator `aggregatorUrl` != primary official URL**；其他平台不能因標題相似就自動複製日期或提升 Golden/售票狀態。
> - Article identity: StrollTimes homepage `2026新竹市萬聖節` / same-site article H1 `2026新竹市萬聖節（10/16~10/31）`。僅允許有錨定的末尾純 `(MM/DD～MM/DD)` 展示標記，不能將標記當作官方展期，也不能使用一般 fuzzy title 對兩篇無關文章認列相同 ID。原主辦官方來源欄位保持 **NULL/HOLD**，L4-L6 才能來源對照。
> - Native [Run 40295191261](https://github.com/easonliu714/event_scraper_public/actions/runs/40295191261) 11/11 offline PASS、rendered 113 anchor /24 unique aggregator articles/1 sample detail same-site title+HTTP200 PASS、original primary authority count=0。Artifact `12638155320`, SHA manifest PASS，PR #22 HEAD `e7e13c845d042b4a0b13cc98bdd51ba03d836fa8`；JS asset-block pageerrors=24 應列診斷監控、不當作官方資料。Repo main `fc4f963247d68eed29425808cc14e7250f312d05`、44 Android accepted data、FamiTicket 47、ibon 23 previous branches unchanged。Next `P30-L4/L5` lineaged first-party evidence, classification G5J and Android G5K only once candidate is usable。
>


> **2026-10-26 P30-L3-B-B ibon headless JS display-only list 23（Source Draft PR #20/21）**
>
> - `scripts/p30_l3bb_ibon.py`（PR #20）安全純 HTTP 雙官方清單入口 → requests GET 200/200、固定 5,766 bytes JS shell，`<script>` 11、DOM link 0、visible text 8；13/13 offline tests PASS，但抽不到可驗證活動，該純 HTTP Gate **HOLD**，不嘗試非公開 API、登入或驗證碼繞過。原 Source `docs/data.json` 不變。
> - `scripts/p30_l3bb_ibon_browser.mjs`（PR #21）為獨立的 **readonly Chromium one-page public browser rendering diagnostic**：只開 `https://ticket.ibon.com.tw/Index/entertainment`，無 stealth/代理繞過/購票/登入/憑證/Service Worker，限制 ibon HTTPS host、單次導航／90 網路請求上限、最多 80 候選，封鎖第三方及圖片/字型。公眾頁面渲染得到 DOM 70 anchors，萃取 `/ActivityInfo/Details/<numericId>` 並以 hostname+path+title 嚴格 identity（含 URL alias `/Web/`、`/WebV3/`），本次 23 unique candidates。
> - JSON 候選欄位仍為 `platform=ibon`、`title`、`officialUrl`、`dateStart/dateEnd=NULL`、`dateRole=UNKNOWN`、`ticketStatus=UNKNOWN`、`price=NULL`、`category=待分類`、`classificationEvidence=UNVERIFIED`、`detailStatus=NOT_CHECKED`、`goldenVerified=false`。不得因官網顯示「售票中／即將開賣」標籤便推定正式票況。此 browser **沒有點入詳情**，L4/L5 顯示待驗證而非 FAIL 或 Golden。
> - Native CI [40292155453](https://github.com/easonliu714/event_scraper_public/actions/runs/40292155453) `completed/success`、7/7 Offline security、Source main Blob Guard、23 HTTP asset requests、4 external blocked、41 passive resources skipped、0 JS errors、isolated candidate/diagnostics/SHA artifact `12635589126`。PR #20/21 均 Draft stacked；正式 Pages/UI, Android accepted 44, runtime scheduler, notifications, GitHub main HEAD `fc4f963247d68eed29425808cc14e7250f312d05` untouched。下一為 StrollTimes L3-B-C + L4/L5 來源詳情補強後，才有理由重建新 Android 來源整併候選。
>


> **2026-10-26 P30-L3-B-A FamiTicket isolated official list recovery source module**
>
> - 確認 P30-L4-C Android local `8770` 使用者截圖驗收 PASS（限來源日期角色/場地/清單/詳情/不回歸），不重新開始 L4-B/C 來源開發。新增 FamiTicket SRC[PR #19](https://github.com/easonliu714/event_scraper_public/pull/19)，分支堆疊 PR #18 `2656c43fc1fa4486fcbd8be641531e4d15220104`，三個新增檔案**無 UI/Android/formal docs 改動**。
> - `scripts/p30_l3b_a_famiticket.py` 的 `allowed/canonical/fetch` 只接受 `https://www.famiticket.com.tw/Home` 與固定 same-host `/Home/Activity/Info/<opaque-id>`；最多 1 listing + 1 sampled detail；TLS/HTTP 200、Content-Type、SHA256、HTML body 限 2 MB、無 GET retry/登入/購票流程。卡片解析優先 heading、去重 unique detail URL，保留 title、official_url、rawScheduleText、`rawScheduleRole=UNCLASSIFIED_LISTING_TEXT`；尚未證實日期/票價/票況/分類，全部 UNKNOWN/NULL/待分類。
> - 同一 ITF 已被觀察到 GitHub Runner 連續樣本變動：實際清單始終 HTTP200 並產 47 unique rows，但詳情有時包含 `h2` 精確標題，有時 200 HTML 無 heading；這屬 `DETAIL_TITLE_CONTENT_INTERMITTENT_HOLD`，不誤認為整個清單恢復失敗或整批詳情 Golden。最終 CI [Run 40289865032](https://github.com/easonliu714/event_scraper_public/actions/runs/40289865032) Success、12/12 offline、47 LIST、1 正確 detail identity、SHA manifest PASS；Artifact 12636240385；PR #19 HEAD `17acb05b8da6066883113e91d68e852ba3db080f`。
> - 尚未串接 `docs/data.json` 或已驗收 44 Android rows，正式 PWA/Web/UI 的 FamiTicket 新平台維持 **NOT_DEPLOYED**。L3-B-B ibon、L3-B-C StrollTimes = OPEN；需要更完整詳情來源與欄位語義、活動身份和跨平台重複確認才可產 Android 新候選。
>


> **2026-10-26 P30-L4-C CKSMH EVENT_SESSION versus REGISTRATION_WINDOW semantic model**
>
> - P30-L4-B Android 真機部分 PASS，但多場次時間來源角色錯誤：官方 `場次：` 標題明確列 *活動實際時間*，其下 `報 名 期 間` 為 **REGISTER WINDOW**。L4-C 新讀取層先以固定 5 筆 HTTPS actId/標題驗證，再按個別 `場次：` 區塊截斷 `報名期間`；標題內接受 `YYYY/MM/DD (星期) HHmm-HHmm` 或 `YYYY/MM/DD HH:MM～YYYY/MM/DD HH:MM`，不允許以未標記長區間冒充場次。有活動日期卻含多個未命名日期時 fail-closed，不推測。「自由花蕊」名稱不可混淆不同 actId（61021 為系列講座、51331 為免費參觀常設展）。
> - 新候選欄位 `sessions[].{start,end,venue,role=OFFICIAL_EVENT_SESSION_TIME,registration}` + `registrationWindows[].{start,end,role=OFFICIAL_REGISTRATION_WINDOW}` + `timeRole=OFFICIAL_EVENT_SESSION_BOUNDS`；`dateStart/dateEnd` 僅代表有證據的**活動場次涵蓋日期**。對常設展 actId 51331，`listPeriodStart/End` 保留 2025/11/24～2030/12/31，`timeRole=OFFICIAL_LIST_PERIOD_UNCLASSIFIED`，`dateStart/End=NULL`，UI 說明「官方清單所列期間／非每日場次，實際開放以官方為準」，不得自行寫成報名或每日場次。
> - Android `scripts/p30_l7a_smoke_index.html` 結構不增加權限：列表「活動場次：日期範圍（非報名期間）」、modal 每場顯示活動時間、個別場地、報名開始結束並註明「非活動時間」，清單期間單獨呈現。仍只使用 `textContent` 避免 XSS。平台其他 39 TWTC rows 位元級相同；FinTech 原訂／暫定／confirmed NULL 不變。沒有 PWA Scope/Service Worker、Golden、票況可信資料或正式 JSON 發布。
> - [Draft PR #18](https://github.com/easonliu714/event_scraper_public/pull/18) HEAD `2656c43fc1fa4486fcbd8be641531e4d15220104`，CI [40287542387](https://github.com/easonliu714/event_scraper_public/actions/runs/40287542387) completed/success：12/12 tests、5 HTTP 200、10 real event sessions、8 registration windows，actId 51331 long listing interval separate、Android local Artifact `12634941609` SHA256 manifest PASS，port 8770 真機待使用者驗收。全 Repo `docs/data.json`／`scraper.py`／`docs/index.html` 保持原 Blob，PR #8 文件更新只在治理分支。
>


> **2026-10-26 P30-L4-B 最終清單與場次時態 UI 保護**
>
> - CKSMH `OFFICIAL_LIST_ACTID_BOUND_DATE_RANGE` 改成 UI 明確「官方清單期間」而非無條件活動場次，`OFFICIAL_MULTIPLE_SESSIONS_BOUNDS` 顯示涵蓋日期並展開獨立 sessions（非每日舉辦），多場次無唯一場地保留 `venueNote`。CKSMH source role 轉繁體中文可理解標示。
> - PR #17 HEAD `d79de853c007ac965d02b56cc2e556f8ad5f1bff`。最終 CI Run `40285154986` completed/success，14/14 test + JS + 五件詳情/清單綁定 + 44 Id／39 TWTC immutable + SHA 4/4。**Android 最終 Artifact 12633104025**，舊 12633399655 只保留歷史；Android 實機未 PASS 前保持 `WAITING_USER`。不寫 formal Pages，不發通知，不更動 G5J/G5K 或 Golden。
>


> **2026-10-26 P30-L4-B CKSMH 活動詳情場次來源分欄（PR #17 Draft，Android 8769 待回報）**
>
> - `scripts/p30_l4b_cksmh_details.py` 使用已驗證 L7-D 44 rows 的五個 CKSMH 官方活動 actId URL，逐一 HTTPS GET (5)，另對官方 `Query.list.ctr` GET (1)；嚴格 TLS、限定 `event.culture.tw` 官方 actId 路徑、同 ID redirect、HTML byte budget、無重試。優先以詳情 top title 精確匹配（僅移除尾端「圖片說明」alt）、`場次資料` 區取得毫秒以下的 YYYY/MM/DD HH:MM 開始/結束，保留獨立 `sessions[]`（多場次不可當作每日連續開放），單場地僅在 Google Map 官方 anchor 唯一時成立，`活動內容介紹` 區取得最長 360 字摘要；缺值保留未知。
> - 對 actId 51331「自由花蕊」之詳情**未提供活動場次日期**，獨立允許官方清單 `/mocweb/reg/CKSMH/Query.list.ctr` 同一 `actId+title` 之活動卡片 `活動時間` 2025/11/24～2030/12/31，回填 `timeRole=OFFICIAL_LIST_ACTID_BOUND_DATE_RANGE`，不可假冒「詳情場次」或以全站日期推測。其它有 session 的四筆以詳情為準；兩筆多場次無法證明唯一場地，UI 透過 `venueNote` 顯示「多場次：各場次地點請依官方明細確認」。
> - `scripts/p30_l7a_smoke_index.html` 僅在 PR #17 隔離分支修改：CKSMH `dateStart/dateEnd`、`venue`、`venueNote`、`summary`、`sessions[]`、官方證據 label；多場次清單顯示涵蓋日期和「詳見個別場次」，modal 展開每個 `start/end` 臺灣時間，不用 `innerHTML`；舊金融科技展延期原訂/暫定/未確認三種欄位維持。
> - CI Run [40284806144](https://github.com/easonliu714/event_scraper_public/actions/runs/40284806144) 14/14 tests + JS + 完整父資料 SHA PASS，5/5 title、5/5 date、3/5 unique venue、5/5摘要、2 multi-session；Android-only Artifact `12633399655`，SHA manifest PASS。44 IDs 不變、39 TWTC rows 完全不變；不更動正式 `docs/data.json`、`docs/index.html`、`scraper.py`、PWA Scope/Service Worker、Writer、通知、Golden。Android 8769 尚未實測。
>


> **2026-10-26 P30-L7-D 官方機構雙角色延期候選與 Android UI（PR #16 Draft）**
>
> - 新 source `scripts/p30_l7d_official_fallback.py`：三個固定 HTTPS 入口，一次一站、有限位元組、嚴格網域路徑與 redirect allowlist、不得重試與停用 TLS；`TWTC_DETAIL`=官方原訂時間與延期標題、`FINANCIAL_FEDERATION_NOTICE`=聯合主辦/金融總會延期暨正式確認未完成、`NCCC_NOTICE`=聯卡中心對預定 12/18～19 的公告。各來源 HTTP status/sha256/URL/parse 對應證據寫入隔離 `schedule_roles.json`／`diagnostics.json`。聯卡中心 canonical HTTPS host 為 `www.nccc.com.tw`；原 bare host 故障不被當成 HTML 解析問題。
> - 僅更新 FinTech 2026 一筆候選：`scheduleStatus=POSTPONED_PENDING_FINAL_CONFIRMATION`、`originalDateStart/End=2026-10-23/24`、`tentativeDateStart/End=2026-12-18/19`、`confirmedDateStart/End=NULL`、`dateStart/End=NULL`，附上機構公告來源。其餘 43 筆與全部 44 個 id 不變，來源詳細日期 38 仍保留。Android `when()` 顯示「已延期／正式展期待確認」，modal 分列「原訂日期」、「預定改期」、「正式日期」及官方證據連結，不把預定當正式確定。
> - 最終 GitHub Actions Run `40281136558` 3/3 HTTPS HTTP 200、13/13 Python offline、JS Node syntax、SHA immutable old UAT、精確四路徑、五檔 SHA256 全 PASS；可供 Android 本機 `127.0.0.1:8768` 煙霧測試的 Artifact `12632108815`。**Android 新版使用者實測尚未回報**，PR #16 與 PR #15 仍 Draft 未 Merge，正式 Pages/通知/排程/Writer/Golden 全未啟用。
>


> **2026-10-26 P30-L7-C FINTECH POSTPONEMENT SEMANTIC DATA ROLES**
>
> - Source TWTC 清單 `延期未定` + TWTC 詳情 `展出日期：2026/10/23～2026/10/24` 並非不同 HTML 日期格式，為同一活動**取消原訂／預定另定日期**的狀態切換。現有 P30-L4-A `raw_period_matches()` 將 `延期未定` 拒絕與正常 MM/DD 日期同等對照，產出 `LIST_DETAIL_PERIOD_CONFLICT` 防止原訂日期誤作有效日期。
> - 大會正式公告 2026/10/20 `https://www.fintechtaipei.tw/Announcement/19` 表示「預定延期至 2026/12/18～12/19」，**仍待正式確認**。新 PR #15 隔離候選 schema 準備 `originalDateStart/End`、`tentativeDateStart/End`、`confirmedDateStart/End=NULL`、`scheduleStatus`、HTTP SHA256/來源與公告連結，顯示原訂與暫定各自標籤，不得填 `dateStart/End` 為已確認。
> - 11/11 Python 離線測試 PASS，Node frontend JS Syntax PASS。P30-L7-C GitHub Run `40275813585` 對 TWTC detail HTTP OK、對大會 announcement 為 `SSLError`，故 Gate **HOLD**，沒有生成新的 Android candidate；只保存 `hold_diagnostics.json` 至 Artifact `12630675096`。這是網站對 GitHub Runner 憑證信任／TLS 連線驗證問題，非 HTML Parser 合約通過或否定；禁止 TLS verify=false 繞過。
> - 使用者已回報 P30-L7-B Android 截圖符合預期，舊已驗收版仍有效；此 PR #15 未成功更新發布資料及 Android ZIP。未來有可信第二來源後再做独立 UAT／收斂至正式資料架構。
>


> **2026-10-26 L4-A / L7-B 完整年份回填與 Android CI 實證**
>
> - L4-A 新 `scripts/p30_l4a_twtc_detail_dates.py`（PR #13）實際以 L3-A Run 40270383643 原始 39 筆為身份參照，39 次限流官方詳情 GET，來源資料 Evidence 僅標準化 `DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE` 38 件，延期活動一件 HOLD。Run 40273199767 CI SUCCESS，13/13 tests；來源 Artifact 12629371018。這裡的 DATE_VERIFIED 仍為候選證據，不是人工 Golden。
> - L7-B 新 `scripts/p30_l7b_date_overlay.py` 對固定原 44 筆 Android candidate 與 L4-A 原始 39 筆來源 SHA 進行雙向 lineage Gate，只有正確活動網址/標題/原始展期的 38 筆填入 `dateStart/dateEnd`、`OFFICIAL_EXHIBITION_DATE`、`dateEvidenceRunId`、`dateEvidenceSHA256`，一件延期維持 NULL；CKSMH 五件完全保留、44 活動 IDs 未改、票況 UNKNOWN、validity UNCERTAIN。新的 UI `when()` 能顯示 YYYY-MM-DD，延期優先顯示「展覽延期／日期未定」，`sourceLabel()` 將 LIST_TABLE_ONLY 等技術代號翻譯為易懂文字。
> - PR #14 `feat/eventradar-p30-l7b-android-date-uat` 與已通過的 PR #12 採**新增分支／隔離差異**，不改既有 Android 7/7 PASS 原始版本。Run [40273949404](https://github.com/easonliu714/event_scraper_public/actions/runs/40273949404) 10/10 Offline、Node syntax、Immutable SHA、44/38/1 實際 Artifact + 四檔 SHA Gate PASS。最終 Artifact 12628754512；**使用者 L7-B Android UAT 尚未執行**。
> - 後續發展：先 P30-L7-B Android 日期回填 UI 煙霧測試；其後 L3-B FamiTicket/ibon/StrollTimes 列表、CKSMH 詳情欄位、TWTC 延期語義、全來源 Category/Golden/可逆有效性，再進入正式 PWA、單 Writer/發版及雙 Repo 退役。
>


> **2026-10-26 P30-L4-A TWTC date evidence 結構修正（PR #13 Draft）**
>
> - 使用者 Android 畫面證明：TWTC 清單 LIST_TABLE_ONLY 只有 MM/DD～MM/DD，許多活動仍標示年份待核對，然而官方 exhibition_more.aspx?id=... 詳情有 YYYY/MM/DD～YYYY/MM/DD。原 L3-A run() 只抽樣第一筆，所以其餘不自動回填。
> - 隔離 L4-A source-only 實作 p30_l4a_twtc_detail_dates.py，復用 L3-A get_html()、parse_detail_date()；每筆走 HTTPS allowlist → URL Detail ID 一致 → H1/H2/H3 活動標題一致 → 完整官方日期合法 → 與原始清單 MM/DD 一致的 Gate，通過才輸出 start/end/source_time_role/response_sha256。缺詳情、403、重定向活動 ID、延期、時間衝突皆 HOLD。
> - PR #13 目前只生產 GitHub Artifact 日期證據，不更動 PR #11 與 PR #12 原始程式、Android UI 或正式 docs/。L7-B 方可依固定 SHA 合約回填 dateStart/dateEnd 並重新驗證 Android；票價、票況仍 UNKNOWN，GOLDEN_ACCEPTED=0、AUTO_HIDDEN=0、APP_DATA_PUBLISHED=false。
>


> **2026-10-26 P30-L7-A USER-ATTESTED Android 7/7 PASS**
>
> - Android 本機 `127.0.0.1:8766` 候選 UI 已由使用者回報七項 PASS：44 筆首頁、CKSMH 5／TWTC 39、關鍵字及類別、詳情 modal/關閉與無重疊、未知日期票價票況提示、官方 HTTPS 連結。對應 PR #12 HEAD `76171eae8352818721a5480d18a1cc4c0e283ccc`、Run `40271164263`、Artifact `12628147623`。不改動 UI/PWA 正式 `docs/index.html`、`docs/data.json`。
> - 架構狀態升級只適用 `ANDROID_LOCAL_TWO_SOURCE_SMOKE=PASS`，不得延伸為 PWA Install/Offline Scope、19 平台全面來源回歸、官方 Golden、有效性可逆引擎或已部署 Pages PASS。後續 P30-L3-B 需維持可追溯的 GET→LIST→DETAIL→FIELDS 來源分層證據，個別失敗不得污染已過 Gate。
>


> **P30-L7-A Android Portable Manifest 修復驗證**：PR #12 最新 HEAD `76171eae8352818721a5480d18a1cc4c0e283ccc` 僅更新 workflow 打包命令，在 Artifact 內使用相對檔名的 `SHA256SUMS.txt`，CI 先在 `p30-smoke/` 下 `sha256sum -c`，三檔 OK。正式 GitHub Run `40271164263` SUCCESS，最終 Android-only Artifact `12628147623`，須使用此包、不要使用前版 `12629030170`。瀏覽器測試必須以同支 Android `127.0.0.1:8766` loopback HTTP 服務載入，非正式 Pages、非安裝型 PWA、無外部數據寫入。Android 實機尚待使用者執行，不得將 Actions SUCCESS 當 Android UAT PASS。
>


> **P30-L3-A 與 L7-A Android 隔離 UI 實作 2026-10-26（PR #11 / #12 仍 Draft）**
>
> - L3-A 官方展覽檔期（PR #11）：`scripts/p30_l3a_twtc.py` 以 TWTC `/exhibition?p=home` HTML 表格逐列解析 title/organizer/venue/rawPeriod/本網站 `exhibition_more.aspx?id`；對只含月日的清單日期保留 `date=null`、`EXHIBITION_PERIOD_RAW_UNNORMALIZED`；只有抽樣詳情頁**來源身分及完整年份展期都匹配**才產生日期候選。正式 Run 40270383643：HTTP 200、39 清單、11/11 offline、單筆詳情日期候選；非 Golden。Workflow `.github/workflows/eventradar_p30_l3a_twtc.yml` 限一清單與一詳情 GET。
> - L7-A Android local smoke（PR #12）：`scripts/p30_l7a_build_candidate.py` 將 L2-B CKSMH 5 件與 L3-A TWTC 39 件 Artifact 唯讀轉 `P30-CANDIDATE-1` Schema（來源名稱、原始網址、日期欄位角色、分類依據、UNKNOWN 票況、UNCERTAIN 有效性、id SHA）；嚴格禁用假 Golden/Writer/已發布與非允許來源；不連網，不讀舊 JSON。CI Run 40270957865 PASS，8/8 offline + Node syntax；結果 Artifact 12629030170。
> - Mobile UI `scripts/p30_l7a_smoke_index.html`：單檔 CSS/JS、`fetch('./data.json')`、來源與類別篩選、關鍵字搜尋、活動清單、詳情 modal、官方 HTTPS 連結、缺值以官方為準、固定候選免責聲明；**不含** Service Worker/安裝 PWA/正式 UI 合併/正式資料 Writer、外部 JS/CDN。Artifact `index.html + data.json + README.txt + SHA256SUMS.txt` 由 Android 同機 loopback HTTP server 讀取，不改原 Pages scope。
> - 狀態層級：`L7A_CI_PASS` / `ANDROID_LOCAL_SMOKE_READY`，但 `ANDROID_UAT=NOT_ATTESTED`、`GOLDEN_ACCEPTED=0`、`AUTO_HIDDEN=0`、`APP_DATA_PUBLISHED=false`。此 UI 是最小候選驗證面板，不等於完整 P20 Preview UI 功能已合併或真實 G5K 已結案。
>

> **2026-10-26 CKSMH 官方入口實作（PR #10，尚未併入 main）**：新增 `scripts/p30_l2b_cksmh.py`（兩個官網 allowlisted HTTPS GET + 最多一筆詳情、分段 HTTP/HTML digest、actId 去 session/tracking、LIST_ONLY 不推定票況）；`tests/p30/test_l2b_cksmh.py`（11/11 Offline）；`.github/workflows/eventradar_p30_l2b_cksmh.yml`（自動隔離 Gate，原 JSON/UI/Runtime 不變）。Run [40269917573](https://github.com/easonliu714/event_scraper_public/actions/runs/40269917573) SUCCESS，Query.list.ctr **200 / LIST=5**、`/CKSMH` **200 / LIST=0**、一筆 DETAIL_HTTP_OK；報告 Artifact `12627554765`。以上只代表清單與回應層次，可用來源修復，不代表 Golden/PWA 發布。
>

> **L2-B 可用來源入口候選（尚未程式實作）：** 中正紀念堂（`event.culture.tw`）以 `https://event.culture.tw/CKSMH` 或 `https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr` 作唯讀官網資料入口提案；原診斷基線 `https://event.culture.tw/mocweb/reg/CKSMH/` 回 404。**入口存在不代表 Python Runner 200、清單/詳情欄位可解析**。後續需要 allowlist/事件連結解析、受控單次 HTTP 及 CI/Artifact，未達成則 L2-B HOLD。
>

> **SRC-P30-L2-A 實作證據（2026-10-26，Source PR #9 Draft，未併入 main）**
>
> - `scripts/p30_l2_http_triage.py`：只解析 P30-L1 GitHub Artifact 的 `diagnostics.json`，逐平台原樣保留 HTTP code、observed URL、redirect trail、Content-Type、HTML SHA256、list/detail 計數；僅輸出 L2_HTTP_FAILURE_REVIEW、L3_LIST_EMPTY_REVIEW、L4_DETAIL_SAMPLE_NEXT 三類，不發活動網站 HTTP，不推定 SOURCE_GONE/過期/售票情況，不允許 AUTO_HIDE。
> - `tests/p30/test_http_triage.py`：9 個離線正反向案例（錯誤狀態碼、計數不符、重複來源、Writer/通知/Golden/發布旗標、403/404/429 等 FAIL CLOSED）。
> - `.github/workflows/eventradar_p30_l2a_offline.yml`：P30-L2-A 單分支唯讀 push Gate，檢查相對 PR #7 **恰好三檔新增**、主線 `docs/data.json` / `scraper.py` / `docs/index.html` 不變、Python 離線測試、從既有 Run 40196442965 下載診斷 Artifact 並產出獨立 triage 報告，不抓活動網站、不寫正式資料。
> - Run `40266605126` SUCCESS，Job `121390275278`、9/9 測試、19/4/4/11 重播全 PASS；下個 L2-B 以 403: KKTIX/拓元/BeClass，404: 中正紀念堂；HTTP 200/LIST=0: FamiTicket/ibon/台北世貿/StrollTimes 為優先對象。可解析 11 平台繼續 L4，不等待其他來源解除 HOLD。
> - L2-A 的 Source PR #9 Head `7fd14010f5dbc3ef383919ee67eb21283904afe2`，其 PR base 為未合併 PR #7，非正式 main；任何 P30-L2-A 正式併入 main 須先解決堆疊祖先/Review/授權及獨立 Read-back。
>

> **2026-10-26 最新功能架構檢核（PR #8 候選；僅 Source 最終保留）**
>
> - 實際 GitHub 權威：Source main `fc4f963247d68eed29425808cc14e7250f312d05`；Preview `03e515d65e827d5ed67fe341d079907a96bf784a`；ShowNews `85fed3e85ff5deff479a85b8d692aa9e6d2bdcad`。Source PR #6 是凍結 Snapshot 遷移候選（CI PASS 但已被「新資料優先」決策取代）；#7 是一次性診斷工具；#8 是此文件治理候選。
> - L2 HTTP fault buckets：`HTTP_ERROR` 4（KKTIX、拓元、BeClass、中正紀念堂）；L3 HTML `HTTP_OK/LIST=0` 4（FamiTicket、ibon、台北世貿、StrollTimes）；其他 11 平台已有非空清單候選，**只有取樣 11 筆詳情成功，非正式覆蓋率**。證據為 Source Actions `40196442965` 的 Job `121178174230`，Report Artifact `12600795314`。
> - L2 最小架構：純函式 `classify_http(outcome)`、受控官方 URL allowlist、HTTP code/redirect/content-type/byte SHA + error bucket 的資料結構、offline fixture；禁止以 HTML 200 代理 LIST 成功、不能用 403/404 直接判定 SOURCE_GONE、更不能用繞過限制或重試轟炸修正錯誤。
> - L3～L5 架構優先繫結 `platform→list URL→event URL→detail response→canonical event identity→field role/evidence`，欄位可 NULL/UNKNOWN、保留官方連結；L6 可逆 ledger；L7 新一輪 candidate JSON+run_id+SHA，不讀入歷史 JSON；L8 隔離 UI Android UAT，L9 明確授權單 Writer/正式 Pages，L10 兩庫外部依賴核查後再授權 Archive。
> - 已有 P1～P29 Android/P29 原生 CI Gate 保留且不重做；Source 原 PR #1 writer / notification / schedule HIGH_RISK_HOLD，Source P20 PR #2 與 Preview P20 PR #1 暫不 Merge。完整各 Gate 測試、優先序與驗收狀態唯一參照同版本 `ROADMAP_PR_ISSUE_CLOSURE_AUDIT.md`。
>


> **最新架構增量候選｜2026-10-25 P30 重新抓取優先（Docs-only Draft；尚未併入 main）**
>
> GitHub 即時身分：Source main `fc4f963247d68eed29425808cc14e7250f312d05`、Preview main `03e515d65e827d5ed67fe341d079907a96bf784a`、ShowNews main `85fed3e85ff5deff479a85b8d692aa9e6d2bdcad`。SRC-P29 Source PR #5/Preview PR #2 **MERGED**，原 P20 HEAD 各 1 個 GitHub native check SUCCESS，歷史下文舊「P29 候選」「HEAD 0 checks」不再代表現況；SRC-P1～P28 Android 實測 PASS 繼續有效。
>
> 本節把本輪最新討論的分段 Gate 明確繫結到 **UI／API／Parser／Data／CI**；詳細分層 Gate、驗收契約、狀態詞與優先順序由相同 GitHub Commit 的 `docs/ROADMAP_PR_ISSUE_CLOSURE_AUDIT.md` 唯一對應，不可另建平行 Roadmap。舊正文完整保留。

## SRC-P30 即時來源品質導向 UI／API／資料架構

```text
GitHub easonliu714/event_scraper_public  [最終單一權威目標; 目前尚未正式整併]
├─ main@fc4f963247d6... [已部署歷史狀態，禁止本 Gate 覆蓋]
│  ├─ scraper.py [舊版同步/非同步抓取+寫 docs/data.json+通知，會有副作用]
│  ├─ docs/index.html, docs/manifest.json [正式 Pages 舊入口；保持不變]
│  ├─ docs/data.json [8,436 筆舊靜態資料；最新內容未被證明]
│  └─ docs/{ROADMAP_PR_ISSUE_CLOSURE_AUDIT,UI_API_DB_FEATURE_ARCHITECTURE_TREE}.md [兩份唯一治理]
├─ PR #7: feat/eventradar-p30-live-diagnostic@959324cb3bad... [DRAFT, NO MERGE]
│  ├─ scripts/p30_live_acquisition.py [P30-L1 僅診斷；單次有限量 public HTTPS]
│  │  ├─ Stage 1 HTTP [原始/最後網址、狀態碼、HTML、redirect、安全白名單]
│  │  ├─ Stage 2 LIST [HTML anchor → 清單候選 title/url/platform，不推測日期]
│  │  ├─ Stage 3 DETAIL [每平台最多抽樣一頁，標 HTTP 與來源身分]
│  │  ├─ Stage 4 FIELDS [date/location/price/description 獨立證據，允許 UNKNOWN]
│  │  └─ Runtime 只產生 p30-artifacts，不 import 主程式、不呼叫通知/寫入功能
│  ├─ tests/p30/test_live_acquisition.py [HTTP block, redirect, URL, list, unknowns 等離線負例]
│  ├─ docs/P30_LIVE_ACQUISITION_DIAGNOSTIC.md [非正式運作的技術候選說明]
│  └─ .github/workflows/eventradar_p30_live_diagnostic.yml [P30 專用隔離分支 push]
│     ├─ CI 校驗正式 docs/data.json / scraper.py Git Blob 沒變、P20 純 parser SHA
│     ├─ P20 PR #2 event_details.py@4c2c9ec... [僅作純解析器，未合併/未執行 show_news]
│     └─ Run 40196442965 SUCCESS → Artifact 12600795314 [新鮮 338 筆抽樣候選]
│        ├─ candidate.json [短期候選，非完整資料、非 Golden、非正式 Pages]
│        └─ diagnostics.json [19 平台 HTTP / 清單 / 詳情 / 欄位品質與失敗原因]
├─ PR #6: feat/eventradar-p30-preview-isolated@1402df1bd32a... [DRAFT, SUPERSEDED]
│  └─ docs/p30-preview/data-parts/* [歷史 9,850 筆 byte-preserving CI PASS，非新 PWA 資料來源]
├─ PR #2: feat/eventradar-source-only-p20@4c2c9ec... [DRAFT, DORMANT]
│  ├─ show_news.py [複合抓取/排程/通知；不得直接執行]
│  └─ event_details.py [JSON-LD/DOM 身分及欄位候選；已被 P30-L1 SHA 限定讀用]
├─ PR #1@26888422e486... [DRAFT, Cloud Scheduler/Writer HIGH-RISK HOLD]
└─ Future P30 source-quality modules [尚未實作]
   ├─ source_catalog / http_probe [L2: 官方來源入口 + 403/404/429/redirect 診斷]
   ├─ list_parser / fixture tests [L3: 正確清單、URL、去重、分頁]
   ├─ detail_parser / identity tests [L4: 詳情身分、多場次/合集、缺頁]
   ├─ field_evidence / source_roles [L5: 活動日期 vs 售票期間、地點、票價、摘要]
   ├─ reversible_validity_ledger [L6/G5J: ACTIVE/EXPIRED/NON_EVENT/SOURCE_GONE/UNCERTAIN]
   ├─ candidate-json / schema / sha / report [L7/R3C-O3: 新鮮隔離資料 + 官方 Golden]
   ├─ docs/p30-fresh-qa/ [L8/G5K: 新資料隔離 PWA 與 Android UAT，路徑待 Gate 核准]
   ├─ single-authorized-writer / production QA [L9: 完整驗證+另案發布授權]
   └─ repo-consolidation [L10: Source 最終單 Repo；Preview/ShowNews 不自動封存/刪除]

Separate Preview main@03e515d65e... [舊 9,850 筆測試快照與 G5C/G5D visibility UI；不當新數據]
└─ PR #1@b55b367308... [九卡片/詳情 Android UAT PASS, HEAD 原生 CI SUCCESS, STILL DRAFT]

Separate ShowNews main@85fed3e85ff5... [歷史 FastAPI/七平台/Telegram，Render 仍 UNKNOWN]
└─ /test-crawl 可能觸發網路抓取+推播；禁止在唯讀/QA 中呼叫
```

### 新資料契約與 PWA 介面角色（規格，非已發布）

| 節點 | 最小可安全使用的輸出 | 必須保留的證據／邊界 |
| --- | --- | --- |
| HTTP network (L2) | platform, requested/final_url, status, timestamp, content_type | 403/404/429/Redirect/非 HTML ≠ HTTP PASS；域名白名單，不繞過限制 |
| List parser (L3) | title, official_url, platform, list_observed_at, list_status | URL 去重、清單身份、連結是活動而非導覽；空清單/JS-only 明示 HOLD |
| Detail parser (L4) | detail_http, canonical_identity, source_page_type, session evidence | 可核實的來源身分，集合頁/多場次不得誤綁單場 |
| Field roles (L5) | date?, location?, price?, description?, type?, evidence and UNKNOWN | 日期必須是活動角色而非促銷／開賣日期；不得捏造票價、票況 |
| Validity (L6/G5J) | reversible validity_status + reason + original record | 五種狀態；單次來源失效不自動下架 |
| Candidate JSON (L7) | isolated new snapshot + run_id + acquisition time + report/hash | 舊 8,436/9,850 不混用；Schema、欄位完整率、來源清單 |
| PWA list (L8) | card title / official URL / source / available verified fields | 允許局部資訊；空值顯示「未確認／請見官方」，不顯示假精度 |
| PWA detail (L8) | source-linked detail and session disambiguation | 票價／日期／場次若條件性或來源不確定，標示以官方公告為準 |
| Publish (L9) | approved data.json via single writer, manifest/URL parity & rollback | 尚 LOCKED；Android 新資料驗證不能借用舊 P20 測試代替 |

**Stage-to-Gate Crosswalk**：`P30-L2` HTTP → `P30-L3` LIST → `P30-L4` DETAIL → `P30-L5` FIELDS → `P30-L6` G5J VALIDITY → `P30-L7` R3C-O3 GOLDEN+NEW JSON → `P30-L8` G5K ANDROID UAT → `P30-L9` controlled production → `P30-L10` repo consolidation。下一個開發點為 **START P30-L2-A HTTP 失敗類型與官方入口修復**；先用 Run `40196442965` 的 `diagnostics.json` 分流 403/404/429 和 HTML 200 但無清單，建立來源負例，再定點更正；避免原樣重跑全部 19 平台。

**治理固定旗標**：`SOURCE_RUNTIME=DORMANT`; `GOLDEN_ACCEPTED=0`; `AUTO_HIDDEN=0`; `APP_DATA_PUBLISHED=false`。即使使用者允許忽略/將來刪除舊 JSON，也不是允許本 PR 改寫正式 JSON、清空 Pages、啟動 Cloud Writer、通知、Schedule、改開 PR 狀態或 Archive Repo。將來正式新資料可取代舊資料之前，必須有單 Writer、SHA、回復、UAT 與獨立授權。

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

> **最新合併基準：SRC-P25（2026-10-24，Asia/Taipei）。** Source `main@a8d21d2e6aa056a13d5eb9de3d32920d11d4f740` 已一般 Merge Commit 合併 [Docs PR #3](https://github.com/easonliu714/event_scraper_public/pull/3)；兩份文件正式存在 `main`。下方 SRC-P24「候選」章節是原始歷史記錄，不再代表現況。
> **P26 文件修訂範圍：** 本次僅新增最新狀態與歷史分界，仍需新的 Docs-only Draft PR 合併才能成為 `main` 的最新版；不更動 Source、Preview、Workflow 或資料。

## 現行 UI／API／資料架構（SRC-P25 基準）

```text
EventRadar Taiwan
├── SOURCE: easonliu714/event_scraper_public
│   ├── main@a8d21d2e6aa... [GOVERNANCE_MAIN; P25 MERGED]
│   │   ├── scraper.py [legacy runtime，未改]
│   │   ├── docs/data.json [既有正式靜態資料，未改]
│   │   ├── docs/index.html [既有網頁，未改]
│   │   ├── docs/ROADMAP_PR_ISSUE_CLOSURE_AUDIT.md [正式治理]
│   │   └── docs/UI_API_DB_FEATURE_ARCHITECTURE_TREE.md [正式治理]
│   ├── PR #1@26888422e486... [OPEN/DRAFT; 34 檔; Cloud Writer HIGH-RISK HOLD]
│   ├── PR #2@4c2c9ec93ae... [OPEN/DRAFT; 新增 5 檔; SOURCE DORMANT]
│   └── ci/eventradar-source-ci-p22@a50bfd25... [Runner 40094208387 SUCCESS]
├── PREVIEW: easonliu714/eventradar-pwa-preview
│   ├── main@a8cde084ab55... [既有 PWA；data.json／visibility.js／period_gate.js 不變]
│   ├── PR #1@b55b3673088b... [OPEN/DRAFT; index.html 僅一檔；九案例 Android UAT]
│   └── ci/eventradar-preview-ci-p22@0c894a36... [Runner 40094214324 SUCCESS]
├── STORAGE／API [不自行捏造資料庫]
│   ├── Python parser candidate → 靜態 JSON [main Runtime 尚未接入]
│   ├── Source docs/data.json／Preview data.json [不可在本 Gate 業務寫入]
│   ├── PWA HTTP 靜態 JSON 載入、localStorage 已讀、卡片/Modal 顯示
│   └── 沒有已證明的新 EventRadar 專屬 REST/SQL 後端
└── QUALITY / RELEASE
    ├── SRC-P1～P25: PASS；P23 固定 P20 HEAD 的兩條 Runner SUCCESS
    ├── P20 PR HEAD 直接 CI: 0/0 Check runs，NOT_ATTESTED
    ├── GOLDEN_ACCEPTED=0;AUTO_HIDDEN=0;APP_DATA_PUBLISHED=false；G5J／G5K: OPEN／HOLD
    └── Merge/正式資料/Cloud Scheduler/通知: LOCKED
```

**架構更新政策：** 保留 SRC-P24 以下所有 UI/UX、API、資料架構與 Gate 歷史原文；新開發以 GitHub `main` 這兩份文件為唯一進度治理基線。任何 Runtime/資料發布須另行授權，不能以 Candidate 或 CI 成功冒稱 Golden。

---

## 歷史封存：SRC-P24 UI／API／資料架構（原文逐位元組保留）

# 活動暨售票雷達｜UI／API／資料儲存／CI 功能架構樹（SRC-P24 候選）

> **最新快照：2026-10-24，Asia/Taipei。** 本文件為 GitHub `docs/` 文件治理 Draft PR 候選；待經核准 Merge 至 `main` 並獨立讀回後，才可主張為 Source Repo `main` 的正式功能樹權威。後續歷史附錄為時間點紀錄，最新狀態以本章為準。

## 最新功能架構（來源、狀態、Gate、下一步）

```text
活動暨售票雷達 EventRadar Taiwan
├── A. Source Repo: easonliu714/event_scraper_public
│   ├── main@6004754f90d5... [FROZEN; legacy scraper.py/ docs/data.json/ docs/index.html]
│   │   ├── 爬蟲 scraper.py [MAIN 存在；非新候選 runtime]
│   │   └── 原 docs/data.json / index.html [未更動]
│   ├── PR #1@26888422e486... [OPEN/DRAFT/HOLD; 34 files; schedule + writer risk]
│   ├── PR #2@4c2c9ec93ae... [OPEN/DRAFT; 5 added; SOURCE DORMANT]
│   │   ├── show_news.py [Android P13/P16/P18 源碼候選 PASS；主線未接線]
│   │   ├── event_details.py [G5H offline tests PASS]
│   │   ├── requirements-actions.txt [依賴聲明，尚未正式執行]
│   │   └── tests/test_event_details*.py [離線回歸 PASS]
│   ├── ci/eventradar-source-ci-p22@a50bfd25ff07... [ONE READONLY WORKFLOW]
│   │   ├── .github/workflows/eventradar_source_p22_branch_ci.yml
│   │   └── [CI SUCCESS Run 40094208387] 固定 PR #2 HEAD 4c2c9ec...
│   └── docs-only P24 governance PR [本次候選；尚未合併 main]
├── B. Preview Repo: easonliu714/eventradar-pwa-preview
│   ├── main@a8cde084ab55... [FROZEN]
│   │   ├── index.html [主線現行 UI；P20 UI 尚在 Draft]
│   │   ├── event_visibility.js [G5C 曾驗證；主線維持原值]
│   │   ├── eventgo_period_gate.js [G5D 曾驗證；主線維持原值]
│   │   ├── data.json [固定 9,850 historical snapshot；未被改寫]
│   │   └── manifest.json / preview_status.json / .nojekyll [現有]
│   ├── PR #1@b55b3673088b... [OPEN/DRAFT; index.html ONLY]
│   │   ├── Card referenceCardSummary: date/location/price + escape [9/9 Synthetic Android PASS]
│   │   └── Modal display_roles / 免責／缺值 [9/9 Synthetic Android PASS]
│   └── ci/eventradar-preview-ci-p22@0c894a3626fc... [ONE READONLY WORKFLOW]
│       ├── .github/workflows/eventradar_preview_p22_branch_ci.yml
│       └── [CI SUCCESS Run 40094214324] 固定 PR #1 HEAD b55b367...
├── C. 介面與儲存資料
│   ├── 輸入：官網公開活動/售票資訊 [未經 Golden 真值全面驗證]
│   ├── 傳遞：show_news.py + event_details.py 候選 JSON [非正式主線資料流]
│   ├── 正式靜態儲存：Source docs/data.json / Preview data.json [IMMUTABLE IN THIS GATE]
│   ├── UI 顯示：查詢、篩選、卡片／Modal、localStorage 已讀 [Preview 已有功能]
│   └── API：靜態 JSON 由頁面載入；無已驗證新增 SQL/REST DB [不自行擴充]
├── D. 品質與測試
│   ├── SRC-P1–P23 [所屬階段 PASS；保留 lineage]
│   ├── Source G5H：Python AST／兩組 offline parser tests [CI SUCCESS, governance branch]
│   ├── Preview：Node 22／9 個 synthetic roles／escape／modal [CI SUCCESS, governance branch]
│   ├── P20 PR HEAD 直接 Check [0/0；NOT ATTESTED]
│   └── Golden 簽認 [0；HOLD], G5J / G5K [OPEN / HOLD]
└── E. 尚未完成發布鏈
    ├── P24 docs-only Draft PR 註冊及審核；須另行授權合併至 main
    ├── P25 PR HEAD 直接 CI Checks；與 P23 branch-run CI 分離
    ├── R3C-O3 Golden 覆核 → G5J validity → G5K 真實資料 UI/UAT
    └── Cloud Scheduler / commit_data writer / Merge / Notifications [LOCKED]
```

### 狀態定義與資料安全

| 狀態 | 意義 | 本輪案例 |
|---|---|---|
| `PRESENT_IN_MAIN` | 預覽/來源 main 真正存在的元件 | legacy scraper.py；preview event_visibility.js |
| `DRAFT_ONLY` | PR 裡已有、main 尚無 | Source 五新增檔；Preview index.html 改版 |
| `ANDROID_PASS` | Android 合成或封存樣本 Gate，非 Golden | P13、P15、P21/22 |
| `GOVERNANCE_RUNNER_PASS` | GitHub 治理分支 Checkout 固定 P20 Head | P23 Source/Preview Run SUCCESS |
| `PR_HEAD_CI_PASS` | PR Head 本身 check run 成功 | **目前 NOT ATTESTED** |
| `GOLDEN_ACCEPTED` | 真實官方資料獨立核准 | 0 |
| `APP_PUBLISHED` | 主線功能或正式資料授權合併部署 | false |

**防重工準則**：既有來源 parser、既有 Preview UI、G5C/G5D visibility、static JSON 資料流、P20 分支與 P23 CI 工作不能重做平行系統；只能針對未完成 Gate 增量補證。P24 文件內容在 Draft PR 中不視為 main 權威。

---

## 歷史功能架構紀錄（按原始時點保留；待驗文字不得蓋過最新章節）

# EventRadar Taiwan — UI / API / DATA / FEATURE ARCHITECTURE TREE

> 盤點日期：**2026-10-24（Asia/Taipei）**。以 GitHub **現有檔案、具名程式入口**與 Android Gate 證據復原既有系統，不是要求重新設計。  
> 狀態：**治理基線候選／已完成本地 MD；未 Commit/Push 到 GitHub**。  
> Source `easonliu714/event_scraper_public`: `main@6004754f90d551cdb0cdb91a3e04b42c04f45f48`；Draft PR #1 `26888422e48634d9729d2deea67b7996a5d1e4ee`。  
> Preview `easonliu714/eventradar-pwa-preview`: `main@a8cde084ab5581736d86094d8cdcc2cdc9963000`。

## 0. 證據語義（禁止越級宣稱）

- `[CODE]` 程式碼/HTML/Workflow 存在；`[CI]` 特定 PR HEAD Actions 有 success；`[ANDROID]` 指定凍結快照 Termux PASS；`[UI-DEPLOYED]` 已進入**獨立測試 PWA**，不等於正式網站；`[REVIEW]` 候選證據；`[NOT-PROVEN]` 缺可靠證據；`[BLOCK]` 未授權或前置未完成。
- 官方內容正確性與「URL 可連線」不同；Android 來源差異 0 與「日期正確」不同；JSON-LD 存在與「正式 Golden」不同。
- 使用者提供的 `SPC_System_*.md` 只供格式比照：**EventRadar 不是 FastAPI+PostgreSQL 的 SPC_System**。本 Repo 查得的 EventRadar 主鏈為 GitHub Actions/Python + 靜態 JSON PWA + Termux Toolkit；沒有查到已部署 EventRadar 自有 REST API 或 RDBMS，不能捏造資料表。

## 1. 操作介面/UI/UX 多層樹（真正測試站 source）

**目前測試 UI 權威**：`eventradar-pwa-preview/index.html` Git blob `c11c65322444a309ab04751887f670b25fe8cf6f`；配套 `event_visibility.js` blob `8aa965a4a4640a926c6dd0078f701d543665a9b4`、`eventgo_period_gate.js` blob `96505b78943fdaffef2a87f9b09d139800b6f140`。

```text
EventRadar PWA PREVIEW / index.html [CODE; UI-DEPLOYED；正式 UAT NOT-PROVEN]
├── 00. 明確測試站警告＋noindex/nofollow [CODE; DEPLOYED]
├── 01. 頂部/更新 [CODE; DEPLOYED]
│   ├── 活動雷達名稱與全部標示已讀 [CODE]
│   ├── 設定 ⚙️ [CODE]
│   ├── 關鍵字搜尋框 #search [CODE]
│   ├── 下拉刷新 → init() → fetch(data.json?t=...) [CODE]
│   └── 最後更新時間、讀取失敗重試 3 次及錯誤提示 [CODE]
├── 02. 篩選 Chips [CODE]
│   ├── #platform-chips 來源平台（各來源筆數）
│   ├── #region-chips 北/中/南/東/離島/未定等區域處理
│   ├── #status-chips 「新進活動」「關注關鍵字」
│   └── #type-chips 活動分類
├── 03. 列表與統計 [CODE; 2026-10-23 FROZEN ANDROID 8233]
│   ├── #validity-audit G5C/G5D 可見/隱藏/待查摘要 [CODE; Android replay]
│   ├── #result-count／#update-time／來源資訊免責 [CODE]
│   ├── #event-list 活動卡片、來源平台/類型/區域、基本日期 [CODE]
│   ├── currentPage / PAGE_SIZE=50 分頁 [CODE]
│   └── 排序/搜尋/區域選取邏輯 [CODE; 端到端 UX UAT 尚非本輪驗證]
├── 04. 詳情 Modal #detail-modal [CODE]
│   ├── 活動圖、平台／類型 badge、標題
│   ├── #m-date 日期、#m-location 地點、#m-price 票價
│   ├── #m-desc 活動說明（缺值顯示提示）
│   └── #m-link 前往來源官方活動詳情（外部連結）
├── 05. 使用者本地偏好與已讀 [CODE]
│   ├── eventradar_preview_myKeywords  關注關鍵字 JSON
│   ├── eventradar_preview_readEvents 已讀 URL 陣列 JSON
│   ├── eventradar_preview_lastDataTime 快照時間
│   ├── 「全部已讀」/移除或新增關注關鍵字
│   └── localStorage 僅瀏覽器本機，不是伺服器 DB 或跨裝置同步
├── 06. 通知 UI [CODE STUB; PREVIEW DISABLED]
│   ├── 設定頁有通知狀態/檢查權限元件
│   ├── checkAndNotifyNewFavs() 立即 return
│   ├── requestNotifyPermission() 顯示「測試站不啟用通知」
│   └── checkNotifyStatus() 固定顯示「通知停用」 [安全預期]
└── 07. PWA manifest [CODE]；offline/service worker [NOT-PROVEN]
    ├── manifest.json 有 icons/name/display 等資訊
    ├── 目前 Preview repo tree **未見 service-worker 檔案**
    └── 不得直接宣稱離線安裝/背景推播已有完整 UAT

OLDER SITE / event_scraper_public/docs/index.html [LEGACY FORMAL MAIN]
├── 具有類似搜尋/平台/地區/狀態/類別/詳情 UI [CODE]
├── 本次 PR 不修改 docs/index.html [DIFFERENT DEPLOYMENT AUTHORITY]
└── 不得修改舊站 HTML 後宣稱 Preview UI 已更新
```

**畫面功能驗證邊界**：UI 程式存在並已在隔離測試站，G5C/G5D 於 2026-10-23 Android 8,233 筆 replay PASS；但本輪沒有重新用瀏覽器完成所有互動、輔助使用、跨裝置及速度 UAT。資料可信度不足時顯示欄位仍可能是 `詳內文` 或不正確值。

## 2. 內外部 API／HTTP 介面樹

**EventRadar 目前架構以靜態檔案與 Python HTTP 擷取為主，未查到現有 FastAPI/Flask server/正式 SQL DB API。** 不能套用 SPC 的 `/api/dashboard`、PG 或 ETL routes。

```text
A. PWA → 同網域靜態資源 [CURRENT PREVIEW]
├── GET /eventradar-pwa-preview/index.html [DEPLOYED]
├── GET /eventradar-pwa-preview/data.json?t=<cache-buster> [CODE; UI]
│   ├── cache:no-store / 三次重試 / JSON array
│   └── 原始快照 9,850 → G5C → G5D → UI-visible 8,233（僅 2026-10-23）
├── GET /eventradar-pwa-preview/event_visibility.js [G5C]
├── GET /eventradar-pwa-preview/eventgo_period_gate.js [G5D]
├── GET /eventradar-pwa-preview/manifest.json [manifest]
└── 外部官方詳情 URL（使用者點擊 #m-link）[官方網域，不是本站 API]

B. GitHub Actions → Python 來源抓取 [PR #1 CANDIDATE]
├── .github/workflows/event_radar_pr.yml [CI read-only]
├── event_radar_pr_source_probe.yml [G4B CI]
├── event_radar_pr_g5f_source_ab.yml [G5F CI]
├── event_radar_pr_g5g_field_ab.yml [G5G CI]
├── event_radar_pr_dryrun.yml [Live Dry Run CI]
├── event_radar_pr_preview_snapshot.yml [review-only artifact]
├── .github/workflows/event_radar.yml [daily schedule / writer design; DRAFT ONLY]
│   ├── schedule: 09:17,15:17,21:17 Asia/Taipei（在 PR 檔案宣告）
│   ├── workflow_dispatch（候選）
│   ├── contents:write + concurrency single writer（候選）
│   └── `scripts/commit_data.sh` 企圖唯一寫入 docs/data.json（LOCKED）
└── 非正式 REST API；未經審查不得用該 workflow 進正式部署

C. 外部官方活動網頁/平台 [SOURCE API / HTML]
├── `show_news.py` 的各平台 async fetch_*_events_list() [CODE]
├── 官方詳情內容 → `extract_event_details_simple` + event_details.parse_detail()
├── JSON-LD Event / 活動 DOM / meta 欄位／部分平台 API [CODE]
└── 回應 200、302、403、404/410、429、503、timeout 均需語意分類；不單憑 HTTP 下架

D. 人工稽核入口 [ANDROID CLI / NO HTTP DEFAULT]
├── G5I V1.0.1 分類 receipts [ANDROID PASS]
├── G5I-R2 完整日期標題 review receipts [ANDROID PASS]
├── G5I-R3A --preflight / --probe-once [ANDROID PASS；實際 HTTP GET=8]
├── G5I-R3B --selftest / --preflight [ANDROID PASS；HTTP=0]
└── G5I-R3C 離線來源對位 [ANDROID PASS；官方內容 Golden HOLD]
```

**注意**：PR `event_radar.yml` 寫入意圖有 `contents: write`，但 PR #1 尚在 Draft/未合併，GitHub default main 並無這份新檔；不能推論正式排程已在跑。單一 writer 控制屬設計/程式候選，尚未正式運轉 UAT。

## 3. Python 服務/解析/儲存呼叫鏈與既有檔案權威

```text
Repository `event_scraper_public` [MAIN FROZEN / DRAFT PR CANDIDATE]
├── 入口: scripts/run_show_news.sh [CODE; ACTIONS-TESTED]
│   ├── --version（無網路解析 VERSION）
│   ├── --once（GitHub Actions 一次抓取）
│   ├── --daemon（背景模式；GitHub runner 不允許）
│   └── 通知 opt-in --telegram / --termux（預設 OFF）
├── 正式候選爬蟲核心: show_news.py [CODE; CI-PASS]
│   ├── stage1_fetch_lists() 各來源清單
│   │   ├── KKTIX、拓元、OPENTIX、寬宏、年代、UDN、TixFun、Event Go
│   │   ├── ACCUPASS、BeClass、FamiTicket、華山、松山文創
│   │   ├── 台北世貿、中正紀念堂、KidsClub、文化快遞、便宜旅遊網等
│   │   └── ibon/Klook/易遊網/TaiwanPass/Funcard 的部分函數目前 return [] [DISABLED STUB]
│   ├── is_known_non_event_list_entry() 列表非活動項目防線 [G4A]
│   ├── stage2_fetch_details_and_notify() 受限的詳情修復 [CODE]
│   ├── extract_event_details_simple() / `event_details.py` [G5H]
│   ├── plan_detail_updates() NEW/REPAIR budget [CODE]
│   ├── save_data_to_docs() 原始 JSON 寫入候選 [CODE]
│   ├── send_telegram_message_with_retry / Termux notify [OFF by default]
│   └── `check_and_notify()` → save_data_to_docs() → Action writer guard [CANDIDATE]
├── event_details.py [G5H CI-PASS]
│   ├── parse_detail(html,expected_url) [JSON-LD / DOM metadata]
│   ├── clean_event_url / clean_event_title / _date/_price/_loc
│   └── source binding / multi-Event / Markup warning regressions
├── Dry-run / preview evidence
│   ├── scripts/pr1_cloud_dryrun.py [CI; ephemeral temp]
│   ├── scripts/pr1_preview_snapshot.py [CI; sanitized JSON artifact]
│   ├── scripts/pr1_source_probe.py / g5f_probe.py / g5g_field_probe.py
│   └── tests/* [CI; no official golden claim]
├── 發布 guard：scripts/validate_data.py、audit_quality.py、commit_data.sh
│   ├── 基本 schema/URL/唯一性/近期 scraped_at [CODE/CI]
│   ├── 每來源欄位存在率 [CODE]
│   ├── exact `docs/data.json` staging，remote main SHA check [CODE]
│   └── 正式 main commit/push [NOT AUTHORIZED]
└── scraper.py [LEGACY CODE；非 V44 current runner]
    └── 不以其修改結果聲稱目前 Actions 實際爬蟲已更動
```

### 4 平台 R3A/R3B 日期訊號處理（官方資料 ≠ Golden）

```text
R3A 八筆 URL SHA 來源候選 [ANDROID PASS]
├── OPENTIX × 2 → 多場次／每場次 endDate 需獨立核對
├── BeClass × 2 → ROC 活動日期與報名截止日分離
├── ACCUPASS × 2 → 票券銷售區間不可當 eventEnd
└── KidsClub × 2 → 課程若仍可動態預約，不可使用歷史年份推定下架

R3B 來源回條審核 [ANDROID PASS; goldens=0]
├── 6 筆 HTTP 200，但內容完整性尚未經獨立保存/人工認證
│   ├── 2 筆 DATE_SIGNAL_REVIEW [CANDIDATE ONLY]
│   └── 4 筆 NO_VERIFIABLE_EVENT_DATE_SIGNAL
└── 2 筆 REDIRECT_UNCERTAIN → ACCESS_UNCERTAIN
```

## 4. 資料保存／傳遞架構（沒有自有 SQL DB 的證據）

```text
A. 正式來源 Git Repo / event_scraper_public
├── docs/data.json [version-controlled historic snapshot; main immutable]
├── docs/index.html, docs/manifest.json [historic site code]
├── show_news.py 寫入候選 docs/data.json（Draft workflow 尚未合併）
└── 原始 Git Blob / commit / manifest 作為權威

B. PR GitHub Actions ephemeral runner [CI-PASS; no publish]
├── `/tmp` / runner.temp 工作目錄做 live dry run
├── report.md/json 等採集品質證據 artifact（設定 retention-days 7）
├── sanitized `data.json` + preview_status.json 作為 review artifact
└── 此段不寫正式 main/data.json，不等於已發布 PWA

C. 獨立 PWA GitHub Pages / eventradar-pwa-preview [UI-DEPLOYED]
├── data.json [9,850 frozen rows; SHA256 ef39c6be...fea43b]
│   └── 不覆蓋：正式 G5I-R3C/G5J/G5K 授權與 UAT 前凍結
├── preview_status.json [source_head、baseline_sha、unverified warning]
├── event_visibility.js [G5C runtime view-only filter]
├── eventgo_period_gate.js [G5D runtime view-only filter]
├── index.html / manifest.json / .nojekyll
└── client localStorage: preview_myKeywords、preview_readEvents、preview_lastDataTime

D. Android Termux （本地驗證與不可變 evidence）[ANDROID PASS]
├── ~/eventradar                             [PR source checkout; fixed]
├── ~/eventradar_preview_site                [independent PWA checkout; fixed]
├── ~/eventradar_toolkit/gates/
│   ├── g5i_date_normalization_v101/evidence/2026-10-23/
│   ├── g5i_r2_title_period_v100/evidence/2026-10-23/
│   ├── g5i_r3a_official_golden_v101/evidence/2026-10-23/
│   │   └── official_probe/{summary.json,receipts.jsonl}
│   └── g5i_r3b_official_receipt_review_v100/evidence/2026-10-23/
│       ├── summary.json
│       ├── review_receipts.jsonl
│       └── review.md
├── evidence create-only + SHA256 + URL sha key + decision reason
└── 不含官方原始 HTML；不取代獨立 Golden 真值證據

E. 尚未觀測的系統（避免虛構）
├── EventRadar PostgreSQL / SQLite / Redis 實體表：NOT OBSERVED
├── EventRadar 服務端 REST /api/*：NOT OBSERVED
├── 主動推播訂閱伺服器／Service Worker：NOT OBSERVED IN PREVIEW TREE
└── 如未來要新增，必須先具目標、Owner、資料流、相容性 Gate 與明確授權
```

### JSON Record Schema — 真正 Snapshot Exporter 檔案定義

`pr1_preview_snapshot.py` 所接受的 PWA 欄位：

| Key | 語意 | 稽核要求 |
|---|---|---|
| `title`, `url`, `platform` | 必需身分（名稱／來源詳情 URL／來源） | URL 唯一、HTTPS、來源綁定，不等於已驗證 |
| `type`, `region` | 活動分類/地區 | 欄位存在≠分類正確；區域未知需有顯示策略 |
| `date` | 活動日期原始字串 | 不得混入 `ticket_date`；複數場次需獨立 endDate |
| `ticket_date` | 售票/報名相關日期 | 禁止用來推定活動結束日 |
| `location`, `price` | 地點、票價 | 必須官方來源 Golden parity；`詳內文`=未知 |
| `description` | 活動描述 | 有字串≠官方內容仍有效 |
| `img_url` | 活動圖像 URL | HTTPS、隱私/來源歸屬 |
| `scraped_at` | 最後採集時間 | 不是活動結束日；執行時 freshness Gate |
| `detail_checked_at` | 詳情上次校驗時間 | 不等於網頁目前有效 |

PWA exporter 對文字 HTML escape、驗證 HTTPS、同 URL 去重；`preview_status.json` 記錄原始與來源 hash/rows；R3B receipts 用 URL SHA，而非攜帶完整 URL/raw HTML；SHA 證明位元組一致，不證明語意正確。

## 5. UI ↔ 程式 ↔ 資料 ↔ 來源 Gate 矩陣

| 功能／目標 | 目前 owner 與實作 | 驗證等級 | 未完成／限制 |
|---|---|---|---|
| 來源活動清單擷取 | `show_news.py stage1_fetch_lists` | CODE/CI G4B | 真實來源完整 coverage、部分 stub disabled |
| 多 JSON-LD/詳情來源歸屬 | `event_details.parse_detail` | CODE/CI G5H/R1 | 官方 field Golden 未完成 |
| title/date/location/price/desc | `extract_event_details_simple` + export | CODE/CI dry-run | 欄位真值未獨立驗證 |
| 靜態 JSON 的資料消費 | preview `index.html init()` | UI-DEPLOYED；ANDROID snapshot | 正式動態更新/長期品質 Gate 未通過 |
| 來源／地區／類別／狀態篩選 | `renderChips`, `applyFilters` | CODE/UI-DEPLOYED | 互動 UAT/無障礙另驗 |
| 關鍵字搜尋／50筆分頁 | `#search`, `renderPagination` | CODE/UI-DEPLOYED | 實機大型效能另驗 |
| 詳情/官方跳轉 | `openDetail`, `#m-link` | CODE/UI-DEPLOYED | 來源失效仍可能跳到無效頁 |
| 已讀/關注關鍵字 | localStorage preview keys | CODE/UI-DEPLOYED | 無伺服器同步，通知 disabled |
| PWA 安裝/離線 | manifest | CODE | Service Worker/離線穩定性 NOT-PROVEN |
| 保守隱藏 | `event_visibility.js`, `eventgo_period_gate.js` | ANDROID G5C/D PASS | 只對當時 frozen 快照；G5J 尚未接線 |
| 日期候選辨識 | G5I V1.0.1 | ANDROID PASS | `DATE_UNKNOWN=6548` 是分類非核准 |
| 松山/TixFun 完整 range | G5I-R2 | ANDROID PASS | 125 僅候選，沒有接 PWA |
| 官方 8 GET / 日期訊號 review | G5I-R3A/R3B | ANDROID PASS | 2 個 date signal 未核准；golden=0 |
| 判下架 / SOURCE_GONE | G5J proposed | DESIGN/BLOCK | HTTP 不可直接推論；沒有已驗收引擎 |
| 候選 JSON 正式替換 | G5K proposed | LOCKED | Golden、隔離 QA、回滾、明確授權 |
| 主要雲端排程 | Draft `.github/workflows/event_radar.yml` | CODE/CI candidate | 不在正式 main；不得啟用雙寫 |
| 通知 | V44 Telegram/Termux / Preview UI stub | CODE, default OFF | 無授權勿啟用 |
| 正式完整發布 | PR #1 / commit_data | LOCKED | source truth、R3C/J/K、QA/UAT/PR review |

## 6. 防遺漏：目前真正缺口及優先序

### P0：阻擋資料可信度與正式發布

1. **R3C 官方 Golden 身分及資料真值**：使用既有 8 筆 URL SHA 及 R3B receipts，建立獨立可比對、可審計的頁面/時間/場次證據；人工簽認何者可接受；允許全部 HOLD；不使用 HTTP 200/302 直接判有效／下架。
2. **資料來源完整性**：針對既有 fetchers 計數，收斂 disabled/stub 來源、缺失欄位、分類誤差，標註來源與時間；不得重寫整套採集。
3. **G5J 可逆有效性模型**：`ACTIVE / EXPIRED / NON_EVENT / SOURCE_GONE / ACCESS_UNCERTAIN / DATE_CONFLICT / DATE_UNKNOWN`、來源 SHA/證據日期/reason/source authority/復歸，長期活動保護。
4. **G5K 凍結原始 9850 → 另產候選 JSON → 獨立 PWA 手機 QA**：確認淨增/排除逐筆理由；不直接覆蓋正式 data。
5. **正式發布準備**：唯一 GitHub Actions writer、整合 Gate、Draft PR 審核、授權、回滾、實機讀回。

### P1：可在不阻擋 R3C 的條件下規劃

- PWA 搜尋／篩選／詳細內容多裝置 UAT；time/locale/空結果/可及性。
- Stable event identity（URL 改名／重導向／多場次）與同活動跨來源重複的辨識證據；**未經需求授權不新增 DB**。
- 原始 event_date vs sale_date vs signup deadline 的統一欄位模型、資料完整性趨勢；官方來源內容版本化保留策略與隱私控制。
- 「資料顯示筆數隨今日變化」的凍結測試模式與當日動態模式，避免把 8,233 當永久 KPI。

### P2：治理與效能

- 將本次兩份治理 MD 以獨立 docs-only 發布 Gate 經授權上傳 GitHub；保留本地舊 Gate evidence，不重新下載 5MB 快照。
- 標示 `scraper.py` 與 `show_news.py` 角色；`docs/index.html` 與 Preview `index.html` 角色，避免重複維護。
- CI artifact 保留 7 天的證據保存策略：正式通過的摘要、manifest、SHA 與必要 Golden review 應有可持續追溯位置，不依賴短期 artifact 過期後才發現無證據。

## 7. 精確變更前 Checklist 與安全邊界

1. `Request → Current Owner File/Function → Real runtime entry → Exact data object → Existing Gate/CI → Evidence → Proposed Diff` 完整填寫；先重用，除非客觀缺口才新增。
2. GitHub live: source `main`, PR #1 Draft/head/base, parser Blob, Preview `main`；本地 `~/eventradar`、`~/eventradar_preview_site` branch/HEAD/clean；不一致必須 HOLD。
3. `event_scraper_public/main`、原始 `docs/data.json`、`eventradar-pwa-preview/main` 不得未授權寫入；**禁止 `~/my_project`**。
4. Preflight →（明確允許的）Stage → 授權後 Commit/Push → 遠端 readback；本輪治理文件仍未發布。
5. G5I/R2/R3A/R3B PASS 為永久歷史證據；不得因換對話重新跑全套。只在實質程式變更下做限定回歸。
6. Toolkit 單 ZIP、exact-member SHA256、Bash/Python **實際入口**、正反向 fixtures、壞輸入 Fail-Closed、zip 重新解壓比對；Termux Python 3.13 缺 `tzdata` 不得重犯。
7. 禁止直接貼 Python `from datetime ...` 到 Bash；在 Toolkit Python 檔中更新並從 Bash 啟動入口。
8. 報告 `CODE / CI / ANDROID / GOLDEN / PUBLISHED` 不同狀態，維持文件為唯一整體進度樹，但版本權威以**已正式發布 GitHub 的最新兩 MD**為準；目前候選 MD 不可假冒遠端正式版本。

## 8. 檔案及 URL 來源

- [Preview 真正 UI `index.html`](https://github.com/easonliu714/eventradar-pwa-preview/blob/a8cde084ab5581736d86094d8cdcc2cdc9963000/index.html)
- [Preview G5C `event_visibility.js`](https://github.com/easonliu714/eventradar-pwa-preview/blob/a8cde084ab5581736d86094d8cdcc2cdc9963000/event_visibility.js)
- [Preview G5D `eventgo_period_gate.js`](https://github.com/easonliu714/eventradar-pwa-preview/blob/a8cde084ab5581736d86094d8cdcc2cdc9963000/eventgo_period_gate.js)
- [V44 source `show_news.py`](https://github.com/easonliu714/event_scraper_public/blob/26888422e48634d9729d2deea67b7996a5d1e4ee/show_news.py)
- [G5H `event_details.py`](https://github.com/easonliu714/event_scraper_public/blob/26888422e48634d9729d2deea67b7996a5d1e4ee/event_details.py)
- [PR cloud schedule candidate](https://github.com/easonliu714/event_scraper_public/blob/26888422e48634d9729d2deea67b7996a5d1e4ee/.github/workflows/event_radar.yml)
- [PR1 preview snapshot exporter](https://github.com/easonliu714/event_scraper_public/blob/26888422e48634d9729d2deea67b7996a5d1e4ee/scripts/pr1_preview_snapshot.py)
- [Source `main` historical UI](https://github.com/easonliu714/event_scraper_public/blob/6004754f90d551cdb0cdb91a3e04b42c04f45f48/docs/index.html)
- [Draft PR #1](https://github.com/easonliu714/event_scraper_public/pull/1)

**End-state**：先完成來源證據／日期真值，再完成保守有效性及候選 PWA 驗收，最後正式發布。沒有理由重新搭建既有 PWA、另寫一套爬蟲或把手機改成正式排程。

## 9. 2026-10-24 R3C 增量與實作邊界

```text
G5I-R3C Golden contract / local evidence consumer [ANDROID OFFLINE PASS; OFFICIAL GOLDEN HOLD]
├── run.sh → r3c.py (synthetic positives/negatives + GH/Termux Git authority)
├── R3A upstream exact SHA → R3B receipts URL SHA/platform/identity cross-link [ANDROID PASS]
├── evidence/2026-10-23_r3c_offline [CREATE-ONLY, NO AUTO HIDE]
└── official HTML / true Golden / independent signoff [HOLD, no new GET]
```

本工具不改 `show_news.py`、`event_details.py`、PWA `index.html`、`data.json`、原有 G5C/G5D visibility filter 或任何 Actions schedule。此文件尚未正式 GitHub 發布，不能宣稱 remote 本版已生效。

## 11. 2026-10-24 R3C Android Offline / Evidence Lineage 實測（最新優先）

```text
G5I-R3C V1.0.0 (Termux)
├── --selftest                  [ANDROID PASS; 4 positive + 26 negative]
├── --preflight                 [ANDROID PASS; source/preview Git clean+SHA+blob+data; GitHub Draft PR]
├── --audit-evidence            [ANDROID PASS; exact 6 upstream input paths]
│   ├── R3A 4 input SHA         [PASS]
│   ├── R3B 8 records/2:4:2    [PASS]
│   ├── 8 URL hash/platform/id  [PASS]
│   ├── create-only receipts    [PASS; evidence/2026-10-23_r3c_offline]
│   └── audit exit             [0]
├── official raw HTML          [NOT CAPTURED IN R3A; HOLD]
├── independent Golden signoff [HOLD; accepted=0]
├── auto-hide                  [0; unchanged]
└── published                  [false; no PWA/data.json changes]
```

- R3C 從現有 R3A/R3B 只讀證據出發，沒有重跑 G1～R3B、未呼叫新的活動網站 HTTP、未變更既有 `show_news.py`、`event_details.py`、PWA、`data.json` 或自動排程。
- HTTP 200、重新導向、JSON-LD 日期訊號皆不能當作有效性或到期下架的直接真值；沒有原始來源 SHA/場次語義及獨立人工簽認就維持 `GOLDEN HOLD`。
- 實機固定權威：source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`、PR #1 head `26888422e48634d9729d2deea67b7996a5d1e4ee`、preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`、parser blob `ed425662b4f2ce2032a0fa0c3e83075842f30767`。
- 治理文件仍**未**進入 GitHub：docs-only branch 嘗試因 connector 缺少 Git refs 建立權限而被 403 擋下；未 Commit/Push，須後續以受權方式完成獨立分支與 readback。不得把本地候選文件宣稱為 main 正式權威。


## 2026-10-24 R3C-O1 官方原始來源 Evidence 延伸樹（未部署、未 GitHub 發布）

```text
Android Termux（隔離 Toolkit；非正式服務）
└── ~/eventradar_toolkit/gates/g5i_r3c_official_raw_v100/ [TOOLKIT BUILT / ANDROID PENDING]
    ├── run.sh [ENTRYPOINT; --selftest / --preflight / --capture / --verify]
    ├── capture.py [本地 one-shot 八來源原始內容取證；不可觸及主程式或 PWA]
    │   ├── R3C 已 PASS 來源權威檢查 + 八筆 lineage 的 pinned SHA [DEPENDENCY]
    │   ├── R3A targets.jsonl → 8 筆原始 URL；不接受新 URL [EXACT INPUT]
    │   ├── 同源 HTTPS GET / public DNS / no-proxy / no-redirect / no-retry [BOUNDED]
    │   ├── 每 URL create-only attempts / receipts / raw .html / SHA256 [AUDIT ONLY]
    │   ├── 日期候選訊號（JSON-LD / meta）≠ 官方真值 [HINTS ONLY]
    │   └── Golden accepted=0 / auto_hidden=0 / published=false [FROZEN]
    └── evidence/2026-10-24_r3c_o1_official_raw/ [CREATE ON REAL CAPTURE ONLY]
        ├── capture_plan.json / attempt_started.json
        ├── 01..08_<URL_SHA_PREFIX>.attempt.json [PERMANENT NO-RETRY RESERVATION]
        ├── 01..08_<URL_SHA_PREFIX>.receipt.json [HTTP + BODY SHA + date hints]
        ├── 01..08_<URL_SHA_PREFIX>.html [ONLY IF CAPTURED; PRIVATE 0600]
        └── capture_summary.json [GOLDEN HOLD; NOT PWA DECISION]
```

- 這是已存在系統旁的隔離稽核工具，**不是**新的爬蟲、DB、PWA、正式 API、永久排程或正式資料寫入器；未授權 merge / publish。
- 此文件為本地候選，尚未發布 GitHub。Github 兩份治理文件須另行以 docs-only exact-two-path 且有權限之分支、Draft PR、獨立讀回發布。

## 2026-10-24 R3C-O1 V1.0.1 取證 URL Recovery 修復（候選，未 Android 驗收）

```text
R3C-O1 V1.0.1  [NEW TOOLKIT; PRE-CAPTURE NO OFFICIAL GET]
├── R3A targets.jsonl [EXACT PINNED SHA; 8 URL hashes]
├── R3A official_probe receipts / R3B reviews [EXACT SHA & ID lineage]
├── Preview data.json [SHA-LOCKED 9850; READONLY MATCH]  ─┐
│   └── url UTF-8 SHA256 exact match (8/8 & platform) ───┤
├── R3C original lineage receipts [EXACT 8 URL hashes] ───┘
├── V100 attempt ledger guard [NO RETRY ACROSS VERSION]
├── no URL found / multiple distinct URLs / platform conflict -> HOLD
└── after preflight PASS, bounded explicit-authorized GET only [GOLDEN HOLD]
```

- V1.0.0 Android Selftest/Authority PASS but URL payload assumption caused early Preflight HOLD。沒有新 GET；禁止重跑 G1～R3B。
- V1.0.1 不更動 show_news.py、event_details.py、GitHub Actions、PWA、正式 data.json、既有 display filters 或其他 Gate。治理文件尚未發布 GitHub。

## G5I-R3C-O1 / O2 supplemental architecture (2026-10-24 evidence append)

```text
Termux existing G5I-R3A/R3B/R3C evidence [ANDROID PASS; don't rerun]
  └── G5I-R3C-O1 v1.0.1 original official GET ledger [ANDROID PASS; one-shot]
        ├── eight .attempt.json / eight .receipt.json [SHA readback PASS]
        ├── six raw .html (ACCUPASS/KidsClub/OPENTIX) [stored locally, private]
        └── two BeClass HTTP 302 [ACCESS_UNCERTAIN; no follow]
               └── G5I-R3C-O2 offline_review_v100 [toolkit candidate / Android not yet verified]
                     ├── imports pinned O1 verify() in read-only mode
                     ├── original raw SHA/date role hints, no event-site GET
                     ├── output redacted eight receipt rows, summary + review.md, create-only
                     └── Golden signoff HOLD; no writes to data.json or PWA
```

Production code owner remains `show_news.py` and `event_details.py` on Draft PR #1. O2 is **not a replacement parser or a new scrape service**. The mobile PWA continues to rely on G5C/G5D reversible filtering; O2 date candidates must **not** feed PWA visibility until the separately authorized G5J/G5K Gates. Both governance docs remain unpublished GitHub candidates until exact-file docs-only readback.

## 2026-10-24 G5I-R3C-O2 Android PASS → O3 Pre-Signoff Gap Matrix

```text
R3C O1 v1.0.1 [ANDROID PASS; 8 ONE-SHOT GET COMPLETED; NEVER RE-CAPTURE]
   ├── raw HTML 6 / URL-bound SHA 6 [VERIFIED]
   └── BeClass HTTP302 ×2 [REDIRECT NOT FOLLOWED]
       ↓ only offline evidence, source SHA locked
R3C O2 v1.0.0 [ANDROID PASS; --audit, --verify, CREATE-ONLY]
   ├── evidence/.../summary.json
   ├── evidence/.../review_receipts.jsonl [8 rows]
   └── evidence/.../review.md
       ↓ O3 pinned O2 SHA + O2 --verify readback (no event-site GET)
R3C O3 v1.0.0 [NEW LOCAL TOOLKIT; ANDROID NOT YET VERIFIED]
   ├── summary.json [upstream exact SHA & review queue counts]
   ├── decision_matrix.jsonl [8 event URL SHA; date category; all HOLD]
   └── review_worklist.md [independent human Golden signoff gaps]
       └── Golden signoff remains HOLD/0; G5J/G5K blocked until confirmed
```

O3 is an offline derived review aid, not a crawler, API, scheduler, database, PWA update, or published decision engine. Production Source main / PR Draft / preview data.json frozen. Governance docs remain GitHub-unpublished candidates due write connector 403.


## 2026-10-24 補充：R3C-O3 Android PASS 與 O4 資料／介面層

```
Android Termux ~/eventradar_toolkit/gates/
├── g5i_r3c_official_raw_v101/
│   └── evidence/2026-10-24_r3c_o1_v101_official_raw/
│       ├── capture_plan.json           [已保存；不可覆寫]
│       ├── capture_summary.json        [已保存；不可覆寫]
│       ├── 8 × *.receipt.json          [SHA readback PASS]
│       └── 6 × *.html                  [SHA readback PASS；另 2 筆 302 不跟隨]
├── g5i_r3c_o2_offline_review_v100/
│   └── evidence/2026-10-24_r3c_o2_offline_review/ [PASS]
│       └── review_receipts.jsonl        [歷史格式：多行 JSON 物件連接]
├── g5i_r3c_o3_review_matrix_v100/
│   └── evidence/2026-10-24_r3c_o3_signoff_gap_matrix/ [Android PASS]
│       ├── summary.json
│       ├── decision_matrix.jsonl       [標準單行 JSONL ×8]
│       └── review_worklist.md
└── g5i_r3c_o4_identity_semantics_v100/ [候選；需 Android Gate]
    ├── o4_identity.py                  [僅讀 O1/O3，檢查 Event 身分及欄位]
    ├── run.sh                          [--selftest|--preflight|--audit|--verify]
    └── evidence/2026-10-24_r3c_o4_identity_semantics/
        ├── summary.json               [Create-Only]
        ├── identity_semantics.jsonl    [8 筆，無原文 HTML / URL / 標題]
        └── manual_review.md           [待人工簽認；不是 Golden]
```

O3 Android 實機 `PASS R3C_O3_ANDROID_AUDIT_AND_READBACK` 與 `POSITIVE=15 NEGATIVE=16` 均已見 Console。O4 新增同 JSON-LD `Event.startDate/endDate` 配對、`Event.url/@id` 精確 SHA 同源判別、`subEvent` 最晚日期候選、`offers.validThrough` 作售票候選分離。這些欄位**沒有任一項單獨構成官方排程真值**。O4 不重新 GET、不修改既有 O1～O3；PWA 搜尋及 G5C/G5D 過濾層不變。

GitHub main/PR1/Preview main 分別仍為 `6004754f90d551cdb0cdb91a3e04b42c04f45f48` / `26888422e48634d9729d2deea67b7996a5d1e4ee` Draft / `a8cde084ab5581736d86094d8cdcc2cdc9963000`。本段落為**本地治理候選**，非 GitHub 已發布版本；先前 GitHub create_branch 403 權限限制仍需處理，禁止假裝已發布或改 main。


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

### UI / API / Data Tree 補充（規格提案；現況非已部署）

```text
EventRadar data.json [正式結構維持不變]
└── G5I source-evidence overlay [Android local, tested O1–O6]
    ├── verified event identity / start / end / timezone [#1 screenshot corroborated; no Golden yet]
    ├── source page type
    │   ├── SINGLE_EVENT / SINGLE_PERFORMANCE [candidate]
    │   └── SPECIAL_ELIGIBILITY_TICKET_PORTAL [#8 observed, candidate]
    ├── ticket availability [UNKNOWN default]
    │   ├── SOLD_OUT_OBSERVED [must scope to specific performance, ticket type, URL, observed time]
    │   ├── REGISTRATION_CLOSED_OBSERVED [only if explicit official proof]
    │   └── UNKNOWN [do not infer from URL, clock timer or registration button]
    └── official event URL + optional separately verified related-performance URL
        └── exact source/event mapping mandatory before dedup / visibility decisions

PWA G5C/G5D [EXISTING, do not rebuild]
└── G5J/G5K requested behavior [PROPOSED, NOT IMPLEMENTED]
    ├── activity date shown independently of live ticket availability
    ├── when availability UNKNOWN: `查看官方最新票況` → original official link
    ├── badge/filter for eligibility-restricted ticket portals (without presuming user eligibility)
    └── no irreversible deletion, no auto-expiry from special portal last observed session
```

**證據語意**：`HUMAN_SCREEN_DATE_CORROBORATED` 與 `HUMAN_SCREEN_PORTAL_TYPE_CORROBORATED` 僅是審查備註，**不得誤寫成正式系統已存在的 enum 值或已發布 schema 欄位**。上述樹狀欄位皆屬後續決策/實作候選，不改現有 data.json。


## 2026-10-24 SRC-P1 SOURCE / API / DATA 增量（候選）

- 使用者於 2026-10-24 授權將 **各平台資訊取得品質** 調整為近期 P0 第一優先；保留既定 Roadmap `G5I → G5J → G5K → 發布`，SRC-P1 是 G5I/來源品質的新增實作支線，不代表啟動 G5J 自動失效決策。
- 來源固定：Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`；PR #1 Draft HEAD `26888422e48634d9729d2deea67b7996a5d1e4ee`；Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000`；Parser Git blob `ed425662b4f2ce2032a0fa0c3e83075842f30767`。
- 真實代碼檢查：`show_news.py` 是運作程式，`event_details.py` 是既有 parser；禁止建立平行爬蟲、第二 parser、新資料庫。
- SRC-P1 候選：`fetch_accupass_events_list()` 增加同平台絕對網址精確辨識；`fetch_text()` 修正 UTF-8 ignore 破壞 Big5 的風險；`fetch_opentix_events_list()` 為特殊資格集合標識來源角色；`fetch_kidsclub_events_list()` 將課程／商品列表保留為未核驗目錄；`extract_event_details_simple()` 與 `parse_detail()` 只增加來源角色及 `ticket_availability=UNKNOWN`，阻止特殊資格專區以其中場次日期推定整站過期。
- 本次只交付 **隔離候選完整程式與 diff**、正反向 QA、Termux preflight；不修改 Android Source Git 工作樹、不 Stage/Commit/Push/Merge、不重跑 O1 的八筆 GET、不改 PWA/data.json/排程。Android 實機未回報前 **SRC-P1=HOLD（候選）**。
- 後續階段：逐平台取得方式與欄位缺漏率比較（OPENTIX、ACCUPASS、BeClass、KidsClub → KKTIX、拓元、FamiTicket、TixFun 等），用限制筆數、限定來源的 Wi-Fi/行動網路對照作補充證據；HTTP 200/302/售完按鈕不直接當成 Golden 或活動有效性。
- 治理文件依然是 **GitHub 尚未發布的本地候選**；既有 403 寫入限制未解除，不能聲稱已發布。


## 2026-10-24 來源擷取 A/B 增量架構（候選，尚未發布 GitHub）

```text
SRC-P1 [Android PASS, isolated candidate only]
  ├─ candidate_source/show_news.py (原既有函數精確增量)
  ├─ candidate_source/event_details.py (G5H相容、角色與身分保守標記)
  └─ platform_quality_baseline.md (凍結9,850筆；僅欄位存在率)
SRC-P2 [Android待驗]
  ├─ --audit-offline [O1 已封存6份HTML/2筆302, original vs P1 candidate, no GET]
  ├─ --verify-offline [create-only SHA reread]
  ├─ --capture-live [最多四次官方列表GET, 顯式授權, no retry/redirect]
  └─ --verify-live [recompute raw SHA, no GET]
主系統 / show_news.py / event_details.py / 正式data.json / Preview PWA [FROZEN]
```

來源優先缺口：BeClass 4,472筆（Date 1）；ACCUPASS 733筆（核心欄位全0）；OPENTIX 2,535筆（Price 242）；台北世貿 586筆（Date/Location/Price 0）。

`available_tickets` 未確認維持 `UNKNOWN`；HTTP200、302、售票日期、商品/專區日期均不得直接驅動下架或 Golden；不用平行 DB/PWA。


## 2026-10-24 SRC-P2 Android 實機 PASS 與 SRC-P3 續作（候選文件，未上傳 GitHub）

- SRC-P1：完整候選源碼與 9,850 筆存在率基線，Android selftest/preflight/build/verify PASS；未修改工作樹。
- SRC-P2：Wi-Fi 真實四個官方列表 GET（ACCUPASS=200、OPENTIX=200、BECLASS=302、KIDSCLUB=200）與封存證據讀回 PASS；兩個來源解析器對 O1 六份 HTML 的 date/location/price/description 存在率未改善。
- SRC-P2 用戶證據：四筆一次性 GET Ledger 與三份 raw HTML 已保存，**禁止再次執行 capture-live**。三筆 HTTP200 ≠ 已驗證來源內容；BeClass 302 ≠ 零活動。
- SRC-P3：只讀 SRC-P2 封存 HTML 與 P1 候選程式的來源 URL／DOM 選擇器差距矩陣，不重新 GET、不修改正式 main/Draft PR/PWA/data.json。利用實機真實列表結果優先排序 platform fetch 函數修復。
- Android 本地 Git Branch／HEAD／Clean 由 SRC-P2 原本的唯讀權威入口重新驗證；GitHub 遠端來源 HEAD 仍需每輪重新核對。
- Golden=0、AutoHidden=0、Published=false；下架證據 G5J 與 PWA UAT G5K 不提前發布。
- GitHub 對 docs-only 建分支先前回覆 403，兩份治理 MD 仍為**未發布候選**；不得宣稱已成為 Repo 權威。

## 2026-10-24 SRC-P4 資訊取得品質候選增量（未上 GitHub）

```text
EventRadar Source main@6004754 (FROZEN)
└── PR #1@2688842 (DRAFT, FROZEN)
    ├── show_news.py [既有唯一抓取入口；P4 僅生成完整候選]
    │   ├── fetch_accupass_events_list [P3 實機：舊→新 25→25，增量0，不重複修改]
    │   ├── fetch_opentix_events_list [P1 標示特殊資格集合，P4 沿用]
    │   └── extract_event_details_simple [P4 保留 source_time_role / 票況UNKNOWN]
    └── event_details.py [既有唯一詳頁 Parser；P4 完整候選]
        └── extract_source_time_roles [新增：ACCUPASS ISO 起迄時間候選；OPENTIX 跨節目場次候選]

Termux Toolkit / eventradar_src_p4_detail_upgrade_v100 (isolated)
├── --selftest [合成正反向；無網路]
├── --preflight [官方 repo SHA + Android 本地 Root/HEAD/Branch/Clean]
├── --build [既有 O1 六份 HTML / 兩筆302，P1 vs P4 真實離線 A/B]
└── --verify [重算完整候選、Diff、比較結果之 SHA；無 GET]

PWA Preview/data.json [FROZEN；不得改寫]
GitHub 治理 MD [本地候選，遠端 403 HOLD]
```

- 新時間與場次欄位僅為 `candidate`，**未驗證、未部署、非 Golden**，不得擴張成售完、過期、可預約、特殊票種對一般民眾均適用。
- P4 輸出 `candidate_source/show_news.py`、`candidate_source/event_details.py`、`diff_vs_frozen_pr`、`diff_vs_src_p1` 與八筆比對證據；不新增第二套爬蟲、資料庫或 PWA。


---

## 2026-10-24 SRC-P4 Android PASS → SRC-P5 BeClass mobile one-GET diagnosis (unpublished candidate)

- SRC-P4 Termux `--build` / `--verify` PASS; P1→P4 ACCUPASS complete timestamps 0→2, OPENTIX special collection session candidates 0→8; core Date/Location/Price/Description unchanged, BeClass stays 302, KidsClub still unknown. Candidate only, source tree unchanged.
- SRC-P5 is scoped to P2's **exact same BeClass ShowRegist listing URL**, cellular user-attested once (not a P2 retry), to compare response status and redacted Location. Must verify P2 Wi-Fi receipt SHA and GitHub/local frozen HEAD first, then create-only attempt prior to GET. No redirects, retry, cookies or challenge bypass.
- If 200, record only candidate rid-link count, not activity truth; if 302, retain ACCESS_UNCERTAIN. Do not assume mobile transport from the script, rely on user network-setting confirmation.
- Golden=0, auto_hidden=0, published=false. No production data, PWA, main, or Draft PR #1 mutation. Two governance documents remain local candidates: GitHub docs-only publication was previously blocked by 403, no branch/commit/push.
- Following P5: use actual redirect evidence to repair `fetch_beclass_events_list()` / `extract_event_details_simple()` in **candidate code**, then test on pinned samples and only request further live retrieval if necessary.

## 2026-10-24 SRC-P5/P6 platform acquisition delta (local candidate; NOT GITHUB PUBLISHED)

```text
Source acquisition / show_news.py [PR1 Draft, unchanged]
  fetch_beclass_events_list() [production currently follows HTTP redirects]
    legacy ShowRegist list + /rid= anchor extraction [implemented]
    mobile 302 to /m/default.php verified by P5 Location SHA [Android receipt PASS]
    SRC-P6 same-host one-hop guarded redirect [candidate, offline tests only]
    SRC-P6 strict official rid candidate filtering [candidate, offline tests only]
    SRC-P6 explicit 活動日期 field candidate [candidate, NOT authoritative]
    SRC-P6 exact pinned mobile final landing 1 GET [optional, Android pending]
  extract_event_details_simple() [production existing; data-field improvement pending]
    BeClass event date/location/price [not validated using real page HTML]
    historical 4472-row repair [NOT executed]
  SRC-P4 ACCUPASS 2 complete start/end times and OPENTIX 8 session
    candidate fields [Android PASS, NOT DEPLOYED]
Storage
  docs/data.json [untouched; frozen baseline 9850]
  Toolkit evidence/P5 [CREATE_ONLY, 302 SHA, PASS]
  Toolkit evidence/P6 [pending, CREATE_ONLY]
Frontend
  PWA UI [unchanged]; ticket availability UNKNOWN when unproven
Governance
  Source SHA and Preview SHA stable; GitHub governance docs publication HOLD 403
  Golden=0; AUTO_HIDDEN=0; PUBLISHED=false; PR1 Draft
```

## 2026-10-24 SRC-P6 Android PASS → SRC-P7 BeClass RID functional remediation (local, NOT GitHub published)

- SRC-P6 Android `--build`, `--verify`, one-shot Wi-Fi `--capture-mobile-listing`, `--verify-live`: PASS. SHA-verified HTTP200, raw 19,745 bytes SHA `834196a704703eef935a6d4c62375fb1d1510a2bcad3b7dc5a2671550dd99631`; 20 `rid=` anchors, but `strict_distinct_rid_urls=0` and no verified title. All prior P1–P6 Android PASS retained; do not rerun captures or replace attempt ledgers.
- Root discrepancy: SRC-P6 `beclass_rid_url()` accepts only strict direct `/rid=<16..28 hex>` while live mobile HTML has 20 apparent rid anchors. Exact shapes of raw hrefs must be derived **offline** from the private P6 snapshot; don't assume all are real events.
- SRC-P7 reconstructs a full *candidate* `show_news.py` with source-safe BeClass rid canonicalization, same-card title heuristics and source-role conservative handling. Reads exactly the P6 sealed HTML locally, compares normalized/titled candidate counts to P6 0; emits sanitized aggregates, full candidate, diff and SHA-verifiable output. Never exports raw HTML/URLs/titles. No HTTP GET, no source worktree write, no official data/PWA change, no Golden approvals, no auto hide.
- If candidate counts are zero, preserve HOLD and use aggregated href shape classification to fix exact false-negative. A positive count is parsing coverage only and is NOT correctness or Golden acceptance. Next: subject to real result, address BeClass detail-date extraction and bounded update/UAT, OPENTIX & KidsClub remain P0 source quality tasks.
- GitHub authority remains source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`, PR #1 Draft `26888422e48634d9729d2deea67b7996a5d1e4ee`, preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000` as checked this turn. Governance docs are local candidate; GitHub write 403 HOLD. No merge/close/push/commit/deploy.

### 2026-10-24 SRC-P7 verified / SRC-P8 detail roles (candidate)
- `show_news.py → fetch_beclass_events_list`: SRC-P7 Android PASS 20/20 safe official `/m/rid=...` URL candidates, 20 attributable anchor titles from P6 frozen source. Full function remains candidate; not merged/published.
- `show_news.py → extract_event_details_simple → beclass_detail_roles` (SRC-P8 candidate): explicitly labeled event-date and location role extraction, ambiguity exclusion, registration availability `UNKNOWN`, two once-only source-bound detail GETs for factual UAT; don't infer date from signup deadline.
- DB/PWA/Actions: unchanged, `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`; remote docs publication HOLD.


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

### 2026-10-24 SRC-P8 V102 official two-detail evidence -> SRC-P9 field-role candidate
- `show_news.py > extract_event_details_simple > beclass_detail_roles()` candidate P8 V102 has been Android validated on two real SHA-bound private HTML responses (HTTP 200 each): date present 1/2, location present 0/2, title present 2/2. P8 candidate not merged to GitHub/PWA.
- SRC-P9 offline candidate upgrades only the existing BeClass helper: short explicit date headings and adjacent date, source-scoped location labels including "活動地點資訊" block, no private form field capture, reject ambiguous values; compare actual retained evidence by field presence/hashes, not activity truth. No new HTTP GET and no update to `docs/data.json`.
- P1-P8 verified historical gates immutable, Golden=0, Auto-hide=0, Published=false; official GitHub governance publication HOLD.

## 2026-10-24 SRC-P9 Android evidence and SRC-P10 integration mapping (local governance candidate, NOT remote)

```text
Draft PR #1 actual Python runtime `show_news.py` + `event_details.py` (NOT scraper.py)
├── Existing list fetch functions [P7 candidate integrated]
│   └── fetch_beclass_events_list [P6 mobile-landing guarded; P7 safe RID normalize + title]
│       └── P6 stored HTML: 20 RID anchors -> P7: 20 normalized URL/20 titles [ANDROID PASS, UNVERIFIED EVENT TRUTH]
├── Existing detail parser call-chain [P1/P4/P8/P9 candidate integrated]
│   ├── P1 scoped source-page types and special-ticket collection guard
│   ├── P4 timestamp candidates ACCUPASS (2/2 O1), multi-event OPENTIX (8 sessions), NOT stock
│   ├── P8 BeClass explicit event date/short place labels [ANDROID PASS]
│   └── P9 BeClass bounded DOM block and adjacent date [ANDROID PASS]
│       └── P8 2 detail pages: date 1/2 unchanged; location 0/2 -> 1/2; page2 location conflict HOLD
└── Existing `event_details.py` parse_detail [P1 scoped JSONLD + P4 source_time roles]

Saved data / API / UI
├── Frozen preview data.json [9,850 snapshot, SHA-locked, NOT edited]
├── Draft PR #1 Actions and writer [NOT enabled on default main; DRAFT UNMERGED]
├── Preview UI [no update; frozen]
└── Production publish, Golden status, auto-hide [LOCKED]
```

Source integration deliverable is **only two candidate Python source files plus exact diff** in the P10 create-only evidence, not a second crawler or a deployment. Future G5J (expiry evidence) and G5K (isolated preview UAT) remain open. Remote GitHub governance documents **not published** (earlier integration 403).

## 2026-10-24 SRC-P10/P11 已驗證功能與待驗 UAT（本地增量；非遠端發布）

```text
EventRadar / 已驗 Android 候選來源架構
├── show_news.py [SRC-P10 ANDROID PASS; NOT DEPLOYED]
│   ├── ACCUPASS P4: 單一 Event 身分下起訖時間候選 [2/2; GOLDEN HOLD]
│   ├── OPENTIX P4: 特殊資格多節目場次候選 [8 slots; GOLDEN HOLD]
│   ├── BeClass P7: 20/20 手機列表 RID URL + 標題 [CANDIDATE; GOLDEN HOLD]
│   └── BeClass P8/P9: 詳頁日期 1/2、地點 1/2 [ANDROID PASS; 人工 UAT HOLD]
├── event_details.py [SRC-P10 ANDROID PASS; NOT DEPLOYED]
│   └── P1 身分保護 + P4 時間來源角色 [既有 G5H Regression PASS]
├── 資料/證據層 [PRIVATE_ANDROID_ONLY]
│   ├── P6 一筆 HTTP 200 手機版列表 HTML SHA 封存
│   ├── P8 V102 兩筆 HTTP 200 詳頁 HTML SHA 封存
│   └── SRC-P11 欄位 UAT [PLANNED / Android 尚未通過]
│       ├── PRIVATE：手機本地候選標題、日期、地點，禁止貼上傳
│       ├── REDACTED：只有 SHA/來源角色/核對狀態，可回傳
│       └── GOLDEN=0, AUTO_HIDDEN=0, PUBLISHED=false
└── 發布層 [LOCKED]
    ├── GitHub PR / CI source merge [需授權；Draft PR #1 未合併]
    ├── 4,472 BeClass 歷史資料批次修補 [未執行]
    └── PWA / data.json / schedule / notification [未授權、不變]
```


## 2026-10-24 SRC-P11 實機 UAT 佐證與多選項來源展示架構（候選，非 GitHub 已發布）

```text
現有 eventradar-pwa-preview/index.html [Git Blob c11c6532...; 未修改]
├── 列表 #result-count / #update-time / .disclaimer [CODE; 改既有文案即可]
│   └── NEW CANDIDATE: 「活動資訊僅供參考，請以官方網站及主辦單位最新公告為準」
├── 詳情 #detail-modal [CODE]
│   ├── #m-date：主標示日 / 多場次提示 / 缺值導向官方 [PROPOSED, NOT IMPLEMENTED]
│   ├── #m-location：地點層級或線上/實體選項；衝突不隨意選唯一地址 [PROPOSED]
│   ├── #m-price：按票種及資格而異，無證據不直接寫「免費」 [PROPOSED]
│   ├── #m-desc：已有摘要，禁止混入報名表個資/銀行資料 [PROPOSED GOVERNANCE]
│   └── #m-link：保留官方詳情跳轉 [EXISTING CODE]
└── 仍只讀正式凍結 data.json，不寫入、不更新 PWA [LOCKED]

既有 P10 source candidate [ANDROID PASS, NOT MERGED]
├── BeClass P7: 20/20 RID URL 和標題 [PASS; 來源候選]
├── BeClass P8/P9/P11: 封存 2 筆，date 1/2, location 1/2, title 2/2 [PASS]
├── 人工官網截圖: A 有「課程日期」(P11 漏抓); B 10/26 及內文 10/25~26 不必然矛盾
└── 建議角色：SOURCE_OBSERVED / MULTI_SESSION / MULTI_OPTION / NEEDS_REVIEW
    └── UNKNOWN 和 CONFLICT 不代表活動不存在或需隱藏
```

- **政策分層**：顯示「來源彙整參考」與 Golden/正式資料寫入是兩種獨立 Gate；人工來源截圖可佐證而非替代原始 HTML SHA 或正式核准證據。既有 P11 `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false` 不變。
- **原本就有免責**：Preview `index.html` Line116 `.disclaimer` 為 `⚠️ 活動列表僅供參考，活動內容以各平台資訊為準。`；**原地改善，不新建重複區塊**。現有 #m-date/#m-location/#m-price 缺值顯示 `詳內文`；可改為清晰的「請見官方」語意，但必須另經 PWA UI 候選驗證。
- BeClass 實機 UAT 已提供 A/B 兩筆活動人工畫面佐證；不要上傳金融收款資料、私人報名欄位。詳見本地 `SRC_P11_UAT_DISPLAY_POLICY.md`；尚未修改任一受保護原始碼。


## 2026-10-24 SRC-P12 實作候選架構（尚未部署）

```text
Preview index.html (原 SHA Git Blob c11c6532...；frozen HEAD a8cde084...)
├── .disclaimer [既有，原位換文，不重複 banner]
├── #detail-modal [既有]
│   ├── #m-date / #m-location / #m-price [缺值更清楚，保留既有有值]
│   │   └── referenceFieldText(ev, field) [候選輔助；可選 display_roles]
│   ├── #m-link [保留既有官方站連結]
│   └── #m-source-note [新加簡短字級完整免責聲明]
├── allEvents + filter/search + favorites + pagination [未改]
└── data.json [9,850 frozen, 完全未寫]

P10 show_news.py (精確 SHA 綁定；現行 Draft PR 本體仍不改)
└── beclass_detail_roles(html_text) [原函數定點修補]
    ├── 原 P9 活動日期/活動地點標籤與 conflict HOLD [保留]
    ├── SRC-P12 明確課程日期、上課日期；ROC 民國年→公元候選 [NEW]
    ├── additional_session_role [非單值，僅來源提示，NEEDS_REVIEW]
    └── price_option_role [只有條件提示，票價/票況仍不推定]

P10 event_details.py [來源 SHA 原封不動，不重建 parser]
P11 P8 HTML 兩筆 [唯讀 SHA 受保護，無重複 GET]
P12 candidate output [新的 evidence/p12_source_ui_candidate_v100，Create-Only、SHA 重算]
```

- 「官方來源有數值但解析器缺」與「來源有多個合法場次／價格」是兩種不同情況。顯示參考資訊的 UAT ≠ 資料 Golden 簽認 ≠ 正式發布。
- 兩份正式治理文件 GitHub 仍為未發布候選；不得在沒有權限或授權下自行推送。


## 2026-10-24 — SRC-P12 Android PASS / SRC-P13 candidate (local, not GitHub published)

- SRC-P12 Android: `--selftest`, `--preflight`, `--build`, `--verify` PASS; PWA display contract candidate PASS. First BeClass class-date **still UNKNOWN**, so course-date capture improvement HOLD. Second date remains present, conflicting venue remains HOLD. `GOLDEN=0 AUTO_HIDDEN=0 PUBLISHED=false`.
- SRC-P13 V1.0.0: bounded BeClass adjacent DOM label/date parser **candidate**, based on exact P12 `show_news.py` SHA `1c2eded2999cb28ce8e635d360e80bfb84841a4150311c34e62b49e2e5a8e155`. P12 Preview SHA `802168998ad83d1155e8c010f83205b3229722e2b7bf60ceb6b35aafdf36137a` immutable; parser `event_details.py` SHA `2cac084b2ad0ed28baf1e98388e3686746d83d06e2403f586e85ee1484d38595` immutable.
- SRC-P13 requires offline Android AB on P11's two previously archived official details; no new HTTP GET or historic data overwrite; no new branch or PR merge. Real AB may show zero gain, and must not be mislabeled PASS for source quality.
- Pending: UI isolated preview/manual UAT, PR source review/authorization, two governance docs official GitHub publication (previous 403), then G5J/G5K. Previously passed Android Gates remain frozen.

## 2026-10-24 SRC-P14 UI isolated UAT addendum (本地候選／遠端治理未發布)

```text
Preview PWA index.html [GitHub main a8cde... ; unchanged]
├── Disclaimer / main list [P12 candidate; Android Build+Verify PASS]
├── Detail modal
│   ├── date / location / price base field [EXISTING]
│   ├── display_roles opt-in : MULTI_SESSION | MULTI_LOCATION | HYBRID | CONDITIONAL_PRICE
│   │   └── [SRC-P12 static candidate; SRC-P14 synthetic browser UAT PENDING]
│   ├── official source CTA [EXISTING; disabled ONLY in local synthetic UAT copy]
│   └── official source disclaimer [P12 candidate; visual UAT PENDING]
├── event_visibility.js (G5C) [Git blob pinned, unchanged]
├── eventgo_period_gate.js (G5D) [Git blob pinned, unchanged]
├── data.json [9,850 formal frozen snapshot; must NOT change]
└── localhost 127.0.0.1:18766 [SRC-P14 ephemeral isolated synthetic UI]
    ├── site/index.html [P12 candidate plus explicit UAT-only noindex/notice/no-outlink]
    ├── site/data.json [NINE SYNTHETIC RECORDS, NOT REAL]
    └── static G5C/G5D JS [pinned to Preview Git Blob]

Source show_news.py [P13 candidate Android PASS; date 1/2 → 2/2; still not published]
Source event_details.py [P10 SHA unchanged]
PR #1 [OPEN DRAFT; merge unauthorized]
```


## 2026-10-24 SRC-P14 實機列表驗收與 SRC-P15 卡片摘要候選（本地治理增量，未發布）

- SRC-P14 Android：Toolkit Selftest/Preflight/Build/Verify PASS；`127.0.0.1:18766` `index.html`、G5C/G5D JS、9 筆合成 `data.json` HTTP 200；畫面顯示 9/9 虛構活動、免責與卡片。`favicon.ico` 404 不屬於資料功能故障。
- SRC-P14 詳情視窗逐一 UAT **尚未完成**，不得宣稱 9/9 互動 PASS。現有卡片缺值仍為 `詳內文`，列為確定 UI 改善。
- SRC-P15：使用與 SRC-P14 相同 9 筆**虛構**資料、相同 P12/P13 候選 UI；只改列表卡片摘要為三行日期、地點、票價，完全採用 `referenceFieldText()` 角色契約、HTML escape，減少簡略卡片誤導。
- 正式 9,850 筆 `data.json`、GitHub Source/Preview、排程及通知不變；Draft PR #1 未 merge；Golden=0、Auto hidden=0、Published=false。
- 下一 Gate：SRC-P15 Android 獨立列表與詳情互動 UAT（port 18767），再進入 GitHub PR 來源功能收斂與 G5J/G5K 隔離資料策略。

## SRC-P15 UI 九案人工 UAT PASS 與 SRC-P16 候選來源樹（2026-10-24，本地候選）

```text
EventRadar review-only release candidate [SRC-P16; ANDROID verification PENDING]
├── Source: event_scraper_public / Draft PR #1 HEAD 26888422... [GITHUB ORIGINAL]
│   ├── show_news.py [P13 full, includes P1/P4/P7/P8/P9/P12/P13; Android previous PASS]
│   │   ├── BeClass list mobile RID: 20/20 canonical (candidate identity, not Golden)
│   │   └── BeClass detail explicit course-date roles: 2/2 two archived HTMLs; location 1/2, conflict HOLD
│   └── event_details.py [unchanged P10 integrated parser, G5H Regression]
├── Preview: eventradar-pwa-preview / main a8cde084... [GITHUB ORIGINAL]
│   └── index.html [P15 full review candidate, no local UAT-disabled official-link override]
│       ├── List cards: date/location/price source-aware; HTML escaping [ANDROID UAT 9/9 SYNTHETIC]
│       ├── Modal: one/multi/missing roles, terms, disclaimer [ANDROID UAT 9/9 SYNTHETIC]
│       ├── Search/filter/page/unknown retained [STATIC; broader E2E remains NOT PROVEN]
│       └── G5C/G5D original two JS assets unchanged [GITHUB PREVIEW BLOB]; no real data.json changes
├── Data persistence: frozen 9,850-record static data.json [NOT MODIFIED; NOT RE-READ]
├── Golden: 0 [HOLD]; Auto-hidden: 0 [LOCKED]; Published: false [LOCKED]
└── G5J / G5K: Real candidate identity, business UAT, rollout permissions [OPEN/HOLD]
```

**Source/Preview/正式資料三個生命週期不可混同。** 九筆 synthetic UAT 合格只代表 UI 角色顯示；完整 `P15 index.html` 仍未部署至 preview main。兩份治理文件目前僅為本 ZIP 的本地候選，GitHub 正式檔案尚未更新。

## 2026-10-24 — SRC-P17 來源／UI／Cloud 風險分流（治理候選）

```text
EventRadar GitHub release architecture（current P16 candidate SHA pinned）
├─ Source repo: easonliu714/event_scraper_public
│  ├─ Main: 6004754f90d5... [FROZEN]
│  ├─ PR #1 HEAD 26888422e486... [OPEN/DRAFT/UNMERGED; 34 FILES]
│  │  ├─ show_news.py + event_details.py [P16 ANDROID PASS; NOT DEPLOYED]
│  │  ├─ .github/workflows/*.yml [SEVEN; STATIC REVIEW TARGET]
│  │  └─ scripts/commit_data.sh [MAIN DATA WRITE/PUSH RISK; HOLD]
│  └─ proposed Source-only Draft PR [NOT CREATED; AUTHORIZATION REQUIRED]
├─ Preview repo: easonliu714/eventradar-pwa-preview
│  ├─ Main: a8cde084ab55... [FROZEN]
│  ├─ index.html [P15 NINE CARD + NINE MODAL HUMAN UAT PASS; NOT DEPLOYED]
│  └─ proposed UI-only Draft PR [NOT CREATED; AUTHORIZATION REQUIRED]
├─ Data
│  ├─ formal data.json 9,850 rows [NO WRITE]
│  ├─ BeClass historical 4,472 [NO BULK REPAIR]
│  └─ Golden 0 / auto_hidden 0 [LOCKED]
└─ Next Governance
   ├─ Two GitHub governance MDs [LOCAL CANDIDATES, NOT PUBLISHED]
   ├─ G5J validity [OPEN]
   └─ G5K real candidate UAT/publication [HOLD]
```

審查中「候選可套用／Android PASS」不等同「工作流程可啟用／正式資料已更新」。三路 Source、Preview、Cloud 的權限、CI 與 Merge Conditions 必須分開評估。

**Source branch dependency Gate**：P16 兩份 Source Diff 以 `PR #1 HEAD` 為 before baseline；故 `main -> source-only` 需要另造安全 Diff，不得使用 PR1 HEAD 分支繼承七項 Actions workflow。SRC-P17 僅審查、不宣告 Source clean branch 建立完成。


## SRC-P18 main-based source-only candidate (local governance update, 2026-10-24)

Source `main` remains legacy `scraper.py` + `docs/data.json`, without PR1 runtime `show_news.py`. SRC-P18's five new files are intentionally dormant. No Cloud Actions nor PWA UI change is included. PR1 source-only P16 Diff cannot be applied to main; P18 creates add-only Patch from exact main tree. Android P18 verification is pending.


### SRC-P18 V1.0.1 — fresh evidence parent bootstrap correction (2026-10-24)

- V100 Android selftest/preflight/five-file main additive patch/G5H PASS; BUILD HOLD `EVIDENCE_PARENT_BAD` before writing output due to missing extracted `evidence/` directory. No source Git write or website GET.
- V101 corrects create-only bootstrap only for `evidence/` and adds missing-parent/symlink/path-traversal/re-entry negatives. New output root; do not alter V100 evidence. V101 Android BUILD/VERIFY remains **pending** until host results.
- Existing SRC-P1–P17 and Source main `6004754f90d551cdb0cdb91a3e04b42c04f45f48`, PR #1 Draft `26888422e48634d9729d2deea67b7996a5d1e4ee`, Preview main `a8cde084ab5581736d86094d8cdcc2cdc9963000` unchanged subject to fresh independent readback. Governance text candidate local-only; GitHub not published.
- `GOLDEN_ACCEPTED=0`, `AUTO_HIDDEN=0`, `PUBLISHED=false`, Source-only five files DORMANT; G5J/G5K remain OPEN/HOLD.


## 2026-10-24 SRC-P18 V101 / P19 實作與發布分界

- Source main 使用 legacy scraper.py；新 show_news.py / event_details.py 以及 requirements-actions.txt / 兩個 G5H 測試僅作新增且 DORMANT，不與任何 workflow 接線。
- Preview UI：獨立 repo 僅 index.html 編輯，P15 九案例卡片／詳情 UAT PASS；不得更新正式 data.json。
- PR #1 34 files 全是相對 main 的新增項，7 workflows 與 commit_data.sh 的 write/push 是 Cloud side effects，獨立 HOLD。
- SRC-P19 僅在 Toolkit evidence 中產生兩條 PR 的 Patch／Draft PR body／SHA proof，不建立真實分支或 PR。


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
## SRC-P23 隔離 CI 發布架構（2026-10-24 候選，遠端未證實）
```
EventRadar CI governance branch (Source Repo, based on frozen main)
└─ ci/eventradar-source-ci-p22
   └─ [A / SHA-pinned] .github/workflows/eventradar_source_p22_branch_ci.yml
      ├─ trigger: push only, exact CI branch
      ├─ checkout: Source PR #2 frozen HEAD (five files)
      ├─ verify parent main SHA & exact five-file diff
      ├─ Python AST and G5H offline tests
      └─ no scraper / no schedule / no Git write / no data.json

EventRadar CI governance branch (Preview Repo, based on frozen main)
└─ ci/eventradar-preview-ci-p22
   └─ [A / SHA-pinned] .github/workflows/eventradar_preview_p22_branch_ci.yml
      ├─ trigger: push only, exact CI branch
      ├─ checkout: Preview PR #1 frozen HEAD (index.html only)
      ├─ verify parent main SHA & exact index-only diff
      ├─ Node 22 syntax + nine synthetic role cases + HTML escape
      └─ no deployment / no data write / no notifications
```
**Release policy:** SRC-P22 Android Workflow SHA PASS；SRC-P23 GitHub publish and Runner **待 Android/Remote 讀回**。CI 治理分支的 GitHub Check 與 P20 PR HEAD Checks 必須分開記錄，`CI_RUNNER_PASS != PR_HEAD_CI_PASS`。
