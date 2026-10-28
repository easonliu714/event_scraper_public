import test from "node:test";
import assert from "node:assert/strict";
import {KIND,IDS,HOLD,parents,roles,verdict,inspect,safeOut} from "../../scripts/p30_l9m_ibon_neighbor_reasons.mjs";
const sample=(value,extra={})=>({relation:"NEXT_SIBLING",hops:1,value,interactive:false,otherRoleCount:0,descendants:0,imageOnly:false,...extra});
const fixture=()=>{
 const l={kind:"EVENTRADAR_P30_L9L_FOUR_IBON_DETAIL_SEMANTIC_REVIEW_V1",
  sampleCount:4,titleParityCount:4,reviewPairCount:0,rejectedPairCount:4,
  formalFieldPromotions:0,goldenAccepted:0,published:false,releaseState:HOLD,
  results:IDS.map(id=>({id,url:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,
   http:200,titleParity:true,accepted:[],rejected:[{quality:"REJECT_NO_TIME_TOKEN"}]}))};
 const f={kind:"EVENTRADAR_P30_L9F_IBON_PINNED_DETAIL_ROLE_REVIEW_V1",
  additionalSampleSize:5,additionalTitleParity:5,formalFieldPromotions:0,
  goldenAccepted:0,published:false,releaseState:HOLD,
  samples:[...IDS,"39961"].map(id=>({candidateId:"ibon:"+id,
    officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,
    titleParity:true,listTitle:"台灣活動演出 "+id}))};
 return {l,f,lb:Buffer.from(JSON.stringify(l)),fb:Buffer.from(JSON.stringify(f))};
};
test("01 exact gate kind",()=>assert.match(KIND,/NEIGHBOR_REASON/));
test("02 four IDs exclude current 39961 drift",()=>assert.deepEqual(IDS,["39575","39878","39907","39978"]));
test("03 source lineage two parents",()=>{const x=fixture();assert.equal(parents(x.l,x.lb,x.f,x.fb).originals.length,4)});
test("04 source bytes cannot be forged",()=>{const x=fixture();x.l.reviewPairCount=4;assert.throws(()=>parents(x.l,x.lb,x.f,x.fb))});
test("05 source exact four parity must hold",()=>{const x=fixture();x.l.results[0].titleParity=false;x.lb=Buffer.from(JSON.stringify(x.l));assert.throws(()=>parents(x.l,x.lb,x.f,x.fb))});
test("06 historic original title required",()=>{const x=fixture();x.f.samples[0].listTitle="";x.fb=Buffer.from(JSON.stringify(x.f));assert.throws(()=>parents(x.l,x.lb,x.f,x.fb))});
test("07 cross-artifact identity URL cannot differ",()=>{const x=fixture();x.f.samples[0].officialUrl="https://evil.test/";x.fb=Buffer.from(JSON.stringify(x.f));assert.throws(()=>parents(x.l,x.lb,x.f,x.fb))});
test("08 prior Golden tamper denied",()=>{const x=fixture();x.l.goldenAccepted=1;x.lb=Buffer.from(JSON.stringify(x.l));assert.throws(()=>parents(x.l,x.lb,x.f,x.fb))});
test("09 EVENT, SALE, ADMISSION separate typed labels",()=>{assert.equal(roles["活動日期"],"EVENT_PERIOD");assert.equal(roles["售票時間"],"SALE_PERIOD");assert.equal(roles["入場時間"],"ADMISSION_TIME")});
test("10 exact local date token review-only",()=>{const v=verdict("活動日期",sample("2026/10/28"));assert.equal(v.reason,"SOURCE_BOUND_REVIEW_ONLY");assert.equal(v.fieldPromotion,false)});
test("11 missing neighbor explicit",()=>assert.equal(verdict("活動日期",null).reason,"NO_LOCAL_NEIGHBOR"));
test("12 nested subnode not safely bound",()=>assert.equal(verdict("活動日期",sample("",{descendants:3})).reason,"NESTED_CHILDREN_VALUE_NOT_BOUND"));
test("13 empty neighbor distinct",()=>assert.equal(verdict("活動日期",sample("")).reason,"EMPTY_VALUE"));
test("14 image-only label remains unknown",()=>assert.equal(verdict("活動日期",sample("",{imageOnly:true})).reason,"IMAGE_ONLY_NOT_TEXT"));
test("15 global page body denied",()=>assert.equal(verdict("活動日期",sample("2026/10/28",{relation:"PAGE_BODY"})).reason,"UNAPPROVED_RELATION"));
test("16 2-hop ancestor denied",()=>assert.equal(verdict("活動日期",sample("2026/10/28",{hops:2})).reason,"TOO_DISTANT"));
test("17 interactive control denied",()=>assert.equal(verdict("活動日期",sample("2026/10/28",{interactive:true})).reason,"AMBIGUOUS_OR_INTERACTIVE"));
test("18 other role on same element denied",()=>assert.equal(verdict("活動日期",sample("2026/10/28",{otherRoleCount:2})).reason,"AMBIGUOUS_OR_INTERACTIVE"));
test("19 event date conflicts with sale tokens",()=>assert.equal(verdict("活動日期",sample("2026/10/28 售票")).reason,"CROSS_ROLE_DATE"));
test("20 no date time token fails",()=>assert.equal(verdict("活動日期",sample("詳見官方")).reason,"NO_TIME_TOKEN"));
test("21 PRICE 資訊 not a price",()=>assert.equal(verdict("票價",sample("資訊")).reason,"GENERIC_NON_PRICE"));
test("22 numeric price only review",()=>assert.equal(verdict("票價",sample("NT$ 500")).reviewable,true));
test("23 venue generic rejected",()=>assert.equal(verdict("場地",sample("待公告")).reason,"GENERIC_VENUE"));
test("24 unknown label never silently inferred",()=>assert.equal(verdict("介紹",sample("2026/10/28")).reason,"UNKNOWN_LABEL"));
test("25 no contexts yields zero evidence",()=>{let v=inspect({contexts:[]},true);assert.equal(v.accepted,0);assert.equal(v.diagnostics.length,0)});
test("26 title parity failure suppresses all evidence",()=>{let v=inspect({contexts:[{label:"活動日期",probes:[sample("2026/10/28")]}]},false);assert.equal(v.diagnostics.length,0)});
test("27 matched label absence produces reason",()=>{let v=inspect({contexts:[{label:"活動日期",tag:"H3",parentTag:"DIV",probes:[]}]},true);assert.equal(v.reasonCounts.NO_LOCAL_NEIGHBOR,1)});
test("28 bounded review remains unverified",()=>{let v=inspect({contexts:[{label:"活動日期",tag:"H3",parentTag:"DIV",probes:[sample("2026/10/28")]}]},true);assert.equal(v.accepted,1);assert.equal(v.diagnostics[0].fieldPromotion,false)});
test("29 context bomb rejected",()=>assert.throws(()=>inspect({contexts:Array(17).fill({label:"活動日期",probes:[]})},true)));
test("30 probe bomb rejected",()=>assert.throws(()=>inspect({contexts:[{label:"活動日期",probes:Array(7).fill(sample("2026/10/28"))}]},true)));
test("31 no formal output paths",()=>{for(const v of [".","docs","docs/data.json","scripts/test","tests/a",".git",".github"])assert.throws(()=>safeOut(v))});
