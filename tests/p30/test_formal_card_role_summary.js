'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('docs/index.html','utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/);
assert(script);
const helpers = script[1].match(/\/\/ P30-L8 formal list summary[\s\S]*?(?=    function renderList\(\))/);
assert(helpers,'L8 formal price+modal helper anchor');
const ctx={
  URL,
  isCandidateOfficialUrl(raw){
    try {
      const u = new URL(raw);
      return u.protocol === 'https:' && !!u.hostname && !u.username && !u.password;
    } catch {return false;}
  }
};
vm.runInNewContext(helpers[0]+';this.api={formalCardPriceSummary,formalEventDetailEvidence};',ctx);
const {formalCardPriceSummary:summary,formalEventDetailEvidence:detail}=ctx.api;
function e(price){const url='https://official.example/event/1';return {url,price,formal_field_pass:true,golden_accepted:true,_formal_field_evidence:{price:{source:url,value:price,role:'EVENT_ADMISSION_PRICE',decision:'GOLDEN_ACCEPTED',accepted:true,observed_at:'2026-11-02T12:30:00+08:00'}}};}
assert.equal(summary(e('NT$2880')),'NT$2,880（詳官方）');
assert.equal(summary(e('NT$2,880')),'NT$2,880（詳官方）');
assert.equal(summary(e('一般票 NT$2,880／3,380／3,880／4,880；VIP 套票 NT$5,880／6,880')),'NT$2,880 起（詳官方）');
assert.equal(summary(e('標準票 NT$1,680、2,280；VIP 升級 NT$2,900')),'NT$1,680 起（詳官方）');
for(const price of [
  '一般票 NT$2,880／會員優惠 NT$1,280',
  '一般票 NT$2,880 加 NT$200 服務費',
  '一般票 NT$2,880／3,380、日期 2026-11-28',
  '身障票 NT$1,840／一般票 NT$2,880',
  '預售票 NT$150／原價 NT$250'
]) assert.equal(summary(e(price)),'票價詳官方資訊',price);
const untrustedTier=e('一般票 NT$2,880／3,380');
untrustedTier._formal_field_evidence.price.decision='REVIEW';
assert.equal(summary(untrustedTier),'票價詳官方資訊');
assert.equal(summary(e('新台幣 150 元')),'NT$150（詳官方）');
assert.equal(summary(e('免費')),'免費（詳官方）');
assert.equal(summary(e('免門票')),'免費（詳官方）');
for(const p of [
  'NT$2,880／3,880','一般票 NT$2,880／VIP 加價 NT$200','VIP 升級 NT$200',
  'NT$150 預售','會員 NT$490','門票 NT$600 加 NT$200 服務費',
  'NT$0','NT$1000000','2026-11-28','依官方','未確認','詳內文','優惠 NT$250'
]){
  assert.equal(summary(e(p)),'票價詳官方資訊',p);
}
assert.equal(summary({...e('NT$2880'),_candidate:{scope:'CANDIDATE_PREVIEW_ONLY'}}),'票價詳官方資訊');
assert.equal(summary(null),'票價詳官方資訊');
// Independent overlap audit #226 vs #227: never certify plain legacy price text.
assert.equal(summary({url:'https://official.example/event/1',price:'NT$2880'}),'票價詳官方資訊');
const good=e('NT$2880');
for (const broken of [
  {...good,golden_accepted:false},
  {...good,formal_field_pass:false},
  {...good,_formal_field_evidence:null},
  {...good,_formal_field_evidence:{price:{...good._formal_field_evidence.price,accepted:false}}},
  {...good,_formal_field_evidence:{price:{...good._formal_field_evidence.price,decision:'REVIEW'}}},
  {...good,_formal_field_evidence:{price:{...good._formal_field_evidence.price,role:'VENUE_ADVERTISED_PRICE'}}},
  {...good,_formal_field_evidence:{price:{...good._formal_field_evidence.price,source:'https://official.example/event/2'}}},
  {...good,_formal_field_evidence:{price:{...good._formal_field_evidence.price,value:'NT$100'}}},
  {...good,_formal_field_evidence:{price:{...good._formal_field_evidence.price,observed_at:'2026-11-02T12:30:00'}}}
]) assert.equal(summary(broken),'票價詳官方資訊');
const stamp='2026-11-02T12:30:00+08:00';
const base={...e('NT$2,880'),formal_field_pass:true,golden_accepted:true,detail_evidence:[
  {source:'https://official.example/event/1',role:'SALE_START',label:'開賣時間',value:'10:00',decision:'GOLDEN_ACCEPTED',observed_at:stamp},
  {source:'https://official.example/event/other',role:'EVENT_DATE',label:'跨活動',value:'錯誤',decision:'GOLDEN_ACCEPTED',observed_at:stamp},
  {source:'https://official.example/event/1',role:'INVENTORY',label:'誤當庫存',value:'可售',decision:'GOLDEN_ACCEPTED',observed_at:stamp},
  {source:'https://official.example/event/1',role:'SERVICE_FEE',label:'未驗',value:'NT$200',decision:'REVIEW',observed_at:stamp},
  {source:'https://official.example/event/1',role:'EVENT_DATE',label:'無時區',value:'2026-11-29',decision:'GOLDEN_ACCEPTED',observed_at:'2026-11-02T12:30:00'}
]};
const allowed=detail(base);
assert.equal(allowed.length,1);
assert.equal(allowed[0].role,'SALE_START');
assert.equal(detail({...base,golden_accepted:false}).length,0);
assert.equal(detail({...base,formal_field_pass:false}).length,0);
assert.equal(detail({...base,_candidate:{scope:'CANDIDATE_PREVIEW_ONLY'}}).length,0);
assert.match(html,/formalCardPriceSummary\(e\)/);
assert.match(html,/class="formal-card-price"/);
assert.match(html,/formalEventDetailEvidence\(ev\)/);
assert.match(html,/<img src="\$\{e\.img_url\}" class="card-img" loading="lazy">/);
assert.match(html,/img\.src = ev\.img_url/);
assert.match(html,/function applyFilters\(\)/);
assert.match(html,/function renderPagination\(\)/);
assert.match(html,/function openCandidateDetail\(/);
assert.match(html,/function closeCandidateReview\(/);
assert.match(html,/if \(candidateReviewActive\) return/);
console.log('PASS_L8_FORMAL_CARD_ROLE_SUMMARY_MODAL_AND_REGRESSION');
