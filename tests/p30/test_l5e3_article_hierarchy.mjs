import test from "node:test";
import assert from "node:assert/strict";
import {KIND,PARENT_KIND,MAX_HELD,MAX_NETWORK,n,titleRelation,validateParent,compare}
 from "../../scripts/p30_l5e3_article_hierarchy.mjs";
const PREFIX="https://strolltimes.com/events/";
const urls=["taoyuan/261016120001/","hsinchu/261016120002/","new-taipei/261016120003/","taipei/261016120004/"];
const titles=["2026桃園眷村文化節 龜山眷村故事館場次","2026香山濕地藝術季",
 "2026新北濕地藝術季 《萌芽之境》","2026晴空季"];
const rows=()=>titles.map((title,i)=>({
 aggregatorUrl:PREFIX+urls[i],observedArticleUrl:PREFIX+urls[i],title,articleHttp:200,
 articleIdentity:"ARTICLE_TITLE_OR_HTTP_HOLD",originalOfficialUrl:null,
 dateStart:null,dateEnd:null,published:false,goldenVerified:false}));
const parent=()=>({kind:PARENT_KIND,sourceRuntime:"DORMANT",
 published:false,goldenAccepted:false,fieldPromotionCount:0,
 firstPartyEventDetailsIndependentlyVerified:0,articleSamplesCount:6,
 listCandidateCount:24,originalOfficialEventUrl:null,mainAndroid44Preserved:true,
 samples:[...rows(),{articleIdentity:"AGGREGATOR_ARTICLE_H1_MATCH"},
  {articleIdentity:"AGGREGATOR_ARTICLE_H1_MATCH"}]});
const observations=()=>rows().map((x,i)=>({
 aggregatorUrl:x.aggregatorUrl,currentUrl:x.aggregatorUrl,http:200,
 h1:[i===0?"2026桃園眷村文化節":x.title],
 breadcrumbText:["活動","所在縣市"],sectionHeadings:["活動資訊"]}));
test("01 source role is review-only",()=>assert.match(KIND,/REVIEW_ONLY/));
test("02 resource budgets are immutable",()=>{
 assert.equal(MAX_HELD,4);assert.equal(MAX_NETWORK,240);
});
test("03 hierarchical relation only explicit parent prefix with specific child field",()=>{
 const x=titleRelation("2026桃園眷村文化節 龜山眷村故事館場次","2026桃園眷村文化節");
 assert.equal(x.kind,"POTENTIAL_PARENT_CHILD_SUFFIX_REVIEW");
 assert.equal(x.edgeType,"SUBEVENT_OF_UNVERIFIED");
});
test("04 exact article title remains exact, no new edge",()=>{
 const x=titleRelation("2026新北濕地藝術季","2026新北濕地藝術季");
 assert.equal(x.kind,"EXACT_AGGREGATOR_ARTICLE_MATCH");assert.equal(x.edgeType,null);
});
test("05 title date-only suffix remains aggregator identity not a new event date",()=>{
 const x=titleRelation("2026新竹市萬聖節","2026新竹市萬聖節（10/16~10/31）");
 assert.equal(x.kind,"EXACT_AGGREGATOR_ARTICLE_MATCH");
});
test("06 no common root = neither duplicate nor parent",()=>{
 assert.equal(titleRelation("2026桃園眷村文化節","2026香山濕地藝術季").edgeType,null);
});
test("07 year drift must hold",()=>{
 assert.equal(titleRelation("2027桃園眷村文化節 龜山眷村故事館場次","2026桃園眷村文化節").kind,
   "UNRESOLVED_LIST_ARTICLE_H1_HOLD");
});
test("08 a location-only suffix cannot become parent",()=>{
 assert.equal(titleRelation("2026桃園眷村文化節 桃園市","2026桃園眷村文化節").edgeType,null);
});
test("09 cancellation/postponement in title suffix cannot be promoted",()=>{
 assert.equal(titleRelation("2026桃園眷村文化節 龜山場次延期","2026桃園眷村文化節").edgeType,null);
});
test("10 no visible h1 => evidence HOLD",()=>{
 assert.equal(titleRelation("2026桃園眷村文化節 場次","").kind,"NO_VISIBLE_H1_HOLD");
});
test("11 normalization does not invent new qualifiers",()=>{
 assert.equal(n("  2026 桃園  \n 眷村 "), "2026 桃園 眷村");
});
test("12 E1 frozen parent validates exactly four HTTP200 unmatched",()=>{
 assert.equal(validateParent(parent()).length,4);
});
test("13 reject parent publication/Golden/writer-like source drift",()=>{
 for(const [k,v] of [["published",true],["goldenAccepted",true],
   ["sourceRuntime","ACTIVE"],["fieldPromotionCount",1],
   ["firstPartyEventDetailsIndependentlyVerified",2],["listCandidateCount",25]]){
  const p=parent();p[k]=v;
  assert.throws(()=>validateParent(p),/HOLD_E1_BASELINE_INTEGRITY/,k);
 }
});
test("14 reject forged same URL duplicate and no unique relationship",()=>{
 const p=parent();p.samples[1].aggregatorUrl=p.samples[0].aggregatorUrl;
 assert.throws(()=>validateParent(p),/HOLD_FOUR_HELD_SOURCE_IDENTITIES/);
});
test("15 reject held article external origin link or promoted date",()=>{
 const p=parent();p.samples[0].originalOfficialUrl="https://news.example.com/foo";
 assert.throws(()=>validateParent(p),/HOLD_HELD_ARTICLE_PROVENANCE/);
});
test("16 exact current article HTTP+URL must be bound",()=>{
 const obs=observations();obs[0].currentUrl="https://evil.example.com/path";
 assert.throws(()=>compare(parent(),obs),/HOLD_EXACT_SOURCE_TRANSPORT/);
});
test("17 event graph audit does not auto-merge parent-child",()=>{
 const x=compare(parent(),observations());
 assert.equal(x.reviewedHeldArticleCount,4);
 assert.equal(x.explicitParentChildCandidates,1);
 assert.equal(x.firstPartyNewEventConfirmations,0);
 assert.equal(x.canonicalParentAutoMergeCount,0);
 assert.equal(x.deleteCount,0);
 assert.equal(x.fieldPromotionCount,0);
 assert.equal(x.goldenAccepted,false);
 assert.equal(x.published,false);
 assert.equal(x.originalAndroid44Preserved,true);
});
test("18 all four articles have nil data and unapproved graph edges",()=>{
 const x=compare(parent(),observations());
 for(const row of x.reviews){
  assert.equal(row.originalOfficialUrl,null);
  assert.equal(row.dateStart,null);assert.equal(row.dateEnd,null);
  assert.equal(row.price,null);assert.equal(row.ticketStatus,"UNKNOWN");
  assert.equal(row.edgeApproval,"NOT_VERIFIED");
  assert.equal(row.explicitFirstPartySameEventProof,false);
  assert.equal(row.parentOrSubeventAutoMerged,false);
  assert.equal(row.goldenVerified,false);
 }
});
