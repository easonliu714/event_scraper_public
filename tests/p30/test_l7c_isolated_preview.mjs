import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {mkdtemp,rm,readFile,writeFile} from "node:fs/promises";
import {resolve} from "node:path";
import {KIND,PARENT,PORTALS,safeOfficialUrl,verifyParent,convert,run} from "../../scripts/p30_l7c_isolated_preview.mjs";
const sha=s=>createHash("sha256").update(s).digest("hex");
const URL1="https://www.opentix.life/event/12345";
const URL2="https://strolltimes.com/events/taipei/261017444444/";
function row(platform,url,verified){
 return {candidateId:"er7b_"+sha(platform+"\n"+url).slice(0,24),
 sourcePlatform:platform,sourceRole:platform==="StrollTimes"?"THIRD_PARTY_AGGREGATOR_ARTICLE":"PLATFORM_LISTED_EVENT_UNVERIFIED",
 sourceUrl:url,title:"2026 臺灣城市大型音樂會",listEvidence:{listUrl:url,anchorText:"2026 臺灣城市大型音樂會",provenance:"FRESH_HTML_ANCHOR"},
 detailStatus:verified?"DETAIL_TITLE_PARITY_PASS":"NOT_SAMPLED",detailTitle:verified?"2026 臺灣城市大型音樂會":null,
 detailIdentityVerified:verified,detailHttp:verified?{requestedUrl:url}:undefined,
 fieldEvidence:verified?[{role:"EVENT_PERIOD",label:"活動日期",observedValue:"2026/10/28",sourceUrl:url,
 verification:"FRESH_LABEL_OBSERVED_REVIEW_REQUIRED"}]:[],
 dateStart:null,dateEnd:null,eventTimeZone:null,venue:null,price:null,registrationPeriod:null,
 saleWindow:null,voucherValidity:null,ticketStatus:"UNKNOWN",category:"待分類",
 mergeAllowed:false,goldenVerified:false,published:false};
}
const mock=()=>{
 const items=[row("OPENTIX",URL1,true),row("StrollTimes",URL2,false)];
 const source={kind:PARENT,candidateOrigin:"L7B_ACTUAL_NEW_PUBLIC_HTTP",
 runId:"P30-L7B-FRESH-20261026-155431-123456789abc",actualFreshHTTPRequests:9,
 collectedAtUTC:"2026-10-26T15:54:31Z",fullPlatformCoverageVerified:false,candidateCount:2,
 candidateEventRecords:items,goldenAccepted:0,published:false,formalFieldPromotionCount:0,
 mergeAllowed:false};
 const diagnostics={kind:"EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1",
 candidateOrigin:source.candidateOrigin,runId:source.runId,actualFreshHTTPRequests:9,
 all19PlatformsAttempted:true,platforms:Array.from({length:19},(_,i)=>({platform:"T"+i})),
 fullPlatformCoverageVerified:false,counts:{listCandidates:2},
 writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,published:false,
 goldenAccepted:0,automaticMergeCount:0,automaticHideCount:0,deletedCount:0};
 return {source,diagnostics};
};
const pair=()=>{const a=mock();return convert(a.source,a.diagnostics,Buffer.from(JSON.stringify(a.source)));};
test("01 L7C kind and expected L7B parent are explicit",()=>{
 assert.match(KIND,/ISOLATED_FRESH_REVIEW/);assert.match(PARENT,/FRESH_BOUNDED/);
});
test("02 19 source allowlist entries are keyed",()=>assert.equal(Object.keys(PORTALS).length,19));
test("03 official source HTTPS accepted",()=>{
 assert.equal(safeOfficialUrl("OPENTIX",URL1),true);
 assert.equal(safeOfficialUrl("StrollTimes",URL2),true);
});
test("04 third party host-spoofing rejected",()=>{
 for(const url of ["https://evil.com/x","https://www.opentix.life.evil.com/x",
 "http://www.opentix.life/event/12345","https://user:pass@www.opentix.life/event/12345",
 "javascript:alert(1)"])assert.equal(safeOfficialUrl("OPENTIX",url),false,url);
});
test("05 unrecognized fake platform is rejected",()=>{
 assert.equal(safeOfficialUrl("Fake",URL1),false);
});
test("06 valid pinned raw parent verifies",()=>{
 const {source,diagnostics}=mock();assert.equal(verifyParent(source,diagnostics),true);
});
test("07 immutable candidate id contains source platform and exact URL",()=>{
 const {source,diagnostics}=mock();source.candidateEventRecords[1].candidateId=source.candidateEventRecords[0].candidateId;
 assert.throws(()=>verifyParent(source,diagnostics));
});
test("08 synthetic historical input cannot masquerade as fresh",()=>{
 const a=mock();a.source.candidateOrigin="L7B_SYNTHETIC_TEST_INJECTION_NOT_FRESH";
 assert.throws(()=>verifyParent(a.source,a.diagnostics));
});
test("09 zero GETs or forged run id rejected",()=>{
 for(const [field,value] of [["actualFreshHTTPRequests",0],["runId","P30-L7A-FAKE"]]){
  const a=mock();a.source[field]=value;assert.throws(()=>verifyParent(a.source,a.diagnostics),field);
 }
});
test("10 no formal event date/price/ticket promotion",()=>{
 for(const [key,val] of [["dateStart","2026-10-28"],["price","NT$500"],["ticketStatus","ON_SALE"],
 ["saleWindow",["2026-10-01","2026-10-28"]]]){
  const a=mock();a.source.candidateEventRecords[0][key]=val;
  assert.throws(()=>verifyParent(a.source,a.diagnostics),key);
 }
});
test("11 third-party aggregator cannot be called official ticket platform",()=>{
 const a=mock();a.source.candidateEventRecords[1].sourceRole="PLATFORM_LISTED_EVENT_UNVERIFIED";
 assert.throws(()=>verifyParent(a.source,a.diagnostics));
});
test("12 detail title mismatch cannot inject field evidence",()=>{
 const a=mock();a.source.candidateEventRecords[1].fieldEvidence=[{verification:"FRESH_LABEL_OBSERVED_REVIEW_REQUIRED"}];
 assert.throws(()=>verifyParent(a.source,a.diagnostics));
});
test("13 wrong evidence role or source not accepted",()=>{
 const a=mock();a.source.candidateEventRecords[0].fieldEvidence[0].verification="OFFICIAL_CONFIRMED";
 assert.throws(()=>verifyParent(a.source,a.diagnostics));
});
test("14 anti-publish and anti-writer flags cannot be bypassed",()=>{
 for(const [key,val] of [["published",true],["writerExecuted",true],["schedulerExecuted",true],["goldenAccepted",1]]){
  const a=mock();a.diagnostics[key]=val;assert.throws(()=>verifyParent(a.source,a.diagnostics),key);
 }
});
test("15 one verified + one list-only with no fabricated activity fields",()=>{
 const d=pair();
 assert.equal(d.previewOnly,true);assert.equal(d.published,false);
 assert.equal(d.counts.total,2);assert.equal(d.counts.verifiedDetail,1);
 assert.equal(d.counts.listOnly,1);assert.equal(d.counts.identityHold,0);
 assert.equal(d.actualFreshHTTPRequestsInThisGate,0);
 assert.equal(d.items.find(x=>x.sourcePlatform==="StrollTimes").fieldEvidence.length,0);
 assert.ok(d.items.every(x=>x.dateStart===null&&x.price===null&&x.ticketStatus==="UNKNOWN"));
});
test("16 deterministic preview run only pinned fresh file SHA not wall clock",()=>{
 assert.equal(pair().previewRunId,pair().previewRunId);
 assert.match(pair().sourceCandidateSHA256,/^[a-f0-9]{64}$/);
});
test("17 output docs path forbidden",async()=>{
 const a=mock();const bytes=JSON.stringify(a.source),info=JSON.stringify(a.diagnostics);
 const path=await mkdtemp(resolve("p30-l7c-test-"));
 try {
  await writeFile(path+"/source.json",bytes);await writeFile(path+"/diag.json",info);
  await assert.rejects(()=>run(path+"/source.json",path+"/diag.json","docs/l7c"),/HOLD_PREVIEW_OUTPUT/);
 }finally{await rm(path,{recursive:true,force:true});}
});
test("18 sealed output includes exactly isolated preview trio",async()=>{
 const a=mock();const path=await mkdtemp(resolve("p30-l7c-test-"));
 try{
  await writeFile(path+"/source.json",JSON.stringify(a.source));
  await writeFile(path+"/diag.json",JSON.stringify(a.diagnostics));
  const d=await run(path+"/source.json",path+"/diag.json",path+"/mobile");
  const sums=(await readFile(path+"/mobile/SHA256SUMS.txt","utf8")).trim().split("\n");
  assert.equal(sums.length,3);
  for(const line of sums){const [expected,name]=line.split(/\s+/);
   assert.equal(expected,sha(await readFile(path+"/mobile/"+name)));}
  const saved=JSON.parse(await readFile(path+"/mobile/preview-data.json","utf8"));
  assert.equal(saved.previewRunId,d.previewRunId);
  assert.equal(saved.counts.verifiedDetail,1);
 }finally{await rm(path,{recursive:true,force:true});}
});
