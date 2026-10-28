#!/usr/bin/env node
/** P30-L9-J two independent ephemeral normal Chromium rounds of ibon 39961.
 * Read-only; no stealth/WAF bypass, checkout, login, arbitrary API, cookies or raw HTML.
 * A pair of same-run matches does NOT erase historic L9-H mismatch or release HOLD.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {createHash} from "node:crypto";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";
import {adjudicate,currentListCandidates,normalize,clip,LIST_URL,DETAIL_URL,EVENT_ID} from "./p30_l9i_ibon_39961_identity.mjs";
export {LIST_URL,DETAIL_URL,EVENT_ID};

export const KIND="EVENTRADAR_P30_L9J_IBON_39961_SAME_RUN_REPEATABILITY_V1";
export const PARENT_J_KIND="EVENTRADAR_P30_L9I_IBON_39961_CURRENT_IDENTITY_AUDIT_V1";
export const PARENT_H_KIND="EVENTRADAR_P30_L9H_IBON_LOCAL_DOM_HIERARCHY_READONLY_V1";
export const PARENT_I_HEAD="ca60d3182172ad7f824fbcb5a2a6c9189fecc74b";
export const PARENT_I_RUN=40524765567;
export const PARENT_I_ARTIFACT=12744025880;
export const PARENT_H_RUN=40516301527;
export const PARENT_H_ARTIFACT=12740505389;
export const ROUND_COUNT=2;
export const GAP_MS=8000;
export const HOST="ticket.ibon.com.tw";
export const HARD_HOLD="HARD_HOLD_NO_PUBLICATION";
export const sha=bytes=>createHash("sha256").update(bytes).digest("hex");
const stable=obj=>JSON.stringify(obj,null,2)+"\n";

export function validateParents(parent,raw,history,historyRaw){
 assert.deepEqual(JSON.parse(raw),parent,"HOLD_L9J_I_SOURCE_BYTES_DISAGREE");
 assert.deepEqual(JSON.parse(historyRaw),history,"HOLD_L9J_H_SOURCE_BYTES_DISAGREE");
 assert.equal(parent?.kind,PARENT_J_KIND);
 assert.equal(parent.parentL9HHead,"56d309a9d4d895c7adfb525723c6e2a9c4abd2cb");
 assert.equal(parent.parentL9HRun,PARENT_H_RUN);
 assert.equal(parent.parentL9HArtifact,PARENT_H_ARTIFACT);
 assert.equal(parent.eventId,EVENT_ID);
 assert.equal(parent.officialDetailUrl,DETAIL_URL);
 assert.equal(parent.navigationAttemptCount,2);
 assert.equal(parent.list.status,200);
 assert.equal(parent.detail.status,200);
 assert.equal(parent.listTitles.length,1);
 assert.equal(parent.decision.status,"REVIEW_ONLY_NO_RELEASE");
 assert.equal(parent.decision.currentSourceParity,true);
 assert.equal(parent.decision.historicTitleStillObserved,true);
 assert.equal(parent.decision.driftObserved,false);
 assert.equal(parent.currentTitleAcceptedForPublication,false);
 assert.equal(parent.releaseState,HARD_HOLD);
 assert.equal(parent.goldenAccepted,0);assert.equal(parent.formalFieldPromotions,0);
 assert.equal(parent.published,false);assert.equal(parent.writerExecuted,false);
 assert.equal(history?.kind,PARENT_H_KIND);
 assert.equal(history.parentHead,"07cc3ce1743a56d2bc60213d345f27672cef97d5");
 assert.equal(history.sampleCount,5);
 assert.equal(history.titleParityCount,4);
 assert.equal(history.releaseState,HARD_HOLD);
 const row=history.rows.filter(x=>x.candidateId==="ibon:"+EVENT_ID);
 assert.equal(row.length,1);
 assert.equal(row[0].officialUrl,DETAIL_URL);
 assert.equal(row[0].httpStatus,200);
 assert.equal(row[0].titleParity,false,"HOLD_L9J_PRIOR_CONTRADICTION_ABSENT");
 assert.equal(row[0].status,"HOLD_TITLE_MISMATCH");
 assert.equal(row[0].reviewPairs.length,0);
 assert.equal(parent.originalTitle&&typeof parent.originalTitle,"string");
 assert.ok(clip(parent.originalTitle).length>=4);
 return {iSHA256:sha(raw),hSHA256:sha(historyRaw),historicalTitle:clip(parent.originalTitle)};
}
export function validateOfficialFinal(url,expected){
 try{
  const u=new URL(url);
  const v=new URL(expected);
  return u.protocol==="https:"&&u.hostname===HOST&&!u.username&&!u.password&&
    !u.search&&!u.hash&&u.pathname===v.pathname&&(!u.port||u.port==="443");
 }catch{return false;}
}
function listDomRead(){
 const clean=x=>String(x??"").trim().replace(/\s+/g," ").slice(0,180);
 const rows=[...document.querySelectorAll("a[href]")].slice(0,500).map(a=>{
  const parent=a.closest("article,li,[class*='card'],[class*='Card'],[class*='item'],[class*='Item']")||
   (a.parentElement&&a.parentElement.tagName!=="BODY"?a.parentElement:a);
  return {href:a.getAttribute("href")||"",
   cardTitle:clean(parent?.querySelector("h2,h3,h4,h5")?.textContent),
   anchorTitle:clean(a.getAttribute("title")),ariaLabel:clean(a.getAttribute("aria-label")),
   anchorText:clean(a.textContent),imageAlt:clean(a.querySelector("img")?.getAttribute("alt"))};
 });
 const txt=(document.body?.innerText||"").slice(0,3000);
 return {rows,anchorCount:document.querySelectorAll("a[href]").length,
  textLength:document.body?.innerText?.length||0,
  wafHint:/captcha|cloudflare|verify you are human|存取遭拒/i.test(txt)};
}
function detailDomRead(){
 const clean=x=>String(x??"").trim().replace(/\s+/g," ").slice(0,180);
 const txt=(document.body?.innerText||"").slice(0,3000);
 return {headings:[...document.querySelectorAll("h1,h2,h3,h4")].slice(0,30)
  .map(x=>clean(x.textContent)).filter(Boolean),
  headingCount:document.querySelectorAll("h1,h2,h3,h4").length,
  textLength:document.body?.innerText?.length||0,
  wafHint:/captcha|cloudflare|verify you are human|存取遭拒/i.test(txt)};
}
function newRound(i){
 return {index:i+1,startedUtc:new Date().toISOString(),
  list:{url:LIST_URL,httpStatus:null,finalUrlRole:"UNOBSERVED",state:"NOT_ATTEMPTED",
   totalAnchors:0,textLength:0,candidateTitleCount:0},
  detail:{url:DETAIL_URL,httpStatus:null,finalUrlRole:"UNOBSERVED",state:"NOT_ATTEMPTED",
   headingCount:0,textLength:0},
  listTitles:[],detailHeadings:[],decision:null,endedUtc:null};
}
export async function capture(browser,roundNumber,sourceTitle,{settleMs=1600}={}){
 // Fresh browser process and context per round, no reuse of browser state/cookies.
 const output=newRound(roundNumber);
 const driver=await browser.launch({headless:true,args:["--no-sandbox"]});
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},acceptDownloads:false,
    javaScriptEnabled:true,permissions:[]});
  try{
   const lp=await ctx.newPage();
   try{
    const response=await lp.goto(LIST_URL,{waitUntil:"domcontentloaded",timeout:22000});
    output.list.httpStatus=response?.status()??null;
    const valid=validateOfficialFinal(lp.url(),LIST_URL);
    output.list.finalUrlRole=valid?"EXACT_OFFICIAL_ENTRY":"HOLD_REDIRECT_OR_DIFFERENT_PATH";
    if(!valid)output.list.state="HOLD_LIST_FINAL_URL";
    else if(output.list.httpStatus!==200)output.list.state="HOLD_LIST_HTTP";
    else{
     await lp.waitForTimeout(settleMs);
     const doc=await lp.evaluate(listDomRead);
     output.list.totalAnchors=doc.anchorCount;
     output.list.textLength=doc.textLength;
     output.list.wafHint=doc.wafHint;
     output.listTitles=currentListCandidates(doc.rows).map(x=>x.title);
     output.list.candidateTitleCount=output.listTitles.length;
     output.list.state=doc.wafHint?"HOLD_LIST_WAF":"RENDERED_PUBLIC_LIST";
    }
   }catch(e){
    output.list.state=e?.name==="TimeoutError"?"HOLD_LIST_TIMEOUT":"HOLD_LIST_BROWSER_ERROR";
   }finally{await lp.close();}
   const dp=await ctx.newPage();
   try{
    const response=await dp.goto(DETAIL_URL,{waitUntil:"domcontentloaded",timeout:22000});
    output.detail.httpStatus=response?.status()??null;
    const valid=validateOfficialFinal(dp.url(),DETAIL_URL);
    output.detail.finalUrlRole=valid?"EXACT_OFFICIAL_DETAIL":"HOLD_REDIRECT_OR_DIFFERENT_PATH";
    if(!valid)output.detail.state="HOLD_DETAIL_FINAL_URL";
    else if(output.detail.httpStatus!==200)output.detail.state="HOLD_DETAIL_HTTP";
    else{
     await dp.waitForTimeout(settleMs);
     const dom=await dp.evaluate(detailDomRead);
     output.detailHeadings=dom.headings;
     output.detail.headingCount=dom.headingCount;
     output.detail.textLength=dom.textLength;
     output.detail.wafHint=dom.wafHint;
     output.detail.state=dom.wafHint?"HOLD_DETAIL_WAF":"RENDERED_PUBLIC_DETAIL";
    }
   }catch(e){
    output.detail.state=e?.name==="TimeoutError"?"HOLD_DETAIL_TIMEOUT":"HOLD_DETAIL_BROWSER_ERROR";
   }finally{await dp.close();}
  }finally{await ctx.close();}
 }finally{await driver.close();}
 output.decision=adjudicate({
  listStatus:output.list.httpStatus,
  detailStatus:output.detail.httpStatus,
  listTitles:output.listTitles,
  detailHeadings:output.detailHeadings,
  oldTitle:sourceTitle,
  foreignRedirect:output.list.finalUrlRole!=="EXACT_OFFICIAL_ENTRY"||
    output.detail.finalUrlRole!=="EXACT_OFFICIAL_DETAIL",
  waf:output.list.wafHint===true||output.detail.wafHint===true
 });
 // A failed JS navigation must be a HOLD even if a page returned status 200.
 if(output.list.state!=="RENDERED_PUBLIC_LIST"||output.detail.state!=="RENDERED_PUBLIC_DETAIL"){
  output.decision={status:"HOLD",reason:"BROWSER_RENDER_NOT_COMPLETE",currentSourceParity:false,
   historicTitleStillObserved:false,driftObserved:false};
 }
 output.endedUtc=new Date().toISOString();
 return output;
}
export function grade(rounds,historyMismatch=true){
 assert.equal(historyMismatch,true,"HOLD_L9J_HISTORICAL_CONTRADICTION_MUST_REMAIN");
 assert.equal(rounds.length,ROUND_COUNT);
 const same=rounds.filter(x=>x.decision?.status==="REVIEW_ONLY_NO_RELEASE"&&
   x.decision.currentSourceParity===true&&
   x.decision.historicTitleStillObserved===true&&
   x.decision.driftObserved===false);
 const signatures=rounds.map(x=>JSON.stringify(x.listTitles.map(normalize).sort()));
 const consistent=signatures[0]===signatures[1]&&
   rounds.every(x=>x.listTitles.length===1);
 const match=consistent&&same.length===ROUND_COUNT;
 return {sameRunTitleMatches:same.length,consistentBetweenRounds:consistent,
  currentTwoRoundObservation:match?"TWO_SEPARATE_BROWSER_MATCHES_REVIEW_ONLY":
   "REPEATABILITY_FAILURE_OR_INCOMPLETE_HOLD",
  historicalMismatchRetained:true,unexplainedPriorMismatch:true,
  formalIdentityReleaseEligible:false,releaseState:HARD_HOLD};
}
export async function audit(i,ir,h,hr,browser=chromium,opts={}){
 const pinned=validateParents(i,ir,h,hr);
 const gap=opts.gapMs??GAP_MS;
 if(!Number.isFinite(gap)||gap<8000||gap>60000)throw Error("HOLD_L9J_RATE_INTERVAL");
 const pause=opts.pause??(ms=>new Promise(resolve=>setTimeout(resolve,ms)));
 const rounds=[];
 for(let n=0;n<ROUND_COUNT;n++){
  if(n>0)await pause(gap);
  rounds.push(await capture(browser,n,pinned.historicalTitle,opts));
 }
 const gradeResult=grade(rounds,true);
 const report={kind:KIND,
  sourceOrigin:"TWO_NEW_INDEPENDENT_NORMAL_BROWSER_PROCESSES_SAME_RUN",
  parentL9IHead:PARENT_I_HEAD,parentL9IRun:PARENT_I_RUN,
  parentL9IArtifact:PARENT_I_ARTIFACT,parentL9HRun:PARENT_H_RUN,
  parentL9HArtifact:PARENT_H_ARTIFACT,
  pinnedL9ISHA256:pinned.iSHA256,pinnedL9HSHA256:pinned.hSHA256,
  eventId:EVENT_ID,officialListUrl:LIST_URL,officialDetailUrl:DETAIL_URL,
  roundCount:ROUND_COUNT,minimumRoundGapMs:gap,topLevelNavigationsAttempted:4,
  independentBrowserProcesses:2,rounds,grade:gradeResult,
  goldenAccepted:0,formalFieldPromotions:0,formalTicketStatus:"UNKNOWN",
  formalEventDate:null,formalPrice:null,sessionSplits:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,cookiesPersisted:false,
  screenshotsPersisted:false,networkBodiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  releaseState:HARD_HOLD};
 validateReport(report);return report;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);assert.equal(r.parentL9IHead,PARENT_I_HEAD);
 assert.equal(r.parentL9IRun,PARENT_I_RUN);assert.equal(r.parentL9IArtifact,PARENT_I_ARTIFACT);
 assert.equal(r.parentL9HRun,PARENT_H_RUN);assert.equal(r.parentL9HArtifact,PARENT_H_ARTIFACT);
 assert.equal(r.eventId,EVENT_ID);assert.equal(r.officialListUrl,LIST_URL);
 assert.equal(r.officialDetailUrl,DETAIL_URL);assert.equal(r.roundCount,2);
 assert.equal(r.topLevelNavigationsAttempted,4);assert.equal(r.independentBrowserProcesses,2);
 assert.equal(r.rounds.length,2);
 assert.ok(r.minimumRoundGapMs>=8000&&r.minimumRoundGapMs<=60000);
 assert.deepEqual(r.grade,grade(r.rounds,true));
 assert.equal(r.grade.historicalMismatchRetained,true);
 assert.equal(r.grade.formalIdentityReleaseEligible,false);
 assert.equal(r.releaseState,HARD_HOLD);
 for(const row of r.rounds){
  assert.equal(row.list.url,LIST_URL);assert.equal(row.detail.url,DETAIL_URL);
  assert.ok(row.listTitles.length<=4);assert.ok(row.detailHeadings.length<=30);
  assert.ok(row.decision.status==="HOLD"||row.decision.status==="REVIEW_ONLY_NO_RELEASE");
 }
 for(const [key,value] of Object.entries({
  goldenAccepted:0,formalFieldPromotions:0,formalTicketStatus:"UNKNOWN",
  formalEventDate:null,formalPrice:null,sessionSplits:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,cookiesPersisted:false,screenshotsPersisted:false,networkBodiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true
 }))assert.equal(r[key],value,key);
 return true;
}
export function safeOutput(where){
 const root=resolve("."),target=resolve(where);
 if(target===root||!target.startsWith(root+sep)||
   ["docs","scripts","tests","schemas",".github",".git"].some(x=>target===resolve(x)||target.startsWith(resolve(x)+sep)))
  throw Error("HOLD_L9J_ISOLATED_OUTPUT_ONLY");
 return target;
}
export async function emit(r,where){
 validateReport(r);
 const dir=safeOutput(where);await mkdir(dir,{recursive:true});
 const file=Buffer.from(stable(r));
 await writeFile(dir+"/ibon_39961_repeatability.json",file);
 const manifest={kind:"EVENTRADAR_P30_L9J_SHA256_MANIFEST_V1",
  parentL9IArtifact:PARENT_I_ARTIFACT,parentL9HArtifact:PARENT_H_ARTIFACT,
  sourceL9ISHA256:r.pinnedL9ISHA256,sourceL9HSHA256:r.pinnedL9HSHA256,
  fileSHA256:{"ibon_39961_repeatability.json":sha(file)},
  releaseState:HARD_HOLD,published:false};
 await writeFile(dir+"/manifest.json",stable(manifest));return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let n=2;n<process.argv.length;n+=2)args[process.argv[n]]=process.argv[n+1];
 if(!args["--l9i"]||!args["--l9h"]||!args["--out"]){console.error("HOLD_L9J_INPUT_MISSING");process.exitCode=2;}
 else{
  safeOutput(args["--out"]);
  const ir=await readFile(args["--l9i"]),hr=await readFile(args["--l9h"]);
  const result=await audit(JSON.parse(ir),ir,JSON.parse(hr),hr);
  await emit(result,args["--out"]);
  for(const round of result.rounds)console.log("L9J_39961_ROUND",JSON.stringify({
   number:round.index,startedUtc:round.startedUtc,endedUtc:round.endedUtc,
   listHTTP:round.list.httpStatus,detailHTTP:round.detail.httpStatus,
   listTitleCount:round.listTitles.length,detailHeadingCount:round.detailHeadings.length,
   decision:round.decision.reason,status:round.decision.status
  }));
  console.log("PASS L9J_NEW_PUBLIC_TWO_ROUNDS_SOURCE_GRADE",result.grade.currentTwoRoundObservation);
  console.log("HOLD L9J_HISTORIC_MISMATCH_RETAINED_NO_FORMAL_RELEASE");
 }
}
