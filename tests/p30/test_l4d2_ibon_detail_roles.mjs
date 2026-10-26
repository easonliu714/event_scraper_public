import test from "node:test";
import assert from "node:assert/strict";
import {KIND,labels,listRows,assess,scheduleBlockEvidence} from "../../scripts/p30_l4d2_ibon_detail_roles.mjs";
const U="https://ticket.ibon.com.tw/ActivityInfo/Details/40010";
const title="2026 OPEN DREAM WORLD 音樂節";
const row={title,officialUrl:U};
const view={headings:[title],lines:["演出日期：2026/11/14～2026/11/15",
  "售票期間：2026/09/01～2026/11/13",
  "票券使用期間：2026/11/01～2026/12/31",
  "活動地點：臺北市南港展覽館"],pageTitle:title};
test("explicit gate identity not Golden",()=>assert.match(KIND,/NOT_GOLDEN/));
test("event date labeled vs sale time is distinct",()=>{
  const p=labels(view.lines);
  assert.deepEqual(p.map(x=>x.role),["EVENT_DATE_LABEL_ONLY","SALE_WINDOW_NOT_EVENT",
    "VOUCHER_VALIDITY_NOT_EVENT","VENUE_LABEL_ONLY"]);
});
test("no automatic date promotion even when exact title and HTTP200",()=>{
  const a=assess(row,view,{status:200,url:U});
  assert.equal(a.identity,"EXACT_LIST_DETAIL_HEADING");
  assert.equal(a.dateStart,null);
  assert.equal(a.dateEnd,null);
  assert.equal(a.officialActivityScheduleVerified,false);
  assert.equal(a.ticketStatus,"UNKNOWN");
  assert.equal(a.price,null);
});
test("heading mismatch returns no date roles",()=>{
  const a=assess(row,{...view,headings:["Unrelated Artist Event"]},{status:200,url:U});
  assert.equal(a.identity,"DETAIL_TITLE_OR_HTTP_HOLD");
  assert.deepEqual(a.roleEvidence,[]);
  assert.equal(a.goldenVerified,false);
});
test("HTTP error with matching DOM cannot verify",()=>{
  const a=assess(row,view,{status:403,url:U});
  assert.equal(a.identity,"DETAIL_TITLE_OR_HTTP_HOLD");
  assert.deepEqual(a.roleEvidence,[]);
});
test("date without label not promoted",()=>{
  assert.deepEqual(labels(["2026/12/01～2026/12/03"]),[]);
  assert.deepEqual(labels(["2026/12/01 售票期間"]),[]);
});
test("registration and usage validity tags distinguish",()=>{
  const s=labels(["報名期間：2026/10/01至2026/10/10","使用期限：2026/12/31"]);
  assert.equal(s[0].role,"REGISTRATION_WINDOW_NOT_EVENT");
  assert.equal(s[1].role,"VOUCHER_VALIDITY_NOT_EVENT");
});
test("show time as event evidence ONLY, still no accepted schedule",()=>{
  const r=labels(["演出時間：2026-11-06 19:00"]);
  assert.equal(r[0].role,"EVENT_DATE_LABEL_ONLY");
  assert.equal(r[0].status,"RAW_UNPROMOTED_EVIDENCE");
});
test("unknown label ignored",()=>{
  assert.deepEqual(labels(["頁面刊登日期：2026/10/01","頁面更新：2026/10/03"]),[]);
});
test("bounded date fragments",()=>{
  let v=labels(["演出時間："+("2026/10/01 ".repeat(1000))]);
  assert.equal(v[0].evidenceExcerpt.length<=150,true);
  assert.equal(v[0].observedDateTokens.length<=3,true);
});
test("source-bound numeric ID and strict unique URL",()=>{
  const out=listRows([
    {href:U,heading:title,text:""},
    {href:"https://ticket.ibon.com.tw/Web/ActivityInfo/Details/40010",heading:title},
    {href:"https://ticket.ibon.com.tw/ActivityInfo/Details/40011",heading:"2026 音樂祭" },
    {href:"https://other.example/ActivityInfo/Details/40012",heading:"偽造"},
    {href:"https://ticket.ibon.com.tw/ActivityInfo/Details/40014",text:"購票"}]);
  assert.equal(out.length,2);
  assert.equal(out[0].officialUrl,U);
  assert.equal(out[0].dateStart,null);
  assert.equal(out[0].ticketStatus,"UNKNOWN");
  assert.equal(out[0].detailIdentity,"NOT_CHECKED");
  assert.equal(out[0].goldenVerified,false);
});
test("reject CTA disguised as activity",()=>{
  assert.deepEqual(listRows([{href:U,text:"即將開賣"}]),[]);
});
test("reject query/checkout/log-in urls",()=>{
  const out=listRows([{href:U+"?order=1",heading:title},
    {href:"https://ticket.ibon.com.tw/Order/Checkout",heading:title},
    {href:"https://ticket.ibon.com.tw/ActivityInfo/Details/abcde",heading:title}]);
  assert.equal(out.length,0);
});
test("only first three full-year role tokens retained as raw evidence",()=>{
  const q=labels(["活動日期：2026/11/01,2026/11/02,2026/11/03,2026/11/04"]);
  assert.equal(q.length,1);assert.equal(q[0].observedDateTokens.length,3);
});

test("official ibon boxed activity-time section binds next text only",()=>{
  const r=scheduleBlockEvidence(["【活動時間（台灣時間）】",
    "2026年11月7日 14:00 - 16:00", "2026/11/13 14:00 - 16:00",
    "入場資訊請依主辦單位"]);
  assert.equal(r.length,1);
  assert.equal(r[0].role,"ACTUAL_EVENT_TIME_LABELED_RAW_UNPROMOTED");
  assert.deepEqual(r[0].observedFullYearDates,["2026-11-07","2026-11-13"]);
  assert.equal(r[0].status,"RAW_UNPROMOTED_EVIDENCE");
});
test("ibon split date/time vertical-bar style retains full-year date tokens",()=>{
  const r=scheduleBlockEvidence(["日期/時間｜2027.02.20（SAT.）18:00 開演／2027.02.21（SUN.）14:00"]);
  assert.equal(r.length,1);
  assert.deepEqual(r[0].observedFullYearDates,["2027-02-20","2027-02-21"]);
});
test("sale and voucher lines never masquerade as event time",()=>{
  assert.deepEqual(scheduleBlockEvidence([
    "售票時間：2026/10/01～2026/10/31","使用期限：2026/12/31",
    "活動開賣：2026/10/15"]),[]);
});
test("invalid day and bare partial date not treated as full-year event",()=>{
  const r=scheduleBlockEvidence(["【活動時間】","2026/02/29 14:00 / 11/09"]);
  assert.deepEqual(r[0].observedFullYearDates,[]);
});
test("mismatched list-detail must have no event-time evidence",()=>{
  const v=assess(row,{...view,headings:["other"],
    lines:["【活動時間】","2027/02/20"]},{status:200,url:U});
  assert.equal(v.identity,"DETAIL_TITLE_OR_HTTP_HOLD");
  assert.deepEqual(v.scheduleBlockEvidence,[]);
});
