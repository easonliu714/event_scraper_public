#!/usr/bin/env node
/* P30-L9-M, bounded official ibon local section topology diagnostics.
 * Double-pin L9F original titles and L9L four-detail results. No writes/publication,
 * no raw HTML/screenshots/cookies or whole-page time extraction.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";
export const KIND="EVENTRADAR_P30_L9M_IBON_NEIGHBOR_REASON_DIAGNOSTICS_V1";
export const IDS=["39575","39878","39907","39978"];
export const HEAD="627a8175b1095c42d878219d95935357457d35e5";
export const L9L_RUN=40681114004, L9L_ART=12812317856;
export const L9F_RUN=40494326021, L9F_ART=12729277485;
export const HOLD="HARD_HOLD_NO_PUBLICATION";
const BASE="https://ticket.ibon.com.tw/ActivityInfo/Details/";
const sha=b=>createHash("sha256").update(b).digest("hex");
const json=o=>JSON.stringify(o,null,2)+"\n";
const clip=s=>String(s??"").replace(/\s+/gu," ").trim().slice(0,130);
const norm=s=>clip(s).replace(/[，,。．.\-–—_·•]/gu,"").toLowerCase();
export const roles=Object.freeze({
 "活動日期":"EVENT_PERIOD","演出日期":"EVENT_PERIOD","活動時間":"EVENT_PERIOD",
 "演出時間":"EVENT_PERIOD","開演時間":"EVENT_PERIOD",
 "售票時間":"SALE_PERIOD","售票期間":"SALE_PERIOD","開賣時間":"SALE_PERIOD",
 "入場時間":"ADMISSION_TIME","進場時間":"ADMISSION_TIME",
 "報名期間":"REGISTRATION_PERIOD","登記期間":"REGISTRATION_PERIOD",
 "票券有效期限":"VOUCHER_VALIDITY","兌換期限":"VOUCHER_VALIDITY",
 "演出地點":"VENUE","活動地點":"VENUE","場地":"VENUE",
 "票價":"PRICE","票券價格":"PRICE","場次":"SESSION"
});
const datePattern=/(?:20\d{2}[\/.\-年]\s*\d{1,2}|\d{1,2}\/\d{1,2}|\d{1,2}:\d{2})/u;
const moneyPattern=/(?:NT\s*\$|TWD\s*|[$＄])\s*[\d,]+|[\d,]+\s*(?:元|圓)/iu;
export function parents(l,lbytes,f,fbytes){
 assert.deepEqual(JSON.parse(lbytes),l);
 assert.deepEqual(JSON.parse(fbytes),f);
 assert.equal(l?.kind,"EVENTRADAR_P30_L9L_FOUR_IBON_DETAIL_SEMANTIC_REVIEW_V1");
 assert.equal(l.sampleCount,4);assert.equal(l.titleParityCount,4);
 assert.equal(l.reviewPairCount,0);assert.equal(l.rejectedPairCount,4);
 assert.equal(l.formalFieldPromotions,0);assert.equal(l.goldenAccepted,0);
 assert.equal(l.published,false);assert.equal(l.releaseState,HOLD);
 assert.equal(f?.kind,"EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1");
 assert.equal(f.additionalSampleSize,5);assert.equal(f.additionalTitleParity,5);
 assert.equal(f.formalFieldPromotions,0);assert.equal(f.goldenAccepted,0);
 assert.equal(f.published,false);assert.equal(f.releaseState,HOLD);
 const originals=IDS.map(id=>{
  const a=l.results.filter(r=>r.id===id),b=f.samples.filter(r=>r.candidateId==="ibon:"+id);
  assert.equal(a.length,1);assert.equal(b.length,1);
  assert.equal(a[0].url,BASE+id);assert.equal(b[0].officialUrl,BASE+id);
  assert.equal(a[0].titleParity,true);assert.equal(a[0].http,200);
  assert.equal(a[0].accepted.length,0);assert.equal(a[0].rejected.length,1);
  assert.equal(b[0].titleParity,true);assert.ok(norm(b[0].listTitle).length>=4);
  return{id,url:BASE+id,title:b[0].listTitle};
 });
 return {l9lSha:sha(lbytes),l9fSha:sha(fbytes),originals};
}
export function verdict(label,probe){
 const role=roles[clip(label).replace(/[：:]$/u,"")];
 if(!role)return{reason:"UNKNOWN_LABEL",role:null,reviewable:false};
 const base={role,reason:"HOLD_UNBOUND_LOCAL_SECTION",reviewable:false,
  fieldPromotion:false,verified:false};
 if(!probe||typeof probe!=="object")return{...base,reason:"NO_LOCAL_NEIGHBOR"};
 if(probe.hops!==1)return{...base,reason:"TOO_DISTANT"};
 if(!["NEXT_SIBLING","PARENT_NEXT","DIRECT_PARENT_TEXT","SAME_LOCAL_SECTION"].includes(probe.relation))
  return{...base,reason:"UNAPPROVED_RELATION"};
 if(probe.interactive||probe.otherRoleCount>0)return{...base,reason:"AMBIGUOUS_OR_INTERACTIVE"};
 if(probe.imageOnly)return{...base,reason:"IMAGE_ONLY_NOT_TEXT"};
 const value=clip(probe.value);
 if(!value)return{...base,reason:probe.descendants>0?"NESTED_CHILDREN_VALUE_NOT_BOUND":"EMPTY_VALUE"};
 if(value.length>=120)return{...base,reason:"VALUE_TOO_LONG"};
 if(role==="EVENT_PERIOD"&&/(?:售票|開賣|入場|報名|登記|有效期限)/u.test(value))
  return{...base,reason:"CROSS_ROLE_DATE"};
 if(["EVENT_PERIOD","SALE_PERIOD","ADMISSION_TIME","REGISTRATION_PERIOD","VOUCHER_VALIDITY"].includes(role)&&!datePattern.test(value))
  return{...base,reason:"NO_TIME_TOKEN"};
 if(role==="PRICE"&&!moneyPattern.test(value))return{...base,reason:"GENERIC_NON_PRICE"};
 if(role==="VENUE"&&/^(?:資訊|詳情|未知|待公告)$/u.test(value))
  return{...base,reason:"GENERIC_VENUE"};
 return{...base,reason:"SOURCE_BOUND_REVIEW_ONLY",reviewable:true,value};
}
export function inspect(d,parity){
 const contexts=d?.contexts??[];
 assert.ok(Array.isArray(contexts)&&contexts.length<=16,"HOLD_CONTEXT_BOMB");
 const diagnostics=[],reasonCounts={};
 if(!parity)return {diagnostics,reasonCounts,labelsVisible:contexts.length,accepted:0};
 for(const ctx of contexts){
  assert.ok(Array.isArray(ctx.probes)&&ctx.probes.length<=6,"HOLD_PROBE_BOMB");
  const typed=roles[clip(ctx.label).replace(/[：:]$/u,"")];
  if(!typed)continue;
  const candidates=ctx.probes.length?ctx.probes:[null];
  for(const p of candidates){
   const v=verdict(ctx.label,p);
   reasonCounts[v.reason]=(reasonCounts[v.reason]||0)+1;
   diagnostics.push({label:clip(ctx.label),role:typed,
    labelTag:clip(ctx.tag),parentTag:clip(ctx.parentTag),
    parentChildCount:Math.min(99,Number(ctx.parentChildCount)||0),
    childCount:Math.min(99,Number(ctx.childCount)||0),
    imageNearLabel:Math.min(99,Number(ctx.imageNearLabel)||0),
    relation:p?.relation??"NONE",reason:v.reason,
    reviewable:v.reviewable,reviewValue:v.reviewable?v.value:null,
    fieldPromotion:false,verified:false});
   if(diagnostics.length>=32)break;
  }
  if(diagnostics.length>=32)break;
 }
 return{diagnostics,reasonCounts,labelsVisible:contexts.length,
  accepted:diagnostics.filter(x=>x.reviewable).length};
}
function readLocalDom(){
 const c=s=>String(s??"").replace(/\s+/g," ").trim().slice(0,130);
 const labels=new Set(["活動日期","演出日期","活動時間","演出時間","開演時間","售票時間",
 "售票期間","開賣時間","入場時間","進場時間","報名期間","登記期間",
 "票券有效期限","兌換期限","演出地點","活動地點","場地","票價","票券價格","場次"]);
 const contexts=[],nodes=[...document.querySelectorAll("strong,b,h2,h3,h4,span,dt,th,label,p,li")].slice(0,2800);
 for(const el of nodes){
  if(contexts.length>=16)break;
  const label=c(el.childElementCount?Array.from(el.childNodes).filter(n=>n.nodeType===3).map(n=>n.textContent).join(" "):el.textContent).replace(/[：:]$/,"");
  if(!labels.has(label))continue;
  const parent=el.parentElement, grand=parent?.parentElement;
  const ctx={label,tag:el.tagName,parentTag:parent?.tagName??"NONE",
   parentChildCount:parent?.childElementCount||0,childCount:el.childElementCount,
   imageNearLabel:parent?.querySelectorAll("img").length||0,probes:[]};
  const add=(elem,relation)=>{
   if(!elem||ctx.probes.length>=6||elem.matches("script,style,form,button,a,input"))return;
   const raw=c(elem.textContent);
   const direct=c([...elem.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(" "));
   const txt=direct||((elem.childElementCount===0)?raw:"");
   const roleHits=(raw.match(/活動日期|演出日期|售票期間|售票時間|入場時間|報名期間|票價|場次/g)||[]).length;
   ctx.probes.push({relation,hops:1,value:txt,descendants:elem.childElementCount,
    otherRoleCount:roleHits,interactive:!!elem.querySelector("button,a,input,form"),
    imageOnly:!!elem.querySelector("img")&&!txt});
  };
  add(el.nextElementSibling,"NEXT_SIBLING");
  if(parent?.childElementCount===1&&grand)add(parent.nextElementSibling,"PARENT_NEXT");
  if(parent&&parent.childElementCount<=4){
   const direct=c([...parent.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(" "));
   if(direct&&direct!==label)ctx.probes.push({relation:"DIRECT_PARENT_TEXT",hops:1,
    value:direct,descendants:0,otherRoleCount:0,interactive:false,imageOnly:false});
  }
  const section=el.closest("section,article,[class*='detail'],[class*='info']");
  if(section&&section!==parent&&section.childElementCount<=4){
   const local=section.children.length===2?section.children[1]:null;
   if(local&&local!==el&&local!==parent)add(local,"SAME_LOCAL_SECTION");
  }
  contexts.push(ctx);
 }
 return{headings:[...document.querySelectorAll("h1,h2,h3,h4")].slice(0,30).map(e=>c(e.textContent)),
 contexts,anchorCount:document.querySelectorAll("a").length};
}
export async function audit(l,lb,f,fb,browser=chromium,opts={}){
 const proof=parents(l,lb,f,fb);
 const driver=await browser.launch({headless:true,args:["--no-sandbox"]});
 const result=[];
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},javaScriptEnabled:true,
   acceptDownloads:false,permissions:[]});
  try{
   for(const source of proof.originals){
    const row={id:source.id,url:source.url,http:null,state:"NOT_VISITED",
      titleParity:false,labelsVisible:0,reasonCounts:{},diagnostics:[],
      reviewCandidateCount:0,formalDate:null,formalPrice:null,ticketStatus:"UNKNOWN",
      published:false,goldenVerified:false};
    result.push(row);
    const page=await ctx.newPage();
    try{
     const response=await page.goto(source.url,{waitUntil:"domcontentloaded",timeout:22000});
     row.http=response?.status()??null;
     if(page.url()!==source.url){row.state="HOLD_REDIRECT";continue;}
     if(row.http!==200){row.state="HOLD_HTTP";continue;}
     await page.waitForTimeout(opts.settleMs??1500);
     const dom=await page.evaluate(readLocalDom);
     row.titleParity=dom.headings.some(x=>norm(x)===norm(source.title));
     row.state=row.titleParity?"TITLE_SOURCE_PARITY_REVIEW_ONLY":"HOLD_TITLE_DRIFT";
     const diag=inspect(dom,row.titleParity);
     Object.assign(row,{labelsVisible:diag.labelsVisible,reasonCounts:diag.reasonCounts,
      diagnostics:diag.diagnostics,reviewCandidateCount:diag.accepted});
    }catch(e){row.state=e?.name==="TimeoutError"?"HOLD_TIMEOUT":"HOLD_RENDER";}
    finally{await page.close();}
   }
  }finally{await ctx.close();}
 }finally{await driver.close();}
 const r={kind:KIND,parentL9LHead:HEAD,parentL9LRun:L9L_RUN,
  parentL9LArtifact:L9L_ART,parentL9FRun:L9F_RUN,parentL9FArtifact:L9F_ART,
  parentL9LSHA256:proof.l9lSha,parentL9FSHA256:proof.l9fSha,
  sourceOrigin:"NEW_FOUR_OFFICIAL_RENDERED_LOCAL_HIERARCHIES",
  sampleCount:4,titleParityCount:result.filter(x=>x.titleParity).length,
  localReviewCount:result.reduce((n,x)=>n+x.reviewCandidateCount,0),rows:result,
  formalFieldPromotions:0,sessionSplits:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,cookiesPersisted:false,
  screenshotsPersisted:false,networkBodiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  releaseState:HOLD};
 validateReport(r);return r;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);assert.equal(r.parentL9LHead,HEAD);assert.equal(r.sampleCount,4);
 assert.deepEqual(r.rows.map(x=>x.id),IDS);
 assert.equal(r.titleParityCount,r.rows.filter(x=>x.titleParity).length);
 assert.equal(r.localReviewCount,r.rows.reduce((n,x)=>n+x.reviewCandidateCount,0));
 for(const x of r.rows){
  assert.equal(x.url,BASE+x.id);assert.equal(x.formalDate,null);
  assert.equal(x.formalPrice,null);assert.equal(x.ticketStatus,"UNKNOWN");
  assert.equal(x.published,false);assert.equal(x.goldenVerified,false);
  if(!x.titleParity)assert.equal(x.diagnostics.length,0);
  assert.ok(x.diagnostics.length<=32);
  for(const e of x.diagnostics){assert.equal(e.fieldPromotion,false);assert.equal(e.verified,false);}
 }
 for(const [k,v] of Object.entries({formalFieldPromotions:0,sessionSplits:0,
  goldenAccepted:0,published:false,writerExecuted:false,schedulerExecuted:false,
  notifierExecuted:false,mergeExecuted:false,rawHtmlPersisted:false,
  cookiesPersisted:false,screenshotsPersisted:false,networkBodiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD}))
  assert.equal(r[k],v,k);
 return true;
}
export function safeOut(where){
 const root=resolve("."),d=resolve(where);
 if(d===root||!d.startsWith(root+sep)||["docs","scripts","tests",".github",".git"].some(s=>d===resolve(s)||d.startsWith(resolve(s)+sep)))
  throw Error("HOLD_OUTPUT_BOUNDARY");
 return d;
}
export async function emit(r,path){
 validateReport(r);const d=safeOut(path);await mkdir(d,{recursive:true});
 const b=Buffer.from(json(r));await writeFile(d+"/ibon_neighbor_reasons.json",b);
 const m={kind:"EVENTRADAR_P30_L9M_SHA_MANIFEST_V1",
  sourceL9LSHA256:r.parentL9LSHA256,sourceL9FSHA256:r.parentL9FSHA256,
  sha256:{"ibon_neighbor_reasons.json":sha(b)},releaseState:HOLD,published:false};
 await writeFile(d+"/manifest.json",json(m));return m;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let n=2;n<process.argv.length;n+=2)args[process.argv[n]]=process.argv[n+1];
 if(!args["--l9l"]||!args["--l9f"]||!args["--out"]){console.error("HOLD_TWO_SOURCES_REQUIRED");process.exitCode=2;}
 else{
  const lb=await readFile(args["--l9l"]),fb=await readFile(args["--l9f"]);
  const r=await audit(JSON.parse(lb),lb,JSON.parse(fb),fb);
  await emit(r,args["--out"]);
  for(const row of r.rows)console.log("L9M_SOURCE_REASON",JSON.stringify({id:row.id,http:row.http,
   title:row.titleParity,labels:row.labelsVisible,review:row.reviewCandidateCount,
   reasons:row.reasonCounts}));
  console.log("PASS L9M_FOUR_SOURCE_HIERARCHY_DIAGNOSTICS",r.sampleCount);
  console.log("HOLD L9M_FORMAL_FIELDS_GOLDEN_PUBLICATION_DENIED");
 }
}
