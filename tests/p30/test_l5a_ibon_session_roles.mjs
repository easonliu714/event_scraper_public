import test from "node:test";
import assert from "node:assert/strict";
import {KIND,INPUT_KIND,ROLE,officialIbonDetail,isoDate,decodeActivityBlock,transform} from "../../scripts/p30_l5a_ibon_session_roles.mjs";
const block1={role:ROLE,status:"RAW_UNPROMOTED_EVIDENCE",
  heading:"【活動時間（台灣時間）】",
  rawExcerpt:"【活動時間（台灣時間）】 2026年12月19日（土） 開場 16:00 開演 17:00",
  observedFullYearDates:["2026-12-19"]};
const block2={role:ROLE,status:"RAW_UNPROMOTED_EVIDENCE",
  heading:"日期/時間｜2027.02.20（SAT.）18:00 開演  ⏰ 預計 17:00 開放入場／2027.02.21（SUN.）14:00",
  rawExcerpt:"日期/時間｜2027.02.20（SAT.）18:00 開演  ⏰ 預計 17:00 開放入場／2027.02.21（SUN.）14:00 開演（追加場） ⏰ 預計 13:00 開放入場",
  observedFullYearDates:["2027-02-20","2027-02-21"]};
const mkdetail=(num,block)=>({
  requestedOfficialUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+num,
  responseUrl:"https://ticket.ibon.com.tw/ActivityInfo/Details/"+num,
  responseStatus:200,identity:"EXACT_LIST_DETAIL_HEADING",listTitle:"2026 SAMPLE CONCERT "+num,
  dateStart:null,dateEnd:null,price:null,ticketStatus:"UNKNOWN",goldenVerified:false,
  scheduleBlockEvidence:[block]});
const fixture=()=>({kind:INPUT_KIND,sourceRole:"OFFICIAL_TICKET_PLATFORM",
  stats:{listStatus:200},listCount:23,
  details:[mkdetail("12345",block1),mkdetail("23456",block2)],
  sourceRuntime:"DORMANT",verifiedDateCount:0,published:false,goldenAccepted:false,
  writerExecuted:false,notifierExecuted:false,autoHidden:0});
