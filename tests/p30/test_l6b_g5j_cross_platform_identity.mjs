import test from "node:test";
import assert from "node:assert/strict";
import {KIND,strictTicketUrl,verifyInputs,pairStatus,reconcile} from "../../scripts/p30_l6b_g5j_cross_platform_identity.mjs";
const BITAN="https://strolltimes.com/events/new-taipei/261016084730/";
const CAL="https://newtaipei.travel/zh-tw/calendar/detail/4058";
const NIER="https://ticket.ibon.com.tw/ActivityInfo/Details/39974";
const TOUR="https://www.nierconcert.com/12026";
const FBASE="https://www.famiticket.com.tw/Home/Activity/Info/";
const SUFFIX=["A","B","C","D"].map(x=>x.repeat(40));
const AGG=["https://strolltimes.com/events/hsinchu/261016123223/",BITAN,
"https://strolltimes.com/events/taoyuan/261017111111/","https://strolltimes.com/events/hsinchu/261017222222/",
"https://strolltimes.com/events/new-taipei/261017333333/","https://strolltimes.com/events/taipei/261017444444/"];
const sample=(title,officialUrl,proposedSessions)=>({
 listTitle:title,officialUrl,proposedSessions,sessionStatus:"LABELED_SESSION_CANDIDATES_REVIEW_ONLY",
 dateStart:null,dateEnd:null,price:null,ticketStatus:"UNKNOWN",goldenVerified:false,published:false
});
const show=(date,time)=>({eventStartLocal:date+"T"+time,proposedOnly:true,
 admissionIsNotEventStart:true,verifiedAgainstOrganiser:false,verifiedAgainstChangeNotices:false});
