import test from 'node:test';
import assert from 'node:assert/strict';
import {KIND,ID,URL,HOLD,SAMPLES,INTERVAL_MS,Q_ZIP,F_SHA,
 parents,titleState,observe,analyze,validate} from '../../scripts/p30_l9r_ibon_title_state.mjs';
import {safeOut} from '../../scripts/p30_l9p_ibon_control_types.mjs';
const probe=(x={})=>({readyState:'complete',headings:['來源活動標題'],
 candidates:['來源活動標題'],dateLabelCount:1,...x});
const obs=(x={})=>observe(probe(x),'來源活動標題',0);
const timeline=()=>Array.from({length:SAMPLES},(_,i)=>({...obs(),index:i}));
const report=()=>{const t=timeline();return{kind:KIND,sourceId:ID,sourceUrl:URL,
 http:200,sampleCount:SAMPLES,intervalMs:INTERVAL_MS,timeline:t,analysis:analyze(t),
 parentL9QRun:40721117824,parentL9QArtifact:12829898767,parentL9QZipSHA256:Q_ZIP,
 parentL9QFileSHA256:'a'.repeat(64),parentL9FFileSHA256:F_SHA,
 formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN',formalFieldPromotions:0,
 goldenAccepted:0,published:false,writerExecuted:false,schedulerExecuted:false,
 notifierExecuted:false,mergeExecuted:false,rawHtmlPersisted:false,
 sourceTextPersisted:false,linkUrlsPersisted:false,screenshotsPersisted:false,
 cookiesPersisted:false,existingAndroid44Preserved:true,
 l8CoreAndroidPassPreserved:true,releaseState:HOLD};};
const mutate=fn=>{const r=report();fn(r);assert.throws(()=>validate(r));};
test('01 exact official ID',()=>assert.equal(ID,'39878'));
test('02 exact official URL',()=>assert.equal(URL,'https://ticket.ibon.com.tw/ActivityInfo/Details/39878'));
test('03 bounded passive sample count',()=>assert.equal(SAMPLES,8));
test('04 bounded passive interval',()=>assert.equal(INTERVAL_MS,650));
test('05 pinned Q artifact ZIP digest',()=>assert.equal(Q_ZIP,'0e07aec0a6c8a0524457c58e782906d799e3a7f773d084e876bcf1aaddd3ab48'));
test('06 pinned original F report digest',()=>assert.equal(F_SHA,'81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4'));
test('07 forged parents fail',()=>assert.throws(()=>parents({},Buffer.from('{}'),{},Buffer.from('{}'))));
test('08 exact title match',()=>assert.equal(obs().titleState,'MATCH'));
test('09 absent heading',()=>assert.equal(obs({headings:[],candidates:[]}).titleState,'HOLD_HEADING_ABSENT'));
test('10 not complete with unrelated heading',()=>assert.equal(obs({readyState:'interactive',headings:['導覽'],candidates:['導覽']}).titleState,'HOLD_DOCUMENT_NOT_COMPLETE'));
test('11 no title candidate',()=>assert.equal(obs({headings:['導覽'],candidates:[]}).titleState,'HOLD_NO_H1_H2_CANDIDATE'));
test('12 complete unmatched candidate',()=>assert.equal(obs({headings:['其他活動'],candidates:['其他活動']}).titleState,'HOLD_UNMATCHED_H1_H2_CANDIDATE'));
test('13 candidate fingerprint stable',()=>assert.equal(obs().candidateFingerprint,obs().candidateFingerprint));
test('14 changed candidate fingerprint',()=>assert.notEqual(obs().candidateFingerprint,obs({candidates:['其他活動']}).candidateFingerprint));
test('15 no candidate fingerprint',()=>assert.equal(obs({candidates:[]}).candidateFingerprint,null));
test('16 all matched tail still HOLD',()=>assert.equal(analyze(timeline()).decision,'HOLD_TRANSIENT_TITLE_RENDER_NO_FIELD_PROMOTION'));
test('17 initial absent then match',()=>{const t=timeline();t[0]={...obs({headings:[],candidates:[],readyState:'interactive'}),index:0};const a=analyze(t);assert.equal(a.firstMatchIndex,1);assert.equal(a.earlyAbsentOrNotReady,true);});
test('18 complete nonmatch counted',()=>{const t=timeline();t[1]={...obs({headings:['其他活動'],candidates:['其他活動']}),index:1};assert.equal(analyze(t).nonmatchCompleteCount,1);});
test('19 stable unmatched candidate never proven true mismatch',()=>{const t=timeline().map((_,i)=>({...obs({headings:['其他活動'],candidates:['其他活動']}),index:i}));const a=analyze(t);assert.equal(a.stableUnmatchedCandidateTail,true);assert.equal(a.decision,'HOLD_PERSISTENT_NONMATCH_CANDIDATE_NOT_PROVEN');});
test('20 changing unmatched candidate remains unresolved',()=>{const t=timeline().map((_,i)=>({...obs({headings:[i%2?'甲':'乙'],candidates:[i%2?'甲':'乙']}),index:i}));assert.equal(analyze(t).decision,'HOLD_TITLE_IDENTITY_UNRESOLVED');});
test('21 not-ready tail remains unresolved',()=>{const t=timeline();t[7]={...obs({readyState:'interactive'}),index:7};assert.equal(analyze(t).decision,'HOLD_TITLE_IDENTITY_UNRESOLVED');});
test('22 report validates',()=>assert.equal(validate(report()),true));
test('23 publication forged rejected',()=>mutate(r=>r.published=true));
test('24 Golden forged rejected',()=>mutate(r=>r.goldenAccepted=1));
test('25 date promotion forged rejected',()=>mutate(r=>r.formalDate='2026-11-01'));
test('26 unexpected raw title text rejected',()=>mutate(r=>r.timeline[0].headingText='unsafe'));
test('27 URL extraction rejected',()=>mutate(r=>r.timeline[0].href='https://example.com'));
test('28 wrong official ID rejected',()=>mutate(r=>r.sourceId='39961'));
test('29 altered decision rejected',()=>mutate(r=>r.analysis.decision='PASS'));
test('30 wrong parent ZIP rejected',()=>mutate(r=>r.parentL9QZipSHA256='0'.repeat(64)));
test('31 wrong index rejected',()=>mutate(r=>r.timeline[2].index=9));
test('32 forged source title state rejected',()=>mutate(r=>r.timeline[0].titleState='MATCH_FALSE'));
test('33 malformed fingerprint rejected',()=>mutate(r=>r.timeline[0].candidateFingerprint='raw title'));
test('34 source value cannot be stored',()=>mutate(r=>r.timeline[0].date='2026-11-01'));
test('35 unsafe output directories blocked',()=>{for(const x of ['.','docs','docs/data.json','scripts','tests','.github','.git/config'])assert.throws(()=>safeOut(x));});
test('36 isolated evidence directory allowed',()=>assert.ok(safeOut('p30-l9r-evidence').endsWith('p30-l9r-evidence')));
