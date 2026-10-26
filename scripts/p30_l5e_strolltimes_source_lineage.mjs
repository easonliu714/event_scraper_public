#!/usr/bin/env node
/**
 * P30-L5-E1: StrollTimes explicitly attributed "資料來源" links.
 * Third-party article -> directly attributed outbound citation is ONLY lineage
 * evidence; not verified primary organiser, activity/date/price/availability.
 * One homepage + <=6 article pages via stock Chromium, no outbound follow.
 */
import { chromium } from "playwright";
import { mkdir,writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {HOME,canonicalArticle,safeAssetHost,candidatesFromLinks,articleHeadingMatches} from "./p30_l3bc_strolltimes.mjs";
export const KIND="EVENTRADAR_P30_L5E1_STROLLTIMES_ATTRIBUTED_SOURCE_LINEAGE_NOT_GOLDEN";
export const MAX_ARTICLES=6,MAX_REQUESTS=150;
const AGGREGATOR=new Set(["strolltimes.com","www.strolltimes.com"]);
const MAPS=new Set(["maps.google.com","www.google.com","goo.gl","maps.app.goo.gl"]);
const SOCIAL=new Set(["facebook.com","www.facebook.com","m.facebook.com","fb.watch",
  "instagram.com","www.instagram.com","threads.net","www.threads.net","x.com","twitter.com"]);
const TICKET=new Set(["ticket.ibon.com.tw","www.famiticket.com.tw","kktix.com","www.kktix.com",
  "tixcraft.com","tixfun.com","www.opentix.life","www.accupass.com","ticket.com.tw"]);
const GENERIC=/^(?:首頁|更多|相關文章|閱讀更多|購票|活動資訊|活動詳情|點我前往|Google 地圖|地圖)$/u;
function trim(s){return String(s??"").replace(/[\u200B-\u200D\uFEFF]/g,"").replace(/\s+/g," ").trim().slice(0,250);}
export function safeCreditUrl(href){
 try{
  const u=new URL(href);
  if(u.protocol!=="https:"||u.username||u.password||u.port||
      !u.hostname.includes(".")||u.href.length>800||/[\x00-\x1f]/.test(href))return null;
  if(AGGREGATOR.has(u.hostname))return null;
  // Defang only tracking query keys, preserve legitimate post/story identity.
  for(const k of [...u.searchParams.keys()]){
   if(/^utm_/i.test(k)||["fbclid","gclid","igshid","mibextid"].includes(k))u.searchParams.delete(k);
  }
  return u.toString();
 }catch{return null;}
}
export function creditRole(url){
 try{
  const h=new URL(url).hostname.toLowerCase();
  if(MAPS.has(h))return "VENUE_MAP_NOT_EVENT_SOURCE";
  if(SOCIAL.has(h))return "ATTRIBUTED_SOCIAL_POST_ACCOUNT_NOT_VERIFIED";
  if(TICKET.has(h)||h.endsWith(".kktix.cc"))return "TICKET_SITE_EVENT_IDENTITY_NOT_VERIFIED";
  if(h.endsWith(".gov.tw")||h==="gov.tw"||h.endsWith(".edu.tw"))
    return "GOV_INSTITUTION_WEBSITE_EVENT_IDENTITY_NOT_VERIFIED";
  return "OTHER_REFERENCED_WEBSITE_IDENTITY_NOT_VERIFIED";
 }catch{return "INVALID_HOLD";}
}
export function attributedCredits(articleTitle,h1,raw){
 if(!articleHeadingMatches(articleTitle,h1))return {
   state:"ARTICLE_TITLE_MISMATCH_HOLD",credits:[],sourceSectionFound:false,
   officialEventSourceVerified:false};
 const sectionFound=Boolean(raw?.sourceSectionFound);
 if(!sectionFound)return {state:"NO_EXPLICIT_SOURCE_SECTION_HOLD",credits:[],
   sourceSectionFound:false,officialEventSourceVerified:false};
 const credits=[],seen=new Set();
 for(const link of (raw?.links||[]).slice(0,32)){
  const url=safeCreditUrl(link.href);
  if(!url||seen.has(url))continue;
  const label=trim(link.label);
  if(!label||GENERIC.test(label))continue;
  seen.add(url);
  const role=creditRole(url);
  credits.push({url,anchorLabel:label,sourceSection:"資料來源",role,
      sourceCitationIdentified:true,
      linkedEventTitleIndependentlyMatched:false,
      organiserAccountAuthenticityVerified:false,
      originalOfficialEventDetailVerified:false,
      independentNoticeTimestampVerified:false});
  if(credits.length>=12)break;
 }
 return {state:credits.length?"ATTRIBUTED_LINKS_FOUND_UNVERIFIED":"SOURCE_SECTION_NO_ACCEPTED_EXTERNAL_CREDIT_HOLD",
   credits,sourceSectionFound:true,officialEventSourceVerified:false};
}
function homepageLinks(){
 return [...document.querySelectorAll("a[href]")].map(a=>({
  href:a.href,heading:a.querySelector("h1,h2,h3,h4,h5")?.textContent??"",
  alt:a.querySelector("img[alt]")?.getAttribute("alt")??"",
  text:(a.textContent||"").slice(0,220)
 }));
}
function sourceSectionDOM(){
 const root=document.querySelector("main")||document.querySelector("article")||document.body;
 const headings=[...root.querySelectorAll("h2,h3")];
 const source=headings.find(h=>/^[\s\u200B]*資料來源[\s\u200B]*$/u.test(h.textContent||""));
 const title=[...root.querySelectorAll("h1")].map(x=>x.textContent.trim().slice(0,240));
 if(!source)return {h1:title,sourceSectionFound:false,links:[],sectionBound:"NO_HEADING"};
 // Only anchors strictly AFTER the heading and BEFORE the next H2/H3 in the
 // same article main content; Google Maps elsewhere must never be mistaken
 // for a "資料來源" citation.
 const later=headings.find(h=>(source.compareDocumentPosition(h)&Node.DOCUMENT_POSITION_FOLLOWING)!==0);
 const links=[...root.querySelectorAll("a[href]")].filter(a=>{
  const post=(source.compareDocumentPosition(a)&Node.DOCUMENT_POSITION_FOLLOWING)!==0;
  const pre=!later||(a.compareDocumentPosition(later)&Node.DOCUMENT_POSITION_FOLLOWING)!==0;
  return post&&pre;
 }).slice(0,32).map(a=>({href:a.href,label:(a.textContent||a.getAttribute("aria-label")||"").slice(0,220)}));
 return {h1:title,sourceSectionFound:true,links,sectionBound:"H2_H3_HEADER_TO_NEXT_HEADER"};
}
export function makeResult(rows,samples,net){
 const verifiedCredits=samples.reduce((sum,r)=>sum+r.credits.length,0);
 return {kind:KIND,observedAtUTC:new Date().toISOString(),
  listCandidateCount:rows.length,articleSamplesCount:samples.length,
  exactAggregatorArticleCount:samples.filter(x=>x.articleIdentity==="AGGREGATOR_ARTICLE_H1_MATCH").length,
  attributedCreditCount:verifiedCredits,
  firstPartyEventDetailsIndependentlyVerified:0,
  samples,
  lineageState:verifiedCredits?"EXPLICIT_CREDIT_LINKS_CAPTURED_PRIMARY_VERIFICATION_HOLD":
    "NO_ACCEPTED_CREDIT_LINKS_PRIMARY_VERIFICATION_HOLD",
  rawAggregatorArticlesAll24Promoted:false,
  originalOfficialEventUrl:null,
  officialEventDatesVerified:0,officialTicketAvailabilityVerified:0,
  formalCandidateEventCount:0,fieldPromotionCount:0,
  goldenAccepted:false,published:false,writerExecuted:false,
  notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT",
  mainAndroid44Preserved:true,noLogin:true,noCheckout:true,noCaptchaBypass:true,
  noStealth:true,noPrivateAPI:true,noRetries:true,
  maxNavigation:1+MAX_ARTICLES,maxRequests:MAX_REQUESTS,network:net};
}
export async function run(out){
 const dir=resolve(out),docs=resolve("docs");
 if(dir===docs||dir.startsWith(docs+"/"))throw Error("HOLD_FORMAL_DATA_WRITER_PATH");
 const net={homepageHttp:null,allowedRequests:0,blockedForeign:0,
  blockedAssets:0,blockedBudget:0,navigationCount:0,pageErrors:0};
 let rows=[],samples=[],fatal=null;
 const browser=await chromium.launch({headless:true});
 try{
  const ctx=await browser.newContext({javaScriptEnabled:true,serviceWorkers:"block",
    permissions:[],acceptDownloads:false});
  const page=await ctx.newPage();
  page.on("pageerror",()=>net.pageErrors++);
  await page.route("**/*",async route=>{
   const request=route.request();
   if(!safeAssetHost(request.url())){net.blockedForeign++;return route.abort("blockedbyclient");}
   if(["image","media","font"].includes(request.resourceType())){
    net.blockedAssets++;return route.abort("blockedbyclient");
   }
   if(net.allowedRequests>=MAX_REQUESTS){
    net.blockedBudget++;return route.abort("blockedbyclient");
   }
   net.allowedRequests++;return route.continue();
  });
  try{
   const res=await page.goto(HOME,{waitUntil:"domcontentloaded",timeout:23000});
   net.navigationCount++;net.homepageHttp=res?.status()??null;
   await page.waitForTimeout(3800);
   rows=candidatesFromLinks(await page.evaluate(homepageLinks));
   for(const item of rows.slice(0,MAX_ARTICLES)){
    await page.waitForTimeout(700);
    let status=null,observed=null,dom=null,err=null;
    try{
     const rsp=await page.goto(item.aggregatorUrl,{waitUntil:"domcontentloaded",timeout:23000});
     net.navigationCount++;status=rsp?.status()??null;observed=page.url();
     if(status===200&&canonicalArticle(observed)===item.aggregatorUrl){
      await page.waitForTimeout(950);
      dom=await page.evaluate(sourceSectionDOM);
     }
    }catch(e){err=String(e.name||"Error");}
    const exact=Boolean(status===200&&observed===item.aggregatorUrl&&
       dom?.h1.some(x=>articleHeadingMatches(item.title,x)));
    const evidence=exact?attributedCredits(item.title,
       dom.h1.find(x=>articleHeadingMatches(item.title,x)),dom):{
       state:"ARTICLE_TITLE_OR_HTTP_HOLD",sourceSectionFound:false,credits:[],officialEventSourceVerified:false};
    samples.push({aggregatorUrl:item.aggregatorUrl,title:item.title,
       observedArticleUrl:observed,articleHttp:status,
       articleIdentity:exact?"AGGREGATOR_ARTICLE_H1_MATCH":"ARTICLE_TITLE_OR_HTTP_HOLD",
       sourceSectionFound:evidence.sourceSectionFound,creditState:evidence.state,
       credits:evidence.credits,firstPartyVerified:false,errorType:err,
       originalOfficialUrl:null,dateStart:null,dateEnd:null,
       venue:null,price:null,ticketStatus:"UNKNOWN",goldenVerified:false,published:false});
   }
  }catch(e){fatal={type:String(e.name||"Error"),message:String(e.message||"").slice(0,160)};}
  await ctx.close();
 }finally{await browser.close();}
 const result=makeResult(rows,samples,net);result.fatal=fatal;
 await mkdir(dir,{recursive:true});
 await writeFile(dir+"/lineage_evidence.json",JSON.stringify(result,null,2)+"\n");
 console.log("STROLL_L5E_HOME",net.homepageHttp,"LIST",rows.length);
 console.log("STROLL_L5E_SAMPLE_COUNT",samples.length,"TITLE_MATCH",result.exactAggregatorArticleCount,
 "EXPLICIT_CREDITS",result.attributedCreditCount);
 for(const s of samples)console.log("STROLL_L5E_ARTICLE",JSON.stringify({
  title:s.title,http:s.articleHttp,identity:s.articleIdentity,
  sourceSection:s.sourceSectionFound,creditState:s.creditState,
  credits:s.credits.map(c=>({role:c.role,host:new URL(c.url).hostname,label:c.anchorLabel}))}));
 if(net.homepageHttp!==200||rows.length<6||samples.length!==MAX_ARTICLES){
  console.log("HOLD P30_L5E_INSUFFICIENT_AGGREGATOR_SAMPLE");process.exitCode=2;
 }else{
  console.log("PASS P30_L5E_SIX_SOURCE_SECTION_ARTICLE_AUDITS");
  if(result.exactAggregatorArticleCount<MAX_ARTICLES)
   console.log("HOLD P30_L5E_ARTICLE_TITLE_IDENTITY");
  if(result.attributedCreditCount===0)
   console.log("HOLD P30_L5E_NO_ATTRIBUTED_OUTBOUND_LINKS");
  console.log("HOLD P30_L5E_FIRST_PARTY_SAME_EVENT_INDEPENDENT_IDENTITY_NOT_YET_VERIFIED");
  console.log("PASS P30_L5E_ZERO_GOLDEN_ZERO_PUBLICATION");
 }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const i=process.argv.indexOf("--out-dir");
 if(i<0||!process.argv[i+1]){console.error("HOLD_OUTDIR");process.exitCode=2;}
 else await run(process.argv[i+1]);
}
