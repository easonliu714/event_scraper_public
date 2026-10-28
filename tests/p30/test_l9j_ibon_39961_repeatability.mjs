import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {KIND,PARENT_J_KIND,PARENT_H_KIND,EVENT_ID,LIST_URL,DETAIL_URL,
 HARD_HOLD,ROUND_COUNT,GAP_MS,validateParents,validateOfficialFinal,grade,
 capture,audit,validateReport,safeOutput,emit} from "../../scripts/p30_l9j_ibon_39961_repeatability.mjs";
const hash=b=>createHash("sha256").update(b).digest("hex");
const OLD="模擬官方臺灣音樂會";
function fixture(){
 const i={kind:PARENT_J_KIND,parentL9HHead:"56d309a9d4d895c7adfb525723c6e2a9c4abd2cb",
  parentL9HRun:40516301527,parentL9HArtifact:12740505389,
  eventId:EVENT_ID,officialDetailUrl:DETAIL_URL,navigationAttemptCount:2,
  originalTitle:OLD,list:{status:200},detail:{status:200},listTitles:[OLD],
  decision:{status:"REVIEW_ONLY_NO_RELEASE",currentSourceParity:true,
   historicTitleStillObserved:true,driftObserved:false},
  currentTitleAcceptedForPublication:false,releaseState:HARD_HOLD,
  goldenAccepted:0,formalFieldPromotions:0,published:false,writerExecuted:false};
 const h={kind:PARENT_H_KIND,
  parentHead:"07cc3ce1743a56d2bc60213d345f27672cef97d5",
  sampleCount:5,titleParityCount:4,releaseState:HARD_HOLD,
  rows:[...["39575","39878","39907","39961","39978"]].map(id=>({
   candidateId:"ibon:"+id,officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,
   httpStatus:200,titleParity:id!=="39961",
   status:id==="39961"?"HOLD_TITLE_MISMATCH":"TITLE_PARITY_PASS",
   reviewPairs:[]
  }))};
 return{i,ir:Buffer.from(JSON.stringify(i)),h,hr:Buffer.from(JSON.stringify(h))};
}
const card=(name=OLD)=>({href:"/ActivityInfo/Details/39961",cardTitle:name,
 anchorText:"立即購票",anchorTitle:"",ariaLabel:"",imageAlt:""});
