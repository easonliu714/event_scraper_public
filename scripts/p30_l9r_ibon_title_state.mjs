#!/usr/bin/env node
/* P30-L9-R: distinguish missing/not-ready heading from persistent nonmatching
 * title candidates for exact ibon 39878. One normal public navigation, eight
 * passive observations. No clicks, value extraction, raw text/HTML persistence,
 * screenshots, global date regex, login, purchase, or production writes.
 */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {validate as validateQ, KIND as Q_KIND, ID, URL, HOLD} from './p30_l9q_ibon_hydration.mjs';
import {norm,safeOut} from './p30_l9p_ibon_control_types.mjs';
export const KIND='EVENTRADAR_P30_L9R_IBON_39878_TITLE_STATE_V1';
export const Q_RUN=40721117824,Q_ART=12829898767;
export const Q_ZIP='0e07aec0a6c8a0524457c58e782906d799e3a7f773d084e876bcf1aaddd3ab48';
export const F_SHA='81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4';
export const SAMPLES=8,INTERVAL_MS=650;
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
export function parents(q,qb,f,fb){
 assert.deepEqual(JSON.parse(qb),q);assert.deepEqual(JSON.parse(fb),f);
 validateQ(q);assert.equal(q.kind,Q_KIND);
 assert.equal(q.sourceId,ID);assert.equal(q.sourceUrl,URL);assert.equal(q.http,200);
 assert.equal(q.sampleCount,6);assert.equal(q.analysis.titleAll,false);
 assert.equal(q.formalFieldPromotions,0);assert.equal(q.goldenAccepted,0);
 assert.equal(q.published,false);assert.equal(q.releaseState,HOLD);
 assert.equal(sha(fb),F_SHA,'HOLD_L9R_F_SOURCE_SHA');
 assert.equal(f.kind,'EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1');
 assert.equal(f.published,false);assert.equal(f.releaseState,HOLD);
 const m=f.samples.filter(x=>x.candidateId==='ibon:'+ID);
 assert.equal(m.length,1);assert.equal(m[0].officialUrl,URL);
 assert.equal(m[0].titleParity,true);
 assert.ok(norm(m[0].listTitle).length>=4);
 return{title:m[0].listTitle,qSha:sha(qb),fSha:sha(fb)};
}
export function titleState(s){
 if(s.exactTitleMatch)return'MATCH';
 if(s.headingCount===0)return'HOLD_HEADING_ABSENT';
 if(s.readyState!=='complete')return'HOLD_DOCUMENT_NOT_COMPLETE';
 if(s.titleCandidateCount===0)return'HOLD_NO_H1_H2_CANDIDATE';
 return'HOLD_UNMATCHED_H1_H2_CANDIDATE';
}
export function observe(p,title,index){
 const h=p.headings.map(norm).filter(Boolean),c=p.candidates.map(norm).filter(Boolean);
 const x={index,readyState:p.readyState,headingCount:h.length,
  titleCandidateCount:c.length,exactTitleMatch:h.includes(norm(title)),
  candidateFingerprint:c.length?sha(Buffer.from(c.join('|'))).slice(0,16):null,
  dateLabelCount:p.dateLabelCount};
 return{...x,titleState:titleState(x)};
}
export function analyze(t){
 assert.equal(t.length,SAMPLES);
 const firstMatchIndex=t.findIndex(x=>x.exactTitleMatch);
 const firstCompleteIndex=t.findIndex(x=>x.readyState==='complete');
 const tail=t.slice(-3);
 const stableMatchedTail=tail.every(x=>x.readyState==='complete'&&x.exactTitleMatch);
 const stableUnmatchedCandidateTail=tail.every(x=>x.readyState==='complete'&&
  !x.exactTitleMatch&&x.titleCandidateCount>0&&x.candidateFingerprint!==null&&
  x.candidateFingerprint===tail[0].candidateFingerprint);
 const earlyAbsentOrNotReady=t.some((x,i)=>i<(firstMatchIndex<0?SAMPLES:firstMatchIndex)&&
  (x.titleState==='HOLD_HEADING_ABSENT'||x.titleState==='HOLD_DOCUMENT_NOT_COMPLETE'));
 const nonmatchCompleteCount=t.filter(x=>x.readyState==='complete'&&!x.exactTitleMatch).length;
 const decision=stableMatchedTail?'HOLD_TRANSIENT_TITLE_RENDER_NO_FIELD_PROMOTION':
  stableUnmatchedCandidateTail?'HOLD_PERSISTENT_NONMATCH_CANDIDATE_NOT_PROVEN':
  'HOLD_TITLE_IDENTITY_UNRESOLVED';
 return{firstMatchIndex:firstMatchIndex<0?null:firstMatchIndex,
  firstCompleteIndex:firstCompleteIndex<0?null:firstCompleteIndex,
  earlyAbsentOrNotReady,stableMatchedTail,stableUnmatchedCandidateTail,
  nonmatchCompleteCount,decision,acceptedFields:0};
}
function pageProbe(){
 const clip=s=>String(s??'').replace(/\s+/g,' ').trim().slice(0,130);
 const heads=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35);
 const labels=[...document.querySelectorAll('h3')].slice(0,250).filter(x=>
  clip([...x.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ')).replace(/[：:]$/u,'')==='活動日期');
 return{readyState:document.readyState,headings:heads.map(x=>clip(x.textContent)),
  candidates:heads.filter(x=>x.matches('h1,h2')).map(x=>clip(x.textContent)),
  dateLabelCount:labels.length};
}
export async function audit(q,qb,f,fb,browser=chromium){
 const proof=parents(q,qb,f,fb),driver=await browser.launch({headless:true,args:['--no-sandbox']});
 let http=null;const timeline=[];
 try{
  const context=await driver.newContext({viewport:{width:1280,height:800},
   javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   const page=await context.newPage();
   try{
    const response=await page.goto(URL,{waitUntil:'domcontentloaded',timeout:22000});
    http=response?.status()??null;
    assert.equal(page.url(),URL,'HOLD_L9R_REDIRECT');
    assert.equal(http,200,'HOLD_L9R_HTTP');
    for(let i=0;i<SAMPLES;i++){
     if(i)await page.waitForTimeout(INTERVAL_MS);
     const probe=await page.evaluate(pageProbe);
     timeline.push(observe(probe,proof.title,i));
    }
   }finally{await page.close();}
  }finally{await context.close();}
 }finally{await driver.close();}
 const report={kind:KIND,sourceOrigin:'ONE_NORMAL_OFFICIAL_CHROMIUM_EIGHT_PASSIVE_TITLE_OBSERVATIONS',
  parentL9QRun:Q_RUN,parentL9QArtifact:Q_ART,parentL9QZipSHA256:Q_ZIP,
  parentL9QFileSHA256:proof.qSha,parentL9FFileSHA256:proof.fSha,
  sourceId:ID,sourceUrl:URL,http,sampleCount:SAMPLES,intervalMs:INTERVAL_MS,
  timeline,analysis:analyze(timeline),formalDate:null,formalPrice:null,
  ticketStatus:'UNKNOWN',formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,
  notifierExecuted:false,mergeExecuted:false,rawHtmlPersisted:false,
  sourceTextPersisted:false,linkUrlsPersisted:false,screenshotsPersisted:false,
  cookiesPersisted:false,existingAndroid44Preserved:true,
  l8CoreAndroidPassPreserved:true,releaseState:HOLD};
 validate(report);return report;
}
export function validate(r){
 assert.equal(r.kind,KIND);assert.equal(r.sourceId,ID);assert.equal(r.sourceUrl,URL);
 assert.equal(r.http,200);assert.equal(r.sampleCount,SAMPLES);
 assert.equal(r.intervalMs,INTERVAL_MS);assert.equal(r.timeline.length,SAMPLES);
 assert.deepEqual(r.timeline.map(x=>x.index),[0,1,2,3,4,5,6,7]);
 for(const x of r.timeline){
  assert.ok(['loading','interactive','complete'].includes(x.readyState));
  assert.equal(typeof x.exactTitleMatch,'boolean');
  for(const k of ['headingCount','titleCandidateCount','dateLabelCount'])
   assert.ok(Number.isInteger(x[k])&&x[k]>=0&&x[k]<=250,k);
  assert.ok(x.titleCandidateCount<=x.headingCount);
  assert.ok(x.candidateFingerprint===null||/^[a-f0-9]{16}$/.test(x.candidateFingerprint));
  assert.equal(x.titleState,titleState(x));
  assert.deepEqual(Object.keys(x).sort(),
   ['index','readyState','headingCount','titleCandidateCount','exactTitleMatch',
    'candidateFingerprint','dateLabelCount','titleState'].sort());
 }
 assert.deepEqual(r.analysis,analyze(r.timeline));
 assert.ok(r.analysis.decision.startsWith('HOLD_'));
 assert.equal(r.analysis.acceptedFields,0);
 assert.equal(r.parentL9QRun,Q_RUN);assert.equal(r.parentL9QArtifact,Q_ART);
 assert.equal(r.parentL9QZipSHA256,Q_ZIP);
 assert.equal(r.parentL9FFileSHA256,F_SHA);
 assert.equal(r.formalDate,null);assert.equal(r.formalPrice,null);
 assert.equal(r.ticketStatus,'UNKNOWN');
 for(const [k,v] of Object.entries({formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,
  notifierExecuted:false,mergeExecuted:false,rawHtmlPersisted:false,
  sourceTextPersisted:false,linkUrlsPersisted:false,screenshotsPersisted:false,
  cookiesPersisted:false,existingAndroid44Preserved:true,
  l8CoreAndroidPassPreserved:true,releaseState:HOLD}))assert.equal(r[k],v,k);
 return true;
}
export async function emit(r,where){
 validate(r);const dir=safeOut(where);await mkdir(dir,{recursive:true});
 const bytes=Buffer.from(json(r));await writeFile(dir+'/ibon_39878_title_state.json',bytes);
 const m={kind:'EVENTRADAR_P30_L9R_SHA_MANIFEST_V1',parentL9QZipSHA256:Q_ZIP,
  parentL9QFileSHA256:r.parentL9QFileSHA256,parentL9FFileSHA256:F_SHA,
  filesSHA256:{'ibon_39878_title_state.json':sha(bytes)},
  releaseState:HOLD,published:false};
 await writeFile(dir+'/manifest.json',json(m));return m;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9q']||!flags['--l9f']||!flags['--out'])throw Error('HOLD_L9R_TWO_PINNED_PARENTS_REQUIRED');
 const qb=await readFile(flags['--l9q']),fb=await readFile(flags['--l9f']);
 const r=await audit(JSON.parse(qb),qb,JSON.parse(fb),fb);
 await emit(r,flags['--out']);
 console.log('L9R_39878',JSON.stringify({http:r.http,
  firstMatchIndex:r.analysis.firstMatchIndex,
  firstCompleteIndex:r.analysis.firstCompleteIndex,
  earlyAbsentOrNotReady:r.analysis.earlyAbsentOrNotReady,
  stableMatchedTail:r.analysis.stableMatchedTail,
  stableUnmatchedCandidateTail:r.analysis.stableUnmatchedCandidateTail,
  nonmatchCompleteCount:r.analysis.nonmatchCompleteCount,
  decision:r.analysis.decision}));
 console.log('PASS_L9R_EIGHT_PASSIVE_TITLE_STATE_SNAPSHOTS');
 console.log('HOLD_L9R_NO_TYPED_FIELDS_NO_GOLDEN_NO_PUBLICATION');
}
