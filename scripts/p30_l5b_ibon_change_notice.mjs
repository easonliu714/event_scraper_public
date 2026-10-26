#!/usr/bin/env node
/** P30-L5-B: ibon 2 source-bound public activity change notice snapshots.
 * Fails closed: absence of a captured change notice does NOT prove no change.
 * Same exact numeric URLs as accepted L5A run artifact; at most 2 navigation.
 * No login, checkout, CAPTCHA, private APIs, publishing, or app data changes.
 */
import {chromium} from "playwright";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {scheduleBlockEvidence} from "./p30_l4d2_ibon_detail_roles.mjs";
import {decodeActivityBlock,officialIbonDetail,KIND as PARENT_KIND} from "./p30_l5a_ibon_session_roles.mjs";
export const KIND="EVENTRADAR_P30_L5B_IBON_CHANGE_NOTICE_CROSSCHECK_NOT_GOLDEN";
const MAX_NAV=2,MAX_REQUESTS=120;
const noticeHeading=/^(?:最新演出相關資訊[／/]公告|最新演出公告|活動異動公告|場次異動公告|演出異動公告|最新公告|公告事項)\s*[:：]?$/u;
const sectionEnd=/^(?:注意事項|票務資訊|購票須知|退換票須知|禁止事項|演出介紹|活動介紹|主辦單位|票價資訊)\s*[:：]?$/u;
const cancellations=/(?:演出取消|活動取消|取消演出|取消活動|全場取消|場次取消|本場取消)/u;
const postponement=/(?:演出延期|活動延期|場次延期|延期演出|延期舉辦|延後舉行|改期至|演出改期|活動改期)/u;
const additions=/(?:追加場|加開場次|新增場次|加場公告)/u;
const salesOnly=/(?:開賣時間調整|延後開賣|售票延期|開賣延期|售票時間調整)/u;
const genericHazard=/(?:延期|取消|改期|更改|變更)/u;
const trim=x=>String(x??"").replace(/\s+/g," ").trim();
export function changeSignals(text){
  const line=trim(text);
  if(!line)return [];
  const found=[];
  if(cancellations.test(line))found.push("EVENT_CANCELLATION_SIGNAL_REVIEW");
  if(postponement.test(line))found.push("EVENT_POSTPONEMENT_SIGNAL_REVIEW");
  if(additions.test(line))found.push("ADDITIONAL_SESSION_SIGNAL_REVIEW");
  if(salesOnly.test(line))found.push("SALE_CHANGE_ONLY_NOT_EVENT_TIME");
  if(!found.length&&genericHazard.test(line))found.push("AMBIGUOUS_CHANGE_WORD_HOLD");
  return found;
}
export function scopedNotice(lines){
  const arr=(Array.isArray(lines)?lines:[]).map(trim).filter(Boolean).slice(0,350);
  const heads=[];
  for(let i=0;i<arr.length;i++)if(noticeHeading.test(arr[i]))heads.push(i);
  if(!heads.length)return {state:"NO_EXPLICIT_NOTICE_SECTION_CAPTURED_UNKNOWN",
     sections:[],signals:[],isNoChangesProven:false};
  const sections=[],signals=new Set();
  for(const idx of heads.slice(0,3)){
    const bounded=[];
    for(let j=idx+1;j<arr.length&&j<=idx+14;j++){
      const line=arr[j];
      if(sectionEnd.test(line)||noticeHeading.test(line))break;
      if(line.length>280){bounded.push(line.slice(0,280));break;}
      bounded.push(line);
    }
    const group=[...new Set(bounded.flatMap(changeSignals))];
    group.forEach(s=>signals.add(s));
    sections.push({heading:arr[idx],boundedLines:bounded.slice(0,14),
      snippet:bounded.join(" ").slice(0,720),signals:group,
      officialNoticeStatus:"NOT_INDEPENDENTLY_CONFIRMED"});
  }
  const all=[...signals];
  return {state:all.length?"CHANGE_SIGNAL_REQUIRES_ORGANISER_REVIEW":
      "NOTICE_SECTION_CAPTURED_NO_CONFIRMED_CHANGE_UNKNOWN",
    sections,signals:all,isNoChangesProven:false};
}
export function additionalSessionEvidence(blocks){
  const result=[];
  for(const block of (blocks||[]).slice(0,12)){
    const excerpt=trim(block.rawExcerpt);
    if(additions.test(excerpt))result.push({
      role:"ADDITIONAL_SESSION_MARKER_IN_SCHEDULE_NOT_AN_INDEPENDENT_CHANGE_NOTICE",
      excerpt:excerpt.slice(0,190),sourceSection:block.heading,
      verifiedAgainstOrganiser:false});
  }
  return result;
}
export function compareCurrentRows(parent,current){
  if(!parent||parent.kind!==PARENT_KIND||parent.sourceCount!==2||
     parent.sessionRoleCandidateCount!==3||parent.published!==false||
     parent.goldenAccepted!==false||parent.fieldPromotionCount!==0||
     parent.sourceRuntime!=="DORMANT"||parent.samples?.length!==2)
    throw Error("HOLD_PARENT_L5A_GOVERNANCE");
  if(!Array.isArray(current)||current.length!==2)throw Error("HOLD_EXACT_TWO_DETAILS");
  const out=[],ids=new Set();
  for(const old of parent.samples){
    const url=old.officialUrl;
    if(!officialIbonDetail(url)||ids.has(url)||old.goldenVerified!==false||old.published!==false)
      throw Error("HOLD_PARENT_SOURCE_IDENTITY");
    ids.add(url);
    const fresh=current.find(x=>x.officialUrl===url);
    if(!fresh||fresh.listTitle!==old.listTitle||fresh.httpStatus!==200||
       fresh.currentUrl!==url||fresh.titleExactMatched!==true)
      throw Error("HOLD_CURRENT_SOURCE_TITLE_IDENTITY");
    const dates=fresh.scheduleBlocks.flatMap(b=>decodeActivityBlock(b).proposals);
    const original=old.proposedSessions.map(s=>s.eventStartLocal).sort();
    const got=dates.map(s=>s.eventStartLocal).sort();
    const parity=JSON.stringify(original)===JSON.stringify(got);
    const note=scopedNotice(fresh.lines);
    out.push({
      officialUrl:url,listTitle:old.listTitle,httpStatus:200,
      scheduleParity:parity?"EXACT_SAMPLED_EVENT_STARTS":"CHANGED_OR_MISSING_SCHEDULE_HOLD",
      originalSampleEventStarts:original,currentSampleEventStarts:got,
      timezoneStillUnprovenForSomeSessions:old.proposedSessions.some(x=>x.sourceTimeZone===null),
      notice:note,
      scheduleInlineAdditionEvidence:additionalSessionEvidence(fresh.scheduleBlocks),
      organiserChangeApproval:"NOT_VERIFIED",
      liveTicketAvailability:"UNKNOWN",dateStart:null,dateEnd:null,
      ticketStatus:"UNKNOWN",price:null,goldenVerified:false,published:false
    });
  }
  const parity=out.every(x=>x.scheduleParity==="EXACT_SAMPLED_EVENT_STARTS");
  const signals=out.flatMap(x=>x.notice.signals);
  return {kind:KIND,sourceCount:2,details:out,
    scheduleParityStatus:parity?"TWO_SAMPLED_DETAIL_SCHEDULES_UNCHANGED":"SOURCE_SCHEDULE_DRIFT_HOLD",
    changeNoticeStatus:signals.length?"CHANGE_SIGNAL_REQUIRES_REVIEW":"NO_CONFIRMED_NOTICE_IN_BOUNDED_CAPTURE_UNKNOWN",
    additionalSessionMarkerCount:out.reduce((n,x)=>n+x.scheduleInlineAdditionEvidence.length,0),
    organiserConfirmationCount:0,all23IbonVerified:false,
    sourceTimeZoneBackfillCount:0,formalDatePromotionCount:0,
    accepted44AndroidPreserved:true,goldenAccepted:false,published:false,
    writerExecuted:false,notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT"};
}
function detailDOM(){
  const txt=document.body?.innerText||"";
  return {
    headings:[...document.querySelectorAll("h1,h2,h3")].map(x=>x.textContent.replace(/\s+/g," ").trim()).filter(Boolean).slice(0,40),
    lines:txt.split("\n").map(s=>s.trim()).filter(Boolean).slice(0,350),
    visibleLength:txt.length
  };
}
export async function audit(parent,outDir){
  const root=resolve(outDir),docs=resolve("docs");
  if(root===docs||root.startsWith(docs+"/"))throw Error("HOLD_PAGES_WRITER");
  const stats={allowed:0,blockedForeign:0,blockedPassive:0,blockedBudget:0,
     jsPageErrors:0,navigations:0};
  const observations=[];
  const browser=await chromium.launch({headless:true});
  try{
    const context=await browser.newContext({serviceWorkers:"block",permissions:[],
      acceptDownloads:false,javaScriptEnabled:true});
    const page=await context.newPage();
    page.on("pageerror",()=>stats.jsPageErrors++);
    await page.route("**/*",async route=>{
      const req=route.request(),url=req.url();
      let trusted=false;
      try{const x=new URL(url);trusted=x.protocol==="https:"&&
       (x.hostname==="ticket.ibon.com.tw"||x.hostname.endsWith(".ibon.com.tw"))&&
       !x.username&&!x.password&&!x.port;}catch{}
      if(!trusted){stats.blockedForeign++;return route.abort("blockedbyclient");}
      if(["image","font","media"].includes(req.resourceType())){
        stats.blockedPassive++;return route.abort("blockedbyclient");
      }
      if(stats.allowed>=MAX_REQUESTS){stats.blockedBudget++;return route.abort("blockedbyclient");}
      stats.allowed++;return route.continue();
    });
    for(const p of parent.samples){
      if(!officialIbonDetail(p.officialUrl))throw Error("HOLD_PARENT_UNSAFE_DETAIL_URL");
      await page.waitForTimeout(1100);
      let status=null,landed=null,visible=null,fail=null;
      try{
        const r=await page.goto(p.officialUrl,{waitUntil:"domcontentloaded",timeout:18000});
        stats.navigations++;status=r?.status()??null;landed=page.url();
        if(landed===p.officialUrl&&status===200){
          await page.waitForTimeout(1700);
          visible=await page.evaluate(detailDOM);
        }
      }catch(e){fail=String(e.name||"NavigationError");}
      observations.push({
        officialUrl:p.officialUrl,listTitle:p.listTitle,
        httpStatus:status,currentUrl:landed,
        titleExactMatched:Boolean(visible?.headings.includes(p.listTitle)),
        lines:visible?.lines||[],
        scheduleBlocks:visible?scheduleBlockEvidence(visible.lines):[],
        failure:fail
      });
    }
    await context.close();
  }finally{await browser.close();}
  let result=compareCurrentRows(parent,observations);
  result.observedAtUTC=new Date().toISOString();
  result.maxNavigation=MAX_NAV;result.maxRequests=MAX_REQUESTS;
  result.networkStats=stats;
  result.noLogin=true;result.noCheckout=true;result.noStealth=true;
  result.noCaptchaBypass=true;result.noPrivateAPI=true;result.noRetries=true;
  await mkdir(root,{recursive:true});
  await writeFile(root+"/change_notice_review.json",JSON.stringify(result,null,2)+"\n");
  console.log("PASS P30_L5B_SOURCE_BOUND_SNAPSHOT_COUNT",result.sourceCount);
  console.log("P30_L5B_SCHEDULE_PARITY",result.scheduleParityStatus);
  console.log("P30_L5B_NOTICES",result.changeNoticeStatus,
    "INLINE_ADDITIONAL",result.additionalSessionMarkerCount);
  for(const x of result.details)console.log("P30_L5B_DETAIL",
    x.listTitle,x.scheduleParity,x.notice.state,
    x.notice.signals.join(","),x.scheduleInlineAdditionEvidence.length);
  if(result.scheduleParityStatus!=="TWO_SAMPLED_DETAIL_SCHEDULES_UNCHANGED"){
    console.log("HOLD P30_L5B_SCHEDULE_CHANGED_SINCE_L5A");process.exitCode=2;
  }else console.log("PASS P30_L5B_BOUNDED_OFFICIAL_NOTICE_AUDIT_NO_GOLDEN_PROMOTION");
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const a=process.argv.indexOf("--parent"),b=process.argv.indexOf("--out-dir");
  if(a<0||b<0||!process.argv[a+1]||!process.argv[b+1]){
    console.error("HOLD_REQUIRED_PARENT_AND_OUTDIR");process.exitCode=2;
  }else{
    const parentRaw=await readFile(process.argv[a+1]);
    const parent=JSON.parse(parentRaw.toString("utf8"));
    await audit(parent,process.argv[b+1]);
  }
}
