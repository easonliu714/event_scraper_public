#!/usr/bin/env node
/** P30-L9-A: release BLOCKER matrix. Never release, merge, schedule or write app data.
 * Input exclusively from immutable SHA-verified L7B + L7C CI artifacts.
 * Caller must independently check both upstream archives' SHA256SUMS before use.
 */
import assert from "node:assert/strict";
import {readFile, mkdir, writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";
export const KIND="EVENTRADAR_P30_L9A_RELEASE_BLOCKER_MATRIX_READONLY_V1";
export const FRESH_KIND="EVENTRADAR_P30_L7B_FRESH_BOUNDED_CANDIDATES_V1";
export const PREVIEW_KIND="EVENTRADAR_P30_L7C_ISOLATED_FRESH_REVIEW_PREVIEW_V1";
export const EXPECTED_L7B="P30-L7B-FRESH-20261026-155341-e690bec0b1ac";
export const L7B_RUN=40353636708;
export const L7C_RUN=40436642012;
export const PARENT_HEAD="4668dab1c7061e9d752da0cdfcd58a004e1459f1";
const sha=b=>createHash("sha256").update(b).digest("hex");
const stable=o=>JSON.stringify(o,null,2)+"\n";
const own=(x,k)=>Object.prototype.hasOwnProperty.call(x,k);
export function evaluate(fresh,diag,preview,raw) {
 assert.equal(fresh?.kind,FRESH_KIND,"HOLD_L9A_FRESH_KIND");
 assert.equal(preview?.kind,PREVIEW_KIND,"HOLD_L9A_PREVIEW_KIND");
 assert.equal(diag?.kind,"EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1","HOLD_L9A_DIAG_KIND");
 assert.equal(fresh.runId,EXPECTED_L7B,"HOLD_L9A_SOURCE_RUN");
 assert.equal(diag.runId,fresh.runId,"HOLD_L9A_DIAG_RUN");
 assert.equal(preview.sourceRunId,fresh.runId,"HOLD_L9A_PREVIEW_LINEAGE");
 assert.equal(preview.sourceCandidateSHA256,sha(raw.fresh),"HOLD_L9A_FRESH_SHA");
 assert.equal(fresh.candidateOrigin,"L7B_ACTUAL_NEW_PUBLIC_HTTP","HOLD_L9A_NO_FRESH");
 assert.equal(preview.candidateOrigin,"L7C_PINNED_NEW_HTTP_ARTIFACT_PREVIEW_NOT_A_NEW_CRAWL");
 assert.equal(fresh.actualFreshHTTPRequests,34);
 assert.equal(preview.actualFreshHTTPRequestsInThisGate,0);
 assert.equal(preview.sourceFreshHTTPRequests,34);
 assert.equal(fresh.candidateCount,264);
 assert.equal(fresh.candidateEventRecords?.length,264);
 assert.equal(preview.items?.length,264);
 assert.equal(preview.counts.total,264);
 assert.equal(preview.counts.verifiedDetail,5);
 assert.equal(preview.counts.listOnly+preview.counts.identityHold,259);
 assert.equal(diag.counts.platformsChecked,19);
 assert.equal(diag.platforms.length,19);
 assert.equal(diag.counts.httpOK,16);
 assert.equal(diag.counts.listPositive,12);
 assert.equal(diag.counts.listCandidates,264);
 assert.equal(diag.counts.detailAttempts,12);
 assert.equal(diag.counts.detailHttpOK,12);
 assert.equal(diag.counts.detailIdentityVerified,5);
 assert.equal(diag.counts.labelEvidenceObserved,12);
 assert.equal(diag.fullPlatformCoverageVerified,false);
 assert.equal(fresh.fullPlatformCoverageVerified,false);
 assert.equal(preview.previewOnly,true);
 assert.equal(preview.acceptedAndroid44Preserved,true);
 for(const x of [fresh,diag,preview]){
  assert.equal(x.published,false,"HOLD_L9A_UPSTREAM_PUBLISHED");
  assert.equal(x.goldenAccepted,0,"HOLD_L9A_UPSTREAM_GOLDEN");
 }
 for(const [k,val] of [["writerExecuted",false],["schedulerExecuted",false],
   ["notifierExecuted",false],["automaticMergeCount",0],["automaticHideCount",0],
   ["deletedCount",0]])assert.equal(diag[k],val,"HOLD_L9A_UPSTREAM_SIDE_EFFECT_"+k);
 const byId=new Map();
 for(const c of fresh.candidateEventRecords){
  assert.equal(c.published,false);assert.equal(c.goldenVerified,false);
  assert.equal(c.mergeAllowed,false);assert.equal(c.ticketStatus,"UNKNOWN");
  assert.equal(c.dateStart,null);assert.equal(c.dateEnd,null);
  assert.equal(c.price,null);assert.equal(c.venue,null);
  assert.equal(c.registrationPeriod,null);assert.equal(c.saleWindow,null);
  assert.equal(c.voucherValidity,null);
  assert.ok(!byId.has(c.candidateId),"HOLD_L9A_DUPLICATE_SOURCE_ID");
  byId.set(c.candidateId,c);
 }
 const tierCounts={DETAIL_TITLE_PARITY_PASS:0,LIST_ONLY_UNVERIFIED:0,DETAIL_IDENTITY_HOLD:0};
 let ambiguousPriceEvidence=0;
 let flagged=[];
 for(const c of preview.items){
  assert.ok(byId.has(c.candidateId),"HOLD_L9A_PREVIEW_SOURCE_NOT_IN_FRESH");
  const parent=byId.get(c.candidateId);
  assert.equal(c.sourceUrl,parent.sourceUrl,"HOLD_L9A_URL_DRIFT");
  assert.equal(c.sourcePlatform,parent.sourcePlatform,"HOLD_L9A_PLATFORM_DRIFT");
  assert.equal(c.title,parent.title,"HOLD_L9A_TITLE_DRIFT");
  assert.equal(c.sourceRole,parent.sourceRole,"HOLD_L9A_SOURCE_ROLE_DRIFT");
  assert.equal(c.qualityTier,parent.detailIdentityVerified?"DETAIL_TITLE_PARITY_PASS":
    parent.detailStatus==="NOT_SAMPLED"?"LIST_ONLY_UNVERIFIED":"DETAIL_IDENTITY_HOLD");
  assert.ok(own(tierCounts,c.qualityTier),"HOLD_L9A_UNAPPROVED_QUALITY_TIER");
  tierCounts[c.qualityTier]++;
  assert.equal(c.ticketStatus,"UNKNOWN");
  for(const key of ["dateStart","dateEnd","venue","price","registrationPeriod",
    "saleWindow","voucherValidity"])assert.equal(c[key],null);
  for(const e of c.fieldEvidence){
   assert.equal(e.verification,"FRESH_LABEL_OBSERVED_REVIEW_REQUIRED");
   if(e.role==="PRICE"&&!/(?:\d(?:[\d,.]*\d)?\s*(?:元|NT|TWD|[$＄])|[$＄]\s*\d)/i.test(e.observedValue)){
    ambiguousPriceEvidence++;flagged.push({candidateId:c.candidateId,label:e.label,
      value:e.observedValue,reason:"NOT_MACHINE_VERIFIED_PRICE_REVIEW_ONLY"});
   }
  }
 }
 assert.equal(tierCounts.DETAIL_TITLE_PARITY_PASS,5);
 assert.equal(tierCounts.LIST_ONLY_UNVERIFIED+tierCounts.DETAIL_IDENTITY_HOLD,259);
 assert.equal(tierCounts.DETAIL_IDENTITY_HOLD,7,"HOLD_L9A_DETAILED_IDENTITY_HOLD_DRIFT");
 const b=[
  {id:"RELEASE_AUTHORIZATION",value:"HOLD",observed:"No explicit permission to merge, publish, enable cron/Writer, or retire repositories"},
  {id:"ANDROID_FULL_E2E",value:"HOLD",observed:"Core UI user-attested; keyword search, all 5 modals, outbound HTTPS navigation, review-259 subset not yet evidenced"},
  {id:"ALL_PLATFORM_LIST_COVERAGE",value:"HOLD",observed:"12/19 list-positive; 7 platforms without parsed list. HTTP 200 alone is not parsing proof"},
  {id:"FULL_DETAIL_IDENTITY",value:"HOLD",observed:"5/12 title parity verified; 7 title identity HOLD; 259 candidates do not have detail parity"},
  {id:"FORMAL_FIELD_EVIDENCE",value:"HOLD",observed:"Review-only snippets, no first-party field-level adjudication; formal dates/prices/ticket/sale/registration remain UNKNOWN"},
  {id:"PRICE_PARSER_FALSE_POSITIVE",value:"HOLD",observed:ambiguousPriceEvidence+" ambiguous PRICE evidence labels (non-numeric), never promote"},
  {id:"DEDUP_AND_EVENT_SESSIONS",value:"HOLD",observed:"Cross-platform duplicates, parent/subevent and multi-session identity remain review-only"},
  {id:"ROLLBACK_REHEARSAL",value:"HOLD",observed:"No production rollback rehearsal / restoration SHA / deployment owner signoff"},
  {id:"GOLDEN_WRITER_SECURITY",value:"HOLD",observed:"GOLDEN=0; formal writer/scheduler/notifier remain locked, Cloud Scheduler Source PR #1 HIGH_RISK_HOLD"},
  {id:"THREE_REPOSITORY_RETIREMENT",value:"HOLD",observed:"Pages/PWA/Android/rollback/source parity not signed off; Preview and ShowNews must remain available"}
 ];
 assert.ok(b.every(x=>x.value==="HOLD"));
 const report={kind:KIND,schemaVersion:"1.0.0",
  sourceL7BRun:L7B_RUN,sourceL7CRun:L7C_RUN,parentSourceHead:PARENT_HEAD,
  sourceRunId:fresh.runId,sourceFreshCandidateSHA256:sha(raw.fresh),
  previewSHA256:sha(raw.preview),diagnosticsSHA256:sha(raw.diag),
  actualFreshHTTPRequestsThisGate:0,releaseState:"HARD_HOLD_NO_PUBLICATION",
  readyToMerge:false,readyToDeploy:false,readyToStartScheduler:false,
  readyToEnableWriter:false,readyToRetireRepos:false,
  evidenceLevel:"ANDROID_CORE_UI_USER_ATTESTED_FULL_E2E_PARTIAL",
  metrics:{platforms:19,httpOK:16,listPositive:12,listCandidates:264,
   detailHTTP:12,detailTitleParity:5,detailIdentityHold:7,
   reviewOnly:259,fieldLabelsReviewOnly:12,ambiguousPriceEvidence},
  qualityTiers:tierCounts,ambiguousPriceReviewOnly:flagged,
  blockerCount:b.length,blockers:b,approvedActions:[],
  protectedMainHead:"fc4f963247d68eed29425808cc14e7250f312d05",
  existingAndroid44Preserved:true,published:false,goldenAccepted:0,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  automaticMergeCount:0,automaticHideCount:0,deleteCount:0};
 return report;
}
function safeDest(dest){
 const p=resolve(dest),cwd=resolve(".");
 if(p===cwd||!p.startsWith(cwd+sep)||["docs","scripts",".git",".github","schemas","tests"].some(
  x=>p===resolve(x)||p.startsWith(resolve(x)+sep)))throw Error("HOLD_L9A_ISOLATED_OUTPUT_ONLY");
 return p;
}
export async function build(paths,out){
 const raw={fresh:await readFile(paths.fresh),diag:await readFile(paths.diag),
            preview:await readFile(paths.preview)};
 const f=JSON.parse(raw.fresh),d=JSON.parse(raw.diag),p=JSON.parse(raw.preview);
 const m=evaluate(f,d,p,raw);
 const target=safeDest(out);await mkdir(target,{recursive:true});
 const data=stable(m), digest=sha(data);
 await writeFile(target+"/release_blocker_matrix.json",data,"utf8");
 const manifest={kind:"EVENTRADAR_P30_L9A_BLOCKER_MANIFEST_READONLY",
  sourceL7BRun:L7B_RUN,sourceL7CRun:L7C_RUN,releaseState:m.releaseState,
  inputSHA256:{fresh_candidate_json:m.sourceFreshCandidateSHA256,
   platform_diagnostics_json:m.diagnosticsSHA256,preview_data_json:m.previewSHA256},
  filesSHA256:{"release_blocker_matrix.json":digest},published:false,writerExecuted:false};
 await writeFile(target+"/manifest.json",stable(manifest),"utf8");
 console.log("PASS L9A_REAL_UPSTREAM_LINEAGE_SHA_264_5_259");
 console.log("PASS L9A_READONLY_BLOCKER_MATRIX",m.blockerCount);
 console.log("HOLD L9A_PRODUCTION_RELEASE_DENIED");
 return {matrix:m,manifest};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};
 for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--fresh"]||!args["--diagnostics"]||!args["--preview"]||!args["--out"]){
  console.error("HOLD_L9A_INPUTS_REQUIRED");process.exitCode=2;
 }else await build({fresh:args["--fresh"],diag:args["--diagnostics"],preview:args["--preview"]},args["--out"]);
}
