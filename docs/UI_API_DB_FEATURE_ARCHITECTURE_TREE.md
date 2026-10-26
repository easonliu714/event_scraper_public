# 活動暨售票雷達｜UI／API／資料儲存／CI 功能架構樹

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
