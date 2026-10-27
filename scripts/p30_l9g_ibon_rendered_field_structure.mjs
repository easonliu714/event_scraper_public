#!/usr/bin/env node
/** EventRadar P30-L9-G. Five SHA-pinned, already-title-verified ibon public details:
 * structural DOM diagnostics for field role parsing only. No raw HTML, cookies,
 * screenshots, network body archive, checkout, login, stealth, or production edits.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {createHash} from "node:crypto";
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";

export const KIND="EVENTRADAR_P30_L9G_IBON_RENDERED_FIELD_STRUCTURE_READONLY_V1";
export const PARENT_KIND="EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1";
export const PARENT_HEAD="d85504773108281099ec0654c5c772de243f910c";
export const PARENT_RUN=40494326021;
export const PARENT_ARTIFACT=12729277485;
export const SOURCE_IDS=Object.freeze(["39575","39878","39907","39961","39978"]);
export const HOST="ticket.ibon.com.tw";
export const HOLD="HARD_HOLD_NO_PUBLICATION";
export const MAX_PROBES=80;
const digest=b=>createHash("sha256").update(b).digest("hex");
const stable=x=>JSON.stringify(x,null,2)+"\n";
const tidy=x=>String(x??"").replace(/\s+/gu," ").trim().slice(0,180);
const DETAIL=/^https:\/\/ticket\.ibon\.com\.tw\/ActivityInfo\/Details\/([0-9]{3,8})$/;
export function canonical(url){
 const m=typeof url==="string"?DETAIL.exec(url):null;
 return m?m[1]:null;
}
export function validateParent(parent,raw){
 assert.equal(parent?.kind,PARENT_KIND,"HOLD_L9G_WRONG_SOURCE_KIND");
 assert.equal(parent.parentL9EHead,"63a079c1bee7111b1ef7b04431607d9845fe3b9f");
 assert.equal(parent.parentL9ERun,40449476633);
 assert.equal(parent.parentArtifactId,12709568132);
 assert.equal(parent.parentCandidateCount,22);
 assert.equal(parent.previousDetailTitleParity,1);
 assert.equal(parent.additionalSampleSize,5);
 assert.equal(parent.additionalTitleParity,5);
 assert.equal(parent.additionalRoleEvidenceCount,0);
 assert.equal(parent.additionalRejectedEvidenceCount,0);
 assert.equal(parent.samples?.length,5);
 assert.equal(parent.goldenAccepted,0);
 assert.equal(parent.formalFieldPromotions,0);
 assert.equal(parent.sessionSplits,0);
 assert.equal(parent.published,false);
 assert.equal(parent.writerExecuted,false);
 assert.equal(parent.schedulerExecuted,false);
 assert.equal(parent.notifierExecuted,false);
 assert.equal(parent.mergeExecuted,false);
 assert.equal(parent.releaseState,HOLD);
 assert.equal(parent.existingAndroid44Preserved,true);
 assert.equal(parent.l8CoreAndroidPassPreserved,true);
 const seen=new Set();
 for(const s of parent.samples){
  const id=canonical(s.officialUrl);
  assert.ok(id&&s.candidateId==="ibon:"+id,"HOLD_L9G_UNSAFE_DETAIL_URL");
  assert.equal(s.detailState,"DETAIL_TITLE_PARITY_PASS");
  assert.equal(s.titleParity,true);
  assert.equal(s.httpStatus,200);
  assert.ok(tidy(s.listTitle).length>=4);
  assert.equal(s.formalDate,null);
  assert.equal(s.formalPrice,null);
  assert.equal(s.ticketStatus,"UNKNOWN");
  assert.equal(s.fieldPromotions,0);
  assert.equal(s.published,false);
  assert.ok(!seen.has(id));seen.add(id);
 }
 assert.deepEqual([...seen].sort(),[...SOURCE_IDS].sort(),"HOLD_L9G_UNPINNED_SOURCE_IDS");
 return {sha256:digest(raw),rows:parent.samples.slice().sort((a,b)=>Number(canonical(a.officialUrl))-Number(canonical(b.officialUrl)))};
}
const RULES=[
 ["VOUCHER_VALIDITY",/^(?:票券有效期限|票券有效期間|兌換期限|使用期限)$/u],
 ["REGISTRATION_PERIOD",/^(?:報名期間|報名時間|登記期間|登記時間)$/u],
 ["ADMISSION_TIME",/^(?:入場時間|進場時間|開放入場)$/u],
 ["SALE_PERIOD",/^(?:售票期間|售票時間|開賣時間|預售期間|開賣日期|啟售日期)$/u],
 ["EVENT_PERIOD",/^(?:活動日期|活動時間|展演日期|演出日期|演出時間|開演時間|場次日期)$/u],
 ["VENUE",/^(?:活動場地|演出場地|活動地點|演出地點|活動場館|演出場館|場地|地點)$/u],
 ["PRICE",/^(?:票價|票價資訊|票券價格|售票價格)$/u],
 ["SESSION",/^(?:場次|場次資訊|演出場次|演出日期與場次)$/u]
];
const DATE=/(?:20\d{2}[\/.\-年]\s*\d{1,2}|\d{1,2}\/\d{1,2}|\d{1,2}:\d{2})/u;
const CURRENCY=/(?:NT\s*\$\s*[\d,]+|TWD\s*[\d,]+|[$＄]\s*[\d,]+|[\d,]+\s*(?:元|圓))/iu;
const OTHER_TIME=/(?:售票|開賣|預售|報名|登記|入場|進場|有效期限|兌換期限)/u;
export function role(label){
 const cleaned=tidy(label).replace(/[：:]\s*$/u,"");
 return RULES.find(([_,re])=>re.test(cleaned))?.[0]??null;
}
export function evaluateProbe(probe){
 if(!probe||typeof probe!=="object")return null;
 const label=tidy(probe.label).replace(/[：:]\s*$/u,""),r=role(label);
 if(!r)return null;
 const origin=String(probe.structure??"");
 const allowed=new Set(["TH_TD","DT_DD","LOCAL_SIBLING","SAME_NODE_COLON"]);
 if(!allowed.has(origin))return {role:r,label,structure:origin,quality:"HOLD_UNBOUND_DOM_STRUCTURE",promotable:false,verified:false,formalFieldPromoted:false};
 const value=tidy(probe.value);
 if(!value||value.length>120)return {role:r,label,structure:origin,quality:"REJECT_EMPTY_OR_OVERSIZE",promotable:false,verified:false,formalFieldPromoted:false};
 let quality="REVIEW_ONLY";
 if(r==="PRICE"){
  quality=CURRENCY.test(value)?"PRICE_TOKEN_REVIEW_ONLY":
   /^(?:免費|免票|自由入場)$/u.test(value)?"FREE_TEXT_REVIEW_ONLY":"REJECT_GENERIC_PRICE_TEXT";
 }else if(r==="EVENT_PERIOD"&&OTHER_TIME.test(value)){
  quality="HOLD_CROSS_ROLE_EVENT_DATE";
 }else if(["EVENT_PERIOD","ADMISSION_TIME","SALE_PERIOD","REGISTRATION_PERIOD","VOUCHER_VALIDITY"].includes(r)){
  quality=DATE.test(value)?"TIME_ROLE_REVIEW_ONLY":"REJECT_MISSING_DATE_TIME";
 }else if(r==="VENUE"){
  quality=/^(?:資訊|詳情|請洽官方|未公布|待公告|未知)$/u.test(value)?
   "REJECT_GENERIC_VENUE":"VENUE_TEXT_REVIEW_ONLY";
 }else if(r==="SESSION"){
  quality="SESSION_MULTIPLE_SHOWS_REVIEW_ONLY_NO_SPLIT";
 }
 return {role:r,label,observedValue:value,structure:origin,quality,
  sourceBound:true,verified:false,promotable:false,formalFieldPromoted:false};
}
export function reviewStructures(diag,titleParity){
 const probes=diag?.roleProbes??[];
 assert.ok(Array.isArray(probes)&&probes.length<=MAX_PROBES,"HOLD_L9G_UNBOUNDED_DOM_PROBES");
 const metrics={
  recognizedLabelNodes:Number(diag?.recognizedLabelNodes??0),
  rawProbeCount:probes.length,
  imagesNearLabels:Number(diag?.imagesNearLabels??0),
  bodyTextLength:Number(diag?.bodyTextLength??0),
  domTagCounts:diag?.domTagCounts??{}
 };
 const accepted=[],rejected=[],seen=new Set();
 if(!titleParity)return{accepted,rejected,metrics};
 for(const probe of probes){
  const row=evaluateProbe(probe);
  if(!row)continue;
  const key=[row.role,row.label,row.observedValue,row.structure].join("|");
  if(seen.has(key))continue;
  seen.add(key);
  if(row.quality.startsWith("REJECT")||row.quality.startsWith("HOLD"))rejected.push(row);
  else accepted.push(row);
  if(accepted.length+rejected.length>=30)break;
 }
 return{accepted,rejected,metrics};
}
// Browser evaluate only. Inspects local DOM adjacency; no fetch or clicks.
// Diagnostic fields are bounded public label fragments, never entire HTML/body.
function readDomStructure(){
 const trim=x=>String(x??"").replace(/\s+/g," ").trim().slice(0,180);
 const labelRE=/^(活動日期|活動時間|展演日期|演出日期|演出時間|開演時間|場次日期|入場時間|進場時間|開放入場|售票期間|售票時間|開賣時間|預售期間|開賣日期|啟售日期|報名期間|報名時間|登記期間|登記時間|票券有效期限|票券有效期間|兌換期限|使用期限|活動場地|演出場地|活動地點|演出地點|活動場館|演出場館|場地|地點|票價|票價資訊|票券價格|售票價格|場次|場次資訊|演出場次|演出日期與場次)$/u;
 const roleProbes=[],seen=new Set();
 let recognizedLabelNodes=0,imagesNearLabels=0;
 const add=(label,value,structure)=>{
  if(roleProbes.length>=80)return;
  const l=trim(label),v=trim(value);
  const key=l+"|"+v+"|"+structure;
  if(l&&v&&l!==v&&!seen.has(key)){
   seen.add(key);roleProbes.push({label:l,value:v.slice(0,120),structure});
  }
 };
 const els=[...document.querySelectorAll("th,dt,h2,h3,h4,h5,strong,b,label,span,p,li,div")].slice(0,3500);
 for(const e of els){
  if(roleProbes.length>=80)break;
  const directText=trim(e.childElementCount?Array.from(e.childNodes).filter(x=>x.nodeType===3).map(x=>x.textContent).join(" "):e.textContent);
  const own=directText.replace(/[：:]\s*$/,"");
  if(!labelRE.test(own))continue;
  recognizedLabelNodes++;
  const parent=e.parentElement;
  if(parent?.querySelector("img"))imagesNearLabels++;
  if(e.tagName==="TH"){
   const td=e.parentElement?.querySelector("td");
   if(td)add(own,td.innerText,"TH_TD");
  }else if(e.tagName==="DT"&&e.nextElementSibling?.tagName==="DD"){
   add(own,e.nextElementSibling.innerText,"DT_DD");
  }else if(e.nextElementSibling && e.nextElementSibling.parentElement===parent &&
    !e.nextElementSibling.matches("script,style,button,a,form")){
   add(own,e.nextElementSibling.innerText,"LOCAL_SIBLING");
  }
 }
 // Within a single leaf text node only, explicit label:value. No page-global search.
 for(const e of els){
  if(roleProbes.length>=80)break;
  if(e.childElementCount>0)continue;
  const t=trim(e.textContent);
  const m=/^([^:：]{2,15})\s*[:：]\s*(.{1,110})$/u.exec(t);
  if(m&&labelRE.test(m[1].trim()))add(m[1],m[2],"SAME_NODE_COLON");
 }
 const domTagCounts={};
 for(const n of ["table","tr","th","td","dl","dt","dd","strong","b","label","h1","h2","h3","h4","h5","img","iframe"])
  domTagCounts[n]=document.querySelectorAll(n).length;
 return{roleProbes,recognizedLabelNodes,imagesNearLabels,
  bodyTextLength:document.body?.innerText?.length??0,
  domTagCounts,headings:[...document.querySelectorAll("h1,h2,h3,h4")].slice(0,32).map(x=>trim(x.textContent))};
}
const canonicalTitle=x=>tidy(x).replace(/[，,。．.\-–—_·•]/gu,"").toLowerCase();
export async function run(parent,parentBytes,browser=chromium,options={}){
 const {sha256,rows}=validateParent(parent,parentBytes);
 const instance=await browser.launch({headless:true,args:["--no-sandbox"]});
 const results=[];
 try{
  const context=await instance.newContext({viewport:{width:1280,height:800},
   javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   for(const s of rows){
    const item={candidateId:s.candidateId,officialUrl:s.officialUrl,
      httpStatus:null,sourceTitleParity:false,renderState:"NOT_ATTEMPTED",
      fieldCandidates:[],fieldRejected:[],structureMetrics:null,
      fieldPromotions:0,sessionSplitCount:0,goldenVerified:false,
      formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN",published:false};
    results.push(item);
    const page=await context.newPage();
    try{
     const response=await page.goto(s.officialUrl,{waitUntil:"domcontentloaded",timeout:22000});
     item.httpStatus=response?.status()??null;
     if(new URL(page.url()).hostname!==HOST){item.renderState="HOLD_FOREIGN_ORIGIN";continue;}
     if(item.httpStatus!==200){item.renderState="HOLD_HTTP_"+item.httpStatus;continue;}
     await page.waitForTimeout(options.settleMs??1800);
     const dom=await page.evaluate(readDomStructure);
     item.sourceTitleParity=dom.headings.some(x=>canonicalTitle(x)===canonicalTitle(s.listTitle));
     item.renderState=item.sourceTitleParity?"DETAIL_TITLE_PARITY_PASS":"HOLD_TITLE_PARITY";
     const reviewed=reviewStructures(dom,item.sourceTitleParity);
     item.fieldCandidates=reviewed.accepted;
     item.fieldRejected=reviewed.rejected;
     item.structureMetrics=reviewed.metrics;
    }catch(e){item.renderState=e?.name==="TimeoutError"?"HOLD_BROWSER_TIMEOUT":"HOLD_BROWSER_RENDER_ERROR";}
    finally{await page.close();}
   }
  }finally{await context.close();}
 }finally{await instance.close();}
 const report={kind:KIND,version:"1.0.0",runId:"P30-L9G-"+new Date().toISOString().replace(/\D/g,"").slice(0,14),
  sourceOrigin:"FRESH_PUBLIC_RENDERED_DETAIL_STRUCTURE_ONLY",
  parentHead:PARENT_HEAD,parentRun:PARENT_RUN,parentArtifact:PARENT_ARTIFACT,
  parentReportSHA256:sha256,sampleCount:results.length,
  sourceTitleParityCount:results.filter(x=>x.sourceTitleParity).length,
  eligibleReviewPairs:results.reduce((n,x)=>n+x.fieldCandidates.length,0),
  rejectedOrHoldPairs:results.reduce((n,x)=>n+x.fieldRejected.length,0),
  results,fullPlatformCoverageVerified:false,productionRollbackVerified:false,
  rawHtmlPersisted:false,cookiesPersisted:false,networkBodiesPersisted:false,
  formalFieldPromotions:0,sessionSplitCount:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  releaseState:HOLD};
 validateReport(report);
 return report;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);assert.equal(r.parentHead,PARENT_HEAD);
 assert.equal(r.parentRun,PARENT_RUN);assert.equal(r.parentArtifact,PARENT_ARTIFACT);
 assert.equal(r.sampleCount,5);assert.equal(r.results.length,5);
 assert.equal(r.sourceTitleParityCount,r.results.filter(x=>x.sourceTitleParity).length);
 assert.equal(r.eligibleReviewPairs,r.results.reduce((n,x)=>n+x.fieldCandidates.length,0));
 assert.equal(r.rejectedOrHoldPairs,r.results.reduce((n,x)=>n+x.fieldRejected.length,0));
 assert.equal(r.releaseState,HOLD);
 for(const [k,v] of [["fullPlatformCoverageVerified",false],["productionRollbackVerified",false],
  ["rawHtmlPersisted",false],["cookiesPersisted",false],["networkBodiesPersisted",false],
  ["formalFieldPromotions",0],["sessionSplitCount",0],["goldenAccepted",0],
  ["published",false],["writerExecuted",false],["schedulerExecuted",false],
  ["notifierExecuted",false],["mergeExecuted",false],
  ["existingAndroid44Preserved",true],["l8CoreAndroidPassPreserved",true]])assert.equal(r[k],v,k);
 const ids=new Set();
 for(const item of r.results){
  assert.ok(canonical(item.officialUrl)&&item.candidateId==="ibon:"+canonical(item.officialUrl));
  assert.ok(SOURCE_IDS.includes(canonical(item.officialUrl)));
  assert.ok(!ids.has(item.candidateId));ids.add(item.candidateId);
  assert.equal(item.fieldPromotions,0);assert.equal(item.sessionSplitCount,0);
  assert.equal(item.goldenVerified,false);assert.equal(item.published,false);
  assert.equal(item.formalDate,null);assert.equal(item.formalPrice,null);
  assert.equal(item.ticketStatus,"UNKNOWN");
  if(!item.sourceTitleParity){assert.equal(item.fieldCandidates.length,0);assert.equal(item.fieldRejected.length,0);}
  assert.ok(item.fieldCandidates.length+item.fieldRejected.length<=30);
  for(const e of [...item.fieldCandidates,...item.fieldRejected]){
   assert.ok(RULES.some(([role])=>role===e.role));
   assert.equal(e.promotable,false);
   assert.equal(e.formalFieldPromoted,false);
   assert.equal(e.verified,false);
  }
 }
 assert.equal(ids.size,5);
 return true;
}
export function safeOut(value){
 const cwd=resolve("."),p=resolve(value);
 if(p===cwd||!p.startsWith(cwd+sep)||["docs","scripts","tests","schemas",".github",".git"].some(v=>p===resolve(v)||p.startsWith(resolve(v)+sep)))
  throw Error("HOLD_L9G_ISOLATED_OUTPUT_ONLY");
 return p;
}
export async function emit(report,out){
 validateReport(report);
 const p=safeOut(out);await mkdir(p,{recursive:true});
 const raw=Buffer.from(stable(report));await writeFile(p+"/rendered_field_structure.json",raw);
 const manifest={kind:"EVENTRADAR_P30_L9G_MANIFEST_SHA256_V1",
  parentRun:PARENT_RUN,parentArtifact:PARENT_ARTIFACT,parentSHA256:report.parentReportSHA256,
  filesSHA256:{"rendered_field_structure.json":digest(raw)},
  published:false,releaseState:HOLD};
 await writeFile(p+"/manifest.json",stable(manifest));
 return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};
 for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--source"]||!args["--out"]){console.error("HOLD_L9G_SOURCE_OUTPUT_REQUIRED");process.exitCode=2;}
 else{
  safeOut(args["--out"]);
  const raw=await readFile(args["--source"]);const parent=JSON.parse(raw);
  const report=await run(parent,raw);
  await emit(report,args["--out"]);
  for(const item of report.results)console.log("L9G_PUBLIC_DOM",JSON.stringify({
   id:item.candidateId,http:item.httpStatus,titleParity:item.sourceTitleParity,
   status:item.renderState,roleHits:item.structureMetrics?.recognizedLabelNodes??0,
   probes:item.structureMetrics?.rawProbeCount??0,
   review:item.fieldCandidates.length,rejected:item.fieldRejected.length,
   tags:item.structureMetrics?.domTagCounts??{}}));
  console.log("PASS L9G_BOUND_PUBLIC_DETAIL_DOM_FIVE",report.sampleCount);
  console.log("QUALITY L9G_TITLE",report.sourceTitleParityCount,
   "REVIEW_PAIRS",report.eligibleReviewPairs,"HOLD_PAIRS",report.rejectedOrHoldPairs);
  console.log("HOLD L9G_FORMAL_FIELDS_WRITER_PUBLISHER_NO_RELEASE");
 }
}
