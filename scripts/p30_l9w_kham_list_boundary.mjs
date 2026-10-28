#!/usr/bin/env node
/* P30-L9-W: one normal public Kham Chromium navigation, bounded static HTML
 * versus rendered DOM list-anchor comparison. No clicks, login, bypass,
 * event/date/price extraction, raw source persistence or production writes. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';

export const KIND='EVENTRADAR_P30_L9W_KHAM_LIST_BOUNDARY_V1';
export const RELEASE='HARD_HOLD_NO_PUBLICATION';
export const ENTRY='https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205';
export const STATUS_BLOB='e19ca37c4c80c10b7278d0813b8ff1047535d124';
export const L7B_SHA='e07c01a5d36ab0c950c45fb26e5fdd270103b4013bbf62a00c48291fee5f595a';
export const L7B_ART='8ad3a6c8d0b3259ef9187830a33455365a8ff4c7bc30061653345d74cef758c6';
export const PARENT='46dd6ddade398603cca4fc6f8dbb8f644ce64d3c';
export const N=4,INTERVAL=800,MAX_LINKS=1200;
const sha=b=>createHash('sha256').update(b).digest('hex');
const gitBlob=b=>createHash('sha1').update(Buffer.concat([Buffer.from('blob '+b.length+'\0'),b])).digest('hex');
const j=x=>JSON.stringify(x,null,2)+'\n';

export function allowed(url) {
  try {
    const u=new URL(url);
    return u.protocol==='https:'&&!u.username&&!u.password&&
      (!u.port||u.port==='443')&&
      (u.hostname==='kham.com.tw'||u.hostname.endsWith('.kham.com.tw'));
  }catch{return false;}
}
export function links(hrefs,base) {
  assert.ok(Array.isArray(hrefs)&&hrefs.length<=MAX_LINKS);
  const found=new Set();
  const stats={anchors:hrefs.length,detailUnique:0,detailRepeated:0,
    categoryLinks:0,javascriptLinks:0,offsiteLinks:0,otherLinks:0};
  for(const raw of hrefs) {
    if(typeof raw!=='string'||raw.length>2048){stats.otherLinks++;continue;}
    if(/^\s*javascript:/i.test(raw)){stats.javascriptLinks++;continue;}
    let u;
    try{u=new URL(raw,base);}catch{stats.otherLinks++;continue;}
    if(!allowed(u.href)){stats.offsiteLinks++;continue;}
    if(/UTK0201/i.test(u.pathname)){
      const key=u.origin+u.pathname+u.search;
      if(found.has(key))stats.detailRepeated++;
      else found.add(key);
    } else if(/UTK0101/i.test(u.pathname))stats.categoryLinks++;
    else stats.otherLinks++;
  }
  stats.detailUnique=found.size;
  return stats;
}
export function parents(statusBytes,l7bBytes,manifest) {
  assert.equal(gitBlob(statusBytes),STATUS_BLOB,'HOLD_L9W_STATUS_BLOB');
  assert.equal(sha(l7bBytes),L7B_SHA,'HOLD_L9W_L7B_SHA');
  assert.equal(manifest.filesSHA256?.['platform_diagnostics.json'],L7B_SHA,'HOLD_L9W_L7B_MANIFEST');
  assert.equal(manifest.sourceMainSHA,'fc4f963247d68eed29425808cc14e7250f312d05');
  const status=JSON.parse(statusBytes),diag=JSON.parse(l7bBytes);
  assert.equal(status.kind,'EVENTRADAR_PUBLIC_PLATFORM_ENGINEERING_STATUS_V1');
  assert.equal(status.production.eventFeedReleaseState,RELEASE);
  assert.equal(status.production.goldenAccepted,0);
  assert.equal(diag.kind,'EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1');
  assert.equal(diag.published,false);
  const a=status.platforms.filter(x=>x.platform==='寬宏');
  const b=diag.platforms.filter(x=>x.platform==='寬宏');
  assert.equal(a.length,1);assert.equal(b.length,1);
  assert.equal(a[0].baseline.httpStatus,200);
  assert.equal(a[0].baseline.listCandidates,0);
  assert.equal(b[0].http.httpStatus,200);
  assert.equal(b[0].listCandidateCount,0);
  return {historicalHTTP:200,historicalList:0,statusBlob:STATUS_BLOB,l7bReportSha:L7B_SHA};
}
export function decide(http,staticStats,frames,finalAllowed,staticAvailable) {
  if(!finalAllowed)return 'HOLD_UNSAFE_OR_OFFSITE_FINAL';
  if(http!==200)return 'HOLD_HTTP_NOT_200';
  if(!staticAvailable)return 'HOLD_STATIC_RESPONSE_UNAVAILABLE';
  if(frames.length!==N)return 'HOLD_INCOMPLETE_RENDER_SNAPSHOTS';
  const latest=frames.at(-1);
  const tail=frames.slice(-2);
  if(latest.ready!=='complete')return 'HOLD_RENDER_NOT_COMPLETE';
  if(!tail.every(x=>x.links.detailUnique===latest.links.detailUnique))
    return 'HOLD_RENDER_NOT_STABLE';
  if(staticStats.detailUnique===0&&latest.links.detailUnique>0)
    return 'REVIEW_CURRENT_JS_DETAIL_LINKS_HISTORIC_ZERO';
  if(staticStats.detailUnique>0&&latest.links.detailUnique>0)
    return 'REVIEW_CURRENT_STATIC_DETAIL_LINKS_HISTORIC_ZERO';
  if(staticStats.detailUnique>0&&latest.links.detailUnique===0)
    return 'HOLD_STATIC_DETAIL_ANCHORS_REMOVED';
  if(latest.forms>0||latest.onclickElements>0||latest.frames>0)
    return 'HOLD_NON_ANCHOR_OR_INTERACTIVE_STRUCTURE';
  return 'HOLD_ZERO_ANCHORS_OR_ENTRY_MISMATCH';
}
export function report(historical,probe) {
  assert.equal(historical.historicalHTTP,200);
  assert.equal(historical.historicalList,0);
  assert.equal(probe.navigations,1);
  assert.equal(probe.snapshots.length,N);
  const decision=decide(probe.http,probe.staticLinks,probe.snapshots,
    probe.finalAllowed,probe.staticAvailable);
  return {kind:KIND,platform:'寬宏',sourceEntryId:'KHAM_CATEGORY_205',
    parentHead:PARENT,sourceL7BRun:40353636708,sourceL7BArtifact:12665097220,
    sourceL7BArtifactSHA256:L7B_ART,sourceL7BReportSHA256:L7B_SHA,
    publishedStatusBlob:STATUS_BLOB,historicalHTTP:200,historicalList:0,
    historicalObservationIsNotCurrent:true,observedAtUTC:new Date().toISOString(),
    navigationsAttempted:1,redirectCount:probe.redirectCount,
    finalAllowed:probe.finalAllowed,http:probe.http,
    staticAvailable:probe.staticAvailable,staticLinks:probe.staticLinks,
    snapshots:probe.snapshots,decision,
    listEventIdentityVerified:0,acceptedFields:0,goldenAccepted:0,
    published:false,writerExecuted:false,schedulerExecuted:false,
    notifierExecuted:false,mergeExecuted:false,productionModified:false,
    rawHtmlPersisted:false,rawUrlsPersisted:false,rawTitlesPersisted:false,
    cookiesPersisted:false,screenshotsPersisted:false,networkBodiesPersisted:false,
    releaseState:RELEASE};
}
export function safeOutput(path) {
  const p=resolve(path),cwd=resolve('.');
  if(!p.startsWith(cwd+sep))throw Error('HOLD_L9W_ISOLATED_OUTPUT');
  const first=p.slice(cwd.length+1).split(sep)[0];
  if(['docs','scripts','tests','schemas','.github','.git'].includes(first))
    throw Error('HOLD_L9W_ISOLATED_OUTPUT');
  return p;
}
async function observe(page) {
  const dom=await page.evaluate(max=>{
    const a=Array.from(document.querySelectorAll('a[href]')).slice(0,max)
      .map(x=>x.getAttribute('href')||'');
    return {hrefs:a,ready:document.readyState,
      forms:document.querySelectorAll('form').length,
      onclickElements:document.querySelectorAll('[onclick]').length,
      frames:document.querySelectorAll('iframe').length,
      scripts:document.querySelectorAll('script').length};
  },MAX_LINKS);
  return {ready:dom.ready,links:links(dom.hrefs,page.url()),
    forms:dom.forms,onclickElements:dom.onclickElements,
    frames:dom.frames,scripts:dom.scripts};
}
export async function oneNavigation(browserType) {
  const browser=await browserType.launch({headless:true});
  const context=await browser.newContext({acceptDownloads:false,serviceWorkers:'block'});
  const page=await context.newPage();
  let redirects=0,html=null,http=null,finalAllowed=false,staticAvailable=false;
  const empty=links([],ENTRY),snapshots=[];
  await page.route('**/*',route=>{
    if(route.request().isNavigationRequest()&&!allowed(route.request().url()))
      return route.abort('blockedbyclient');
    return route.continue();
  });
  try{
    const response=await page.goto(ENTRY,{waitUntil:'domcontentloaded',timeout:18000});
    if(response){
      http=response.status();
      let prev=response.request().redirectedFrom();
      while(prev){redirects++;prev=prev.redirectedFrom();if(redirects>4)break;}
    }
    finalAllowed=allowed(page.url())&&redirects<=2;
    if(finalAllowed&&http===200&&response){
      const size=Number(response.headers()['content-length']||0);
      if(!size||size<=1500000){
        try{
          const body=await response.text();
          if(body.length<=1500000){
            html=await page.evaluate(({raw,max})=>{
              const d=new DOMParser().parseFromString(raw,'text/html');
              return Array.from(d.querySelectorAll('a[href]')).slice(0,max)
                .map(x=>x.getAttribute('href')||'');
            },{raw:body,max:MAX_LINKS});
            staticAvailable=true;
          }
        }catch{/* static response unavailable is a HOLD, never guessed */}
      }
    }
    for(let i=0;i<N;i++){
      if(i)await page.waitForTimeout(INTERVAL);
      snapshots.push(finalAllowed?await observe(page):
        {ready:'unknown',links:empty,forms:0,onclickElements:0,frames:0,scripts:0});
    }
  }catch{
    while(snapshots.length<N)
      snapshots.push({ready:'unknown',links:empty,forms:0,onclickElements:0,frames:0,scripts:0});
  }finally{await context.close();await browser.close();}
  return {navigations:1,http,redirectCount:redirects,finalAllowed,
    staticAvailable,staticLinks:staticAvailable?links(html,ENTRY):empty,
    snapshots};
}
async function main(){
  const args=process.argv.slice(2);
  const arg=name=>{const i=args.indexOf(name);return i<0?null:args[i+1];};
  if(!args.includes('--live-kham')||!arg('--status')||!arg('--l7b')||
     !arg('--manifest')||!arg('--out'))throw Error('HOLD_L9W_EXPLICIT_SCOPE_REQUIRED');
  const [sb,lb,mb]=await Promise.all([readFile(arg('--status')),
    readFile(arg('--l7b')),readFile(arg('--manifest'))]);
  const historical=parents(sb,lb,JSON.parse(mb));
  const {chromium}=await import('playwright');
  const result=report(historical,await oneNavigation(chromium));
  const dir=safeOutput(arg('--out'));await mkdir(dir,{recursive:true});
  const raw=Buffer.from(j(result));
  await writeFile(dir+'/kham_list_boundary.json',raw);
  await writeFile(dir+'/manifest.json',j({kind:'EVENTRADAR_P30_L9W_SHA_MANIFEST_V1',
    sourceStatusBlob:STATUS_BLOB,sourceL7BReportSHA256:L7B_SHA,
    filesSHA256:{'kham_list_boundary.json':sha(raw)},
    releaseState:RELEASE,published:false}));
  console.log('L9W_KHAM',JSON.stringify({http:result.http,
    static:result.staticLinks.detailUnique,
    rendered:result.snapshots.map(x=>x.links.detailUnique),
    decision:result.decision}));
  console.log('HOLD_L9W_NO_EVENT_PROMOTION_NO_PUBLICATION');
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))
  main().catch(e=>{console.error('HOLD_L9W_GATE',e.message);process.exitCode=1;});