function mockBrowser(opts={}){
 const state={launches:0,visits:[]};
 const client={launch:async()=>{
  const round=state.launches++;
  let index=0;
  return{
   newContext:async()=>({
    newPage:async()=>{
     const pageIndex=index++;
     let url=null;
     return{
      async goto(next){
       url=next;state.visits.push({round,pageIndex,url:next});
       if(opts.timeout&&round===opts.timeout.round&&pageIndex===opts.timeout.page)
        throw Object.assign(new Error("timeout"),{name:"TimeoutError"});
       const code=opts.http?.[round]?.[pageIndex]??200;
       return{status:()=>code};
      },
      url(){
       if(opts.foreign?.[round]?.[pageIndex])return"https://evil.example/test";
       return url;
      },
      async waitForTimeout(){},
      async evaluate(){
       if(pageIndex===0){
        const title=opts.listTitle?.[round]??OLD;
        return{rows:opts.emptyList?.includes(round)?[]:[card(title)],
         anchorCount:67,textLength:1600,wafHint:opts.waf?.includes(round)??false};
       }
       return{headings:opts.detailHeadings?.[round]??[OLD],
         headingCount:3,textLength:1800,wafHint:opts.waf?.includes(round)??false};
      },
      async close(){}
     };
    },async close(){}
   }),async close(){}
  };
 }};
 return{client,state};
}
const accepted=(i=1)=>({
 index:i,list:{url:LIST_URL,httpStatus:200},
 detail:{url:DETAIL_URL,httpStatus:200},listTitles:[OLD],
 detailHeadings:[OLD],decision:{status:"REVIEW_ONLY_NO_RELEASE",
 currentSourceParity:true,historicTitleStillObserved:true,driftObserved:false}
});
test("01 typed two-browser repeatability experiment",()=>{
 assert.match(KIND,/SAME_RUN_REPEATABILITY/);
 assert.equal(ROUND_COUNT,2);
});
test("02 only one exact ibon Event ID",()=>assert.equal(EVENT_ID,"39961"));
test("03 source Lineage L9I and historical mismatch cross-verified",()=>{
 const x=fixture(),p=validateParents(x.i,x.ir,x.h,x.hr);
 assert.equal(p.historicalTitle,OLD);assert.equal(p.iSHA256,hash(x.ir));
});
test("04 modified I JSON object cannot masquerade as SHA sealed",()=>{
 const x=fixture();x.i.originalTitle="另一標題";
 assert.throws(()=>validateParents(x.i,x.ir,x.h,x.hr));
});
test("05 modified H JSON object cannot masquerade as sealed history",()=>{
 const x=fixture();x.h.rows[3].titleParity=true;
 assert.throws(()=>validateParents(x.i,x.ir,x.h,x.hr));
});
test("06 prior known H mismatch must remain TRUE",()=>{
 const x=fixture();x.h.rows[3].titleParity=true;x.hr=Buffer.from(JSON.stringify(x.h));
 assert.throws(()=>validateParents(x.i,x.ir,x.h,x.hr));
});
test("07 prior I exact-current match required, no conflicting baseline",()=>{
 const x=fixture();x.i.decision.currentSourceParity=false;
 x.ir=Buffer.from(JSON.stringify(x.i));assert.throws(()=>validateParents(x.i,x.ir,x.h,x.hr));
});
test("08 source old title not guessed from numeric ID",()=>{
 const x=fixture();delete x.i.originalTitle;x.ir=Buffer.from(JSON.stringify(x.i));
 assert.throws(()=>validateParents(x.i,x.ir,x.h,x.hr));
});
test("09 upstream Golden/Writer tampering refused",()=>{
 for(const [key,value] of [["goldenAccepted",1],["writerExecuted",true],["published",true]]){
  const x=fixture();x.i[key]=value;x.ir=Buffer.from(JSON.stringify(x.i));
  assert.throws(()=>validateParents(x.i,x.ir,x.h,x.hr));
 }
});
test("10 exact HTTPS same host and path accepted",()=>{
 assert.equal(validateOfficialFinal(LIST_URL,LIST_URL),true);
 assert.equal(validateOfficialFinal(DETAIL_URL,DETAIL_URL),true);
});
test("11 foreign host and deceptive suffix rejected",()=>{
 for(const u of ["https://evil.test/Index/entertainment",
 "https://ticket.ibon.com.tw.evil.test/Index/entertainment"])
  assert.equal(validateOfficialFinal(u,LIST_URL),false);
});
test("12 login path, query, and HTTP downgrade rejected",()=>{
 for(const u of ["https://ticket.ibon.com.tw/login",
 LIST_URL+"?a=1","http://ticket.ibon.com.tw/Index/entertainment"])
  assert.equal(validateOfficialFinal(u,LIST_URL),false);
});
test("13 both matching independent rounds are review only",()=>{
 const g=grade([accepted(1),accepted(2)]);
 assert.equal(g.sameRunTitleMatches,2);
 assert.equal(g.consistentBetweenRounds,true);
 assert.equal(g.currentTwoRoundObservation,"TWO_SEPARATE_BROWSER_MATCHES_REVIEW_ONLY");
 assert.equal(g.formalIdentityReleaseEligible,false);
});
test("14 once good once missing keeps HARD HOLD",()=>{
 const a=accepted(),b=accepted(2);b.listTitles=[];b.decision.status="HOLD";
 const g=grade([a,b]);assert.equal(g.sameRunTitleMatches,1);
 assert.equal(g.currentTwoRoundObservation,"REPEATABILITY_FAILURE_OR_INCOMPLETE_HOLD");
});
test("15 once good once different names is inconsistent",()=>{
 const a=accepted(),b=accepted(2);b.listTitles=["另一節目"];b.decision.driftObserved=true;
 const g=grade([a,b]);assert.equal(g.consistentBetweenRounds,false);
});
test("16 cannot erase historical mismatch even with twice green",()=>{
 assert.throws(()=>grade([accepted(),accepted(2)],false));
});
test("17 grade refuses one or three samples",()=>{
 assert.throws(()=>grade([accepted()]));assert.throws(()=>grade([accepted(),accepted(),accepted()]));
});
test("18 independent round one with exact public pages",async()=>{
 const m=mockBrowser();
 const r=await capture(m.client,0,OLD,{settleMs:0});
 assert.equal(m.state.launches,1);
 assert.equal(m.state.visits.length,2);
 assert.equal(r.decision.currentSourceParity,true);
});
test("19 detail 403 yields HOLD (not event cancelled)",async()=>{
 const m=mockBrowser({http:[[200,403]]});
 const r=await capture(m.client,0,OLD,{settleMs:0});
 assert.equal(r.decision.status,"HOLD");
});
test("20 missing official ID card yields HOLD",async()=>{
 const m=mockBrowser({emptyList:[0]});
 const r=await capture(m.client,0,OLD,{settleMs:0});
 assert.equal(r.decision.reason,"OFFICIAL_LIST_ID_NOT_OBSERVED");
});
test("21 list & detail mismatched name rejected",async()=>{
 const m=mockBrowser({detailHeadings:[["完全不同的節目"]]});
 const r=await capture(m.client,0,OLD,{settleMs:0});
 assert.equal(r.decision.status,"HOLD");
});
test("22 WAF hint is source HOLD not synthetic candidate",async()=>{
 const m=mockBrowser({waf:[0]});
 const r=await capture(m.client,0,OLD,{settleMs:0});
 assert.equal(r.decision.status,"HOLD");
 assert.equal(r.decision.reason,"BROWSER_RENDER_NOT_COMPLETE");
});
test("23 foreign redirect source path denies read-only identity",async()=>{
 const m=mockBrowser({foreign:[[true,false]]});
 const r=await capture(m.client,0,OLD,{settleMs:0});
 assert.equal(r.decision.status,"HOLD");
});
test("24 timeout never counts a parity MATCH",async()=>{
 const m=mockBrowser({timeout:{round:0,page:0}});
 const r=await capture(m.client,0,OLD,{settleMs:0});
 assert.equal(r.decision.status,"HOLD");
});
test("25 twice new ephemeral Chromium processes with one gap",async()=>{
 const x=fixture(),m=mockBrowser();const delays=[];
 const r=await audit(x.i,x.ir,x.h,x.hr,m.client,{gapMs:8000,
  pause:async ms=>delays.push(ms),settleMs:0});
 assert.equal(m.state.launches,2);assert.equal(m.state.visits.length,4);
 assert.deepEqual(delays,[8000]);assert.equal(r.grade.sameRunTitleMatches,2);
 assert.equal(r.goldenAccepted,0);validateReport(r);
});
test("26 insufficient gap denied before any browser request",async()=>{
 const x=fixture(),m=mockBrowser();
 await assert.rejects(()=>audit(x.i,x.ir,x.h,x.hr,m.client,{gapMs:1000,pause:async()=>{},settleMs:0}));
 assert.equal(m.state.launches,0);
});
test("27 one mismatch among two observed rounds stays HOLD",async()=>{
 const x=fixture(),m=mockBrowser({detailHeadings:[[OLD],["另一演出"]]});
 const r=await audit(x.i,x.ir,x.h,x.hr,m.client,{gapMs:8000,pause:async()=>{},settleMs:0});
 assert.equal(r.grade.sameRunTitleMatches,1);
 assert.equal(r.grade.formalIdentityReleaseEligible,false);
});
test("28 report anti-promotion mutation fails closed",async()=>{
 const x=fixture(),m=mockBrowser();
 const r=await audit(x.i,x.ir,x.h,x.hr,m.client,{gapMs:8000,pause:async()=>{},settleMs:0});
 r.published=true;assert.throws(()=>validateReport(r));
});
test("29 report grade must match observed actual rounds",async()=>{
 const x=fixture(),m=mockBrowser();
 const r=await audit(x.i,x.ir,x.h,x.hr,m.client,{gapMs:8000,pause:async()=>{},settleMs:0});
 r.grade.sameRunTitleMatches=0;assert.throws(()=>validateReport(r));
});
test("30 SHA manifest and local output path confinement",async()=>{
 const x=fixture(),m=mockBrowser();
 const r=await audit(x.i,x.ir,x.h,x.hr,m.client,{gapMs:8000,pause:async()=>{},settleMs:0});
 const temp=await mkdtemp(resolve("p30-l9j-test-"));
 try{
  const manifest=await emit(r,temp),data=await readFile(temp+"/ibon_39961_repeatability.json");
  assert.equal(manifest.fileSHA256["ibon_39961_repeatability.json"],hash(data));
  for(const p of [".","docs","docs/data.json","scripts/a","tests/a",".github",".git"])
   assert.throws(()=>safeOutput(p));
 }finally{await rm(temp,{recursive:true,force:true});}
});
