import test from "node:test";
import assert from "node:assert/strict";
import {KIND,IDS,ROOT,HOLD,validateParent,evaluatePair,review,validateReport,safeOut} from "../../scripts/p30_l9l_ibon_four_field_semantics.mjs";
const sample=(label,value,extra={})=>({label,value,relation:"DIRECT_SIBLING",distance:1,otherRoleCount:0,interactive:false,...extra});
const source=()=>({kind:"EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1",
 parentL9ERun:40449476633,additionalSampleSize:5,additionalTitleParity:5,
 formalFieldPromotions:0,goldenAccepted:0,published:false,releaseState:HOLD,
 samples:["39575","39878","39907","39961","39978"].map(id=>({
 candidateId:"ibon:"+id,officialUrl:ROOT+id,titleParity:true,
 detailState:"DETAIL_TITLE_PARITY_PASS",listTitle:"臺灣活動展演 "+id}))});
test("01 typed Gate",()=>assert.match(KIND,/SEMANTIC_REVIEW/));
test("02 exact stable four excluding 39961",()=>assert.deepEqual(IDS,["39575","39878","39907","39978"]));
test("03 correct pinned source",()=>{let s=source();assert.equal(validateParent(s,Buffer.from(JSON.stringify(s))).rows.length,4)});
test("04 wrong source kind rejected",()=>{let s=source();s.kind="OLD";assert.throws(()=>validateParent(s,Buffer.from(JSON.stringify(s))))});
test("05 wrong run rejected",()=>{let s=source();s.parentL9ERun=1;assert.throws(()=>validateParent(s,Buffer.from(JSON.stringify(s))))});
test("06 identity URL tamper rejected",()=>{let s=source();s.samples[0].officialUrl="https://evil.test";assert.throws(()=>validateParent(s,Buffer.from(JSON.stringify(s))))});
test("07 title proof required",()=>{let s=source();s.samples[0].titleParity=false;assert.throws(()=>validateParent(s,Buffer.from(JSON.stringify(s))))});
test("08 golden tamper rejected",()=>{let s=source();s.goldenAccepted=1;assert.throws(()=>validateParent(s,Buffer.from(JSON.stringify(s))))});
test("09 source bytes mismatch rejected",()=>{let s=source();let raw=Buffer.from(JSON.stringify(s));s.published=true;assert.throws(()=>validateParent(s,raw))});
test("10 event date source review",()=>assert.equal(evaluatePair(sample("活動日期","2026/11/12 18:00")).quality,"EVENT_PERIOD_SOURCE_BOUND_REVIEW_ONLY"));
test("11 sale period separate",()=>assert.equal(evaluatePair(sample("售票期間","2026/10/28")).role,"SALE_PERIOD"));
test("12 admission separate",()=>assert.equal(evaluatePair(sample("入場時間","18:30")).role,"ADMISSION_TIME"));
test("13 registration separate",()=>assert.equal(evaluatePair(sample("報名期間","2026/10/28")).role,"REGISTRATION_PERIOD"));
test("14 voucher separate",()=>assert.equal(evaluatePair(sample("票券有效期限","2026/11/01")).role,"VOUCHER_VALIDITY"));
test("15 venue generic reject",()=>assert.equal(evaluatePair(sample("場地","資訊")).quality,"REJECT_GENERIC_VENUE"));
test("16 venue text review",()=>assert.equal(evaluatePair(sample("演出地點","臺北場館")).role,"VENUE"));
test("17 PRICE 資訊 rejected",()=>assert.equal(evaluatePair(sample("票價","資訊")).quality,"REJECT_GENERIC_PRICE"));
test("18 price numeric review",()=>assert.equal(evaluatePair(sample("票價","NT$ 700")).quality,"PRICE_SOURCE_BOUND_REVIEW_ONLY"));
test("19 session no split",()=>assert.equal(evaluatePair(sample("場次","兩場")).quality,"SESSION_REVIEW_NO_SPLIT"));
test("20 unbound page body rejected",()=>assert.equal(evaluatePair(sample("活動日期","2026/11/12",{relation:"BODY"})).quality,"HOLD_UNBOUND_OR_AMBIGUOUS"));
test("21 multiple roles same fragment rejected",()=>assert.equal(evaluatePair(sample("活動日期","2026/11/12",{otherRoleCount:1})).quality,"HOLD_UNBOUND_OR_AMBIGUOUS"));
test("22 click control rejected",()=>assert.equal(evaluatePair(sample("活動日期","2026/11/12",{interactive:true})).quality,"HOLD_UNBOUND_OR_AMBIGUOUS"));
test("23 cross sale date rejected",()=>assert.equal(evaluatePair(sample("演出日期","2026/11/12 開賣")).quality,"HOLD_ROLE_CONFLICT"));
test("24 missing date token rejected",()=>assert.equal(evaluatePair(sample("活動日期","請查官方")).quality,"REJECT_NO_TIME_TOKEN"));
test("25 unknown label not inferred",()=>assert.equal(evaluatePair(sample("資訊","2026/11/12")),null));
test("26 mismatch suppresses field review",()=>assert.deepEqual(review([sample("活動日期","2026/11/12")],false),{accepted:[],rejected:[]}));
test("27 title matched review remains unverified",()=>{let v=review([sample("票價","NT$ 700")],true);assert.equal(v.accepted[0].formalFieldPromoted,false)});
test("28 oversized DOM evidence is HOLD",()=>assert.throws(()=>review(Array(51).fill(sample("票價","100元")),true)));
test("29 formal production path blocked",()=>{for(let x of [".","docs","scripts/test","tests/a",".git",".github"])assert.throws(()=>safeOut(x))});
test("30 only 4 distinct IDs",()=>assert.equal(new Set(IDS).size,4));
