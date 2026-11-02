'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('docs/index.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/); assert(script);
const block=script[1].match(/    \/\/ Formal card summary:[\s\S]*?(?=    function renderList\(\))/); assert(block);
const c={}; vm.runInNewContext(block[0]+';this.price=formalPriceSummary;',c); const price=c.price;
const receipt={accepted:true,role:'EVENT_ADMISSION_PRICE',source:'https://example.org/a',value:'一般票 NT$2,880／3,380；VIP NT$5,880'};
const e={url:receipt.source,price:receipt.value,_formal_field_evidence:{price:receipt}};
assert.match(price(e),/NT\$2,880 起/);
for(const value of ['VIP 升級 NT$200','服務費 NT$200','優惠票 NT$100','一般票 NT$2,880（會員優惠）']) { const r={...e,price:value,_formal_field_evidence:{price:{...receipt,value}}};assert.equal(price(r),'票價詳官方資訊'); }
for(const fields of [{accepted:false},{role:'SERVICE_FEE'},{source:'https://example.org/b'},{value:'another'}]) {const r={...e,_formal_field_evidence:{price:{...receipt,...fields}}};assert.equal(price(r),'票價詳官方資訊');}
assert.equal(price({...e,_formal_field_evidence:null}),'票價詳官方資訊');
assert(html.includes('${formalPriceSummary(e)}'));
assert(html.includes('loading="lazy"'));
console.log('PASS_FORMAL_SUMMARY_FAIL_CLOSED');
