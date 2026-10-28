#!/usr/bin/env node
/* P30-L9-S: extend L9-R title readiness to three OTHER SHA-pinned ibon IDs.
 * One normal public Chromium navigation per exact ID; eight passive snapshots.
 * Never click, submit, login, bypass, persist source text/HTML/links/cookies,
 * infer dates from global text, promote fields, or publish.
 */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {validate as validateR,observe,analyze,titleState,HOLD} from './p30_l9r_ibon_title_state.mjs';
import {norm,safeOut} from './p30_l9p_ibon_control_types.mjs';
export {HOLD};
export const KIND='EVENTRADAR_P30_L9S_IBON_THREE_TITLE_READINESS_V1';
export const IDS=['39575','39907','39978'];
export const BASE='https://ticket.ibon.com.tw/ActivityInfo/Details/';
export const SAMPLES=8,INTERVAL_MS=600;
export const R_RUN=40731815454,R_ART=12835237400;
export const R_ZIP='cce75aa2bd82d4a695b58019db8e6c0cee5e703052039f3cb80210dfa70df96a';
export const F_SHA='81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4';
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=o=>JSON.stringify(o,null,2)+'\n';
export function parents(r,rb,f,fb){
 assert.deepEqual(JSON.parse(rb),r);assert.deepEqual(JSON.parse(fb),f);
 validateR(r);
 assert.equal(r.kind,'EVENTRADAR_P30_L9R_IBON_39878_TITLE_STATE_V1');
 assert.equal(r.sourceId,'39878');assert.equal(r.http,200);
 assert.equal(r.analysis.stableMatchedTail,true);
 assert.equal(r.analysis.nonmatchCompleteCount,0);
 assert.equal(r.formalFieldPromotions,0);assert.equal(r.published,false);
 assert.equal(r.releaseState,HOLD);
 assert.equal(sha(fb),F_SHA,'HOLD_L9S_F_SOURCE_SHA');
 assert.equal(f.kind,'EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1');
 assert.equal(f.additionalTitleParity,5);
 assert.equal(f.goldenAccepted,0);assert.equal(f.published,false);
 assert.equal(f.releaseState,HOLD);
 const sources=IDS.map(id=>{
  const x=f.samples.filter(z=>z.candidateId==='ibon:'+id);
  assert.equal(x.length,1,'HOLD_L9S_EXACT_ID_NOT_IN_PINNED_SOURCE');
  assert.equal(x[0].officialUrl,BASE+id);
  assert.equal(x[0].titleParity,true);
  assert.ok(norm(x[0].listTitle).length>=4);
  return{id,url:BASE+id,title:x[0].listTitle};
 });
 return{sources,rSha:sha(rb),fSha:sha(fb)};
}
export function readiness(a){
 if(a.stableMatchedTail&&a.nonmatchCompleteCount===0)
  return'REVIEW_STABLE_TITLE_READY_NO_FIELD_PROMOTION';
 if(a.stableMatchedTail&&a.nonmatchCompleteCount>0)
  return'HOLD_COMPLETE_NONMATCH_BEFORE_STABLE_TAIL';
 if(a.stableUnmatchedCandidateTail)return'HOLD_STABLE_UNMATCHED_CANDIDATE';
 return'HOLD_TITLE_READINESS_UNRESOLVED';
}
function pageProbe(){
 const clip=s=>String(s??'').replace(/\s+/g,' ').trim().slice(0,130);
 const h=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35);
 const labels=[...document.querySelectorAll('h3')].slice(0,250).filter(x=>
  clip([...x.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ')).replace(/[：:]$/u,'')==='活動日期');
 return{readyState:document.readyState,headings:h.map(x=>clip(x.textContent)),
  candidates:h.filter(x=>x.matches('h1,h2')).map(x=>clip(x.textContent)),
  dateLabelCount:labels.length};
}
export async function audit(r,rb,f,fb,browser=chromium){
 const proof=parents(r,rb,f,fb);
 const driver=await browser.launch({headless:true,args:['--no-sandbox']});
 const rows=[];
 try{
  const context=await driver.newContext({viewport:{width:1280,height:800},
   javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   for(const source of proof.sources){
    const row={id:source.id,url:source.url,http:null,finalUrlExact:false,
     state:'HOLD_NOT_VISITED',timeline:[],analysis:null};
    rows.push(row);
    const page=await context.newPage();
    try{
     const response=await page.goto(source.url,{waitUntil:'domcontentloaded',timeout:22000});
     row.http=response?.status()??null;
     row.finalUrlExact=page.url()===source.url;
     if(!row.finalUrlExact){row.state='HOLD_REDIRECT';continue;}
     if(row.http!==200){row.state='HOLD_HTTP';continue;}
     for(let i=0;i<SAMPLES;i++){
      if(i)await page.waitForTimeout(INTERVAL_MS);
      row.timeline.push(observe(await page.evaluate(pageProbe),source.title,i));
     }
     row.analysis=analyze(row.timeline);
     row.state=readiness(row.analysis);
    }catch(e){row.state=e?.name==='TimeoutError'?'HOLD_TIMEOUT':'HOLD_BROWSER';}
    finally{await page.close();}
   }
  }finally{await context.close();}
 }finally{await driver.close();}
 const report={kind:KIND,sourceOrigin:'THREE_EXACT_IBON_PUBLIC_CHROMIUM_EIGHT_PASSIVE_SNAPSHOTS',
  parentL9RRun:R_RUN,parentL9RArtifact:R_ART,parentL9RZipSHA256:R_ZIP,
  parentL9RFileSHA256:proof.rSha,parentL9FFileSHA256:proof.fSha,
  sampleCount:SAMPLES,intervalMs:INTERVAL_MS,rows,
  stableTitleReviewCount:rows.filter(x=>x.state==='REVIEW_STABLE_TITLE_READY_NO_FIELD_PROMOTION').length,
  formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,sourceTextPersisted:false,
  linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
 validate(report);return report;
}
export function validate(r){
 assert.equal(r.kind,KIND);assert.equal(r.sourceOrigin,'THREE_EXACT_IBON_PUBLIC_CHROMIUM_EIGHT_PASSIVE_SNAPSHOTS');
 assert.equal(r.parentL9RRun,R_RUN);assert.equal(r.parentL9RArtifact,R_ART);
 assert.equal(r.parentL9RZipSHA256,R_ZIP);assert.equal(r.parentL9FFileSHA256,F_SHA);
 assert.match(r.parentL9RFileSHA256,/^[a-f0-9]{64}$/);
 assert.equal(r.sampleCount,SAMPLES);assert.equal(r.intervalMs,INTERVAL_MS);
 assert.equal(r.rows.length,IDS.length);
 for(let i=0;i<IDS.length;i++){
  const x=r.rows[i];
  assert.deepEqual(Object.keys(x).sort(),['id','url','http','finalUrlExact','state','timeline','analysis'].sort());
  assert.equal(x.id,IDS[i]);assert.equal(x.url,BASE+IDS[i]);
  if(x.http===200&&x.finalUrlExact){
   assert.equal(x.timeline.length,SAMPLES);
   assert.deepEqual(x.timeline.map(s=>s.index),[0,1,2,3,4,5,6,7]);
   for(const s of x.timeline){
    assert.deepEqual(Object.keys(s).sort(),['index','readyState','headingCount','titleCandidateCount','exactTitleMatch','candidateFingerprint','dateLabelCount','titleState'].sort());
    assert.ok(['loading','interactive','complete'].includes(s.readyState));
    assert.equal(s.titleState,titleState(s));
    assert.equal(typeof s.exactTitleMatch,'boolean');
    for(const key of ['headingCount','titleCandidateCount','dateLabelCount'])
     assert.ok(Number.isInteger(s[key])&&s[key]>=0&&s[key]<=250);
    assert.ok(s.titleCandidateCount<=s.headingCount);
    assert.ok(s.candidateFingerprint===null||/^[a-f0-9]{16}$/.test(s.candidateFingerprint));
   }
   assert.deepEqual(x.analysis,analyze(x.timeline));
   assert.equal(x.state,readiness(x.analysis));
  }else{
   assert.equal(x.timeline.length,0);assert.equal(x.analysis,null);
   assert.ok(['HOLD_HTTP','HOLD_REDIRECT','HOLD_TIMEOUT','HOLD_BROWSER'].includes(x.state));
  }
 }
 assert.equal(r.stableTitleReviewCount,r.rows.filter(x=>x.state==='REVIEW_STABLE_TITLE_READY_NO_FIELD_PROMOTION').length);
 for(const [k,v] of Object.entries({formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,sourceTextPersisted:false,
  linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD}))
  assert.equal(r[k],v,k);
 return true;
}
export async function emit(r,path){
 validate(r);const out=safeOut(path);await mkdir(out,{recursive:true});
 const bytes=Buffer.from(json(r));await writeFile(out+'/three_title_readiness.json',bytes);
 const m={kind:'EVENTRADAR_P30_L9S_SHA_MANIFEST_V1',parentL9RZipSHA256:R_ZIP,
  parentL9RFileSHA256:r.parentL9RFileSHA256,parentL9FFileSHA256:F_SHA,
  filesSHA256:{'three_title_readiness.json':sha(bytes)},releaseState:HOLD,published:false};
 await writeFile(out+'/manifest.json',json(m));return m;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9r']||!flags['--l9f']||!flags['--out'])throw Error('HOLD_L9S_PINNED_PARENTS_REQUIRED');
 const rb=await readFile(flags['--l9r']),fb=await readFile(flags['--l9f']);
 const result=await audit(JSON.parse(rb),rb,JSON.parse(fb),fb);
 await emit(result,flags['--out']);
 for(const x of result.rows)console.log('L9S_TITLE',JSON.stringify({id:x.id,http:x.http,
  firstMatch:x.analysis?.firstMatchIndex??null,firstComplete:x.analysis?.firstCompleteIndex??null,
  nonmatchComplete:x.analysis?.nonmatchCompleteCount??null,state:x.state}));
 console.log('PASS_L9S_THREE_EXACT_TITLE_READINESS_REVIEW_ONLY');
 console.log('HOLD_L9S_NO_FIELDS_NO_GOLDEN_NO_PUBLICATION');
}