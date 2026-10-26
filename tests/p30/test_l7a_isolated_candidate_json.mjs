import test from "node:test";
import assert from "node:assert/strict";
import {KIND,SCHEMA_VERSION,PARENT,safeSourceUrl,candidateId,checkParent,transform} from "../../scripts/p30_l7a_isolated_candidate_json.mjs";
const S="https://strolltimes.com/events/",F="https://www.famiticket.com.tw/Home/Activity/Info/";
const BITAN=S+"new-taipei/261016084730/",GOV="https://newtaipei.travel/zh-tw/calendar/detail/4058";
const NIER="https://ticket.ibon.com.tw/ActivityInfo/Details/39974",TOUR="https://www.nierconcert.com/12026";
const urls=[S+"hsinchu/261016123223/",BITAN,S+"taoyuan/261017111111/",S+"hsinchu/261017222222/",S+"new-taipei/261017333333/",S+"taipei/261017444444/"];
const make=()=>{
 const list=[];
 const add=(platform,eventUrl,title,provenance,sessionCount=0,official=null,range=null,categoryHint="待分類")=>
  list.push({platform,eventUrl,title,provenance,sessionCount,unverifiedSessionCount:sessionCount,
    referenceFirstPartyUrl:official,referenceTimeRange:range,
    verifiedSourceEventId:platform==="StrollTimes"?"NOT_PROVEN":"TICKET_EVENT_URL_EXACT",
    categoryHint,categoryVerified:false,eventDateStart:null,eventDateEnd:null,
    ticketStatus:"UNKNOWN",price:null,mergeAllowed:false,published:false});
 urls.forEach((url,i)=>add("StrollTimes",url,["2026新竹市萬聖節","碧潭地景裝置展 遇見小王子漫遊碧潭間",
   "2026桃園眷村文化節","2026香山濕地藝術季","2026新北濕地藝術季","2026晴空季"][i],
   "THIRD_PARTY_AGGREGATOR_ONLY",0,i===1?GOV:null,i===1?["2026-10-17","2026-12-13"]:null,i===1?"藝文展覽":"文化節慶"));
 ["A","B","C","D"].forEach((ch,i)=>add("FamiTicket",F+ch.repeat(40),
   ["2026 ITF 台灣國際旅展","臺中市立美術館典藏展","2026 駁二動漫祭","TPBL 高雄全家海神"][i],
   "OFFICIAL_TICKET_DETAIL_EXACT_TITLE"));
 add("ibon","https://ticket.ibon.com.tw/ActivityInfo/Details/40010",
   "RUNIDRE 演出","OFFICIAL_TICKET_DETAIL_EXACT_TITLE",1);
 add("ibon",NIER,"NieR:Orchestra Concert 12026","OFFICIAL_TICKET_DETAIL_EXACT_TITLE",2,TOUR);
 const pairs=[];
 for(let i=0;i<list.length;i++)for(let j=i+1;j<list.length;j++){
  const a=list[i],b=list[j];
  pairs.push({a:a.eventUrl,b:b.eventUrl,crossPlatform:a.platform!==b.platform,
   duplicateAccepted:false,automaticMergeAllowed:false,automaticHideAllowed:false,
   deleteAllowed:false,action:"RETAIN_SEPARATELY_REVIEW_ONLY",
   primarySourceEventIdParity:"NOT_PROVEN_BOTH_SIDES",
   organiserIdentityParity:"NOT_PROVEN_BOTH_SIDES"});
 }
 return {kind:PARENT,sourceEventRecords:12,
  platformBreakdown:{StrollTimes:6,FamiTicket:4,ibon:2},
  candidateRecords:list,totalPairCount:66,examinedPairs:pairs,
  crossPlatformPairCount:44,samePlatformPairCount:22,
  firstPartyReferenceCount:2,firstPartyReferenceEdges:[
   {from:BITAN,to:GOV,kind:"GOV_CALENDAR_ONE_EVENT_REFERENCE",independentEventProof:true,mergeAllowed:false},
   {from:NIER,to:TOUR,kind:"ORIGINAL_PRODUCER_TWO_SHOWS_REFERENCE",independentEventProof:true,
    originalAdditionalShowNoticeTimestampVerified:false,mergeAllowed:false,
    showStartTimes:["2027-02-20T18:00","2027-02-21T14:00"]}],
  inputIbonDetailCount:2,inputIbonSampledShowStartCount:3,
  ibonShowSessionsAreNotSeparateEventRecords:true,
  actualDuplicateEventPairsVerified:0,firstPartySameEventCrossPlatformMatchesVerified:0,
  actualParentChildLinksVerified:0,automaticMergeCount:0,automaticHideCount:0,deleteCount:0,
  confirmedOfficialClassificationCount:0,productionDatePromotionCount:0,productionFieldPromotionCount:0,
  sourceRuntime:"DORMANT",goldenAccepted:false,published:false,writerExecuted:false,
  notifierExecuted:false,autoHidden:0,accepted44AndroidPreserved:true,
  reversibleWithoutWrites:true,sourceEventRoleIntegrity:true};
};
const json=x=>Buffer.from(JSON.stringify(x),"utf8");
const built=()=>{const f=make();return transform(f,json(f));};
test("01 L7A kind/schema is snapshot only",()=>{
 assert.match(KIND,/ISOLATED_SAMPLE/);assert.equal(SCHEMA_VERSION,"1.0.0");
});
test("02 validate complete frozen parent",()=>assert.equal(checkParent(make()),true));
test("03 stable runID is SHA-derived and honest about freshness",()=>{
 const a=built().candidate,b=built().candidate;
 assert.equal(a.runId,b.runId);assert.match(a.runId,/^P30-L7A-SNAPSHOT-[a-f0-9]{16}$/);
 assert.equal(a.actualFreshHTTPRequests,0);assert.equal(a.evidenceAsOfUTC,null);
 assert.equal(a.fullPlatformCoverageVerified,false);assert.equal(a.sampledSourceOnly,true);
});
test("04 12 total candidate IDs unique across 3 roles",()=>{
 const a=built().candidate;
 assert.equal(a.candidateCount,12);assert.equal(a.candidateEventRecords.length,12);
 assert.equal(new Set(a.candidateEventRecords.map(x=>x.candidateId)).size,12);
 assert.deepEqual(a.platformBreakdown,{StrollTimes:6,FamiTicket:4,ibon:2});
});
test("05 deterministic candidateId includes exact platform and URL",()=>{
 const d=make().candidateRecords[0];
 assert.equal(candidateId(d),candidateId(d));
 assert.notEqual(candidateId({...d,platform:"FamiTicket"}),candidateId(d));
});
test("06 every formal event field UNKNOWN/null",()=>{
 const a=built().candidate;
 for(const x of a.candidateEventRecords){
  assert.equal(x.dateStart,null);assert.equal(x.dateEnd,null);assert.equal(x.eventTimeZone,null);
  assert.equal(x.price,null);assert.equal(x.venue,null);assert.equal(x.ticketStatus,"UNKNOWN");
  assert.equal(x.registrationPeriod,null);assert.equal(x.saleWindow,null);
  assert.equal(x.voucherValidity,null);assert.equal(x.category,"待分類");
  assert.equal(x.goldenVerified,false);assert.equal(x.published,false);
  assert.equal(x.assumedFresh,false);
 }
});
test("07 Bitan first-party period is evidence-only not published date",()=>{
 const r=built().candidate.candidateEventRecords.find(x=>x.sourceUrl===BITAN);
 assert.equal(r.officialLinkUrl,GOV);
 assert.deepEqual(r.sourceDateEvidence[0].value,["2026-10-17","2026-12-13"]);
 assert.equal(r.sourceDateEvidence[0].dateRole,"OFFICIAL_EVENT_PERIOD_REVIEW_ONLY");
 assert.equal(r.dateStart,null);assert.equal(r.dateEnd,null);
 assert.equal(r.qualityState,"ONE_GOV_FIRST_PARTY_EVENT_REFERENCE_REVIEW_ONLY");
});
test("08 NIEr show dates retained as same ticket event source",()=>{
 const r=built().candidate.candidateEventRecords.find(x=>x.sourceUrl===NIER);
 assert.equal(r.candidateSessionCount,2);
 assert.equal(r.showSessionEvidence.length,2);
 assert.equal(r.officialLinkUrl,NIER);
 assert.equal(r.firstPartyReferenceUrl,TOUR);
 assert.deepEqual(r.showSessionEvidence.map(x=>x.eventStartLocal),["2027-02-20T18:00","2027-02-21T14:00"]);
 assert.ok(r.showSessionEvidence.every(x=>!x.isEventRecord));
});
test("09 RUNIDRE one show count but no invented precise producer time",()=>{
 const r=built().candidate.candidateEventRecords.find(x=>x.sourcePlatform==="ibon"&&x.sourceUrl!==NIER);
 assert.equal(r.candidateSessionCount,1);assert.deepEqual(r.showSessionEvidence,[]);
});
test("10 66 pairs remain in separate file and no merging",()=>{
 const a=built();assert.equal(a.relations.reviewedPairCount,66);
 assert.equal(a.relations.reviewedCrossPlatformPairs,44);
 assert.equal(a.relations.identities.length,66);
 assert.ok(a.relations.identities.every(x=>x.relationship==="UNPROVEN_DO_NOT_MERGE"&&!x.mergeAllowed));
});
test("11 no automatic delete/hide or Golden in manifest",()=>{
 const a=built().candidate;
 assert.equal(a.automaticMergeCount,0);assert.equal(a.deletedCount,0);
 assert.equal(a.formalFieldPromotionCount,0);assert.equal(a.goldenAccepted,0);
 assert.equal(a.appDataPublished,false);assert.equal(a.notifierExecuted,false);
 assert.equal(a.schedulerExecuted,false);assert.equal(a.sourceRuntime,"DORMANT");
});
test("12 official ticket URLs not misrepresented as organiser primary page",()=>{
 const a=built().candidate;
 assert.ok(a.candidateEventRecords.filter(x=>x.sourcePlatform==="FamiTicket")
 .every(x=>x.officialLinkUrl===x.sourceUrl&&x.firstPartyReferenceUrl===null));
});
test("13 six StrollTimes articles aren't silently first-party events",()=>{
 const a=built().candidate;
 assert.ok(a.candidateEventRecords.filter(x=>x.sourcePlatform==="StrollTimes"&&x.sourceUrl!==BITAN)
  .every(x=>x.officialLinkUrl===null&&x.sourceRole==="THIRD_PARTY_AGGREGATOR_ARTICLE"));
});
test("14 source host must be exact not spoofed",()=>{
 assert.equal(safeSourceUrl("ibon","https://ticket.ibon.com.tw.evil.com/ActivityInfo/Details/39974"),false);
 assert.equal(safeSourceUrl("StrollTimes","https://strolltimes.com.evil.com/events/x/261016123223/"),false);
});
test("15 no forged URL tokens, redirects, credentials or queries",()=>{
 for(const u of ["http://ticket.ibon.com.tw/ActivityInfo/Details/39974",
  NIER+"?token=1",NIER+"#x","https://bad:pw@ticket.ibon.com.tw/ActivityInfo/Details/39974"])
 assert.equal(safeSourceUrl("ibon",u),false,u);
});
test("16 parent Golden/Published/Writer tampering fails",()=>{
 for(const [k,v] of [["published",true],["goldenAccepted",true],["writerExecuted",true],["sourceRuntime","ACTIVE"]]){
  const a=make();a[k]=v;assert.throws(()=>checkParent(a),/HOLD_L6B/,k);
 }
});
test("17 parent miscount 3 ibon events fails",()=>{
 const a=make();a.platformBreakdown.ibon=3;assert.throws(()=>checkParent(a),/HOLD_L6B/);
});
test("18 parent missing one source fails",()=>{
 const a=make();a.candidateRecords.pop();assert.throws(()=>checkParent(a),/HOLD_L6B/);
});
test("19 parent duplicate source URL fails",()=>{
 const a=make();a.candidateRecords[2].eventUrl=a.candidateRecords[0].eventUrl;
 assert.throws(()=>checkParent(a),/HOLD_PARENT_SOURCE_ROW/);
});
test("20 forged event date or price rejected",()=>{
 for(const [key,val] of [["eventDateStart","2026-10-17"],["price",500],["ticketStatus","ON_SALE"]]){
  const a=make();a.candidateRecords[0][key]=val;
  assert.throws(()=>checkParent(a),/HOLD_PARENT_SOURCE_ROW/);
 }
});
test("21 guessed first party gov URL for other article rejected",()=>{
 const a=make();a.candidateRecords[0].referenceFirstPartyUrl=GOV;
 assert.throws(()=>checkParent(a),/HOLD_PARENT_FIRST_PARTY/);
});
test("22 fake Bitan government period in source rejected",()=>{
 const a=make();a.candidateRecords.find(x=>x.eventUrl===BITAN).referenceTimeRange=["2026-10-14","2026-12-13"];
 assert.throws(()=>checkParent(a),/HOLD_PARENT_FIRST_PARTY/);
});
test("23 NIEr new fabricated third show fails",()=>{
 const a=make();a.firstPartyReferenceEdges[1].showStartTimes.push("2027-02-22T14:00");
 assert.throws(()=>checkParent(a),/HOLD_PARENT_FIRST_PARTY/);
});
test("24 forged organizer timestamp for added show fails",()=>{
 const a=make();a.firstPartyReferenceEdges[1].originalAdditionalShowNoticeTimestampVerified=true;
 assert.throws(()=>checkParent(a),/HOLD_PARENT_FIRST_PARTY/);
});
test("25 fake approved duplicate among 66 pairs fails",()=>{
 const a=make();a.examinedPairs[0].duplicateAccepted=true;
 assert.throws(()=>checkParent(a),/HOLD_PARENT_PAIR/);
});
test("26 duplicate pair identity fails even if count still 66",()=>{
 const a=make();a.examinedPairs[1]={...a.examinedPairs[0]};
 assert.throws(()=>checkParent(a),/HOLD_PARENT_DUPLICATE_PAIR/);
});
test("27 wrong source relationship evidence can't promote event",()=>{
 const a=make();a.firstPartyReferenceEdges[0].mergeAllowed=true;
 assert.throws(()=>checkParent(a),/HOLD_PARENT_FIRST_PARTY/);
});
test("28 no verified cross-platform duplicate, no unique claim",()=>{
 const a=built();
 assert.equal(a.relations.verifiedDuplicateCount,0);
 assert.equal(a.candidate.actualFreshHTTPRequests,0);
 assert.equal(a.candidate.existingAndroid44PassPreserved,true);
});
test("29 two source reference edges not two additional event records",()=>{
 const a=built().candidate;
 assert.equal(a.referenceCount,2);assert.equal(a.candidateCount,12);
 assert.equal(a.candidateEventRecords.filter(x=>x.firstPartyReferenceUrl!==null).length,2);
});
test("30 preserving 3 ibon shows means two timed producer evidence, no fake RUNIDRE",()=>{
 const a=built().candidate;
 assert.equal(a.showStartsInPinnnedInput,3);
 assert.equal(a.candidateEventRecords.reduce((n,x)=>n+x.showSessionEvidence.length,0),2);
});
