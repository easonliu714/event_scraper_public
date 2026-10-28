import test from 'node:test';
import assert from 'node:assert/strict';
import {KIND,ID,URL,HOLD,SAMPLES,INTERVAL_MS,P_ZIP,F_SHA,
 parents,controlKind,signature,analyze,validate}
 from '../../scripts/p30_l9q_ibon_hydration.mjs';
import {safeOut} from '../../scripts/p30_l9p_ibon_control_types.mjs';
const snap=(x={})=>({index:0,readyState:'complete',labelCount:1,siblingTag:'DIV',
 directTextPresent:false,anchorCount:0,buttonCount:2,formCount:0,
 inputCount:2,selectCount:0,roleButtonCount:0,controlCount:4,
 titleMatch:true,...x});
const timeline=()=>Array.from({length:SAMPLES},(_,i)=>snap({index:i}));
const report=()=>{
 const t=timeline();
 return{kind:KIND,sourceId:ID,sourceUrl:URL,http:200,sampleCount:SAMPLES,
  intervalMs:INTERVAL_MS,timeline:t,analysis:analyze(t),
  formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN',
  formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
  rawHtmlPersisted:false,sourceTextPersisted:false,linkUrlsPersisted:false,
  screenshotsPersisted:false,cookiesPersisted:false,
  existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD};
};
const mutate=(fn)=>{const r=report();fn(r);assert.throws(()=>validate(r));};
test('01 exact single official ID and URL',()=>{assert.equal(ID,'39878');assert.equal(URL,'https://ticket.ibon.com.tw/ActivityInfo/Details/39878');});
test('02 bounded six passive snapshots',()=>{assert.equal(SAMPLES,6);assert.equal(INTERVAL_MS,700);});
test('03 pinned parent ZIP digest',()=>assert.equal(P_ZIP,'24fbff9dc7d6a2723731a7968e4e13a8740dc1d1cb766ed86f089ddba4cb3f03'));
test('04 pinned original source digest',()=>assert.equal(F_SHA,'81780c6cf5d7fa09239f9d90c5a889b53016c81693d47dc20e8f73a9dc77ffe4'));
test('05 forged parents rejected',()=>assert.throws(()=>parents({},Buffer.from('{}'),{},Buffer.from('{}'))));
test('06 missing label stays HOLD',()=>assert.equal(controlKind(snap({labelCount:0})),'HOLD_LABEL_ABSENT_OR_DUPLICATE'));
test('07 duplicate label stays HOLD',()=>assert.equal(controlKind(snap({labelCount:2})),'HOLD_LABEL_ABSENT_OR_DUPLICATE'));
test('08 absent sibling stays HOLD',()=>assert.equal(controlKind(snap({siblingTag:null})),'HOLD_NO_ADJACENT_REGION'));
test('09 widget cannot be date',()=>assert.equal(controlKind(snap()),'HOLD_WIDGET_CONTROLS_UNTYPED'));
test('10 direct text without controls still untyped',()=>assert.equal(controlKind(snap({controlCount:0,directTextPresent:true})),'HOLD_DIRECT_TEXT_UNTYPED'));
test('11 empty sibling cannot be accepted',()=>assert.equal(controlKind(snap({controlCount:0})),'HOLD_EMPTY_LOCAL_REGION'));
test('12 signature identical',()=>assert.equal(signature(snap()),signature(snap())));
test('13 signature control count drift',()=>assert.notEqual(signature(snap()),signature(snap({inputCount:1}))));
test('14 all stable still widget HOLD',()=>{const a=analyze(timeline());assert.equal(a.stableTail,true);assert.equal(a.decision,'HOLD_WIDGET_CONTROLS_UNTYPED');});
test('15 first seen at initial snapshot',()=>assert.equal(analyze(timeline()).firstLabelIndex,0));
test('16 no hydration claim if initially present',()=>assert.equal(analyze(timeline()).hydrationObserved,false));
test('17 missing to present hydration recognized',()=>{const t=timeline();t[0]=snap({index:0,labelCount:0,siblingTag:null,controlCount:0,buttonCount:0,inputCount:0});const a=analyze(t);assert.equal(a.firstLabelIndex,1);assert.equal(a.hydrationObserved,true);});
test('18 no label never fabricates hydration',()=>{const t=timeline().map((x,i)=>snap({index:i,labelCount:0,siblingTag:null,controlCount:0,buttonCount:0,inputCount:0}));const a=analyze(t);assert.equal(a.firstLabelIndex,null);assert.equal(a.hydrationObserved,false);});
test('19 transient last-tail label causes HOLD',()=>{const t=timeline();t[4]=snap({index:4,labelCount:0,siblingTag:null,controlCount:0,buttonCount:0,inputCount:0});assert.equal(analyze(t).decision,'HOLD_RENDER_HYDRATION_NOT_STABLE');});
test('20 transient last-tail control count causes HOLD',()=>{const t=timeline();t[5]=snap({index:5,inputCount:1,controlCount:3});assert.equal(analyze(t).stableTail,false);});
test('21 title drift overrides widget',()=>{const t=timeline();t[1]=snap({index:1,titleMatch:false});assert.equal(analyze(t).decision,'HOLD_SOURCE_TITLE_PARITY_DRIFT');});
test('22 direct text stable tail never accepted',()=>{const t=timeline().map((x,i)=>snap({index:i,controlCount:0,buttonCount:0,inputCount:0,directTextPresent:true}));const a=analyze(t);assert.equal(a.decision,'HOLD_DIRECT_TEXT_UNTYPED');assert.equal(a.acceptedFields,0);});
test('23 readyState incomplete not called complete',()=>{const t=timeline();t[0]=snap({index:0,readyState:'interactive'});assert.equal(analyze(t).allReadyComplete,false);});
test('24 valid isolated report',()=>assert.equal(validate(report()),true));
test('25 publication forged rejected',()=>mutate(r=>r.published=true));
test('26 Golden forged rejected',()=>mutate(r=>r.goldenAccepted=1));
test('27 formal field forged rejected',()=>mutate(r=>r.formalFieldPromotions=1));
test('28 formal date forged rejected',()=>mutate(r=>r.formalDate='2026-11-01'));
test('29 formal price forged rejected',()=>mutate(r=>r.formalPrice='100'));
test('30 unsafe HTML field rejected',()=>mutate(r=>r.timeline[0].rawHtml='<div>secret</div>'));
test('31 extracted href rejected',()=>mutate(r=>r.timeline[0].href='https://example.com'));
test('32 wrong source URL rejected',()=>mutate(r=>r.sourceUrl='https://example.com'));
test('33 wrong sample length rejected',()=>mutate(r=>r.timeline.pop()));
test('34 wrong timeline index rejected',()=>mutate(r=>r.timeline[2].index=8));
test('35 altered analysis rejected',()=>mutate(r=>r.analysis.acceptedFields=1));
test('36 unsafe output directories blocked',()=>{for(const x of ['.','docs','docs/data.json','scripts','tests','.github','.git/config'])assert.throws(()=>safeOut(x));assert.ok(safeOut('p30-l9q-evidence').endsWith('p30-l9q-evidence'));});
