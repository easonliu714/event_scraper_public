#!/usr/bin/env node
/* P30-L9-O: compare L9-N h3-only label selector with L9-M's bounded
 * multi-tag direct-text selector, plus exact source-title identity.
 * Public normal Chromium only. Four fixed official details, no data publishing.
 * Never extract event dates/prices or infer missing labels mean no events.
 */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
export const KIND='EVENTRADAR_P30_L9O_IBON_LABEL_SELECTOR_PARITY_V1';
export const IDS=['39575','39878','39907','39978'];
export const BASE='https://ticket.ibon.com.tw/ActivityInfo/Details/';
export const HOLD='HARD_HOLD_NO_PUBLICATION';
export const L9N_RUN=40686039228,L9N_ART=12814702732,L9F_RUN=40494326021,L9F_ART=12729277485;
export const L9N_ZIP_SHA='a049545092f6a508791f3a12b5c05395de7b4eb975efbb3d9b8813319ec1a5c9';
export const L9F_FILE_SHA='81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4';
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=o=>JSON.stringify(o,null,2)+'\n';
export function norm(s){return String(s??'').replace(/\s+/gu,' ').trim().slice(0,130).replace(/[，,。．.\-–—_·•]/gu,'').toLowerCase();}
export function parents(n,nb,f,fb){
 assert.deepEqual(JSON.parse(nb),n);assert.deepEqual(JSON.parse(fb),f);
 assert.equal(sha(fb),L9F_FILE_SHA,'HOLD_L9O_L9F_FILE_SHA');
 assert.equal(n.kind,'EVENTRADAR_P30_L9N_IBON_SPLIT_LOCAL_CAUSE_V1');
 assert.equal(n.sampleCount,4);assert.equal(n.currentTitleMatchCount,3);
 assert.equal(n.reviewOnlyCandidates,0);assert.equal(n.formalFieldPromotions,0);
 assert.equal(n.published,false);assert.equal(n.releaseState,HOLD);
 assert.equal(f.kind,'EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1');
 assert.equal(f.additionalTitleParity,5);assert.equal(f.goldenAccepted,0);
 assert.equal(f.published,false);assert.equal(f.releaseState,HOLD);
 const expected=[false,true,true,true];
 const sources=IDS.map((id,i)=>{
  const a=n.rows.filter(x=>x.id===id),b=f.samples.filter(x=>x.candidateId==='ibon:'+id);
  assert.equal(a.length,1);assert.equal(b.length,1);
  assert.equal(a[0].url,BASE+id);assert.equal(b[0].officialUrl,BASE+id);
  assert.equal(a[0].http,200);assert.equal(a[0].sourceTitleMatched,expected[i]);
  assert.equal(a[0].labelCount,0);assert.equal(a[0].safeReviewCandidates,0);
  assert.equal(a[0].formalDate,null);assert.equal(a[0].formalPrice,null);
  assert.equal(b[0].titleParity,true);
  assert.ok(norm(b[0].listTitle).length>=4);
  return{id,url:BASE+id,title:b[0].listTitle,previousL9NTitleMatched:expected[i]};
 });
 return{sources,nsha:sha(nb),fsha:sha(fb)};
}
export function titleDecision(title,dom){
 const original=norm(title);
 if(!original)return{kind:'HOLD_MISSING_ORIGINAL_TITLE',headingExact:false,metaOnly:false};
 const headings=(dom?.headings??[]).slice(0,35);
 const exactHeading=headings.some(x=>norm(x)===original);
 const exactMeta=norm(dom?.ogTitle)===original;
 const exactDocument=norm(dom?.documentTitle)===original;
 return{kind:exactHeading?'SOURCE_TITLE_HEADING_EXACT':
   exactMeta?'HOLD_TITLE_META_ONLY':exactDocument?'HOLD_TITLE_DOCUMENT_ONLY':
   headings.length?'HOLD_TITLE_HEADING_DRIFT':'HOLD_TITLE_NO_HEADING',
  headingExact:exactHeading,metaOnly:!exactHeading&&(exactMeta||exactDocument),
  titleHeadingCount:headings.length,ogTitleExact:exactMeta,documentTitleExact:exactDocument};
}
export function localDecision(o){
 if(!o)return'HOLD_NO_DIRECT_LABEL';
 if(!o.labelDirect)return'HOLD_LABEL_NOT_DIRECT_TEXT';
 if(o.interactiveCount>0)return'HOLD_INTERACTIVE_LOCAL';
 if(o.otherRoleCount>0)return'HOLD_MIXED_OTHER_ROLE_LOCAL';
 if(!o.siblingTag)return'HOLD_NO_ADJACENT_SIBLING';
 if(o.siblingChildCount>0&&!o.siblingDirectText)return'HOLD_NESTED_LOCAL_NOT_BOUND';
 if(!o.siblingDirectText)return'HOLD_EMPTY_DIRECT_LOCAL';
 if(!o.hasDateToken)return'HOLD_NO_DIRECT_DATE_TOKEN';
 if(o.siblingTag==='SCRIPT'||o.siblingTag==='STYLE')return'HOLD_NONCONTENT_SIBLING';
 return'DIRECT_LABEL_LOCAL_TOKEN_REVIEW_ONLY';
}
export function summarize(dom,source){
 const title=titleDecision(source.title,dom);
 const observations=(dom?.observations??[]).slice(0,12).map(o=>({
  labelTag:o.labelTag,parentTag:o.parentTag,siblingTag:o.siblingTag,
  directText:o.labelDirect,interactiveCount:o.interactiveCount,
  otherRoleCount:o.otherRoleCount,siblingChildCount:o.siblingChildCount,
  siblingDirectText:o.siblingDirectText,hasDateToken:o.hasDateToken,
  localCause:localDecision(o),fieldPromoted:false
 }));
 const labelTagCounts={};
 for(const x of observations)labelTagCounts[x.labelTag]=(labelTagCounts[x.labelTag]||0)+1;
 const strictH3=observations.filter(x=>x.labelTag==='H3').length;
 return{title,strictH3LabelCount:strictH3,
  l9mSelectorLabelCount:observations.length,labelTagCounts,observations,
  localReviewOnlyCount:title.headingExact?observations.filter(x=>x.localCause==='DIRECT_LABEL_LOCAL_TOKEN_REVIEW_ONLY').length:0,
  formalFieldPromotions:0};
}
function pageProbe(){
 const c=s=>String(s??'').replace(/\s+/g,' ').trim().slice(0,130);
 const headings=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35).map(x=>c(x.textContent));
 const ogTitle=document.querySelector('meta[property="og:title"]')?.getAttribute('content')??'';
 const selector='strong,b,h2,h3,h4,span,dt,th,label,p,li';
 const candidates=[...document.querySelectorAll(selector)].slice(0,2800);
 const observations=[];
 for(const el of candidates){
  if(observations.length>=12)break;
  const direct=c([...el.childNodes].filter(x=>x.nodeType===3).map(x=>x.textContent).join(' '));
  const text=el.childElementCount?direct:c(el.textContent);
  if(text.replace(/[：:]$/u,'')!=='活動日期')continue;
  const next=el.nextElementSibling;
  const siblingText=next?c([...next.childNodes].filter(x=>x.nodeType===3).map(x=>x.textContent).join(' ')):'';
  const all=next?c(next.textContent):'';
  observations.push({
   labelTag:el.tagName,parentTag:el.parentElement?.tagName??'NONE',
   labelDirect:direct==='活動日期'||direct==='活動日期：',
   siblingTag:next?.tagName??null,
   siblingChildCount:next?.childElementCount??0,
   siblingDirectText:siblingText.length>0,
   hasDateToken:/(?:20\d{2}[-/.年]\d{1,2}|\d{1,2}[/月]\d{1,2}|\d{1,2}:\d{2})/u.test(siblingText),
   interactiveCount:next?.querySelectorAll('button,a,input,form,select,[role="button"]').length??0,
   otherRoleCount:(all.match(/售票期間|售票時間|入場時間|報名期間|票價|場次|演出日期|活動日期/g)||[]).length
  });
 }
 return{headings,ogTitle:c(ogTitle),documentTitle:c(document.title),observations};
}
export async function audit(n,nb,f,fb,browser=chromium,options={}){
 const proof=parents(n,nb,f,fb);
 const driver=await browser.launch({headless:true,args:['--no-sandbox']});
 const rows=[];
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},javaScriptEnabled:true,
   acceptDownloads:false,permissions:[]});
  try{
   for(const src of proof.sources){
    const r={id:src.id,url:src.url,http:null,state:'NOT_VISITED',
     previousL9NTitleMatched:src.previousL9NTitleMatched,
     title:{kind:'HOLD_NOT_VISITED',headingExact:false,metaOnly:false},
     strictH3LabelCount:0,l9mSelectorLabelCount:0,labelTagCounts:{},observations:[],
     localReviewOnlyCount:0,formalFieldPromotions:0,formalDate:null,formalPrice:null,
     ticketStatus:'UNKNOWN'};
    rows.push(r);const page=await ctx.newPage();
    try{
     const response=await page.goto(src.url,{waitUntil:'domcontentloaded',timeout:22000});
     r.http=response?.status()??null;
     if(page.url()!==src.url){r.state='HOLD_REDIRECT';continue;}
     if(r.http!==200){r.state='HOLD_HTTP';continue;}
     await page.waitForTimeout(options.settleMs??1500);
     Object.assign(r,summarize(await page.evaluate(pageProbe),src));
     r.state=r.title.headingExact?'TITLE_EXACT_LOCAL_TOPOLOGY_REVIEW_ONLY':'HOLD_SOURCE_TITLE_DRIFT';
    }catch(e){r.state=e?.name==='TimeoutError'?'HOLD_TIMEOUT':'HOLD_BROWSER';}
    finally{await page.close();}
   }
  }finally{await ctx.close();}
 }finally{await driver.close();}
 const report={kind:KIND,sourceOrigin:'FOUR_BOUNDED_NORMAL_PUBLIC_CHROMIUM_DETAILS',
  parentL9NRun:L9N_RUN,parentL9NArtifact:L9N_ART,parentL9NZipSHA256:L9N_ZIP_SHA,
  parentL9NFileSHA256:proof.nsha,parentL9FRun:L9F_RUN,parentL9FArtifact:L9F_ART,
  parentL9FFileSHA256:proof.fsha,sampleCount:4,rows,
  currentExactHeadingCount:rows.filter(x=>x.title.headingExact).length,
  l9mScopeLabelCount:rows.reduce((s,x)=>s+x.l9mSelectorLabelCount,0),
  l9nH3LabelCount:rows.reduce((s,x)=>s+x.strictH3LabelCount,0),
  localReviewOnlyCount:rows.reduce((s,x)=>s+x.localReviewOnlyCount,0),
  formalFieldPromotions:0,goldenAccepted:0,published:false,writerExecuted:false,
  schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,cookiesPersisted:false,screenshotsPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
 validate(report);return report;
}
export function validate(r){
 assert.equal(r.kind,KIND);assert.equal(r.sampleCount,4);
 assert.deepEqual(r.rows.map(x=>x.id),IDS);
 assert.equal(r.currentExactHeadingCount,r.rows.filter(x=>x.title.headingExact).length);
 assert.equal(r.l9mScopeLabelCount,r.rows.reduce((s,x)=>s+x.l9mSelectorLabelCount,0));
 assert.equal(r.l9nH3LabelCount,r.rows.reduce((s,x)=>s+x.strictH3LabelCount,0));
 assert.equal(r.localReviewOnlyCount,r.rows.reduce((s,x)=>s+x.localReviewOnlyCount,0));
 for(const x of r.rows){
  assert.equal(x.url,BASE+x.id);assert.equal(x.formalDate,null);
  assert.equal(x.formalPrice,null);assert.equal(x.ticketStatus,'UNKNOWN');
  assert.equal(x.formalFieldPromotions,0);
  assert.ok(x.observations.length<=12);
  assert.equal(x.l9mSelectorLabelCount,x.observations.length);
  assert.equal(x.strictH3LabelCount,x.observations.filter(z=>z.labelTag==='H3').length);
  if(!x.title.headingExact)assert.equal(x.localReviewOnlyCount,0);
  for(const y of x.observations)assert.equal(y.fieldPromoted,false);
 }
 for(const [k,v]of Object.entries({formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,cookiesPersisted:false,
  screenshotsPersisted:false,existingAndroid44Preserved:true,
  l8CoreAndroidPassPreserved:true,releaseState:HOLD}))assert.equal(r[k],v,k);
 return true;
}
export function safeOut(where){
 const root=resolve('.'),p=resolve(where);
 if(p===root||!p.startsWith(root+sep)||['docs','scripts','tests','.git','.github'].some(x=>p===resolve(x)||p.startsWith(resolve(x)+sep)))
  throw Error('HOLD_ISOLATED_OUTPUT_ONLY');
 return p;
}
export async function emit(r,where){
 validate(r);const dir=safeOut(where);await mkdir(dir,{recursive:true});
 const data=Buffer.from(json(r));await writeFile(dir+'/ibon_label_topology.json',data);
 const manifest={kind:'EVENTRADAR_P30_L9O_SHA_MANIFEST_V1',
  parentL9NZipSHA256:L9N_ZIP_SHA,parentL9NFileSHA256:r.parentL9NFileSHA256,
  parentL9FFileSHA256:L9F_FILE_SHA,filesSHA256:{'ibon_label_topology.json':sha(data)},
  releaseState:HOLD,published:false};
 await writeFile(dir+'/manifest.json',json(manifest));return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9n']||!flags['--l9f']||!flags['--out'])throw Error('HOLD_TWO_PARENT_REPORTS_REQUIRED');
 const nb=await readFile(flags['--l9n']),fb=await readFile(flags['--l9f']);
 const r=await audit(JSON.parse(nb),nb,JSON.parse(fb),fb);
 await emit(r,flags['--out']);
 for(const x of r.rows)console.log('L9O_TOPOLOGY',JSON.stringify({id:x.id,http:x.http,title:x.title.kind,
  oldL9NTitle:x.previousL9NTitleMatched,l9mLabels:x.l9mSelectorLabelCount,
  h3Labels:x.strictH3LabelCount,tagCounts:x.labelTagCounts,
  localCauses:x.observations.map(o=>o.localCause),reviewOnly:x.localReviewOnlyCount}));
 console.log('PASS L9O_FOUR_SOURCE_LABEL_SELECTOR_DIAGNOSTIC_COMPLETED');
 console.log('HOLD L9O_NO_FORMAL_FIELD_NO_GOLDEN_NO_PUBLICATION');
}
