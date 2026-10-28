#!/usr/bin/env node
/** P30-L9-K: cross-time-window ibon ID 39961 source identity stability evidence.
 * Pin sealed L9-J successful 2/2 short-window report AND L9-H prior mismatch.
 * One NEW normal ephemeral browser list + exact detail only, after >=4h.
 * Never auto-certify long term stability, rewrite formal data, publish or schedule.
 */
import assert from "node:assert/strict";
import {chromium} from "playwright";
import {createHash} from "node:crypto";
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";
import {capture,validateReport as validateJ,LIST_URL,DETAIL_URL,EVENT_ID} from "./p30_l9j_ibon_39961_repeatability.mjs";
import {normalize} from "./p30_l9i_ibon_39961_identity.mjs";

export const KIND="EVENTRADAR_P30_L9K_IBON_39961_CROSS_WINDOW_SOURCE_V1";
export const SOURCE_J_KIND="EVENTRADAR_P30_L9J_IBON_39961_SAME_RUN_REPEATABILITY_V1";
export const SOURCE_H_KIND="EVENTRADAR_P30_L9H_IBON_LOCAL_DOM_HIERARCHY_READONLY_V1";
export const HEAD_J="727aea8aa673b29cd4a589c0a9ca68836fac4b92";
export const RUN_J=40619619643;
export const ARTIFACT_J=12786507149;
export const RUN_H=40516301527;
export const ARTIFACT_H=12740505389;
export const MIN_GAP_MS=4*60*60*1000;
export const RELEASE="HARD_HOLD_NO_PUBLICATION";
const sha=b=>createHash("sha256").update(b).digest("hex");
const serial=x=>JSON.stringify(x,null,2)+"\n";

