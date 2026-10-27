import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {KIND,PARENT_KIND,PARENT_HEAD,PARENT_RUN,PARENT_ARTIFACT,SOURCE_IDS,HOLD,
 canonical,role,evaluateProbe,validateParent,reviewStructures,validateReport,
 run,safeOut,emit} from "../../scripts/p30_l9g_ibon_rendered_field_structure.mjs";
const sha=b=>createHash("sha256").update(b).digest("hex");
const T="台灣示範音樂活動";
function fixture(){
 const p={kind:PARENT_KIND,parentL9EHead:"63a079c1bee7111b1ef7b04431607d9845fe3b9f",
  parentL9ERun:40449476633,parentArtifactId:12709568132,parentCandidateCount:22,
  previousDetailTitleParity:1,additionalSampleSize:5,additionalTitleParity:5,
  additionalRoleEvidenceCount:0,additionalRejectedEvidenceCount:0,
  goldenAccepted:0,formalFieldPromotions:0,sessionSplits:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,releaseState:HOLD,existingAndroid44Preserved:true,
  l8CoreAndroidPassPreserved:true,
  samples:SOURCE_IDS.map((id,i)=>({candidateId:"ibon:"+id,
    officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,
    listTitle:T+" "+i,detailState:"DETAIL_TITLE_PARITY_PASS",
    titleParity:true,httpStatus:200,formalDate:null,formalPrice:null,
    ticketStatus:"UNKNOWN",fieldPromotions:0,published:false}))};
 return {p,raw:Buffer.from(JSON.stringify(p))};
}
const probe=(label,value,structure="LOCAL_SIBLING")=>({label,value,structure});
function synthetic(parent,config={}){
 const visited=[],titles=new Map(parent.samples.map(x=>[x.officialUrl,x.listTitle]));
 const browser={launch:async()=>({
   newContext:async()=>({
    newPage:async()=>({
     pageUrl:"",
     async goto(url){this.pageUrl=url;visited.push(url);return{status:()=>config.httpStatus??200};},
     url(){return config.external?"https://evil.example/":this.pageUrl;},
     async waitForTimeout(){},
     async evaluate(){
      return {headings:config.mismatch?["另一活動"]:[titles.get(this.pageUrl)],
       roleProbes:config.probes??[
        probe("活動日期","2026/10/31 19:00"),
        probe("售票期間","2026/10/01 12:00"),
        probe("票價","資訊")],
       recognizedLabelNodes:3,imagesNearLabels:0,bodyTextLength:1250,
       domTagCounts:{table:0,th:0,dt:0,strong:5,img:3}};
     },
     async close(){}
    }),async close(){}
   }),async close(){}
 })};
 return{browser,visited};
}
test("01 exact typed read-only result",()=>assert.match(KIND,/FIELD_STRUCTURE_READONLY/));
test("02 canonical five source IDs",()=>{
 for(const id of SOURCE_IDS)assert.equal(canonical("https://ticket.ibon.com.tw/ActivityInfo/Details/"+id),id);
});
test("03 offhost, wrong path, query, http rejected",()=>{
 for(const u of ["http://ticket.ibon.com.tw/ActivityInfo/Details/39575",
 "https://evil.com/ActivityInfo/Details/39575",
 "https://ticket.ibon.com.tw/login",
 "https://ticket.ibon.com.tw/ActivityInfo/Details/39575?x=1",
 "https://ticket.ibon.com.tw/ActivityInfo/Details/abc"]){
  assert.equal(canonical(u),null,u);
 }
});
test("04 parent SHA and five exact identities",()=>{
 const f=fixture();const p=validateParent(f.p,f.raw);
 assert.equal(p.sha256,sha(f.raw));assert.equal(p.rows.length,5);
});
test("05 counterfeit parent rejects incorrect sample count",()=>{
 const f=fixture();f.p.additionalSampleSize=4;assert.throws(()=>validateParent(f.p,f.raw));
});
test("06 counterfeit identity or duplicate rejected",()=>{
 for(const mutation of [x=>x.samples[0].candidateId="ibon:99999",
 x=>x.samples[0].officialUrl=x.samples[1].officialUrl,
 x=>x.samples[0].officialUrl="https://evil.com/event/39575"]){
  const f=fixture();mutation(f.p);assert.throws(()=>validateParent(f.p,f.raw));
 }
});
test("07 prior incomplete detail no authority",()=>{
 const f=fixture();f.p.samples[0].titleParity=false;assert.throws(()=>validateParent(f.p,f.raw));
});
test("08 source field, Golden, publisher tamper rejects",()=>{
 for(const [key,value] of [["formalFieldPromotions",1],["published",true],["goldenAccepted",1],["writerExecuted",true]]){
  const f=fixture();f.p[key]=value;assert.throws(()=>validateParent(f.p,f.raw));
 }
});
test("09 event date recognised, sale not event",()=>{
 assert.equal(role("活動日期"),"EVENT_PERIOD");assert.equal(role("售票時間"),"SALE_PERIOD");
});
test("10 entry, registration, voucher distinct",()=>{
 assert.equal(role("入場時間"),"ADMISSION_TIME");
 assert.equal(role("報名期間"),"REGISTRATION_PERIOD");
 assert.equal(role("票券有效期限"),"VOUCHER_VALIDITY");
});
test("11 venue, price and session roles distinct",()=>{
 assert.equal(role("演出場館"),"VENUE");
 assert.equal(role("票價"),"PRICE");
 assert.equal(role("演出場次"),"SESSION");
});
test("12 ambiguous generic time/title never treated as date",()=>{
 for(const x of ["時間","活動資訊","節目介紹","購票","更多"])
  assert.equal(role(x),null,x);
});
test("13 valid local sibling event date remains review only",()=>{
 const r=evaluateProbe(probe("活動日期","2026/10/31 19:00"));
 assert.equal(r.role,"EVENT_PERIOD");assert.equal(r.quality,"TIME_ROLE_REVIEW_ONLY");
 assert.equal(r.promotable,false);assert.equal(r.formalFieldPromoted,false);
});
test("14 sale-admission role separation",()=>{
 assert.equal(evaluateProbe(probe("售票時間","2026/10/01 12:00")).role,"SALE_PERIOD");
 assert.equal(evaluateProbe(probe("入場時間","2026/10/31 17:00")).role,"ADMISSION_TIME");
});
test("15 PRICE 資訊 is rejected",()=>{
 assert.equal(evaluateProbe(probe("票價","資訊")).quality,"REJECT_GENERIC_PRICE_TEXT");
});
test("16 numeric price remains review-only, no official formal price",()=>{
 const r=evaluateProbe(probe("票價","NT$ 800"));
 assert.equal(r.quality,"PRICE_TOKEN_REVIEW_ONLY");assert.equal(r.promotable,false);
});
test("17 sale date inside event date is a role conflict",()=>{
 const r=evaluateProbe(probe("活動日期","2026/10/01 12:00 售票開賣"));
 assert.equal(r.quality,"HOLD_CROSS_ROLE_EVENT_DATE");
});
test("18 event date text without date is rejected",()=>{
 assert.equal(evaluateProbe(probe("演出時間","請依官方公告")).quality,"REJECT_MISSING_DATE_TIME");
});
test("19 venue generic text rejected",()=>{
 assert.equal(evaluateProbe(probe("場地","資訊")).quality,"REJECT_GENERIC_VENUE");
});
test("20 SESSION multiple shows never split into new events",()=>{
 const r=evaluateProbe(probe("場次","10/28 14:00、10/28 19:00"));
 assert.equal(r.quality,"SESSION_MULTIPLE_SHOWS_REVIEW_ONLY_NO_SPLIT");
});
test("21 label without local binding is HOLD",()=>{
 const r=evaluateProbe(probe("售票時間","2026/10/01","UNBOUND_GLOBAL_TEXT"));
 assert.equal(r.quality,"HOLD_UNBOUND_DOM_STRUCTURE");
 assert.equal(r.verified,false);assert.equal(r.formalFieldPromoted,false);
});
test("22 empty adjacent value rejected as evidence",()=>{
 const r=evaluateProbe(probe("票價",""));
 assert.equal(r.quality,"REJECT_EMPTY_OR_OVERSIZE");
 assert.equal(r.formalFieldPromoted,false);
});
test("23 unknown field label does not create candidate",()=>{
 assert.equal(evaluateProbe(probe("品牌代碼","2026/10/31")),null);
});
test("24 structural no match means no guessed values",()=>{
 const d={roleProbes:[],recognizedLabelNodes:0};
 const r=reviewStructures(d,true);
 assert.equal(r.accepted.length,0);assert.equal(r.rejected.length,0);
});
test("25 five probes bounded and deduplicated",()=>{
 const p=[probe("票價","資訊"),probe("票價","資訊"),probe("活動日期","2026/10/31")];
 const r=reviewStructures({roleProbes:p,recognizedLabelNodes:2},true);
 assert.equal(r.accepted.length,1);assert.equal(r.rejected.length,1);
});
test("26 failed title parity suppresses every role",()=>{
 const r=reviewStructures({roleProbes:[probe("票價","NT$ 800")],recognizedLabelNodes:1},false);
 assert.deepEqual(r.accepted,[]);assert.deepEqual(r.rejected,[]);
});
test("27 DOM probe bomb fails",()=>{
 assert.throws(()=>reviewStructures({roleProbes:Array(81).fill(probe("票價","NT$ 50"))},true));
});
test("28 synthetic five official visits report review+rejected",async()=>{
 const f=fixture(),mock=synthetic(f.p);
 const r=await run(f.p,f.raw,mock.browser,{settleMs:0});
 assert.equal(r.sampleCount,5);assert.equal(r.sourceTitleParityCount,5);
 assert.equal(r.eligibleReviewPairs,10);assert.equal(r.rejectedOrHoldPairs,5);
 assert.equal(mock.visited.length,5);assert.equal(r.formalFieldPromotions,0);
 validateReport(r);
});
test("29 synthetic source title mismatch returns zero field candidates",async()=>{
 const f=fixture(),mock=synthetic(f.p,{mismatch:true});
 const r=await run(f.p,f.raw,mock.browser,{settleMs:0});
 assert.equal(r.sourceTitleParityCount,0);
 assert.equal(r.eligibleReviewPairs,0);assert.equal(r.rejectedOrHoldPairs,0);
});
test("30 synthetic server error or off-host holds",async()=>{
 for(const config of [{httpStatus:403},{external:true}]){
  const f=fixture(),mock=synthetic(f.p,config);
  const r=await run(f.p,f.raw,mock.browser,{settleMs:0});
  assert.equal(r.sourceTitleParityCount,0);assert.equal(r.eligibleReviewPairs,0);
  assert.ok(r.results.every(x=>x.renderState.startsWith("HOLD_")));
 }
});
test("31 report refuses fictitious promotion",async()=>{
 const f=fixture(),mock=synthetic(f.p,{mismatch:true});
 const r=await run(f.p,f.raw,mock.browser,{settleMs:0});
 r.results[0].formalPrice=800;assert.throws(()=>validateReport(r));
});
test("32 output SHA manifest and no production path",async()=>{
 const f=fixture(),mock=synthetic(f.p,{mismatch:true});
 const r=await run(f.p,f.raw,mock.browser,{settleMs:0});
 const tmp=await mkdtemp(resolve("p30-l9g-test-"));
 try{
  const m=await emit(r,tmp);
  const raw=await readFile(tmp+"/rendered_field_structure.json");
  assert.equal(m.filesSHA256["rendered_field_structure.json"],sha(raw));
  for(const p of [".","docs","docs/data.json","scripts/x","tests/a",".git",".github/workflows"])
   assert.throws(()=>safeOut(p));
 }finally{await rm(tmp,{recursive:true,force:true});}
});
