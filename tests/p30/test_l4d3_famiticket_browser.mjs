import test from "node:test";
import assert from "node:assert/strict";
import {HOME,TITLE,KIND,clean,officialDetail,allowedResource,selectExact,classify} from "../../scripts/p30_l4d3_famiticket_browser.mjs";
const ID="A".repeat(45),URL="https://www.famiticket.com.tw/Home/Activity/Info/"+ID;
test("read-only non-Golden Gate identity",()=>assert.match(KIND,/NOT_GOLDEN/));
test("official HTTPS opaque activity link",()=>{
  assert.equal(officialDetail(URL),URL);
  assert.equal(officialDetail("/Home/Activity/Info/"+ID),URL);
});
test("foreign sites and unsafe port excluded",()=>{
  for(const u of ["http://www.famiticket.com.tw/Home/Activity/Info/"+ID,
    "https://evil.com/Home/Activity/Info/"+ID,
    "https://www.famiticket.com.tw.evil.com/Home/Activity/Info/"+ID,
    "https://www.famiticket.com.tw:8080/Home/Activity/Info/"+ID,
    "https://user@www.famiticket.com.tw/Home/Activity/Info/"+ID,
    "file:///tmp/test"])assert.equal(officialDetail(u),null,u);
});
test("query and fragment not mistaken for same ID",()=>{
  assert.equal(officialDetail(URL+"?utm_source=x"),null);
  assert.equal(officialDetail(URL+"#top"),null);
});
test("checkout, login and category not activity link",()=>{
  for(const s of ["/Home/Activity/Search/242","/Home/Login","/Home/Checkout","/Home"])
    assert.equal(officialDetail(s),null,s);
});
test("allow only HTTPS official and known static asset domains",()=>{
  assert.equal(allowedResource(HOME),true);
  assert.equal(allowedResource("https://cdnjs.cloudflare.com/x.css"),true);
  for(const u of ["https://evil.com/x.js","http://cdn.jsdelivr.net/x.js",
    "https://api.unknown.example.com/index","https://evil@cdn.jsdelivr.net/x.js"])
    assert.equal(allowedResource(u),false,u);
});
test("title must equal exact one, never fuzzy",()=>{
  assert.equal(selectExact([{href:URL,heading:TITLE}]).url,URL);
  assert.equal(selectExact([{href:URL,heading:TITLE+" 追加場"}]),null);
  assert.equal(selectExact([{href:URL,heading:"2026 ITF台灣國際旅展"}]),null);
});
test("duplicate identical href not duplicate candidate",()=>{
  let a=selectExact([{href:URL,heading:TITLE},{href:URL,text:TITLE}]);
  assert.equal(a.url,URL);
});
test("two distinct opaque IDs with same title HOLD",()=>{
  assert.equal(selectExact([{href:URL,heading:TITLE},{href:URL+"B",heading:TITLE}]),null);
});
test("detail exact header must be visible for verified identity",()=>{
  const a=classify({title:TITLE,url:URL},
    {headings:[TITLE],exactBodyContainsTitle:true,pageTitle:"FamiTicket",
     visibleChars:270,scriptCount:8,hints:["展出日期：2026/11/06"]},
    {status:200,url:URL});
  assert.equal(a.state,"PUBLIC_BROWSER_EXACT_HEADING_PASS");
  assert.equal(a.eventDateStart,null);
  assert.equal(a.goldenVerified,false);
  assert.equal(a.ticketStatus,"UNKNOWN");
});
test("body title only is not a matched detail heading",()=>{
  const a=classify({title:TITLE,url:URL},
    {headings:[],exactBodyContainsTitle:true,pageTitle:"FamiTicket",
     visibleChars:50,scriptCount:8,hints:[]},{status:200,url:URL});
  assert.equal(a.state,"BROWSER_DETAIL_IDENTITY_HOLD");
});
test("wrong heading and HTTP error HOLD",()=>{
  const data={headings:["Other event"],exactBodyContainsTitle:false,
    pageTitle:"FamiTicket",visibleChars:100,scriptCount:2,hints:[]};
  for(const status of [200,403]){
    assert.equal(classify({title:TITLE,url:URL},data,{status,url:URL}).state,
                 "BROWSER_DETAIL_IDENTITY_HOLD");
  }
});
test("missing list identity always HOLD",()=>{
  assert.equal(classify(null,null,{}).state,"LIST_EXACT_UNIQUE_IDENTITY_HOLD");
});
test("whitespace title normalization deterministic",()=>{
  assert.equal(clean("2026   ITF 台灣國際旅展  "),TITLE);
});
