import test from "node:test";
import assert from "node:assert/strict";
import {KIND,MAX_ARTICLES,MAX_REQUESTS,safeCreditUrl,creditRole,
        attributedCredits,makeResult} from "../../scripts/p30_l5e_strolltimes_source_lineage.mjs";
const A="2026新竹市萬聖節";
const data={sourceSectionFound:true,links:[
 {href:"https://www.facebook.com/hsinchu/posts/123456?utm_source=social&fbclid=test",label:"新竹火車站旅遊服務中心 的貼文"},
 {href:"https://www.google.com/maps/place/park",label:"場館地圖"},
 {href:"https://ticket.ibon.com.tw/ActivityInfo/Details/39974",label:"ibon 官方售票平台活動頁"}
]};
test("01 review only never source Golden",()=>assert.match(KIND,/NOT_GOLDEN/));
test("02 maximum six public article details plus homepage",()=>{
 assert.equal(MAX_ARTICLES,6);assert.equal(MAX_REQUESTS,150);
});
test("03 social source citation remains unverified owner",()=>{
 const e=attributedCredits(A,A+"（10/16~10/31）",data);
 assert.equal(e.state,"ATTRIBUTED_LINKS_FOUND_UNVERIFIED");
 assert.equal(e.credits[0].role,"ATTRIBUTED_SOCIAL_POST_ACCOUNT_NOT_VERIFIED");
 assert.equal(e.credits[0].organiserAccountAuthenticityVerified,false);
 assert.equal(e.credits[0].originalOfficialEventDetailVerified,false);
});
test("04 maps is venue link and not an event source",()=>{
 const e=attributedCredits(A,A,data);
 assert.equal(e.credits[1].role,"VENUE_MAP_NOT_EVENT_SOURCE");
 assert.equal(e.credits[1].originalOfficialEventDetailVerified,false);
});
test("05 ticket vendor link not independent same event",()=>{
 const e=attributedCredits(A,A,data);
 assert.equal(e.credits[2].role,"TICKET_SITE_EVENT_IDENTITY_NOT_VERIFIED");
 assert.equal(e.officialEventSourceVerified,false);
});
test("06 gov URL is an institutional candidate but not verified event",()=>{
 assert.equal(creditRole("https://www.hccg.gov.tw/News_Content.aspx?n=1001"),
 "GOV_INSTITUTION_WEBSITE_EVENT_IDENTITY_NOT_VERIFIED");
});
test("07 external news blog does not automatically become producer",()=>{
 assert.equal(creditRole("https://travelblog.example.com/event"),
 "OTHER_REFERENCED_WEBSITE_IDENTITY_NOT_VERIFIED");
});
test("08 only source section links accepted; no section is HOLD",()=>{
 const e=attributedCredits(A,A,{sourceSectionFound:false,links:data.links});
 assert.equal(e.state,"NO_EXPLICIT_SOURCE_SECTION_HOLD");
 assert.deepEqual(e.credits,[]);
});
test("09 list article identity mismatch invalidates all citations",()=>{
 const e=attributedCredits(A,"2026其他萬聖節",data);
 assert.equal(e.state,"ARTICLE_TITLE_MISMATCH_HOLD");
 assert.deepEqual(e.credits,[]);
});
test("10 supplementary date-only title suffix accepted as aggregator title, no event date",()=>{
 const e=attributedCredits(A,A+"（10/16~10/31）",data);
 assert.equal(e.officialEventSourceVerified,false);
});
test("11 rejected non-HTTPS private or impersonating hosts",()=>{
 for(const u of ["http://www.facebook.com/posts/123",
 "https://name:password@facebook.com/post/123",
 "javascript:alert(1)","file:///etc/passwd",
 "https://evil@ticket.ibon.com.tw/ActivityInfo/Details/39974",
 "https://facebook.com:8080/a"])
 assert.equal(safeCreditUrl(u),null,u);
});
test("12 internal StrollTimes related post is not an original source",()=>{
 assert.equal(safeCreditUrl("https://strolltimes.com/events/hsinchu/261016123223/"),null);
 assert.equal(safeCreditUrl("https://www.strolltimes.com/about/"),null);
});
test("13 remove tracking, preserve actual Facebook post ID",()=>{
 const u=safeCreditUrl("https://www.facebook.com/hsinchu/posts/123?fbclid=Y&utm_campaign=x&id=79");
 assert.equal(u,"https://www.facebook.com/hsinchu/posts/123?id=79");
});
test("14 social and government cannot be conflated",()=>{
 assert.notEqual(creditRole("https://www.facebook.com/hsinchu/posts/123"),
 creditRole("https://www.hccg.gov.tw/News_Content.aspx?n=1"));
});
test("15 blank anchor text is not accepted as attributable link",()=>{
 const e=attributedCredits(A,A,{sourceSectionFound:true,links:[{href:"https://example.com/event",label:""}]});
 assert.equal(e.state,"SOURCE_SECTION_NO_ACCEPTED_EXTERNAL_CREDIT_HOLD");
});
test("16 generic navigation text is not attributable",()=>{
 const e=attributedCredits(A,A,{sourceSectionFound:true,links:[{href:"https://example.com/event",label:"更多"}]});
 assert.deepEqual(e.credits,[]);
});
test("17 identical credit URLs deduplicated",()=>{
 const e=attributedCredits(A,A,{sourceSectionFound:true,links:[
  {href:"https://www.hccg.gov.tw/News/123",label:"市府新聞"},
  {href:"https://www.hccg.gov.tw/News/123",label:"同個新聞"}]});
 assert.equal(e.credits.length,1);
});
test("18 cap credit count to twelve and do not execute external websites",()=>{
 const links=Array.from({length:50},(_,i)=>({href:"https://source"+i+".example.com/abc",label:"來源"+i}));
 assert.equal(attributedCredits(A,A,{sourceSectionFound:true,links}).credits.length,12);
});
test("19 official ticket site is still only linked identity evidence",()=>{
 const e=attributedCredits(A,A,{sourceSectionFound:true,links:[{
  href:"https://www.famiticket.com.tw/Home/Activity/Info/"+"A".repeat(40),label:"FamiTicket"
 }]});
 assert.equal(e.credits[0].role,"TICKET_SITE_EVENT_IDENTITY_NOT_VERIFIED");
 assert.equal(e.credits[0].linkedEventTitleIndependentlyMatched,false);
});
test("20 missing source links cannot be used to mark article invalid/expired",()=>{
 const e=attributedCredits(A,A,{sourceSectionFound:true,links:[]});
 assert.equal(e.state,"SOURCE_SECTION_NO_ACCEPTED_EXTERNAL_CREDIT_HOLD");
 assert.equal(e.officialEventSourceVerified,false);
});
test("21 result maintains all zero promotions and published Android",()=>{
 const z=makeResult(Array.from({length:24},()=>({})),[
  {articleIdentity:"AGGREGATOR_ARTICLE_H1_MATCH",credits:attributedCredits(A,A,data).credits}
 ],{homepageHttp:200});
 assert.equal(z.listCandidateCount,24);
 assert.equal(z.attributedCreditCount,3);
 assert.equal(z.firstPartyEventDetailsIndependentlyVerified,0);
 assert.equal(z.formalCandidateEventCount,0);
 assert.equal(z.fieldPromotionCount,0);
 assert.equal(z.originalOfficialEventUrl,null);
 assert.equal(z.goldenAccepted,false);
 assert.equal(z.published,false);
 assert.equal(z.mainAndroid44Preserved,true);
 assert.equal(z.sourceRuntime,"DORMANT");
});
test("22 capped alias links with tracking dedup",()=>{
 const l=[{href:"https://facebook.com/post/99?fbclid=abc",label:"報導"},
          {href:"https://facebook.com/post/99?fbclid=def",label:"相同報導"}];
 assert.equal(attributedCredits(A,A,{sourceSectionFound:true,links:l}).credits.length,1);
});
test("23 reject source with content too long",()=>{
 assert.equal(safeCreditUrl("https://example.com/"+"a".repeat(1000)),null);
});
