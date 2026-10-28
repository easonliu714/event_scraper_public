import test from 'node:test';
import assert from 'node:assert/strict';
import {KIND,IDS,BASE,SAMPLES,INTERVAL_MS,R_ZIP,F_SHA,HOLD,
 parents,readiness,validate} from '../../scripts/p30_l9s_ibon_three_title_readiness.mjs';
import {observe,analyze} from '../../scripts/p30_l9r_ibon_title_state.mjs';
import {safeOut} from '../../scripts/p30_l9p_ibon_control_types.mjs';
const probe=(x={})=>({readyState:'complete',headings:['來源活動標題'],
 candidates:['來源活動標題'],dateLabelCount:1,...x});
const obs=(x={})=>observe(probe(x),'來源活動標題',0);
const timeline=()=>Array.from({length:SAMPLES},(_,i)=>({...obs(),index:i}));
const report=()=>{
 const rows=IDS.map(id=>{
  const t=timeline(),a=analyze(t);
  return{id,url:BASE+id,http:200,finalUrlExact:true,
   state:readiness(a),timeline:t,analysis:a};
 });
 return{kind:KIND,sourceOrigin:'THREE_EXACT_IBON_PUBLIC_CHROMIUM_EIGHT_PASSIVE_SNAPSHOTS',
  parentL9RRun:40731815454,parentL9RArtifact:12835237400,
  parentL9RZipSHA256:R_ZIP,parentL9RFileSHA256:'a'.repeat(64),
  parentL9FFileSHA256:F_SHA,sampleCount:SAMPLES,intervalMs:INTERVAL_MS,rows,
  stableTitleReviewCount:3,formalFieldPromotions:0,goldenAccepted:0,
  published:false,writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,sourceTextPersisted:false,
  linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
};
const mutate=fn=>{const r=report();fn(r);assert.throws(()=>validate(r));};
test('01 exact three new IDs',()=>assert.deepEqual(IDS,['39575','39907','39978']));
test('02 exact canonical URLs',()=>assert.ok(IDS.every(x=>(BASE+x).startsWith('https://ticket.ibon.com.tw/ActivityInfo/Details/'))));
test('03 bounded passive snapshots',()=>assert.equal(SAMPLES,8));
test('04 bounded interval',()=>assert.equal(INTERVAL_MS,600));
test('05 exact R ZIP digest',()=>assert.equal(R_ZIP,'cce75aa2bd82d4a695b58019db8e6c0cee5e703052039f3cb80210dfa70df96a'));
test('06 pinned F report digest',()=>assert.equal(F_SHA,'81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4'));
test('07 forged parents fail',()=>assert.throws(()=>parents({},Buffer.from('{}'),{},Buffer.from('{}'))));
test('08 exact heading match',()=>assert.equal(obs().titleState,'MATCH'));
test('09 missing heading not a mismatch',()=>assert.equal(obs({headings:[],candidates:[]}).titleState,'HOLD_HEADING_ABSENT'));
test('10 not-ready heading not proven mismatch',()=>assert.equal(obs({readyState:'interactive',headings:['其他'],candidates:['其他']}).titleState,'HOLD_DOCUMENT_NOT_COMPLETE'));
test('11 complete nonmatching candidate',()=>assert.equal(obs({headings:['其他'],candidates:['其他']}).titleState,'HOLD_UNMATCHED_H1_H2_CANDIDATE'));
test('12 stable matched tail remains review only',()=>assert.equal(readiness(analyze(timeline())),'REVIEW_STABLE_TITLE_READY_NO_FIELD_PROMOTION'));
test('13 early complete mismatch blocks readiness',()=>{
 const t=timeline();t[0]={...obs({headings:['其他'],candidates:['其他']}),index:0};
 assert.equal(readiness(analyze(t)),'HOLD_COMPLETE_NONMATCH_BEFORE_STABLE_TAIL');
});
test('14 persistent wrong-title candidate never accepted',()=>{
 const t=timeline().map((_,i)=>({...obs({headings:['其他'],candidates:['其他']}),index:i}));
 assert.equal(readiness(analyze(t)),'HOLD_STABLE_UNMATCHED_CANDIDATE');
});
test('15 incomplete final tail stays HOLD',()=>{
 const t=timeline();t[7]={...obs({readyState:'interactive'}),index:7};
 assert.equal(readiness(analyze(t)),'HOLD_TITLE_READINESS_UNRESOLVED');
});
test('16 valid review-only report',()=>assert.equal(validate(report()),true));
test('17 forged publication rejected',()=>mutate(r=>r.published=true));
test('18 forged Golden rejected',()=>mutate(r=>r.goldenAccepted=1));
test('19 wrong exact source ID rejected',()=>mutate(r=>r.rows[0].id='39961'));
test('20 wrong official URL rejected',()=>mutate(r=>r.rows[1].url='https://example.com'));
test('21 raw heading text persistence rejected',()=>mutate(r=>r.rows[0].timeline[0].headingText='raw'));
test('22 wrong R artifact digest rejected',()=>mutate(r=>r.parentL9RZipSHA256='0'.repeat(64)));
test('23 wrong F file digest rejected',()=>mutate(r=>r.parentL9FFileSHA256='0'.repeat(64)));
test('24 wrong snapshot index rejected',()=>mutate(r=>r.rows[2].timeline[0].index=9));
test('25 forged readiness decision rejected',()=>mutate(r=>r.rows[1].state='PASS'));
test('26 forged ready count rejected',()=>mutate(r=>r.stableTitleReviewCount=4));
test('27 unsafe output directories blocked',()=>{
 for(const x of ['.','docs','docs/data.json','scripts','tests','.github','.git/config'])
  assert.throws(()=>safeOut(x));
});
test('28 isolated output directory allowed',()=>assert.ok(safeOut('p30-l9s-evidence').endsWith('p30-l9s-evidence')));
test('29 formal field promotion rejected',()=>mutate(r=>r.formalFieldPromotions=1));
test('30 raw fingerprint rejected',()=>mutate(r=>r.rows[0].timeline[0].candidateFingerprint='raw-title'));
