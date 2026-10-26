import test from "node:test";
import assert from "node:assert/strict";
import {KIND,HOME,normalize,canonicalArticle,isAggregatorOwned,safeAssetHost,titleText,candidatesFromLinks} from "../../scripts/p30_l3bc_strolltimes.mjs";
const A="https://strolltimes.com/events/hsinchu/261016123223/";
const B="https://strolltimes.com/events/new-taipei/261016084730/";
test("immutable role: aggregator, not original organiser",()=>{
  assert.match(KIND,/AGGREGATOR/);
  assert.match(KIND,/NOT_GOLDEN/);
});
test("known current public event articles accepted",()=>{
  assert.equal(canonicalArticle(A),A);
  assert.equal(canonicalArticle(B),B);
  assert.equal(canonicalArticle("/events/hsinchu/261016123223"),A);
  assert.equal(canonicalArticle("https://www.strolltimes.com/events/hsinchu/261016123223/"),A);
});
test("no arbitrary informational URLs or category pages",()=>{
  for(const u of ["/about/","/events/search/","/events/taipei/","/events/singer/",
                  "/privacy-policy/","/","/events/new-taipei/latest",
                  "/events/new-taipei/no-id/"])assert.equal(canonicalArticle(u),null,u);
});
test("no cross-origin article impersonation",()=>{
  for(const u of ["http://strolltimes.com/events/hsinchu/261016123223/",
                 "https://strolltimes.com.evil.org/events/hsinchu/261016123223/",
                 "https://strolltimes.com:8080/events/hsinchu/261016123223/",
                 "https://evil@strolltimes.com/events/hsinchu/261016123223/",
                 "https://other.example.com/events/hsinchu/261016123223/"]){
    assert.equal(canonicalArticle(u),null,u);
  }
});
test("reject tracking query or fragment, fail closed",()=>{
  assert.equal(canonicalArticle(A+"?token=1"),null);
  assert.equal(canonicalArticle(A+"#thing"),null);
});
test("external sources stay external, never original official",()=>{
  assert.equal(isAggregatorOwned("https://strolltimes.com/about/"),true);
  assert.equal(isAggregatorOwned("https://ticket.ibon.com.tw/Index/entertainment"),false);
  assert.equal(safeAssetHost("https://cdn.jsdelivr.net/npm/vue"),true);
  assert.equal(safeAssetHost("https://malicious.com/api"),false);
  assert.equal(safeAssetHost("http://strolltimes.com"),false);
});
test("dedup same article identity and explicit UNKNOWN data roles",()=>{
  const items=candidatesFromLinks([
    {href:A,heading:"2026新竹市萬聖節",text:""},
    {href:A,heading:"重複",text:""},
    {href:B,heading:"",text:"碧潭地景裝置展 遇見小王子漫遊碧潭間"},
    {href:"https://evil.com/events/hsinchu/261016123223/",text:"偽活動"}]);
  assert.equal(items.length,2);
  assert.equal(items[0].aggregatorUrl,A);
  assert.equal(items[0].originalOfficialUrl,null);
  assert.equal(items[0].originalOfficialIdentityState,"NOT_VERIFIED");
  assert.equal(items[0].sourceRole,"THIRD_PARTY_EVENT_AGGREGATOR");
  assert.equal(items[0].dateStart,null);
  assert.equal(items[0].ticketStatus,"UNKNOWN");
  assert.equal(items[0].goldenVerified,false);
  assert.equal(items[0].published,false);
});
test("deny link-only CTA and navigation as event names",()=>{
  const items=candidatesFromLinks([
    {href:A,text:"查看更多"},
    {href:B,text:"首頁"},
    {href:"/events/hsinchu/261016123223/",text:"2026新竹市萬聖節"}]);
  assert.equal(items.length,1);
  assert.equal(items[0].title,"2026新竹市萬聖節");
});
test("normalization never invents content",()=>{
  assert.equal(normalize(" a  \n b "),"a b");
  assert.equal(titleText("  2026   晴空季   "),"2026 晴空季");
  assert.equal(titleText("更多"),null);
  assert.equal(titleText(null),null);
});
test("refuse private or non-article destinations",()=>{
  assert.equal(canonicalArticle("javascript:alert(1)"),null);
  assert.equal(canonicalArticle("mailto:test@strolltimes.com"),null);
  assert.equal(canonicalArticle("//evil.com/events/hsinchu/261016123223/"),null);
});
