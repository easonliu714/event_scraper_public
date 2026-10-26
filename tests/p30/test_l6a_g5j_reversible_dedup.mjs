import test from "node:test";
import assert from "node:assert/strict";
import {KIND,PARENT,BITAN,CAL,classificationHint,pairEvidence,verifyGraph,buildReview} from "../../scripts/p30_l6a_g5j_reversible_dedup.mjs";
const urls=["https://strolltimes.com/events/hsinchu/261016123223/",BITAN,
 "https://strolltimes.com/events/taoyuan/261017111111/",
 "https://strolltimes.com/events/hsinchu/261017222222/",
 "https://strolltimes.com/events/new-taipei/261017333333/",
 "https://strolltimes.com/events/taipei/261017444444/"];
const titles=["2026新竹市萬聖節","碧潭地景裝置展 遇見小王子漫遊碧潭間",
 "2026桃園眷村文化節 龜山眷村故事館場次","2026香山濕地藝術季",
 "2026新北濕地藝術季 《萌芽之境》","2026晴空季"];
const heads=["2026新竹市萬聖節（10/16~10/31）","碧潭地景裝置展 遇見小王子漫遊碧潭間（10/17~12/13）",
 "2026桃園眷村文化節：四大場域一村一家人！施孝榮等開唱（10/9~11/8）",
 "2026香山濕地藝術季：踏走一道波痕8件作品（10/2~11/1）",
 "2026新北濕地藝術季《萌芽之境》：新海二期人工濕地20週年（10/3~11/8）",
 "2026晴空季：打開七萬坪神祕軍事禁地（8/1~11/15）"];
const states=["AGGREGATOR_TITLE_IDENTITY_MATCH","AGGREGATOR_TITLE_IDENTITY_MATCH",
 "TITLE_OVERLAP_RELATIONSHIP_REVIEW","EDITORIAL_HEADLINE_EXTENSION_REVIEW",
 "EDITORIAL_HEADLINE_EXTENSION_REVIEW","EDITORIAL_HEADLINE_EXTENSION_REVIEW"];
