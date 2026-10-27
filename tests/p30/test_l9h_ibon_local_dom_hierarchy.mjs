import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {KIND,PARENT_KIND,PARENT_HEAD,PARENT_RUN,PARENT_ARTIFACT,TITLE_PARENT_KIND,IDS,HOLD,
 LABEL_ROLES,parentProof,reviewNeighbor,assessStructure,audit,validateReport,
 safeOut,emit} from "../../scripts/p30_l9h_ibon_local_dom_hierarchy.mjs";

const sha=b=>createHash("sha256").update(b).digest("hex");
const eventTitle="模擬官方節目與展演";
function fixture(){
 const p={kind:PARENT_KIND,
  parentHead:"d85504773108281099ec0654c5c772de243f910c",
  parentRun:40494326021,parentArtifact:12729277485,
  sourceOrigin:"FRESH_PUBLIC_RENDERED_DETAIL_STRUCTURE_ONLY",
  sampleCount:5,sourceTitleParityCount:5,eligibleReviewPairs:0,rejectedOrHoldPairs:5,
  formalFieldPromotions:0,goldenAccepted:0,published:false,writerExecuted:false,
  schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  releaseState:HOLD,existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  results:IDS.map((id,i)=>({
   candidateId:"ibon:"+id,officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,
   httpStatus:200,sourceTitleParity:true,renderState:"DETAIL_TITLE_PARITY_PASS",
   fieldCandidates:[],
   fieldRejected:[{role:"EVENT_PERIOD",quality:"REJECT_MISSING_DATE_TIME",structure:"LOCAL_SIBLING"}],
   formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN",published:false
  }))
 };
 return{p,raw:Buffer.from(JSON.stringify(p))};
}
function titleFixture(parent){
 const doc={kind:TITLE_PARENT_KIND,parentL9ERun:40449476633,
  parentArtifactId:12709568132,parentCandidateCount:22,
  additionalSampleSize:5,additionalTitleParity:5,formalFieldPromotions:0,
  goldenAccepted:0,published:false,releaseState:HOLD,
  samples:parent.results.map((row,i)=>({
   candidateId:row.candidateId,officialUrl:row.officialUrl,
   listTitle:eventTitle+i,titleParity:true,httpStatus:200
  }))};
 return {doc,raw:Buffer.from(JSON.stringify(doc))};
}
const neighbor=(value,relation="LABEL_NEXT_ELEMENT",over={})=>({
 value,relation,distance:1,otherRoleCount:0,interactive:false,...over});
