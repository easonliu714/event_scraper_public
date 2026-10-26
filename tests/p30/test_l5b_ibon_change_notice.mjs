import test from "node:test";
import assert from "node:assert/strict";
import {KIND,changeSignals,scopedNotice,additionalSessionEvidence,compareCurrentRows} from "../../scripts/p30_l5b_ibon_change_notice.mjs";
const PARENT_KIND="EVENTRADAR_P30_L5A_IBON_SESSION_ROLE_REVIEW_ONLY";
const BLOCK_ROLE="ACTUAL_EVENT_TIME_LABELED_RAW_UNPROMOTED";
const row=(id,title,start,raw)=>({
 officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+id,listTitle:title,
 proposedSessions:start.map(x=>({eventStartLocal:x,sourceTimeZone:null})),
 goldenVerified:false,published:false,
});
const block1={role:BLOCK_ROLE,status:"RAW_UNPROMOTED_EVIDENCE",
 heading:"【活動時間（台灣時間）】",
 rawExcerpt:"【活動時間（台灣時間）】 2026年12月19日（土） 開場 16:00 開演 17:00",
 observedFullYearDates:["2026-12-19"]};
const block2={role:BLOCK_ROLE,status:"RAW_UNPROMOTED_EVIDENCE",
 heading:"日期/時間｜2027.02.20（SAT.）18:00 開演 ⏰ 預計 17:00 開放入場／2027.02.21（SUN.）14:00",
 rawExcerpt:"日期/時間｜2027.02.20（SAT.）18:00 開演 ⏰ 預計 17:00 開放入場／2027.02.21（SUN.）14:00 開演（追加場） ⏰ 預計 13:00 開放入場",
 observedFullYearDates:["2027-02-20","2027-02-21"]};
const parent=()=>({
 kind:PARENT_KIND,sourceCount:2,sessionRoleCandidateCount:3,
 sourceRuntime:"DORMANT",published:false,goldenAccepted:false,fieldPromotionCount:0,
 samples:[
   row("12345","RUNIDRE",["2026-12-19T17:00"],block1),
   row("23456","NieR",["2027-02-20T18:00","2027-02-21T14:00"],block2)
 ]});