const fixture=()=>({
 kind:PARENT,sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",
 sourceRuntime:"DORMANT",published:false,goldenAccepted:false,
 writerExecuted:false,notifierExecuted:false,autoHidden:0,
 accepted44AndroidPreserved:true,sourceEventPromotionCount:0,
 formalDatePromotionCount:0,automaticDedupMergeCount:0,confirmedParentChildEventEdges:0,
 graphReversible:true,all24AggregatorDetailsVerified:false,
 all23OthersOriginalSourcesVerified:false,oneIndependentGovReferenceCount:1,
 currentSampleCount:6,priorArticleSampleCount:6,priorE1ExactH1Count:2,
 currentExactH1Count:2,
 nodes:urls.map((id,i)=>({id,platform:"StrollTimes",
  role:"THIRD_PARTY_EVENT_AGGREGATOR",homepageCardTitle:titles[i],
  articleH1:heads[i],currentTitleState:states[i],
  officialGovernmentProof:i===1?"ONE_INDEPENDENT_GOV_EVENT_CORROBORATED_REVIEW_ONLY":"NOT_VERIFIED",
  sourceEventDateStart:null,sourceEventDateEnd:null,price:null,ticketStatus:"UNKNOWN",
  mergeAllowed:false,goldenVerified:false,published:false})),
 edges:[
  ...urls.map(id=>({from:"strolltimes-home-card:"+id,to:id,
    kind:"AGGREGATOR_LIST_CARD_POINTS_TO_SAME_ARTICLE",
    state:"OBSERVED_SAME_ARTICLE_URL",mergeAllowed:false,originalOrganiserProven:false})),
  {from:BITAN,to:CAL,kind:"ONE_EVENT_OFFICIAL_GOV_CALENDAR_CORROBORATED",
   source:"P30_L5E2_PINNED_GOV_ARTIFACT",
   eventPeriodReviewOnly:["2026-10-17","2026-12-13"],
   state:"INDEPENDENT_FIRST_PARTY_EVIDENCE_FOR_ONE_EVENT",
   organisationAndUpdatesFullyVerified:false,mergeAllowed:false}
 ],
 notesRequiringReview:urls.slice(2).map(articleUrl=>({articleUrl,autoMergeAllowed:false}))
});
test("01 result is offline review only",()=>assert.match(KIND,/REVIEW_ONLY/));
test("02 strict parent graph acceptance",()=>assert.equal(verifyGraph(fixture()),true));
test("03 six nodes and seven evidence edges",()=>{
 const d=buildReview(fixture());assert.equal(d.inputNodes,6);
 assert.equal(d.reviewedCandidates.length,6);assert.equal(d.sourceEvidenceEdges.length,7);
});
test("04 exactly 15 unordered pairs",()=>{
 const d=buildReview(fixture());assert.equal(d.pairedReviewCount,15);
 assert.equal(new Set(d.reviewPairs.map(p=>[p.a,p.b].sort().join("|"))).size,15);
});
test("05 every pair is no merge nor hide nor delete",()=>{
 const d=buildReview(fixture());
 for(const p of d.reviewPairs){
  assert.equal(p.proposedAction,"KEEP_SEPARATE_PENDING_EVIDENCE");
  assert.equal(p.mergeAllowed,false);
  assert.equal(p.autoHideAllowed,false);
  assert.equal(p.deleteAllowed,false);
  assert.equal(p.primarySourceCrossIdentity,"NOT_PROVEN");
 }
});
test("06 no report claims distinct events definitively",()=>{
 const d=buildReview(fixture());
 assert.ok(d.reviewPairs.every(p=>p.relationship==="UNKNOWN_NOT_MERGED"));
});
test("07 article card URL is not a cross-platform event identity",()=>{
 const d=buildReview(fixture());
 assert.equal(d.confirmedDuplicatePairs,0);
 assert.equal(d.tentativeCrossPlatformDuplicates,0);
});
test("08 government corroboration belongs only to Bitan",()=>{
 const d=buildReview(fixture());
 const bitan=d.reviewedCandidates.find(n=>n.id===BITAN);
 assert.equal(bitan.provenance,"ONE_FIRST_PARTY_CALENDAR_CORROBORATED_REVIEW_ONLY");
 assert.equal(bitan.provenanceRank,3);
 assert.deepEqual(bitan.referenceOfficialPeriod,["2026-10-17","2026-12-13"]);
 assert.equal(bitan.referenceOfficialUrl,CAL);
 assert.equal(d.oneGovernmentReferenceCount,1);
});
test("09 government calendar reference not official date field",()=>{
 const d=buildReview(fixture());
 const b=d.reviewedCandidates.find(n=>n.id===BITAN);
 assert.equal(b.dateStart,null);assert.equal(b.dateEnd,null);
 assert.equal(b.officialCategoryVerified,false);
 assert.equal(d.formalDatePromotionCount,0);
});
test("10 all other five articles have no official provenance",()=>{
 const d=buildReview(fixture());
 for(const x of d.reviewedCandidates.filter(x=>x.id!==BITAN)){
  assert.equal(x.provenance,"AGGREGATOR_ONLY");
  assert.equal(x.referenceOfficialUrl,null);
  assert.equal(x.referenceOfficialPeriod,null);
  assert.equal(x.officialOriginalEventDetailVerified,false);
 }
});
test("11 event category keywords produce proposal not official category",()=>{
 const x=classificationHint("2026新竹市萬聖節");
 assert.equal(x.categoryHint,"文化節慶");
 assert.equal(x.reason,"TITLE_KEYWORD_PROPOSAL_ONLY");
});
test("12 exhibition is distinct from sales period",()=>{
 assert.equal(classificationHint("碧潭地景裝置展 遇見小王子").categoryHint,"藝文展覽");
});
test("13 parent/child series candidate still provisional cultural category",()=>{
 const d=buildReview(fixture());
 const t=d.reviewedCandidates.find(x=>x.homepageCardTitle.includes("桃園眷村"));
 assert.equal(t.relationshipRisk,"POSSIBLE_SERIES_SUBEVENT_HOLD");
 assert.equal(t.categoryHint,"文化節慶");
 assert.equal(t.autoMergeAllowed,false);
});
test("14 editorial title variants distinct from parent/child",()=>{
 const d=buildReview(fixture());
 assert.equal(d.reviewedCandidates.filter(x=>x.relationshipRisk==="EDITORIAL_TITLE_SUFFIX_REVIEW").length,3);
});
test("15 competing category terms explicitly HOLD not arbitrary priority",()=>{
 const a=classificationHint("萬聖節裝置展");
 assert.equal(a.categoryHint,"待分類");
 assert.equal(a.reason,"COMPETING_CATEGORY_KEYWORDS_HOLD");
});
test("16 uncategorised unknown preserved",()=>{
 assert.equal(classificationHint("匿名2026活動").categoryHint,"待分類");
 assert.equal(classificationHint("").reason,"EMPTY_TITLE_HOLD");
});
test("17 title or Gregorian year alone does not establish duplicate",()=>{
 const [a,b]=fixture().nodes;const p=pairEvidence(a,b);
 assert.equal(p.sharedTitleEvidence,null);
 assert.equal(p.mergeAllowed,false);
});
test("18 same heading but different source URLs is review only",()=>{
 const a=fixture().nodes[0],b={...fixture().nodes[1],homepageCardTitle:a.homepageCardTitle};
 const v=pairEvidence(a,b);
 assert.equal(v.titleRelationship,"TITLE_OVERLAP_REVIEW_ONLY");
 assert.equal(v.primarySourceCrossIdentity,"NOT_PROVEN");
 assert.equal(v.mergeAllowed,false);
});
test("19 suspicious venue or edition overlap never auto merge",()=>{
 const a={id:urls[0],homepageCardTitle:"2026 桃園眷村文化節 A 場"};
 const b={id:urls[2],homepageCardTitle:"2027 桃園眷村文化節 B 場"};
 const x=pairEvidence(a,b);
 assert.equal(x.venueSame,"NOT_PROVEN");
 assert.equal(x.editionSame,"NOT_PROVEN");
 assert.equal(x.mergeAllowed,false);
});
test("20 forged Golden upstream rejected",()=>{
 let a=fixture();a.goldenAccepted=true;
 assert.throws(()=>verifyGraph(a),/HOLD_L5E3_PARENT_GOVERNANCE/);
});
test("21 any upstream writer/autoHide rejected",()=>{
 for(const [k,v] of [["published",true],["writerExecuted",true],["notifierExecuted",true],
    ["autoHidden",1],["automaticDedupMergeCount",1],["confirmedParentChildEventEdges",1]]){
  const a=fixture();a[k]=v;
  assert.throws(()=>verifyGraph(a),/HOLD_L5E3_PARENT_GOVERNANCE/,k);
 }
});
test("22 bad canonical source URLs and duplicate IDs fail closed",()=>{
 let a=fixture();a.nodes[0].id="https://strolltimes.com.evil.com/events/x/123456789012/";
 assert.throws(()=>verifyGraph(a),/HOLD_GRAPH_CANONICAL_URL_IDENTITY/);
 let b=fixture();b.nodes[2].id=b.nodes[0].id;
 assert.throws(()=>verifyGraph(b),/HOLD_GRAPH_CANONICAL_URL_IDENTITY/);
});
test("23 anti spoof extra Bitan government origin",()=>{
 const a=fixture();a.nodes[3].officialGovernmentProof="ONE_INDEPENDENT_GOV_EVENT_CORROBORATED_REVIEW_ONLY";
 assert.throws(()=>verifyGraph(a),/HOLD_FALSE_GOV_CORROBORATION_ON_OTHER_NODE/);
});
test("24 forged first party detail fields rejected",()=>{
 const a=fixture();a.nodes[0].sourceEventDateStart="2026-10-16";
 assert.throws(()=>verifyGraph(a),/HOLD_UNTRUSTED_GRAPH_NODE_PROMOTION/);
});
test("25 tampered same-article URL edge rejected",()=>{
 const a=fixture();a.edges[0].from="strolltimes-home-card:"+urls[1];
 assert.throws(()=>verifyGraph(a),/HOLD_SEVEN_SOURCE_EDGE_IDENTITY/);
});
test("26 forged government period cannot update event dates",()=>{
 const a=fixture();a.edges[6].eventPeriodReviewOnly=["2026-10-14","2026-12-13"];
 assert.throws(()=>verifyGraph(a),/HOLD_SEVEN_SOURCE_EDGE_IDENTITY/);
});
test("27 missing government edge cannot be silently ignored",()=>{
 const a=fixture();a.edges.pop();
 assert.throws(()=>verifyGraph(a),/HOLD_L5E3_PARENT_GOVERNANCE/);
});
test("28 forged parent-child review approval rejected",()=>{
 const a=fixture();a.notesRequiringReview[0].autoMergeAllowed=true;
 assert.throws(()=>verifyGraph(a),/HOLD_E3_FOUR_REVIEW_NOTES/);
});
test("29 unreviewed extra evidence or fewer HOLD notes rejected",()=>{
 const a=fixture();a.notesRequiringReview.pop();
 assert.throws(()=>verifyGraph(a),/HOLD_E3_FOUR_REVIEW_NOTES/);
});
test("30 no mutations, fully reversible",()=>{
 const d=buildReview(fixture());
 assert.equal(d.restorePlan,"NO_MUTATIONS_WERE_PERFORMED");
 for(const k of ["automaticMergeCount","automaticHideCount","deleteCount",
 "manuallyApprovedMergeCount","actualMergedRecords","officialClassificationPromotions",
 "formalFieldPromotionCount","formalDatePromotionCount"])assert.equal(d[k],0,k);
 assert.equal(d.accepted44AndroidPreserved,true);
 assert.equal(d.sourceRuntime,"DORMANT");
 assert.equal(d.notifierExecuted,false);
});
