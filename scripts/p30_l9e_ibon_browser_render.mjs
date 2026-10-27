#!/usr/bin/env node
/** P30-L9-E normal Chromium rendering of TWO ibon public list entry pages.
 * Source-only isolated investigation. No stealth, WAF evasion, login, checkout,
 * cookie export, API guessing, stored browser profile, app Writer or Publisher.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {createHash} from "node:crypto";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";

export const KIND="EVENTRADAR_P30_L9E_IBON_PUBLIC_BROWSER_RENDER_DIAGNOSTICS_V1";
export const LISTS=Object.freeze([
  "https://ticket.ibon.com.tw/Index/entertainment",
  "https://ticket.ibon.com.tw/Home/MoreResult?inATAPID=105&inATAPWebType=entertainment"
]);
export const HOST="ticket.ibon.com.tw";
export const PARENT="8836dc29a6dcf4baaabed08102ffb1b7fbed6bc3";
export const MAX_ANCHORS=1000;
export const MAX_CANDIDATES=40;
const SAFE_DETAIL=/^\/(?:Web\/|WebV3\/)?ActivityInfo\/Details\/([0-9]{3,8})\/?$/;
const TITLE_SKIP=new Set(["活動詳情","查看詳情","查看活動","了解更多","立即購票","購票","更多","熱賣中","售票中","img","image","熱門","活動","娛樂","next","previous","詳細資料"]);
const sha=b=>createHash("sha256").update(b).digest("hex");
const json=x=>JSON.stringify(x,null,2)+"\n";
export function cleanTitle(value){
 return String(value??"").replace(/\s+/gu," ").trim().slice(0,180);
}
export function officialUrl(href,base=LISTS[0]){
 try{
  if(typeof href!=="string"||!href||/[\x00-\x1f\\]/.test(href))return null;
  const u=new URL(href,base);
  if(u.protocol!=="https:"||u.hostname!==HOST||u.username||u.password||
    (u.port&&u.port!=="443")||u.search||u.hash)return null;
  const match=SAFE_DETAIL.exec(u.pathname);
  if(!match)return null;
  return {url:"https://"+HOST+"/ActivityInfo/Details/"+match[1],eventId:match[1]};
 }catch{return null;}
}
export function candidateFromAnchor(row,base){
 if(!row||typeof row!=="object")return null;
 const canonical=officialUrl(row.href,base);
 if(!canonical)return null;
 const options=[row.cardHeading,row.anchorTitle,row.ariaLabel,row.anchorText,row.imageAlt];
 const title=options.map(cleanTitle).find(x=>x.length>=4&&x.length<=180&&!TITLE_SKIP.has(x.toLowerCase())&&!/^20\d{2}[/-]\d{1,2}[/-]\d{1,2}$/.test(x));
 if(!title)return null;
 return {candidateId:"ibon:"+canonical.eventId,officialUrl:canonical.url,title,
  evidenceRole:"BROWSER_RENDERED_SAME_CARD_LINK_TITLE_REVIEW_ONLY",
  detailTitleParity:false,formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN",
  goldenVerified:false,published:false};
}
export function parseRenderedAnchors(records,base){
 assert.ok(Array.isArray(records),"HOLD_L9E_DOM_RECORDS_MUST_BE_ARRAY");
 assert.ok(records.length<=MAX_ANCHORS,"HOLD_L9E_UNBOUNDED_DOM_ANCHORS");
 const found=[],seen=new Set();
 for(const row of records){
  const c=candidateFromAnchor(row,base);
  if(!c||seen.has(c.officialUrl))continue;
  seen.add(c.officialUrl);found.push(c);
  if(found.length>=MAX_CANDIDATES)break;
 }
 return found;
}
export function classify(state){
 if(state.error)return "HOLD_RENDER_NAVIGATION_OR_EVALUATION";
 if(state.redirectOutOfOrigin)return "HOLD_FOREIGN_NAVIGATION";
 if(state.httpStatus!==200)return "HOLD_HTTP_"+String(state.httpStatus??"NO_RESPONSE");
 if(state.wafHint)return "HOLD_WAF_OR_CAPTCHA_NO_BYPASS";
 return state.candidateCount>0?"RENDERED_SOURCE_CANDIDATES_REVIEW_ONLY":"HOLD_HTTP200_RENDERED_NO_BOUND_EVENT_ID";
}
export function validateReport(report){
 assert.equal(report.kind,KIND);
 assert.equal(report.parentL9DHead,PARENT);
 assert.equal(report.browserMode,"NORMAL_HEADLESS_CHROMIUM_NO_STEALTH");
 assert.equal(report.platform,"ibon");
 assert.equal(report.navigationAttemptCount,2);
 assert.equal(report.pages.length,2);
 assert.deepEqual(report.pages.map(x=>x.entryUrl),LISTS);
 assert.ok(report.candidateCount>=0&&report.candidateCount<=MAX_CANDIDATES);
 assert.equal(report.candidates.length,report.candidateCount);
 assert.equal(report.detailSamplesAttempted<=1,true);
 assert.equal(report.persistedRawHtml,false);
 assert.equal(report.persistedCookies,false);
 assert.equal(report.persistedNetworkBodies,false);
 assert.equal(report.executedUnapprovedNetworkCalls,false);
 assert.equal(report.releasedProductionData,false);
 assert.equal(report.goldenAccepted,0);
 assert.equal(report.formalFieldPromotions,0);
 assert.equal(report.published,false);
 assert.equal(report.writerExecuted,false);
 assert.equal(report.schedulerExecuted,false);
 assert.equal(report.notifierExecuted,false);
 assert.equal(report.releaseState,"HARD_HOLD_NO_PUBLICATION");
 assert.equal(report.existingAndroid44Preserved,true);
 for(const r of report.candidates){
  const match=officialUrl(r.officialUrl);
  assert.ok(match&&r.candidateId==="ibon:"+match.eventId);
  assert.equal(r.goldenVerified,false);assert.equal(r.published,false);
  assert.equal(r.formalDate,null);assert.equal(r.formalPrice,null);
  assert.equal(r.ticketStatus,"UNKNOWN");
 }
 return true;
}
function safeOut(out){
 const cwd=resolve("."),v=resolve(out);
 if(v===cwd||!v.startsWith(cwd+sep)||
   ["docs","scripts","tests",".github",".git","schemas"].some(d=>v===resolve(d)||v.startsWith(resolve(d)+sep)))
  throw Error("HOLD_L9E_ISOLATED_OUTPUT_ONLY");
 return v;
}
export {safeOut};
function origin(url){
 try{return new URL(url).hostname===HOST&&new URL(url).protocol==="https:";}catch{return false;}
}
function observeNetwork(page){
 const state={requests:0,firstPartyRequests:0,otherOriginRequests:0,
  firstPartyHttp200:0,firstPartyHttp403:0,firstPartyHttpOther:0,failedRequests:0};
 page.on("request",req=>{
  state.requests++;
  if(origin(req.url()))state.firstPartyRequests++;
  else state.otherOriginRequests++;
 });
 page.on("requestfailed",()=>{state.failedRequests++;});
 page.on("response",res=>{
  if(!origin(res.url()))return;
  if(res.status()===200)state.firstPartyHttp200++;
  else if(res.status()===403)state.firstPartyHttp403++;
  else state.firstPartyHttpOther++;
 });
 return state;
}
// Evaluated only inside the current browser document to READ public DOM.
// No form submission, clicks, storage access, fetch(), script injection or navigation.
function domRead(){
 const clip=x=>String(x||"").trim().replace(/\s+/g," ").slice(0,220);
 const anchors=[...document.querySelectorAll("a[href]")].slice(0,1000).map(a=>{
  const card=a.closest("article,li,[class*='card'],[class*='Card'],[class*='item'],[class*='Item']")||
    (a.parentElement&&a.parentElement.tagName!=="BODY"?a.parentElement:a);
  return {href:a.getAttribute("href")||"",cardHeading:clip(card.querySelector("h2,h3,h4,h5")?.textContent),
    anchorTitle:clip(a.getAttribute("title")),ariaLabel:clip(a.getAttribute("aria-label")),
    anchorText:clip(a.textContent),imageAlt:clip(a.querySelector("img")?.getAttribute("alt"))};
 });
 const texts=(document.body?.innerText||"").slice(0,4000).toLowerCase();
 return {anchorRecords:anchors,anchorTotal:document.querySelectorAll("a[href]").length,
  scriptCount:document.scripts.length,visibleBodyTextLength:document.body?.innerText?.length||0,
  documentTitleLength:document.title.length,
  wafHint:/cloudflare|captcha|verify you are human|access denied|存取遭拒|機器人驗證/i.test(texts)};
}
export async function audit(browser=chromium, opts={}){
 const context=await browser.launch({headless:true,args:["--no-sandbox"]});
 const results=[],map=new Map(),timeLimit=opts.maxSettleMs??5000;
 let attempts=0,detailAttempts=0,detailStatus="NOT_ATTEMPTED_NO_BOUND_SOURCE_ID";
 try{
  const ctx=await context.newContext({
    viewport:{width:1280,height:800},
    acceptDownloads:false,
    permissions:[],
    javaScriptEnabled:true
  });
  try{
   for(const entry of LISTS){
    const page=await ctx.newPage();
    const net=observeNetwork(page);
    const result={entryUrl:entry,httpStatus:null,finalOrigin:"UNDETERMINED",
      redirectOutOfOrigin:false,error:null,candidateCount:0,dom:{},
      networkObservation:net,state:"NOT_STARTED"};
    results.push(result);attempts++;
    try{
     const response=await page.goto(entry,{waitUntil:"domcontentloaded",timeout:25000});
     result.httpStatus=response?.status()??null;
     result.finalOrigin=origin(page.url())?"OFFICIAL_IBON":"OTHER_ORIGIN";
     result.redirectOutOfOrigin=!origin(page.url());
     if(!result.redirectOutOfOrigin&&result.httpStatus===200){
      await page.waitForTimeout(timeLimit);
      const dom=await page.evaluate(domRead);
      result.dom={anchorTotal:dom.anchorTotal,scriptCount:dom.scriptCount,
        visibleBodyTextLength:dom.visibleBodyTextLength,
        documentTitleLength:dom.documentTitleLength,wafHint:dom.wafHint};
      result.wafHint=dom.wafHint;
      for(const row of parseRenderedAnchors(dom.anchorRecords,page.url())){
       map.set(row.officialUrl,map.get(row.officialUrl)||row);
       if(map.size>=MAX_CANDIDATES)break;
      }
      result.candidateCount=parseRenderedAnchors(dom.anchorRecords,page.url()).length;
     }
    }catch(e){
     result.error=e?.name==="TimeoutError"?"NAVIGATION_TIMEOUT":
       "BROWSER_RENDER_ERROR_"+String(e?.name||"UNKNOWN").slice(0,32);
    }finally{
     result.state=classify(result);
     await page.close();
    }
   }
   if(map.size){
    const first=[...map.values()][0];
    const validated=officialUrl(first.officialUrl);
    assert.ok(validated,"HOLD_NON_CANONICAL_DETAIL_ID");
    const page=await ctx.newPage();
    detailAttempts=1;
    try{
     const response=await page.goto(first.officialUrl,{waitUntil:"domcontentloaded",timeout:25000});
     if(!origin(page.url())||response?.status()!==200){
      detailStatus="HOLD_DETAIL_HTTP_OR_REDIRECT";
     }else{
      await page.waitForTimeout(Math.min(timeLimit,4000));
      const headings=await page.locator("h1,h2,h3,h4").allTextContents({timeout:6000});
      const norm=s=>cleanTitle(s).replace(/\s+/gu," ");
      const matched=headings.some(h=>norm(h)===norm(first.title));
      first.detailTitleParity=matched;
      detailStatus=matched?"DETAIL_TITLE_PARITY_PASS":"HOLD_DETAIL_TITLE_MISMATCH";
     }
    }catch(e){detailStatus=e?.name==="TimeoutError"?"HOLD_DETAIL_TIMEOUT":"HOLD_DETAIL_BROWSER_ERROR";}
    finally{await page.close();}
   }
  }finally{await ctx.close();}
 }finally{await context.close();}
 const report={kind:KIND,runId:"P30-L9E-"+new Date().toISOString().replace(/[-:TZ.]/g,"").slice(0,14),
  parentL9DHead:PARENT,sourceOrigin:"FRESH_REAL_PUBLIC_CHROMIUM_RENDERING",
  browserMode:"NORMAL_HEADLESS_CHROMIUM_NO_STEALTH",platform:"ibon",
  navigationAttemptCount:attempts,pages:results,
  renderedSourceIdentityCandidatesOnly:true,candidateCount:map.size,
  candidates:[...map.values()],detailSamplesAttempted:detailAttempts,sampledDetailStatus:detailStatus,
  persistedRawHtml:false,persistedCookies:false,persistedNetworkBodies:false,
  executedUnapprovedNetworkCalls:false,releasedProductionData:false,
  fullCatalogVerified:false,formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  releaseState:"HARD_HOLD_NO_PUBLICATION"};
 validateReport(report);
 return report;
}
export async function emit(report,out){
 validateReport(report);
 const dir=safeOut(out);await mkdir(dir,{recursive:true});
 const source=Buffer.from(json(report));
 await writeFile(dir+"/ibon_browser_render_diagnostics.json",source);
 const manifest={kind:"EVENTRADAR_P30_L9E_BROWSER_SHA_MANIFEST_V1",
  sourceL9DHead:PARENT,runId:report.runId,sha256:{
    "ibon_browser_render_diagnostics.json":sha(source)},
  published:false,releaseState:"HARD_HOLD_NO_PUBLICATION"};
 await writeFile(dir+"/manifest.json",json(manifest));
 return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--out"]){process.stderr.write("HOLD_L9E_OUTPUT_REQUIRED\n");process.exitCode=2;}
 else{
  safeOut(args["--out"]);
  const report=await audit();
  await emit(report,args["--out"]);
  for(const p of report.pages)process.stdout.write("IBON_L9E_RENDER "+
   JSON.stringify({entryUrl:p.entryUrl,httpStatus:p.httpStatus,state:p.state,
    candidateCount:p.candidateCount,dom:p.dom,networkObservation:p.networkObservation})+"\n");
  process.stdout.write("PASS L9E_REAL_CHROMIUM_TWO_LIST_NAVIGATIONS "+
     report.navigationAttemptCount+"\n");
  process.stdout.write("QUALITY L9E_RENDERED_IBON_BOUND_CANDIDATES "+report.candidateCount+
     " DETAIL "+report.sampledDetailStatus+"\n");
  process.stdout.write("HOLD L9E_GOLDEN_PUBLISH_WRITER_SCHEDULER_DISABLED\n");
 }
}
