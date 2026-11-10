/* PUB-OD-02: static Pages read-only freshness, never a dispatch authority.
 * Only docs/data.json and docs/platform_status.json are fetched. Missing
 * publisher receipts remain UNKNOWN; browser clock is not a trusted TTL gate.
 */
(function (root) {
  "use strict";
  const STATES = new Set(["RUNNING", "NOT_DUE", "HOLD", "FAIL", "SUCCESS"]);
  const UNKNOWN = "未提供";
  function exactTime(value) {
    return typeof value === "string" &&
      /(Z|[+-]\d{2}:\d{2})$/i.test(value) &&
      Number.isFinite(Date.parse(value)) ? value : null;
  }
  function safeCount(value) {
    return Number.isSafeInteger(value) && value >= 0 ? value : null;
  }
  function summarize(feed, status) {
    if (!Array.isArray(feed) || !status || typeof status !== "object" || Array.isArray(status)) {
      throw new Error("READONLY_SCHEMA_HOLD");
    }
    const published = feed.filter(row => row && typeof row === "object" && row.published === true);
    const times = published.map(row => exactTime(row.scraped_at)).filter(Boolean);
    times.sort((a, b) => Date.parse(b) - Date.parse(a));
    const telemetry = status.publisherStatus && typeof status.publisherStatus === "object" &&
      !Array.isArray(status.publisherStatus) ? status.publisherStatus : {};
    const counts = telemetry.counts && typeof telemetry.counts === "object" &&
      !Array.isArray(telemetry.counts) ? telemetry.counts : {};
    const hold = status.production?.eventFeedReleaseState === "HARD_HOLD_NO_PUBLICATION";
    const state = hold ? "HOLD" : STATES.has(telemetry.state) ? telemetry.state : "UNKNOWN";
    return {
      state, publishedCount: published.length,
      lastObserved: times[0] || null,
      lastVerified: exactTime(telemetry.last_verified_at),
      lastSuccess: exactTime(telemetry.last_success),
      lastAttempt: exactTime(telemetry.last_attempt),
      counts: {
        added: safeCount(counts.added), changed: safeCount(counts.changed),
        retained: safeCount(counts.retained), rejected: safeCount(counts.rejected)
      },
      statusReportDate: /^\d{4}-\d{2}-\d{2}$/.test(status.reportDate || "") ?
        status.reportDate : null,
      ttlAuthority: "NOT_AVAILABLE_NO_TRUSTED_GATEWAY"
    };
  }
  function taipei(value) {
    return value ? new Date(value).toLocaleString("zh-TW", {
      timeZone: "Asia/Taipei", hour12: false
    }) + "（台灣時間）" : UNKNOWN;
  }
  function renderSummary(summary, target) {
    if (!target) return;
    const stateNames = {
      HOLD: "HOLD（禁止新發布，既有正式資料仍可讀）",
      RUNNING: "運作中", NOT_DUE: "未到期", FAIL: "FAIL",
      SUCCESS: "最近一次執行成功", UNKNOWN: "UNKNOWN（缺正式發布收據）"
    };
    const number = value => value === null ? UNKNOWN : String(value);
    const c = summary.counts;
    target.textContent =
      "正式已發布 " + summary.publishedCount + " 筆｜狀態：" + stateNames[summary.state] +
      "\n最近來源觀測：" + taipei(summary.lastObserved) +
      "｜最後實際驗證：" + taipei(summary.lastVerified) +
      "\nPublisher last_success：" + taipei(summary.lastSuccess) +
      "｜last_attempt：" + taipei(summary.lastAttempt) +
      "\n正式變更：新增 " + number(c.added) + "／變更 " + number(c.changed) +
      "／保留 " + number(c.retained) + "／拒絕 " + number(c.rejected) +
      "｜全域 TTL：尚無可信 Gateway 判定" +
      "\n平台工程報告日期：" + (summary.statusReportDate || UNKNOWN) +
      "（非即時發布時間）；Pages 部署與快取可能延遲。";
  }
  async function readJson(name) {
    if (name !== "data.json" && name !== "platform_status.json") {
      throw new Error("READONLY_PATH_HOLD");
    }
    const response = await fetch("./" + name + "?read_only=" + Date.now(), {
      cache: "no-store", headers: { "Cache-Control": "no-cache" }
    });
    if (response.status === 403 || response.status === 429) {
      throw new Error("READONLY_HTTP_" + response.status + "_HOLD");
    }
    if (!response.ok) throw new Error("READONLY_HTTP_FAILURE");
    return response.json();
  }
  let pending = null;
  function refresh() {
    if (pending) return pending;
    const target = document.getElementById("pwa-freshness-detail");
    if (!target) return Promise.resolve(null);
    pending = Promise.all([readJson("data.json"), readJson("platform_status.json")])
      .then(([feed, status]) => {
        const summary = summarize(feed, status);
        renderSummary(summary, target);
        return summary;
      })
      .catch(() => {
        target.textContent = "只讀新鮮度資訊暫不可驗證（FAIL/UNKNOWN）；" +
          "不影響既有正式活動卡片，亦不會啟動擷取或發布。請稍後下拉重新讀取。";
        return null;
      })
      .finally(() => { pending = null; });
    return pending;
  }
  // A restored/backgrounded PWA can keep stale event cards even when the
  // freshness panel re-reads JSON. Reuse the existing formal-feed init() only
  // on BFCache restore or foreground return; never GET source or dispatch.
  let cardsPending = null;
  function refreshPublishedCards() {
    if (!root || typeof root.init !== "function") return Promise.resolve(null);
    if (cardsPending) return cardsPending;
    cardsPending = Promise.resolve().then(() => root.init())
      .catch(() => null)
      .finally(() => { cardsPending = null; });
    return cardsPending;
  }
  const api = { summarize, renderSummary, refresh, refreshPublishedCards };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root && typeof document !== "undefined") {
    root.EventRadarReadOnlyFreshness = api;
    root.addEventListener("pageshow", event => {
      // Initial load already runs init() in the existing inline application.
      if (event && event.persisted) void refreshPublishedCards();
      void refresh();
    });
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        void refreshPublishedCards();
        void refresh();
      }
    });
    root.addEventListener("touchend", () => {
      const ptr = document.getElementById("pull-to-refresh");
      if (ptr && ptr.style.top === "60px") void refresh();
    });
  }
})(typeof window === "undefined" ? null : window);
