#!/usr/bin/env node
/** P30-L9-B: read-only field-quality evidence and synthetic rollback.
 * No live network, production writer, publisher, notification or scheduler.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile, writeFile, mkdir, rm, cp} from 'node:fs/promises';
import {resolve, sep, join} from 'node:path';
import {fileURLToPath} from 'node:url';

export const KIND='EVENTRADAR_P30_L9B_FIELD_QUALITY_ROLLBACK_REVIEW_V1';
export const FRESH_RUN='P30-L7B-FRESH-20261026-155341-e690bec0b1ac';
const sha=x=>createHash('sha256').update(x).digest('hex');
const stringify=x=>JSON.stringify(x,null,2)+'\n';
const ROLES=new Set(['EVENT_PERIOD','ADMISSION_TIME','REGISTRATION_PERIOD','SALE_PERIOD','VOUCHER_VALIDITY','PRICE','VENUE']);
const NONPRICE=/^(?:資訊|詳情|說明|未定|未知|待公告|請見官網|請洽主辦|more|info|information|n\/a|票價資訊)$/iu;
const FREE=/^(?:免費|自由入場|免票|免門票|free)$/iu;
const NUMCURRENCY=/(?:NT\s*\$\s*\d|NTD\s*\d|TWD\s*\d|[$＄]\s*\d|\d[\d,]*(?:\.\d+)?\s*(?:元|塊|圓))/iu;
const CURRENCYPREFIX=/(?:NT\s*\$|NTD|TWD|新臺幣|新台幣|票價\s*[:：]?\s*|[$＄]\s*\d|\d[\d,]*(?:\.\d+)?\s*(?:元|塊|圓))/iu;
const TIME=/(?:\b20\d{2}[-/.年]\s*\d{1,2}|\d{1,2}\s*[月/]\s*\d{1,2}|\d{1,2}:\d{2})/u;
const ROLE_WORDS=[
  ['REGISTRATION_PERIOD',/(報名|登記|註冊)/u],
  ['SALE_PERIOD',/(售票|預售|開賣|開售|販售|購票)/u],
  ['ADMISSION_TIME',/(入場|進場)/u],
  ['VOUCHER_VALIDITY',/(有效期限|票券有效|兌換期限|使用期限)/u]
];
export function labelQuality(e){
 assert.ok(e&&ROLES.has(e.role),'HOLD_UNSUPPORTED_FIELD_ROLE');
 assert.equal(e.verification,'FRESH_LABEL_OBSERVED_REVIEW_REQUIRED','HOLD_FORGED_FIELD_VERIFICATION');
 const val=String(e.observedValue??'').trim().replace(/\s+/gu,' ');
 if(!val||val.length>110)return{quality:'REJECT_EMPTY_OR_OVERSIZE',promotable:false};
 if(e.role==='PRICE'){
  if(NONPRICE.test(val)||/^\W*資訊\W*$/u.test(val))return{quality:'REJECT_GENERIC_NON_PRICE',promotable:false};
  if(FREE.test(val))return{quality:'FREE_TEXT_REVIEW_ONLY',promotable:false};
  if(NUMCURRENCY.test(val))return{quality:'PRICE_TOKEN_REVIEW_ONLY',promotable:false};
  if(CURRENCYPREFIX.test(val))return{quality:'REJECT_INCOMPLETE_PRICE_TOKEN',promotable:false};
  return{quality:'REJECT_NO_PRICE_TOKEN',promotable:false};
 }
 if(e.role==='VENUE'){
  if(NONPRICE.test(val)||val.length<3)return{quality:'REJECT_UNSPECIFIC_VENUE',promotable:false};
  return{quality:'VENUE_TEXT_REVIEW_ONLY',promotable:false};
 }
 const other=ROLE_WORDS.filter(([r,re])=>r!==e.role&&re.test(val)).map(([r])=>r);
 if(other.length&&!ROLE_WORDS.some(([r,re])=>r===e.role&&re.test(val)))return{quality:'HOLD_TIME_ROLE_CONFLICT',crossRoleHints:other,promotable:false};
 if(!TIME.test(val))return{quality:'REJECT_NO_DATE_OR_TIME_TOKEN',promotable:false};
 return{quality:'TIME_ROLE_TOKEN_REVIEW_ONLY',promotable:false};
}
const GAP_ADAPTERS={
 '中正紀念堂':['P30_L4B_CKSMH_QUERY_LIST_ID_CARD','CKSMH Query.list.ctr needs actId-bound card parsing','FRESH_HTML_BODY_NOT_ARCHIVED'],
 '台北世貿':['P30_L3A_TWTC_EXHIBITION_TABLE','TWTC exhibition table needs exhibition_more.aspx?id identity','FRESH_HTML_BODY_NOT_ARCHIVED'],
 'ibon':['P30_L3BB_IBON_JS_LIST','Index/entertainment JS shell requires bounded official rendered ID proof','JS_RENDERING_NOT_PROVEN'],
 'FamiTicket':['P30_L3BA_FAMITICKET_HOME','Home lists but exact /Home/Activity/Info detail parity HOLD','FRESH_LIST_CANDIDATES_ONLY'],
 '寬宏':['P30_TICKET_QUERY_LIST','HTTP200/list0; do not assert no events','FRESH_LIST0_NOT_REPROOFED']
};
function validate(x){
 const {fresh,diagnostics,preview,release,raw}=x;
 assert.equal(fresh?.kind,'EVENTRADAR_P30_L7B_FRESH_BOUNDED_CANDIDATES_V1');
 assert.equal(diagnostics?.kind,'EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1');
 assert.equal(preview?.kind,'EVENTRADAR_P30_L7C_ISOLATED_FRESH_REVIEW_PREVIEW_V1');
 assert.equal(release?.kind,'EVENTRADAR_P30_L9A_RELEASE_BLOCKER_MATRIX_READONLY_V1');
 assert.equal(fresh.runId,FRESH_RUN);
 assert.equal(diagnostics.runId,FRESH_RUN);
 assert.equal(preview.sourceRunId,FRESH_RUN);
 assert.equal(release.sourceRunId,FRESH_RUN);
 assert.equal(fresh.actualFreshHTTPRequests,34);
 assert.equal(preview.sourceFreshHTTPRequests,34);
 assert.equal(preview.actualFreshHTTPRequestsInThisGate,0);
 assert.equal(preview.sourceCandidateSHA256,sha(raw.fresh));
 assert.equal(release.sourceFreshCandidateSHA256,sha(raw.fresh));
 assert.equal(release.previewSHA256,sha(raw.preview));
 assert.equal(release.diagnosticsSHA256,sha(raw.diagnostics));
 assert.equal(fresh.candidateCount,264);
 assert.equal(fresh.candidateEventRecords.length,264);
 assert.equal(preview.items.length,264);
 assert.equal(preview.counts.total,264);
 assert.equal(preview.counts.verifiedDetail,5);
 assert.equal(preview.counts.listOnly+preview.counts.identityHold,259);
 assert.equal(diagnostics.counts.platformsChecked,19);
 assert.equal(diagnostics.platforms.length,19);
 assert.equal(diagnostics.counts.httpOK,16);
 assert.equal(diagnostics.counts.listPositive,12);
 assert.equal(diagnostics.counts.detailIdentityVerified,5);
 assert.equal(diagnostics.counts.labelEvidenceObserved,12);
 assert.equal(release.releaseState,'HARD_HOLD_NO_PUBLICATION');
 assert.equal(release.blockerCount,10);
 assert.equal(release.blockers.length,10);
 assert.ok(release.blockers.every(q=>q.value==='HOLD'));
 for(const a of [fresh,diagnostics,preview,release]){
  assert.equal(a.published,false);assert.equal(a.goldenAccepted,0);
 }
 for(const k of ['writerExecuted','schedulerExecuted','notifierExecuted'])assert.equal(diagnostics[k],false);
 for(const k of ['readyToMerge','readyToDeploy','readyToEnableWriter','readyToStartScheduler','readyToRetireRepos'])assert.equal(release[k],false);
 assert.equal(release.existingAndroid44Preserved,true);
}
export function review(x){
 validate(x);
 const {fresh,diagnostics,preview,raw}=x;
 const byId=new Map(preview.items.map(c=>[c.candidateId,c]));
 assert.equal(byId.size,264,'HOLD_DUPLICATE_PREVIEW_ID');
 const found=[],statusCounts={};let rejected=0,conflicts=0,acceptedReviewTokens=0;
 for(const row of fresh.candidateEventRecords){
  const peer=byId.get(row.candidateId);assert.ok(peer,'HOLD_MISSING_PREVIEW_RECORD');
  for(const key of ['title','sourcePlatform','sourceRole','sourceUrl'])assert.equal(peer[key],row[key],'HOLD_SOURCE_PREVIEW_DRIFT');
  assert.equal(row.ticketStatus,'UNKNOWN');
  for(const key of ['dateStart','dateEnd','venue','price','registrationPeriod','saleWindow','voucherValidity']){
   assert.equal(row[key],null);assert.equal(peer[key],null);
  }
  assert.equal(row.mergeAllowed,false);assert.equal(row.published,false);assert.equal(row.goldenVerified,false);
  assert.ok(!row.fieldEvidence.length||row.detailIdentityVerified,'HOLD_UNBOUND_FIELD_EVIDENCE');
  for(const e of row.fieldEvidence){
   assert.ok(typeof e.sourceUrl==='string'&&e.sourceUrl.startsWith('https://'));
   const result=labelQuality(e);
   found.push({candidateId:row.candidateId,platform:row.sourcePlatform,sourceUrl:e.sourceUrl,
    observedLabel:e.label,observedValue:e.observedValue,role:e.role,
    sourceEvidenceStatus:'SOURCE_LABEL_OBSERVED_NOT_VERIFIED',
    quality:result.quality,reviewOnly:true,formalFieldPromoted:false});
   statusCounts[result.quality]=(statusCounts[result.quality]??0)+1;
   if(result.quality.startsWith('REJECT'))rejected++;
   else if(result.quality.startsWith('HOLD'))conflicts++;
   else acceptedReviewTokens++;
  }
 }
 assert.equal(found.length,12,'HOLD_L9B_FIELD_COUNT_DRIFT');
 const platforms=diagnostics.platforms.map(p=>{
  const c=GAP_ADAPTERS[p.platform];
  return{platform:p.platform,httpState:p.http?.state??'NOT_ATTEMPTED',
   listState:p.listState,listCandidateCount:p.listCandidateCount,
   detailAttempted:p.detailAttempted,detailIdentityVerified:p.detailIdentityVerified,
   freshness:'L7B_PINNED_CURRENT_SOURCE_NOT_REFETCHED',
   adapterRecommendation:c?.[0]??null,reason:c?.[1]??null,
   evidenceGap:c?.[2]??null,requiresNewFreshHTTPBeforeClaimingRepair:!!c,
   resolutionStatus:c?'HOLD_ADAPTER_NOT_FRESH_VERIFIED':'NO_NEW_CLAIM'};
 });
 assert.equal(platforms.length,19);
 return{kind:KIND,schemaVersion:'1.0.0',
  sourceRuns:{l7b:40353636708,l7c:40436642012,l9a:40439742917},
  sourceSHA256:{fresh:sha(raw.fresh),diagnostics:sha(raw.diagnostics),preview:sha(raw.preview),release:sha(raw.release)},
  producedFrom:'SHA_PINNED_IMMUTABLE_ARTIFACTS_NOT_NEW_HTTP',actualFreshHTTPRequestsThisGate:0,
  android44UserPassPreserved:true,androidL8CoreUIUserPassPreserved:true,
  sourceCounts:{platforms:19,httpOK:16,listPositive:12,candidates:264,detailTitleParity:5,reviewPending:259},
  fieldReview:{total:found.length,acceptedReviewTokens,rejected,conflicts,statusCounts,items:found},
  sourceAdapterReview:platforms,rollbackSimulation:{state:'PENDING_SYNTHETIC_ROLLBACK',
   baselineSHA256:null,restoredSHA256:null,productionRollbackVerified:false,simulationOnly:true},
  releaseState:'HARD_HOLD_NO_PUBLICATION',publisherExecuted:false,writerExecuted:false,
  schedulerExecuted:false,notifierExecuted:false,sourceMainTouched:false,
  autoMergeCount:0,goldenAccepted:0,published:false,formalFieldPromotions:0,
  nextGate:'P30-L9-C platform-specific fresh limited adapter acquisition'};
}
export function allowedOutput(output){
 const cwd=resolve('.'),dest=resolve(output);
 if(dest===cwd||!dest.startsWith(cwd+sep)||['docs','scripts','schemas','tests','.github','.git'].some(name=>dest===resolve(name)||dest.startsWith(resolve(name)+sep)))
  throw Error('HOLD_L9B_ISOLATED_OUTPUT_REQUIRED');
 return dest;
}
export async function syntheticRollback(dir,baseline){
 const original=join(dir,'rollback_lab_base.bin'),work=join(dir,'rollback_lab_work.bin'),restored=join(dir,'rollback_lab_restored.bin');
 try{
  await writeFile(original,baseline);await cp(original,work);
  assert.equal(sha(await readFile(work)),sha(baseline));
  await writeFile(work,Buffer.from('SYNTHETIC_BAD_PUBLISH_PAYLOAD_DO_NOT_USE\n'));
  const corrupted=sha(await readFile(work));
  assert.notEqual(corrupted,sha(baseline));
  await cp(original,restored);
  const restoredHash=sha(await readFile(restored));
  assert.equal(restoredHash,sha(baseline));
  return{state:'PASS_SYNTHETIC_ROLLBACK_ONLY',baselineSHA256:sha(baseline),
   corruptedSHA256:corrupted,restoredSHA256:restoredHash,
   productionRollbackVerified:false,simulationOnly:true,realProductionFileOpened:false};
 }finally{await Promise.all([original,work,restored].map(p=>rm(p,{force:true})));}
}
export async function build(paths,out){
 const dest=allowedOutput(out);
 const raw={fresh:await readFile(paths.fresh),diagnostics:await readFile(paths.diagnostics),
  preview:await readFile(paths.preview),release:await readFile(paths.release)};
 const x={fresh:JSON.parse(raw.fresh),diagnostics:JSON.parse(raw.diagnostics),
  preview:JSON.parse(raw.preview),release:JSON.parse(raw.release),raw};
 const report=review(x);
 await mkdir(dest,{recursive:true});
 report.rollbackSimulation=await syntheticRollback(dest,raw.preview);
 assert.equal(report.rollbackSimulation.state,'PASS_SYNTHETIC_ROLLBACK_ONLY');
 const outputs={
  'field_quality_review.json':report,
  'platform_adapter_gaps.json':{kind:'EVENTRADAR_P30_L9B_PLATFORM_ADAPTER_GAPS_READONLY_V1',
    rows:report.sourceAdapterReview,sourceRunId:FRESH_RUN,sourceOrigin:'PINNED_NOT_REFETCHED',published:false},
  'rollback_simulation.json':{kind:'EVENTRADAR_P30_L9B_SYNTHETIC_ROLLBACK_V1',
    ...report.rollbackSimulation,goldenAccepted:0,published:false}
 };
 const fileSHA={};
 for(const [file,data] of Object.entries(outputs)){
  const payload=Buffer.from(stringify(data));
  await writeFile(join(dest,file),payload);fileSHA[file]=sha(payload);
 }
 const manifest={kind:'EVENTRADAR_P30_L9B_IMMUTABLE_EVIDENCE_MANIFEST_V1',
  outputSHA256:fileSHA,inputSHA256:report.sourceSHA256,
  exactSourceRuns:report.sourceRuns,releaseState:'HARD_HOLD_NO_PUBLICATION',
  actualFreshHTTPRequestsThisGate:0,productionFilesModified:false,published:false};
 await writeFile(join(dest,'manifest.json'),stringify(manifest));
 console.log('PASS L9B_SOURCE_PROVENANCE_SHA_19_264_5_259');
 console.log('PASS L9B_FIELD_LABEL_REVIEW_ONLY',JSON.stringify(report.fieldReview.statusCounts));
 console.log('PASS L9B_SYNTHETIC_ROLLBACK_ONLY',report.rollbackSimulation.restoredSHA256);
 console.log('HOLD L9B_PRODUCTION_ROLLBACK_UNVERIFIED_AND_RELEASE_DENIED');
 return{report,manifest};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const a={};for(let i=2;i<process.argv.length;i+=2)a[process.argv[i]]=process.argv[i+1];
 if(!a['--fresh']||!a['--diagnostics']||!a['--preview']||!a['--release']||!a['--out']){
  console.error('HOLD_L9B_INPUTS_REQUIRED');process.exitCode=2;
 }else await build({fresh:a['--fresh'],diagnostics:a['--diagnostics'],
   preview:a['--preview'],release:a['--release']},a['--out']);
}
