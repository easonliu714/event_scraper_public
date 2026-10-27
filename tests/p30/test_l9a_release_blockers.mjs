import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,writeFile,rm,readFile} from "node:fs/promises";
import {resolve} from "node:path";
import {createHash} from "node:crypto";
import {KIND,EXPECTED_L7B,evaluate,build} from "../../scripts/p30_l9a_release_blockers.mjs";
const hash=v=>createHash("sha256").update(v).digest("hex");
function sample(){
 const fres=[],prev=[];
 for(let i=0;i<264;i++){
  const verified=i<5,failed=i>=5&&i<12;
  const id="er7b_"+String(i).padStart(24,"0");
  const title="Sample Event "+i;
  const url="https://www.opentix.life/event/"+(100000+i);
  const status=verified?"DETAIL_TITLE_PARITY_PASS":failed?"HOLD_DETAIL_TITLE_PARITY":"NOT_SAMPLED";
  const field=verified?[{role:i%2===0?"PRICE":"EVENT_PERIOD",label:i%2===0?"票價":"活動日期",
     observedValue:i%2===0?"資訊":"2026/10/27",sourceUrl:url,
     verification:"FRESH_LABEL_OBSERVED_REVIEW_REQUIRED"}]:[];
  const item={candidateId:id,sourcePlatform:"OPENTIX",
    sourceRole:"PLATFORM_LISTED_EVENT_UNVERIFIED",sourceUrl:url,title,
    detailIdentityVerified:verified,detailStatus:status,fieldEvidence:field,
    ticketStatus:"UNKNOWN",dateStart:null,dateEnd:null,price:null,venue:null,
    registrationPeriod:null,saleWindow:null,voucherValidity:null,mergeAllowed:false,
    goldenVerified:false,published:false};
  fres.push(item);
  prev.push({...item,qualityTier:verified?"DETAIL_TITLE_PARITY_PASS":
   failed?"DETAIL_IDENTITY_HOLD":"LIST_ONLY_UNVERIFIED"});
 }
 const fresh={kind:"EVENTRADAR_P30_L7B_FRESH_BOUNDED_CANDIDATES_V1",runId:EXPECTED_L7B,
  candidateOrigin:"L7B_ACTUAL_NEW_PUBLIC_HTTP",actualFreshHTTPRequests:34,
  candidateCount:264,candidateEventRecords:fres,goldenAccepted:0,published:false,
  fullPlatformCoverageVerified:false};
 const diag={kind:"EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1",
  runId:EXPECTED_L7B,platforms:Array.from({length:19},(_,i)=>({platform:"p"+i})),
  counts:{platformsChecked:19,httpOK:16,listPositive:12,listCandidates:264,
  detailAttempts:12,detailHttpOK:12,detailIdentityVerified:5,labelEvidenceObserved:12},
  fullPlatformCoverageVerified:false,published:false,goldenAccepted:0,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  automaticMergeCount:0,automaticHideCount:0,deletedCount:0};
 const freshBytes=Buffer.from(JSON.stringify(fresh));
 const preview={kind:"EVENTRADAR_P30_L7C_ISOLATED_FRESH_REVIEW_PREVIEW_V1",
  sourceRunId:EXPECTED_L7B,sourceCandidateSHA256:hash(freshBytes),
  candidateOrigin:"L7C_PINNED_NEW_HTTP_ARTIFACT_PREVIEW_NOT_A_NEW_CRAWL",
  actualFreshHTTPRequestsInThisGate:0,sourceFreshHTTPRequests:34,
  previewOnly:true,acceptedAndroid44Preserved:true,
  counts:{total:264,verifiedDetail:5,listOnly:252,identityHold:7},
  items:prev,published:false,goldenAccepted:0};
 const raw={fresh:freshBytes,diag:Buffer.from(JSON.stringify(diag)),
  preview:Buffer.from(JSON.stringify(preview))};
 return {fresh,diag,preview,raw};
}
function check(a=sample()){return evaluate(a.fresh,a.diag,a.preview,a.raw)}
const mutation=(fn)=>{const a=sample();fn(a);assert.throws(()=>check(a));};
test("01 contract is not release-readiness approval",()=>assert.match(KIND,/BLOCKER_MATRIX_READONLY/));
test("02 strict current source input valid",()=>assert.equal(sample().fresh.runId,EXPECTED_L7B));
test("03 closed: ten explicit holds and all publication flags false",()=>{
 const x=check();assert.equal(x.blockerCount,10);assert.equal(x.releaseState,"HARD_HOLD_NO_PUBLICATION");
 assert.ok(x.blockers.every(v=>v.value==="HOLD"));assert.equal(x.readyToDeploy,false);
 assert.equal(x.readyToMerge,false);assert.equal(x.readyToEnableWriter,false);
});
test("04 reviewed source count vs detail statuses",()=>{
 const x=check();assert.equal(x.metrics.listCandidates,264);assert.equal(x.metrics.detailTitleParity,5);
 assert.equal(x.metrics.detailIdentityHold,7);assert.equal(x.metrics.reviewOnly,259);
});
test("05 title reviewed is NOT Golden",()=>{
 const x=check();assert.equal(x.goldenAccepted,0);assert.equal(x.published,false);
 assert.equal(x.writerExecuted,false);assert.equal(x.existingAndroid44Preserved,true);
});
test("06 non-numeric PRICE labels are never published",()=>{
 const x=check();assert.equal(x.metrics.ambiguousPriceEvidence,3);
 assert.ok(x.ambiguousPriceReviewOnly.every(y=>y.value==="資訊"));
});
test("07 wrong run ID rejects",()=>mutation(a=>{a.fresh.runId="forged";}));
test("08 wrong preview parent ID rejects",()=>mutation(a=>{a.preview.sourceRunId="forged";}));
test("09 forged fresh source SHA rejects",()=>mutation(a=>{a.preview.sourceCandidateSHA256="0".repeat(64);}));
test("10 stale fake fresh origin rejects",()=>mutation(a=>{a.fresh.candidateOrigin="L7A_OLD";}));
test("11 fresh request count cannot be zero",()=>mutation(a=>{a.fresh.actualFreshHTTPRequests=0;}));
test("12 user-preserved Android identity must remain true",()=>mutation(a=>{a.preview.acceptedAndroid44Preserved=false;}));
test("13 no activity date promotion",()=>mutation(a=>{a.preview.items[0].dateStart="2026-10-27";}));
test("14 no ticket status claim",()=>mutation(a=>{a.fresh.candidateEventRecords[0].ticketStatus="AVAILABLE";}));
test("15 no Golden claim",()=>mutation(a=>{a.preview.goldenAccepted=1;}));
test("16 no Writer or Scheduler claim",()=>mutation(a=>{a.diag.writerExecuted=true;}));
test("17 no rename title across source & preview",()=>mutation(a=>{a.preview.items[0].title="Other event";}));
test("18 no forged external source URL",()=>mutation(a=>{a.preview.items[0].sourceUrl="https://evil.com";}));
test("19 no list or review count drift",()=>mutation(a=>{a.preview.counts.verifiedDetail=6;}));
test("20 no extra duplicate candidate id",()=>mutation(a=>{a.fresh.candidateEventRecords[1].candidateId=a.fresh.candidateEventRecords[0].candidateId;}));
test("21 no date/registration period guessing",()=>mutation(a=>{a.fresh.candidateEventRecords[0].saleWindow="2026-10-01";}));
test("22 no source role drift",()=>mutation(a=>{a.preview.items[0].sourceRole="THIRD_PARTY_AGGREGATOR_ARTICLE";}));
test("23 no unwarranted synthetic field verification",()=>mutation(a=>{a.preview.items[0].fieldEvidence[0].verification="OFFICIAL";}));
test("24 frozen browser provenance current run must be pinned",()=>mutation(a=>{a.diag.counts.detailIdentityVerified=6;}));
test("25 readonly output rejects docs root",async()=>{
 const tmp=await mkdtemp(resolve("p30-l9a-test-"));
 try{
  const a=sample();await writeFile(tmp+"/f.json",a.raw.fresh);
  await writeFile(tmp+"/d.json",a.raw.diag);
  await writeFile(tmp+"/p.json",a.raw.preview);
  await assert.rejects(()=>build({fresh:tmp+"/f.json",diag:tmp+"/d.json",preview:tmp+"/p.json"},"docs/test"),/HOLD_L9A_ISOLATED/);
 }finally{await rm(tmp,{recursive:true,force:true});}
});
test("26 readonly output manifest has matching exact sha and HOLD",async()=>{
 const tmp=await mkdtemp(resolve("p30-l9a-test-"));
 try{
  const a=sample();await writeFile(tmp+"/f.json",a.raw.fresh);
  await writeFile(tmp+"/d.json",a.raw.diag);
  await writeFile(tmp+"/p.json",a.raw.preview);
  const v=await build({fresh:tmp+"/f.json",diag:tmp+"/d.json",preview:tmp+"/p.json"},tmp+"/out");
  const buffer=await readFile(tmp+"/out/release_blocker_matrix.json");
  assert.equal(hash(buffer),v.manifest.filesSHA256["release_blocker_matrix.json"]);
  assert.equal(v.matrix.releaseState,"HARD_HOLD_NO_PUBLICATION");
 }finally{await rm(tmp,{recursive:true,force:true});}
});
