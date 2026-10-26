#!/usr/bin/env node
/** P30-L7-A: immutable evidence -> ISOLATED sample candidate JSON (not fresh crawl).
 * No network. No production docs writer. No publisher or Golden promotions.
 * Input: native sealed L6-B G5J review. 12 ticket/aggregator identities.
 * All missing/uncertain fields remain null/UNKNOWN. One official government
 * event period and two producer show starts remain evidence ONLY.
 */
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";

export const KIND="EVENTRADAR_P30_L7A_ISOLATED_SAMPLE_CANDIDATES_V1";
export const SCHEMA_VERSION="1.0.0";
export const PARENT="EVENTRADAR_P30_L6B_G5J_CROSS_PLATFORM_EVENT_IDENTITY_REVIEW_ONLY";
const BITAN="https://strolltimes.com/events/new-taipei/261016084730/";
const GOV="https://newtaipei.travel/zh-tw/calendar/detail/4058";
const NIER="https://ticket.ibon.com.tw/ActivityInfo/Details/39974";
const PRODUCER="https://www.nierconcert.com/12026";
const MARK="L7A_PINNED_HISTORICAL_EVIDENCE_NOT_FRESH";
const hash=s=>createHash("sha256").update(s).digest("hex");
const frozen=o=>JSON.stringify(o);
export function safeSourceUrl(platform,u){
 try{
  const x=new URL(u);
  if(x.protocol!=="https:"||x.username||x.password||x.port||x.search||x.hash)return false;
  if(platform==="StrollTimes")return x.hostname==="strolltimes.com"&&/^\/events\/[a-z-]+\/\d{12}\/$/.test(x.pathname);
  if(platform==="ibon")return x.hostname==="ticket.ibon.com.tw"&&/^\/ActivityInfo\/Details\/\d{3,8}$/.test(x.pathname);
  if(platform==="FamiTicket")return x.hostname==="www.famiticket.com.tw"&&/^\/Home\/Activity\/Info\/[A-Za-z0-9_+=-]{20,500}$/.test(x.pathname);
  return false;
 }catch{return false;}
}
export function checkParent(p){
 if(!p||p.kind!==PARENT||p.sourceEventRecords!==12||
    p.platformBreakdown?.StrollTimes!==6||p.platformBreakdown?.FamiTicket!==4||
    p.platformBreakdown?.ibon!==2||p.candidateRecords?.length!==12||
    p.totalPairCount!==66||p.examinedPairs?.length!==66||
    p.crossPlatformPairCount!==44||p.samePlatformPairCount!==22||
    p.firstPartyReferenceCount!==2||p.firstPartyReferenceEdges?.length!==2||
    p.inputIbonDetailCount!==2||p.inputIbonSampledShowStartCount!==3||
    p.ibonShowSessionsAreNotSeparateEventRecords!==true||
    p.actualDuplicateEventPairsVerified!==0||p.firstPartySameEventCrossPlatformMatchesVerified!==0||
    p.actualParentChildLinksVerified!==0||p.automaticMergeCount!==0||
    p.automaticHideCount!==0||p.deleteCount!==0||
    p.confirmedOfficialClassificationCount!==0||
    p.productionDatePromotionCount!==0||p.productionFieldPromotionCount!==0||
    p.sourceRuntime!=="DORMANT"||p.goldenAccepted!==false||
    p.published!==false||p.writerExecuted!==false||p.notifierExecuted!==false||
    p.autoHidden!==0||p.accepted44AndroidPreserved!==true||
    p.reversibleWithoutWrites!==true||
    p.sourceEventRoleIntegrity!==true)
  throw Error("HOLD_L6B_PARENT_IDENTITY_OR_WRITE_STATE");
 const seen=new Set(),counts={StrollTimes:0,FamiTicket:0,ibon:0};
 for(const s of p.candidateRecords){
  if(!s||!Object.hasOwn(counts,s.platform)||
     !safeSourceUrl(s.platform,s.eventUrl)||seen.has(s.eventUrl)||
     typeof s.title!=="string"||!s.title.trim()||s.title.length>320||
     s.eventDateStart!==null||s.eventDateEnd!==null||
     s.ticketStatus!=="UNKNOWN"||s.price!==null||
     s.categoryVerified!==false||s.mergeAllowed!==false||s.published!==false)
    throw Error("HOLD_PARENT_SOURCE_ROW_FIELD_PROMOTION_OR_DUPLICATION");
  if(s.platform==="StrollTimes"&&s.provenance!=="THIRD_PARTY_AGGREGATOR_ONLY")throw Error("HOLD_PARENT_STROLL_ROLE");
  if(["ibon","FamiTicket"].includes(s.platform)&&s.provenance!=="OFFICIAL_TICKET_DETAIL_EXACT_TITLE")throw Error("HOLD_PARENT_TICKET_ROLE");
  const firstPartyExpected=s.eventUrl===BITAN?GOV:s.eventUrl===NIER?PRODUCER:null;
  if(s.referenceFirstPartyUrl!==firstPartyExpected||
     (s.eventUrl===BITAN?frozen(s.referenceTimeRange)!==frozen(["2026-10-17","2026-12-13"]):
          s.referenceTimeRange!==null))
    throw Error("HOLD_PARENT_FIRST_PARTY_REFERENCE_SCOPE");
  if(s.platform!=="ibon"&&(s.sessionCount!==0||s.unverifiedSessionCount!==0))throw Error("HOLD_PARENT_AGGREGATOR_OR_FAMITICKET_SESSIONS");
  if(s.platform==="ibon"&&(s.sessionCount<1||s.sessionCount>2||s.unverifiedSessionCount!==s.sessionCount))
    throw Error("HOLD_PARENT_TICKET_SESSIONS");
  counts[s.platform]++;seen.add(s.eventUrl);
 }
 if(frozen(counts)!==frozen({StrollTimes:6,FamiTicket:4,ibon:2}))
   throw Error("HOLD_PARENT_SOURCE_COUNTS");
 const refs=p.firstPartyReferenceEdges;
 const gov=refs.filter(e=>e.from===BITAN&&e.to===GOV&&e.kind==="GOV_CALENDAR_ONE_EVENT_REFERENCE");
 const prod=refs.filter(e=>e.from===NIER&&e.to===PRODUCER&&e.kind==="ORIGINAL_PRODUCER_TWO_SHOWS_REFERENCE");
 if(gov.length!==1||prod.length!==1||
    gov[0].independentEventProof!==true||gov[0].mergeAllowed!==false||
    prod[0].independentEventProof!==true||prod[0].mergeAllowed!==false||
    prod[0].originalAdditionalShowNoticeTimestampVerified!==false||
    frozen(prod[0].showStartTimes)!==frozen(["2027-02-20T18:00","2027-02-21T14:00"])||
    p.candidateRecords.find(s=>s.eventUrl===NIER)?.sessionCount!==2||
    p.candidateRecords.find(s=>s.eventUrl===BITAN)?.referenceFirstPartyUrl!==GOV||
    frozen(p.candidateRecords.find(s=>s.eventUrl===BITAN)?.referenceTimeRange)!==
      frozen(["2026-10-17","2026-12-13"]))
   throw Error("HOLD_PARENT_FIRST_PARTY_EVENT_VS_SHOW_ROLE");
 const pairKeys=new Set();
 for(const pair of p.examinedPairs){
  if(!seen.has(pair.a)||!seen.has(pair.b)||pair.a===pair.b||
     pair.duplicateAccepted!==false||pair.automaticMergeAllowed!==false||
     pair.automaticHideAllowed!==false||pair.deleteAllowed!==false||
     pair.action!=="RETAIN_SEPARATELY_REVIEW_ONLY"||
     pair.primarySourceEventIdParity!=="NOT_PROVEN_BOTH_SIDES"||
     pair.organiserIdentityParity!=="NOT_PROVEN_BOTH_SIDES"||
     pair.relationshipNotKnown===false)throw Error("HOLD_PARENT_PAIR_IMPLICIT_MERGE");
  const key=[pair.a,pair.b].sort().join("\n");
  if(pairKeys.has(key))throw Error("HOLD_PARENT_DUPLICATE_PAIR");
  pairKeys.add(key);
 }
 if(pairKeys.size!==66)throw Error("HOLD_PARENT_PAIR_COVERAGE");
 return true;
}
export function candidateId(source){return "er7a_"+hash(source.platform+"\n"+source.eventUrl).slice(0,24);}
export function transform(p,parentBytes){
 checkParent(p);
 const sha=hash(parentBytes);
 const runId="P30-L7A-SNAPSHOT-"+sha.slice(0,16);
 const lines=p.candidateRecords.map(s=>{
  const isAgg=s.platform==="StrollTimes",isBitan=s.eventUrl===BITAN,isNier=s.eventUrl===NIER;
  const quality=isBitan?"ONE_GOV_FIRST_PARTY_EVENT_REFERENCE_REVIEW_ONLY":
     isNier?"TICKET_DETAIL_AND_PRODUCER_SHOWS_REVIEW_ONLY":
     isAgg?"AGGREGATOR_ARTICLE_OFFICIALITY_HOLD":
     "TICKET_DETAIL_IDENTITY_PASS_FIELDS_UNKNOWN";
  const official=isBitan?GOV:isNier?PRODUCER:null;
  const role=isAgg?"THIRD_PARTY_AGGREGATOR_ARTICLE":"OFFICIAL_TICKET_EVENT_DETAIL";
  const dateE=isBitan?[{sourceUrl:GOV,sourceRole:"GOV_OFFICIAL_CALENDAR",
       dateRole:"OFFICIAL_EVENT_PERIOD_REVIEW_ONLY",value:["2026-10-17","2026-12-13"],
       approval:"ISOLATED_EVIDENCE_NOT_PROMOTED"}]:[];
  const showE=isNier?[
    {eventStartLocal:"2027-02-20T18:00",sourceUrl:PRODUCER,
      role:"PRODUCER_SHOW_START_CORROBORATED_NO_FINAL_TIMEZONE",isEventRecord:false},
    {eventStartLocal:"2027-02-21T14:00",sourceUrl:PRODUCER,
      role:"PRODUCER_SHOW_START_CORROBORATED_NO_FINAL_TIMEZONE",isEventRecord:false}
  ]:[];
  return {candidateId:candidateId(s),runId,sourcePlatform:s.platform,
    sourceRole:role,sourceUrl:s.eventUrl,sourceIdentityRole:s.verifiedSourceEventId,
    title:s.title,officialLinkUrl:isAgg?official:s.eventUrl,
    originalSourceUrl:s.eventUrl,
    firstPartyReferenceUrl:official,
    qualityState:quality,qualityFlags:[
      "PINNED_PRIOR_EVIDENCE_NOT_FRESH_HTTP",
      "TICKET_SALE_STATUS_UNKNOWN",
      "NOT_GOLDEN_NOT_PUBLISHED",
      ...(isAgg?["THIRD_PARTY_ARTICLE_NOT_AUTOMATICALLY_OFFICIAL"]:[]),
      ...(isBitan?["OFFICIAL_PERIOD_ONLY_IN_EVIDENCE"]:[]),
      ...(isNier?["MULTIPLE_SHOW_SESSIONS_NOT_SEPARATE_EVENTS","NO_TIMESTAMPED_CHANGE_NOTICE"]:[])
    ],
    categoryHint:s.categoryHint||"待分類",category:"待分類",categoryVerified:false,
    dateStart:null,dateEnd:null,eventTimeZone:null,venue:null,price:null,
    ticketStatus:"UNKNOWN",
    registrationPeriod:null,saleWindow:null,voucherValidity:null,
    sourceDateEvidence:dateE,showSessionEvidence:showE,
    candidateSessionCount:s.sessionCount,
    sourceLineage:[{from:s.eventUrl,to:s.eventUrl,
      role:isAgg?"AGGREGATOR_ARTICLE":"TICKET_DETAIL",
      verification:"SOURCE_URL_IDENTITY_ONLY"},...(official?[{from:s.eventUrl,to:official,
      role:isBitan?"ONE_GOV_CALENDAR_EVENT_REFERENCE":"ORIGINAL_PRODUCER_SHOW_REFERENCE",
      verification:"INDEPENDENT_SOURCE_EVIDENCE_ONLY"}]:[])],
    assumedFresh:false,originalOrganiserIdentityVerified:isBitan,
    crossPlatformSameEventVerified:false,mergeAllowed:false,
    autoHideAllowed:false,deleteAllowed:false,goldenVerified:false,published:false};
 });
 lines.sort((a,b)=>a.candidateId.localeCompare(b.candidateId,"en"));
 if(new Set(lines.map(x=>x.candidateId)).size!==12)throw Error("HOLD_CANDIDATE_KEY_COLLISION");
 const pairs=p.examinedPairs.map(e=>({
   a:candidateId(p.candidateRecords.find(x=>x.eventUrl===e.a)),
   b:candidateId(p.candidateRecords.find(x=>x.eventUrl===e.b)),
   relationship:"UNPROVEN_DO_NOT_MERGE",reviewStatus:"REQUIRES_INDEPENDENT_FIRST_PARTY_SAME_EVENT_PROOF",
   crossPlatform:e.crossPlatform,mergeAllowed:false,deleteAllowed:false,hideAllowed:false
 })).sort((a,b)=>(a.a+a.b).localeCompare(b.a+b,"en"));
 const root={kind:KIND,schemaVersion:SCHEMA_VERSION,runId,
  candidateOrigin:MARK,collectionMode:"IMMUTABLE_UPSTREAM_ARTIFACT_TRANSFORM_OFFLINE",
  evidenceAsOfUTC:null,actualFreshHTTPRequests:0,
  fullPlatformCoverageVerified:false,sampledSourceOnly:true,
  expectedSourceCoverage:"6_AGGREGATOR_ARTICLES_4_FAMITICKET_2_IBON_EVENT_DETAILS",
  sourceParentKind:PARENT,sourceParentRunId:40331119770,
  sourceParentSHA256:sha,
  candidateCount:12,platformBreakdown:{StrollTimes:6,FamiTicket:4,ibon:2},
  referenceCount:2,totalSourceEventRecords:12,
  candidateEventRecords:lines,
  showStartsInPinnedInput:3,independentFirstPartyRefs:2,
  automaticMergeCount:0,automaticHideCount:0,deletedCount:0,
  formalDatePromotionCount:0,formalFieldPromotionCount:0,
  goldenAccepted:0,appDataPublished:false,notifierExecuted:false,
  schedulerExecuted:false,sourceRuntime:"DORMANT",
  existingAndroid44PassPreserved:true};
 return {candidate:root,relations:{kind:"EVENTRADAR_P30_L7A_66_UNMERGED_RELATIONSHIPS_REVIEW_ONLY",
  runId,sourceParentSHA256:sha,reviewedPairCount:66,reviewedCrossPlatformPairs:44,
  identities:pairs,verifiedDuplicateCount:0,automaticMerges:0,autoHidden:0,
  published:false}};
}
function within(path,parent){
 return path===parent||path.startsWith(parent+sep);
}
export async function run(input,out){
 const dir=resolve(out);
 if(within(dir,resolve("docs")))throw Error("HOLD_PRODUCTION_DOCS_WRITER");
 const source=await readFile(input),parent=JSON.parse(source);
 const {candidate,relations}=transform(parent,source);
 await mkdir(dir,{recursive:true});
 const c=JSON.stringify(candidate,null,2)+"\n";
 const r=JSON.stringify(relations,null,2)+"\n";
 await writeFile(dir+"/candidate_sample.json",c,"utf8");
 await writeFile(dir+"/relationships_review.json",r,"utf8");
 const manifest={kind:"EVENTRADAR_P30_L7A_ARTIFACT_MANIFEST_ONLY",
   runId:candidate.runId,sourceParentRunId:40331119770,
   parentSHA256:hash(source),files:{
      "candidate_sample.json":hash(c),"relationships_review.json":hash(r)},
   goldenAccepted:0,published:false,sourceRuntime:"DORMANT"};
 await writeFile(dir+"/manifest.json",JSON.stringify(manifest,null,2)+"\n","utf8");
 console.log("L7A_RUN_ID",candidate.runId,"PARENT_SHA",candidate.sourceParentSHA256);
 console.log("L7A_ROWS",candidate.candidateCount,"RELATION_PAIRS",relations.reviewedPairCount,
   "PRODUCER_SHOW_TIMES",candidate.candidateEventRecords.filter(x=>x.showSessionEvidence.length).length);
 console.log("PASS P30_L7A_SAMPLE_SNAPSHOT_12_RECORDS_66_REVIEWS_SHA_MANIFEST");
 console.log("HOLD P30_L7A_NOT_FRESH_ALL_PLATFORM_CRAWL_OR_GOLDEN");
 console.log("PASS P30_L7A_ZERO_PRODUCTION_WRITES");
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const arg=k=>{const n=process.argv.indexOf("--"+k);return n>=0?process.argv[n+1]:null;};
 if(!arg("input")||!arg("out-dir")){console.error("HOLD_REQUIRED_INPUT_AND_OUTDIR");process.exitCode=2;}
 else await run(arg("input"),arg("out-dir"));
}
