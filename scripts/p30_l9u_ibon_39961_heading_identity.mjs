#!/usr/bin/env node
/* P30-L9-U: exact ibon 39961 source identity. One bounded public list/detail
 * Chromium pair and twelve passive detail snapshots; no interaction, title
 * persistence, raw HTML, global date regex, login, purchase or publication.
 * Historical L9-H title contradiction is mandatory and NEVER auto-closed. */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {currentListCandidates,normalize,LIST_URL,DETAIL_URL,EVENT_ID} from './p30_l9i_ibon_39961_identity.mjs';

export const KIND='EVENTRADAR_P30_L9U_IBON_39961_HISTORIC_IDENTITY_V1';
export const HOLD='HARD_HOLD_NO_PUBLICATION';
export const K_KIND='EVENTRADAR_P30_L9K_IBON_39961_CROSS_WINDOW_SOURCE_V1';
export const H_KIND='EVENTRADAR_P30_L9H_IBON_LOCAL_DOM_HIERARCHY_READONLY_V1';
export const K_HEAD='30aa18a9fbe4dc7b46f9b4b2cf41a51b70f0b11a';
export const K_RUN=40673236521,K_ART=12809656497;
export const K_ZIP='c20ac82e7bd0c5a8e87530bbe126a81741fae2776058dd9394a8291c737118de';
export const H_RUN=40516301527,H_ART=12740505389;
export const H_SHA='e8a5e392e3f80ce6504df88c2564506b32d476204c01c5de139869dfd5b7965b';
export const N=12,MS=500;
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';

