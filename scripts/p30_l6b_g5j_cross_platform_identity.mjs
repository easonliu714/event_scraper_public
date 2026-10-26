#!/usr/bin/env node
/**
 * P30-L6-B (G5J): SHA-bound offline, cross-platform EVENT-ID review.
 * 6 aggregator articles + 4 FamiTicket ticket events + 2 ibon ticket events.
 * NieR 2 show starts are sessions of ONE ibon event, not event duplicates.
 * One Bitan gov-calendar and one NieR original-producer source edge only.
 * No web calls. No official data, Android, PWA, DB, notifications or merges.
 */
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
export const KIND="EVENTRADAR_P30_L6B_G5J_CROSS_PLATFORM_EVENT_IDENTITY_REVIEW_ONLY";
const KINDS={
  g5j:"EVENTRADAR_P30_L6A_G5J_REVERSIBLE_CLASSIFICATION_AND_DEDUP_REVIEW_ONLY",
  fami:"EVENTRADAR_P30_L5D1_FAMITICKET_OFFICIAL_FIELD_ROLES_REVIEW_ONLY",
  ibon:"EVENTRADAR_P30_L5A_IBON_SESSION_ROLE_REVIEW_ONLY",
  nier:"EVENTRADAR_P30_L5C_NIER_PRODUCER_CROSS_SOURCE_REVIEW_ONLY"
};
const BITAN="https://strolltimes.com/events/new-taipei/261016084730/";
const BITAN_OFFICIAL="https://newtaipei.travel/zh-tw/calendar/detail/4058";
const NIER_TICKET="https://ticket.ibon.com.tw/ActivityInfo/Details/39974";
const NIER_TOUR="https://www.nierconcert.com/12026";
const NIER_DETAIL="https://www.nierconcert.com/12026/taipei-2";
const safe=s=>typeof s==="string"&&s.trim().length>0&&s.length<240;
export function strictTicketUrl(url,platform){
 try{
  const u=new URL(url);
  if(u.protocol!=="https:"||u.username||u.password||u.port||u.search||u.hash)return false;
  if(platform==="ibon")return u.hostname==="ticket.ibon.com.tw"&&/^\/ActivityInfo\/Details\/[0-9]{3,8}$/.test(u.pathname);
  if(platform==="FamiTicket")return u.hostname==="www.famiticket.com.tw"&&
     /^\/Home\/Activity\/Info\/[A-Za-z0-9_+=-]{20,500}$/.test(u.pathname);
  return false;
 }catch{return false;}
}
export function verifyInputs(d){
 const {g5j,fami,ibon,nier}=d;
 if(!g5j||g5j.kind!==KINDS.g5j||g5j.inputNodes!==6||
  g5j.reviewedCandidates?.length!==6||g5j.reviewPairs?.length!==15||
  g5j.sourceEvidenceEdges?.length!==7||g5j.oneGovernmentReferenceCount!==1||
  g5j.confirmedDuplicatePairs!==0||g5j.automaticMergeCount!==0||
  g5j.automaticHideCount!==0||g5j.deleteCount!==0||
  g5j.published!==false||g5j.goldenAccepted!==false||
  g5j.writerExecuted!==false||g5j.notifierExecuted!==false||
  g5j.sourceRuntime!=="DORMANT"||g5j.accepted44AndroidPreserved!==true)
  throw Error("HOLD_L6A_G5J_PARENT_INTEGRITY");
 const agg=new Set();
 for(const x of g5j.reviewedCandidates){
  if(!safe(x.id)||!/^https:\/\/strolltimes\.com\/events\/[a-z-]+\/\d{12}\/$/.test(x.id)||
   agg.has(x.id)||x.sourceRole!=="THIRD_PARTY_EVENT_AGGREGATOR"||
   x.goldenVerified!==false||x.published!==false||x.autoMergeAllowed!==false||
   x.dateStart!==null||x.dateEnd!==null||x.referenceOfficialUrl!== (x.id===BITAN?BITAN_OFFICIAL:null))
    throw Error("HOLD_AGGREGATOR_EVENT_AND_OFFICIAL_EVIDENCE");
  agg.add(x.id);
 }
 if(!agg.has(BITAN))throw Error("HOLD_REQUIRED_BITAN_SOURCE");
 if(!fami||fami.kind!==KINDS.fami||fami.sourceRuntime!=="DORMANT"||
  fami.detailSamples?.length!==4||fami.exactTitleMatches!==4||
  fami.listedSampleCount!==4||fami.labeledRoleEvidenceCount<3||
  fami.published!==false||fami.goldenAccepted!==false||
  fami.writerExecuted!==false||fami.notifierExecuted!==false||fami.autoHidden!==0)
   throw Error("HOLD_FAMITICKET_FOUR_EXACT_DETAILS");
 const fids=new Set();
 for(const f of fami.detailSamples){
  if(!strictTicketUrl(f.officialUrl,"FamiTicket")||fids.has(f.officialUrl)||
    f.observedUrl!==f.officialUrl||f.detailHttp!==200||
    f.identity!=="EXACT_LIST_DETAIL_TITLE_PASS"||!safe(f.listTitle)||
    f.dateStart!==null||f.dateEnd!==null||f.venue!==null||
    f.price!==null||f.ticketStatus!=="UNKNOWN"||
    f.goldenVerified!==false||f.published!==false||f.fieldPromotionCount!==0)
   throw Error("HOLD_FAMITICKET_DETAIL_IDENTITY_OR_FIELDS");
  fids.add(f.officialUrl);
 }
 if(!ibon||ibon.kind!==KINDS.ibon||ibon.sourceCount!==2||
    ibon.samples?.length!==2||ibon.detailSourcesParsed!==2||
    ibon.sessionRoleCandidateCount!==3||ibon.fieldPromotionCount!==0||
    ibon.sourceRuntime!=="DORMANT"||ibon.published!==false||
    ibon.goldenAccepted!==false||ibon.writerExecuted!==false||
    ibon.notifierExecuted!==false||ibon.autoHidden!==0)
  throw Error("HOLD_IBON_TWO_DETAILS_THREE_SESSIONS");
 const iids=new Set();
 for(const item of ibon.samples){
  if(!strictTicketUrl(item.officialUrl,"ibon")||iids.has(item.officialUrl)||
    !safe(item.listTitle)||item.proposedSessions?.length<1||
    item.sessionStatus!=="LABELED_SESSION_CANDIDATES_REVIEW_ONLY"||
    item.dateStart!==null||item.dateEnd!==null||item.price!==null||
    item.ticketStatus!=="UNKNOWN"||item.goldenVerified!==false||
    item.published!==false)
   throw Error("HOLD_IBON_EVENT_OR_SESSION_ROLE");
  const ts=new Set();
  for(const show of item.proposedSessions){
   if(!/^(?:20\d\d)-\d\d-\d\dT(?:[01]\d|2[0-3]):[0-5]\d$/.test(show.eventStartLocal)||
    ts.has(show.eventStartLocal)||show.proposedOnly!==true||
    show.admissionIsNotEventStart!==true||
    show.verifiedAgainstOrganiser!==false||
    show.verifiedAgainstChangeNotices!==false)
    throw Error("HOLD_IBON_SHOW_OR_ADMISSION_PROOF");
   ts.add(show.eventStartLocal);
  }
  iids.add(item.officialUrl);
 }
 if(!iids.has(NIER_TICKET))throw Error("HOLD_NIER_IBON_SOURCE_IDENTITY");
 if(ibon.samples.reduce((n,s)=>n+s.proposedSessions.length,0)!==3)
  throw Error("HOLD_THREE_SHOWS_NOT_THREE_EVENTS");
 if(!nier||nier.kind!==KINDS.nier||
  nier.officialOriginalTicketUrl!==NIER_TICKET||
  nier.producerSourceUrl!==NIER_TOUR||nier.producerDetailUrl!==NIER_DETAIL||
  nier.producerOriginalTwoStartsSame!==true||
  nier.producerSessionCount!==2||
  JSON.stringify(nier.originalOfficialStarts)!==
      JSON.stringify(["2027-02-20T18:00","2027-02-21T14:00"])||
  nier.officialFirstPartyIndependentEventIdentityCount>1||
  nier.additionalShowAnnouncementIndependentlyVerified!==false||
  nier.organiserChangeApproval!=="NOT_VERIFIED"||
  nier.announcementTimestampVerified!==false||
  nier.dateStart!==null||nier.dateEnd!==null||
  nier.ticketStatus!=="UNKNOWN"||nier.price!==null||
  nier.formalFieldPromotionCount!==0||
  nier.goldenAccepted!==false||nier.published!==false||
  nier.writerExecuted!==false||nier.notifierExecuted!==false||
  nier.autoHidden!==0||nier.sourceRuntime!=="DORMANT")
  throw Error("HOLD_NIER_ORIGINAL_PRODUCER_SOURCE_OR_UNPROVEN_NOTICE");
 const shows=ibon.samples.find(x=>x.officialUrl===NIER_TICKET)
    .proposedSessions.map(x=>x.eventStartLocal).sort();
 if(JSON.stringify(shows)!==JSON.stringify(nier.originalOfficialStarts))
  throw Error("HOLD_IBON_NIER_TWO_SHOWS_PRODUCER_MISMATCH");
 return true;
}
export function pairStatus(a,b){
 if(a.eventUrl===b.eventUrl)throw Error("HOLD_DUPLICATE_PLATFORM_EVENT_IDENTITY");
 const platforms=[a.platform,b.platform].sort();
 const cross=a.platform!==b.platform;
 const sameNormalizedTitle=a.title.normalize("NFKC").replace(/\s+/g,"").toLowerCase()===
   b.title.normalize("NFKC").replace(/\s+/g,"").toLowerCase();
 // A pair is NEVER promoted just because the title/date/venue looks similar.
 return {a:a.eventUrl,b:b.eventUrl,platforms,crossPlatform:cross,
  titleEqualityObservation:sameNormalizedTitle?"SAME_VISIBLE_TITLE_REVIEW_ONLY":"NOT_SAME_VISIBLE_TITLE",
  organiserIdentityParity:"NOT_PROVEN_BOTH_SIDES",
  primarySourceEventIdParity:"NOT_PROVEN_BOTH_SIDES",
  activityEditionParity:"NOT_PROVEN",
  venueIdentityParity:"NOT_PROVEN_BOTH_SIDES",
  eventDateRoleParity:"NOT_PROVEN_BOTH_SIDES",
  showSessionIdentityParity:"NOT_PROVEN",
  action:"RETAIN_SEPARATELY_REVIEW_ONLY",
  automaticMergeAllowed:false,automaticHideAllowed:false,deleteAllowed:false,
  duplicateAccepted:false};
}
export function reconcile(d){
 verifyInputs(d);
 const events=[];
 for(const a of d.g5j.reviewedCandidates)
  events.push({platform:"StrollTimes",eventUrl:a.id,title:a.homepageCardTitle,
    provenance:"THIRD_PARTY_AGGREGATOR_ONLY",
    referenceFirstPartyUrl:a.referenceOfficialUrl,
    referenceTimeRange:a.referenceOfficialPeriod,verifiedSourceEventId:a.id===BITAN?
     "ONE_GOV_EVENT_REFERENCE_ONLY":"NOT_PROVEN",
    sessionCount:0,unverifiedSessionCount:0,
    categoryHint:a.categoryHint,categoryVerified:false,
    eventDateStart:null,eventDateEnd:null,ticketStatus:"UNKNOWN",price:null,
    mergeAllowed:false,published:false});
 for(const a of d.fami.detailSamples)
  events.push({platform:"FamiTicket",eventUrl:a.officialUrl,title:a.listTitle,
    provenance:"OFFICIAL_TICKET_DETAIL_EXACT_TITLE",
    referenceFirstPartyUrl:null,referenceTimeRange:null,verifiedSourceEventId:"TICKET_EVENT_URL_EXACT",
    sessionCount:0,unverifiedSessionCount:0,
    categoryHint:"待分類",categoryVerified:false,
    eventDateStart:null,eventDateEnd:null,ticketStatus:"UNKNOWN",price:null,
    mergeAllowed:false,published:false});
 for(const a of d.ibon.samples)
  events.push({platform:"ibon",eventUrl:a.officialUrl,title:a.listTitle,
    provenance:"OFFICIAL_TICKET_DETAIL_EXACT_TITLE",
    referenceFirstPartyUrl:a.officialUrl===NIER_TICKET?NIER_TOUR:null,
    referenceTimeRange:null,verifiedSourceEventId:"TICKET_EVENT_URL_EXACT",
    sessionCount:a.proposedSessions.length,unverifiedSessionCount:a.proposedSessions.length,
    categoryHint:"待分類",categoryVerified:false,
    eventDateStart:null,eventDateEnd:null,ticketStatus:"UNKNOWN",price:null,
    mergeAllowed:false,published:false});
 events.sort((a,b)=>a.eventUrl.localeCompare(b.eventUrl,"en"));
 const pairs=[];
 for(let i=0;i<events.length;i++)for(let j=i+1;j<events.length;j++)
  pairs.push(pairStatus(events[i],events[j]));
 const references=[
  {from:BITAN,to:BITAN_OFFICIAL,kind:"GOV_CALENDAR_ONE_EVENT_REFERENCE",
   role:"OFFICIAL_EVENT_PERIOD_REVIEW_ONLY",independentEventProof:true,
   firstPartyTitleAndVenueCorroborated:true,
   originalPublicationTimestampVerified:false,
   mergeAllowed:false},
  {from:NIER_TICKET,to:NIER_TOUR,kind:"ORIGINAL_PRODUCER_TWO_SHOWS_REFERENCE",
   role:"PRODUCER_SHOW_TIMES_REVIEW_ONLY",independentEventProof:true,
   showStartTimes:[...d.nier.originalOfficialStarts],
   originalAdditionalShowNoticeTimestampVerified:false,
   producerTimeZoneForBothVerified:false,
   mergeAllowed:false}
 ];
 const cross=pairs.filter(x=>x.crossPlatform).length;
 return {kind:KIND,inputKind:KINDS,
  sourceEventRecords:events.length,platformBreakdown:{
    StrollTimes:6,FamiTicket:4,ibon:2},
  inputAggregatorArticleCount:6,inputFamiTicketDetailCount:4,inputIbonDetailCount:2,
  inputIbonSampledShowStartCount:3,
  ibonShowSessionsAreNotSeparateEventRecords:true,
  candidateRecords:events,examinedPairs:pairs,
  totalPairCount:pairs.length,crossPlatformPairCount:cross,
  samePlatformPairCount:pairs.length-cross,
  firstPartyReferenceEdges:references,
  firstPartyReferenceCount:2,
  firstPartySameEventCrossPlatformMatchesVerified:0,
  actualDuplicateEventPairsVerified:0,
  actualParentChildLinksVerified:0,
  sourceEventRoleIntegrity:true,
  confirmedCrossPlatformMerges:0,
  automaticMergeCount:0,automaticHideCount:0,deleteCount:0,
  confirmedOfficialClassificationCount:0,
  productionDatePromotionCount:0,productionFieldPromotionCount:0,
  formalEventWriterExecuted:false,
  restoredOriginalRowsRequired:false,
  reversibleWithoutWrites:true,
  accepted44AndroidPreserved:true,
  sourceRuntime:"DORMANT",goldenAccepted:false,published:false,
  writerExecuted:false,notifierExecuted:false,autoHidden:0};
}
export async function run(paths,outdir){
 const target=resolve(outdir),docs=resolve("docs");
 if(target===docs||target.startsWith(docs+"/"))throw Error("HOLD_PRODUCTION_WRITER");
 const inputs={};const sha={};
 for(const key of ["g5j","fami","ibon","nier"]){
  const raw=await readFile(paths[key]);
  sha[key]=createHash("sha256").update(raw).digest("hex");
  inputs[key]=JSON.parse(raw);
 }
 const result=reconcile(inputs);
 result.parentEvidenceSHA256=sha;
 await mkdir(target,{recursive:true});
 await writeFile(target+"/cross_platform_review.json",JSON.stringify(result,null,2)+"\n");
 console.log("L6B_G5J_EVENT_RECORDS",result.sourceEventRecords,"BY_PLATFORM",JSON.stringify(result.platformBreakdown));
 console.log("L6B_G5J_PAIRS",result.totalPairCount,"CROSS",result.crossPlatformPairCount,
    "SAME",result.samePlatformPairCount);
 console.log("L6B_G5J_REFERENCE_EDGES",result.firstPartyReferenceCount,
    "IBON_SHOW_SESSIONS",result.inputIbonSampledShowStartCount,"IBON_EVENT_RECORDS",result.inputIbonDetailCount);
 console.log("PASS P30_L6B_TWELVE_EVENT_SOURCES_66_PAIRS_44_CROSS_PLATFORM_TWO_REFERENCES");
 console.log("PASS P30_L6B_ZERO_AUTOMATIC_MERGE_HIDE_DELETE_OR_FORMAL_DATA_WRITES");
 console.log("HOLD P30_L6B_CROSS_PLATFORM_EVENT_MATCHES_AND_PARENT_CHILD_ORIGINAL_PROOFS");
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const arg=name=>{const i=process.argv.indexOf("--"+name);return i>=0?process.argv[i+1]:null;};
 const keys=["g5j","fami","ibon","nier","out-dir"];
 if(keys.some(x=>!arg(x))){console.error("HOLD_REQUIRED_FOUR_PINNED_ARTIFACTS_AND_OUTPUT");process.exitCode=2;}
 else await run(Object.fromEntries(keys.slice(0,4).map(k=>[k,arg(k)])),arg("out-dir"));
}
