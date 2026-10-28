#!/usr/bin/env node
/* P30-L9-P: characterize only controls adjacent to the four source-pinned
 * ibon 活動日期 labels. No clicks, form submissions, page text/date extraction,
 * credentials, screenshots, raw HTML, new event records or publication.
 * Two bounded DOM snapshots in the SAME normal Chromium page per ID.
 */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
export const KIND='EVENTRADAR_P30_L9P_IBON_LOCAL_CONTROL_TYPES_V1';
export const IDS=['39575','39878','39907','39978'];
export const BASE='https://ticket.ibon.com.tw/ActivityInfo/Details/';
export const HOLD='HARD_HOLD_NO_PUBLICATION';
export const PARENT_RUN=40702378377,PARENT_ART=12820574944;
export const PARENT_ZIP_SHA='c0f03e2448ae90388f113164388a254808656d5f274a75e2eaad66c2a530b8d3';
export const L9F_RUN=40494326021,L9F_ART=12729277485;
export const L9F_FILE_SHA='81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4';
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
export const norm=s=>String(s??'').replace(/\s+/gu,' ').trim().slice(0,130).replace(/[，,。．.\-–—_·•]/gu,'').toLowerCase();
export function parents(o,ob,f,fb){
 assert.deepEqual(JSON.parse(ob),o);assert.deepEqual(JSON.parse(fb),f);
 assert.equal(sha(fb),L9F_FILE_SHA,'HOLD_L9P_L9F_FILE_SHA');
 assert.equal(o.kind,'EVENTRADAR_P30_L9O_IBON_LABEL_SELECTOR_PARITY_V1');
 assert.equal(o.sampleCount,4);assert.equal(o.currentExactHeadingCount,4);
 assert.equal(o.l9mScopeLabelCount,4);assert.equal(o.l9nH3LabelCount,4);
 assert.equal(o.localReviewOnlyCount,0);assert.equal(o.formalFieldPromotions,0);
 assert.equal(o.published,false);assert.equal(o.releaseState,HOLD);
 assert.equal(f.kind,'EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1');
 assert.equal(f.additionalTitleParity,5);assert.equal(f.goldenAccepted,0);
 assert.equal(f.published,false);assert.equal(f.releaseState,HOLD);
 const sources=IDS.map(id=>{
  const a=o.rows.filter(x=>x.id===id),b=f.samples.filter(x=>x.candidateId==='ibon:'+id);
  assert.equal(a.length,1);assert.equal(b.length,1);
  assert.equal(a[0].url,BASE+id);assert.equal(a[0].http,200);
  assert.equal(a[0].title.kind,'SOURCE_TITLE_HEADING_EXACT');
  assert.equal(a[0].strictH3LabelCount,1);
  assert.equal(a[0].observations.length,1);
  assert.equal(a[0].observations[0].localCause,'HOLD_INTERACTIVE_LOCAL');
  assert.equal(a[0].localReviewOnlyCount,0);
  assert.equal(b[0].officialUrl,BASE+id);assert.equal(b[0].titleParity,true);
  assert.ok(norm(b[0].listTitle).length>=4);
  return{id,url:BASE+id,title:b[0].listTitle};
 });
 return{sources,osha:sha(ob),fsha:sha(fb)};
}
export function controlCause(p){
 if(!p)return'HOLD_NO_LABEL';
 if(p.labelCount!==1)return'HOLD_LABEL_COUNT_DRIFT';
 if(!p.siblingTag)return'HOLD_NO_ADJACENT_REGION';
 if(p.controlCount<1)return'HOLD_NO_INTERACTIVE_CONTROL_NOW';
 if(p.otherRoleCount>0)return'HOLD_OTHER_ROLE_INSIDE_CONTROL_REGION';
 const form=p.formCount+p.inputCount+p.selectCount;
 const action=p.buttonCount+p.roleButtonCount;
 if(form>0&&p.anchorCount>0)return'HOLD_MIXED_LINK_AND_FORM';
 if(form>0)return'HOLD_FORM_INPUT_OR_SELECT';
 if(action>0&&p.anchorCount>0)return'HOLD_MIXED_LINK_AND_BUTTON';
 if(action>0)return'HOLD_BUTTON_OR_ROLE_BUTTON';
 if(p.anchorCount>0&&p.controlCount===p.anchorCount)return'HOLD_NAVIGATION_ANCHOR_ONLY';
 return'HOLD_OTHER_INTERACTIVE';
}
export function compareTwo(first,second){
 const a=controlCause(first),b=controlCause(second);
 if(a!==b)return{stable:false,cause:'HOLD_RENDER_CONTROL_CAUSE_DRIFT',first:a,second:b};
 const fields=['labelCount','siblingTag','controlCount','anchorCount','buttonCount',
  'formCount','inputCount','selectCount','roleButtonCount','otherRoleCount'];
 if(fields.some(k=>first?.[k]!==second?.[k]))
  return{stable:false,cause:'HOLD_RENDER_CONTROL_TOPOLOGY_DRIFT',first:a,second:b};
 return{stable:true,cause:a,first:a,second:b};
}
function pageProbe(){
 const clip=s=>String(s??'').replace(/\s+/g,' ').trim().slice(0,130);
 const headings=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35).map(x=>clip(x.textContent));
 const labels=[...document.querySelectorAll('h3')].slice(0,250)
  .filter(x=>clip([...x.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ')).replace(/[：:]$/u,'')==='活動日期');
 const label=labels.length===1?labels[0]:null;
 const sibling=label?.nextElementSibling??null;
 const counts={anchorCount:0,buttonCount:0,formCount:0,inputCount:0,
  selectCount:0,roleButtonCount:0,controlCount:0};
 if(sibling){
  const nodes=[sibling,...sibling.querySelectorAll('a,button,form,input,select,[role="button"]')].slice(0,32);
  for(const n of nodes){
   if(n.matches('a'))counts.anchorCount++;
   if(n.matches('button'))counts.buttonCount++;
   if(n.matches('form'))counts.formCount++;
   if(n.matches('input'))counts.inputCount++;
   if(n.matches('select'))counts.selectCount++;
   if(n.matches('[role="button"]'))counts.roleButtonCount++;
   if(n.matches('a,button,form,input,select,[role="button"]'))counts.controlCount++;
  }
 }
 const local=sibling?clip(sibling.textContent):'';
 const otherRoleCount=(local.match(/售票期間|售票時間|入場時間|報名期間|票價|場次|演出日期|活動日期/g)||[]).length;
 return{headings,local:{labelCount:labels.length,siblingTag:sibling?.tagName??null,
  siblingChildren:sibling?.childElementCount??0,
  directTextPresent:!!sibling&&[...sibling.childNodes].some(n=>n.nodeType===3&&clip(n.textContent).length>0),
  otherRoleCount,...counts}};
}
export function summarize(source,first,second){
 const titleFirst=first.headings.some(x=>norm(x)===norm(source.title));
 const titleSecond=second.headings.some(x=>norm(x)===norm(source.title));
 const result=compareTwo(first.local,second.local);
 return{titleFirst,titleSecond,stableTitle:titleFirst&&titleSecond,
  first:first.local,second:second.local,
  controlDecision:titleFirst&&titleSecond?result.cause:'HOLD_SOURCE_TITLE_DRIFT',
  controlStable:result.stable&&titleFirst&&titleSecond,
  firstControlCause:result.first,secondControlCause:result.second,
  acceptedFields:0,formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN'};
}
export async function audit(o,ob,f,fb,browser=chromium,opts={}){
 const proof=parents(o,ob,f,fb),driver=await browser.launch({headless:true,args:['--no-sandbox']});
 const rows=[];
 try{
  const context=await driver.newContext({viewport:{width:1280,height:800},
   javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   for(const source of proof.sources){
    const r={id:source.id,url:source.url,http:null,state:'NOT_VISITED',
     titleFirst:false,titleSecond:false,stableTitle:false,first:null,second:null,
     controlDecision:'HOLD_NOT_VISITED',controlStable:false,
     firstControlCause:null,secondControlCause:null,acceptedFields:0,
     formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN'};
    rows.push(r);const page=await context.newPage();
    try{
     const response=await page.goto(source.url,{waitUntil:'domcontentloaded',timeout:22000});
     r.http=response?.status()??null;
     if(page.url()!==source.url){r.state='HOLD_REDIRECT';continue;}
     if(r.http!==200){r.state='HOLD_HTTP';continue;}
     await page.waitForTimeout(opts.initialMs??1500);
     const first=await page.evaluate(pageProbe);
     await page.waitForTimeout(opts.followupMs??1800);
     const second=await page.evaluate(pageProbe);
     Object.assign(r,summarize(source,first,second));
     r.state=r.stableTitle?'SOURCE_TITLE_TWO_SNAPSHOTS_REVIEW_ONLY':'HOLD_SOURCE_TITLE_DRIFT';
    }catch(e){r.state=e?.name==='TimeoutError'?'HOLD_TIMEOUT':'HOLD_BROWSER';}
    finally{await page.close();}
   }
  }finally{await context.close();}
 }finally{await driver.close();}
 const report={kind:KIND,sourceOrigin:'FOUR_NORMAL_OFFICIAL_PAGES_TWO_PASSIVE_DOM_SNAPSHOTS',
  parentL9ORun:PARENT_RUN,parentL9OArtifact:PARENT_ART,parentL9OZipSHA256:PARENT_ZIP_SHA,
  parentL9OFileSHA256:proof.osha,parentL9FRun:L9F_RUN,parentL9FArtifact:L9F_ART,
  parentL9FFileSHA256:proof.fsha,sampleCount:4,rows,
  currentTitleBothSnapshots:rows.filter(x=>x.stableTitle).length,
  controlTopologyStableCount:rows.filter(x=>x.controlStable).length,
  reasonCounts:rows.reduce((a,x)=>(a[x.controlDecision]=(a[x.controlDecision]||0)+1,a),{}),
  formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,sourceTextPersisted:false,linkUrlsPersisted:false,
  screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
 validate(report);return report;
}
export function validate(r){
 assert.equal(r.kind,KIND);assert.equal(r.sampleCount,4);
 assert.deepEqual(r.rows.map(x=>x.id),IDS);
 assert.equal(r.currentTitleBothSnapshots,r.rows.filter(x=>x.stableTitle).length);
 assert.equal(r.controlTopologyStableCount,r.rows.filter(x=>x.controlStable).length);
 assert.deepEqual(r.reasonCounts,r.rows.reduce((a,x)=>(a[x.controlDecision]=(a[x.controlDecision]||0)+1,a),{}));
 for(const x of r.rows){
  assert.equal(x.url,BASE+x.id);assert.equal(x.acceptedFields,0);
  assert.equal(x.formalDate,null);assert.equal(x.formalPrice,null);
  assert.equal(x.ticketStatus,'UNKNOWN');
  if(!x.stableTitle)assert.equal(x.controlStable,false);
  for(const p of [x.first,x.second]){
   if(!p)continue;
   assert.ok(p.labelCount>=0&&p.labelCount<=250);
   assert.ok(p.controlCount>=0&&p.controlCount<=32);
   for(const key of ['anchorCount','buttonCount','formCount','inputCount',
    'selectCount','roleButtonCount','otherRoleCount'])assert.ok(Number.isInteger(p[key])&&p[key]>=0);
   assert.ok(!Object.keys(p).some(k=>/url|href|textvalue|html|cookie|date|price/i.test(k)));
  }
  assert.ok(x.controlDecision.startsWith('HOLD_'));
 }
 for(const [key,val]of Object.entries({formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,sourceTextPersisted:false,
  linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD}))
  assert.equal(r[key],val,key);
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
 const b=Buffer.from(json(r));await writeFile(dir+'/ibon_local_control_types.json',b);
 const manifest={kind:'EVENTRADAR_P30_L9P_SHA_MANIFEST_V1',
  parentL9OZipSHA256:PARENT_ZIP_SHA,parentL9OFileSHA256:r.parentL9OFileSHA256,
  parentL9FFileSHA256:L9F_FILE_SHA,
  filesSHA256:{'ibon_local_control_types.json':sha(b)},releaseState:HOLD,published:false};
 await writeFile(dir+'/manifest.json',json(manifest));return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9o']||!flags['--l9f']||!flags['--out'])throw Error('HOLD_TWO_PARENT_REPORTS_REQUIRED');
 const ob=await readFile(flags['--l9o']),fb=await readFile(flags['--l9f']);
 const r=await audit(JSON.parse(ob),ob,JSON.parse(fb),fb);
 await emit(r,flags['--out']);
 for(const x of r.rows)console.log('L9P_CONTROL',JSON.stringify({id:x.id,http:x.http,
  titleBoth:x.stableTitle,topologyStable:x.controlStable,
  cause:x.controlDecision,first:x.firstControlCause,second:x.secondControlCause,
  firstCounts:x.first&&{a:x.first.anchorCount,button:x.first.buttonCount,
   form:x.first.formCount,input:x.first.inputCount,select:x.first.selectCount,
   roleButton:x.first.roleButtonCount},secondCounts:x.second&&{a:x.second.anchorCount,
   button:x.second.buttonCount,form:x.second.formCount,input:x.second.inputCount,
   select:x.second.selectCount,roleButton:x.second.roleButtonCount}}));
 console.log('PASS L9P_FOUR_SOURCE_TWO_PASSIVE_SNAPSHOTS');
 console.log('HOLD L9P_NO_EVENT_FIELDS_NO_GOLDEN_NO_PUBLICATION');
}
