#!/usr/bin/env node
// L8 source-bound REVIEW field guard. Synthetic only; never reads live data.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('docs/index.html', 'utf8');
const cut = (start, end) => {
  const i = html.indexOf(start), j = html.indexOf(end, i + start.length);
  assert.ok(i >= 0 && j > i, 'missing exact UI function boundary: ' + start);
  return html.slice(i, j);
};
const fieldCode = cut('function candidateReviewField(', '    // Review-only: an explicit local-file gesture');
const urlCode = cut('function isCandidateOfficialUrl(', '    function renderCandidateReview()');
const candidateReviewField = vm.runInNewContext(urlCode + '\n' + fieldCode + '\n candidateReviewField', { URL, Date, Number, Array });
assert.match(html, /date: fields\.date\.value/);
assert.match(html, /location: fields\.location\.value/);
assert.match(html, /price: fields\.price\.value/);
assert.match(html, /reasons: \[\.\.\.meta\.hold_reasons\.map/);
assert.doesNotMatch(html, /date: typeof row\.date === 'string'/);
const url = 'https://example.org/events/123';
const row = { url, date: '2026-11-21 19:30', location: '新北市', price: 'NT$100', description: '活動說明' };
const receipt = (value, role) => ({ value, role, source: url, observed_at: '2026-11-01T14:00:00+08:00', decision: 'REVIEW' });
const meta = { sources: [url], field_evidence: {
  date: receipt(row.date, 'EVENT_DATE'),
  location: receipt(row.location, 'EVENT_VENUE'),
  price: receipt(row.price, 'EVENT_ADMISSION_PRICE'),
  description: receipt(row.description, 'EVENT_DESCRIPTION')
}};
const check = (key, roles, expected, m=meta) => {
  const actual = candidateReviewField(row, m, key, roles);
  assert.equal(actual.value, expected, key);
  if (expected === '未確認') assert.equal(actual.hold, 'FIELD_' + key.toUpperCase() + '_PROVENANCE_HOLD');
  else assert.equal(actual.hold, null);
};
check('date', ['EVENT_DATE', 'VENUE_EVENT_DATE'], row.date);
check('location', ['EVENT_VENUE'], row.location);
check('price', ['EVENT_ADMISSION_PRICE'], row.price);
check('description', ['EVENT_DESCRIPTION'], row.description);
for (const change of [
  { source: 'https://another.example.org/123' },
  { role: 'SALE_END' },
  { role: ['EVENT_DATE'] },
  { observed_at: '2026-11-01T14:00:00' },
  { observed_at: 'not-a-time' },
  { value: '2026-11-22 19:30' },
  { decision: 'PASS' }
]) {
  const m = JSON.parse(JSON.stringify(meta));
  Object.assign(m.field_evidence.date, change);
  check('date', ['EVENT_DATE'], '未確認', m);
}
const missing = { sources: [url], field_evidence: {} };
check('date', ['EVENT_DATE'], '未確認', missing);
check('price', ['EVENT_ADMISSION_PRICE'], '未確認', missing);
const foreign = JSON.parse(JSON.stringify(meta));
foreign.sources = ['https://example.org/events/other'];
check('date', ['EVENT_DATE'], '未確認', foreign);
// A-line #03 tixCraft: a VIP add-on URL is not the base concert's price
// receipt, even when both HTTPS URLs are in the same REVIEW sources array.
const baseConcert = 'https://tixcraft.com/activity/detail/26_wte';
const vipAddon = 'https://tixcraft.com/activity/detail/26_wte_v';
const baseRow = { url: baseConcert, price: 'NT$4,800' };
const baseMeta = { sources: [baseConcert, vipAddon], field_evidence: {
  price: { ...receipt(baseRow.price, 'EVENT_ADMISSION_PRICE'), source: vipAddon }
}};
assert.equal(candidateReviewField(baseRow, baseMeta, 'price', ['EVENT_ADMISSION_PRICE']).value, '未確認');
baseMeta.field_evidence.price.source = baseConcert;
baseMeta.field_evidence.price.role = 'VIP_ADDON_PRICE';
assert.equal(candidateReviewField(baseRow, baseMeta, 'price', ['EVENT_ADMISSION_PRICE']).value, '未確認');
// B-line New Taipei bulletin and OPENTIX multi-venue Event share a link,
// not a verified ticket Session ID or interchangeable field ownership.
const bulletin = 'https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168';
const ticket = 'https://www.opentix.life/event/2086734015886159873';
const venueRow = { url: bulletin, date: '2026-11-07 14:30' };
const venueMeta = { sources: [bulletin, ticket], field_evidence: {
  date: { ...receipt(venueRow.date, 'VENUE_EVENT_DATE'), source: ticket }
}};
assert.equal(candidateReviewField(venueRow, venueMeta, 'date', ['EVENT_DATE', 'VENUE_EVENT_DATE']).value, '未確認');
venueMeta.field_evidence.date.source = bulletin;
venueMeta.field_evidence.date.role = 'VENUE_BULLETIN_PUBLICATION_DATE';
assert.equal(candidateReviewField(venueRow, venueMeta, 'date', ['EVENT_DATE', 'VENUE_EVENT_DATE']).value, '未確認');
// Same-host, different event is equally invalid; host allowlisting is not identity.
const bleed = JSON.parse(JSON.stringify(meta));
bleed.sources.push('https://example.org/events/456');
bleed.field_evidence.date.source = 'https://example.org/events/456';
check('date', ['EVENT_DATE'], '未確認', bleed);
const absent = { url, date: '未確認' };
assert.equal(candidateReviewField(absent, missing, 'date', ['EVENT_DATE']).hold, null);
const unknown = { url, date: '詳內文' };
assert.equal(candidateReviewField(unknown, missing, 'date', ['EVENT_DATE']).value, '未確認');
console.log('PASS_L8_REVIEW_FIELD_PROVENANCE_SYNTHETIC_17_CASES_NO_PUBLICATION');
