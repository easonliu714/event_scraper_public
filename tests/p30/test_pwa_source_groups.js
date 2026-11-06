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
assert.match(html, /售票／活動資訊平台/);
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
    {platform: "OPENTIX"}, {platform: "OPENTIX"}, {platform: "KKTIX"},
    {platform: "<img src=x onerror=alert(1)>"}
];
const filters = {platforms: new Set()};
const context = {
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

for (const name of ["華山1914", "松山文創", "台北世貿", "中正紀念堂"]) {
    assert.equal(context.sourceGroup(name), "venue", name);
}
for (const name of ["OPENTIX", "KKTIX", "ACCUPASS", "FamiTicket", "StrollTimes"]) {
    assert.equal(context.sourceGroup(name), "platform", name);
}
assert.equal(context.sourceGroup(" 華山1914 "), "venue", "trim / normalization");

context.renderSourceChips();
assert.deepEqual(names(roots["venue-platform-chips"]).sort(),
    ["華山1914", "松山文創", "台北世貿", "中正紀念堂"].sort());
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
console.log("PASS PWA source-category UI groups, mobile buttons, OR filters, counts, safe labels");