const context=(value,relation="LABEL_NEXT_ELEMENT",label="活動日期",over={})=>({
 label,tag:"STRONG",parentTag:"DIV",grandparentTag:"ARTICLE",
 parentChildCount:2,directTextLength:4,imageCount:0,
 neighbors:[neighbor(value,relation)],...over
});
function fakeBrowser(parent,options={}){
 const urls=[],titles=new Map(parent.results.map((x,i)=>[x.officialUrl,eventTitle+i]));
 const client={launch:async()=>({
  newContext:async()=>({
   newPage:async()=>({
    active:null,
    async goto(url){urls.push(url);this.active=url;return{status:()=>options.httpStatus??200};},
    url(){return options.offHost?"https://evil.example/":this.active;},
    async waitForTimeout(){},
    async evaluate(){return{
     headings:options.titleMismatch?["不同活動"]:[options.fakeTitle?"假標題":titles.get(this.active)],
     labelContexts:options.contexts??[context("2026/10/31 19:00")],
     tagCounts:{strong:170,b:45,table:0,dl:0,img:9}
    };},
    async close(){}
   }),async close(){}
  }),async close(){}
 })};
 // Fixture does not contain listTitle field; caller must supply it before run.
 return{client,urls};
}
test("01 task is explicitly read-only",()=>assert.match(KIND,/HIERARCHY_READONLY/));
test("02 exact 5 known official ibon IDs",()=>assert.deepEqual(IDS,["39575","39878","39907","39961","39978"]));
test("03 parent report includes 5 precise source matches and digest",()=>{
 const p=fixture(),t=titleFixture(p.p),o=parentProof(p.p,p.raw,t.doc,t.raw);
 assert.equal(o.sha256,sha(p.raw));assert.equal(o.sources.length,5);
});
test("04 source cannot be historical or wrong kind",()=>{
 for(const field of ["kind","sourceOrigin"]){
  const p=fixture();p.p[field]="L7A_HISTORICAL";assert.throws(()=>parentProof(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw));
 }
});
test("05 wrong source identity denied",()=>{
 const p=fixture();p.p.results[0].officialUrl="https://evil.test/Details/39575";
 assert.throws(()=>parentProof(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw));
});
test("06 forged source title parity denied",()=>{
 const p=fixture();p.p.results[0].sourceTitleParity=false;assert.throws(()=>parentProof(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw));
});
test("07 altered source rejection quality denied",()=>{
 const p=fixture();p.p.results[0].fieldRejected[0].quality="PRICE_REVIEW_ONLY";
 assert.throws(()=>parentProof(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw));
});
test("08 source with field promotion denied",()=>{
 for(const [k,v] of [["formalFieldPromotions",1],["published",true],["goldenAccepted",1],["writerExecuted",true]]){
  const p=fixture();p.p[k]=v;assert.throws(()=>parentProof(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw));
 }
});
test("09 role dictionary separates sale vs actual event time",()=>{
 assert.equal(LABEL_ROLES["活動日期"],"EVENT_PERIOD");
 assert.equal(LABEL_ROLES["售票時間"],"SALE_PERIOD");
 assert.equal(LABEL_ROLES["入場時間"],"ADMISSION_TIME");
 assert.equal(LABEL_ROLES["報名期間"],"REGISTRATION_PERIOD");
});
test("10 price/info rejected in local DOM",()=>{
 assert.equal(reviewNeighbor(neighbor("資訊"),"PRICE").quality,"REJECT_GENERIC_PRICE");
});
test("11 valid numeric price is review-only",()=>{
 const r=reviewNeighbor(neighbor("NT$ 700"),"PRICE");
 assert.equal(r.quality,"PRICE_TOKEN_REVIEW_ONLY");
 assert.equal(r.promotable,false);
});
test("12 event date bound by direct label-next-element review-only",()=>{
 const r=reviewNeighbor(neighbor("2026/10/31 19:00"),"EVENT_PERIOD");
 assert.equal(r.bindingState,"LOCAL_BOUND_REVIEW_ONLY");
 assert.equal(r.quality,"EVENT_DATE_TOKEN_REVIEW_ONLY");
});
test("13 nested label parent/next element is allowed for review",()=>{
 const r=reviewNeighbor(neighbor("2026/10/31 19:00","LABEL_PARENT_NEXT_ELEMENT"),"EVENT_PERIOD");
 assert.equal(r.quality,"EVENT_DATE_TOKEN_REVIEW_ONLY");
});
test("14 direct same-parent text is allowed only with explicit binding",()=>{
 const r=reviewNeighbor(neighbor("2026/10/31 19:00","SAME_PARENT_TEXT_AFTER_LABEL"),"EVENT_PERIOD");
 assert.equal(r.bindingState,"LOCAL_BOUND_REVIEW_ONLY");
});
test("15 global page body relation is denied",()=>{
 const r=reviewNeighbor(neighbor("2026/10/31","PAGE_BODY_GLOBAL"),"EVENT_PERIOD");
 assert.equal(r.quality,"HOLD_UNBOUND_STRUCTURE");
});
test("16 distant two hop relation denied",()=>{
 assert.equal(reviewNeighbor(neighbor("2026/10/31","LABEL_NEXT_ELEMENT",{distance:2}),"EVENT_PERIOD").quality,
 "HOLD_UNBOUND_STRUCTURE");
});
test("17 interactive control cannot become activity date",()=>{
 assert.equal(reviewNeighbor(neighbor("2026/10/31","LABEL_NEXT_ELEMENT",{interactive:true}),"EVENT_PERIOD").quality,
 "HOLD_INTERACTIVE_NEIGHBOR");
});
test("18 shared section containing other role labels is HOLD",()=>{
 const r=reviewNeighbor(neighbor("2026/10/31 19:00 售票 2026/10/01","LABEL_NEXT_ELEMENT",{otherRoleCount:2}),"EVENT_PERIOD");
 assert.equal(r.quality,"HOLD_MULTIPLE_ROLE_LABELS_IN_SECTION");
});
test("19 non-date text adjacent to EVENT_PERIOD rejected",()=>{
 assert.equal(reviewNeighbor(neighbor("資訊說明"),"EVENT_PERIOD").quality,"REJECT_NO_DATE_TIME_TOKEN");
});
test("20 cross-role terms may not become performance dates",()=>{
 assert.equal(reviewNeighbor(neighbor("2026/10/31 售票開賣"),"EVENT_PERIOD").quality,"HOLD_ROLE_CONFLICT_EVENT_DATE");
});
test("21 session text is review-only without splitting event IDs",()=>{
 const r=reviewNeighbor(neighbor("10/31 14:00、10/31 19:00"),"SESSION");
 assert.equal(r.quality,"SESSION_EVIDENCE_REVIEW_ONLY_NO_SPLIT");
});
test("22 role-local voucher deadline is distinct",()=>{
 const r=reviewNeighbor(neighbor("2026/11/30 23:59"),"VOUCHER_VALIDITY");
 assert.equal(r.quality,"VOUCHER_VALIDITY_TOKEN_REVIEW_ONLY");
});
test("23 empty neighbor must be rejected",()=>{
 assert.equal(reviewNeighbor(neighbor(""),"EVENT_PERIOD").quality,"REJECT_EMPTY_VALUE");
});
test("24 too-long neighbor must not be captured",()=>{
 assert.equal(reviewNeighbor(neighbor("2026/10/31 "+"X".repeat(140)),"EVENT_PERIOD").quality,"REJECT_OVERSIZE_BOUND_VALUE");
});
test("25 local-bound typed review structure",()=>{
 const r=assessStructure({labelContexts:[context("2026/10/31 19:00")]},true);
 assert.equal(r.reviewPairs.length,1);assert.equal(r.rejections.length,0);
 assert.equal(r.reviewPairs[0].formalFieldPromoted,false);
});
test("26 parent image structure is metadata only",()=>{
 const r=assessStructure({labelContexts:[context("資訊","LABEL_NEXT_ELEMENT","活動日期",{imageCount:2})]},true);
 assert.equal(r.imageNearLabels,2);assert.equal(r.reviewPairs.length,0);
});
test("27 title mismatch causes no candidate or rejected role",()=>{
 const r=assessStructure({labelContexts:[context("2026/10/31 19:00")]},false);
 assert.equal(r.reviewPairs.length,0);assert.equal(r.rejections.length,0);
});
test("28 DOM label bomb is fail closed",()=>{
 assert.throws(()=>assessStructure({labelContexts:Array(17).fill(context("2026/10/31"))},true));
});
test("29 DOM neighbor bomb is fail closed",()=>{
 const c=context("2026/10/31");c.neighbors=Array(4).fill(neighbor("2026/10/31"));
 assert.throws(()=>assessStructure({labelContexts:[c]},true));
});
test("30 malformed role not promoted",()=>{
 const r=assessStructure({labelContexts:[context("2026/10/31","LABEL_NEXT_ELEMENT","節目說明")]},true);
 assert.equal(r.reviewPairs.length,0);
});
test("31 no invented field when no DOM neighbor",()=>{
 const r=assessStructure({labelContexts:[context("", "LABEL_NEXT_ELEMENT","活動日期",{neighbors:[]})]},true);
 assert.equal(r.reviewPairs.length,0);
});
test("32 synthetic five official pages with review-only dates",async()=>{
 const p=fixture();
 
 const b=fakeBrowser(p.p);
 const r=await audit(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw,b.client,{settleMs:0});
 assert.equal(b.urls.length,5);assert.equal(r.sampleCount,5);
 assert.equal(r.titleParityCount,5);
 assert.equal(r.locallyBoundReviewPairs,5);
 assert.equal(r.formalFieldPromotions,0);assert.equal(r.goldenAccepted,0);
 assert.equal(r.published,false);
 validateReport(r);
});
test("33 synthetic no page title parity still has zero field evidence",async()=>{
 const p=fixture();
 const b=fakeBrowser(p.p,{titleMismatch:true});
 const r=await audit(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw,b.client,{settleMs:0});
 assert.equal(r.titleParityCount,0);
 assert.equal(r.locallyBoundReviewPairs,0);assert.equal(r.rejectedOrHoldPairs,0);
});
test("34 off-origin redirect or 403 cannot generate fields",async()=>{
 for(const option of [{offHost:true},{httpStatus:403}]){
  const p=fixture();
  const b=fakeBrowser(p.p,option);
  const r=await audit(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw,b.client,{settleMs:0});
  assert.equal(r.locallyBoundReviewPairs,0);
  assert.ok(r.rows.every(x=>x.status.startsWith("HOLD")));
 }
});
test("35 reject metadata promoting Golden or formal prices",async()=>{
 const p=fixture();
 const b=fakeBrowser(p.p,{titleMismatch:true});
 const r=await audit(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw,b.client,{settleMs:0});
 r.rows[0].formalPrice=900;assert.throws(()=>validateReport(r));
});
test("36 SHA manifest and output confinement",async()=>{
 const p=fixture();
 const b=fakeBrowser(p.p,{titleMismatch:true});
 const r=await audit(p.p,p.raw,titleFixture(p.p).doc,titleFixture(p.p).raw,b.client,{settleMs:0});
 const dir=await mkdtemp(resolve("p30-l9h-test-"));
 try{
  const m=await emit(r,dir);
  const raw=await readFile(dir+"/ibon_local_dom_hierarchy.json");
  assert.equal(m.filesSHA256["ibon_local_dom_hierarchy.json"],sha(raw));
  for(const x of [".","docs","docs/data.json","scripts/x","tests/a",".github",".git"])
   assert.throws(()=>safeOut(x));
 }finally{await rm(dir,{recursive:true,force:true});}
});