test("01 input output purpose nonGolden",()=>{
  assert.match(KIND,/REVIEW_ONLY/);
  assert.match(INPUT_KIND,/NOT_GOLDEN/);
});
test("02 first activity Tokyo-style weekday and Taiwan timezone",()=>{
  const v=decodeActivityBlock(block1);assert.equal(v.state,"ALL_EXPLICIT_EVENT_START_SEGMENTS_PARSED");
  assert.equal(v.proposals[0].eventStartLocal,"2026-12-19T17:00");
  assert.equal(v.proposals[0].admissionStartLocal,"2026-12-19T16:00");
  assert.equal(v.proposals[0].sourceTimeZone,"Asia/Taipei");
});
test("03 second official two-session date and times",()=>{
  const x=decodeActivityBlock(block2);
  assert.deepEqual(x.proposals.map(a=>a.eventStartLocal),["2027-02-20T18:00","2027-02-21T14:00"]);
  assert.deepEqual(x.proposals.map(a=>a.admissionStartLocal),["2027-02-20T17:00","2027-02-21T13:00"]);
});
test("04 second raw excerpt timezone not assumed",()=>{
  const x=decodeActivityBlock(block2);
  assert.equal(x.proposals[0].sourceTimeZone,null);
  assert.equal(x.proposals[0].sourceTimeZoneStatus,"NOT_EXPLICIT_IN_CAPTURED_BLOCK");
});
test("05 two source detail records produce three review candidates",()=>{
  const x=transform(fixture());
  assert.equal(x.sourceCount,2);
  assert.equal(x.detailSourcesParsed,2);
  assert.equal(x.sessionRoleCandidateCount,3);
  assert.equal(x.overallState,"TWO_DETAIL_SOURCES_EVENT_TIMES_DECODED");
  assert.equal(x.fieldPromotionCount,0);
  assert.equal(x.androidOriginalAccepted44Preserved,true);
});
test("06 proposed date never written into official candidate dateStart/dateEnd",()=>{
  const x=transform(fixture());
  for(const a of x.samples){
    assert.equal(a.dateStart,null);assert.equal(a.dateEnd,null);
    assert.equal(a.ticketStatus,"UNKNOWN");assert.equal(a.price,null);
    assert.equal(a.saleWindow,null);assert.equal(a.voucherValidity,null);
    assert.equal(a.goldenVerified,false);assert.equal(a.published,false);
    for(const p of a.proposedSessions){
      assert.equal(p.proposedOnly,true);
      assert.equal(p.verifiedAgainstOrganiser,false);
      assert.equal(p.admissionIsNotEventStart,true);
    }
  }
});
test("07 no unsafe URL or wrong role/path",()=>{
  assert.equal(officialIbonDetail("https://ticket.ibon.com.tw/ActivityInfo/Details/12345"),true);
  for(const u of ["https://evil.com/ActivityInfo/Details/12345",
    "http://ticket.ibon.com.tw/ActivityInfo/Details/12345",
    "https://ticket.ibon.com.tw/Order/Checkout",
    "https://ticket.ibon.com.tw/ActivityInfo/Details/12345?x=1",
    "https://ticket.ibon.com.tw/ActivityInfo/Details/12345#x",
    "https://ticket.ibon.com.tw/ActivityInfo/Details/abc",
    "https://ticket.ibon.com.tw.evil.com/ActivityInfo/Details/12345"])
    assert.equal(officialIbonDetail(u),false,u);
});
test("08 strict date calendar validity",()=>{
  assert.equal(isoDate(2027,2,29),null);
  assert.equal(isoDate(2024,2,29).iso,"2024-02-29");
  assert.equal(isoDate(2026,12,19).iso,"2026-12-19");
});
test("09 wrong upstream reported day prefix immediately HOLD",()=>{
  const b={...block1,observedFullYearDates:["2026-12-01"]};
  assert.throws(()=>decodeActivityBlock(b),/HOLD_UPSTREAM_DATE_TOKEN_MISMATCH/);
});
test("10 invalid day after correct label HOLD",()=>{
  const b={...block1,rawExcerpt:"【活動時間（台灣時間）】 2026年02月29日 16:00 開演",
    observedFullYearDates:["2026-02-29"]};
  assert.equal(decodeActivityBlock(b).state,"HOLD_INVALID_SOURCE_DATE");
});
test("11 wrong weekday yields no proposed start",()=>{
  const b={...block1,rawExcerpt:block1.rawExcerpt.replace("（土）","（日）")};
  assert.equal(decodeActivityBlock(b).state,"PARTIAL_EVENT_TIME_ROLE_HOLD");
  assert.equal(decodeActivityBlock(b).proposals.length,0);
});
test("12 cancellation notice must not be accepted as event",()=>{
  const b={...block1,rawExcerpt:block1.rawExcerpt.replace("開場","延期 開場")};
  const x=decodeActivityBlock(b);
  assert.equal(x.state,"PARTIAL_EVENT_TIME_ROLE_HOLD");
  assert.equal(x.proposals.length,0);
});
test("13 admission time later than show time requires manual review",()=>{
  const b={...block1,rawExcerpt:block1.rawExcerpt.replace("開場 16:00","開場 19:00")};
  assert.equal(decodeActivityBlock(b).proposals.length,0);
});
test("14 sales/registration/voucher heading cannot create a session",()=>{
  for(const heading of ["售票期間：","票券使用期限：","報名期間："]){
    assert.throws(()=>decodeActivityBlock({...block1,heading,rawExcerpt:heading+" 2026/12/19 開演17:00"}),/HOLD_EVENT_TIME_HEADING/);
  }
});
test("15 full-year date required, no inference from event title",()=>{
  const b={...block1,rawExcerpt:"【活動時間（台灣時間）】 12/19 開演17:00",observedFullYearDates:[]};
  assert.equal(decodeActivityBlock(b).state,"HOLD_BOUNDED_DATE_COUNT");
});
test("16 untrusted block role / promotion flag rejected",()=>{
  assert.throws(()=>decodeActivityBlock({...block1,status:"GOLDEN"}),/HOLD_UNTRUSTED_BLOCK_ROLE/);
  assert.throws(()=>decodeActivityBlock({...block1,role:"SALE_WINDOW_NOT_EVENT"}),/HOLD_UNTRUSTED_BLOCK_ROLE/);
});
test("17 wrong HTTP title cannot contribute event",()=>{
  const x=fixture();x.details[0].identity="DETAIL_TITLE_OR_HTTP_HOLD";
  assert.throws(()=>transform(x),/HOLD_SOURCE_BOUND_DETAIL_IDENTITY/);
});
test("18 exact URL mismatch or duplicate cannot be merged",()=>{
  const x=fixture();x.details[0].responseUrl=x.details[1].responseUrl;
  assert.throws(()=>transform(x),/HOLD_SOURCE_BOUND_DETAIL_IDENTITY/);
  const y=fixture();y.details[1].requestedOfficialUrl=y.details[0].requestedOfficialUrl;
  y.details[1].responseUrl=y.details[0].responseUrl;
  assert.throws(()=>transform(y),/HOLD_SOURCE_BOUND_DETAIL_IDENTITY/);
});
test("19 no writer / notifier / auto hide / Golden",()=>{
  for(const [k,v] of [["published",true],["writerExecuted",true],
    ["notifierExecuted",true],["autoHidden",1],["goldenAccepted",true],
    ["sourceRuntime","ACTIVE"],["verifiedDateCount",3]]){
    const x=fixture();x[k]=v;assert.throws(()=>transform(x),/HOLD_L4D2_EVIDENCE_GOVERNANCE/,k);
  }
});
test("20 partial session has HOLD state and zero promoted fields",()=>{
  const x=fixture();x.details[1].scheduleBlockEvidence[0]={...block2,observedFullYearDates:["2026-12-20"]};
  assert.throws(()=>transform(x),/HOLD_UPSTREAM_DATE_TOKEN_MISMATCH/);
});
test("21 no show time rejects while admission alone remains not an event",()=>{
  const b={...block1,rawExcerpt:"【活動時間（台灣時間）】 2026年12月19日（土） 開場16:00"};
  const x=decodeActivityBlock(b);
  assert.equal(x.proposals.length,0);
  assert.equal(x.state,"PARTIAL_EVENT_TIME_ROLE_HOLD");
});
test("22 bounded multiple explicit blocks, wrong role not copied",()=>{
  const x=fixture();
  x.details[0].scheduleBlockEvidence=[block1,{...block1,heading:"【售票時間】"}];
  assert.throws(()=>transform(x),/HOLD_EVENT_TIME_HEADING|HOLD_ACTIVITY_LABEL_BINDING/);
});
