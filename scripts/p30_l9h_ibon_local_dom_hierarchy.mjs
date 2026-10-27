#!/usr/bin/env node
/** EventRadar P30-L9-H: bounded structural adjacency audit near source-bound labels.
 * Source: EXACT SHA sealed L9G five same Event IDs. Ordinary Chromium only.
 * Never search page-global dates, run guessed APIs, store HTML/screenshots/cookies,
 * activate Writer/Publisher/Scheduler, or promote DATE/PRICE/TICKET fields.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {createHash} from "node:crypto";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";

export const KIND="EVENTRADAR_P30_L9H_IBON_LOCAL_DOM_HIERARCHY_READONLY_V1";
export const PARENT_KIND="EVENTRADAR_P30_L9G_IBON_RENDERED_FIELD_STRUCTURE_READONLY_V1";
export const PARENT_HEAD="07cc3ce1743a56d2bc60213d345f27672cef97d5";
export const PARENT_RUN=40511115223;
export const PARENT_ARTIFACT=12738140163;
export const TITLE_PARENT_RUN=40494326021;
export const TITLE_PARENT_ARTIFACT=12729277485;
export const TITLE_PARENT_KIND="EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1";
export const IDS=Object.freeze(["39575","39878","39907","39961","39978"]);
export const HOLD="HARD_HOLD_NO_PUBLICATION";
const ROOT="https://ticket.ibon.com.tw/ActivityInfo/Details/";
const MATCH=/^https:\/\/ticket\.ibon\.com\.tw\/ActivityInfo\/Details\/([0-9]{3,8})$/;
const digest=raw=>createHash("sha256").update(raw).digest("hex");
const stable=x=>JSON.stringify(x,null,2)+"\n";
const short=s=>String(s??"").replace(/\s+/gu," ").trim().slice(0,160);
const title=s=>short(s).replace(/[，,。．.\-–—_·•]/gu,"").toLowerCase();
const DATE=/(?:20\d{2}[\/.\-年]\s*\d{1,2}|\d{1,2}\/\d{1,2}|\d{1,2}:\d{2})/u;
const PRICE=/(?:NT\s*\$\s*[\d,]+|TWD\s*[\d,]+|[$＄]\s*[\d,]+|[\d,]+\s*(?:元|圓))/iu;
const ROLE_TEXT=/(?:活動日期|活動時間|演出日期|演出時間|開演時間|入場時間|進場時間|售票期間|售票時間|開賣時間|預售期間|報名期間|報名時間|登記期間|票券有效期限|兌換期限|活動場地|演出地點|票價|場次)/gu;
export const LABEL_ROLES=Object.freeze({
 "活動日期":"EVENT_PERIOD","活動時間":"EVENT_PERIOD","演出日期":"EVENT_PERIOD",
 "演出時間":"EVENT_PERIOD","開演時間":"EVENT_PERIOD","場次日期":"EVENT_PERIOD",
 "入場時間":"ADMISSION_TIME","進場時間":"ADMISSION_TIME",
 "售票期間":"SALE_PERIOD","售票時間":"SALE_PERIOD","開賣時間":"SALE_PERIOD",
 "預售期間":"SALE_PERIOD","報名期間":"REGISTRATION_PERIOD","報名時間":"REGISTRATION_PERIOD",
 "登記期間":"REGISTRATION_PERIOD","票券有效期限":"VOUCHER_VALIDITY","兌換期限":"VOUCHER_VALIDITY",
 "活動場地":"VENUE","演出地點":"VENUE","活動地點":"VENUE",
 "票價":"PRICE","票價資訊":"PRICE","場次":"SESSION","演出場次":"SESSION"
});
export const RELATIONS=Object.freeze([
 "LABEL_NEXT_ELEMENT","LABEL_PARENT_NEXT_ELEMENT","SAME_PARENT_TEXT_AFTER_LABEL"
]);
export function parentProof(p,raw,titleSource,titleRaw){
 assert.deepEqual(JSON.parse(raw),p,"HOLD_L9H_UNSEALED_STRUCTURE_INPUT");
 assert.equal(p?.kind,PARENT_KIND,"HOLD_L9H_PARENT_KIND");
 assert.equal(p.parentHead,"d85504773108281099ec0654c5c772de243f910c");
 assert.equal(p.parentRun,40494326021);
 assert.equal(p.parentArtifact,12729277485);
 assert.equal(p.sourceOrigin,"FRESH_PUBLIC_RENDERED_DETAIL_STRUCTURE_ONLY");
 assert.equal(p.sampleCount,5);assert.equal(p.results?.length,5);
 assert.equal(p.sourceTitleParityCount,5);assert.equal(p.eligibleReviewPairs,0);
 assert.equal(p.rejectedOrHoldPairs,5);
 assert.equal(p.formalFieldPromotions,0);assert.equal(p.goldenAccepted,0);
 assert.equal(p.published,false);assert.equal(p.writerExecuted,false);
 assert.equal(p.schedulerExecuted,false);assert.equal(p.notifierExecuted,false);
 assert.equal(p.mergeExecuted,false);assert.equal(p.releaseState,HOLD);
 assert.equal(p.existingAndroid44Preserved,true);
 assert.equal(p.l8CoreAndroidPassPreserved,true);
 const found=new Set();
 for(const item of p.results){
  const id=MATCH.exec(item.officialUrl)?.[1];
  assert.ok(id&&item.candidateId==="ibon:"+id,"HOLD_L9H_SOURCE_IDENTITY");
  assert.ok(IDS.includes(id));assert.ok(!found.has(id));found.add(id);
  assert.equal(item.httpStatus,200);assert.equal(item.sourceTitleParity,true);
  assert.equal(item.renderState,"DETAIL_TITLE_PARITY_PASS");
  assert.equal(item.fieldCandidates.length,0);
  assert.equal(item.fieldRejected.length,1);
  assert.equal(item.fieldRejected[0].role,"EVENT_PERIOD");
  assert.equal(item.fieldRejected[0].quality,"REJECT_MISSING_DATE_TIME");
  assert.equal(item.fieldRejected[0].structure,"LOCAL_SIBLING");
  assert.equal(item.formalDate,null);assert.equal(item.formalPrice,null);
  assert.equal(item.ticketStatus,"UNKNOWN");assert.equal(item.published,false);
 }
 assert.equal(found.size,5);
 assert.equal(titleSource?.kind,TITLE_PARENT_KIND,"HOLD_L9H_TITLE_SOURCE_KIND");
 assert.deepEqual(JSON.parse(titleRaw),titleSource,"HOLD_L9H_UNSEALED_TITLE_INPUT");
 assert.equal(titleSource.parentL9ERun,40449476633);
 assert.equal(titleSource.parentArtifactId,12709568132);
 assert.equal(titleSource.parentCandidateCount,22);
 assert.equal(titleSource.additionalSampleSize,5);
 assert.equal(titleSource.additionalTitleParity,5);
 assert.equal(titleSource.samples?.length,5);
 assert.equal(titleSource.formalFieldPromotions,0);
 assert.equal(titleSource.goldenAccepted,0);
 assert.equal(titleSource.published,false);
 assert.equal(titleSource.releaseState,HOLD);
 const byId=new Map();
 for(const row of titleSource.samples){
  const id=MATCH.exec(row.officialUrl)?.[1];
  assert.ok(id&&IDS.includes(id)&&row.candidateId==="ibon:"+id);
  assert.equal(row.titleParity,true);
  assert.equal(row.httpStatus,200);
  assert.ok(short(row.listTitle).length>=4);
  assert.ok(!byId.has(id),"HOLD_L9H_DUPLICATE_TITLE_SOURCE_ID");
  byId.set(id,row);
 }
 assert.equal(byId.size,5);
 return {sha256:digest(raw),titleSHA256:digest(titleRaw),
  sources:p.results.slice()
   .sort((a,b)=>Number(MATCH.exec(a.officialUrl)[1])-Number(MATCH.exec(b.officialUrl)[1]))
   .map(x=>{
    const id=MATCH.exec(x.officialUrl)[1],titleRow=byId.get(id);
    assert.ok(titleRow&&titleRow.officialUrl===x.officialUrl,
      "HOLD_L9H_CROSS_ARTIFACT_URL_IDENTITY");
    return {...x,listTitle:titleRow.listTitle};
   })};
}
function typedRole(label){return LABEL_ROLES[short(label).replace(/[：:]\s*$/u,"")]??null;}
export function reviewNeighbor(neighbor,labelRole){
 const base={relation:neighbor?.relation??null,role:labelRole,
  bindingState:"HOLD",quality:"HOLD_UNBOUND_STRUCTURE",
  verified:false,formalFieldPromoted:false,promotable:false};
 if(!neighbor||!RELATIONS.includes(neighbor.relation)||
    !Number.isInteger(neighbor.distance)||neighbor.distance!==1||
    typeof neighbor.value!=="string")return base;
 const value=short(neighbor.value);
 if(!value)return {...base,quality:"REJECT_EMPTY_VALUE"};
 if(neighbor.interactive===true)return {...base,quality:"HOLD_INTERACTIVE_NEIGHBOR"};
 if(!Number.isInteger(neighbor.otherRoleCount)||neighbor.otherRoleCount!==0)
  return {...base,quality:"HOLD_MULTIPLE_ROLE_LABELS_IN_SECTION"};
 if(value.length>120)return {...base,quality:"REJECT_OVERSIZE_BOUND_VALUE"};
 if(labelRole==="EVENT_PERIOD"){
  if(/(?:售票|開賣|預售|入場|進場|報名|登記|票券有效|兌換期限)/u.test(value))
   return {...base,quality:"HOLD_ROLE_CONFLICT_EVENT_DATE"};
  if(!DATE.test(value))return {...base,quality:"REJECT_NO_DATE_TIME_TOKEN"};
  return {...base,bindingState:"LOCAL_BOUND_REVIEW_ONLY",quality:"EVENT_DATE_TOKEN_REVIEW_ONLY",observedValue:value};
 }
 if(labelRole==="PRICE"){
  if(/^(?:資訊|詳情|查詢|未公布|待公告|未知)$/u.test(value))
   return {...base,quality:"REJECT_GENERIC_PRICE"};
  if(!PRICE.test(value))return {...base,quality:"REJECT_NOT_PRICE_TOKEN"};
  return {...base,bindingState:"LOCAL_BOUND_REVIEW_ONLY",quality:"PRICE_TOKEN_REVIEW_ONLY",observedValue:value};
 }
 if(["ADMISSION_TIME","SALE_PERIOD","REGISTRATION_PERIOD","VOUCHER_VALIDITY"].includes(labelRole)){
  if(!DATE.test(value))return {...base,quality:"REJECT_NO_DATE_TIME_TOKEN"};
  return {...base,bindingState:"LOCAL_BOUND_REVIEW_ONLY",quality:labelRole+"_TOKEN_REVIEW_ONLY",observedValue:value};
 }
 if(labelRole==="VENUE"){
  if(/^(?:資訊|詳情|未知|待公告)$/u.test(value))return {...base,quality:"REJECT_GENERIC_VENUE"};
  return {...base,bindingState:"LOCAL_BOUND_REVIEW_ONLY",quality:"VENUE_TEXT_REVIEW_ONLY",observedValue:value};
 }
 if(labelRole==="SESSION")return {...base,bindingState:"LOCAL_BOUND_REVIEW_ONLY",
  quality:"SESSION_EVIDENCE_REVIEW_ONLY_NO_SPLIT",observedValue:value};
 return base;
}
export function assessStructure(dom,matched){
 const contexts=dom?.labelContexts??[];
 assert.ok(Array.isArray(contexts)&&contexts.length<=16,"HOLD_L9H_CONTEXT_BOUND");
 const out={labelCount:contexts.length,structures:[],reviewPairs:[],rejections:[],
  imageNearLabels:0,domCounts:dom?.tagCounts??{},noPromotion:true};
 if(!matched)return out;
 const seen=new Set();
 for(const c of contexts){
  const role=typedRole(c.label);
  if(!role)continue;
  assert.ok(Array.isArray(c.neighbors)&&c.neighbors.length<=3,"HOLD_L9H_NEIGHBOR_BOUND");
  const structure={label:short(c.label),role,tag:short(c.tag),
    parentTag:short(c.parentTag),grandparentTag:short(c.grandparentTag),
    parentChildCount:Number(c.parentChildCount)||0,
    imageCount:Number(c.imageCount)||0,
    directTextLength:Number(c.directTextLength)||0,
    neighborRelations:c.neighbors.map(x=>x.relation)};
  out.structures.push(structure);
  out.imageNearLabels+=structure.imageCount;
  for(const n of c.neighbors){
   const evidence=reviewNeighbor(n,role);
   const signature=[role,short(c.label),n.relation,evidence.quality,evidence.observedValue].join("|");
   if(seen.has(signature))continue;seen.add(signature);
   const row={label:short(c.label),role,relation:n.relation,quality:evidence.quality,
    bindingState:evidence.bindingState,observedValue:evidence.observedValue??null,
    verified:false,formalFieldPromoted:false,promotable:false};
   if(evidence.bindingState==="LOCAL_BOUND_REVIEW_ONLY")out.reviewPairs.push(row);
   else out.rejections.push(row);
  }
 }
 return out;
}
// Evaluated only in public DOM, without page-global date search or script/network API.
function inspectLocalDom(){
 const clip=x=>String(x??"").replace(/\s+/g," ").trim().slice(0,160);
 const labels=new Set([
 "活動日期","活動時間","演出日期","演出時間","開演時間","場次日期",
 "入場時間","進場時間","售票期間","售票時間","開賣時間","預售期間",
 "報名期間","報名時間","登記期間","票券有效期限","兌換期限",
 "活動場地","演出地點","活動地點","票價","票價資訊","場次","演出場次"
 ]);
 const contexts=[],seen=new Set(),nodes=[...document.querySelectorAll("strong,b,span,small,p,li,label,dt,th,h3,h4,div")].slice(0,4500);
 const tag=e=>e?.tagName?.toLowerCase()||"none";
 const direct=e=>clip([...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(" "));
 const roleTokens=/(活動日期|活動時間|演出日期|演出時間|開演時間|入場時間|進場時間|售票期間|售票時間|開賣時間|預售期間|報名期間|報名時間|登記期間|票券有效期限|兌換期限|活動場地|演出地點|活動地點|票價|場次)/g;
 const skip=e=>!e||e.matches("script,style,form,button,a,input,select,textarea")||!!e.closest("form");
 const push=(list,relation,e)=>{
  if(skip(e)||list.length>=3)return;
  const value=clip(e.innerText||e.textContent);
  if(!value)return;
  const roleHits=[...value.matchAll(roleTokens)].map(x=>x[1]);
  list.push({relation,distance:1,value:value.slice(0,120),otherRoleCount:roleHits.length,
    interactive:!!e.querySelector("input,button,select,form")});
 };
 for(const e of nodes){
  if(contexts.length>=16)break;
  const name=(e.childElementCount?direct(e):clip(e.textContent)).replace(/[：:]\s*$/,"");
  if(!labels.has(name)||seen.has(e))continue;
  seen.add(e);
  const p=e.parentElement,g=p?.parentElement,neighbors=[];
  if(e.nextElementSibling?.parentElement===p)push(neighbors,"LABEL_NEXT_ELEMENT",e.nextElementSibling);
  if(p&&g&&p.children.length<=5&&p.nextElementSibling?.parentElement===g &&
     clip(p.textContent).replace(/[：:]\s*$/,"")===name)
   push(neighbors,"LABEL_PARENT_NEXT_ELEMENT",p.nextElementSibling);
  // Direct parent text segment only if it begins with label and a separator.
  // No global body text or ancestor text.
  if(p&&p.childElementCount<=5&&p.textContent.length<=170){
   const rest=direct(p).replace(/^[\s:：]+/,"");
   if(rest&&rest!==name){
    neighbors.push({relation:"SAME_PARENT_TEXT_AFTER_LABEL",distance:1,
      value:rest.slice(0,120),otherRoleCount:[...rest.matchAll(roleTokens)].length,
      interactive:!!p.querySelector("input,button,select,form")});
   }
  }
  contexts.push({label:name,tag:tag(e),parentTag:tag(p),grandparentTag:tag(g),
    parentChildCount:p?.children.length??0,directTextLength:direct(p||e).length,
    imageCount:p?.querySelectorAll("img").length??0,neighbors:neighbors.slice(0,3)});
 }
 const tagCounts={};
 for(const n of ["strong","b","span","label","table","tr","th","td","dt","dd","img","iframe"])
  tagCounts[n]=document.querySelectorAll(n).length;
 return {headings:[...document.querySelectorAll("h1,h2,h3,h4")].slice(0,30).map(e=>clip(e.textContent)),
  labelContexts:contexts,tagCounts};
}
const normTitle=x=>short(x).replace(/[，,。．.\-–—_·•]/gu,"").toLowerCase();
export async function audit(parent,raw,titleSource,titleRaw,browser=chromium,opts={}){
 const source=parentProof(parent,raw,titleSource,titleRaw);
 const driver=await browser.launch({headless:true,args:["--no-sandbox"]});
 const results=[];
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},javaScriptEnabled:true,
    acceptDownloads:false,permissions:[]});
  try{
   for(const s of source.sources){
    const entry={candidateId:s.candidateId,officialUrl:s.officialUrl,
      titleParity:false,httpStatus:null,status:"NOT_ATTEMPTED",labelCount:0,
      structures:[],reviewPairs:[],rejections:[],imageNearLabels:0,domCounts:{},
      formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN",
      goldenVerified:false,published:false};
    results.push(entry);
    const page=await ctx.newPage();
    try{
     const res=await page.goto(s.officialUrl,{waitUntil:"domcontentloaded",timeout:22000});
     entry.httpStatus=res?.status()??null;
     if(new URL(page.url()).hostname!=="ticket.ibon.com.tw"){
      entry.status="HOLD_FOREIGN_REDIRECT";continue;
     }
     if(entry.httpStatus!==200){entry.status="HOLD_HTTP_"+entry.httpStatus;continue;}
     await page.waitForTimeout(opts.settleMs??1600);
     const dom=await page.evaluate(inspectLocalDom);
     entry.titleParity=dom.headings.some(x=>normTitle(x)===normTitle(s.listTitle));
     entry.status=entry.titleParity?"TITLE_PARITY_PASS":"HOLD_TITLE_MISMATCH";
     const out=assessStructure(dom,entry.titleParity);
     Object.assign(entry,{labelCount:out.labelCount,structures:out.structures,
       reviewPairs:out.reviewPairs,rejections:out.rejections,
       imageNearLabels:out.imageNearLabels,domCounts:out.domCounts});
    }catch(e){entry.status=e?.name==="TimeoutError"?"HOLD_BROWSER_TIMEOUT":"HOLD_BROWSER_ERROR";}
    finally{await page.close();}
   }
  }finally{await ctx.close();}
 }finally{await driver.close();}
 const output={kind:KIND,sourceOrigin:"L9H_NEW_NORMAL_PUBLIC_DETAIL_DOM_HIERARCHY",
  parentHead:PARENT_HEAD,parentRun:PARENT_RUN,parentArtifactId:PARENT_ARTIFACT,
  sourceReportSHA256:source.sha256,titleSourceSHA256:source.titleSHA256,
  titleSourceRun:TITLE_PARENT_RUN,titleSourceArtifact:TITLE_PARENT_ARTIFACT,sourceEventIds:IDS.slice(),
  sampleCount:5,titleParityCount:results.filter(x=>x.titleParity).length,
  localLabels:results.reduce((n,x)=>n+x.labelCount,0),
  locallyBoundReviewPairs:results.reduce((n,x)=>n+x.reviewPairs.length,0),
  rejectedOrHoldPairs:results.reduce((n,x)=>n+x.rejections.length,0),
  imagesNearLabels:results.reduce((n,x)=>n+x.imageNearLabels,0),
  rows:results,rawHtmlPersisted:false,screenshotsPersisted:false,
  cookiesPersisted:false,networkBodiesPersisted:false,
  formalFieldPromotions:0,sessionSplits:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,
  notifierExecuted:false,mergeExecuted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  fullPlatformCoverageVerified:false,productionRollbackVerified:false,
  releaseState:HOLD};
 validateReport(output);
 return output;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);assert.equal(r.parentHead,PARENT_HEAD);
 assert.equal(r.parentRun,PARENT_RUN);assert.equal(r.parentArtifactId,PARENT_ARTIFACT);
 assert.equal(r.titleSourceRun,TITLE_PARENT_RUN);assert.equal(r.titleSourceArtifact,TITLE_PARENT_ARTIFACT);
 assert.deepEqual(r.sourceEventIds,IDS);
 assert.equal(r.sampleCount,5);assert.equal(r.rows.length,5);
 assert.equal(r.titleParityCount,r.rows.filter(x=>x.titleParity).length);
 assert.equal(r.localLabels,r.rows.reduce((n,x)=>n+x.labelCount,0));
 assert.equal(r.locallyBoundReviewPairs,r.rows.reduce((n,x)=>n+x.reviewPairs.length,0));
 assert.equal(r.rejectedOrHoldPairs,r.rows.reduce((n,x)=>n+x.rejections.length,0));
 const exact=new Set();
 for(const row of r.rows){
  const id=MATCH.exec(row.officialUrl)?.[1];
  assert.ok(id&&row.candidateId==="ibon:"+id);assert.ok(IDS.includes(id));
  assert.ok(!exact.has(id));exact.add(id);
  assert.equal(row.formalDate,null);assert.equal(row.formalPrice,null);
  assert.equal(row.ticketStatus,"UNKNOWN");assert.equal(row.goldenVerified,false);
  assert.equal(row.published,false);
  if(!row.titleParity){
   assert.equal(row.reviewPairs.length,0);assert.equal(row.rejections.length,0);
  }
  assert.ok(row.structures.length<=16);
  for(const e of [...row.reviewPairs,...row.rejections]){
   assert.equal(e.verified,false);assert.equal(e.formalFieldPromoted,false);
   assert.equal(e.promotable,false);
   assert.ok(LABEL_ROLES[short(e.label)]===e.role);
   assert.ok(RELATIONS.includes(e.relation));
  }
 }
 assert.equal(exact.size,5);
 for(const [key,expected] of Object.entries({
  rawHtmlPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  networkBodiesPersisted:false,formalFieldPromotions:0,sessionSplits:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  fullPlatformCoverageVerified:false,productionRollbackVerified:false,releaseState:HOLD
 }))assert.equal(r[key],expected,key);
 return true;
}
export function safeOut(output){
 const cwd=resolve("."),p=resolve(output);
 if(p===cwd||!p.startsWith(cwd+sep)||["docs","scripts","tests","schemas",".git",".github"].some(x=>p===resolve(x)||p.startsWith(resolve(x)+sep)))
  throw Error("HOLD_L9H_ISOLATED_OUTPUT_ONLY");
 return p;
}
export async function emit(report,out){
 validateReport(report);
 const dir=safeOut(out);await mkdir(dir,{recursive:true});
 const buf=Buffer.from(stable(report));
 await writeFile(dir+"/ibon_local_dom_hierarchy.json",buf);
 const manifest={kind:"EVENTRADAR_P30_L9H_SHA256_MANIFEST_V1",
  parentRun:PARENT_RUN,parentArtifact:PARENT_ARTIFACT,
  parentInputSHA256:report.sourceReportSHA256,
  titleSourceRun:TITLE_PARENT_RUN,titleSourceArtifact:TITLE_PARENT_ARTIFACT,
  titleInputSHA256:report.titleSourceSHA256,
  filesSHA256:{"ibon_local_dom_hierarchy.json":digest(buf)},
  releaseState:HOLD,published:false};
 await writeFile(dir+"/manifest.json",stable(manifest));
 return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--source"]||!args["--title-source"]||!args["--out"]){console.error("HOLD_L9H_SOURCE_AND_OUTPUT_REQUIRED");process.exitCode=2;}
 else{
  safeOut(args["--out"]);
  const raw=await readFile(args["--source"]);
  const titleRaw=await readFile(args["--title-source"]);
  const report=await audit(JSON.parse(raw),raw,JSON.parse(titleRaw),titleRaw);
  await emit(report,args["--out"]);
  for(const row of report.rows)console.log("L9H_BOUND_FIELD_STRUCTURE",JSON.stringify({
   id:row.candidateId,http:row.httpStatus,title:row.titleParity,
   status:row.status,labels:row.labelCount,
   relations:row.structures.map(x=>({role:x.role,tag:x.tag,parent:x.parentTag,
     relations:x.neighborRelations,images:x.imageCount})),
   review:row.reviewPairs.map(x=>({role:x.role,quality:x.quality,relation:x.relation})),
   rejected:row.rejections.map(x=>({role:x.role,quality:x.quality,relation:x.relation}))}));
  console.log("PASS L9H_PINNED_PUBLIC_DOM_FIVE",report.sampleCount);
  console.log("QUALITY L9H_LOCAL_BINDINGS",report.locallyBoundReviewPairs,
    "REJECTED",report.rejectedOrHoldPairs,"IMAGES",report.imagesNearLabels);
  console.log("HOLD L9H_FORMAL_FIELD_GOLDEN_WRITER_RELEASE");
 }
}
