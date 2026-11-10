// PUB-OD-02: deterministic static PWA read-only contract; no source GET/dispatch.
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { summarize, renderSummary, refresh } = require("../../docs/pwa-freshness.js");

const published = [{
  title: "source verified sample", source_event_id: "2040", published: true,
  scraped_at: "2026-11-08T21:15:54+08:00"
}];
const held = {
  reportDate: "2026-10-28",
  production: { eventFeedReleaseState: "HARD_HOLD_NO_PUBLICATION" }
};
async function main() {
  // The legacy platform report date is NOT last_success or last_attempt.
  const base = summarize(published, held);
  assert.equal(base.state, "HOLD");
  assert.equal(base.publishedCount, 1);
  assert.equal(base.lastObserved, published[0].scraped_at);
  assert.equal(base.lastVerified, null);
  assert.equal(base.lastSuccess, null);
  assert.equal(base.lastAttempt, null);
  assert.equal(base.counts.added, null);
  assert.equal(base.ttlAuthority, "NOT_AVAILABLE_NO_TRUSTED_GATEWAY");
  const panel = { textContent: "" };
  renderSummary(base, panel);
  assert.match(panel.textContent, /正式已發布 1 筆/);
  assert.match(panel.textContent, /最後實際驗證：未提供/);
  assert.match(panel.textContent, /全域 TTL：尚無可信 Gateway 判定/);
  assert.match(panel.textContent, /HOLD/);

  // A future telemetry receipt may be displayed but never authorizes dispatch.
  const telemetry = {
    publisherStatus: {
      state: "RUNNING", last_success: "2026-11-10T07:00:00Z",
      last_attempt: "2026-11-10T09:00:00Z",
      last_verified_at: "2026-11-10T08:30:00Z",
      counts: { added: 2, changed: 1, retained: 7, rejected: 3 }
    }
  };
  const future = summarize(published, telemetry);
  assert.equal(future.state, "RUNNING");
  assert.deepEqual(future.counts, { added: 2, changed: 1, retained: 7, rejected: 3 });
  assert.equal(summarize(published, { ...telemetry, ...held }).state, "HOLD");
  assert.equal(summarize(published, {
    publisherStatus: { state: "SUCCESS", last_success: "2026-11-10" }
  }).lastSuccess, null);
  assert.equal(summarize([{ published: true, scraped_at: "bad" }], held).lastObserved, null);
  assert.equal(summarize([{ published: false }, { published: true }], held).publishedCount, 1);
  assert.throws(() => summarize({}, held), /READONLY_SCHEMA_HOLD/);
  assert.throws(() => summarize([], []), /READONLY_SCHEMA_HOLD/);

  // Runtime reads exactly two same-origin published JSON files, no runner calls.
  const calls = [];
  global.document = {
    getElementById(id) { return id === "pwa-freshness-detail" ? panel : null; }
  };
  global.fetch = async (url, options) => {
    calls.push({ url, options });
    if (url.startsWith("./data.json?")) return { ok: true, status: 200, json: async () => published };
    if (url.startsWith("./platform_status.json?")) return { ok: true, status: 200, json: async () => held };
    throw new Error("UNEXPECTED_NETWORK_TARGET");
  };
  const loaded = await refresh();
  assert.equal(loaded.state, "HOLD");
  assert.equal(calls.length, 2);
  assert.ok(calls.every(x => x.options.cache === "no-store"));
  assert.ok(calls.every(x => /^\.\/(data|platform_status)\.json\?read_only=\d+$/.test(x.url)));

  calls.length = 0;
  global.fetch = async url => {
    calls.push(url);
    return { ok: false, status: 429 };
  };
  assert.equal(await refresh(), null);
  assert.equal(calls.length, 2);
  assert.match(panel.textContent, /FAIL\/UNKNOWN/);

  const html = fs.readFileSync(path.join(__dirname, "../../docs/index.html"), "utf8");
  const js = fs.readFileSync(path.join(__dirname, "../../docs/pwa-freshness.js"), "utf8");
  assert.equal((html.match(/id="pwa-freshness-detail"/g) || []).length, 1);
  assert.equal((html.match(/src="pwa-freshness\.js"/g) || []).length, 1);
  assert.match(html, /await init\(\)/); // existing pull-to-refresh still fetches formal data.
  assert.match(html, /fetch\(`data\.json\?t=\$\{timestamp\}`/);
  assert.doesNotMatch(js, /repository_dispatch|workflow_dispatch|api\.github\.com|Authorization\s*:|github_pat_|ghp_/);
  assert.doesNotMatch(js, /tpac\.org|tainex\.com|famiticket\.com/);
  // Reopening a cached PWA must refresh the real event cards as well as
  // the status panel. Initial pageshow must not duplicate inline init().
  const lifecycle = {};
  const lifecyclePanel = { textContent: "" };
  const fakeDocument = {
    visibilityState: "visible",
    getElementById(id) { return id === "pwa-freshness-detail" ? lifecyclePanel : null; },
    addEventListener(name, callback) { lifecycle[name] = callback; }
  };
  let cardReads = 0;
  let statusReads = 0;
  const fakeWindow = {
    init: async () => { cardReads += 1; },
    addEventListener(name, callback) { lifecycle[name] = callback; }
  };
  vm.runInNewContext(js, {
    window: fakeWindow, document: fakeDocument,
    fetch: async url => {
      statusReads += 1;
      return { ok: true, status: 200, json: async () =>
        url.startsWith("./data.json?") ? published : held };
    }
  }, { filename: "docs/pwa-freshness.js" });
  const settled = () => new Promise(resolve => setImmediate(resolve));
  lifecycle.pageshow({ persisted: false });
  await settled();
  assert.equal(cardReads, 0, "initial load already calls init()");
  lifecycle.pageshow({ persisted: true });
  await settled();
  assert.equal(cardReads, 1, "BFCache restore refreshes event cards");
  lifecycle.visibilitychange();
  await settled();
  assert.equal(cardReads, 2, "foreground resume refreshes event cards");
  fakeDocument.visibilityState = "hidden";
  lifecycle.visibilitychange();
  await settled();
  assert.equal(cardReads, 2, "background transition does not refresh cards");
  assert.ok(statusReads >= 4, "read-only status/data remain refreshed");
  assert.doesNotMatch(js, /repository_dispatch|workflow_dispatch|api\\.github\\.com|Authorization\\s*:|github_pat_|ghp_/);
  console.log("PASS PUB_OD_02_BFCACHE_FOREGROUND_FORMAL_CARDS_REFRESH");
  console.log("PASS PUB_OD_02_READONLY_PWA_FRESHNESS_20_ASSERTION_GROUPS");
}
main().catch(err => { console.error(err); process.exitCode = 1; });
