import test from "node:test";
import assert from "node:assert/strict";
import {KIND,PARENT_E1,PARENT_E2,BITAN,lexicalIdentity,validateParents,graphFromEvidence} from "../../scripts/p30_l5e3_strolltimes_identity_graph.mjs";
const urls=["https://strolltimes.com/events/hsinchu/261016123223/",BITAN,
 "https://strolltimes.com/events/taoyuan/261017111111/",
 "https://strolltimes.com/events/hsinchu/261017222222/",
 "https://strolltimes.com/events/new-taipei/261017333333/",
 "https://strolltimes.com/events/taipei/261017444444/"];
const titles=["2026新竹市萬聖節","碧潭地景裝置展 遇見小王子漫遊碧潭間",
 "2026桃園眷村文化節 龜山眷村故事館場次","2026香山濕地藝術季",
 "2026新北濕地藝術季 《萌芽之境》","2026晴空季"];
const h1=["2026新竹市萬聖節","碧潭地景裝置展 遇見小王子漫遊碧潭間",
 "2026桃園眷村文化節","2026香山濕地藝術季 開幕式",
 "2026新北濕地藝術季","異地不相關展覽"];
const E1=()=>({kind:PARENT_E1,listCandidateCount:24,articleSamplesCount:6,
 sourceRuntime:"DORMANT",published:false,goldenAccepted:false,fieldPromotionCount:0,
 firstPartyEventDetailsIndependentlyVerified:0,exactAggregatorArticleCount:2,
 samples:urls.map((aggregatorUrl,i)=>({
  aggregatorUrl,title:titles[i],articleIdentity:i<2?"AGGREGATOR_ARTICLE_H1_MATCH":"ARTICLE_TITLE_OR_HTTP_HOLD",
  originalOfficialUrl:null,dateStart:null,dateEnd:null,published:false,goldenVerified:false
 }))});
const E2=()=>({kind:PARENT_E2,sourceAggregatorUrl:BITAN,
 officialFirstPartyIndependentEventIdentityCount:1,
 reviewOnlyOfficialEventUrl:"https://newtaipei.travel/zh-tw/calendar/detail/4058",
 reviewOnlyOfficialEventPeriod:["2026-10-17","2026-12-13"],
 original44AndroidPreserved:true,allOtherAggregatorArticlesVerified:false,
 sourceRuntime:"DORMANT",published:false,goldenAccepted:false,finalDatePromotionCount:0});
