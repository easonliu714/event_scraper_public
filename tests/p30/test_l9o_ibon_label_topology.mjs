import test from 'node:test';
import assert from 'node:assert/strict';
import {IDS,BASE,HOLD,KIND,norm,titleDecision,localDecision,summarize,
 validate,safeOut,parents} from '../../scripts/p30_l9o_ibon_label_topology.mjs';
const o=(x={})=>({labelTag:'SPAN',parentTag:'DIV',siblingTag:'DIV',
 labelDirect:true,siblingChildCount:0,siblingDirectText:true,
 hasDateToken:true,interactiveCount:0,otherRoleCount:0,...x});
const dom=(x={})=>({headings:['原始活動名稱'],ogTitle:'',documentTitle:'',observations:[o()],...x});
const src={title:'原始活動名稱'};
const row=(id)=>({id,url:BASE+id,http:200,state:'TITLE_EXACT_LOCAL_TOPOLOGY_REVIEW_ONLY',
 previousL9NTitleMatched:id!=='39575',title:titleDecision(src.title,dom()),
 strictH3LabelCount:0,l9mSelectorLabelCount:1,labelTagCounts:{SPAN:1},
 observations:[{labelTag:'SPAN',parentTag:'DIV',siblingTag:'DIV',directText:true,
 interactiveCount:0,otherRoleCount:0,siblingChildCount:0,siblingDirectText:true,
 hasDateToken:true,localCause:'DIRECT_LABEL_LOCAL_TOKEN_REVIEW_ONLY',fieldPromoted:false}],
 localReviewOnlyCount:1,formalFieldPromotions:0,formalDate:null,formalPrice:null,ticketStatus:'UNKNOWN'});
const report=()=>({kind:KIND,sampleCount:4,rows:IDS.map(row),currentExactHeadingCount:4,
 l9mScopeLabelCount:4,l9nH3LabelCount:0,localReviewOnlyCount:4,
 formalFieldPromotions:0,goldenAccepted:0,published:false,writerExecuted:false,
 schedulerExecuted:false,notifierExecuted:false,mergeExecuted:false,
 rawHtmlPersisted:false,cookiesPersisted:false,screenshotsPersisted:false,
 existingAndroid44Preserved:true,l8CoreAndroidPassPreserved:true,releaseState:HOLD});
test('01 four immutable official IDs',()=>assert.deepEqual(IDS,['39575','39878','39907','39978']));
test('02 normalize punctuation and whitespace',()=>assert.equal(norm(' 原始，活動名稱 '),norm('原始活動名稱')));
test('03 title heading exact only source bound',()=>assert.equal(titleDecision(src.title,dom()).kind,'SOURCE_TITLE_HEADING_EXACT'));
test('04 metadata-only match must not be heading exact',()=>{
 const x=titleDecision(src.title,dom({headings:['別的活動'],ogTitle:src.title}));
 assert.equal(x.kind,'HOLD_TITLE_META_ONLY');assert.equal(x.headingExact,false);
});
test('05 document title only is hold',()=>{
 const x=titleDecision(src.title,dom({headings:['別的活動'],documentTitle:src.title}));
 assert.equal(x.kind,'HOLD_TITLE_DOCUMENT_ONLY');assert.equal(x.headingExact,false);
});
test('06 heading drift remains hold',()=>assert.equal(titleDecision(src.title,dom({headings:['另一活動']})).kind,'HOLD_TITLE_HEADING_DRIFT'));
test('07 no heading remains hold',()=>assert.equal(titleDecision(src.title,dom({headings:[]})).kind,'HOLD_TITLE_NO_HEADING'));
test('08 missing original title hold',()=>assert.equal(titleDecision('',dom()).kind,'HOLD_MISSING_ORIGINAL_TITLE'));
test('09 direct label with adjacent date only REVIEW',()=>assert.equal(localDecision(o()),'DIRECT_LABEL_LOCAL_TOKEN_REVIEW_ONLY'));
test('10 interactive neighbor HOLD',()=>assert.equal(localDecision(o({interactiveCount:1})),'HOLD_INTERACTIVE_LOCAL'));
test('11 mixed other role HOLD',()=>assert.equal(localDecision(o({otherRoleCount:2})),'HOLD_MIXED_OTHER_ROLE_LOCAL'));
test('12 interactive takes precedence over mixed',()=>assert.equal(localDecision(o({interactiveCount:1,otherRoleCount:1})),'HOLD_INTERACTIVE_LOCAL'));
test('13 no sibling HOLD',()=>assert.equal(localDecision(o({siblingTag:null})),'HOLD_NO_ADJACENT_SIBLING'));
test('14 nested text without direct proof HOLD',()=>assert.equal(localDecision(o({siblingChildCount:3,siblingDirectText:false})),'HOLD_NESTED_LOCAL_NOT_BOUND'));
test('15 direct text empty HOLD',()=>assert.equal(localDecision(o({siblingDirectText:false})),'HOLD_EMPTY_DIRECT_LOCAL'));
test('16 no date token HOLD',()=>assert.equal(localDecision(o({hasDateToken:false})),'HOLD_NO_DIRECT_DATE_TOKEN'));
test('17 label with descendant-only text HOLD',()=>assert.equal(localDecision(o({labelDirect:false})),'HOLD_LABEL_NOT_DIRECT_TEXT'));
test('18 absent label HOLD',()=>assert.equal(localDecision(null),'HOLD_NO_DIRECT_LABEL'));
test('19 alternate SPAN label counted but h3 not counted',()=>{
 const x=summarize(dom(),src);assert.equal(x.l9mSelectorLabelCount,1);
 assert.equal(x.strictH3LabelCount,0);assert.equal(x.localReviewOnlyCount,1);
});
test('20 h3 label counted independently',()=>{
 const x=summarize(dom({observations:[o({labelTag:'H3'})]}),src);
 assert.equal(x.strictH3LabelCount,1);assert.equal(x.l9mSelectorLabelCount,1);
});
test('21 title drift rejects review even with date-shaped local text',()=>{
 const x=summarize(dom({headings:['別的活動']}),src);
 assert.equal(x.localReviewOnlyCount,0);assert.equal(x.formalFieldPromotions,0);
});
test('22 valid four-row report retains Golden zero',()=>assert.equal(validate(report()),true));
test('23 false field promotion rejected',()=>{
 const x=report();x.rows[0].formalDate='2026/11/01';assert.throws(()=>validate(x));
});
test('24 false Golden rejected',()=>{
 const x=report();x.goldenAccepted=1;assert.throws(()=>validate(x));
});
test('25 missing source identity cannot carry review candidate',()=>{
 const x=report();x.rows[0].title.headingExact=false;assert.throws(()=>validate(x));
});
test('26 unexpected candidate ID rejected',()=>{
 const x=report();x.rows[0].id='39961';assert.throws(()=>validate(x));
});
test('27 provenance parent tamper rejected',()=>{
 assert.throws(()=>parents({kind:KIND},Buffer.from('{}'),{},Buffer.from('{}')));
});
test('28 production output directories forbidden',()=>{
 for(const x of ['.','docs','docs/data.json','scripts','tests','.git','.github/workflows'])assert.throws(()=>safeOut(x));
});
test('29 isolated evidence output accepted',()=>assert.ok(safeOut('p30-l9o-evidence').endsWith('p30-l9o-evidence')));
