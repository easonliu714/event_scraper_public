import test from "node:test";
import assert from "node:assert/strict";
import {KIND,ROLE,parseDates,roleFields,findDetailCards,audit} from "../../scripts/p30_l5d_famiticket_field_roles.mjs";
import {TITLE} from "../../scripts/p30_l4d3_famiticket_browser.mjs";
const root="https://www.famiticket.com.tw/Home/Activity/Info/";
const id=s=>root+s.repeat(40);
const cards=()=>[
 {href:id("A"),text:"展覽",alt:TITLE,heading:"",label:""},
 {href:id("A"),text:"",alt:TITLE,heading:"",label:""},
 {href:id("B"),text:"文化幣(限線上)",alt:"2026 展覽示範候選甲",heading:"",label:""},
 {href:id("C"),text:"表演&劇場",alt:"2026 表演示範候選乙",heading:"",label:""},
 {href:id("D"),text:"演唱會",alt:"2026 音樂會示範候選丙",heading:"",label:""},
 {href:"https://evil.com/Home/Activity/Info/"+("Z".repeat(40)),alt:"2026 造假活動"},
];
const row={title:TITLE,url:id("A")};
test("01 stage identity is review-only",()=>assert.match(KIND,/REVIEW_ONLY/));
test("02 full Gregorian date token valid",()=>{
 assert.deepEqual(parseDates("2026/12/19 與 2027.02.20"),["2026-12-19","2027-02-20"]);
});
test("03 day 19 and 20 never truncated",()=>{
 assert.deepEqual(parseDates("2026年12月19日、2027.02.20"),["2026-12-19","2027-02-20"]);
});
test("04 invalid leap date excluded",()=>{
 assert.deepEqual(parseDates("2026/02/29 2024/02/29"),["2024-02-29"]);
});
test("05 never infer year from mm/dd",()=>{
 assert.deepEqual(parseDates("11/06 至 11/09 展覽"),[]);
});
test("06 event span role separated from sales span",()=>{
 const x=roleFields(["展期：2026/11/06 至 2026/11/09","售票期間：2026/10/01 至 2026/11/05"]);
 assert.deepEqual(x.map(v=>v.role),["EVENT_TIME_LABEL_ONLY","SALE_WINDOW_NOT_EVENT"]);
});
test("07 voucher validity distinct from event",()=>{
 const x=roleFields(["票券使用期限：2026/12/31","展覽日期：2026/11/06"]);
 assert.equal(x[0].role,"VOUCHER_VALIDITY_NOT_EVENT");
 assert.equal(x[1].role,"EVENT_TIME_LABEL_ONLY");
});
test("08 registration period excluded",()=>{
 const x=roleFields(["報名期間","2026/10/01～2026/10/20"]);
 assert.equal(x.length,1);
 assert.equal(x[0].role,"REGISTRATION_WINDOW_NOT_EVENT");
 assert.equal(x[0].evidenceBinding,"ADJACENT_VALUE");
});
test("09 admission opening not event start",()=>{
 const x=roleFields(["入場時間：18:30","演出時間：2026/12/19 19:30"]);
 assert.equal(x[0].role,"ADMISSION_NOT_EVENT_START");
 assert.equal(x[1].role,"EVENT_TIME_LABEL_ONLY");
});
test("10 explicit venue, no false event dates",()=>{
 const x=roleFields(["展覽地點：台北世界貿易中心","展出日期：2026/11/06"]);
 assert.equal(x[0].role,"VENUE_LABEL_ONLY");
 assert.deepEqual(x[0].fullYearDateTokens,[]);
});
test("11 no navigation label glue",()=>{
 const x=roleFields(["活動日期","售票期間：2026/11/01"]);
 assert.equal(x[0].sourceQuality,"EMPTY_ROLE_VALUE_HOLD");
 assert.deepEqual(x[0].fullYearDateTokens,[]);
 assert.equal(x[1].role,"SALE_WINDOW_NOT_EVENT");
});
test("12 unlabeled date in article NOT activity interval",()=>{
 assert.deepEqual(roleFields(["大會資訊 2026/11/06～2026/11/09","請按此購票"]),[]);
});
test("13 title calendar year not dateStart",()=>{
 const x=roleFields(["2026 ITF 台灣國際旅展","展覽","時間詳見官方"]);
 assert.deepEqual(x,[]);
});
test("14 branded list card image ALT exact, category-only text ignored",()=>{
 const x=findDetailCards(cards());
 assert.equal(x.state,"UNIQUE_ITF_PLUS_DEDUP_OTHER_CARDS");
 assert.equal(x.rows[0].url,id("A"));
 assert.equal(x.rows[0].title,TITLE);
 assert.equal(x.rows.length,4);
});
test("15 no foreign/checkout links can become samples",()=>{
 const c=cards();
 c.push({href:"https://www.famiticket.com.tw/Home/Checkout",alt:"2026 購票入口"});
 const x=findDetailCards(c);
 assert.equal(x.rows.length,4);
});
test("16 title duplicate with different official detail URLs blocks sample",()=>{
 const c=cards();c.push({href:id("E"),alt:TITLE});
 const x=findDetailCards(c);
 assert.equal(x.state,"ITF_UNIQUE_LIST_IDENTITY_HOLD");
 assert.deepEqual(x.rows,[]);
});
test("17 no ITF exact title blocks sample",()=>{
 const c=cards();c[0].alt="2026 ITF台灣國際旅展";c[1].alt="展覽";
 const x=findDetailCards(c);
 assert.equal(x.state,"ITF_UNIQUE_LIST_IDENTITY_HOLD");
});
test("18 exact same detail title match yields unpromoted fields",()=>{
 const x=audit(row,{headings:[TITLE],lines:["展期：2026/11/06 至 2026/11/09","售票時間：2026/10/01"],
    visibleCharacters:180},{status:200,url:id("A")});
 assert.equal(x.identity,"EXACT_LIST_DETAIL_TITLE_PASS");
 assert.equal(x.fields.length,2);
 assert.equal(x.dateStart,null);
 assert.equal(x.dateEnd,null);
 assert.equal(x.price,null);
 assert.equal(x.ticketStatus,"UNKNOWN");
 assert.equal(x.venue,null);
 assert.equal(x.fieldPromotionCount,0);
 assert.equal(x.goldenVerified,false);
});
test("19 only body mentions activity without heading cannot supply roles",()=>{
 const x=audit(row,{headings:["Other Show"],lines:["展期：2026/11/06"],visibleCharacters:60},
   {status:200,url:id("A")});
 assert.equal(x.identity,"DETAIL_TITLE_OR_HTTP_HOLD");assert.deepEqual(x.fields,[]);
});
test("20 redirect or status403 prohibits fields",()=>{
 const data={headings:[TITLE],lines:["展期：2026/11/06"],visibleCharacters:60};
 for(const http of [{status:403,url:id("A")},{status:200,url:id("B")}])
  assert.equal(audit(row,data,http).fields.length,0);
});
test("21 year+day prefix overlap rejected",()=>{
 assert.deepEqual(parseDates("2027.02.200"),[]);
});
test("22 unknown sale status never inferred from button",()=>{
 const v=roleFields(["立即購票","2026/11/06","展覽日期：2026/11/06"]);
 assert.equal(v.length,1);
 assert.equal(v[0].role,"EVENT_TIME_LABEL_ONLY");
 assert.equal(v[0].officialEventDateAccepted,false);
});
