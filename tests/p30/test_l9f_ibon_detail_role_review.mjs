import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {KIND,INPUT_KIND,SAMPLE_LIMIT,PARENT_SHA,canonical,validateSource,
 chooseAdditional,classifyField,reviewPairs,emptyResult,acceptResult,
 audit,validateReport,safeOut,emit} from "../../scripts/p30_l9f_ibon_detail_role_review.mjs";
const sha=x=>createHash("sha256").update(x).digest("hex");
const title="臺灣示範文化展演活動";
function fixture(){
 const candidates=Array.from({length:22},(_,i)=>({
  candidateId:"ibon:"+(1000+i),
  officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+(1000+i),
  title:title+" "+i,detailTitleParity:i===0,
  formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN",
  goldenVerified:false,published:false
 }));
 const doc={kind:INPUT_KIND,
  parentL9DHead:"8836dc29a6dcf4baaabed08102ffb1b7fbed6bc3",
  sourceOrigin:"FRESH_REAL_PUBLIC_CHROMIUM_RENDERING",navigationAttemptCount:2,
  candidateCount:22,candidates,detailSamplesAttempted:1,
  sampledDetailStatus:"DETAIL_TITLE_PARITY_PASS",
  persistedRawHtml:false,persistedCookies:false,persistedNetworkBodies:false,
  formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  releaseState:"HARD_HOLD_NO_PUBLICATION",existingAndroid44Preserved:true};
 return {doc,bytes:Buffer.from(JSON.stringify(doc))};
}
function browser(behavior={}){
 const observed={pages:[],navigations:[]};
 return {observed,api:{
  launch:async()=>({
   newContext:async()=>({
    newPage:async()=>{
     const i=observed.pages.length;
     const page={
      _url:null,_i:i,
      async goto(url){this._url=url;observed.navigations.push(url);
       if(behavior.timeout)throw Object.assign(new Error("time"),{name:"TimeoutError"});
       return {status:()=>behavior.http??200};},
      url(){return behavior.foreign?"https://other.test/":this._url;},
      async waitForTimeout(){},
      async evaluate(){return {headings:behavior.mismatch?["不同活動"]:
        [title+" "+(1+Math.floor(i*5))],
       pairs:behavior.pairs??[{label:"票價",value:"資訊"},
          {label:"活動日期",value:"2026/10/28 18:30"},
          {label:"售票期間",value:"2026/10/01 10:00"}],
       hasHtmlBody:true};},
      async close(){}
     };observed.pages.push(page);return page;
    },async close(){}
   }),async close(){}
  })
 }};
}
test("01 proper typed source kind",()=>assert.match(KIND,/PINNED_DETAIL_ROLE_REVIEW/));
test("02 pin 22 real source records",()=>assert.equal(validateSource(...Object.values(fixture())).candidateCount,22));
test("03 source L7A historical origin cannot masquerade",()=>{
 const x=fixture();x.doc.sourceOrigin="L7A_HISTORICAL";assert.throws(()=>validateSource(x.doc,x.bytes));
});
test("04 wrong L9E count or parent parity is fail closed",()=>{
 for(const [k,v] of [["candidateCount",12],["detailSamplesAttempted",0],["sampledDetailStatus","HOLD"]]){
  const x=fixture();x.doc[k]=v;assert.throws(()=>validateSource(x.doc,x.bytes));
 }
});
test("05 upstream Golden/Writer forgery fails",()=>{
 for(const [k,v] of [["goldenAccepted",1],["writerExecuted",true],["published",true]]){
  const x=fixture();x.doc[k]=v;assert.throws(()=>validateSource(x.doc,x.bytes));
 }
});
test("06 numeric ibon HTTPS source ID passes",()=>assert.equal(canonical("https://ticket.ibon.com.tw/ActivityInfo/Details/1234").eventId,"1234"));
test("07 foreign host / login / wrong ID / query rejects",()=>{
 for(const u of ["http://ticket.ibon.com.tw/ActivityInfo/Details/1234",
 "https://ticket.ibon.com.tw.evil.net/ActivityInfo/Details/1234",
 "https://ticket.ibon.com.tw/ActivityInfo/Details/invalid",
 "https://ticket.ibon.com.tw/login",
 "https://ticket.ibon.com.tw/ActivityInfo/Details/1234?token=1",
 "https://user@ticket.ibon.com.tw/ActivityInfo/Details/1234"]){
  assert.equal(canonical(u),null,u);
 }
});
test("08 tampered cross-origin source URL rejects",()=>{
 const x=fixture();x.doc.candidates[2].officialUrl="https://evil.test/event";
 assert.throws(()=>validateSource(x.doc,x.bytes));
});
test("09 tampered source Event ID rejects",()=>{
 const x=fixture();x.doc.candidates[3].candidateId="ibon:9999";
 assert.throws(()=>validateSource(x.doc,x.bytes));
});
test("10 all selected are distinct and not previously inspected",()=>{
 const x=fixture();const a=chooseAdditional(x.doc);
 assert.equal(a.length,5);assert.equal(new Set(a.map(v=>v.candidateId)).size,5);
 assert.ok(a.every(v=>!v.detailTitleParity));
});
test("11 bounded three to five samples",()=>{
 const x=fixture();
 for(const n of [3,4,5])assert.equal(chooseAdditional(x.doc,n).length,n);
 for(const n of [0,2,6,100])assert.throws(()=>chooseAdditional(x.doc,n));
});
test("12 PRICE 資訊 is rejected",()=>assert.equal(classifyField({label:"票價",value:"資訊"}).quality,"REJECT_GENERIC_OR_NONNUMERIC_PRICE"));
test("13 PRICE numeric still review only, never published",()=>{
 const r=classifyField({label:"票價",value:"NT$ 500"});
 assert.equal(r.quality,"PRICE_TOKEN_REVIEW_REQUIRED");assert.equal(r.formalFieldPromoted,false);
});
test("14 free-price language still review only",()=>assert.equal(classifyField({label:"票價",value:"免費"}).quality,"FREE_TEXT_REVIEW_REQUIRED"));
test("15 EVENT_PERIOD date token role",()=>assert.equal(classifyField({label:"演出日期",value:"2026/10/28 18:30"}).role,"EVENT_PERIOD"));
test("16 sale date separate from event date",()=>assert.equal(classifyField({label:"售票期間",value:"2026/10/01 10:00"}).role,"SALE_PERIOD"));
test("17 admission role is independent",()=>assert.equal(classifyField({label:"入場時間",value:"2026/10/28 17:30"}).role,"ADMISSION_TIME"));
test("18 registration role is independent",()=>assert.equal(classifyField({label:"報名期間",value:"2026/10/10-10/20"}).role,"REGISTRATION_PERIOD"));
test("19 voucher expiry role independent",()=>assert.equal(classifyField({label:"票券有效期限",value:"2026/10/31"}).role,"VOUCHER_VALIDITY"));
test("20 no date token no promotion",()=>assert.equal(classifyField({label:"演出日期",value:"詳情請參考官方"}).quality,"REJECT_NO_DATE_TIME_TOKEN"));
test("21 event-date containing sale wording conflicts",()=>assert.equal(classifyField({label:"演出日期",value:"2026/10/28 18:30 開賣"}).quality,"HOLD_ROLE_CONFLICT_EVENT_VS_SALE_OR_ADMISSION"));
test("22 same event multi-session not split",()=>{
 const r=classifyField({label:"場次",value:"10/28 18:00、10/29 14:00"});
 assert.equal(r.quality,"SESSION_RELATION_REVIEW_REQUIRED_NO_SPLIT");
});
test("23 reject non-adjacent global body and overly long text",()=>{
 assert.equal(classifyField({label:"活動日期",value:"X".repeat(120)}),null);
 assert.equal(classifyField({label:"沒有此欄位",value:"2026/10/28"}),null);
});
test("24 mismatched title suppresses ALL fields",()=>{
 const q=reviewPairs([{label:"票價",value:"NT$100"}],false);
 assert.equal(q.evidence.length,0);assert.equal(q.rejected.length,0);
});
test("25 title bound still keeps rejected values separate",()=>{
 const q=reviewPairs([{label:"票價",value:"資訊"},{label:"演出日期",value:"2026/10/28"}],true);
 assert.equal(q.evidence.length,1);assert.equal(q.rejected.length,1);
});
test("26 unbounded DOM labels fail closed",()=>assert.throws(()=>reviewPairs(Array(61).fill({label:"票價",value:"300元"}),true)));
test("27 formal field promotion is not allowed",()=>{
 const x=emptyResult(fixture().doc.candidates[1]);
 assert.equal(x.formalDate,null);assert.equal(x.formalPrice,null);
 x.formalDate="2026-10-28";assert.throws(()=>acceptResult(x));
});
test("28 synthetic Chromium mismatch is HOLD and has no evidence",async()=>{
 const x=fixture(),b=browser({mismatch:true});
 const report=await audit(x.doc,x.bytes,b.api,{sampleSize:3,settleMs:0});
 assert.equal(report.additionalTitleParity,0);
 assert.ok(report.samples.every(s=>s.roleEvidence.length===0&&s.detailState==="HOLD_TITLE_PARITY"));
 assert.equal(report.formalFieldPromotions,0);
 assert.equal(b.observed.navigations.length,3);
});
test("29 synthetic Chromium timeout is HOLD, never fabricated candidate",async()=>{
 const x=fixture(),b=browser({timeout:true});
 const report=await audit(x.doc,x.bytes,b.api,{sampleSize:3,settleMs:0});
 assert.ok(report.samples.every(s=>s.detailState==="HOLD_DETAIL_TIMEOUT"));
 assert.equal(report.additionalRoleEvidenceCount,0);
});
test("30 sealed output and recovery safety",async()=>{
 const x=fixture(),b=browser({mismatch:true});
 const report=await audit(x.doc,x.bytes,b.api,{sampleSize:3,settleMs:0});
 const dir=await mkdtemp(resolve("p30-l9f-test-"));
 try{
  const manifest=await emit(report,dir);
  const raw=await readFile(dir+"/detail_role_review.json");
  assert.equal(manifest.fileSHA256["detail_role_review.json"],sha(raw));
  assert.equal(report.releaseState,"HARD_HOLD_NO_PUBLICATION");
  for(const path of ["docs","scripts/a","tests/a",".git",".github/workflows","."]){
   assert.throws(()=>safeOut(path));
  }
 }finally{await rm(dir,{recursive:true,force:true});}
});