export function provenance(j,jBytes,h,hBytes){
 assert.deepEqual(JSON.parse(jBytes),j,"HOLD_L9K_J_OBJECT_BYTES_DRIFT");
 assert.deepEqual(JSON.parse(hBytes),h,"HOLD_L9K_H_OBJECT_BYTES_DRIFT");
 assert.equal(j?.kind,SOURCE_J_KIND);
 validateJ(j);
 assert.equal(j.parentL9IHead,"ca60d3182172ad7f824fbcb5a2a6c9189fecc74b");
 assert.equal(j.parentL9IRun,40524765567);
 assert.equal(j.parentL9IArtifact,12744025880);
 assert.equal(j.parentL9HRun,RUN_H);
 assert.equal(j.parentL9HArtifact,ARTIFACT_H);
 assert.equal(j.sourceOrigin,"TWO_NEW_INDEPENDENT_NORMAL_BROWSER_PROCESSES_SAME_RUN");
 assert.equal(j.roundCount,2);
 assert.equal(j.grade.sameRunTitleMatches,2);
 assert.equal(j.grade.consistentBetweenRounds,true);
 assert.equal(j.grade.currentTwoRoundObservation,"TWO_SEPARATE_BROWSER_MATCHES_REVIEW_ONLY");
 assert.equal(j.grade.unexplainedPriorMismatch,true);
 assert.equal(j.grade.historicalMismatchRetained,true);
 assert.equal(j.grade.formalIdentityReleaseEligible,false);
 assert.equal(j.releaseState,RELEASE);
 assert.equal(h?.kind,SOURCE_H_KIND);
 assert.equal(h.parentHead,"07cc3ce1743a56d2bc60213d345f27672cef97d5");
 assert.equal(h.parentRun,40511115223);
 assert.equal(h.sampleCount,5);
 assert.equal(h.titleParityCount,4);
 assert.equal(h.releaseState,RELEASE);
 assert.equal(h.formalFieldPromotions,0);
 assert.equal(h.goldenAccepted,0);
 assert.equal(j.pinnedL9HSHA256,sha(hBytes),"HOLD_L9K_SOURCE_H_DIGEST_REBOUND");
 const contradict=h.rows.filter(x=>x.candidateId==="ibon:"+EVENT_ID);
 assert.equal(contradict.length,1);
 assert.equal(contradict[0].officialUrl,DETAIL_URL);
 assert.equal(contradict[0].httpStatus,200);
 assert.equal(contradict[0].titleParity,false);
 assert.equal(contradict[0].status,"HOLD_TITLE_MISMATCH");
 const old=j.rounds;
 assert.equal(old.length,2);
 for(const x of old){
  assert.equal(x.list.url,LIST_URL);
  assert.equal(x.detail.url,DETAIL_URL);
  assert.equal(x.list.httpStatus,200);
  assert.equal(x.detail.httpStatus,200);
  assert.equal(x.listTitles.length,1);
  assert.equal(x.decision.status,"REVIEW_ONLY_NO_RELEASE");
  assert.equal(x.decision.currentSourceParity,true);
  assert.equal(x.decision.historicTitleStillObserved,true);
  assert.equal(x.decision.driftObserved,false);
  assert.equal(x.list.finalUrlRole,"EXACT_OFFICIAL_ENTRY");
  assert.equal(x.detail.finalUrlRole,"EXACT_OFFICIAL_DETAIL");
 }
 const originals=old.map(x=>normalize(x.listTitles[0]));
 assert.ok(originals[0]&&originals[0]===originals[1],"HOLD_L9K_PREVIOUS_ROUNDS_TITLE_UNSTABLE");
 const end1=Date.parse(old[0].endedUtc),end2=Date.parse(old[1].endedUtc);
 assert.ok(Number.isFinite(end1)&&Number.isFinite(end2)&&end2>end1);
 return{jSHA256:sha(jBytes),hSHA256:sha(hBytes),
  historicalTitle:old[0].listTitles[0],lastCaptureUtc:old[1].endedUtc,
  previousTitleNormalized:originals[0]};
}
export function minimumWindow(historyEndUtc,nowUtc){
 const t=Date.parse(historyEndUtc),n=Date.parse(nowUtc);
 if(!Number.isFinite(t)||!Number.isFinite(n))throw Error("HOLD_L9K_BAD_TIME_PROVENANCE");
 const elapsed=n-t;
 if(elapsed<MIN_GAP_MS)throw Error("HOLD_L9K_WINDOW_SEPARATION_UNDER_4_HOURS");
 return elapsed;
}
export function crossWindowDecision(oldRuns,newRound,historicalTitle){
 assert.equal(oldRuns.length,2);
 const priorTitle=normalize(historicalTitle);
 const priorValid=oldRuns.every(x=>
  x.decision.status==="REVIEW_ONLY_NO_RELEASE"&&
  x.list.httpStatus===200&&x.detail.httpStatus===200&&
  x.listTitles.length===1&&normalize(x.listTitles[0])===priorTitle);
 const freshValid=newRound?.decision?.status==="REVIEW_ONLY_NO_RELEASE"&&
  newRound.decision.currentSourceParity===true&&
  newRound.decision.historicTitleStillObserved===true&&
  newRound.decision.driftObserved===false&&
  newRound.list.httpStatus===200&&newRound.detail.httpStatus===200&&
  newRound.list.finalUrlRole==="EXACT_OFFICIAL_ENTRY"&&
  newRound.detail.finalUrlRole==="EXACT_OFFICIAL_DETAIL"&&
  newRound.listTitles.length===1&&
  normalize(newRound.listTitles[0])===priorTitle;
 const matchedCount=(oldRuns.filter(x=>x.decision.status==="REVIEW_ONLY_NO_RELEASE").length)+(freshValid?1:0);
 return{observedCrossWindowParity:priorValid&&freshValid,
  totalComparableMatches:matchedCount,totalObservedRounds:3,
  crossWindowStatus:priorValid&&freshValid?
   "CROSS_WINDOW_THREE_MATCHES_REVIEW_ONLY":"CROSS_WINDOW_SOURCE_MISMATCH_OR_INCOMPLETE_HOLD",
  historicalMismatchRetained:true,priorRootCauseStillUnknown:true,
  formalIdentityCertified:false,formalReleaseEligible:false,releaseState:RELEASE};
}
export async function audit(j,jBytes,h,hBytes,browser=chromium,opts={}){
 const base=provenance(j,jBytes,h,hBytes);
 const now=opts.now??(()=>new Date().toISOString());
 const preflightNow=now();
 const preGap=minimumWindow(base.lastCaptureUtc,preflightNow);
 const inspect=opts.capture??capture;
 const fresh=await inspect(browser,2,base.historicalTitle,{settleMs:opts.settleMs??1600});
 const observedGap=minimumWindow(base.lastCaptureUtc,fresh.startedUtc);
 const decision=crossWindowDecision(j.rounds,fresh,base.historicalTitle);
 const report={kind:KIND,sourceOrigin:"L9K_ONE_NEW_PUBLIC_NORMAL_BROWSER_DISTINCT_TIME_WINDOW",
  parentJHead:HEAD_J,parentJRun:RUN_J,parentJArtifact:ARTIFACT_J,
  historicHRun:RUN_H,historicHArtifact:ARTIFACT_H,
  sourceJReportSHA256:base.jSHA256,sourceHReportSHA256:base.hSHA256,
  eventId:EVENT_ID,officialListUrl:LIST_URL,officialDetailUrl:DETAIL_URL,
  previousLastCaptureUtc:base.lastCaptureUtc,preflightUtc:preflightNow,
  minWindowGapMs:MIN_GAP_MS,preflightGapMs:preGap,observedGapMs:observedGap,
  newBrowserProcesses:1,newTopLevelNavigationsAttempted:2,
  priorTwoRoundsSummary:j.rounds.map(x=>({index:x.index,startedUtc:x.startedUtc,
   endedUtc:x.endedUtc,listHTTP:x.list.httpStatus,detailHTTP:x.detail.httpStatus,
   listTitleCount:x.listTitles.length,detailHeadingCount:x.detailHeadings.length,
   decision:x.decision.status,titleNormalizedSHA256:sha(normalize(x.listTitles[0]))})),
  currentRound:fresh,decision,
  goldenAccepted:0,formalFieldPromotions:0,formalEventDate:null,formalPrice:null,
  ticketStatus:"UNKNOWN",sessionSplits:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,cookiesPersisted:false,
  screenshotsPersisted:false,networkBodiesPersisted:false,
  fullPlatformCoverageVerified:false,productionRollbackVerified:false,
  previousAndroid44UserAttestedPassPreserved:true,l8CoreAndroidUserAttestedPassPreserved:true,
  releaseState:RELEASE};
 validateReport(report);return report;
}
export function validateReport(r){
 assert.equal(r.kind,KIND);
 assert.equal(r.parentJHead,HEAD_J);assert.equal(r.parentJRun,RUN_J);
 assert.equal(r.parentJArtifact,ARTIFACT_J);
 assert.equal(r.historicHRun,RUN_H);assert.equal(r.historicHArtifact,ARTIFACT_H);
 assert.equal(r.eventId,EVENT_ID);assert.equal(r.officialListUrl,LIST_URL);
 assert.equal(r.officialDetailUrl,DETAIL_URL);
 assert.equal(r.minWindowGapMs,MIN_GAP_MS);
 assert.ok(r.preflightGapMs>=MIN_GAP_MS&&r.observedGapMs>=MIN_GAP_MS);
 assert.equal(r.newBrowserProcesses,1);assert.equal(r.newTopLevelNavigationsAttempted,2);
 assert.equal(r.priorTwoRoundsSummary.length,2);
 assert.equal(r.currentRound.list.url,LIST_URL);assert.equal(r.currentRound.detail.url,DETAIL_URL);
 assert.equal(r.decision.totalObservedRounds,3);
 assert.equal(r.decision.historicalMismatchRetained,true);
 assert.equal(r.decision.priorRootCauseStillUnknown,true);
 assert.equal(r.decision.formalIdentityCertified,false);
 assert.equal(r.decision.formalReleaseEligible,false);
 assert.equal(r.decision.releaseState,RELEASE);
 assert.equal(r.releaseState,RELEASE);
 for(const[k,v]of Object.entries({
  goldenAccepted:0,formalFieldPromotions:0,formalEventDate:null,formalPrice:null,
  ticketStatus:"UNKNOWN",sessionSplits:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,cookiesPersisted:false,
  screenshotsPersisted:false,networkBodiesPersisted:false,
  fullPlatformCoverageVerified:false,productionRollbackVerified:false,
  previousAndroid44UserAttestedPassPreserved:true,l8CoreAndroidUserAttestedPassPreserved:true
 }))assert.equal(r[k],v,k);
 return true;
}
export function safeOut(path){
 const root=resolve("."),target=resolve(path);
 if(target===root||!target.startsWith(root+sep)||["docs","scripts","tests","schemas",".github",".git"].some(x=>target===resolve(x)||target.startsWith(resolve(x)+sep)))
  throw Error("HOLD_L9K_OUTPUT_ISOLATION");
 return target;
}
export async function emit(report,path){
 validateReport(report);
 const dir=safeOut(path);await mkdir(dir,{recursive:true});
 const raw=Buffer.from(serial(report));await writeFile(dir+"/ibon_39961_cross_window.json",raw);
 const manifest={kind:"EVENTRADAR_P30_L9K_SHA256_MANIFEST_V1",
  sourceJRun:RUN_J,sourceJArtifact:ARTIFACT_J,sourceHRun:RUN_H,sourceHArtifact:ARTIFACT_H,
  sourceJReportSHA256:report.sourceJReportSHA256,
  sourceHReportSHA256:report.sourceHReportSHA256,
  fileSHA256:{"ibon_39961_cross_window.json":sha(raw)},
  published:false,releaseState:RELEASE};
 await writeFile(dir+"/manifest.json",serial(manifest));
 return manifest;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--j"]||!args["--h"]||!args["--out"]){
  console.error("HOLD_L9K_TWO_SOURCE_INPUTS_REQUIRED");process.exitCode=2;
 }else{
  safeOut(args["--out"]);
  const jRaw=await readFile(args["--j"]),hRaw=await readFile(args["--h"]);
  const r=await audit(JSON.parse(jRaw),jRaw,JSON.parse(hRaw),hRaw);
  await emit(r,args["--out"]);
  console.log("L9K_CROSS_WINDOW",JSON.stringify({
   previousLastCapture:r.previousLastCaptureUtc,currentStart:r.currentRound.startedUtc,
   gapHours:Number((r.observedGapMs/3600000).toFixed(2)),
   listHTTP:r.currentRound.list.httpStatus,detailHTTP:r.currentRound.detail.httpStatus,
   listTitleCount:r.currentRound.listTitles.length,
   currentDetailHeadingCount:r.currentRound.detailHeadings.length,
   sourceDecision:r.currentRound.decision?.reason,
   crossWindow:r.decision.crossWindowStatus
  }));
  console.log("PASS L9K_DISTINCT_TIME_WINDOW_ONE_PUBLIC_SOURCE_PAIR_AND_SHA");
  console.log("HOLD L9K_HISTORIC_MISMATCH_UNEXPLAINED_NO_GOLDEN_NO_RELEASE");
 }
}
