#!/usr/bin/env node
/** P30-L9-I: source-rebound investigation for exactly ibon ID 39961.
 * Sources L9-F original title + L9-H current mismatch SHA-sealed reports.
 * One normal, nonstealth public list navigation and one exact official detail;
 * no login/checkout/click/script injection/hidden API/credentials/WAF bypass.
 * No release even if current first-party list and detail now match: historical
 * drift remains a flagged provenance change until separate governance review.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {createHash} from "node:crypto";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";

export const KIND="EVENTRADAR_P30_L9I_IBON_39961_CURRENT_IDENTITY_AUDIT_V1";
export const SOURCE_L9H="EVENTRADAR_P30_L9H_IBON_LOCAL_DOM_HIERARCHY_READONLY_V1";
export const SOURCE_L9F="EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1";
export const L9H_HEAD="56d309a9d4d895c7adfb525723c6e2a9c4abd2cb";
export const L9H_RUN=40516301527;
export const L9H_ARTIFACT=12740505389;
export const L9F_RUN=40494326021;
export const L9F_ARTIFACT=12729277485;
export const EVENT_ID="39961";
export const HOST="ticket.ibon.com.tw";
export const LIST_URL="https://ticket.ibon.com.tw/Index/entertainment";
export const DETAIL_URL="https://ticket.ibon.com.tw/ActivityInfo/Details/"+EVENT_ID;
export const HARD_HOLD="HARD_HOLD_NO_PUBLICATION";
const digest=b=>createHash("sha256").update(b).digest("hex");
const output=x=>JSON.stringify(x,null,2)+"\n";
export const clip=x=>String(x??"").replace(/\s+/gu," ").trim().slice(0,180);
export const normalize=x=>clip(x).replace(/[，,。．.\-–—_·•]/gu,"").toLowerCase();
export function canonical(url,base=LIST_URL){
 try{
  const u=new URL(url,base);
  if(u.protocol!=="https:"||u.hostname!==HOST||u.username||u.password||
   (u.port&&u.port!=="443")||u.search||u.hash)return null;
  const m=/^\/ActivityInfo\/Details\/([0-9]{3,8})$/.exec(u.pathname);
  return m?{id:m[1],url:"https://"+HOST+u.pathname}:null;
 }catch{return null;}
}
export function verifyParents(h,hr,f,fr){
 assert.deepEqual(JSON.parse(hr),h,"HOLD_L9I_H_INPUT_BYTES_OBJECT_DISAGREE");
 assert.deepEqual(JSON.parse(fr),f,"HOLD_L9I_F_INPUT_BYTES_OBJECT_DISAGREE");
 assert.equal(h?.kind,SOURCE_L9H);
 assert.equal(h.parentHead,"07cc3ce1743a56d2bc60213d345f27672cef97d5");
 assert.equal(h.parentRun,40511115223);
 assert.equal(h.titleSourceRun,L9F_RUN);
 assert.equal(h.titleSourceArtifact,L9F_ARTIFACT);
 assert.equal(h.sampleCount,5);
 assert.equal(h.titleParityCount,4);
 assert.equal(h.locallyBoundReviewPairs,0);
 assert.equal(h.releaseState,HARD_HOLD);
 assert.equal(h.formalFieldPromotions,0);assert.equal(h.goldenAccepted,0);
 assert.equal(h.published,false);assert.equal(h.writerExecuted,false);
 assert.equal(f?.kind,SOURCE_L9F);assert.equal(f.additionalSampleSize,5);
 assert.equal(f.additionalTitleParity,5);
 assert.equal(f.releaseState,HARD_HOLD);
 assert.equal(f.formalFieldPromotions,0);assert.equal(f.goldenAccepted,0);
 assert.equal(f.published,false);
 const a=h.rows.filter(x=>x.candidateId==="ibon:"+EVENT_ID);
 const b=f.samples.filter(x=>x.candidateId==="ibon:"+EVENT_ID);
 assert.equal(a.length,1);assert.equal(b.length,1);
 const last=a[0],old=b[0];
 assert.equal(last.officialUrl,DETAIL_URL);
 assert.equal(old.officialUrl,DETAIL_URL);
 assert.equal(last.httpStatus,200);
 assert.equal(last.titleParity,false);
 assert.equal(last.status,"HOLD_TITLE_MISMATCH");
 assert.equal(last.reviewPairs?.length,0);
 assert.equal(old.titleParity,true);
 assert.equal(old.detailState,"DETAIL_TITLE_PARITY_PASS");
 assert.ok(clip(old.listTitle).length>=4);
 assert.equal(last.formalDate,null);assert.equal(old.formalDate,null);
 assert.equal(last.formalPrice,null);assert.equal(old.formalPrice,null);
 assert.equal(last.ticketStatus,"UNKNOWN");assert.equal(old.ticketStatus,"UNKNOWN");
 return{l9hSHA256:digest(hr),l9fSHA256:digest(fr),
  historicalTitle:clip(old.listTitle),historicalSource:old.officialUrl,
  priorDetailMatched:true,lastDetailMatched:false};
}
// A valid current listing match requires the SAME official numeric detail ID
// AND a directly associated title in an item/card (never whole page text).
export function currentListCandidates(records){
 assert.ok(Array.isArray(records)&&records.length<=500,"HOLD_UNBOUNDED_LIST_DOM");
 const found=new Map();
 for(const row of records){
  const u=canonical(row?.href);
  if(!u||u.id!==EVENT_ID)continue;
  const choices=[row?.cardTitle,row?.anchorTitle,row?.ariaLabel,row?.anchorText,row?.imageAlt]
   .map(clip).filter(x=>x.length>=4&&!/^(?:立即購票|購票|詳情|查看詳情|活動詳情|查看更多)$/u.test(x));
  if(choices.length===0)continue;
  const value=choices[0],norm=normalize(value);
  if(!norm)continue;
  if(!found.has(norm))found.set(norm,{title:value,officialUrl:DETAIL_URL,
   sourceRole:"CURRENT_RENDERED_OFFICIAL_LIST_SAME_CARD_REVIEW_ONLY"});
  if(found.size>=4)break;
 }
 return[...found.values()];
}
export function adjudicate({listStatus,detailStatus,listTitles,detailHeadings,oldTitle,foreignRedirect=false,waf=false}){
 const result={status:"HOLD",reason:"UNRESOLVED",currentSourceParity:false,
  historicTitleStillObserved:false,driftObserved:false,oldTitleCompared:true};
 if(foreignRedirect){result.reason="FOREIGN_REDIRECT";return result;}
 if(listStatus!==200||detailStatus!==200){result.reason="HTTP_NON_200";return result;}
 if(waf){result.reason="WAF_OR_CAPTCHA_NO_BYPASS";return result;}
 if(!Array.isArray(listTitles)||listTitles.length===0){
  result.reason="OFFICIAL_LIST_ID_NOT_OBSERVED";return result;
 }
 const d=(detailHeadings??[]).map(normalize).filter(Boolean);
 const l=listTitles.map(normalize).filter(Boolean);
 if(d.length===0){result.reason="NO_DETAIL_HEADINGS";return result;}
 result.historicTitleStillObserved=d.includes(normalize(oldTitle));
 const currentMatching=l.filter(x=>d.includes(x));
 // Contradictory current names for identical ID must be reviewed, not merged.
 if(new Set(l).size!==1){
  result.reason="AMBIGUOUS_LIST_TITLES_SAME_ID";
  return result;
 }
 if(currentMatching.length===0){
  result.reason="CURRENT_LIST_DETAIL_TITLE_MISMATCH";
  return result;
 }
 result.currentSourceParity=true;
 result.driftObserved=l[0]!==normalize(oldTitle);
 result.reason=result.driftObserved?
  "CURRENT_LIST_DETAIL_PARITY_BUT_HISTORICAL_TITLE_DRIFT_REVIEW_ONLY":
  "CURRENT_LIST_DETAIL_PARITY_REVIEW_ONLY";
 result.status="REVIEW_ONLY_NO_RELEASE";
 return result;
}
// Evaluate only current public DOM, no page global regex or body excerpt retained.
function listDomRead(){
 const trim=s=>String(s||"").trim().replace(/\s+/g," ").slice(0,180);
 const rows=[...document.querySelectorAll("a[href]")].slice(0,500).map(a=>{
  const holder=a.closest("article,li,[class*='card'],[class*='Card'],[class*='item'],[class*='Item']")||
    (a.parentElement?.tagName!=="BODY"?a.parentElement:a);
  return {href:a.getAttribute("href")||"",
   cardTitle:trim(holder?.querySelector("h2,h3,h4,h5")?.textContent),
   anchorTitle:trim(a.getAttribute("title")),
   ariaLabel:trim(a.getAttribute("aria-label")),
   anchorText:trim(a.textContent),imageAlt:trim(a.querySelector("img")?.getAttribute("alt"))};
 });
 const txt=(document.body?.innerText||"").slice(0,3000);
 return {rows,anchorsTotal:document.querySelectorAll("a[href]").length,
  bodyTextLength:document.body?.innerText?.length||0,
  scriptCount:document.scripts.length,
  wafHint:/captcha|cloudflare|verify you are human|存取遭拒/i.test(txt)};
}
function detailDomRead(){
 const trim=s=>String(s||"").trim().replace(/\s+/g," ").slice(0,180);
 const headings=[...document.querySelectorAll("h1,h2,h3,h4")].slice(0,30).map(x=>trim(x.textContent)).filter(Boolean);
 const txt=(document.body?.innerText||"").slice(0,3000);
 return {headings,headingCount:document.querySelectorAll("h1,h2,h3,h4").length,
  bodyTextLength:document.body?.innerText?.length||0,
  wafHint:/captcha|cloudflare|verify you are human|存取遭拒/i.test(txt)};
}
export async function audit(h,hr,f,fr,browser=chromium,opts={}){
 const provenance=verifyParents(h,hr,f,fr);
 const chromiumInstance=await browser.launch({headless:true,args:["--no-sandbox"]});
 const observed={list:{url:LIST_URL,status:null,state:"NOT_ATTEMPTED",visibleLength:0,links:0,scriptCount:0},
  detail:{url:DETAIL_URL,status:null,state:"NOT_ATTEMPTED",visibleLength:0,headingsCount:0},
  listTitles:[],detailHeadings:[]};
 try{
  const ctx=await chromiumInstance.newContext({viewport:{width:1280,height:800},
    javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   const page=await ctx.newPage();
   try{
    const response=await page.goto(LIST_URL,{waitUntil:"domcontentloaded",timeout:22000});
    observed.list.status=response?.status()??null;
    if(new URL(page.url()).hostname!==HOST)observed.list.state="HOLD_FOREIGN_REDIRECT";
    else if(observed.list.status!==200)observed.list.state="HOLD_HTTP_"+observed.list.status;
    else{
     await page.waitForTimeout(opts.settleMs??1600);
     const dom=await page.evaluate(listDomRead);
     observed.list.links=dom.anchorsTotal;
     observed.list.visibleLength=dom.bodyTextLength;
     observed.list.scriptCount=dom.scriptCount;
     observed.list.wafHint=dom.wafHint;
     observed.listTitles=currentListCandidates(dom.rows).map(x=>x.title);
     observed.list.state=dom.wafHint?"HOLD_WAF":"PUBLIC_LIST_RENDERED";
    }
   }catch(e){observed.list.state=e?.name==="TimeoutError"?"HOLD_LIST_TIMEOUT":"HOLD_LIST_BROWSER_ERROR";}
   finally{await page.close();}
   const detail=await ctx.newPage();
   try{
    const response=await detail.goto(DETAIL_URL,{waitUntil:"domcontentloaded",timeout:22000});
    observed.detail.status=response?.status()??null;
    if(new URL(detail.url()).hostname!==HOST)observed.detail.state="HOLD_FOREIGN_REDIRECT";
    else if(observed.detail.status!==200)observed.detail.state="HOLD_HTTP_"+observed.detail.status;
    else{
     await detail.waitForTimeout(opts.settleMs??1600);
     const dom=await detail.evaluate(detailDomRead);
     observed.detail.visibleLength=dom.bodyTextLength;
     observed.detail.headingsCount=dom.headingCount;
     observed.detail.wafHint=dom.wafHint;
     observed.detailHeadings=dom.headings;
     observed.detail.state=dom.wafHint?"HOLD_WAF":"PUBLIC_DETAIL_RENDERED";
    }
   }catch(e){observed.detail.state=e?.name==="TimeoutError"?"HOLD_DETAIL_TIMEOUT":"HOLD_DETAIL_BROWSER_ERROR";}
   finally{await detail.close();}
  }finally{await ctx.close();}
 }finally{await chromiumInstance.close();}
 const decision=adjudicate({
  listStatus:observed.list.status,detailStatus:observed.detail.status,
  listTitles:observed.listTitles,detailHeadings:observed.detailHeadings,
  oldTitle:provenance.historicalTitle,
  foreignRedirect:observed.list.state==="HOLD_FOREIGN_REDIRECT"||
   observed.detail.state==="HOLD_FOREIGN_REDIRECT",
  waf:observed.list.wafHint||observed.detail.wafHint
 });
 const report={kind:KIND,sourceOrigin:"NEW_PUBLIC_NORMAL_CHROMIUM_LIST_DETAIL_39961",
  eventId:EVENT_ID,originalTitle:provenance.historicalTitle,officialDetailUrl:DETAIL_URL,
  parentL9HHead:L9H_HEAD,parentL9HRun:L9H_RUN,parentL9HArtifact:L9H_ARTIFACT,
  parentL9FRun:L9F_RUN,parentL9FArtifact:L9F_ARTIFACT,
  l9hReportSHA256:provenance.l9hSHA256,l9fReportSHA256:provenance.l9fSHA256,
  navigationAttemptCount:2,...observed,decision,
  currentTitleAcceptedForPublication:false,rawHtmlPersisted:false,
  screenshotPersisted:false,cookiesPersisted:false,networkBodyPersisted:false,
  formalFieldPromotions:0,sessionSplits:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  releaseState:HARD_HOLD};
 validateReport(report);
 return report;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);
 assert.equal(r.eventId,EVENT_ID);assert.equal(r.officialDetailUrl,DETAIL_URL);
 assert.equal(r.parentL9HHead,L9H_HEAD);assert.equal(r.parentL9HRun,L9H_RUN);
 assert.equal(r.parentL9HArtifact,L9H_ARTIFACT);
 assert.equal(r.parentL9FRun,L9F_RUN);assert.equal(r.parentL9FArtifact,L9F_ARTIFACT);
 assert.equal(r.navigationAttemptCount,2);
 assert.equal(r.list.url,LIST_URL);assert.equal(r.detail.url,DETAIL_URL);
 assert.ok(r.listTitles.length<=4);assert.ok(r.detailHeadings.length<=30);
 assert.equal(r.currentTitleAcceptedForPublication,false);
 for(const[k,val]of Object.entries({rawHtmlPersisted:false,screenshotPersisted:false,
  cookiesPersisted:false,networkBodyPersisted:false,formalFieldPromotions:0,
  sessionSplits:0,goldenAccepted:0,published:false,writerExecuted:false,
  schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HARD_HOLD
 }))assert.equal(r[k],val,k);
 assert.equal(r.decision.status==="REVIEW_ONLY_NO_RELEASE"||r.decision.status==="HOLD",true);
 return true;
}
export function safeOut(value){
 const root=resolve("."),p=resolve(value);
 if(p===root||!p.startsWith(root+sep)||["docs","scripts","tests","schemas",".git",".github"].some(x=>p===resolve(x)||p.startsWith(resolve(x)+sep)))
  throw Error("HOLD_L9I_ISOLATED_OUTPUT_ONLY");
 return p;
}
export async function emit(r,path){
 validateReport(r);
 const dir=safeOut(path);await mkdir(dir,{recursive:true});
 const bytes=Buffer.from(output(r));await writeFile(dir+"/ibon_39961_identity_adjudication.json",bytes);
 const manifest={kind:"EVENTRADAR_P30_L9I_IDENTITY_SHA_MANIFEST_V1",
  parentL9HArtifact:L9H_ARTIFACT,parentL9FArtifact:L9F_ARTIFACT,
  parentL9HSHA256:r.l9hReportSHA256,parentL9FSHA256:r.l9fReportSHA256,
  filesSHA256:{"ibon_39961_identity_adjudication.json":digest(bytes)},
  published:false,releaseState:HARD_HOLD};
 await writeFile(dir+"/manifest.json",output(manifest));
 return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--l9h"]||!args["--l9f"]||!args["--out"]){console.error("HOLD_L9I_PINNED_SOURCES_REQUIRED");process.exitCode=2;}
 else{
  safeOut(args["--out"]);
  const hr=await readFile(args["--l9h"]),fr=await readFile(args["--l9f"]);
  const report=await audit(JSON.parse(hr),hr,JSON.parse(fr),fr);
  await emit(report,args["--out"]);
  console.log("L9I_OFFICIAL_39961",JSON.stringify({listHTTP:report.list.status,
   listCandidates:report.listTitles.length,detailHTTP:report.detail.status,
   headings:report.detailHeadings.length,decision:report.decision}));
  console.log("PASS L9I_PINNED_SOURCE_39961_PUBLIC_ADJUDICATION_NO_WRITE");
  console.log("HOLD L9I_FORMAL_GOLDEN_PUBLISHER_RELEASE");
 }
}
