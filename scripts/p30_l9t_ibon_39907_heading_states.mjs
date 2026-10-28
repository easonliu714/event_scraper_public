#!/usr/bin/env node
/* L9-T: ibon 39907, one public Chromium navigation, 12 passive title-state
 * snapshots. No click, login, bypass, purchase, source text persistence or publication. */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {validate as validateS} from './p30_l9s_ibon_three_title_readiness.mjs';
import {observe} from './p30_l9r_ibon_title_state.mjs';
import {norm,safeOut} from './p30_l9p_ibon_control_types.mjs';
export const KIND='EVENTRADAR_P30_L9T_IBON_39907_HEADING_STATES_V1';
export const ID='39907',URL='https://ticket.ibon.com.tw/ActivityInfo/Details/'+ID;
export const N=12,MS=500,HOLD='HARD_HOLD_NO_PUBLICATION';
export const S_ZIP='3b53e69770add8a1c30324e7276ee7d931caf158b53b5c354213c5c074a0c169';
export const F_SHA='81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4';
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
export function parents(s,sb,f,fb){
 assert.deepEqual(JSON.parse(sb),s);assert.deepEqual(JSON.parse(fb),f);
 validateS(s);assert.equal(s.rows.find(x=>x.id===ID)?.state,'HOLD_COMPLETE_NONMATCH_BEFORE_STABLE_TAIL');
 assert.equal(s.parentL9FFileSHA256,F_SHA);assert.equal(s.releaseState,HOLD);
 assert.equal(sha(fb),F_SHA);
 assert.equal(f.kind,'EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1');
 assert.equal(f.releaseState,HOLD);assert.equal(f.goldenAccepted,0);assert.equal(f.published,false);
 const m=f.samples.filter(x=>x.candidateId==='ibon:'+ID);
 assert.equal(m.length,1);assert.equal(m[0].officialUrl,URL);
 assert.equal(m[0].titleParity,true);assert.ok(norm(m[0].listTitle).length>=4);
 return{title:m[0].listTitle,sSha:sha(sb),fSha:sha(fb)};
}
export function classify(x){
 if(x.exactTitleMatch)return'MATCH';
 if(x.readyState!=='complete')return'NOT_COMPLETE';
 if(x.headingCount===0)return'COMPLETE_NO_HEADING';
 if(x.titleCandidateCount===0)return'COMPLETE_NO_H1H2';
 return'COMPLETE_H1H2_NONMATCH_NOT_WRONG_EVENT_PROOF';
}
export function sample(p,title,i){const x=observe(p,title,i);return{...x,headingClass:classify(x)};}
export function analyze(t){
 assert.equal(t.length,N);
 const firstMatch=t.findIndex(x=>x.exactTitleMatch),firstComplete=t.findIndex(x=>x.readyState==='complete');
 const pre=t.filter((x,i)=>x.readyState==='complete'&&!x.exactTitleMatch&&(firstMatch<0||i<firstMatch));
 const counts={absent:pre.filter(x=>x.headingClass==='COMPLETE_NO_HEADING').length,
  noH1H2:pre.filter(x=>x.headingClass==='COMPLETE_NO_H1H2').length,
  nonmatchCandidate:pre.filter(x=>x.headingClass==='COMPLETE_H1H2_NONMATCH_NOT_WRONG_EVENT_PROOF').length};
 const tail=t.slice(-3),stableMatch=tail.every(x=>x.readyState==='complete'&&x.exactTitleMatch);
 const stableCandidate=tail.every(x=>x.readyState==='complete'&&!x.exactTitleMatch&&x.titleCandidateCount>0&&x.candidateFingerprint&&x.candidateFingerprint===tail[0].candidateFingerprint);
 const decision=counts.nonmatchCandidate?'HOLD_TRANSIENT_NONMATCH_CANDIDATE':
  counts.absent+counts.noH1H2?'HOLD_TRANSIENT_HEADING_ABSENCE':
  stableCandidate?'HOLD_STABLE_CANDIDATE_UNVERIFIED':
  stableMatch?'REVIEW_STABLE_TITLE_ONLY':'HOLD_TITLE_IDENTITY_UNRESOLVED';
 return{firstMatchIndex:firstMatch<0?null:firstMatch,firstCompleteIndex:firstComplete<0?null:firstComplete,
  preMatchCompleteCount:pre.length,preMatchClasses:counts,stableMatch,stableCandidate,decision,acceptedFields:0};
}
function probe(){
 const clip=s=>String(s??'').replace(/\s+/g,' ').trim().slice(0,130);
 const hs=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35);
 const labels=[...document.querySelectorAll('h3')].slice(0,250).filter(x=>
  clip([...x.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ')).replace(/[：:]$/u,'')==='活動日期');
 return{readyState:document.readyState,headings:hs.map(x=>clip(x.textContent)),
  candidates:hs.filter(x=>x.matches('h1,h2')).map(x=>clip(x.textContent)),dateLabelCount:labels.length};
}
export async function audit(s,sb,f,fb,browser=chromium){
 const p=parents(s,sb,f,fb),driver=await browser.launch({headless:true,args:['--no-sandbox']});
 let http=null,finalUrlExact=false,state='HOLD_BROWSER';const timeline=[];
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   const page=await ctx.newPage();
   try{
    const response=await page.goto(URL,{waitUntil:'domcontentloaded',timeout:22000});
    http=response?.status()??null;finalUrlExact=page.url()===URL;
    if(http!==200)state='HOLD_HTTP';
    else if(!finalUrlExact)state='HOLD_REDIRECT';
    else{
     for(let i=0;i<N;i++){if(i)await page.waitForTimeout(MS);timeline.push(sample(await page.evaluate(probe),p.title,i));}
     state='HOLD_REVIEW_ONLY';
    }
   }catch(e){state=e?.name==='TimeoutError'?'HOLD_TIMEOUT':'HOLD_BROWSER';}
   finally{await page.close();}
  }finally{await ctx.close();}
 }finally{await driver.close();}
 const r={kind:KIND,sourceOrigin:'EXACT_39907_PUBLIC_CHROMIUM_TWELVE_PASSIVE_SNAPSHOTS',
  parentL9SRun:40740745592,parentL9SArtifact:12838189367,parentL9SZipSHA256:S_ZIP,
  parentL9SFileSHA256:p.sSha,parentL9FFileSHA256:p.fSha,sourceId:ID,sourceUrl:URL,http,finalUrlExact,state,
  sampleCount:N,intervalMs:MS,timeline,analysis:timeline.length===N?analyze(timeline):null,
  formalFieldPromotions:0,goldenAccepted:0,published:false,writerExecuted:false,
  schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,rawHtmlPersisted:false,
  sourceTextPersisted:false,linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  releaseState:HOLD};
 validate(r);return r;
}
export function validate(r){
 assert.equal(r.kind,KIND);assert.equal(r.sourceOrigin,'EXACT_39907_PUBLIC_CHROMIUM_TWELVE_PASSIVE_SNAPSHOTS');
 assert.equal(r.parentL9SRun,40740745592);assert.equal(r.parentL9SArtifact,12838189367);
 assert.equal(r.parentL9SZipSHA256,S_ZIP);assert.equal(r.parentL9FFileSHA256,F_SHA);
 assert.match(r.parentL9SFileSHA256,/^[a-f0-9]{64}$/);
 assert.equal(r.sourceId,ID);assert.equal(r.sourceUrl,URL);assert.equal(r.sampleCount,N);assert.equal(r.intervalMs,MS);
 assert.equal(typeof r.finalUrlExact,'boolean');
 assert.ok(['HOLD_REVIEW_ONLY','HOLD_HTTP','HOLD_REDIRECT','HOLD_TIMEOUT','HOLD_BROWSER'].includes(r.state));
 if(r.state==='HOLD_REVIEW_ONLY'){
  assert.equal(r.http,200);assert.equal(r.finalUrlExact,true);assert.equal(r.timeline.length,N);
  assert.deepEqual(r.timeline.map(x=>x.index),Array.from({length:N},(_,i)=>i));
  for(const x of r.timeline){
   assert.deepEqual(Object.keys(x).sort(),['index','readyState','headingCount','titleCandidateCount','exactTitleMatch','candidateFingerprint','dateLabelCount','titleState','headingClass'].sort());
   assert.ok(['loading','interactive','complete'].includes(x.readyState));
   assert.equal(typeof x.exactTitleMatch,'boolean');
   for(const k of ['headingCount','titleCandidateCount','dateLabelCount'])assert.ok(Number.isInteger(x[k])&&x[k]>=0&&x[k]<=250);
   assert.ok(x.titleCandidateCount<=x.headingCount);
   assert.ok(x.candidateFingerprint===null||/^[a-f0-9]{16}$/.test(x.candidateFingerprint));
   assert.equal(x.headingClass,classify(x));
  }
  assert.deepEqual(r.analysis,analyze(r.timeline));assert.equal(r.analysis.acceptedFields,0);
 }else{assert.equal(r.timeline.length,0);assert.equal(r.analysis,null);}
 for(const [k,v] of Object.entries({formalFieldPromotions:0,goldenAccepted:0,published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,rawHtmlPersisted:false,sourceTextPersisted:false,linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,releaseState:HOLD}))assert.equal(r[k],v,k);
 return true;
}
export async function emit(r,path){
 validate(r);const dir=safeOut(path);await mkdir(dir,{recursive:true});
 const b=Buffer.from(json(r));await writeFile(dir+'/heading_states.json',b);
 const m={kind:'EVENTRADAR_P30_L9T_SHA_MANIFEST_V1',parentL9SZipSHA256:S_ZIP,
  parentL9SFileSHA256:r.parentL9SFileSHA256,parentL9FFileSHA256:F_SHA,
  filesSHA256:{'heading_states.json':sha(b)},releaseState:HOLD,published:false};
 await writeFile(dir+'/manifest.json',json(m));return m;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9s']||!flags['--l9f']||!flags['--out'])throw Error('HOLD_L9T_PINNED_PARENTS_REQUIRED');
 const sb=await readFile(flags['--l9s']),fb=await readFile(flags['--l9f']);
 const r=await audit(JSON.parse(sb),sb,JSON.parse(fb),fb);await emit(r,flags['--out']);
 console.log('L9T_39907',JSON.stringify({http:r.http,state:r.state,analysis:r.analysis}));
 console.log('HOLD_L9T_NO_TYPED_FIELDS_NO_GOLDEN_NO_PUBLICATION');
}