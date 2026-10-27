import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {resolve} from "node:path";
import {createHash} from "node:crypto";
import {KIND,LISTS,HOST,PARENT,cleanTitle,officialUrl,candidateFromAnchor,
 parseRenderedAnchors,classify,validateReport,safeOut,audit,emit} from "../../scripts/p30_l9e_ibon_browser_render.mjs";

const DETAIL="https://ticket.ibon.com.tw/ActivityInfo/Details/1234";
const TITLE="臺灣示範音樂祭";
const fixture={href:"/ActivityInfo/Details/1234",cardHeading:TITLE,anchorText:"立即購票"};
const sha=x=>createHash("sha256").update(x).digest("hex");
function candidate(){return candidateFromAnchor(fixture,LISTS[0]);}
function goodReport(){
 return {kind:KIND,parentL9DHead:PARENT,
  browserMode:"NORMAL_HEADLESS_CHROMIUM_NO_STEALTH",platform:"ibon",
  navigationAttemptCount:2,pages:LISTS.map(entryUrl=>({entryUrl})),
  candidateCount:1,candidates:[candidate()],detailSamplesAttempted:1,
  persistedRawHtml:false,persistedCookies:false,persistedNetworkBodies:false,
  executedUnapprovedNetworkCalls:false,releasedProductionData:false,
  goldenAccepted:0,formalFieldPromotions:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  releaseState:"HARD_HOLD_NO_PUBLICATION",existingAndroid44Preserved:true};
}
function fakeBrowser(hasCandidates=true,override={}){
 const made=[];
 const api={
  launch:async()=>({
   newContext:async()=>({
    newPage:async()=>{
     const position=made.length;
     const page={
      handlers:{},on(name,callback){this.handlers[name]=callback;},
      async goto(url){
       this.location=url;
       return {status:()=>override.status??200};
      },
      url(){return override.outOfOrigin?"https://evil.example.net/":this.location;},
      async waitForTimeout(_ms){},
      async evaluate(_fn){
       return {anchorRecords:(hasCandidates&&position===0)?[fixture]:[],
        anchorTotal:(hasCandidates&&position===0)?1:0,
        scriptCount:11,visibleBodyTextLength:250,documentTitleLength:10,wafHint:false};
      },
      locator(_selector){return {allTextContents:async()=>[TITLE]};},
      async close(){this.closed=true;}
     };
     made.push(page);return page;
    },async close(){}
   }),async close(){}
  })
 };
 return {api,made};
}
test("01 exactly two approved public listing URLs",()=>{
 assert.equal(LISTS.length,2);
 assert.ok(LISTS.every(x=>x.startsWith("https://"+HOST+"/")));
});
test("02 canonical direct activity URL",()=>assert.equal(officialUrl(DETAIL).eventId,"1234"));
test("03 Web and WebV3 official variants normalized",()=>{
 assert.equal(officialUrl("https://ticket.ibon.com.tw/Web/ActivityInfo/Details/1234").url,DETAIL);
 assert.equal(officialUrl("https://ticket.ibon.com.tw/WebV3/ActivityInfo/Details/1234").url,DETAIL);
});
test("04 off-host, deceptive suffix and protocol downgrade refused",()=>{
 for(const u of ["https://evil.test/ActivityInfo/Details/1234",
 "https://ticket.ibon.com.tw.evil.test/ActivityInfo/Details/1234",
 "http://ticket.ibon.com.tw/ActivityInfo/Details/1234"]){assert.equal(officialUrl(u),null,u);}
});
test("05 credentials, port, fragment, query refused",()=>{
 for(const u of ["https://u:p@ticket.ibon.com.tw/ActivityInfo/Details/1234",
 "https://ticket.ibon.com.tw:444/ActivityInfo/Details/1234",
 DETAIL+"#top",DETAIL+"?token=abc"]){assert.equal(officialUrl(u),null,u);}
});
test("06 checkout, login and wrong path rejected",()=>{
 for(const u of ["/login","/Checkout/Details/1234","/ActivityInfo/Details/nope",
 "/ActivityInfo/Details/12"]){assert.equal(officialUrl(u),null,u);}
});
test("07 event ID upper-bound 8 digits",()=>{
 assert.equal(officialUrl("/ActivityInfo/Details/123456789"),null);
 assert.equal(officialUrl("/ActivityInfo/Details/12345678").eventId,"12345678");
});
test("08 title from same-card heading not buy button",()=>{
 const r=candidate();assert.equal(r.title,TITLE);assert.equal(r.officialUrl,DETAIL);
});
test("09 absent same-card credible title means no candidate",()=>{
 assert.equal(candidateFromAnchor({href:DETAIL,anchorText:"購票"}),null);
});
test("10 text normalization only, no metadata inference",()=>{
 assert.equal(cleanTitle(" A \n　 B"),"A B");
 const r=candidate();assert.equal(r.ticketStatus,"UNKNOWN");
 assert.equal(r.formalDate,null);assert.equal(r.formalPrice,null);
});
test("11 dedup URL across repeated anchors",()=>{
 const r=parseRenderedAnchors([fixture,fixture,{...fixture,href:DETAIL}],LISTS[0]);
 assert.equal(r.length,1);
});
test("12 bound records 1000 or fewer",()=>{
 assert.throws(()=>parseRenderedAnchors(Array(1001).fill(fixture),LISTS[0]));
});
test("13 nonarray DOM output rejected",()=>assert.throws(()=>parseRenderedAnchors(null,LISTS[0])));
test("14 200 and no ID remain explicit HOLD",()=>{
 assert.equal(classify({httpStatus:200,candidateCount:0}),"HOLD_HTTP200_RENDERED_NO_BOUND_EVENT_ID");
});
test("15 HTTP 403, timeout, WAF retain different blockers",()=>{
 assert.equal(classify({httpStatus:403}),"HOLD_HTTP_403");
 assert.equal(classify({error:"NAVIGATION_TIMEOUT"}),"HOLD_RENDER_NAVIGATION_OR_EVALUATION");
 assert.equal(classify({httpStatus:200,wafHint:true,candidateCount:2}),"HOLD_WAF_OR_CAPTCHA_NO_BYPASS");
});
test("16 foreign navigation is HOLD",()=>{
 assert.equal(classify({httpStatus:200,redirectOutOfOrigin:true}),"HOLD_FOREIGN_NAVIGATION");
});
test("17 reviewed candidate is never Golden or published",()=>{
 const r=candidate();assert.equal(r.detailTitleParity,false);
 assert.equal(r.goldenVerified,false);assert.equal(r.published,false);
});
test("18 valid read-only diagnostic report accepted",()=>assert.equal(validateReport(goodReport()),true));
test("19 fake released data refused",()=>{
 const r=goodReport();r.releasedProductionData=true;
 assert.throws(()=>validateReport(r));
});
test("20 fake Golden, Writer, scheduler and publisher refused",()=>{
 for(const [key,value] of [["goldenAccepted",1],["writerExecuted",true],
 ["schedulerExecuted",true],["published",true]]){
  const r=goodReport();r[key]=value;assert.throws(()=>validateReport(r),key);
 }
});
test("21 wrong source parent or truncated navigation refused",()=>{
 const a=goodReport();a.parentL9DHead="invalid";assert.throws(()=>validateReport(a));
 const b=goodReport();b.navigationAttemptCount=1;assert.throws(()=>validateReport(b));
});
test("22 altered official provenance URL refused",()=>{
 const r=goodReport();r.candidates[0].officialUrl="https://evil.test/ActivityInfo/Details/1234";
 assert.throws(()=>validateReport(r));
});
test("23 paths cannot overlap production or escape repo",()=>{
 for(const dir of [".","docs","docs/data.json","scripts/out","tests/a",".github/workflows",".git"]){
  assert.throws(()=>safeOut(dir),dir);
 }
});
test("24 fully synthetic no-candidate Chromium still HOLD",async()=>{
 const f=fakeBrowser(false),r=await audit(f.api,{maxSettleMs:0});
 assert.equal(r.navigationAttemptCount,2);assert.equal(r.candidateCount,0);
 assert.equal(r.sampledDetailStatus,"NOT_ATTEMPTED_NO_BOUND_SOURCE_ID");
 assert.ok(r.pages.every(x=>x.state==="HOLD_HTTP200_RENDERED_NO_BOUND_EVENT_ID"));
 assert.equal(f.made.length,2);
});
test("25 synthetic positive browser performs exactly one detail identity",async()=>{
 const f=fakeBrowser(true),r=await audit(f.api,{maxSettleMs:0});
 assert.equal(r.navigationAttemptCount,2);assert.equal(r.candidateCount,1);
 assert.equal(r.detailSamplesAttempted,1);
 assert.equal(r.sampledDetailStatus,"DETAIL_TITLE_PARITY_PASS");
 assert.equal(r.candidates[0].detailTitleParity,true);
 assert.equal(f.made.length,3);
});
test("26 synthetic foreign redirect makes no candidates",async()=>{
 const f=fakeBrowser(true,{outOfOrigin:true}),r=await audit(f.api,{maxSettleMs:0});
 assert.equal(r.candidateCount,0);
 assert.ok(r.pages.every(x=>x.state==="HOLD_FOREIGN_NAVIGATION"));
});
test("27 synthetic server 403 never declares empty event inventory",async()=>{
 const f=fakeBrowser(true,{status:403}),r=await audit(f.api,{maxSettleMs:0});
 assert.equal(r.candidateCount,0);
 assert.equal(r.pages[0].state,"HOLD_HTTP_403");
});
test("28 evidence sha manifest exact and no raw HTML",async()=>{
 const tmp=await mkdtemp(resolve("p30-l9e-test-"));
 try{
  const r=goodReport();r.runId="P30-L9E-TEST";
  const m=await emit(r,tmp);
  const bytes=await readFile(tmp+"/ibon_browser_render_diagnostics.json");
  assert.equal(m.sha256["ibon_browser_render_diagnostics.json"],sha(bytes));
  const o=JSON.parse(bytes.toString());
  assert.equal(o.persistedRawHtml,false);assert.equal(o.published,false);
 }finally{await rm(tmp,{recursive:true,force:true});}
});
test("29 same identity across listings does not make two events",async()=>{
 const row1=fixture;
 const f=fakeBrowser(false);
 // Pure parsing of same ID from both pages, no inferred two separate events.
 const items=parseRenderedAnchors([row1,{...row1,href:DETAIL}],LISTS[1]);
 assert.equal(items.length,1);
});
test("30 title mismatched numeric ID cannot be manufactured from a search URL",()=>{
 assert.equal(candidateFromAnchor({href:"/Search?id=1234",cardHeading:TITLE}),null);
});
