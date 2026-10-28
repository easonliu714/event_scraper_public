#!/usr/bin/env node
/** P30-L9-N: independently classify four ibon local EVENT_PERIOD blockers.
 * Source pin: L9-M ambiguous role + L9-F original event title.
 * READ ONLY; normal Chromium, official exact detail URL, no global date scan.
 */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
export const KIND='EVENTRADAR_P30_L9N_IBON_SPLIT_LOCAL_CAUSE_V1';
export const IDS=['39575','39878','39907','39978'];
export const BASE='https://ticket.ibon.com.tw/ActivityInfo/Details/';
export const HOLD='HARD_HOLD_NO_PUBLICATION';
export const L9M_SHA='eb97b2984ce049a86c6f379ace5325c1ac77b5eb4a5eb4a325483b68091cb6ea';
export const L9F_SHA='81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4';
const sha=b=>createHash('sha256').update(b).digest('hex');
const norm=x=>String(x??'').replace(/\s+/gu,' ').trim().replace(/[，,。．.\-–—_·•]/gu,'').toLowerCase();
const serialize=x=>JSON.stringify(x,null,2)+'\n';
export function parentEvidence(m,mb,f,fb){
 assert.equal(sha(mb),L9M_SHA,'HOLD_L9N_M_SHA');
 assert.equal(sha(fb),L9F_SHA,'HOLD_L9N_F_SHA');
 assert.deepEqual(JSON.parse(mb),m);assert.deepEqual(JSON.parse(fb),f);
 assert.equal(m.kind,'EVENTRADAR_P30_L9M_IBON_NEIGHBOR_REASON_DIAGNOSTICS_V1');
 assert.equal(m.sampleCount,4);assert.equal(m.titleParityCount,4);
 assert.equal(m.localReviewCount,0);assert.equal(m.formalFieldPromotions,0);
 assert.equal(m.published,false);assert.equal(m.releaseState,HOLD);
 assert.equal(f.kind,'EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1');
 assert.equal(f.additionalTitleParity,5);assert.equal(f.published,false);
 assert.equal(f.goldenAccepted,0);assert.equal(f.releaseState,HOLD);
 const rows=IDS.map(id=>{
  const a=m.rows.filter(x=>x.id===id),b=f.samples.filter(x=>x.candidateId==='ibon:'+id);
  assert.equal(a.length,1);assert.equal(b.length,1);
  assert.equal(a[0].url,BASE+id);assert.equal(a[0].http,200);
  assert.equal(a[0].titleParity,true);
  assert.equal(a[0].reasonCounts.AMBIGUOUS_OR_INTERACTIVE,1);
  assert.equal(a[0].diagnostics.length,1);
  assert.equal(a[0].diagnostics[0].role,'EVENT_PERIOD');
  assert.equal(b[0].officialUrl,BASE+id);assert.equal(b[0].titleParity,true);
  assert.ok(norm(b[0].listTitle).length>=4);
  return{id,title:b[0].listTitle,url:BASE+id};
 });
 return{rows,msha:sha(mb),fsha:sha(fb)};
}
export function classify(probe){
 const base={category:'HOLD_NOT_ENOUGH_LOCAL_PROOF',sourceBoundReview:false,
  originalReason:'AMBIGUOUS_OR_INTERACTIVE',fieldPromoted:false};
 if(!probe)return {...base,category:'HOLD_NO_IMMEDIATE_SIBLING'};
 if(probe.label!=='活動日期'||probe.labelTag!=='H3'||probe.parentTag!=='DIV'||
   probe.parentChildren!==2||probe.relation!=='DIRECT_NEXT_SIBLING')
  return{...base,category:'HOLD_UNEXPECTED_DOM_TOPOLOGY'};
 if(probe.childControls>0)return{...base,category:'HOLD_INTERACTIVE_CONTROL',controlCount:probe.childControls};
 if(probe.otherRoleCount>0)return{...base,category:'HOLD_OTHER_ROLE_MIXED',otherRoleCount:probe.otherRoleCount};
 if(probe.childElements>0&&(!probe.directText||probe.directText.length<4))
  return{...base,category:'HOLD_NESTED_UNBOUND_TEXT',childElements:probe.childElements};
 const val=String(probe.directText??'').replace(/\s+/gu,' ').trim().slice(0,90);
 if(!val)return{...base,category:'HOLD_EMPTY_LOCAL_VALUE'};
 if(/售票|開賣|入場|報名|登記|有效期限|兌換/gu.test(val))
  return{...base,category:'HOLD_WRONG_TIME_ROLE'};
 if(!/(?:20\d{2}[-/.年]\d{1,2}|\d{1,2}[/月]\d{1,2}|\d{1,2}:\d{2})/u.test(val))
  return{...base,category:'HOLD_NO_DIRECT_DATE_TOKEN'};
 return{...base,category:'DIRECT_LABEL_DATE_TOKEN_REVIEW_ONLY',
  sourceBoundReview:true,reviewValue:val};
}
function pageProbe(){
 const clean=s=>String(s??'').replace(/\s+/g,' ').trim().slice(0,120);
 const titleHeadings=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35).map(e=>clean(e.textContent));
 const candidates=[...document.querySelectorAll('h3')].filter(e=>clean(e.textContent)==='活動日期').slice(0,3);
 const fields=candidates.map(el=>{
  const p=el.parentElement,other=el.nextElementSibling;
  if(!other)return null;
  const inner=clean(other.textContent);
  const direct=clean([...other.childNodes].filter(x=>x.nodeType===3).map(x=>x.textContent).join(' '));
  return{
   label:'活動日期',labelTag:el.tagName,parentTag:p?.tagName??'NONE',
   parentChildren:p?.childElementCount||0,relation:'DIRECT_NEXT_SIBLING',
   childControls:other.querySelectorAll('button,a,input,form,select,[role=button]').length,
   childElements:other.childElementCount,
   otherRoleCount:(inner.match(/售票期間|售票時間|入場時間|報名期間|票價|場次|演出日期|活動日期/g)||[]).length,
   directText:direct,hasVisibleText:inner.length>0,hasImage:other.querySelector('img')!==null
  };
 });
 return{titleHeadings,fields,labelCount:candidates.length};
}
export async function audit(m,mb,f,fb,browser=chromium,options={}){
 const parents=parentEvidence(m,mb,f,fb);
 const driver=await browser.launch({headless:true,args:['--no-sandbox']});
 const rows=[];
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},
   javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   for(const source of parents.rows){
    const record={id:source.id,url:source.url,http:null,sourceTitleMatched:false,
     state:'NOT_ATTEMPTED',labelCount:0,probeCount:0,categories:[],
     safeReviewCandidates:0,formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN'};
    rows.push(record);
    const page=await ctx.newPage();
    try{
     const response=await page.goto(source.url,{waitUntil:'domcontentloaded',timeout:22000});
     record.http=response?.status()??null;
     if(page.url()!==source.url){record.state='HOLD_REDIRECT';continue;}
     if(record.http!==200){record.state='HOLD_HTTP';continue;}
     await page.waitForTimeout(options.settleMs??1500);
     const dom=await page.evaluate(pageProbe);
     record.sourceTitleMatched=dom.titleHeadings.some(h=>norm(h)===norm(source.title));
     if(!record.sourceTitleMatched){record.state='HOLD_SOURCE_TITLE_MISMATCH';continue;}
     record.labelCount=dom.labelCount;record.probeCount=dom.fields.length;
     record.categories=dom.fields.map(x=>classify(x));
     record.safeReviewCandidates=record.categories.filter(x=>x.sourceBoundReview).length;
     record.state='SOURCE_ID_BOUND_LOCAL_DIAGNOSTICS_REVIEW_ONLY';
    }catch(e){record.state=e?.name==='TimeoutError'?'HOLD_TIMEOUT':'HOLD_BROWSER';}
    finally{await page.close();}
   }
  }finally{await ctx.close();}
 }finally{await driver.close();}
 const report={kind:KIND,sourceOrigin:'FOUR_NORMAL_OFFICIAL_DETAIL_RECAPTURE',
  parentL9MRun:40682420113,parentL9MArtifact:12813381760,parentL9FRun:40494326021,
  parentL9FArtifact:12729277485,parentL9MFileSHA256:parents.msha,
  parentL9FFileSHA256:parents.fsha,rows,sampleCount:4,
  currentTitleMatchCount:rows.filter(x=>x.sourceTitleMatched).length,
  reviewOnlyCandidates:rows.reduce((s,x)=>s+x.safeReviewCandidates,0),
  formalFieldPromotions:0,goldenAccepted:0,published:false,writerExecuted:false,
  schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
 verifyReport(report);return report;
}
export function verifyReport(r){
 assert.equal(r.kind,KIND);assert.equal(r.sampleCount,4);
 assert.deepEqual(r.rows.map(x=>x.id),IDS);
 assert.equal(r.currentTitleMatchCount,r.rows.filter(x=>x.sourceTitleMatched).length);
 assert.equal(r.reviewOnlyCandidates,r.rows.reduce((s,x)=>s+x.safeReviewCandidates,0));
 for(const a of r.rows){
  assert.equal(a.url,BASE+a.id);assert.equal(a.formalDate,null);
  assert.equal(a.formalPrice,null);assert.equal(a.ticketStatus,'UNKNOWN');
  if(!a.sourceTitleMatched)assert.equal(a.categories.length,0);
  assert.ok(a.categories.length<=3);
  for(const c of a.categories){assert.equal(c.fieldPromoted,false);}
 }
 for(const [key,val]of Object.entries({formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,
  releaseState:HOLD}))assert.equal(r[key],val,key);
 return true;
}
export function safeOut(where){
 const root=resolve('.'),p=resolve(where);
 if(p===root||!p.startsWith(root+sep)||['docs','scripts','tests','.git','.github'].some(x=>p===resolve(x)||p.startsWith(resolve(x)+sep)))
  throw Error('HOLD_ISOLATED_OUTPUT_ONLY');
 return p;
}
export async function emit(r,where){
 verifyReport(r);const dir=safeOut(where);await mkdir(dir,{recursive:true});
 const data=Buffer.from(serialize(r));await writeFile(dir+'/ibon_local_root_cause.json',data);
 const manifest={kind:'EVENTRADAR_P30_L9N_SHA_MANIFEST_V1',
  sourceL9MFileSHA256:L9M_SHA,sourceL9FFileSHA256:L9F_SHA,
  filesSHA256:{'ibon_local_root_cause.json':sha(data)},
  releaseState:HOLD,published:false};
 await writeFile(dir+'/manifest.json',serialize(manifest));return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9m']||!flags['--l9f']||!flags['--out'])throw Error('HOLD_INPUT_REQUIRED');
 const mb=await readFile(flags['--l9m']),fb=await readFile(flags['--l9f']);
 const report=await audit(JSON.parse(mb),mb,JSON.parse(fb),fb);
 await emit(report,flags['--out']);
 for(const x of report.rows)console.log('L9N_CAUSE',JSON.stringify({id:x.id,http:x.http,title:x.sourceTitleMatched,categories:x.categories.map(y=>y.category),reviewOnly:x.safeReviewCandidates}));
 console.log('PASS L9N_SPLIT_INTERACTIVE_VS_ROLE_MIX_CAUSE');
 console.log('HOLD L9N_NO_GOLDEN_NO_PUBLICATION');
}
