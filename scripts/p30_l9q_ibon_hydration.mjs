#!/usr/bin/env node
/* P30-L9-Q: one bounded, normal public Chromium navigation for ibon 39878.
 * Observe six passive snapshots of H3 label hydration and immediate sibling
 * controls. No click, value reading, raw HTML, screenshot, extracted URLs,
 * global date regex, publication, or production file mutation.
 */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {norm,safeOut} from './p30_l9p_ibon_control_types.mjs';
export const KIND='EVENTRADAR_P30_L9Q_IBON_39878_HYDRATION_V1';
export const ID='39878';
export const URL='https://ticket.ibon.com.tw/ActivityInfo/Details/'+ID;
export const HOLD='HARD_HOLD_NO_PUBLICATION';
export const P_RUN=40711541169,P_ART=12826851317;
export const P_ZIP='24fbff9dc7d6a2723731a7968e4e13a8740dc1d1cb766ed86f089ddba4cb3f03';
export const F_RUN=40494326021;
export const F_SHA='81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4';
export const SAMPLES=6,INTERVAL_MS=700;
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
export function parents(p,pb,f,fb){
 assert.deepEqual(JSON.parse(pb),p);assert.deepEqual(JSON.parse(fb),f);
 assert.equal(sha(fb),F_SHA,'HOLD_L9Q_F_SOURCE_SHA');
 assert.equal(p.kind,'EVENTRADAR_P30_L9P_IBON_LOCAL_CONTROL_TYPES_V1');
 assert.equal(p.sampleCount,4);assert.equal(p.releaseState,HOLD);
 assert.equal(p.formalFieldPromotions,0);assert.equal(p.goldenAccepted,0);
 assert.equal(p.published,false);assert.equal(p.rows.length,4);
 assert.deepEqual(p.rows.map(x=>x.id),['39575','39878','39907','39978']);
 const old=p.rows.find(x=>x.id===ID);
 assert.equal(old.url,URL);assert.equal(old.http,200);
 assert.equal(old.stableTitle,true);assert.equal(old.controlStable,false);
 assert.equal(old.firstControlCause,'HOLD_LABEL_COUNT_DRIFT');
 assert.equal(old.secondControlCause,'HOLD_FORM_INPUT_OR_SELECT');
 assert.equal(f.kind,'EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1');
 assert.equal(f.published,false);assert.equal(f.releaseState,HOLD);
 const matches=f.samples.filter(x=>x.candidateId==='ibon:'+ID);
 assert.equal(matches.length,1);assert.equal(matches[0].officialUrl,URL);
 assert.equal(matches[0].titleParity,true);
 const title=matches[0].listTitle;
 assert.ok(norm(title).length>=4);
 return{title,pSha:sha(pb),fSha:sha(fb)};
}
export function controlKind(s){
 if(s.labelCount!==1)return'HOLD_LABEL_ABSENT_OR_DUPLICATE';
 if(!s.siblingTag)return'HOLD_NO_ADJACENT_REGION';
 if(s.controlCount>0)return'HOLD_WIDGET_CONTROLS_UNTYPED';
 if(s.directTextPresent)return'HOLD_DIRECT_TEXT_UNTYPED';
 return'HOLD_EMPTY_LOCAL_REGION';
}
export function signature(s){
 return [s.labelCount,s.siblingTag,s.directTextPresent,s.controlCount,
  s.anchorCount,s.buttonCount,s.inputCount,s.formCount,s.selectCount,
  s.roleButtonCount].join('|');
}
export function analyze(snapshots){
 assert.equal(snapshots.length,SAMPLES);
 const firstSeen=snapshots.findIndex(x=>x.labelCount===1);
 const firstIndex=firstSeen<0?null:firstSeen;
 const hydrated=firstSeen>0&&snapshots.slice(0,firstSeen).some(x=>x.labelCount===0);
 const last=snapshots.at(-1),tail=snapshots.slice(-3);
 const stableTail=tail.every(x=>x.titleMatch&&x.labelCount===1&&signature(x)===signature(last));
 const titleAll=snapshots.every(x=>x.titleMatch);
 const anyControls=snapshots.some(x=>x.controlCount>0);
 const anyDirectText=snapshots.some(x=>x.directTextPresent);
 const allReadyComplete=snapshots.every(x=>x.readyState==='complete');
 let decision='HOLD_LABEL_NOT_STABLE';
 if(!titleAll)decision='HOLD_SOURCE_TITLE_PARITY_DRIFT';
 else if(!stableTail)decision='HOLD_RENDER_HYDRATION_NOT_STABLE';
 else decision=controlKind(last);
 return{firstLabelIndex:firstIndex,hydrationObserved:hydrated,
  stableTail,titleAll,allReadyComplete,anyControls,anyDirectText,
  lastControlKind:controlKind(last),decision,acceptedFields:0};
}
function pageProbe(){
 const clip=s=>String(s??'').replace(/\s+/g,' ').trim().slice(0,130);
 const headings=[...document.querySelectorAll('h1,h2,h3,h4')].slice(0,35).map(x=>clip(x.textContent));
 const labels=[...document.querySelectorAll('h3')].slice(0,250).filter(x=>
  clip([...x.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ')).replace(/[：:]$/u,'')==='活動日期');
 const sibling=labels.length===1?labels[0].nextElementSibling:null;
 const nodes=sibling?[sibling,...sibling.querySelectorAll('a,button,form,input,select,[role="button"]')].slice(0,32):[];
 const count=selector=>nodes.filter(x=>x.matches(selector)).length;
 return{headings,readyState:document.readyState,labelCount:labels.length,
  siblingTag:sibling?.tagName??null,
  directTextPresent:!!sibling&&[...sibling.childNodes].some(n=>n.nodeType===3&&clip(n.textContent).length>0),
  anchorCount:count('a'),buttonCount:count('button'),formCount:count('form'),
  inputCount:count('input'),selectCount:count('select'),
  roleButtonCount:count('[role="button"]'),
  controlCount:count('a,button,form,input,select,[role="button"]')};
}
export async function audit(p,pb,f,fb,browser=chromium){
 const proof=parents(p,pb,f,fb);
 const driver=await browser.launch({headless:true,args:['--no-sandbox']});
 let http=null;const timeline=[];
 try{
  const context=await driver.newContext({viewport:{width:1280,height:800},
   javaScriptEnabled:true,acceptDownloads:false,permissions:[]});
  try{
   const page=await context.newPage();
   try{
    const response=await page.goto(URL,{waitUntil:'domcontentloaded',timeout:22000});
    http=response?.status()??null;
    assert.equal(page.url(),URL,'HOLD_L9Q_REDIRECT');
    assert.equal(http,200,'HOLD_L9Q_HTTP');
    for(let i=0;i<SAMPLES;i++){
     if(i)await page.waitForTimeout(INTERVAL_MS);
     const {headings,...observation}=await page.evaluate(pageProbe);
     timeline.push({index:i,...observation,
      titleMatch:headings.some(x=>norm(x)===norm(proof.title))});
    }
   }finally{await page.close();}
  }finally{await context.close();}
 }finally{await driver.close();}
 const analysis=analyze(timeline);
 const report={kind:KIND,sourceOrigin:'ONE_OFFICIAL_NORMAL_CHROMIUM_SIX_PASSIVE_SNAPSHOTS',
  parentL9PRun:P_RUN,parentL9PArtifact:P_ART,parentL9PZipSHA256:P_ZIP,
  parentL9PFileSHA256:proof.pSha,parentL9FRun:F_RUN,parentL9FFileSHA256:proof.fSha,
  sourceId:ID,sourceUrl:URL,http,sampleCount:SAMPLES,intervalMs:INTERVAL_MS,
  timeline,analysis,formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN',
  formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,sourceTextPersisted:false,linkUrlsPersisted:false,
  screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
 validate(report);return report;
}
export function validate(r){
 assert.equal(r.kind,KIND);assert.equal(r.sourceId,ID);assert.equal(r.sourceUrl,URL);
 assert.equal(r.http,200);assert.equal(r.sampleCount,SAMPLES);
 assert.equal(r.intervalMs,INTERVAL_MS);assert.equal(r.timeline.length,SAMPLES);
 assert.deepEqual(r.timeline.map(x=>x.index),[0,1,2,3,4,5]);
 for(const x of r.timeline){
  assert.ok(['loading','interactive','complete'].includes(x.readyState));
  assert.equal(typeof x.titleMatch,'boolean');
  assert.equal(typeof x.directTextPresent,'boolean');
  assert.ok(Number.isInteger(x.labelCount)&&x.labelCount>=0&&x.labelCount<=250);
  assert.ok(x.siblingTag===null||/^[A-Z]{1,16}$/.test(x.siblingTag));
  for(const k of ['controlCount','anchorCount','buttonCount','formCount','inputCount','selectCount','roleButtonCount'])
   assert.ok(Number.isInteger(x[k])&&x[k]>=0&&x[k]<=32,k);
  assert.ok(!Object.keys(x).some(k=>/href|html|cookie|date|price|value|text|url/i.test(k)&&k!=='directTextPresent'));
 }
 assert.deepEqual(r.analysis,analyze(r.timeline));
 assert.ok(r.analysis.decision.startsWith('HOLD_'));
 assert.equal(r.analysis.acceptedFields,0);
 assert.equal(r.formalDate,null);assert.equal(r.formalPrice,null);
 assert.equal(r.ticketStatus,'UNKNOWN');
 for(const [key,val] of Object.entries({formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,sourceTextPersisted:false,
  linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD}))
  assert.equal(r[key],val,key);
 return true;
}
export async function emit(r,where){
 validate(r);const dir=safeOut(where);await mkdir(dir,{recursive:true});
 const bytes=Buffer.from(json(r));await writeFile(dir+'/ibon_39878_hydration.json',bytes);
 const manifest={kind:'EVENTRADAR_P30_L9Q_SHA_MANIFEST_V1',
  parentL9PZipSHA256:P_ZIP,parentL9PFileSHA256:r.parentL9PFileSHA256,
  parentL9FFileSHA256:F_SHA,
  filesSHA256:{'ibon_39878_hydration.json':sha(bytes)},
  releaseState:HOLD,published:false};
 await writeFile(dir+'/manifest.json',json(manifest));return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const flags={};for(let i=2;i<process.argv.length;i+=2)flags[process.argv[i]]=process.argv[i+1];
 if(!flags['--l9p']||!flags['--l9f']||!flags['--out'])throw Error('HOLD_L9Q_TWO_PINNED_PARENTS_REQUIRED');
 const pb=await readFile(flags['--l9p']),fb=await readFile(flags['--l9f']);
 const r=await audit(JSON.parse(pb),pb,JSON.parse(fb),fb);
 await emit(r,flags['--out']);
 console.log('L9Q_39878',JSON.stringify({http:r.http,titleAll:r.analysis.titleAll,
  firstLabelIndex:r.analysis.firstLabelIndex,hydrationObserved:r.analysis.hydrationObserved,
  stableTail:r.analysis.stableTail,lastControlKind:r.analysis.lastControlKind,
  decision:r.analysis.decision}));
 console.log('PASS_L9Q_ONE_BOUNDED_SOURCE_SIX_PASSIVE_SNAPSHOTS');
 console.log('HOLD_L9Q_NO_TYPED_FIELDS_NO_GOLDEN_NO_PUBLICATION');
}
