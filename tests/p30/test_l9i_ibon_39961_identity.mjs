import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {KIND,SOURCE_L9H,SOURCE_L9F,EVENT_ID,HOST,LIST_URL,DETAIL_URL,
 HARD_HOLD,normalize,canonical,verifyParents,currentListCandidates,adjudicate,
 audit,validateReport,safeOut,emit} from "../../scripts/p30_l9i_ibon_39961_identity.mjs";
const d=b=>createHash("sha256").update(b).digest("hex");
const BEFORE="示範音樂祭原活動";
const NOW="示範音樂祭更新活動";
function parents(){
 const rows=["39575","39878","39907","39961","39978"].map(id=>({
   candidateId:"ibon:"+id,officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,
   httpStatus:200,titleParity:id!=="39961",status:id==="39961"?"HOLD_TITLE_MISMATCH":"TITLE_PARITY_PASS",
   reviewPairs:[],rejections:[],formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN"
 }));
 const h={kind:SOURCE_L9H,parentHead:"07cc3ce1743a56d2bc60213d345f27672cef97d5",
  parentRun:40511115223,titleSourceRun:40494326021,titleSourceArtifact:12729277485,
  sampleCount:5,titleParityCount:4,locallyBoundReviewPairs:0,
  releaseState:HARD_HOLD,formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,rows};
 const f={kind:SOURCE_L9F,additionalSampleSize:5,additionalTitleParity:5,
  releaseState:HARD_HOLD,formalFieldPromotions:0,goldenAccepted:0,published:false,
  samples:rows.map(x=>({
    candidateId:x.candidateId,officialUrl:x.officialUrl,
    titleParity:true,detailState:"DETAIL_TITLE_PARITY_PASS",
    listTitle:x.candidateId==="ibon:39961"?BEFORE:"其他模擬活動",
    formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN"
  }))};
 return{h,hr:Buffer.from(JSON.stringify(h)),f,fr:Buffer.from(JSON.stringify(f))};
}
const card=(label=NOW,url=DETAIL_URL)=>({
 href:url,cardTitle:label,anchorTitle:"",ariaLabel:"",anchorText:"立即購票",imageAlt:""});