export function parents(k,kb,h,hb){
 assert.deepEqual(JSON.parse(kb),k);assert.deepEqual(JSON.parse(hb),h);
 assert.equal(k.kind,K_KIND);assert.equal(k.eventId,EVENT_ID);
 assert.equal(k.parentJHead,'727aea8aa673b29cd4a589c0a9ca68836fac4b92');
 assert.equal(k.parentJRun,40619619643);assert.equal(k.parentJArtifact,12786507149);
 assert.equal(k.historicHRun,H_RUN);assert.equal(k.historicHArtifact,H_ART);
 assert.equal(k.sourceHReportSHA256,H_SHA);assert.equal(sha(hb),H_SHA);
 assert.equal(k.officialListUrl,LIST_URL);assert.equal(k.officialDetailUrl,DETAIL_URL);
 assert.equal(k.decision.crossWindowStatus,'CROSS_WINDOW_THREE_MATCHES_REVIEW_ONLY');
 assert.equal(k.decision.historicalMismatchRetained,true);
 assert.equal(k.decision.priorRootCauseStillUnknown,true);
 assert.equal(k.decision.formalIdentityCertified,false);
 assert.equal(k.decision.formalReleaseEligible,false);
 assert.equal(k.currentRound.list.httpStatus,200);
 assert.equal(k.currentRound.detail.httpStatus,200);
 assert.equal(k.currentRound.listTitles.length,1);
 assert.equal(k.currentRound.decision.currentSourceParity,true);
 assert.equal(k.currentRound.decision.status,'REVIEW_ONLY_NO_RELEASE');
 assert.equal(k.releaseState,HOLD);assert.equal(k.published,false);assert.equal(k.goldenAccepted,0);
 assert.equal(h.kind,H_KIND);assert.equal(h.releaseState,HOLD);
 assert.equal(h.titleParityCount,4);assert.equal(h.sampleCount,5);
 const rows=h.rows.filter(x=>x.candidateId==='ibon:'+EVENT_ID);
 assert.equal(rows.length,1);assert.equal(rows[0].officialUrl,DETAIL_URL);
 assert.equal(rows[0].httpStatus,200);assert.equal(rows[0].titleParity,false);
 assert.equal(rows[0].status,'HOLD_TITLE_MISMATCH');
 const old=k.currentRound.listTitles[0];
 assert.ok(normalize(old).length>=4);
 return{priorTitle:old,kSha:sha(kb),hSha:sha(hb)};
}
export function validFinal(actual,expected){
 try{
  const a=new URL(actual),e=new URL(expected);
  return a.protocol==='https:'&&a.hostname==='ticket.ibon.com.tw'&&
   !a.username&&!a.password&&!a.search&&!a.hash&&
   (!a.port||a.port==='443')&&a.pathname===e.pathname;
 }catch{return false;}
}
export function listIdentity(rows){
 assert.ok(Array.isArray(rows)&&rows.length<=500);
 const found=currentListCandidates(rows);
 if(found.length===0)return{state:'HOLD_ID_NOT_IN_LIST',title:null,count:0};
 if(found.length!==1)return{state:'HOLD_AMBIGUOUS_SAME_ID',title:null,count:found.length};
 return{state:'ONE_SAME_ID_TITLE',title:found[0].title,count:1};
}
export function snapshot(p,current,prior,index){
 const h=p.headings.map(normalize).filter(Boolean);
 const c=p.candidates.map(normalize).filter(Boolean);
 const cur=normalize(current),old=normalize(prior);
 const currentMatch=c.includes(cur),priorMatch=c.includes(old);
 const state=currentMatch?'MATCH_CURRENT_H1H2':
  p.readyState!=='complete'?'NOT_COMPLETE':
  c.length===0?(h.length===0?'COMPLETE_NO_HEADING':'COMPLETE_NO_H1H2'):
  priorMatch?'HOLD_HISTORIC_ONLY_H1H2':'HOLD_OTHER_H1H2_CANDIDATE';
 return{index,readyState:p.readyState,headingCount:h.length,
  titleCandidateCount:c.length,currentMatch,priorMatch,
  candidateFingerprint:c.length?sha(Buffer.from(c.join('|'))).slice(0,16):null,
  state};
}
export function analyze(t,listSameAsK){
 assert.equal(t.length,N);
 const tail=t.slice(-3);
 const firstCurrent=t.findIndex(x=>x.currentMatch);
 const firstComplete=t.findIndex(x=>x.readyState==='complete');
 const pre=t.filter((x,i)=>x.readyState==='complete'&&!x.currentMatch&&
  (firstCurrent<0||i<firstCurrent));
 const counts={absent:pre.filter(x=>x.state==='COMPLETE_NO_HEADING').length,
  noH1H2:pre.filter(x=>x.state==='COMPLETE_NO_H1H2').length,
  historicOnly:pre.filter(x=>x.state==='HOLD_HISTORIC_ONLY_H1H2').length,
  otherCandidate:pre.filter(x=>x.state==='HOLD_OTHER_H1H2_CANDIDATE').length};
 const stableCurrent=tail.every(x=>x.readyState==='complete'&&x.currentMatch);
 const stableDifferent=tail.every(x=>x.readyState==='complete'&&!x.currentMatch&&
  x.titleCandidateCount>0&&x.candidateFingerprint&&
  x.candidateFingerprint===tail[0].candidateFingerprint);
 const decision=!listSameAsK?'HOLD_OFFICIAL_LIST_DRIFT_FROM_K':
  counts.otherCandidate||counts.historicOnly?'HOLD_COMPLETE_STATE_NONMATCH_CANDIDATE':
  stableDifferent?'HOLD_STABLE_DIFFERENT_HEADING':
  stableCurrent?'REVIEW_CURRENT_H1H2_STABLE_HISTORIC_CONFLICT_OPEN':
  'HOLD_IDENTITY_OR_HYDRATION_UNRESOLVED';
 return{firstCurrentMatchIndex:firstCurrent<0?null:firstCurrent,
  firstCompleteIndex:firstComplete<0?null:firstComplete,
  preMatchCompleteCounts:counts,stableCurrent,stableDifferent,
  currentListSameAsK:listSameAsK,decision,acceptedFields:0,
  historicalL9HMismatchStillOpen:true};
}
function listProbe(){
 const clip=x=>String(x??'').replace(/\s+/g,' ').trim().slice(0,180);
 return[...document.querySelectorAll('a[href]')].slice(0,500).map(a=>{
  const holder=a.closest("article,li,[class*='card'],[class*='Card'],[class*='item'],[class*='Item']")||
   (a.parentElement&&a.parentElement.tagName!=='BODY'?a.parentElement:a);
  return{href:a.getAttribute('href')||'',
   cardTitle:clip(holder?.querySelector('h2,h3,h4,h5')?.textContent),
   anchorTitle:clip(a.getAttribute('title')),ariaLabel:clip(a.getAttribute('aria-label')),
   anchorText:clip(a.textContent),imageAlt:clip(a.querySelector('img')?.getAttribute('alt'))};
 });
}
function detailProbe(){
 const clip=x=>String(x??'').replace(/\s+/g,' ').trim().slice(0,160);
 const heads=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35);
 return{readyState:document.readyState,headings:heads.map(x=>clip(x.textContent)),
  candidates:heads.filter(x=>x.matches('h1,h2')).map(x=>clip(x.textContent))};
}
export async function audit(k,kb,h,hb,browser=chromium){
 const p=parents(k,kb,h,hb);
 const driver=await browser.launch({headless:true,args:['--no-sandbox']});
 let listHTTP=null,detailHTTP=null,listFinal=false,detailFinal=false;
 let listState='HOLD_NOT_ATTEMPTED',detailState='HOLD_NOT_ATTEMPTED';
 let listCount=0,listSameAsK=false,navigations=0;
 const timeline=[];
 try{
  const ctx=await driver.newContext({viewport:{width:1280,height:800},javaScriptEnabled:true,
   acceptDownloads:false,permissions:[]});
  try{
   const lp=await ctx.newPage();
   let current=null;
   try{
    navigations++;
    const res=await lp.goto(LIST_URL,{waitUntil:'domcontentloaded',timeout:22000});
    listHTTP=res?.status()??null;listFinal=validFinal(lp.url(),LIST_URL);
    if(listHTTP!==200)listState='HOLD_LIST_HTTP';
    else if(!listFinal)listState='HOLD_LIST_REDIRECT';
    else{
     await lp.waitForTimeout(1600);
     const v=listIdentity(await lp.evaluate(listProbe));
     listState=v.state;listCount=v.count;current=v.title;
     if(current)listSameAsK=normalize(current)===normalize(p.priorTitle);
    }
   }catch(e){listState=e?.name==='TimeoutError'?'HOLD_LIST_TIMEOUT':'HOLD_LIST_BROWSER';}
   finally{await lp.close();}
   if(current&&listState==='ONE_SAME_ID_TITLE'){
    const dp=await ctx.newPage();
    try{
     navigations++;
     const res=await dp.goto(DETAIL_URL,{waitUntil:'domcontentloaded',timeout:22000});
     detailHTTP=res?.status()??null;detailFinal=validFinal(dp.url(),DETAIL_URL);
     if(detailHTTP!==200)detailState='HOLD_DETAIL_HTTP';
     else if(!detailFinal)detailState='HOLD_DETAIL_REDIRECT';
     else{
      detailState='HOLD_REVIEW_ONLY';
      for(let i=0;i<N;i++){
       if(i)await dp.waitForTimeout(MS);
       timeline.push(snapshot(await dp.evaluate(detailProbe),current,p.priorTitle,i));
      }
     }
    }catch(e){detailState=e?.name==='TimeoutError'?'HOLD_DETAIL_TIMEOUT':'HOLD_DETAIL_BROWSER';}
    finally{await dp.close();}
   }
  }finally{await ctx.close();}
 }finally{await driver.close();}
 const r={kind:KIND,sourceOrigin:'ONE_PUBLIC_LIST_AND_DETAIL_TWELVE_PASSIVE_H1H2_SNAPSHOTS',
  parentL9KHead:K_HEAD,parentL9KRun:K_RUN,parentL9KArtifact:K_ART,
  parentL9KZipSHA256:K_ZIP,parentL9KFileSHA256:p.kSha,
  parentL9HRun:H_RUN,parentL9HArtifact:H_ART,parentL9HFileSHA256:p.hSha,
  sourceId:EVENT_ID,listHTTP,detailHTTP,listFinal,detailFinal,listState,detailState,
  listSameIdTitleCount:listCount,listSameAsK,navigationsAttempted:navigations,
  sampleCount:N,intervalMs:MS,timeline,
  analysis:timeline.length===N?analyze(timeline,listSameAsK):null,
  historicMismatchRetained:true,formalIdentityCertified:false,
  formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,sourceTextPersisted:false,linkUrlsPersisted:false,
  screenshotsPersisted:false,cookiesPersisted:false,networkBodiesPersisted:false,
  releaseState:HOLD};
 validate(r);return r;
}
export function validate(r){
 assert.equal(r.kind,KIND);assert.equal(r.parentL9KHead,K_HEAD);
 assert.equal(r.parentL9KRun,K_RUN);assert.equal(r.parentL9KArtifact,K_ART);
 assert.equal(r.parentL9KZipSHA256,K_ZIP);
 assert.match(r.parentL9KFileSHA256,/^[a-f0-9]{64}$/);
 assert.equal(r.parentL9HRun,H_RUN);assert.equal(r.parentL9HArtifact,H_ART);
 assert.equal(r.parentL9HFileSHA256,H_SHA);assert.equal(r.sourceId,EVENT_ID);
 assert.ok([1,2].includes(r.navigationsAttempted));
 assert.equal(r.sampleCount,N);assert.equal(r.intervalMs,MS);
 assert.ok(r.listSameIdTitleCount>=0&&r.listSameIdTitleCount<=4);
 if(r.timeline.length){
  assert.equal(r.detailState,'HOLD_REVIEW_ONLY');
  assert.equal(r.listState,'ONE_SAME_ID_TITLE');
  assert.equal(r.listHTTP,200);assert.equal(r.detailHTTP,200);
  assert.equal(r.listFinal,true);assert.equal(r.detailFinal,true);
  assert.equal(r.timeline.length,N);
  for(let i=0;i<N;i++){
   const x=r.timeline[i];assert.equal(x.index,i);
   assert.ok(['loading','interactive','complete'].includes(x.readyState));
   assert.ok(x.headingCount>=x.titleCandidateCount);
   assert.ok(x.headingCount<=35&&x.titleCandidateCount<=35);
   assert.equal(typeof x.currentMatch,'boolean');assert.equal(typeof x.priorMatch,'boolean');
   assert.ok(x.candidateFingerprint===null||/^[a-f0-9]{16}$/.test(x.candidateFingerprint));
   assert.ok(['MATCH_CURRENT_H1H2','NOT_COMPLETE','COMPLETE_NO_HEADING',
    'COMPLETE_NO_H1H2','HOLD_HISTORIC_ONLY_H1H2',
    'HOLD_OTHER_H1H2_CANDIDATE'].includes(x.state));
  }
  assert.deepEqual(r.analysis,analyze(r.timeline,r.listSameAsK));
 }else{assert.equal(r.analysis,null);}
 assert.equal(r.historicMismatchRetained,true);assert.equal(r.formalIdentityCertified,false);
 for(const[k,v]of Object.entries({formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,sourceTextPersisted:false,linkUrlsPersisted:false,
  screenshotsPersisted:false,cookiesPersisted:false,networkBodiesPersisted:false,
  releaseState:HOLD}))assert.equal(r[k],v,k);
 return true;
}
export function safeOut(path){
 const root=resolve('.'),target=resolve(path);
 if(target===root||!target.startsWith(root+sep)||
  ['docs','scripts','tests','schemas','.github','.git'].some(x=>target===resolve(x)||target.startsWith(resolve(x)+sep)))
  throw Error('HOLD_L9U_OUTPUT_SCOPE');
 return target;
}
export async function emit(r,path){
 validate(r);const dir=safeOut(path);await mkdir(dir,{recursive:true});
 const bytes=Buffer.from(json(r));await writeFile(dir+'/identity_heading_states.json',bytes);
 const manifest={kind:'EVENTRADAR_P30_L9U_SHA_MANIFEST_V1',
  parentL9KZipSHA256:K_ZIP,parentL9KFileSHA256:r.parentL9KFileSHA256,
  parentL9HFileSHA256:H_SHA,
  filesSHA256:{'identity_heading_states.json':sha(bytes)},
  releaseState:HOLD,published:false};
 await writeFile(dir+'/manifest.json',json(manifest));return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9k']||!flags['--l9h']||!flags['--out'])throw Error('HOLD_L9U_PARENTS_REQUIRED');
 const kb=await readFile(flags['--l9k']),hb=await readFile(flags['--l9h']);
 const r=await audit(JSON.parse(kb),kb,JSON.parse(hb),hb);
 await emit(r,flags['--out']);
 console.log('L9U_39961',JSON.stringify({listHTTP:r.listHTTP,detailHTTP:r.detailHTTP,
  listState:r.listState,detailState:r.detailState,analysis:r.analysis}));
 console.log('HOLD_L9U_HISTORIC_MISMATCH_OPEN_NO_FIELDS_NO_PUBLICATION');
}