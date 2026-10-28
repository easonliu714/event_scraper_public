import test from 'node:test';
import assert from 'node:assert/strict';
import {IDS,BASE,KIND,HOLD,controlCause,compareTwo,summarize,validate,safeOut,parents}
 from '../../scripts/p30_l9p_ibon_control_types.mjs';
const p=(x={})=>({labelCount:1,siblingTag:'DIV',siblingChildren:1,
 directTextPresent:false,otherRoleCount:0,anchorCount:1,buttonCount:0,
 formCount:0,inputCount:0,selectCount:0,roleButtonCount:0,controlCount:1,...x});
const dom=(x={})=>({headings:['來源活動標題'],local:p(),...x});
const src={title:'來源活動標題'};
const row=id=>({id,url:BASE+id,http:200,state:'SOURCE_TITLE_TWO_SNAPSHOTS_REVIEW_ONLY',
 ...summarize(src,dom(),dom())});
const report=()=>({kind:KIND,sampleCount:4,rows:IDS.map(row),
 currentTitleBothSnapshots:4,controlTopologyStableCount:4,
 reasonCounts:{HOLD_NAVIGATION_ANCHOR_ONLY:4},
 formalFieldPromotions:0,goldenAccepted:0,published:false,
 writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
 rawHtmlPersisted:false,sourceTextPersisted:false,linkUrlsPersisted:false,
 screenshotsPersisted:false,cookiesPersisted:false,
 existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD});
