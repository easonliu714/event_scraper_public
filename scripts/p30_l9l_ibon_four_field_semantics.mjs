#!/usr/bin/env node
/* P30-L9-L: four ibon official detail structural/semantic REVIEW-only.
 * No body-global date matching, raw HTML, authentication, API guessing, publication.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";
export const KIND="EVENTRADAR_P30_L9L_FOUR_IBON_DETAIL_SEMANTIC_REVIEW_V1";
export const IDS=["39575","39878","39907","39978"];
export const ROOT="https://ticket.ibon.com.tw/ActivityInfo/Details/";
export const HOLD="HARD_HOLD_NO_PUBLICATION";
export const sha=b=>createHash("sha256").update(b).digest("hex");
const json=x=>JSON.stringify(x,null,2)+"\n";
const norm=x=>String(x??"").replace(/\s+/gu," ").trim().slice(0,180).replace(/[，,。．.\-–—_·•]/gu,"").toLowerCase();
const ROLE=[
 ["EVENT_PERIOD",/^(?:活動日期|演出日期|演出時間|開演時間|活動時間)$/u],
 ["SALE_PERIOD",/^(?:售票期間|售票時間|開賣時間|預售期間)$/u],
 ["ADMISSION_TIME",/^(?:入場時間|進場時間)$/u],
 ["REGISTRATION_PERIOD",/^(?:報名期間|登記期間)$/u],
 ["VOUCHER_VALIDITY",/^(?:票券有效期限|使用期限|兌換期限)$/u],
 ["VENUE",/^(?:活動地點|演出地點|活動場館|演出場館|場地)$/u],
 ["PRICE",/^(?:票價|票券價格)$/u],
 ["SESSION",/^(?:場次|演出場次)$/u]
];
const DATE=/(?:20\d{2}[\/.\-年]\s*\d{1,2}|\d{1,2}\/\d{1,2}|\d{1,2}:\d{2})/u;
const MONEY=/(?:NT\s*\$|TWD\s*|[$＄])\s*[\d,]+|[\d,]+\s*(?:元|圓)/iu;
export function validateParent(source,bytes){
 assert.deepEqual(JSON.parse(bytes),source);
 assert.equal(source.kind,"EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1");
 assert.equal(source.parentL9ERun,40449476633);
 assert.equal(source.additionalSampleSize,5);assert.equal(source.additionalTitleParity,5);
 assert.equal(source.formalFieldPromotions,0);assert.equal(source.goldenAccepted,0);
 assert.equal(source.published,false);assert.equal(source.releaseState,HOLD);
 const rows=IDS.map(id=>{
  const row=source.samples.filter(x=>x.candidateId==="ibon:"+id);
  assert.equal(row.length,1);
  assert.equal(row[0].officialUrl,ROOT+id);
  assert.equal(row[0].titleParity,true);assert.equal(row[0].detailState,"DETAIL_TITLE_PARITY_PASS");
  assert.ok(norm(row[0].listTitle).length>=4);
  return {id,title:row[0].listTitle,url:row[0].officialUrl};
 });
 return {parentSha256:sha(bytes),rows};
}
export function evaluatePair(pair){
 const label=String(pair?.label??"").replace(/\s+/gu," ").trim().replace(/[:：]$/u,"");
 const relation=pair?.relation;
 const role=ROLE.find(x=>x[1].test(label))?.[0];
 if(!role)return null;
 const base={label,role,relation,quality:"HOLD",sourceBound:false,
  verified:false,formalFieldPromoted:false};
 if(!["SAME_NODE","DIRECT_SIBLING","LOCAL_PARENT"].includes(relation)||
   pair.distance!==1||pair.interactive===true||pair.otherRoleCount!==0)
  return {...base,quality:"HOLD_UNBOUND_OR_AMBIGUOUS"};
 const value=String(pair.value??"").replace(/\s+/gu," ").trim().slice(0,150);
 if(!value||value.length>110)return {...base,quality:"REJECT_EMPTY_OR_OVERLONG"};
 if(role==="EVENT_PERIOD"&&/(售票|開賣|入場|報名|登記|有效期限)/u.test(value))
  return {...base,quality:"HOLD_ROLE_CONFLICT"};
 if(["EVENT_PERIOD","SALE_PERIOD","ADMISSION_TIME","REGISTRATION_PERIOD","VOUCHER_VALIDITY"].includes(role)&&!DATE.test(value))
  return {...base,quality:"REJECT_NO_TIME_TOKEN"};
 if(role==="PRICE"&&!MONEY.test(value))return {...base,quality:"REJECT_GENERIC_PRICE"};
 if(role==="VENUE"&&/^(?:資訊|待公告|詳情|未知)$/u.test(value))
  return {...base,quality:"REJECT_GENERIC_VENUE"};
 const quality=role==="SESSION"?"SESSION_REVIEW_NO_SPLIT":role+"_SOURCE_BOUND_REVIEW_ONLY";
 return {...base,quality,sourceBound:true,value,verified:false,formalFieldPromoted:false};
}
export function review(pairs,matched){
 assert.ok(Array.isArray(pairs)&&pairs.length<=50);
 const accepted=[],rejected=[];
 if(!matched)return {accepted,rejected};
 for(const p of pairs){
  const e=evaluatePair(p);
  if(!e)continue;
  if(e.sourceBound)accepted.push(e);else rejected.push(e);
  if(accepted.length+rejected.length>=16)break;
 }
 return{accepted,rejected};
}
function extract(){
 const clip=s=>String(s??"").replace(/\s+/g," ").trim().slice(0,150);
 const labels=new Set(["活動日期","演出日期","演出時間","開演時間","活動時間",
 "售票期間","售票時間","開賣時間","預售期間","入場時間","進場時間",
 "報名期間","登記期間","票券有效期限","使用期限","兌換期限",
 "活動地點","演出地點","活動場館","演出場館","場地","票價","票券價格","場次","演出場次"]);
 const pairs=[],counts={labels:0,images:document.querySelectorAll("img").length,
  sections:document.querySelectorAll("section,article").length};
 const nodes=[...document.querySelectorAll("strong,b,h2,h3,h4,span,dt,th,p,li,label")].slice(0,2600);
 for(const el of nodes){
  if(pairs.length>=50)break;
  const label=clip(el.childElementCount===0?el.textContent:
    [...el.childNodes].filter(x=>x.nodeType===3).map(x=>x.textContent).join(" ")).replace(/[:：]$/,"");
  if(!labels.has(label))continue;
  counts.labels++;
  const p=el.parentElement, next=el.nextElementSibling;
  if(next&&next.parentElement===p&&!next.matches("a,button,input,form,script")){
   const v=clip(next.innerText||next.textContent);
   const roleCount=[...v.matchAll(/活動日期|演出日期|售票期間|售票時間|入場時間|報名期間|票價/g)].length;
   if(v)pairs.push({label,value:v,relation:"DIRECT_SIBLING",distance:1,otherRoleCount:roleCount,
    interactive:!!next.querySelector("a,button,input,form")});
  }
  if(!next&&p?.nextElementSibling&&p.childElementCount===1&&p.nextElementSibling.tagName!=="A"){
   const v=clip(p.nextElementSibling.innerText||p.nextElementSibling.textContent);
   if(v)pairs.push({label,value:v,relation:"LOCAL_PARENT",distance:1,otherRoleCount:0,
    interactive:!!p.nextElementSibling.querySelector("a,button,input,form")});
  }
 }
 return {headings:[...document.querySelectorAll("h1,h2,h3,h4")].slice(0,28).map(e=>clip(e.textContent)),
 pairs,counts};
}
export async function audit(source,bytes,browser=chromium,opts={}){
 const parent=validateParent(source,bytes),results=[];
 const driver=await browser.launch({headless:true,args:["--no-sandbox"]});
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},permissions:[],
    acceptDownloads:false,javaScriptEnabled:true});
  try{
   for(const s of parent.rows){
    const out={id:s.id,url:s.url,http:null,titleParity:false,state:"NOT_VISITED",
      structuralCounts:{},accepted:[],rejected:[],formalDate:null,formalPrice:null,
      ticketStatus:"UNKNOWN",goldenVerified:false,published:false};
    results.push(out);
    const page=await ctx.newPage();
    try{
     const response=await page.goto(s.url,{waitUntil:"domcontentloaded",timeout:22000});
     out.http=response?.status()??null;
     if(page.url()!==s.url){out.state="HOLD_REDIRECT";continue;}
     if(out.http!==200){out.state="HOLD_HTTP";continue;}
     await page.waitForTimeout(opts.settleMs??1600);
     const dom=await page.evaluate(extract);
     out.titleParity=dom.headings.some(x=>norm(x)===norm(s.title));
     out.state=out.titleParity?"TITLE_PARITY_REVIEW_ONLY":"HOLD_TITLE_DRIFT";
     out.structuralCounts=dom.counts;
     const parsed=review(dom.pairs,out.titleParity);
     out.accepted=parsed.accepted;out.rejected=parsed.rejected;
    }catch(e){out.state=e?.name==="TimeoutError"?"HOLD_TIMEOUT":"HOLD_BROWSER";}
    finally{await page.close();}
   }
  }finally{await ctx.close();}
 }finally{await driver.close();}
 const report={kind:KIND,parentL9KHead:"30aa18a9fbe4dc7b46f9b4b2cf41a51b70f0b11a",
  parentL9FRun:40494326021,parentL9FArtifact:12729277485,parentL9FSourceSHA256:parent.parentSha256,
  sourceOrigin:"FOUR_NEW_NORMAL_PUBLIC_DETAIL_RENDERINGS",sampleCount:4,
  titleParityCount:results.filter(x=>x.titleParity).length,
  reviewPairCount:results.reduce((a,x)=>a+x.accepted.length,0),
  rejectedPairCount:results.reduce((a,x)=>a+x.rejected.length,0),
  results,formalFieldPromotions:0,sessionSplits:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,cookiesPersisted:false,networkBodiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
 validateReport(report);return report;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);assert.equal(r.sampleCount,4);assert.equal(r.results.length,4);
 assert.equal(r.titleParityCount,r.results.filter(x=>x.titleParity).length);
 assert.equal(r.reviewPairCount,r.results.reduce((a,x)=>a+x.accepted.length,0));
 assert.equal(r.rejectedPairCount,r.results.reduce((a,x)=>a+x.rejected.length,0));
 assert.deepEqual(r.results.map(x=>x.id),IDS);
 for(const x of r.results){
  assert.equal(x.url,ROOT+x.id);assert.equal(x.formalDate,null);
  assert.equal(x.formalPrice,null);assert.equal(x.ticketStatus,"UNKNOWN");
  assert.equal(x.goldenVerified,false);assert.equal(x.published,false);
  if(!x.titleParity)assert.equal(x.accepted.length+x.rejected.length,0);
  for(const e of [...x.accepted,...x.rejected]){
   assert.equal(e.verified,false);assert.equal(e.formalFieldPromoted,false);
  }
 }
 for(const [k,v] of Object.entries({formalFieldPromotions:0,sessionSplits:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,cookiesPersisted:false,
  networkBodiesPersisted:false,existingAndroid44Preserved:true,
  l8CoreAndroidPassPreserved:true,releaseState:HOLD}))assert.equal(r[k],v);
 return true;
}
export function safeOut(v){
 const cwd=resolve("."),p=resolve(v);
 if(p===cwd||!p.startsWith(cwd+sep)||["docs","scripts","tests",".github",".git"].some(x=>p===resolve(x)||p.startsWith(resolve(x)+sep)))
  throw Error("HOLD_ISOLATED_OUTPUT_ONLY");
 return p;
}
export async function emit(r,where){
 validateReport(r);const d=safeOut(where);await mkdir(d,{recursive:true});
 const bytes=Buffer.from(json(r));await writeFile(d+"/ibon_four_field_semantics.json",bytes);
 const m={kind:"EVENTRADAR_P30_L9L_SHA_MANIFEST_V1",parentSha256:r.parentL9FSourceSHA256,
  sha256:{"ibon_four_field_semantics.json":sha(bytes)},releaseState:HOLD};
 await writeFile(d+"/manifest.json",json(m));return m;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--source"]||!args["--out"]){console.error("HOLD_INPUT_REQUIRED");process.exitCode=2;}
 else{
  const raw=await readFile(args["--source"]);const r=await audit(JSON.parse(raw),raw);
  await emit(r,args["--out"]);
  for(const row of r.results)console.log("L9L_IBON_DETAIL",JSON.stringify({id:row.id,http:row.http,
   titleParity:row.titleParity,labels:row.structuralCounts.labels||0,
   review:row.accepted.length,rejected:row.rejected.length,state:row.state}));
  console.log("PASS L9L_BOUNDED_FOUR_DETAILS",r.sampleCount);
  console.log("QUALITY L9L_REVIEW_PAIRS",r.reviewPairCount);
  console.log("HOLD L9L_FORMAL_FIELDS_GOLDEN_PUBLISHER");
 }
}
