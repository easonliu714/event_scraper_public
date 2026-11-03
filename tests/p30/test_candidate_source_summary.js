'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('docs/index.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/);
assert(script,'PWA inline script');
const helpers=script[1].match(/\/\/ L8: only an exact-source receipt[\s\S]*?(?=    \/\/ Review-only: an explicit local-file gesture)/);
assert(helpers,'summary helper block');
const ctx={URL,isCandidateOfficialUrl(s){try{let u=new URL(s);return u.protocol==='https:'&&!!u.hostname&&!u.username&&!u.password}catch{return false}}};
vm.runInNewContext(helpers[0]+';this.api={candidatePriceSummary,candidateReviewImage,candidateReviewDetailEvidence};',ctx);
const {candidatePriceSummary:price,candidateReviewImage:image,candidateReviewDetailEvidence:detail}=ctx.api;
const receipt={role:'EVENT_ADMISSION_PRICE',decision:'REVIEW'};
assert.match(price('一般票 NT$2,880／3,380／3,880／4,880；VIP 套票 NT$5,880（另加收每張 NT$200 手續費）',receipt),/NT\$2,880 起/);
assert.match(price('預售單日 NT$150／原價 NT$250；預售雙日 NT$250／原價 NT$500',receipt),/單日預售 NT\$150 起/);
for(const x of ['VIP 升級 NT$200','NT$200 手續費','一般票 NT$800（會員優惠）','優惠價 NT$490']){
 assert.equal(price(x,receipt),'票價詳官方資訊');
}
assert.equal(price('一般票 NT$2,880',null),'票價詳官方資訊');
assert.equal(price('一般票 NT$2,880',{role:'SERVICE_FEE',decision:'REVIEW'}),'票價詳官方資訊');
const row={url:'https://official.example/event/123',img_url:'https://img.example/cover.jpg'};
const stamp='2026-11-02T12:00:00+08:00';
const m={sources:[row.url]};
assert.equal(image(row,m),null);
m.image_evidence={source:row.url,image_url:row.img_url,role:'EVENT_IMAGE',decision:'REVIEW',observed_at:stamp};
assert.equal(image(row,m),row.img_url);
m.image_evidence.source='https://official.example/event/other';
assert.equal(image(row,m),null);
m.image_evidence.source=row.url;
m.detail_evidence=[
 {source:row.url,label:'公告開賣',value:'09/17 12:00',role:'SALE_START',decision:'REVIEW',observed_at:stamp},
 {source:'https://official.example/event/other',label:'跨活動',value:'NT$100',role:'EVENT_ADMISSION_PRICE',decision:'REVIEW',observed_at:stamp},
 {source:row.url,label:'票量',value:'有票',role:'INVENTORY',decision:'REVIEW',observed_at:stamp},
 {source:row.url,label:'舊時間',value:'10:00',role:'SALE_START',decision:'REVIEW',observed_at:'2026-11-02T12:00:00'}
];
assert.equal(detail(row,m).length,1);
assert.match(html,/referrerPolicy = 'no-referrer'/);
assert.match(html,/loading = 'lazy'/);
assert.match(html,/evidence\.hidden = true/);
console.log('PASS_L8_PRICE_ROLE_AND_IMAGE_FAIL_CLOSED');