test('01 four exact official source IDs',()=>assert.deepEqual(IDS,['39575','39878','39907','39978']));
test('02 only anchor in direct adjacent region',()=>assert.equal(controlCause(p()),'HOLD_NAVIGATION_ANCHOR_ONLY'));
test('03 button in direct adjacent region',()=>assert.equal(controlCause(p({anchorCount:0,buttonCount:1})),'HOLD_BUTTON_OR_ROLE_BUTTON'));
test('04 role button in direct adjacent region',()=>assert.equal(controlCause(p({anchorCount:0,roleButtonCount:1})),'HOLD_BUTTON_OR_ROLE_BUTTON'));
test('05 form in direct adjacent region',()=>assert.equal(controlCause(p({anchorCount:0,formCount:1})),'HOLD_FORM_INPUT_OR_SELECT'));
test('06 input in direct adjacent region',()=>assert.equal(controlCause(p({anchorCount:0,inputCount:1})),'HOLD_FORM_INPUT_OR_SELECT'));
test('07 select in direct adjacent region',()=>assert.equal(controlCause(p({anchorCount:0,selectCount:1})),'HOLD_FORM_INPUT_OR_SELECT'));
test('08 anchor and form cannot be accepted',()=>assert.equal(controlCause(p({formCount:1,controlCount:2})),'HOLD_MIXED_LINK_AND_FORM'));
test('09 anchor and button cannot be accepted',()=>assert.equal(controlCause(p({buttonCount:1,controlCount:2})),'HOLD_MIXED_LINK_AND_BUTTON'));
test('10 mixed other date roles override all',()=>assert.equal(controlCause(p({otherRoleCount:1})),'HOLD_OTHER_ROLE_INSIDE_CONTROL_REGION'));
test('11 absent label',()=>assert.equal(controlCause(null),'HOLD_NO_LABEL'));
test('12 missing local label count',()=>assert.equal(controlCause(p({labelCount:0})),'HOLD_LABEL_COUNT_DRIFT'));
test('13 duplicate local label count',()=>assert.equal(controlCause(p({labelCount:2})),'HOLD_LABEL_COUNT_DRIFT'));
test('14 missing sibling',()=>assert.equal(controlCause(p({siblingTag:null})),'HOLD_NO_ADJACENT_REGION'));
test('15 no interactive control this snapshot',()=>assert.equal(controlCause(p({anchorCount:0,controlCount:0})),'HOLD_NO_INTERACTIVE_CONTROL_NOW'));
test('16 unidentified interactive control',()=>assert.equal(controlCause(p({anchorCount:0,controlCount:1})),'HOLD_OTHER_INTERACTIVE'));
test('17 identical two snapshots stable',()=>{
 const x=compareTwo(p(),p());assert.equal(x.stable,true);assert.equal(x.cause,'HOLD_NAVIGATION_ANCHOR_ONLY');
});
test('18 anchor-to-button drift',()=>{
 const x=compareTwo(p(),p({anchorCount:0,buttonCount:1}));assert.equal(x.stable,false);
 assert.equal(x.cause,'HOLD_RENDER_CONTROL_CAUSE_DRIFT');
});
test('19 anchor count changes with same cause',()=>{
 const x=compareTwo(p(),p({anchorCount:2,controlCount:2}));assert.equal(x.stable,false);
 assert.equal(x.cause,'HOLD_RENDER_CONTROL_TOPOLOGY_DRIFT');
});
test('20 sibling tag changes with same cause',()=>{
 const x=compareTwo(p(),p({siblingTag:'SECTION'}));assert.equal(x.stable,false);
 assert.equal(x.cause,'HOLD_RENDER_CONTROL_TOPOLOGY_DRIFT');
});
test('21 other-role drift blocks',()=>{
 const x=compareTwo(p(),p({otherRoleCount:1}));assert.equal(x.stable,false);
});
test('22 stable title and stable control',()=>{
 const x=summarize(src,dom(),dom());assert.equal(x.stableTitle,true);
 assert.equal(x.controlStable,true);assert.equal(x.acceptedFields,0);
});
test('23 title drift at first snapshot blocks',()=>{
 const x=summarize(src,dom({headings:['錯誤活動']}),dom());
 assert.equal(x.controlDecision,'HOLD_SOURCE_TITLE_DRIFT');assert.equal(x.controlStable,false);
});
test('24 title drift at second snapshot blocks',()=>{
 const x=summarize(src,dom(),dom({headings:['錯誤活動']}));
 assert.equal(x.controlDecision,'HOLD_SOURCE_TITLE_DRIFT');assert.equal(x.controlStable,false);
});
test('25 no title heading never allows a field',()=>{
 const x=summarize(src,dom({headings:[]}),dom({headings:[]}));
 assert.equal(x.acceptedFields,0);assert.equal(x.formalDate,null);
});
test('26 four-row control-only report valid',()=>assert.equal(validate(report()),true));
test('27 forged publication fails',()=>{
 const x=report();x.published=true;assert.throws(()=>validate(x));
});
test('28 forged Golden fails',()=>{
 const x=report();x.goldenAccepted=1;assert.throws(()=>validate(x));
});
test('29 forged date fails',()=>{
 const x=report();x.rows[0].formalDate='2026/11/02';assert.throws(()=>validate(x));
});
test('30 extra source ID fails',()=>{
 const x=report();x.rows[0].id='39961';assert.throws(()=>validate(x));
});
test('31 control reason cannot be review-only',()=>{
 const x=report();x.rows[0].controlDecision='ACCEPT';assert.throws(()=>validate(x));
});
test('32 unsafe local metadata field fails',()=>{
 const x=report();x.rows[0].first.href='https://example.com';assert.throws(()=>validate(x));
});
test('33 forged accepted field fails',()=>{
 const x=report();x.rows[0].acceptedFields=1;assert.throws(()=>validate(x));
});
test('34 wrong provenance rejected',()=>assert.throws(()=>parents({},Buffer.from('{}'),{},Buffer.from('{}'))));
test('35 production output paths forbidden',()=>{
 for(const x of ['.','docs','docs/data.json','scripts','tests','.github','.git/config'])
  assert.throws(()=>safeOut(x));
});
test('36 isolated evidence directory allowed',()=>assert.ok(safeOut('p30-l9p-evidence').endsWith('p30-l9p-evidence')));