const current=()=>[
 {officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/12345",
  currentUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/12345",
  listTitle:"RUNIDRE",httpStatus:200,titleExactMatched:true,
  scheduleBlocks:[block1],lines:["最新演出相關資訊／公告：","演出詳情敬請參閱官網","注意事項"]},
 {officialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/23456",
  currentUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/23456",
  listTitle:"NieR",httpStatus:200,titleExactMatched:true,
  scheduleBlocks:[block2],lines:["日期/時間｜2027.02.20（SAT.）18:00 開演",
  "追加場 2027.02.21 14:00"]}
];
test("01 not-Golden status",()=>assert.match(KIND,/NOT_GOLDEN/));
test("02 explicit cancellation signal",()=>{
 for(const s of ["活動取消公告","本場取消，後續將通知","演出取消"])
   assert.ok(changeSignals(s).includes("EVENT_CANCELLATION_SIGNAL_REVIEW"));
});
test("03 explicit postponement signal",()=>{
 for(const s of ["演出延期公告","延期舉辦","原場次改期至2027/01/01"])
   assert.ok(changeSignals(s).includes("EVENT_POSTPONEMENT_SIGNAL_REVIEW"));
});
test("04 additional session independent signal",()=>{
 assert.deepEqual(changeSignals("已公布追加場"),["ADDITIONAL_SESSION_SIGNAL_REVIEW"]);
});
test("05 checkout cancellation unrelated",()=>{
 assert.deepEqual(changeSignals("取消訂單的退款須知"),["AMBIGUOUS_CHANGE_WORD_HOLD"]);
});
test("06 ticket sale moved not event postponement",()=>{
 assert.deepEqual(changeSignals("延後開賣，不影響演出時間"),["SALE_CHANGE_ONLY_NOT_EVENT_TIME"]);
});
test("07 no change language not proof of no changes",()=>{
 const q=scopedNotice(["最新演出相關資訊／公告：","詳細資訊請見官方公布"]);
 assert.equal(q.state,"NOTICE_SECTION_CAPTURED_NO_CONFIRMED_CHANGE_UNKNOWN");
 assert.equal(q.isNoChangesProven,false);
});
test("08 no notice heading is UNKNOWN",()=>{
 const q=scopedNotice(["活動資訊","場次時間"]);
 assert.equal(q.state,"NO_EXPLICIT_NOTICE_SECTION_CAPTURED_UNKNOWN");
 assert.equal(q.isNoChangesProven,false);
});
test("09 scoped notice captures explicit change only inside headed block",()=>{
 const q=scopedNotice(["演出延期", "最新演出相關資訊／公告：",
      "本場取消","注意事項","活動延期"]);
 assert.deepEqual(q.signals,["EVENT_CANCELLATION_SIGNAL_REVIEW"]);
 assert.equal(q.state,"CHANGE_SIGNAL_REQUIRES_ORGANISER_REVIEW");
});
test("10 notice section bounded to 14 and excerpt bounded",()=>{
 const q=scopedNotice(["最新演出公告",...Array.from({length:50},(_,i)=>"第"+i+"項說明")]);
 assert.ok(q.sections[0].boundedLines.length<=14);
 assert.ok(q.sections[0].snippet.length<=720);
 assert.equal(q.isNoChangesProven,false);
});
test("11 additional marker in schedule NOT notice source",()=>{
 const q=additionalSessionEvidence([block1,block2]);
 assert.equal(q.length,1);
 assert.equal(q[0].verifiedAgainstOrganiser,false);
 assert.match(q[0].role,/NOT_AN_INDEPENDENT_CHANGE_NOTICE/);
});
test("12 two current samples exact schedule parity but no Golden",()=>{
 const r=compareCurrentRows(parent(),current());
 assert.equal(r.scheduleParityStatus,"TWO_SAMPLED_DETAIL_SCHEDULES_UNCHANGED");
 assert.equal(r.sourceCount,2);
 assert.equal(r.additionalSessionMarkerCount,1);
 assert.equal(r.organiserConfirmationCount,0);
 assert.equal(r.formalDatePromotionCount,0);
 assert.equal(r.goldenAccepted,false);
 assert.equal(r.accepted44AndroidPreserved,true);
 assert.equal(r.changeNoticeStatus,"NO_CONFIRMED_NOTICE_IN_BOUNDED_CAPTURE_UNKNOWN");
});
test("13 role still no publication, no exact tickets",()=>{
 const r=compareCurrentRows(parent(),current());
 for(const row of r.details){
   assert.equal(row.dateStart,null);
   assert.equal(row.dateEnd,null);
   assert.equal(row.ticketStatus,"UNKNOWN");
   assert.equal(row.price,null);
   assert.equal(row.liveTicketAvailability,"UNKNOWN");
   assert.equal(row.notice.isNoChangesProven,false);
   assert.equal(row.published,false);
 }
});
test("14 changed current show time marked HOLD not accepted",()=>{
 const now=current();now[0].scheduleBlocks[0]={
   ...block1,rawExcerpt:block1.rawExcerpt.replace("17:00","18:00")};
 const r=compareCurrentRows(parent(),now);
 assert.equal(r.scheduleParityStatus,"SOURCE_SCHEDULE_DRIFT_HOLD");
 assert.equal(r.details[0].scheduleParity,"CHANGED_OR_MISSING_SCHEDULE_HOLD");
});
test("15 invalid or unsafe official URL in parent rejected",()=>{
 const p=parent();p.samples[0].officialUrl="https://evil.com/ActivityInfo/Details/12345";
 assert.throws(()=>compareCurrentRows(p,current()),/HOLD_PARENT_UNSAFE_DETAIL_URL|HOLD_PARENT_SOURCE_IDENTITY/);
});
test("16 wrong rendered title must be HOLD",()=>{
 const now=current();now[1].titleExactMatched=false;
 assert.throws(()=>compareCurrentRows(parent(),now),/HOLD_CURRENT_SOURCE_TITLE_IDENTITY/);
});
test("17 HTTP403 or URL redirected not equivalent",()=>{
 const n=current();n[0].httpStatus=403;
 assert.throws(()=>compareCurrentRows(parent(),n),/HOLD_CURRENT_SOURCE_TITLE_IDENTITY/);
 const m=current();m[1].currentUrl="https://ticket.ibon.com.tw/Order/Checkout";
 assert.throws(()=>compareCurrentRows(parent(),m),/HOLD_CURRENT_SOURCE_TITLE_IDENTITY/);
});
test("18 forged parent publication and flags rejected",()=>{
 for(const [key,value] of [["published",true],["sourceRuntime","ACTIVE"],
  ["goldenAccepted",true],["fieldPromotionCount",1]]){
   const p=parent();p[key]=value;
   assert.throws(()=>compareCurrentRows(p,current()),/HOLD_PARENT_L5A_GOVERNANCE/);
 }
});
test("19 full three session identity, not three separate events",()=>{
 const r=compareCurrentRows(parent(),current());
 assert.equal(r.details.length,2);
 assert.equal(r.details.reduce((n,x)=>n+x.currentSampleEventStarts.length,0),3);
});
test("20 no invented approval for additional-show tag",()=>{
 const r=compareCurrentRows(parent(),current());
 assert.equal(r.details[1].scheduleInlineAdditionEvidence[0].verifiedAgainstOrganiser,false);
 assert.equal(r.details[1].notice.state,"NO_EXPLICIT_NOTICE_SECTION_CAPTURED_UNKNOWN");
});