const OBS=()=>urls.map((u,i)=>({aggregatorUrl:u,httpStatus:200,finalUrl:u,h1:h1[i]}));
test("01 dedicated gate cannot be interpreted as Golden",()=>assert.match(KIND,/REVIEW_ONLY/));
test("02 full exact title evidence but no auto merge",()=>{
 const x=lexicalIdentity(titles[0],h1[0]);
 assert.equal(x.state,"AGGREGATOR_TITLE_IDENTITY_MATCH");
 assert.equal(x.mergeAllowed,false);
});
test("03 aggregator display mm/dd suffix is title-only, not event date",()=>{
 const x=lexicalIdentity("2026新竹市萬聖節","2026新竹市萬聖節（10/16~10/31）");
 assert.equal(x.state,"AGGREGATOR_TITLE_IDENTITY_MATCH");
 assert.equal(x.parentChildRelationship,"NOT_PROVEN");
});
test("04 article shorter parent-looking phrase only proposal",()=>{
 const x=lexicalIdentity(titles[2],h1[2]);
 assert.equal(x.state,"TITLE_OVERLAP_RELATIONSHIP_REVIEW");
 assert.equal(x.parentChildRelationship,"POSSIBLE_PARENT_OR_SUBEVENT_NOT_VERIFIED");
 assert.equal(x.mergeAllowed,false);
});
test("05 article title with addition remains review, not same event",()=>{
 const x=lexicalIdentity(titles[3],h1[3]);
 assert.equal(x.state,"TITLE_OVERLAP_RELATIONSHIP_REVIEW");
 assert.equal(x.mergeAllowed,false);
});
test("06 title entirely different is disjoint hold",()=>{
 const x=lexicalIdentity("2026晴空季","2026碧潭小王子展");
 assert.equal(x.state,"DISJOINT_TITLE_IDENTITY_HOLD");
 assert.equal(x.mergeAllowed,false);
});
test("07 shared Gregorian year alone is never evidence",()=>{
 const x=lexicalIdentity("2026 ABC 測試","2026 XYZ 節慶");
 assert.equal(x.state,"DISJOINT_TITLE_IDENTITY_HOLD");
});
test("08 generic two Han characters are too weak",()=>{
 const x=lexicalIdentity("新竹2026","新竹2027");
 assert.equal(x.state,"DISJOINT_TITLE_IDENTITY_HOLD");
});
test("09 whitespace/punctuation cosmetic equality still not official authority",()=>{
 const x=lexicalIdentity("碧潭地景裝置展 遇見小王子漫遊碧潭間",
 "碧潭地景裝置展 遇見小王子漫遊碧潭間");
 assert.equal(x.state,"AGGREGATOR_TITLE_IDENTITY_MATCH");
 assert.equal(x.mergeAllowed,false);
});
test("10 blank rendered H1 is explicit hold",()=>{
 assert.equal(lexicalIdentity("好活動","").state,"ARTICLE_H1_EMPTY_HOLD");
});
test("11 E1 and E2 pinned governed parent accepted",()=>assert.equal(validateParents(E1(),E2()),true));
test("12 E1 forged officiality blocked",()=>{
 let q=E1();q.fieldPromotionCount=1;
 assert.throws(()=>validateParents(q,E2()),/HOLD_E1_GOVERNANCE/);
});
test("13 E1 forged published/sample source refused",()=>{
 let q=E1();q.samples[0].published=true;
 assert.throws(()=>validateParents(q,E2()),/HOLD_E1_SAMPLE_FIELD_PROMOTION/);
});
test("14 E1 off-domain article rejected",()=>{
 let q=E1();q.samples[0].aggregatorUrl="https://evil.com/events/x/123456789012/";
 assert.throws(()=>validateParents(q,E2()),/HOLD_E1_SOURCE_ARTICLE_URL_IDENTITY/);
});
test("15 E1 duplicate URL identity rejected",()=>{
 let q=E1();q.samples[2].aggregatorUrl=q.samples[0].aggregatorUrl;
 assert.throws(()=>validateParents(q,E2()),/HOLD_E1_SOURCE_ARTICLE_URL_IDENTITY/);
});
test("16 E2 forged 24 approvals rejected",()=>{
 let q=E2();q.allOtherAggregatorArticlesVerified=true;
 assert.throws(()=>validateParents(E1(),q),/HOLD_E2_SINGLE_OFFICIAL_BITAN_PROOF/);
});
test("17 E2 incorrect date or primary URL rejected",()=>{
 let q=E2();q.reviewOnlyOfficialEventPeriod=["2026-10-14","2026-12-13"];
 assert.throws(()=>validateParents(E1(),q),/HOLD_E2_SINGLE_OFFICIAL_BITAN_PROOF/);
});
test("18 two exact identities, four review titles, no auto merge",()=>{
 let g=graphFromEvidence(E1(),E2(),OBS(),{navigationCount:6});
 assert.equal(g.nodes.length,6);assert.equal(g.edges.length,7);
 assert.equal(g.currentExactH1Count,2);
 assert.equal(g.automaticDedupMergeCount,0);
 assert.equal(g.confirmedParentChildEventEdges,0);
 assert.equal(g.graphReversible,true);
 assert.equal(g.notesRequiringReview.length,4);
});
test("19 E2 calendar proof remains only BItan node",()=>{
 let g=graphFromEvidence(E1(),E2(),OBS());
 assert.equal(g.oneIndependentGovReferenceCount,1);
 assert.equal(g.edges.filter(e=>e.kind==="ONE_EVENT_OFFICIAL_GOV_CALENDAR_CORROBORATED").length,1);
 assert.equal(g.nodes.filter(e=>e.officialGovernmentProof==="ONE_INDEPENDENT_GOV_EVENT_CORROBORATED_REVIEW_ONLY").length,1);
});
test("20 no stage upgrades ticket or date/availability",()=>{
 let g=graphFromEvidence(E1(),E2(),OBS());
 for(const n of g.nodes){
  assert.equal(n.sourceEventDateStart,null);assert.equal(n.sourceEventDateEnd,null);
  assert.equal(n.ticketStatus,"UNKNOWN");assert.equal(n.price,null);
  assert.equal(n.goldenVerified,false);assert.equal(n.published,false);
  assert.equal(n.mergeAllowed,false);
 }
 assert.equal(g.formalDatePromotionCount,0);assert.equal(g.sourceEventPromotionCount,0);
 assert.equal(g.goldenAccepted,false);assert.equal(g.published,false);
 assert.equal(g.accepted44AndroidPreserved,true);
});
test("21 redirect or HTTP403 does not match",()=>{
 const obs=OBS();obs[0].httpStatus=403;obs[1].finalUrl="https://evil.com";
 const x=graphFromEvidence(E1(),E2(),obs);
 assert.equal(x.nodes[0].currentTitleState,"HTTP_OR_REDIRECT_HOLD");
 assert.equal(x.nodes[1].currentTitleState,"HTTP_OR_REDIRECT_HOLD");
});
test("22 duplicate observed URL can't be silently reused",()=>{
 const ob=OBS();ob[1].aggregatorUrl=ob[0].aggregatorUrl;
 assert.throws(()=>graphFromEvidence(E1(),E2(),ob),/HOLD_DUPLICATE_OR_FOREIGN_OBSERVED_URL/);
});
test("23 source missing in observation cannot pass",()=>{
 const ob=OBS();ob[1].aggregatorUrl="https://strolltimes.com/events/taipei/261017555555/";
 assert.throws(()=>graphFromEvidence(E1(),E2(),ob),/HOLD_MISSING_OBSERVED_SOURCE/);
});
test("24 new DOM title matching cannot rewrite old mismatch",()=>{
 const ob=OBS();ob[2].h1=titles[2];
 const x=graphFromEvidence(E1(),E2(),ob);
 assert.equal(x.nodes[2].currentTitleState,"AGGREGATOR_TITLE_IDENTITY_MATCH");
 assert.ok(x.notesRequiringReview.some(a=>a.role==="HISTORICAL_TITLE_DRIFT_REVIEW_ONLY"));
});
test("25 source graph exact edge only same aggregator article",()=>{
 const x=graphFromEvidence(E1(),E2(),OBS());
 for(const ed of x.edges.filter(x=>x.kind==="AGGREGATOR_LIST_CARD_POINTS_TO_SAME_ARTICLE")){
  assert.equal(ed.mergeAllowed,false);assert.equal(ed.originalOrganiserProven,false);
 }
});

test("26 short 2026 晴空季 title followed by editorial subtitle is not disjoint",()=>{
 const x=lexicalIdentity("2026晴空季",
   "2026晴空季：打開七萬坪神祕軍事禁地，嗨玩全台最狂文化機場（8/1~11/15）");
 assert.equal(x.state,"EDITORIAL_HEADLINE_EXTENSION_REVIEW");
 assert.equal(x.parentChildRelationship,"EDITORIAL_SUBTITLE_RELATIONSHIP_NOT_PROVEN");
 assert.equal(x.mergeAllowed,false);
});
test("27 nonbreaking editorial spacing must never silently merge event",()=>{
 const x=lexicalIdentity("2026新北濕地藝術季 《萌芽之境》",
   "2026新北濕地藝術季《萌芽之境》：新海二期人工濕地20週年！");
 assert.equal(x.state,"EDITORIAL_HEADLINE_EXTENSION_REVIEW");
 assert.equal(x.mergeAllowed,false);
});
