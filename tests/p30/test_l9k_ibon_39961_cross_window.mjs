import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {grade as parentGrade} from "../../scripts/p30_l9j_ibon_39961_repeatability.mjs";
import {KIND,SOURCE_J_KIND,SOURCE_H_KIND,MIN_GAP_MS,RELEASE,
 provenance,minimumWindow,crossWindowDecision,audit,validateReport,safeOut,emit,sha
} from "../../scripts/p30_l9k_ibon_39961_cross_window.mjs";

const TITLE="示範 ibon 正式活動名稱";
const LIST="https://ticket.ibon.com.tw/Index/entertainment";
const DETAIL="https://ticket.ibon.com.tw/ActivityInfo/Details/39961";
const hash=b=>createHash("sha256").update(b).digest("hex");
const round=(n)=>{
 const start=n===1?"2026-10-28T02:13:33.400Z":"2026-10-28T02:13:46.435Z";
 const end=n===1?"2026-10-28T02:13:38.431Z":"2026-10-28T02:13:51.393Z";
 return{index:n,startedUtc:start,endedUtc:end,
  list:{url:LIST,httpStatus:200,finalUrlRole:"EXACT_OFFICIAL_ENTRY",state:"RENDERED_PUBLIC_LIST"},
  detail:{url:DETAIL,httpStatus:200,finalUrlRole:"EXACT_OFFICIAL_DETAIL",state:"RENDERED_PUBLIC_DETAIL"},
  listTitles:[TITLE],detailHeadings:[TITLE],
  decision:{status:"REVIEW_ONLY_NO_RELEASE",currentSourceParity:true,
   historicTitleStillObserved:true,driftObserved:false,reason:"CURRENT_LIST_DETAIL_PARITY_REVIEW_ONLY"}
 };
};
function fixture(){
 const h={kind:SOURCE_H_KIND,parentHead:"07cc3ce1743a56d2bc60213d345f27672cef97d5",
  parentRun:40511115223,sampleCount:5,titleParityCount:4,releaseState:RELEASE,
  formalFieldPromotions:0,goldenAccepted:0,
  rows:["39575","39878","39907","39961","39978"].map(id=>({
   candidateId:"ibon:"+id,officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,
   httpStatus:200,titleParity:id!=="39961",status:id==="39961"?"HOLD_TITLE_MISMATCH":"TITLE_PARITY_PASS"
  }))};
 const hBytes=Buffer.from(JSON.stringify(h));
 const rounds=[round(1),round(2)];
 const j={kind:SOURCE_J_KIND,
  parentL9IHead:"ca60d3182172ad7f824fbcb5a2a6c9189fecc74b",
  parentL9IRun:40524765567,parentL9IArtifact:12744025880,
  parentL9HRun:40516301527,parentL9HArtifact:12740505389,
  pinnedL9HSHA256:hash(hBytes),eventId:"39961",officialListUrl:LIST,officialDetailUrl:DETAIL,
  sourceOrigin:"TWO_NEW_INDEPENDENT_NORMAL_BROWSER_PROCESSES_SAME_RUN",
  roundCount:2,minimumRoundGapMs:8000,topLevelNavigationsAttempted:4,
  independentBrowserProcesses:2,rounds,grade:parentGrade(rounds,true),
  goldenAccepted:0,formalFieldPromotions:0,formalTicketStatus:"UNKNOWN",formalEventDate:null,
  formalPrice:null,sessionSplits:0,published:false,writerExecuted:false,
  schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,cookiesPersisted:false,screenshotsPersisted:false,networkBodiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:RELEASE
 };
 return{j,jBytes:Buffer.from(JSON.stringify(j)),h,hBytes};
}
const fakeFresh=()=>({
 ...round(2),index:3,startedUtc:"2026-10-28T10:20:00.500Z",
 endedUtc:"2026-10-28T10:20:05.900Z"
});
const fakeOptions=(mod={})=>({
 now:()=>mod.now??"2026-10-28T10:20:00.000Z",
 capture:async()=>mod.fresh??fakeFresh(),
 settleMs:0
});
test("01 cross-window report type",()=>assert.match(KIND,/CROSS_WINDOW_SOURCE/));
test("02 minimum gap exactly four hours",()=>assert.equal(MIN_GAP_MS,14400000));
test("03 source dual lineage verified including old mismatch",()=>{
 const x=fixture(),p=provenance(x.j,x.jBytes,x.h,x.hBytes);
 assert.equal(p.jSHA256,hash(x.jBytes));assert.equal(p.hSHA256,hash(x.hBytes));
 assert.equal(p.historicalTitle,TITLE);
});
test("04 source J bytes cannot be altered after SHA",()=>{
 const x=fixture();x.j.grade.sameRunTitleMatches=1;
 assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
});
test("05 source H bytes cannot be altered after SHA",()=>{
 const x=fixture();x.h.rows[3].titleParity=true;
 assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
});
test("06 later conflicting H evidence must remain present",()=>{
 const x=fixture();x.h.rows[3].titleParity=true;x.hBytes=Buffer.from(JSON.stringify(x.h));
 x.j.pinnedL9HSHA256=hash(x.hBytes);x.jBytes=Buffer.from(JSON.stringify(x.j));
 assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
});
test("07 mismatched J historical H digest is refused",()=>{
 const x=fixture();x.j.pinnedL9HSHA256="0".repeat(64);x.jBytes=Buffer.from(JSON.stringify(x.j));
 assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
});
test("08 J previous source parity must be 2 of 2",()=>{
 const x=fixture();x.j.rounds[0].decision.currentSourceParity=false;
 x.j.grade=parentGrade(x.j.rounds,true);x.jBytes=Buffer.from(JSON.stringify(x.j));
 assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
});
test("09 J previous Source two titles must be exactly same",()=>{
 const x=fixture();x.j.rounds[1].listTitles=["不同活動"];
 x.j.grade=parentGrade(x.j.rounds,true);x.jBytes=Buffer.from(JSON.stringify(x.j));
 assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
});
test("10 original source identity path cannot change",()=>{
 const x=fixture();x.j.rounds[0].detail.url="https://evil.test/";
 x.jBytes=Buffer.from(JSON.stringify(x.j));
 assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
});
test("11 source Golden or published mutation denied",()=>{
 for(const [key,value] of [["goldenAccepted",1],["published",true],["writerExecuted",true]]){
  const x=fixture();x.j[key]=value;x.jBytes=Buffer.from(JSON.stringify(x.j));
  assert.throws(()=>provenance(x.j,x.jBytes,x.h,x.hBytes));
 }
});
test("12 preflight 3 hours 59 minutes must be HOLD",()=>{
 assert.throws(()=>minimumWindow("2026-10-28T02:00:00Z","2026-10-28T05:59:59Z"));
});
test("13 preflight 4 hours exactly acceptable",()=>{
 assert.equal(minimumWindow("2026-10-28T02:00:00Z","2026-10-28T06:00:00Z"),MIN_GAP_MS);
});
test("14 bad time evidence refused",()=>{
 assert.throws(()=>minimumWindow("bad","2026-10-28T10:00:00Z"));
});
test("15 clock rollback refused",()=>{
 assert.throws(()=>minimumWindow("2026-10-28T12:00:00Z","2026-10-28T10:00:00Z"));
});
test("16 newer separate capture matches previous original",()=>{
 const x=fixture(),g=crossWindowDecision(x.j.rounds,fakeFresh(),TITLE);
 assert.equal(g.crossWindowStatus,"CROSS_WINDOW_THREE_MATCHES_REVIEW_ONLY");
 assert.equal(g.totalComparableMatches,3);
});
test("17 current source missing ID remains HOLD",()=>{
 const x=fixture(),r=fakeFresh();r.listTitles=[];r.decision.status="HOLD";
 assert.equal(crossWindowDecision(x.j.rounds,r,TITLE).observedCrossWindowParity,false);
});
test("18 new list title changed but detail agrees no automatic clearance",()=>{
 const x=fixture(),r=fakeFresh();r.listTitles=["其他來源標題"];
 assert.equal(crossWindowDecision(x.j.rounds,r,TITLE).crossWindowStatus,
  "CROSS_WINDOW_SOURCE_MISMATCH_OR_INCOMPLETE_HOLD");
});
test("19 new detail mismatch must fail",()=>{
 const x=fixture(),r=fakeFresh();r.decision.status="HOLD";
 assert.equal(crossWindowDecision(x.j.rounds,r,TITLE).observedCrossWindowParity,false);
});
test("20 NEW page 403 not a cancelled event",()=>{
 const x=fixture(),r=fakeFresh();r.detail.httpStatus=403;
 assert.equal(crossWindowDecision(x.j.rounds,r,TITLE).observedCrossWindowParity,false);
});
test("21 redirect/wrong canonical detail is HOLD",()=>{
 const x=fixture(),r=fakeFresh();r.detail.finalUrlRole="HOLD_REDIRECT_OR_DIFFERENT_PATH";
 assert.equal(crossWindowDecision(x.j.rounds,r,TITLE).observedCrossWindowParity,false);
});
test("22 no opening Golden even with 3 of 3",()=>{
 const x=fixture(),g=crossWindowDecision(x.j.rounds,fakeFresh(),TITLE);
 assert.equal(g.formalIdentityCertified,false);
 assert.equal(g.formalReleaseEligible,false);
 assert.equal(g.historicalMismatchRetained,true);
 assert.equal(g.priorRootCauseStillUnknown,true);
});
test("23 real browser not contacted when under four hours",async()=>{
 const x=fixture();let invoked=0;
 await assert.rejects(()=>audit(x.j,x.jBytes,x.h,x.hBytes,null,{
  now:()=>"2026-10-28T03:00:00Z",capture:async()=>{invoked++;return fakeFresh();}
 }));
 assert.equal(invoked,0);
});
test("24 synthetic fresh new interval success",async()=>{
 const x=fixture(),r=await audit(x.j,x.jBytes,x.h,x.hBytes,null,fakeOptions());
 assert.equal(r.decision.observedCrossWindowParity,true);
 assert.equal(r.observedGapMs>=MIN_GAP_MS,true);
 assert.equal(r.newTopLevelNavigationsAttempted,2);
 validateReport(r);
});
test("25 synthetic source regression is a HOLD not success",async()=>{
 const x=fixture(),r=fakeFresh();
 r.decision.status="HOLD";r.listTitles=[];
 const report=await audit(x.j,x.jBytes,x.h,x.hBytes,null,fakeOptions({fresh:r}));
 assert.equal(report.decision.observedCrossWindowParity,false);
 assert.equal(report.releaseState,RELEASE);
});
test("26 synthetic result retains no formal date, price or ticket",async()=>{
 const x=fixture(),r=await audit(x.j,x.jBytes,x.h,x.hBytes,null,fakeOptions());
 assert.equal(r.formalEventDate,null);assert.equal(r.formalPrice,null);
 assert.equal(r.ticketStatus,"UNKNOWN");
});
test("27 reject forged cross-window release",async()=>{
 const x=fixture(),r=await audit(x.j,x.jBytes,x.h,x.hBytes,null,fakeOptions());
 r.decision.formalReleaseEligible=true;assert.throws(()=>validateReport(r));
});
test("28 reject forged Golden or Writer",async()=>{
 for(const [key,value] of [["goldenAccepted",1],["writerExecuted",true],["published",true]]){
  const x=fixture(),r=await audit(x.j,x.jBytes,x.h,x.hBytes,null,fakeOptions());
  r[key]=value;assert.throws(()=>validateReport(r));
 }
});
test("29 bounded output cannot touch production paths",()=>{
 for(const dir of [".","docs","docs/data.json","scripts/x","tests/x",".github/workflows",".git"])
  assert.throws(()=>safeOut(dir));
});
test("30 SHA256 sealed output exact bytes and retained HOLD",async()=>{
 const x=fixture(),r=await audit(x.j,x.jBytes,x.h,x.hBytes,null,fakeOptions());
 const dest=await mkdtemp(resolve("p30-l9k-test-"));
 try{
  const manifest=await emit(r,dest);
  const bytes=await readFile(dest+"/ibon_39961_cross_window.json");
  assert.equal(manifest.fileSHA256["ibon_39961_cross_window.json"],sha(bytes));
  assert.equal(manifest.releaseState,RELEASE);
 }finally{await rm(dest,{recursive:true,force:true});}
});
