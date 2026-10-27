import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm,readdir} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {KIND,FRESH_RUN,labelQuality,review,syntheticRollback,allowedOutput,build} from '../../scripts/p30_l9b_field_quality_rollback.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=o=>Buffer.from(JSON.stringify(o));
function sample(){
 const f=[],p=[];
 for(let i=0;i<264;i++){
  const platform=i<3?'Event Go':i<6?'UDN售票網':'OPENTIX',title='Synthetic Activity '+i;
  const id='er7b_'+String(i).padStart(24,'0');
  const url='https://www.opentix.life/event/'+(10000+i);
  const verified=i<5,bad=i>=5&&i<12;
  const data={candidateId:id,title,sourcePlatform:platform,
   sourceRole:'PLATFORM_LISTED_EVENT_UNVERIFIED',sourceUrl:url,
   detailIdentityVerified:verified,
   detailStatus:verified?'DETAIL_TITLE_PARITY_PASS':bad?'HOLD_DETAIL_TITLE_PARITY':'NOT_SAMPLED',
   fieldEvidence:[],ticketStatus:'UNKNOWN',dateStart:null,dateEnd:null,venue:null,price:null,
   registrationPeriod:null,saleWindow:null,voucherValidity:null,mergeAllowed:false,
   published:false,goldenVerified:false};
  f.push(data);p.push({...data,qualityTier:verified?'DETAIL_TITLE_PARITY_PASS':bad?'DETAIL_IDENTITY_HOLD':'LIST_ONLY_UNVERIFIED'});
 }
 const evidence=(i,role,label,value)=>({role,label,observedValue:value,
  verification:'FRESH_LABEL_OBSERVED_REVIEW_REQUIRED',sourceUrl:f[i].sourceUrl});
 f[0].fieldEvidence=[
  evidence(0,'PRICE','票價','資訊'),evidence(0,'VENUE','地點','台北文創中心'),
  evidence(0,'EVENT_PERIOD','演出日期','2026/10/26 20:00'),
  evidence(0,'SALE_PERIOD','售票時間','2026/10/01 12:00')];
 for(let i=1;i<5;i++)f[i].fieldEvidence=[
  evidence(i,'PRICE','票價',i===1?'NT $ 175 ~ 350':'資訊'),
  evidence(i,'VENUE','演出地點','台北市某某館')];
 const fresh={kind:'EVENTRADAR_P30_L7B_FRESH_BOUNDED_CANDIDATES_V1',runId:FRESH_RUN,
  actualFreshHTTPRequests:34,candidateCount:264,candidateEventRecords:f,published:false,goldenAccepted:0};
 const diagnostics={kind:'EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1',runId:FRESH_RUN,
  counts:{platformsChecked:19,httpOK:16,listPositive:12,detailIdentityVerified:5,labelEvidenceObserved:12},
  platforms:Array.from({length:19},(_,i)=>({platform:['中正紀念堂','台北世貿','ibon','FamiTicket','寬宏'][i]||'S'+i,
   http:{state:'HTTP_OK'},listState:'HOLD_NO_LIST_OR_JS_RENDERED',
   listCandidateCount:0,detailAttempted:0,detailIdentityVerified:0})),
  published:false,goldenAccepted:0,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false};
 const preview={kind:'EVENTRADAR_P30_L7C_ISOLATED_FRESH_REVIEW_PREVIEW_V1',
  sourceRunId:FRESH_RUN,sourceFreshHTTPRequests:34,actualFreshHTTPRequestsInThisGate:0,
  items:p,counts:{total:264,verifiedDetail:5,listOnly:252,identityHold:7},
  published:false,goldenAccepted:0};
 const release={kind:'EVENTRADAR_P30_L9A_RELEASE_BLOCKER_MATRIX_READONLY_V1',
  sourceRunId:FRESH_RUN,releaseState:'HARD_HOLD_NO_PUBLICATION',blockerCount:10,
  blockers:Array.from({length:10},(_,i)=>({id:'B'+i,value:'HOLD'})),
  existingAndroid44Preserved:true,published:false,goldenAccepted:0,
  readyToMerge:false,readyToDeploy:false,readyToEnableWriter:false,
  readyToStartScheduler:false,readyToRetireRepos:false};
 const raw={fresh:json(fresh),diagnostics:json(diagnostics)};
 preview.sourceCandidateSHA256=sha(raw.fresh);raw.preview=json(preview);
 release.sourceFreshCandidateSHA256=sha(raw.fresh);
 release.previewSHA256=sha(raw.preview);release.diagnosticsSHA256=sha(raw.diagnostics);
 raw.release=json(release);
 return{fresh,diagnostics,preview,release,raw};
}
const ev=(role,observedValue)=>({role,observedValue,
 verification:'FRESH_LABEL_OBSERVED_REVIEW_REQUIRED'});
