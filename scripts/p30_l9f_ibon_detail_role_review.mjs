#!/usr/bin/env node
/** P30-L9-F: SHA-pinned L9-E NEW ibon candidate identities -> five fresh details.
 * Normal Chromium only. No login, checkout, stealth, unapproved APIs, Writer,
 * publication, Golden promotion, browser profile/cookie or raw HTML archival.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {createHash} from "node:crypto";
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";
export const KIND="EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1";
export const INPUT_KIND="EVENTRADAR_P30_L9E_IBON_PUBLIC_BROWSER_RENDER_DIAGNOSTICS_V1";
export const PARENT_SHA="63a079c1bee7111b1ef7b04431607d9845fe3b9f";
export const PARENT_RUN=40449476633;
export const PARENT_ARTIFACT=12709568132;
export const HOST="ticket.ibon.com.tw";
export const SAMPLE_LIMIT=5;
export const REPORT_STATE="HARD_HOLD_NO_PUBLICATION";
const sha=x=>createHash("sha256").update(x).digest("hex");
const stable=x=>JSON.stringify(x,null,2)+"\n";
const normalize=x=>String(x??"").replace(/\s+/gu," ").trim().slice(0,220);
const detailRx=/^\/ActivityInfo\/Details\/([0-9]{3,8})$/;
export function canonical(source){
 try{
  const u=new URL(source);
  if(u.protocol!=="https:"||u.hostname!==HOST||u.username||u.password||
    u.search||u.hash||(u.port&&u.port!=="443"))return null;
  const m=detailRx.exec(u.pathname);
  return m?{eventId:m[1],url:"https://"+HOST+u.pathname}:null;
 }catch{return null;}
}
export function validateSource(p,bytes){
 assert.equal(p?.kind,INPUT_KIND,"HOLD_WRONG_SOURCE_GATE");
 assert.equal(p.parentL9DHead,"8836dc29a6dcf4baaabed08102ffb1b7fbed6bc3","HOLD_SOURCE_CHAIN");
 assert.equal(p.sourceOrigin,"FRESH_REAL_PUBLIC_CHROMIUM_RENDERING","HOLD_FAKE_FRESH");
 assert.equal(p.navigationAttemptCount,2,"HOLD_SOURCE_NAVIGATION_COUNT");
 assert.equal(p.candidateCount,22,"HOLD_PINNED_CANDIDATE_COUNT");
 assert.equal(p.candidates?.length,22,"HOLD_SOURCE_CANDIDATE_ROWS");
 assert.equal(p.sampledDetailStatus,"DETAIL_TITLE_PARITY_PASS","HOLD_SOURCE_DETAIL_PARITY");
 assert.equal(p.detailSamplesAttempted,1,"HOLD_SOURCE_SAMPLE_COUNT");
 assert.equal(p.persistedRawHtml,false);assert.equal(p.persistedCookies,false);
 assert.equal(p.persistedNetworkBodies,false);
 assert.equal(p.formalFieldPromotions,0);assert.equal(p.goldenAccepted,0);
 assert.equal(p.published,false);assert.equal(p.writerExecuted,false);
 assert.equal(p.schedulerExecuted,false);assert.equal(p.notifierExecuted,false);
 assert.equal(p.releaseState,REPORT_STATE);
 const ids=new Set();
 let parentMatched=0;
 for(const c of p.candidates){
  const id=canonical(c.officialUrl);
  assert.ok(id,"HOLD_FOREIGN_OR_UNBOUNDED_SOURCE_URL");
  assert.equal(c.candidateId,"ibon:"+id.eventId,"HOLD_ID_URL_MISMATCH");
  assert.ok(normalize(c.title).length>=4,"HOLD_TITLE_EMPTY");
  assert.equal(c.formalDate,null);assert.equal(c.formalPrice,null);
  assert.equal(c.ticketStatus,"UNKNOWN");assert.equal(c.goldenVerified,false);
  assert.equal(c.published,false);
  assert.ok(!ids.has(c.candidateId),"HOLD_DUPLICATE_SOURCE_ID");
  ids.add(c.candidateId);
  if(c.detailTitleParity)parentMatched++;
 }
 assert.equal(parentMatched,1,"HOLD_PARENT_DETAIL_PARITY_COUNT");
 assert.equal(p.existingAndroid44Preserved,true);
 return {sourceSHA256:sha(bytes),candidateCount:22,sourceDetailParity:parentMatched};
}
export function chooseAdditional(p,n=SAMPLE_LIMIT){
 assert.ok(Number.isInteger(n)&&n>=3&&n<=5,"HOLD_SAMPLE_COUNT_NOT_BOUNDED");
 const rows=p.candidates.filter(x=>!x.detailTitleParity)
  .sort((a,b)=>Number(canonical(a.officialUrl).eventId)-Number(canonical(b.officialUrl).eventId));
 assert.ok(rows.length>=n,"HOLD_INSUFFICIENT_UNREVIEWED_SOURCE_IDS");
 const indices=new Set();
 for(let i=0;i<n;i++)indices.add(Math.floor(i*(rows.length-1)/(n-1)));
 assert.equal(indices.size,n);
 return [...indices].map(i=>rows[i]);
}
const LABELS=[
 ["EVENT_PERIOD",/^(?:活動日期|活動時間|展演日期|演出日期|演出時間|開演時間|場次日期)$/u],
 ["ADMISSION_TIME",/^(?:入場時間|進場時間|開放入場)$/u],
 ["SALE_PERIOD",/^(?:售票期間|售票時間|開賣時間|預售期間|啟售日期)$/u],
 ["REGISTRATION_PERIOD",/^(?:報名期間|報名時間|登記期間|登記時間)$/u],
 ["VOUCHER_VALIDITY",/^(?:票券有效期間|票券有效期限|兌換期限|使用期限)$/u],
 ["VENUE",/^(?:場地|活動地點|演出地點|活動場館|演出場館)$/u],
 ["PRICE",/^(?:票價|票價資訊|票券價格|售票價格)$/u],
 ["SESSION",/^(?:場次|場次資訊|演出場次|演出日期與場次)$/u]
];
const TIME_TOKEN=/(?:20\d{2}[年\/.\-]\s*\d{1,2}|\d{1,2}\/\d{1,2}|\d{1,2}:\d{2})/u;
const PRICE_TOKEN=/(?:NT\s*\$\s*[\d,]+|TWD\s*[\d,]+|[$＄]\s*[\d,]+|[\d,]+\s*(?:元|圓))/iu;
const LABEL_RE=/(?:報名|登記|開賣|預售|販售|售票|入場|進場|票券有效)/u;
export function classifyField(pair){
 if(!pair||typeof pair!=="object")return null;
 const label=normalize(pair.label).replace(/[：:]\s*$/u,"");
 const value=normalize(pair.value);
 if(!value||value.length>110)return null;
 const match=LABELS.find(([,re])=>re.test(label));
 if(!match)return null;
 const role=match[0];
 let quality="REVIEW_ONLY";
 if(role==="PRICE"){
  quality=PRICE_TOKEN.test(value)?"PRICE_TOKEN_REVIEW_REQUIRED":
   /^(?:免費|免票|自由入場)$/u.test(value)?"FREE_TEXT_REVIEW_REQUIRED":
   "REJECT_GENERIC_OR_NONNUMERIC_PRICE";
 }else if(role==="VENUE"){
  quality=/^(?:資訊|詳情|尚未公告|待公告|未知|查詢)$/u.test(value)?"REJECT_GENERIC_VENUE":"VENUE_REVIEW_REQUIRED";
 }else if(role==="SESSION"){
  quality="SESSION_RELATION_REVIEW_REQUIRED_NO_SPLIT";
 }else{
  if(!TIME_TOKEN.test(value))quality="REJECT_NO_DATE_TIME_TOKEN";
  else if(role==="EVENT_PERIOD"&&LABEL_RE.test(value))quality="HOLD_ROLE_CONFLICT_EVENT_VS_SALE_OR_ADMISSION";
  else quality="TIME_ROLE_REVIEW_REQUIRED";
 }
 return {role,label,observedValue:value,quality,
  verified:false,formalFieldPromoted:false};
}
export function reviewPairs(pairs,allow){
 if(!allow)return {evidence:[],rejected:[],observedPairCount:Math.min(pairs?.length??0,60)};
 assert.ok(Array.isArray(pairs)&&pairs.length<=60,"HOLD_UNBOUNDED_DETAIL_DOM_PAIRS");
 const evidence=[],rejected=[],seen=new Set();
 for(const p of pairs){
  const r=classifyField(p);
  if(!r)continue;
  const key=r.role+"|"+r.label+"|"+r.observedValue;
  if(seen.has(key))continue;seen.add(key);
  if(r.quality.startsWith("REJECT")||r.quality.startsWith("HOLD"))rejected.push(r);
  else evidence.push(r);
  if(evidence.length+rejected.length>=12)break;
 }
 return {evidence,rejected,observedPairCount:pairs.length};
}
// Browser context only: collect explicit adjacent label/value pairs in public rendered DOM.
// Never scrape a global body date or turn registration into event date.
function readPublicDetails(){
 const clip=v=>String(v??"").replace(/\s+/g," ").trim().slice(0,120);
 const pairs=[];
 const push=(label,value)=>{
  if(pairs.length<60&&clip(label)&&clip(value))pairs.push({label:clip(label),value:clip(value)});
 };
 for(const tr of document.querySelectorAll("tr")){
  const head=tr.querySelector("th"),value=tr.querySelector("td");
  if(head&&value)push(head.textContent,value.textContent);
 }
 for(const dt of document.querySelectorAll("dt")){
  if(dt.nextElementSibling?.tagName==="DD")push(dt.textContent,dt.nextElementSibling.textContent);
 }
 for(const el of document.querySelectorAll("li,p")){
  if(pairs.length>=60)break;
  if(el.querySelector("table,dl,ul,ol"))continue;
  const txt=clip(el.textContent);
  const m=/^([^:：]{2,15})\s*[:：]\s*(.{1,110})$/u.exec(txt);
  if(m)push(m[1],m[2]);
 }
 return {headings:[...document.querySelectorAll("h1,h2,h3,h4")].slice(0,32).map(x=>clip(x.textContent)),
  pairs,hasHtmlBody:!!document.body};
}
export function emptyResult(c){return{
  candidateId:c.candidateId,officialUrl:c.officialUrl,listTitle:c.title,
  httpStatus:null,finalHost:null,titleParity:false,detailState:"NOT_ATTEMPTED",
  roleEvidence:[],rejectedEvidence:[],observedPairCount:0,
  formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN",
  sessionSplitCount:0,fieldPromotions:0,published:false};
}
export function acceptResult(record){
 const c=canonical(record.officialUrl);
 assert.ok(c&&record.candidateId==="ibon:"+c.eventId);
 assert.equal(record.fieldPromotions,0);assert.equal(record.sessionSplitCount,0);
 assert.equal(record.formalDate,null);assert.equal(record.formalPrice,null);
 assert.equal(record.ticketStatus,"UNKNOWN");assert.equal(record.published,false);
 if(!record.titleParity){
  assert.equal(record.roleEvidence.length,0,"HOLD_UNBOUND_FIELDS");
  assert.equal(record.rejectedEvidence.length,0,"HOLD_UNBOUND_REJECTS");
 }
 return true;
}
export async function audit(source,bytes,browser=chromium,opts={}){
 const lineage=validateSource(source,bytes);
 const chosen=chooseAdditional(source,opts.sampleSize??5);
 const browserInstance=await browser.launch({headless:true,args:["--no-sandbox"]});
 const results=[];
 try{
  const context=await browserInstance.newContext({viewport:{width:1280,height:800},
    javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   for(const c of chosen){
    const out=emptyResult(c);results.push(out);
    const page=await context.newPage();
    try{
     const response=await page.goto(c.officialUrl,{waitUntil:"domcontentloaded",timeout:22000});
     out.httpStatus=response?.status()??null;
     out.finalHost=new URL(page.url()).hostname;
     if(out.finalHost!==HOST){out.detailState="HOLD_EXTERNAL_REDIRECT";continue;}
     if(out.httpStatus!==200){out.detailState="HOLD_HTTP_"+out.httpStatus;continue;}
     await page.waitForTimeout(opts.settleMs??1700);
     const dom=await page.evaluate(readPublicDetails);
     const norm=s=>normalize(s).replace(/[，,。．.\-–—_·•]/gu,"").toLowerCase();
     out.titleParity=dom.headings.some(h=>norm(h)===norm(c.title));
     out.detailState=out.titleParity?"DETAIL_TITLE_PARITY_PASS":"HOLD_TITLE_PARITY";
     const reviewed=reviewPairs(dom.pairs,out.titleParity);
     out.roleEvidence=reviewed.evidence;
     out.rejectedEvidence=reviewed.rejected;
     out.observedPairCount=reviewed.observedPairCount;
    }catch(e){out.detailState=e?.name==="TimeoutError"?"HOLD_DETAIL_TIMEOUT":"HOLD_RENDER_EXCEPTION";}
    finally{await page.close();}
    acceptResult(out);
   }
  }finally{await context.close();}
 }finally{await browserInstance.close();}
 const report={kind:KIND,schemaVersion:"1.0.0",
  runId:"P30-L9F-"+new Date().toISOString().replace(/\D/g,"").slice(0,14),
  candidateOrigin:"L9F_NEW_NORMAL_BROWSER_DETAIL_SAMPLE",
  parentL9EHead:PARENT_SHA,parentL9ERun:PARENT_RUN,parentArtifactId:PARENT_ARTIFACT,
  pinnedParentReportSHA256:lineage.sourceSHA256,parentCandidateCount:22,
  previousDetailTitleParity:1,additionalSampleSize:results.length,
  additionalTitleParity:results.filter(x=>x.titleParity).length,
  additionalRoleEvidenceCount:results.reduce((n,x)=>n+x.roleEvidence.length,0),
  additionalRejectedEvidenceCount:results.reduce((n,x)=>n+x.rejectedEvidence.length,0),
  samples:results,sourceCatalogComplete:false,formalFieldPromotions:0,
  sessionSplits:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  releaseState:REPORT_STATE};
 validateReport(report);
 return report;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);assert.equal(r.parentL9EHead,PARENT_SHA);
 assert.equal(r.parentL9ERun,PARENT_RUN);assert.equal(r.parentArtifactId,PARENT_ARTIFACT);
 assert.equal(r.parentCandidateCount,22);assert.equal(r.previousDetailTitleParity,1);
 assert.ok(r.additionalSampleSize>=3&&r.additionalSampleSize<=5);
 assert.equal(r.samples.length,r.additionalSampleSize);
 assert.equal(r.additionalTitleParity,r.samples.filter(x=>x.titleParity).length);
 assert.equal(r.additionalRoleEvidenceCount,r.samples.reduce((n,x)=>n+x.roleEvidence.length,0));
 assert.equal(r.additionalRejectedEvidenceCount,r.samples.reduce((n,x)=>n+x.rejectedEvidence.length,0));
 assert.equal(r.releaseState,REPORT_STATE);
 assert.equal(r.sourceCatalogComplete,false);
 for(const [k,v] of [["formalFieldPromotions",0],["sessionSplits",0],
 ["goldenAccepted",0],["published",false],["writerExecuted",false],
 ["schedulerExecuted",false],["notifierExecuted",false],["mergeExecuted",false],
 ["existingAndroid44Preserved",true],["l8CoreAndroidPassPreserved",true]])assert.equal(r[k],v,k);
 const seen=new Set();
 for(const s of r.samples){acceptResult(s);assert.ok(!seen.has(s.candidateId));seen.add(s.candidateId);}
 return true;
}
export function safeOut(path){
 const root=resolve("."),p=resolve(path);
 if(p===root||!p.startsWith(root+sep)||["docs","scripts","tests",".git",".github","schemas"].some(x=>p===resolve(x)||p.startsWith(resolve(x)+sep)))
  throw Error("HOLD_ISOLATED_OUTPUT_ONLY");
 return p;
}
export async function emit(report,out){
 validateReport(report);
 const dest=safeOut(out);await mkdir(dest,{recursive:true});
 const bytes=Buffer.from(stable(report));await writeFile(dest+"/detail_role_review.json",bytes);
 const manifest={kind:"EVENTRADAR_P30_L9F_SHA_MANIFEST_V1",
  parentL9ERun:PARENT_RUN,parentL9EArtifactId:PARENT_ARTIFACT,
  parentInputSHA256:report.pinnedParentReportSHA256,
  fileSHA256:{"detail_role_review.json":sha(bytes)},
  releaseState:REPORT_STATE,published:false};
 await writeFile(dest+"/manifest.json",stable(manifest));
 return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const a={};for(let i=2;i<process.argv.length;i+=2)a[process.argv[i]]=process.argv[i+1];
 if(!a["--source"]||!a["--out"]){process.stderr.write("HOLD_L9F_INPUT_REQUIRED\n");process.exitCode=2;}
 else{
  safeOut(a["--out"]);
  const bytes=await readFile(a["--source"]),source=JSON.parse(bytes);
  const report=await audit(source,bytes);
  await emit(report,a["--out"]);
  for(const s of report.samples)process.stdout.write("L9F_DETAIL_SAMPLE "+JSON.stringify({
   candidateId:s.candidateId,http:s.httpStatus,parity:s.titleParity,state:s.detailState,
   roleEvidence:s.roleEvidence.length,rejectedEvidence:s.rejectedEvidence.length})+"\n");
  process.stdout.write("PASS L9F_PINNED_BROWSER_DETAIL_SAMPLES "+report.additionalSampleSize+"\n");
  process.stdout.write("QUALITY L9F_TITLE_PARITY "+report.additionalTitleParity+
   " LABEL_REVIEW "+report.additionalRoleEvidenceCount+" REJECT "+report.additionalRejectedEvidenceCount+"\n");
  process.stdout.write("HOLD L9F_NO_GOLDEN_NO_WRITER_NO_RELEASE\n");
 }
}
