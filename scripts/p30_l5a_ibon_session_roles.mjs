#!/usr/bin/env node
/** P30-L5-A ibon offline read-only source-bound session evidence.
 * No dates are promoted into published catalog. No network here. */
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
export const KIND="EVENTRADAR_P30_L5A_IBON_SESSION_ROLE_REVIEW_ONLY";
export const INPUT_KIND="EVENTRADAR_P30_L4D2_IBON_PUBLIC_DETAIL_ROLE_EVIDENCE_NOT_GOLDEN";
export const ROLE="ACTUAL_EVENT_TIME_LABELED_RAW_UNPROMOTED";
const DATE=/(?<!\d)(20\d{2})(?:[./-]|年)(1[0-2]|0?[1-9])(?:[./-]|月)(3[01]|[12]\d|0?[1-9])(?:日)?(?!\d)/g;
const DAY={SUN:0,MON:1,TUE:2,WED:3,THU:4,FRI:5,SAT:6,"日":0,"月":1,"火":2,"水":3,"木":4,"金":5,"土":6};
const HAZARD=/(?:延期|延後|改期|取消|停辦|暫停|更改日期)/;
const norm=x=>String(x??"").replace(/\s+/g," ").trim();
export function officialIbonDetail(url){
  try{const u=new URL(url);return u.protocol==="https:"&&u.hostname==="ticket.ibon.com.tw"&&!u.username&&!u.password&&!u.port&&!u.search&&!u.hash&&/^\/ActivityInfo\/Details\/[0-9]{3,8}$/.test(u.pathname);}catch{return false;}
}
export function isoDate(year,month,day){
  const y=+year,m=+month,d=+day,v=new Date(Date.UTC(y,m-1,d));
  if(v.getUTCFullYear()!==y||v.getUTCMonth()+1!==m||v.getUTCDate()!==d)return null;
  return {iso:[y,String(m).padStart(2,"0"),String(d).padStart(2,"0")].join("-"),weekday:v.getUTCDay()};
}
function taggedWeekday(tail){
  let m=/^\s*[（(]\s*(SUN|MON|TUE|WED|THU|FRI|SAT)\.?\s*[)）]/i.exec(tail);
  if(m)return DAY[m[1].toUpperCase()];
  m=/^\s*[（(]\s*([日月火水木金土])\s*[)）]/u.exec(tail);
  return m?DAY[m[1]]:null;
}
function timed(segment,kind){
  const label=kind==="show"?"開演|演出開始":"開放入場|開場|入場";
  const before=new RegExp("(?:("+label+"))\\s*[:：]?\\s*([01]?\\d|2[0-3]):([0-5]\\d)","u");
  const after=new RegExp("([01]?\\d|2[0-3]):([0-5]\\d)\\s*(?:"+label+")","u");
  const b=before.exec(segment);if(b)return b[2].padStart(2,"0")+":"+b[3];
  const a=after.exec(segment);return a?a[1].padStart(2,"0")+":"+a[2]:null;
}
export function decodeActivityBlock(block){
  if(!block||block.role!==ROLE||block.status!=="RAW_UNPROMOTED_EVIDENCE")throw Error("HOLD_UNTRUSTED_BLOCK_ROLE");
  const head=norm(block.heading);
  const box=/^【活動時間(?:（台灣時間）)?】$/.test(head);
  const inline=/^日期\s*[\/／]\s*時間\s*[｜|:：]/.test(head);
  if(!box&&!inline)throw Error("HOLD_EVENT_TIME_HEADING");
  const raw=String(block.rawExcerpt??"");
  if(!norm(raw).startsWith(head)||raw.length>360)throw Error("HOLD_ACTIVITY_LABEL_BINDING");
  const matches=[...raw.matchAll(DATE)];
  if(!matches.length||matches.length>8)return {state:"HOLD_BOUNDED_DATE_COUNT",proposals:[]};
  const dates=matches.map(x=>isoDate(x[1],x[2],x[3]));
  if(dates.some(x=>x===null))return {state:"HOLD_INVALID_SOURCE_DATE",proposals:[]};
  const old=[...new Set(block.observedFullYearDates||[])],now=[...new Set(dates.map(x=>x.iso))];
  if(JSON.stringify(old)!==JSON.stringify(now))throw Error("HOLD_UPSTREAM_DATE_TOKEN_MISMATCH");
  const tz=head.includes("台灣時間")?"Asia/Taipei":null;
  const proposals=[];let hold=false;
  for(let i=0;i<matches.length;i++){
    const current=matches[i],d=dates[i];
    const stop=i+1<matches.length?matches[i+1].index:raw.length;
    const part=raw.slice(current.index+current[0].length,stop);
    const weekday=taggedWeekday(part);
    if(weekday!==null&&weekday!==d.weekday){hold=true;continue;}
    if(HAZARD.test(part)){hold=true;continue;}
    const show=timed(part,"show"),admit=timed(part,"admission");
    if(!show||admit&&admit>show){hold=true;continue;}
    const start=d.iso+"T"+show;
    if(proposals.some(x=>x.eventStartLocal===start)){hold=true;continue;}
    proposals.push({eventDate:d.iso,eventStartLocal:start,
      admissionStartLocal:admit?d.iso+"T"+admit:null,
      sourceTimeZone:tz,sourceTimeZoneStatus:tz?"EXPLICIT_ASIA_TAIPEI":"NOT_EXPLICIT_IN_CAPTURED_BLOCK",
      dateRole:"OFFICIAL_DETAIL_EVENT_START_CANDIDATE",
      admissionRole:admit?"OFFICIAL_DETAIL_ADMISSION_TIME_CANDIDATE":"NOT_OBSERVED",
      admissionIsNotEventStart:true,proposedOnly:true,
      verifiedAgainstOrganiser:false,verifiedAgainstChangeNotices:false,
      approvalState:"REQUIRES_L5_CROSS_EVIDENCE_REVIEW"});
  }
  return {state:hold?"PARTIAL_EVENT_TIME_ROLE_HOLD":"ALL_EXPLICIT_EVENT_START_SEGMENTS_PARSED",proposals};
}
export function transform(input){
  if(!input||input.kind!==INPUT_KIND||input.sourceRole!=="OFFICIAL_TICKET_PLATFORM"
      ||input.stats?.listStatus!==200||input.listCount<2||input.details?.length!==2
      ||input.sourceRuntime!=="DORMANT"||input.verifiedDateCount!==0
      ||input.published!==false||input.goldenAccepted!==false
      ||input.writerExecuted!==false||input.notifierExecuted!==false||input.autoHidden!==0)
    throw Error("HOLD_L4D2_EVIDENCE_GOVERNANCE");
  const seen=new Set(),results=[];
  for(const row of input.details){
    const url=row.requestedOfficialUrl;
    if(!officialIbonDetail(url)||seen.has(url)||row.responseUrl!==url||row.responseStatus!==200||
       row.identity!=="EXACT_LIST_DETAIL_HEADING"||!row.listTitle||row.goldenVerified!==false||
       row.dateStart!==null||row.dateEnd!==null||row.price!==null||row.ticketStatus!=="UNKNOWN")
      throw Error("HOLD_SOURCE_BOUND_DETAIL_IDENTITY");
    seen.add(url);
    const decoded=(row.scheduleBlockEvidence||[]).map(decodeActivityBlock);
    const proposedSessions=decoded.flatMap(x=>x.proposals);
    const ok=decoded.length>0&&decoded.every(x=>x.state==="ALL_EXPLICIT_EVENT_START_SEGMENTS_PARSED")&&proposedSessions.length>0;
    results.push({platform:"ibon",listTitle:row.listTitle,officialUrl:url,
      sourceRole:"OFFICIAL_TICKET_PLATFORM",observedTimeBlocks:decoded.length,
      sessionStatus:ok?"LABELED_SESSION_CANDIDATES_REVIEW_ONLY":"HOLD_INCOMPLETE_SESSION_EVIDENCE",
      proposedSessions,dateStart:null,dateEnd:null,dateRole:"UNKNOWN_UNTIL_SEPARATE_APPROVAL",
      ticketStatus:"UNKNOWN",saleWindow:null,registrationWindow:null,
      voucherValidity:null,price:null,category:"待分類",
      confidence:"L5_EVENT_TIME_ROLE_CANDIDATE_NOT_GOLDEN",
      goldenVerified:false,published:false});
  }
  const detailCount=results.filter(x=>x.sessionStatus==="LABELED_SESSION_CANDIDATES_REVIEW_ONLY").length;
  const sessionCount=results.reduce((sum,x)=>sum+x.proposedSessions.length,0);
  return {kind:KIND,inputKind:INPUT_KIND,sourceCount:results.length,
    sessionRoleCandidateCount:sessionCount,detailSourcesParsed:detailCount,samples:results,
    overallState:detailCount===2&&sessionCount>=3?
      "TWO_DETAIL_SOURCES_EVENT_TIMES_DECODED":"HOLD_SOURCE_SESSIONS_INCOMPLETE",
    fieldPromotionCount:0,androidOriginalAccepted44Preserved:true,
    goldenAccepted:false,published:false,writerExecuted:false,notifierExecuted:false,
    autoHidden:0,sourceRuntime:"DORMANT",completeCatalogProven:false};
}
export async function run(inputFile,outDir){
  const path=resolve(outDir),docs=resolve("docs");
  if(path===docs||path.startsWith(docs+"/"))throw Error("HOLD_FORMAL_DOCS_WRITER");
  const raw=await readFile(inputFile);
  const result=transform(JSON.parse(raw.toString("utf8")));
  result.inputDiagnosticsSHA256=createHash("sha256").update(raw).digest("hex");
  await mkdir(path,{recursive:true});
  await writeFile(path+"/session_candidates.json",JSON.stringify(result,null,2)+"\n");
  console.log("P30_L5A_SOURCE_SAMPLE_COUNT",result.sourceCount);
  console.log("P30_L5A_TIME_ROLE_CANDIDATES",result.sessionRoleCandidateCount,
    "DETAILS",result.detailSourcesParsed,"STATE",result.overallState);
  for(const x of result.samples)console.log("P30_L5A_SOURCE",x.listTitle,
    JSON.stringify(x.proposedSessions.map(s=>({event:s.eventStartLocal,admission:s.admissionStartLocal,tz:s.sourceTimeZoneStatus}))));
  if(result.overallState!=="TWO_DETAIL_SOURCES_EVENT_TIMES_DECODED"){
    console.log("HOLD P30_L5A_INCOMPLETE_EVENT_TIMES");process.exitCode=2;
  }else console.log("PASS P30_L5A_EVENT_STARTS_DISTINCT_FROM_ADMISSION_REVIEW_ONLY");
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const a=process.argv.indexOf("--input"),b=process.argv.indexOf("--out-dir");
  if(a<0||b<0||!process.argv[a+1]||!process.argv[b+1]){
    console.error("HOLD_REQUIRED_ARGS");process.exitCode=2;
  }else await run(process.argv[a+1],process.argv[b+1]);
}
