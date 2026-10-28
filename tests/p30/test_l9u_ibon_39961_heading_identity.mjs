import test from 'node:test';
import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {KIND,HOLD,K_HEAD,K_ZIP,H_SHA,N,MS,parents,validFinal,listIdentity,
 snapshot,analyze,validate,safeOut} from '../../scripts/p30_l9u_ibon_39961_heading_identity.mjs';

const list='https://ticket.ibon.com.tw/Index/entertainment';
const detail='https://ticket.ibon.com.tw/ActivityInfo/Details/39961';
const row=(title,id='39961')=>({href:'/ActivityInfo/Details/'+id,cardTitle:title});
const snap=(headings=[],candidates=[],readyState='complete',i=0)=>
 snapshot({headings,candidates,readyState},'Current Event','Historical Event',i);
const good=()=>Array.from({length:N},(_,i)=>snap(['Current Event'],['Current Event'],'complete',i));
function report(){
 const timeline=good();
 return{kind:KIND,parentL9KHead:K_HEAD,parentL9KRun:40673236521,
  parentL9KArtifact:12809656497,parentL9KZipSHA256:K_ZIP,
  parentL9KFileSHA256:'a'.repeat(64),parentL9HRun:40516301527,
  parentL9HArtifact:12740505389,parentL9HFileSHA256:H_SHA,
  sourceId:'39961',navigationsAttempted:2,sampleCount:N,intervalMs:MS,
  listSameIdTitleCount:1,listState:'ONE_SAME_ID_TITLE',detailState:'HOLD_REVIEW_ONLY',
  listHTTP:200,detailHTTP:200,listFinal:true,detailFinal:true,
  listSameAsK:true,timeline,analysis:analyze(timeline,true),
  historicMismatchRetained:true,formalIdentityCertified:false,
  formalFieldPromotions:0,goldenAccepted:0,published:false,
  writerExecuted:false,schedulerExecuted:false,notifierExecuted:false,
  mergeExecuted:false,rawHtmlPersisted:false,sourceTextPersisted:false,
  linkUrlsPersisted:false,screenshotsPersisted:false,cookiesPersisted:false,
  networkBodiesPersisted:false,releaseState:HOLD};
}
const cases=[
 ['exact official list URL',()=>assert.equal(validFinal(list,list),true)],
 ['exact official detail URL',()=>assert.equal(validFinal(detail,detail),true)],
 ['wrong host rejected',()=>assert.equal(validFinal('https://example.org/Index/entertainment',list),false)],
 ['wrong path rejected',()=>assert.equal(validFinal(detail+'/123',detail),false)],
 ['query rejected',()=>assert.equal(validFinal(detail+'?id=39961',detail),false)],
 ['hash rejected',()=>assert.equal(validFinal(detail+'#foo',detail),false)],
 ['insecure protocol rejected',()=>assert.equal(validFinal(detail.replace('https','http'),detail),false)],
 ['credential URL rejected',()=>assert.equal(validFinal('https://u:p@ticket.ibon.com.tw/ActivityInfo/Details/39961',detail),false)],
 ['malformed URL rejected',()=>assert.equal(validFinal('not-url',detail),false)],
 ['one same-card ID',()=>assert.deepEqual([listIdentity([row('Current Event')]).state,listIdentity([row('Current Event')]).count],['ONE_SAME_ID_TITLE',1])],
 ['other ID excluded',()=>assert.equal(listIdentity([row('Current Event','39962')]).state,'HOLD_ID_NOT_IN_LIST')],
 ['same ID contradictory cards rejected',()=>assert.equal(listIdentity([row('Current Event'),row('Other Event')]).state,'HOLD_AMBIGUOUS_SAME_ID')],
 ['ID without title rejected',()=>assert.equal(listIdentity([row('')]).state,'HOLD_ID_NOT_IN_LIST')],
 ['list bound 500',()=>assert.throws(()=>listIdentity(Array(501).fill(row('Current Event'))))],
 ['matching H1/H2',()=>assert.equal(snap(['Current Event'],['Current Event']).state,'MATCH_CURRENT_H1H2')],
 ['non-complete candidate',()=>assert.equal(snap(['Other Event'],['Other Event'],'interactive').state,'NOT_COMPLETE')],
 ['complete no heading',()=>assert.equal(snap([],[]).state,'COMPLETE_NO_HEADING')],
 ['complete only H3/H4',()=>assert.equal(snap(['活動日期'],[]).state,'COMPLETE_NO_H1H2')],
 ['historic-only H1/H2',()=>assert.equal(snap(['Historical Event'],['Historical Event']).state,'HOLD_HISTORIC_ONLY_H1H2')],
 ['different H1/H2',()=>assert.equal(snap(['Other Event'],['Other Event']).state,'HOLD_OTHER_H1H2_CANDIDATE')],
 ['fingerprint only, no title in output',()=>{const x=snap(['Other Event'],['Other Event']);assert.match(x.candidateFingerprint,/^[a-f0-9]{16}$/);assert.equal(JSON.stringify(x).includes('Other Event'),false);}],
 ['current match does not certify history',()=>{const a=analyze(good(),true);assert.equal(a.decision,'REVIEW_CURRENT_H1H2_STABLE_HISTORIC_CONFLICT_OPEN');assert.equal(a.historicalL9HMismatchStillOpen,true);}],
 ['source list drift holds',()=>assert.equal(analyze(good(),false).decision,'HOLD_OFFICIAL_LIST_DRIFT_FROM_K')],
 ['stable different heading holds',()=>{const t=Array.from({length:N},(_,i)=>snap(['Other Event'],['Other Event'],'complete',i));assert.equal(analyze(t,true).decision,'HOLD_COMPLETE_STATE_NONMATCH_CANDIDATE');}],
 ['historic only holds',()=>{const t=good();t[0]=snap(['Historical Event'],['Historical Event'],'complete',0);assert.equal(analyze(t,true).preMatchCompleteCounts.historicOnly,1);}],
 ['other candidate before match holds',()=>{const t=good();t[0]=snap(['Other Event'],['Other Event'],'complete',0);assert.equal(analyze(t,true).decision,'HOLD_COMPLETE_STATE_NONMATCH_CANDIDATE');}],
 ['transient no heading is review only',()=>{const t=good();t[0]=snap([],[],'complete',0);assert.equal(analyze(t,true).preMatchCompleteCounts.absent,1);assert.equal(analyze(t,true).decision,'REVIEW_CURRENT_H1H2_STABLE_HISTORIC_CONFLICT_OPEN');}],
 ['short timeline rejects',()=>assert.throws(()=>analyze(good().slice(1),true))],
 ['nominal report validated',()=>assert.equal(validate(report()),true)],
 ['publication blocked',()=>{const r=report();r.published=true;assert.throws(()=>validate(r));}],
 ['golden blocked',()=>{const r=report();r.goldenAccepted=1;assert.throws(()=>validate(r));}],
 ['formal fields blocked',()=>{const r=report();r.formalFieldPromotions=1;assert.throws(()=>validate(r));}],
 ['historic contradiction retained',()=>{const r=report();r.historicMismatchRetained=false;assert.throws(()=>validate(r));}],
 ['no source text persistence',()=>{const r=report();r.sourceTextPersisted=true;assert.throws(()=>validate(r));}],
 ['no raw HTML persistence',()=>{const r=report();r.rawHtmlPersisted=true;assert.throws(()=>validate(r));}],
 ['no network body persistence',()=>{const r=report();r.networkBodiesPersisted=true;assert.throws(()=>validate(r));}],
 ['no scheduler',()=>{const r=report();r.schedulerExecuted=true;assert.throws(()=>validate(r));}],
 ['sample count immutable',()=>{const r=report();r.sampleCount=10;assert.throws(()=>validate(r));}],
 ['timeline index immutable',()=>{const r=report();r.timeline[2].index=7;assert.throws(()=>validate(r));}],
 ['parent H digest pinned',()=>{const r=report();r.parentL9HFileSHA256='b'.repeat(64);assert.throws(()=>validate(r));}],
 ['missing K parent fails closed',()=>assert.throws(()=>parents({},Buffer.from('{}'),{},Buffer.from('{}')))],
 ['missing H parent fails closed',()=>{const k={kind:'invalid'};assert.throws(()=>parents(k,Buffer.from(JSON.stringify(k)),{},Buffer.from('{}')));}],
 ['output in scripts rejected',()=>assert.throws(()=>safeOut('scripts/l9u-evidence'))],
 ['output in docs rejected',()=>assert.throws(()=>safeOut('docs/l9u-evidence'))],
 ['output at root rejected',()=>assert.throws(()=>safeOut('.'))],
 ['isolated output permitted',()=>assert.equal(safeOut('p30-l9u-evidence'),resolve('p30-l9u-evidence'))],
];
assert.equal(cases.length,46);
for(const [name,fn] of cases)test(name,fn);