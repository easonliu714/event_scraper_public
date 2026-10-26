# 活動暨售票雷達｜正式治理 Roadmap、PR、Issue 稽核


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
