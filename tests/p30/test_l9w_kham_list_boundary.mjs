#!/usr/bin/env node
/* P30-L9-W offline, no network or browser. Fail-closed structural contracts. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {allowed,links,decide,report,safeOutput,parents,
  ENTRY,KIND,RELEASE,N,MAX_LINKS} from '../../scripts/p30_l9w_kham_list_boundary.mjs';
const base=()=>({anchors:0,detailUnique:0,detailRepeated:0,
  categoryLinks:0,javascriptLinks:0,offsiteLinks:0,otherLinks:0});
const frame=(n=0,ready='complete',extras={})=>({
  ready,links:{...base(),detailUnique:n},forms:0,onclickElements:0,
  frames:0,scripts:0,...extras});
const probe=(staticN=0,renderN=0)=>({
  navigations:1,http:200,redirectCount:0,finalAllowed:true,
  staticAvailable:true,staticLinks:{...base(),detailUnique:staticN},
  snapshots:Array.from({length:N},()=>frame(renderN))});
const historical={historicalHTTP:200,historicalList:0};
test('01 exact kind',()=>assert.equal(KIND,'EVENTRADAR_P30_L9W_KHAM_LIST_BOUNDARY_V1'));
test('02 hard hold',()=>assert.equal(RELEASE,'HARD_HOLD_NO_PUBLICATION'));
test('03 pinned HTTPS entry',()=>assert.ok(allowed(ENTRY)));
test('04 exact hostname',()=>assert.ok(allowed('https://kham.com.tw/')));
test('05 subdomain allowed',()=>assert.ok(allowed('https://www.kham.com.tw/')));
test('06 other hostname blocked',()=>assert.equal(allowed('https://kham.com.tw.evil.test/'),false));
test('07 downgrade blocked',()=>assert.equal(allowed('http://kham.com.tw/'),false));
test('08 credentials blocked',()=>assert.equal(allowed('https://u:p@kham.com.tw/'),false));
test('09 non-HTTPS blocked',()=>assert.equal(allowed('javascript:alert(1)'),false));
test('10 malformed URL blocked',()=>assert.equal(allowed('bad'),false));
test('11 detail link counted',()=>{
 const s=links(['/application/UTK02/UTK0201_01.aspx?ID=1'],ENTRY);
 assert.equal(s.detailUnique,1);
});
test('12 duplicate detail not counted twice',()=>{
 const u='/application/UTK02/UTK0201_01.aspx?ID=1';
 const s=links([u,u],ENTRY);
 assert.equal(s.detailUnique,1);assert.equal(s.detailRepeated,1);
});
test('13 category link distinct',()=>{
 const s=links(['/application/UTK01/UTK0101_06.aspx'],ENTRY);
 assert.equal(s.categoryLinks,1);assert.equal(s.detailUnique,0);
});
test('14 javascript link is not event',()=>{
 const s=links(['javascript:__doPostBack(1)'],ENTRY);
 assert.equal(s.javascriptLinks,1);assert.equal(s.detailUnique,0);
});
test('15 offsite never event',()=>{
 const s=links(['https://other.example/UTK0201_01.aspx'],ENTRY);
 assert.equal(s.offsiteLinks,1);assert.equal(s.detailUnique,0);
});
test('16 max links cap',()=>{
 assert.throws(()=>links(Array(MAX_LINKS+1).fill('/'),ENTRY));
});
test('17 JS rendered anchor evidence is review only',()=>{
 const p=probe(0,2);
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'REVIEW_CURRENT_JS_DETAIL_LINKS_HISTORIC_ZERO');
});
test('18 static anchor generic-parser gap is review only',()=>{
 const p=probe(2,2);
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'REVIEW_CURRENT_STATIC_DETAIL_LINKS_HISTORIC_ZERO');
});
test('19 static links removed hold',()=>{
 const p=probe(2,0);
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'HOLD_STATIC_DETAIL_ANCHORS_REMOVED');
});
test('20 nonanchor structure hold',()=>{
 const p=probe(0,0);p.snapshots[3].forms=1;
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'HOLD_NON_ANCHOR_OR_INTERACTIVE_STRUCTURE');
});
test('21 no anchors hold',()=>{
 const p=probe(0,0);
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'HOLD_ZERO_ANCHORS_OR_ENTRY_MISMATCH');
});
test('22 HTTP403 never promoted',()=>{
 const p=probe(0,3);p.http=403;
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'HOLD_HTTP_NOT_200');
});
test('23 offsite final hold',()=>{
 const p=probe(0,3);
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,false,true),'HOLD_UNSAFE_OR_OFFSITE_FINAL');
});
test('24 unavailable static response hold',()=>{
 const p=probe(0,3);
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,false),'HOLD_STATIC_RESPONSE_UNAVAILABLE');
});
test('25 incomplete snapshots hold',()=>{
 const p=probe(0,3);p.snapshots.pop();
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'HOLD_INCOMPLETE_RENDER_SNAPSHOTS');
});
test('26 unstable tail hold',()=>{
 const p=probe(0,3);p.snapshots[2].links.detailUnique=2;
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'HOLD_RENDER_NOT_STABLE');
});
test('27 incomplete ready tail hold',()=>{
 const p=probe(0,3);p.snapshots[3].ready='interactive';
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),'HOLD_RENDER_NOT_COMPLETE');
});
test('28 report never publishes',()=>{
 const r=report(historical,probe(0,2));
 assert.equal(r.acceptedFields,0);assert.equal(r.goldenAccepted,0);
 assert.equal(r.listEventIdentityVerified,0);assert.equal(r.published,false);
 assert.equal(r.releaseState,RELEASE);
});
test('29 no raw source persistence flags',()=>{
 const r=report(historical,probe(0,2));
 for(const k of ['rawHtmlPersisted','rawUrlsPersisted','rawTitlesPersisted',
   'cookiesPersisted','screenshotsPersisted','networkBodiesPersisted'])
   assert.equal(r[k],false);
});
test('30 no side effects',()=>{
 const r=report(historical,probe(0,2));
 for(const k of ['writerExecuted','schedulerExecuted','notifierExecuted',
   'mergeExecuted','productionModified'])assert.equal(r[k],false);
});
test('31 output path only isolated',()=>{
 assert.ok(safeOutput('p30-l9w-evidence').startsWith(resolve('.')+'/'));
});
test('32 docs output blocked',()=>assert.throws(()=>safeOutput('docs/status')));
test('33 scripts output blocked',()=>assert.throws(()=>safeOutput('scripts/tmp')));
test('34 parent directory blocked',()=>assert.throws(()=>safeOutput('../outside')));
test('35 invalid historical baseline blocked',()=>{
 assert.throws(()=>report({historicalHTTP:403,historicalList:0},probe(0,2)));
});
test('36 repeated navigation blocked',()=>{
 const p=probe(0,2);p.navigations=2;
 assert.throws(()=>report(historical,p));
});
test('37 mismatched parent status SHA blocked',()=>{
 assert.throws(()=>parents(Buffer.from('{}'),Buffer.from('{}'),{}),/STATUS_BLOB/);
});
test('38 production file immutable by contract',()=>{
 const r=report(historical,probe(0,2));
 assert.equal(r.historicalObservationIsNotCurrent,true);
 assert.equal(r.sourceEntryId,'KHAM_CATEGORY_205');
});
test('39 prior interactive tail with latest complete and stable anchor count is review only',()=>{
 const p=probe(10,10);p.snapshots[2].ready='interactive';
 assert.equal(decide(p.http,p.staticLinks,p.snapshots,true,true),
   'REVIEW_CURRENT_STATIC_DETAIL_LINKS_HISTORIC_ZERO');
});
