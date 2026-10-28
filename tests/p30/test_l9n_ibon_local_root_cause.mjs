import test from 'node:test';
import assert from 'node:assert/strict';
import {IDS,BASE,HOLD,KIND,classify,verifyReport,safeOut} from '../../scripts/p30_l9n_ibon_local_root_cause.mjs';
const p=(over={})=>({
 label:'活動日期',labelTag:'H3',parentTag:'DIV',parentChildren:2,
 relation:'DIRECT_NEXT_SIBLING',childControls:0,otherRoleCount:0,
 childElements:0,directText:'2026/11/08 18:30',...over
});
const rows=()=>IDS.map(id=>({id,url:BASE+id,http:200,sourceTitleMatched:true,
 state:'SOURCE_ID_BOUND_LOCAL_DIAGNOSTICS_REVIEW_ONLY',labelCount:1,probeCount:1,
 categories:[classify(p())],safeReviewCandidates:1,
 formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN'}));
const report=()=>({kind:KIND,sourceOrigin:'FOUR_NORMAL_OFFICIAL_DETAIL_RECAPTURE',
 parentL9MRun:40682420113,parentL9MArtifact:12813381760,parentL9FRun:40494326021,
 parentL9FArtifact:12729277485,
 rows:rows(),sampleCount:4,currentTitleMatchCount:4,reviewOnlyCandidates:4,
 formalFieldPromotions:0,goldenAccepted:0,published:false,writerExecuted:false,
 schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
 existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD});
test('01 exact four source IDs, not 39961',()=>assert.deepEqual(IDS,['39575','39878','39907','39978']));
test('02 valid strict adjacent label/text is REVIEW, not Golden',()=>{
 const x=classify(p());assert.equal(x.category,'DIRECT_LABEL_DATE_TOKEN_REVIEW_ONLY');
 assert.equal(x.sourceBoundReview,true);assert.equal(x.fieldPromoted,false);
});
test('03 button hidden in neighboring cell HOLD',()=>assert.equal(classify(p({childControls:1})).category,'HOLD_INTERACTIVE_CONTROL'));
test('04 role confusion independent of interactive HOLD',()=>assert.equal(classify(p({otherRoleCount:2})).category,'HOLD_OTHER_ROLE_MIXED'));
test('05 both triggers prefer interactive HOLD',()=>assert.equal(classify(p({childControls:1,otherRoleCount:2})).category,'HOLD_INTERACTIVE_CONTROL'));
test('06 child subtree with no direct text HOLD',()=>assert.equal(classify(p({childElements:3,directText:''})).category,'HOLD_NESTED_UNBOUND_TEXT'));
test('07 missing direct neighbor HOLD',()=>assert.equal(classify(null).category,'HOLD_NO_IMMEDIATE_SIBLING'));
test('08 changed label HOLD',()=>assert.equal(classify(p({label:'售票時間'})).category,'HOLD_UNEXPECTED_DOM_TOPOLOGY'));
test('09 unexpected label tag HOLD',()=>assert.equal(classify(p({labelTag:'P'})).category,'HOLD_UNEXPECTED_DOM_TOPOLOGY'));
test('10 wrong parent topology HOLD',()=>assert.equal(classify(p({parentChildren:3})).category,'HOLD_UNEXPECTED_DOM_TOPOLOGY'));
test('11 non-next sibling relationship HOLD',()=>assert.equal(classify(p({relation:'GLOBAL_TEXT'})).category,'HOLD_UNEXPECTED_DOM_TOPOLOGY'));
test('12 no date token is HOLD',()=>assert.equal(classify(p({directText:'詳情以官方為準'})).category,'HOLD_NO_DIRECT_DATE_TOKEN'));
test('13 sale token is wrong event role',()=>assert.equal(classify(p({directText:'2026/11/08 開賣'})).category,'HOLD_WRONG_TIME_ROLE'));
test('14 admission token is wrong event role',()=>assert.equal(classify(p({directText:'入場 19:00'})).category,'HOLD_WRONG_TIME_ROLE'));
test('15 empty text HOLD',()=>assert.equal(classify(p({directText:''})).category,'HOLD_EMPTY_LOCAL_VALUE'));
test('16 unverified two fields cannot be Golden',()=>{let r=report();assert.equal(verifyReport(r),true);assert.equal(r.formalFieldPromotions,0)});
test('17 no title match must not carry field candidates',()=>{const r=report();r.rows[0].sourceTitleMatched=false;assert.throws(()=>verifyReport(r));});
test('18 formal date mutation rejected',()=>{const r=report();r.rows[0].formalDate='2026/11/08';assert.throws(()=>verifyReport(r));});
test('19 published state mutation rejected',()=>{const r=report();r.published=true;assert.throws(()=>verifyReport(r));});
test('20 grade forgery rejected',()=>{const r=report();r.reviewOnlyCandidates=7;assert.throws(()=>verifyReport(r));});
test('21 production paths refused',()=>{
 for(const p of ['.','docs','docs/data.json','scripts/x','tests/x','.github/x','.git/x'])assert.throws(()=>safeOut(p));
});
test('22 locally bound output accepted',()=>assert.ok(safeOut('p30-l9n-evidence').endsWith('p30-l9n-evidence')));
