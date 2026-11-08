"use strict";
// PWA UI regression: group only the source chips; keep one combined platform-selection set.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync("docs/index.html", "utf8");
const blocks = [...html.matchAll(/<script>([^]*?)<\/script>/g)];
assert.equal(blocks.length, 1, "existing single-script PWA structure");
const script = blocks[0][1];
new vm.Script(script, { filename: "docs/index.html#script" });
for (const id of ["ticket-platform-chips", "venue-platform-chips"]) {
    assert.ok(html.includes('id="' + id + '"'), "missing group: " + id);
}
assert.ok(!html.includes('id="platform-chips"'), "legacy mixed source group remains");
assert.ok(html.includes("售票/活動資訊平台"), "exact Owner label");
assert.match(html, /活動場地/);
assert.match(script, /function renderChips\(\)\s*\{\s*renderSourceChips\(\)/);
assert.match(script, /filters\.platforms\.size\s*>\s*0\s*&&\s*!filters\.platforms\.has\(e\.platform\)/);

const begin = script.indexOf("const VENUE_SOURCE_NAMES = new Set(");
const end = script.indexOf("    function renderChips() {", begin);
assert.ok(begin > 0 && end > begin, "source mapping/functions missing");
const code = script.slice(begin, end);
assert.ok(!/\.innerHTML\s*=/.test(code), "source chip names must not interpolate HTML");

class FakeNode {
    constructor(tag) {
        this.tag = tag;
        this.children = [];
        this.attributes = {};
        this.handlers = {};
        this.className = "";
        this.textContent = "";
    }
    append(...children) { this.children.push(...children); }
    replaceChildren(...children) { this.children = children; }
    setAttribute(k, v) { this.attributes[k] = v; }
    addEventListener(name, callback) { this.handlers[name] = callback; }
}
const roots = {
    "ticket-platform-chips": new FakeNode("div"),
    "venue-platform-chips": new FakeNode("div"),
};
const inputs = [
    {platform: "華山1914"}, {platform: "華山1914"},
    {platform: "松山文創"}, {platform: "台北世貿"}, {platform: "中正紀念堂"},
    {platform: "臺北表演藝術中心"},
    {platform: "OPENTIX"}, {platform: "OPENTIX"}, {platform: "KKTIX"},
    {platform: "<img src=x onerror=alert(1)>"}
];
const filters = {platforms: new Set()};
const context = {
    // Node vm sandbox does not expose browser URL by default.
    URL,
    document: {
        getElementById: id => roots[id],
        createElement: tag => new FakeNode(tag),
        createTextNode: text => ({ nodeType: 3, textContent: text })
    },
    allEvents: inputs,
    filters,
    toggleFilter(category, value, button) {
        const set = filters[category];
        if (set.has(value)) set.delete(value);
        else set.add(value);
        button.className = "chip source-chip" + (set.has(value) ? " active" : "");
    }
};
vm.createContext(context);
vm.runInContext(code, context);
const names = root => root.children.map(chip => chip.children[0].textContent.trim());
const find = (root, source) =>
    root.children.find(chip => chip.children[0].textContent.trim() === source);

for (const name of ["華山1914", "松山文創", "台北世貿", "中正紀念堂", "臺北表演藝術中心"]) {
    assert.equal(context.sourceGroup(name), "venue", name);
}
for (const name of ["OPENTIX", "KKTIX", "ACCUPASS", "FamiTicket", "StrollTimes"]) {
    assert.equal(context.sourceGroup(name), "platform", name);
}
assert.equal(context.sourceGroup(" 華山1914 "), "venue", "trim / normalization");
assert.equal(context.sourceGroup("台北表演藝術中心"), "venue", "normalized venue alias");

context.renderSourceChips();
assert.deepEqual(names(roots["venue-platform-chips"]).sort(),
    ["華山1914", "松山文創", "台北世貿", "中正紀念堂", "臺北表演藝術中心"].sort());
assert.deepEqual(names(roots["ticket-platform-chips"]).sort(),
    ["OPENTIX", "KKTIX", "<img src=x onerror=alert(1)>"].sort());
assert.equal(find(roots["venue-platform-chips"], "華山1914").children[1].textContent, "2");
assert.equal(find(roots["ticket-platform-chips"], "OPENTIX").children[1].textContent, "2");
assert.equal(find(roots["ticket-platform-chips"], "OPENTIX").tag, "button");
assert.equal(find(roots["ticket-platform-chips"], "OPENTIX").type, "button");

const venueChip = find(roots["venue-platform-chips"], "華山1914");
const ticketChip = find(roots["ticket-platform-chips"], "OPENTIX");
venueChip.handlers.click();
ticketChip.handlers.click();
assert.equal(venueChip.attributes["aria-pressed"], "true");
assert.equal(ticketChip.attributes["aria-pressed"], "true");
assert.deepEqual([...filters.platforms].sort(), ["華山1914", "OPENTIX"].sort(),
    "both visual groups share the legacy OR source filter");
assert.equal(inputs.filter(e => filters.platforms.has(e.platform)).length, 4,
    "both selected groups contribute their event counts");
context.renderSourceChips();
assert.ok(find(roots["venue-platform-chips"], "華山1914").className.includes("active"));
assert.ok(find(roots["ticket-platform-chips"], "OPENTIX").className.includes("active"));
find(roots["venue-platform-chips"], "華山1914").handlers.click();
assert.equal(filters.platforms.has("華山1914"), false);
assert.equal(filters.platforms.has("OPENTIX"), true);
assert.equal(inputs[0].platform, "華山1914", "original event source identity must not change");

// [新增] 地區回歸：正式 JSON 缺 region 時，官方來源 + 明確場地 + 活動 ID
// 才能使用經官方地址核實的 North；全部地區統計/篩選/卡片必共用同一函數。
const formal = JSON.parse(fs.readFileSync("docs/data.json", "utf8"));
assert.equal(formal.length, 1, "unchanged Owner-authorized formal feed");
const tpac = formal[0];
assert.equal(tpac.region, undefined, "regression source row intentionally has no region");
assert.equal(context.eventRegion(tpac), "north", "verified Taipei Shilin source venue");
assert.equal(context.eventRegion({ ...tpac, region: "North" }), "north", "explicit case normalized");
assert.equal(context.eventRegion({ ...tpac, region: "South" }), "unknown",
    "explicit conflicting region quarantined, not silently overwritten");
assert.equal(context.eventRegion({ ...tpac, location: "外部場地" }), "unknown",
    "organizing platform is not automatically the event venue");
assert.equal(context.eventRegion({ ...tpac, platform: "OPENTIX" }), "unknown",
    "ticket seller source cannot inherit organizer building address");
assert.equal(context.eventRegion({ ...tpac, url: "https://tpac.org.taipei.evil.org/program/2040" }), "unknown",
    "spoofed official host never accepted");
assert.equal(context.eventRegion({ ...tpac, url: "https://tpac.org.taipei/program/2040?session=1" }), "unknown",
    "ticket/session sub-identity not official event key");
assert.equal(context.eventRegion({ ...tpac, location: "台北表演藝術中心" }), "north",
    "official venue name alias normalization");
assert.equal(context.eventRegion({ ...tpac, location: "外部場地", region: "Central" }), "central",
    "already accepted explicit region remains usable for other venues");
assert.equal(context.eventRegion({ ...tpac, location: "外部場地", region: "Unknown" }), "unknown",
    "unknown never invents a location");

assert.match(script, /const r = eventRegion\(e\);/, "region chip count uses canonical event region");
assert.match(script, /const region = eventRegion\(e\);/, "region filtering uses same region");
assert.match(script, /const regionA = eventRegion\(a\);/, "region sorting uses same region");
assert.match(script, /regionLabelMap\[eventRegion\(e\)\]/,
    "formal card region badge uses same region");

const regionalRoots = {
    "region-chips": { innerHTML: "" },
    "type-chips": { innerHTML: "" },
    "result-count": { textContent: "" },
    "search": { value: "" }
};
const regional = {
    URL,
    allEvents: formal,
    filters: { platforms: new Set(), regions: new Set(), status: new Set(), types: new Set() },
    document: { getElementById: id => regionalRoots[id] },
    renderSourceChips() {},
    updateStatusCounts() {},
    readEvents: [],
    checkIsFav: () => false,
    renderList() {},
    renderPagination() {}
};
vm.createContext(regional);
vm.runInContext(code.slice(0, code.indexOf("    function renderSourceChips() {")), regional);
const renderChipsBegin = script.indexOf("    function renderChips() {");
const renderChipsEnd = script.indexOf("    function updateStatusCounts() {", renderChipsBegin);
assert.ok(renderChipsBegin > 0 && renderChipsEnd > renderChipsBegin);
vm.runInContext(script.slice(renderChipsBegin, renderChipsEnd), regional);
regional.renderChips();
assert.match(regionalRoots["region-chips"].innerHTML, /北區 <span>1<\/span>/,
    "formal mobile North chip must show 1, not 0");
assert.match(regionalRoots["region-chips"].innerHTML, /南區 <span>0<\/span>/,
    "unrelated region still zero");

const applyBegin = script.indexOf("    function applyFilters() {");
const applyEnd = script.indexOf("    function formalCardPriceSummary(", applyBegin);
assert.ok(applyBegin > 0 && applyEnd > applyBegin);
vm.runInContext("let filteredEvents = [];\n" + script.slice(applyBegin, applyEnd), regional);
regional.filters.regions.add("north");
regional.applyFilters();
assert.equal(vm.runInContext("filteredEvents.length", regional), 1,
    "select North keeps TPAC official activity");
regional.filters.regions.clear();
regional.filters.regions.add("south");
regional.applyFilters();
assert.equal(vm.runInContext("filteredEvents.length", regional), 0,
    "select South excludes known North event, not unknown fallback");

console.log("PASS PWA source-category UI groups, mobile buttons, OR filters, counts, safe labels");
console.log("PASS PWA official TPAC region North=1, unknown/remote/conflict HOLD, counts and filters");