const negative=mutate=>{const a=sample();mutate(a);assert.throws(()=>review(a));};
test('01 immutable review-only kind',()=>assert.match(KIND,/FIELD_QUALITY_ROLLBACK_REVIEW/));
test('02 PRICE 資訊 rejected',()=>assert.equal(labelQuality(ev('PRICE','資訊')).quality,'REJECT_GENERIC_NON_PRICE'));
test('03 PRICE 詳情 rejected',()=>assert.equal(labelQuality(ev('PRICE','詳情')).quality,'REJECT_GENERIC_NON_PRICE'));
test('04 PRICE bare date rejected',()=>assert.equal(labelQuality(ev('PRICE','2026/10/26')).quality,'REJECT_NO_PRICE_TOKEN'));
test('05 currency range review-only',()=>assert.deepEqual(labelQuality(ev('PRICE','NT $ 175 ~ 350')),{quality:'PRICE_TOKEN_REVIEW_ONLY',promotable:false}));
test('06 800元 token not Golden',()=>assert.equal(labelQuality(ev('PRICE','800 元')).promotable,false));
test('07 free ticket text not Golden',()=>assert.equal(labelQuality(ev('PRICE','免費')).quality,'FREE_TEXT_REVIEW_ONLY'));
test('08 venue generic text rejected',()=>assert.equal(labelQuality(ev('VENUE','資訊')).quality,'REJECT_UNSPECIFIC_VENUE'));
test('09 venue proper-name only review',()=>assert.equal(labelQuality(ev('VENUE','台北流行音樂中心')).quality,'VENUE_TEXT_REVIEW_ONLY'));
test('10 event period token role reviewed',()=>assert.equal(labelQuality(ev('EVENT_PERIOD','2026/10/26 20:00')).quality,'TIME_ROLE_TOKEN_REVIEW_ONLY'));
test('11 sale event period conflict HOLD',()=>assert.equal(labelQuality(ev('EVENT_PERIOD','2026/10/01 開始販售')).quality,'HOLD_TIME_ROLE_CONFLICT'));
test('12 sale period date token review',()=>assert.equal(labelQuality(ev('SALE_PERIOD','2026/10/01 12:00')).quality,'TIME_ROLE_TOKEN_REVIEW_ONLY'));
test('13 date label without time rejected',()=>assert.equal(labelQuality(ev('SALE_PERIOD','詳細資訊')).quality,'REJECT_NO_DATE_OR_TIME_TOKEN'));
test('14 forged verified evidence fails',()=>assert.throws(()=>labelQuality({...ev('VENUE','台北市'),verification:'VERIFIED'})));
test('15 unknown field role fails',()=>assert.throws(()=>labelQuality(ev('FAKE','2026/10/26'))));
test('16 full 264:5:259 + 12 sources and HARD_HOLD',()=>{const r=review(sample());assert.equal(r.fieldReview.total,12);
 assert.equal(r.sourceCounts.candidates,264);assert.equal(r.sourceCounts.reviewPending,259);
 assert.equal(r.formalFieldPromotions,0);assert.equal(r.releaseState,'HARD_HOLD_NO_PUBLICATION');});
test('17 special adapters still HOLD',()=>{const r=review(sample());for(const name of ['中正紀念堂','台北世貿','ibon','FamiTicket']){
 const a=r.sourceAdapterReview.find(x=>x.platform===name);
 assert.equal(a.resolutionStatus,'HOLD_ADAPTER_NOT_FRESH_VERIFIED');}});
test('18 fake source SHA rejects',()=>negative(x=>x.preview.sourceCandidateSHA256='0'.repeat(64)));
test('19 forged run ID rejects',()=>negative(x=>x.fresh.runId='FAKE'));
test('20 fabricated approval rejects',()=>negative(x=>x.release.blockers[0].value='PASS'));
test('21 invented activity date rejects',()=>negative(x=>x.preview.items[0].dateStart='2026-10-26'));
test('22 invented live ticket rejects',()=>negative(x=>x.fresh.candidateEventRecords[0].ticketStatus='AVAILABLE'));
test('23 altered canonical URL rejects',()=>negative(x=>x.preview.items[0].sourceUrl='https://evil.test/'));
test('24 L9A premature release rejects',()=>negative(x=>x.release.readyToDeploy=true));
test('25 spoofed detail parity rejects',()=>negative(x=>x.preview.counts.verifiedDetail=6));
test('26 unexpected Scheduler side-effect rejects',()=>negative(x=>x.diagnostics.schedulerExecuted=true));
test('27 duplicate row identity rejects',()=>negative(x=>x.fresh.candidateEventRecords[1].candidateId=x.fresh.candidateEventRecords[0].candidateId));
test('28 production folder output forbidden',()=>{for(const v of ['docs/data.json','scripts/alpha','.github/workflows','.', 'tests/a'])
 assert.throws(()=>allowedOutput(v),v);});
test('29 synthetic corrupted content can be restored byte-for-byte',async()=>{
 const dir=await mkdtemp(resolve('p30-l9b-test-'));
 try{const b=Buffer.from('clean synthetic baseline');const result=await syntheticRollback(dir,b);
  assert.equal(result.state,'PASS_SYNTHETIC_ROLLBACK_ONLY');
  assert.equal(result.baselineSHA256,result.restoredSHA256);
  assert.equal(result.productionRollbackVerified,false);
  assert.deepEqual(await readdir(dir),[]);
 }finally{await rm(dir,{recursive:true,force:true});}
});
test('30 isolated output manifest and temp cleanup',async()=>{
 const dir=await mkdtemp(resolve('p30-l9b-test-'));
 try{const a=sample(),paths={};
  for(const k of ['fresh','diagnostics','preview','release']){
   paths[k]=join(dir,k+'.json');await writeFile(paths[k],a.raw[k]);
  }
  const {report,manifest}=await build(paths,join(dir,'out'));
  assert.equal(report.rollbackSimulation.productionRollbackVerified,false);
  assert.equal(manifest.releaseState,'HARD_HOLD_NO_PUBLICATION');
  for(const [name,digest] of Object.entries(manifest.outputSHA256))
   assert.equal(sha(await readFile(join(dir,'out',name))),digest);
  assert.deepEqual((await readdir(join(dir,'out'))).sort(),
   ['field_quality_review.json','manifest.json','platform_adapter_gaps.json','rollback_simulation.json'].sort());
 }finally{await rm(dir,{recursive:true,force:true});}
});