function mockBrowser({listCode=200,detailCode=200,listTitle=NOW,detailHeadings=[NOW],
  listMissing=false,detailForeign=false,listForeign=false,waf=false}={}){
 const urls=[];
 const browser={launch:async()=>({
  newContext:async()=>({
   newPage:async()=>{
    const index=urls.length;
    return {
     _url:"",
     async goto(url){urls.push(url);this._url=url;return{status:()=>index===0?listCode:detailCode};},
     url(){return index===0&&listForeign||index===1&&detailForeign?"https://off.test/":this._url;},
     async waitForTimeout(){},
     async evaluate(){
      if(index===0)return{
       rows:listMissing?[]:[card(listTitle)],
       anchorsTotal:67,bodyTextLength:1650,scriptCount:16,wafHint:waf};
      return{headings:detailHeadings,headingCount:detailHeadings.length,bodyTextLength:2000,wafHint:waf};
     },async close(){}
    };
   },async close(){}
  }),async close(){}
 })};
 return{browser,urls};
}
test("01 typed source identity gate",()=>assert.match(KIND,/39961_CURRENT_IDENTITY_AUDIT/));
test("02 one exact approved detail URL",()=>assert.equal(DETAIL_URL,"https://ticket.ibon.com.tw/ActivityInfo/Details/39961"));
test("03 exact site only and official numeric id",()=>{
 assert.equal(canonical(DETAIL_URL).id,EVENT_ID);
 assert.equal(canonical("/ActivityInfo/Details/39961").id,EVENT_ID);
});
test("04 login and checkout rejected",()=>{
 for(const v of ["/login","/Checkout","/ActivityInfo/Details/x39961"]){
  assert.equal(canonical(v),null,v);
 }
});
test("05 off-host, HTTP downgrade, query, fragment rejected",()=>{
 for(const v of ["http://ticket.ibon.com.tw/ActivityInfo/Details/39961",
 "https://ticket.ibon.com.tw.evil.test/ActivityInfo/Details/39961",
 DETAIL_URL+"?foo=1",DETAIL_URL+"#target",
 "https://a@ticket.ibon.com.tw/ActivityInfo/Details/39961"])assert.equal(canonical(v),null,v);
});
test("06 provenance exact dual source bytes and ID titles",()=>{
 const x=parents(),v=verifyParents(x.h,x.hr,x.f,x.fr);
 assert.equal(v.historicalTitle,BEFORE);
 assert.equal(v.l9hSHA256,d(x.hr));assert.equal(v.l9fSHA256,d(x.fr));
});
test("07 stale bytes fail closed",()=>{
 const x=parents();x.h.rows[0].status="other";
 assert.throws(()=>verifyParents(x.h,x.hr,x.f,x.fr));
});
test("08 L9H CURRENT mismatch required",()=>{
 const x=parents();x.h.rows.find(r=>r.candidateId==="ibon:39961").titleParity=true;
 x.hr=Buffer.from(JSON.stringify(x.h));
 assert.throws(()=>verifyParents(x.h,x.hr,x.f,x.fr));
});
test("09 L9F historic verified title required",()=>{
 const x=parents();x.f.samples.find(r=>r.candidateId==="ibon:39961").titleParity=false;
 x.fr=Buffer.from(JSON.stringify(x.f));
 assert.throws(()=>verifyParents(x.h,x.hr,x.f,x.fr));
});
test("10 source ID cannot silently change",()=>{
 const x=parents();x.f.samples.find(r=>r.candidateId==="ibon:39961").officialUrl="https://evil.test/39961";
 x.fr=Buffer.from(JSON.stringify(x.f));
 assert.throws(()=>verifyParents(x.h,x.hr,x.f,x.fr));
});
test("11 source Golden/Writer tamper refused",()=>{
 for(const [k,v] of [["goldenAccepted",1],["writerExecuted",true],["published",true]]){
  const x=parents();x.h[k]=v;x.hr=Buffer.from(JSON.stringify(x.h));
  assert.throws(()=>verifyParents(x.h,x.hr,x.f,x.fr));
 }
});
test("12 same card direct candidate with correct numeric ID",()=>{
 assert.equal(currentListCandidates([card()])[0].title,NOW);
});
test("13 other official ID is not 39961",()=>{
 assert.equal(currentListCandidates([card(NOW,"/ActivityInfo/Details/39978")]).length,0);
});
test("14 generic buy button title not event title",()=>{
 assert.equal(currentListCandidates([{href:DETAIL_URL,anchorText:"立即購票"}]).length,0);
});
test("15 offsite title and detail URL cannot be candidate",()=>{
 assert.equal(currentListCandidates([card(NOW,"https://fake.example/ActivityInfo/Details/39961")]).length,0);
});
test("16 duplicate official card must collapse",()=>{
 assert.equal(currentListCandidates([card(),card(),card()]).length,1);
});
test("17 conflicting titles preserved for ambiguity",()=>{
 assert.equal(currentListCandidates([card(NOW),card(BEFORE)]).length,2);
});
test("18 list DOM anchor bomb fails bounded limit",()=>{
 assert.throws(()=>currentListCandidates(Array(501).fill(card())));
});
test("19 current source title equals detail but historic drift is REVIEW not PASS release",()=>{
 const v=adjudicate({listStatus:200,detailStatus:200,
  listTitles:[NOW],detailHeadings:[NOW],oldTitle:BEFORE});
 assert.equal(v.currentSourceParity,true);assert.equal(v.driftObserved,true);
 assert.equal(v.status,"REVIEW_ONLY_NO_RELEASE");
});
test("20 current historic title matches both means REVIEW not writer",()=>{
 const v=adjudicate({listStatus:200,detailStatus:200,
  listTitles:[BEFORE],detailHeadings:[BEFORE],oldTitle:BEFORE});
 assert.equal(v.status,"REVIEW_ONLY_NO_RELEASE");assert.equal(v.driftObserved,false);
});
test("21 current list absent cannot clear HOLD even if detail same",()=>{
 const v=adjudicate({listStatus:200,detailStatus:200,
  listTitles:[],detailHeadings:[BEFORE],oldTitle:BEFORE});
 assert.equal(v.reason,"OFFICIAL_LIST_ID_NOT_OBSERVED");assert.equal(v.status,"HOLD");
});
test("22 list-detail mismatch stays HOLD",()=>{
 const v=adjudicate({listStatus:200,detailStatus:200,
  listTitles:[NOW],detailHeadings:["另一個活動"],oldTitle:BEFORE});
 assert.equal(v.reason,"CURRENT_LIST_DETAIL_TITLE_MISMATCH");
});
test("23 two different list titles for same ID stay ambiguous",()=>{
 const v=adjudicate({listStatus:200,detailStatus:200,
  listTitles:[BEFORE,NOW],detailHeadings:[NOW],oldTitle:BEFORE});
 assert.equal(v.reason,"AMBIGUOUS_LIST_TITLES_SAME_ID");
});
test("24 403 / 429 / timeout never become cancellation",()=>{
 for(const s of [403,429,null]){
  const v=adjudicate({listStatus:s,detailStatus:200,
   listTitles:[NOW],detailHeadings:[NOW],oldTitle:BEFORE});
  assert.equal(v.reason,"HTTP_NON_200");
 }
});
test("25 WAF or external redirect never promoted",()=>{
 for(const opts of [{waf:true},{foreignRedirect:true}]){
  const v=adjudicate({listStatus:200,detailStatus:200,
   listTitles:[NOW],detailHeadings:[NOW],oldTitle:BEFORE,...opts});
  assert.equal(v.status,"HOLD");
 }
});
test("26 title whitespace normalization is deterministic",()=>{
 assert.equal(normalize(" 示範　活動－Ａ "),normalize("示範 活動－Ａ"));
});
test("27 mocked Chromium visits EXACT two public page URLs",async()=>{
 const x=parents(),b=mockBrowser();
 const r=await audit(x.h,x.hr,x.f,x.fr,b.browser,{settleMs:0});
 assert.deepEqual(b.urls,[LIST_URL,DETAIL_URL]);
 assert.equal(r.navigationAttemptCount,2);
 assert.equal(r.decision.currentSourceParity,true);
 assert.equal(r.published,false);
 validateReport(r);
});
test("28 mocked current stale original title yields mismatch HOLD",async()=>{
 const x=parents(),b=mockBrowser({listTitle:BEFORE,detailHeadings:[NOW]});
 const r=await audit(x.h,x.hr,x.f,x.fr,b.browser,{settleMs:0});
 assert.equal(r.decision.status,"HOLD");
 assert.equal(r.decision.reason,"CURRENT_LIST_DETAIL_TITLE_MISMATCH");
});
test("29 mocked 403 or off-site detail no field promotion",async()=>{
 for(const opts of [{detailCode:403},{detailForeign:true}]){
  const x=parents(),b=mockBrowser(opts);
  const r=await audit(x.h,x.hr,x.f,x.fr,b.browser,{settleMs:0});
  assert.equal(r.decision.status,"HOLD");
  assert.equal(r.formalFieldPromotions,0);
 }
});
test("30 sealed output SHA and output confinement",async()=>{
 const x=parents(),b=mockBrowser({listMissing:true});
 const r=await audit(x.h,x.hr,x.f,x.fr,b.browser,{settleMs:0});
 const dir=await mkdtemp(resolve("p30-l9i-test-"));
 try{
  const manifest=await emit(r,dir);
  const content=await readFile(dir+"/ibon_39961_identity_adjudication.json");
  assert.equal(manifest.filesSHA256["ibon_39961_identity_adjudication.json"],d(content));
  for(const path of [".","docs","docs/data.json","scripts/a","tests/a",".git",".github"])
   assert.throws(()=>safeOut(path));
 }finally{await rm(dir,{recursive:true,force:true});}
});