const fixture=()=>({
 g5j:{kind:"EVENTRADAR_P30_L6A_G5J_REVERSIBLE_CLASSIFICATION_AND_DEDUP_REVIEW_ONLY",
 inputNodes:6,reviewedCandidates:AGG.map((id,i)=>({id,
 sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",
 homepageCardTitle:["2026新竹市萬聖節","碧潭地景裝置展 遇見小王子漫遊碧潭間","2026桃園眷村文化節 龜山眷村故事館場次",
 "2026香山濕地藝術季","2026新北濕地藝術季 《萌芽之境》","2026晴空季"][i],
 categoryHint:i===1?"藝文展覽":"文化節慶",
 referenceOfficialUrl:i===1?CAL:null,dateStart:null,dateEnd:null,
 autoMergeAllowed:false,goldenVerified:false,published:false})),
 reviewPairs:Array(15).fill({}),sourceEvidenceEdges:Array(7).fill({}),
 oneGovernmentReferenceCount:1,confirmedDuplicatePairs:0,automaticMergeCount:0,automaticHideCount:0,
 deleteCount:0,published:false,goldenAccepted:false,writerExecuted:false,notifierExecuted:false,
 sourceRuntime:"DORMANT",accepted44AndroidPreserved:true},
 fami:{kind:"EVENTRADAR_P30_L5D1_FAMITICKET_OFFICIAL_FIELD_ROLES_REVIEW_ONLY",
 sourceRuntime:"DORMANT",detailSamples:SUFFIX.map((s,i)=>({
  officialUrl:FBASE+s,observedUrl:FBASE+s,detailHttp:200,
  identity:"EXACT_LIST_DETAIL_TITLE_PASS",listTitle:["2026 ITF 台灣國際旅展",
  "臺中市立美術館典藏展","2026 駁二動漫祭","TPBL 高雄全家海神 26–27 主場例行賽"][i],
  dateStart:null,dateEnd:null,venue:null,price:null,ticketStatus:"UNKNOWN",
  goldenVerified:false,published:false,fieldPromotionCount:0})),
  exactTitleMatches:4,listedSampleCount:4,labeledRoleEvidenceCount:3,
  published:false,goldenAccepted:false,writerExecuted:false,notifierExecuted:false,autoHidden:0},
 ibon:{kind:"EVENTRADAR_P30_L5A_IBON_SESSION_ROLE_REVIEW_ONLY",
  sourceCount:2,detailSourcesParsed:2,sessionRoleCandidateCount:3,
  samples:[sample("RUNIDRE 台北演出","https://ticket.ibon.com.tw/ActivityInfo/Details/40010",
   [show("2026-12-19","17:00")]),
   sample("NieR:Orchestra Concert 12026",NIER,
   [show("2027-02-20","18:00"),show("2027-02-21","14:00")])],
  fieldPromotionCount:0,sourceRuntime:"DORMANT",published:false,goldenAccepted:false,
  writerExecuted:false,notifierExecuted:false,autoHidden:0},
 nier:{kind:"EVENTRADAR_P30_L5C_NIER_PRODUCER_CROSS_SOURCE_REVIEW_ONLY",
  officialOriginalTicketUrl:NIER,producerSourceUrl:TOUR,
  producerDetailUrl:"https://www.nierconcert.com/12026/taipei-2",
  producerOriginalTwoStartsSame:true,producerSessionCount:2,
  originalOfficialStarts:["2027-02-20T18:00","2027-02-21T14:00"],
  additionalShowAnnouncementIndependentlyVerified:false,
  organiserChangeApproval:"NOT_VERIFIED",announcementTimestampVerified:false,
  dateStart:null,dateEnd:null,ticketStatus:"UNKNOWN",price:null,
  formalFieldPromotionCount:0,goldenAccepted:false,published:false,
  writerExecuted:false,notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT"}
});
function wrong(path,value){
 const d=fixture(),pts=path.split("."),last=pts.pop();
 let x=d;for(const k of pts)x=x[k];x[last]=value;return d;
}
test("01 exact source kind is review-only",()=>assert.match(KIND,/REVIEW_ONLY/));
test("02 valid four-pinned-input governance fixture",()=>assert.equal(verifyInputs(fixture()),true));
test("03 6+4+2 event records only",()=>{
 const p=reconcile(fixture());
 assert.equal(p.sourceEventRecords,12);
 assert.deepEqual(p.platformBreakdown,{StrollTimes:6,FamiTicket:4,ibon:2});
});
test("04 exact 66 pairs and 44 cross-platform, 22 same-platform",()=>{
 const p=reconcile(fixture());assert.equal(p.totalPairCount,66);
 assert.equal(p.crossPlatformPairCount,44);assert.equal(p.samePlatformPairCount,22);
});
test("05 ibon three shows are only two EVENT source IDs",()=>{
 const p=reconcile(fixture());
 assert.equal(p.inputIbonSampledShowStartCount,3);
 assert.equal(p.inputIbonDetailCount,2);
 assert.equal(p.ibonShowSessionsAreNotSeparateEventRecords,true);
 assert.deepEqual(p.candidateRecords.filter(e=>e.platform==="ibon")
  .map(e=>e.sessionCount).sort(),[1,2]);
});
test("06 NieR producer is original reference, not a separate ticket event",()=>{
 const p=reconcile(fixture());const e=p.firstPartyReferenceEdges.find(x=>x.to===TOUR);
 assert.equal(e.from,NIER);assert.equal(e.independentEventProof,true);
 assert.equal(e.originalAdditionalShowNoticeTimestampVerified,false);
 assert.equal(e.mergeAllowed,false);
});
test("07 Bitan govt is independent reference only",()=>{
 const p=reconcile(fixture());const e=p.firstPartyReferenceEdges.find(x=>x.to===CAL);
 assert.equal(e.from,BITAN);assert.equal(e.role,"OFFICIAL_EVENT_PERIOD_REVIEW_ONLY");
 assert.equal(p.firstPartySameEventCrossPlatformMatchesVerified,0);
});
test("08 government period reference stays separate from event Start",()=>{
 const p=reconcile(fixture());const b=p.candidateRecords.find(x=>x.eventUrl===BITAN);
 assert.deepEqual(b.referenceTimeRange,["2026-10-17","2026-12-13"]);
 assert.equal(b.eventDateStart,null);assert.equal(b.eventDateEnd,null);
});
test("09 one producer show is not admission time",()=>{
 const p=reconcile(fixture());
 assert.deepEqual(p.firstPartyReferenceEdges.find(x=>x.to===TOUR).showStartTimes,
  ["2027-02-20T18:00","2027-02-21T14:00"]);
});
test("10 distinct source website domain cannot be spoofed",()=>{
 assert.equal(strictTicketUrl("https://ticket.ibon.com.tw.evil.com/ActivityInfo/Details/39974","ibon"),false);
 assert.equal(strictTicketUrl("https://www.famiticket.com.tw.evil.com/Home/Activity/Info/"+SUFFIX[0],"FamiTicket"),false);
});
test("11 no http/token/query/hash/port in primary event URL",()=>{
 for(const u of ["http://ticket.ibon.com.tw/ActivityInfo/Details/39974",
   "https://ticket.ibon.com.tw/ActivityInfo/Details/39974?x=1",
   "https://ticket.ibon.com.tw/ActivityInfo/Details/39974#ref",
   "https://ticket.ibon.com.tw:8443/ActivityInfo/Details/39974",
   "https://login:pass@ticket.ibon.com.tw/ActivityInfo/Details/39974"])
  assert.equal(strictTicketUrl(u,"ibon"),false,u);
});
test("12 valid ticket event URL syntax",()=>{
 assert.equal(strictTicketUrl(NIER,"ibon"),true);
 assert.equal(strictTicketUrl(FBASE+SUFFIX[0],"FamiTicket"),true);
});
test("13 a title-equal distinct URL remains HOLD",()=>{
 const a={eventUrl:AGG[0],platform:"StrollTimes",title:"同一活動"};
 const b={eventUrl:FBASE+SUFFIX[0],platform:"FamiTicket",title:"同一活動"};
 const p=pairStatus(a,b);assert.equal(p.titleEqualityObservation,"SAME_VISIBLE_TITLE_REVIEW_ONLY");
 assert.equal(p.duplicateAccepted,false);assert.equal(p.automaticMergeAllowed,false);
});
test("14 same exact URL passed as distinct IDs fail",()=>{
 const a={eventUrl:NIER,platform:"ibon",title:"a"};
 assert.throws(()=>pairStatus(a,a),/HOLD_DUPLICATE_PLATFORM_EVENT_IDENTITY/);
});
test("15 first-party ticket URL is a source ID not organiser shared identity",()=>{
 const p=reconcile(fixture());
 assert.ok(p.examinedPairs.every(x=>x.primarySourceEventIdParity==="NOT_PROVEN_BOTH_SIDES"));
});
test("16 title/date/venue sameness alone never merges",()=>{
 const p=reconcile(fixture());
 assert.ok(p.examinedPairs.every(x=>x.organiserIdentityParity==="NOT_PROVEN_BOTH_SIDES"&&
  x.venueIdentityParity==="NOT_PROVEN_BOTH_SIDES"&&
  x.eventDateRoleParity==="NOT_PROVEN_BOTH_SIDES"&&
  x.showSessionIdentityParity==="NOT_PROVEN"));
});
test("17 same organiser may host different editions, no guessed match",()=>{
 const x=pairStatus({eventUrl:AGG[0],platform:"StrollTimes",title:"2026 文化節"},
  {eventUrl:FBASE+SUFFIX[0],platform:"FamiTicket",title:"2027 文化節"});
 assert.equal(x.activityEditionParity,"NOT_PROVEN");assert.equal(x.deleteAllowed,false);
});
test("18 all 66 pairs keep separate and review",()=>{
 const p=reconcile(fixture());
 assert.ok(p.examinedPairs.every(x=>x.action==="RETAIN_SEPARATELY_REVIEW_ONLY"&&
  !x.automaticMergeAllowed&&!x.automaticHideAllowed&&!x.deleteAllowed));
});
test("19 outputs preserve source provenance",()=>{
 const p=reconcile(fixture());
 assert.equal(p.candidateRecords.filter(x=>x.provenance==="OFFICIAL_TICKET_DETAIL_EXACT_TITLE").length,6);
 assert.equal(p.candidateRecords.filter(x=>x.provenance==="THIRD_PARTY_AGGREGATOR_ONLY").length,6);
});
test("20 false Golden in any upstream rejected",()=>{
 for(const k of ["g5j","fami","ibon","nier"]){const d=fixture();d[k].goldenAccepted=true;
  assert.throws(()=>verifyInputs(d),/HOLD_/);}
});
test("21 forged published in any upstream rejected",()=>{
 for(const k of ["g5j","fami","ibon","nier"]){const d=fixture();d[k].published=true;
  assert.throws(()=>verifyInputs(d),/HOLD_/);}
});
test("22 forged prior G5J duplicate approvals rejected",()=>{
 assert.throws(()=>verifyInputs(wrong("g5j.confirmedDuplicatePairs",1)),/HOLD_L6A/);
});
test("23 E1 false government reference rejected",()=>{
 const d=fixture();d.g5j.reviewedCandidates[0].referenceOfficialUrl=CAL;
 assert.throws(()=>verifyInputs(d),/HOLD_AGGREGATOR/);
});
test("24 FamiTicket detail title/HTTP and same-ID duplicates rejected",()=>{
 const d=fixture();d.fami.detailSamples[0].identity="OTHER";
 assert.throws(()=>verifyInputs(d),/HOLD_FAMITICKET_DETAIL/);
 const x=fixture();x.fami.detailSamples[1].officialUrl=x.fami.detailSamples[0].officialUrl;
 assert.throws(()=>verifyInputs(x),/HOLD_FAMITICKET_DETAIL/);
});
test("25 FamiTicket series-derived event date cannot pass",()=>{
 const d=fixture();d.fami.detailSamples[3].dateStart="2026-10-08";
 assert.throws(()=>verifyInputs(d),/HOLD_FAMITICKET_DETAIL/);
});
test("26 ibon ticket checkout/status derived from button prohibited",()=>{
 const d=fixture();d.ibon.samples[0].ticketStatus="ON_SALE";
 assert.throws(()=>verifyInputs(d),/HOLD_IBON_EVENT/);
});
test("27 synthetic session count 3 as standalone events rejected",()=>{
 const d=fixture();d.ibon.sourceCount=3;
 assert.throws(()=>verifyInputs(d),/HOLD_IBON_TWO_DETAILS/);
});
test("28 invented ibon session/tz evidence forbidden",()=>{
 const d=fixture();d.ibon.samples[1].proposedSessions[0].verifiedAgainstOrganiser=true;
 assert.throws(()=>verifyInputs(d),/HOLD_IBON_SHOW/);
});
test("29 no new producer show date without original sample parity",()=>{
 const d=fixture();d.nier.originalOfficialStarts=["2027-02-20T18:00","2027-02-22T14:00"];
 assert.throws(()=>verifyInputs(d),/HOLD_NIER/);
});
test("30 sale opening vs show start cannot become formal event field",()=>{
 const d=fixture();d.nier.dateStart="2026-10-21";
 assert.throws(()=>verifyInputs(d),/HOLD_NIER/);
});
test("31 absent timestamped added-show announcement not forged",()=>{
 const d=fixture();d.nier.announcementTimestampVerified=true;
 assert.throws(()=>verifyInputs(d),/HOLD_NIER/);
});
test("32 producer domain event details must match fixed source",()=>{
 const d=fixture();d.nier.producerDetailUrl="https://evil.com/12026/taipei-2";
 assert.throws(()=>verifyInputs(d),/HOLD_NIER/);
});
test("33 no formal source writer, merge, delete, notif or hide",()=>{
 const p=reconcile(fixture());
 for(const k of ["confirmedCrossPlatformMerges","automaticMergeCount","automaticHideCount",
  "deleteCount","confirmedOfficialClassificationCount","productionDatePromotionCount",
  "productionFieldPromotionCount","actualDuplicateEventPairsVerified",
  "actualParentChildLinksVerified"])assert.equal(p[k],0,k);
 assert.equal(p.sourceRuntime,"DORMANT");
 assert.equal(p.accepted44AndroidPreserved,true);
 assert.equal(p.reversibleWithoutWrites,true);
 assert.equal(p.goldenAccepted,false);assert.equal(p.published,false);
 assert.equal(p.writerExecuted,false);assert.equal(p.notifierExecuted,false);
});
test("34 absence of comparable official evidence is not proof all 12 unique",()=>{
 const p=reconcile(fixture());
 assert.equal(p.actualDuplicateEventPairsVerified,0);
 assert.equal(p.firstPartySameEventCrossPlatformMatchesVerified,0);
 assert.equal(p.examinedPairs.length,66);
});
