#!/usr/bin/env node
/**
 * P30-L3-B-C public StrollTimes aggregator discovery.
 * Evidence-only: curated articles are NOT original organiser / official ticket sources.
 * Strict one homepage + one same-site article, no login/captcha/stealth/checkout.
 */
import { chromium } from "playwright";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const KIND="EVENTRADAR_P30_L3BC_STROLLTIMES_AGGREGATOR_CANDIDATES_NOT_GOLDEN";
export const HOME="https://strolltimes.com/";
const HOSTS=new Set(["strolltimes.com","www.strolltimes.com"]);
const CDN_HOSTS=new Set(["cdn.jsdelivr.net","cdnjs.cloudflare.com","fonts.googleapis.com","fonts.gstatic.com","unpkg.com"]);
const MAX_REQUESTS=100,MAX_ROWS=120,MAX_SAMPLE=1;
const ARTICLE_PATH=/^\/events\/[a-z][a-z0-9-]{1,32}\/[0-9]{12,18}\/?$/;
const generic=/^(?:首頁|最新活動|所有活動|查看更多|查看詳情|閱讀更多|了解更多|活動資訊|漫步時光|更多|更多活動|搜尋活動|點擊查看|前往活動)$/;
export function normalize(s){
  return String(s??"").replace(/\s+/g," ").trim().slice(0,220);
}
export function canonicalArticle(url,base=HOME){
  try{
    const x=new URL(url,base);
    if(x.protocol!=="https:"||!HOSTS.has(x.hostname)||x.port||x.username||x.password||x.hash||x.search) return null;
    const m=ARTICLE_PATH.exec(x.pathname);
    return m?"https://strolltimes.com"+(x.pathname.endsWith("/")?x.pathname:x.pathname+"/"):null;
  }catch{return null;}
}
export function isAggregatorOwned(url) {
  try {
    const x=new URL(url);
    return x.protocol==="https:"&&HOSTS.has(x.hostname)&&!x.port&&!x.username&&!x.password;
  }catch{return false;}
}
export function safeAssetHost(url){
  try{
    const u=new URL(url);
    return u.protocol==="https:"&&!u.username&&!u.password&&!u.port&&(HOSTS.has(u.hostname)||CDN_HOSTS.has(u.hostname));
  }catch{return false;}
}
export function titleText(raw){
  const s=normalize(raw);
  return s.length>=4&&!generic.test(s)&&!/^https?:\/\//i.test(s)?s:null;
}
export function articleHeadingMatches(listTitle,heading){
  const short=normalize(listTitle),full=normalize(heading);
  if(!short||!full)return false;
  if(full===short)return true;
  // Curator may append a date-only display suffix to H1. Identity-only;
  // DO NOT promote suffix as primary-source date evidence.
  if(!full.startsWith(short))return false;
  const extra=full.slice(short.length);
  return /^[（(]\s*\d{1,2}[/]\d{1,2}\s*[~～-]\s*\d{1,2}[/]\d{1,2}\s*[)）]$/.test(extra);
}
export function candidatesFromLinks(input){
  const rows=[],ids=new Set();
  for(const x of input){
    const url=canonicalArticle(x.href);
    if(!url||ids.has(url))continue;
    const title=titleText(x.heading||x.text||x.alt);
    if(!title)continue;
    ids.add(url);
    rows.push({
      platform:"StrollTimes",title,aggregatorUrl:url,
      originalOfficialUrl:null,originalOfficialIdentityState:"NOT_VERIFIED",
      sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",
      sourceLevel:"AGGREGATOR_LIST_IDENTITY_ONLY",
      originalEventDateStart:null,originalEventDateEnd:null,
      dateStart:null,dateEnd:null,dateRole:"UNKNOWN_NEEDS_ORGANISER_VERIFICATION",
      price:null,ticketStatus:"UNKNOWN",classification:"待分類",
      eventVenue:null,detailIdentityState:"NOT_CHECKED",
      goldenVerified:false,published:false
    });
    if(rows.length>=MAX_ROWS)break;
  }
  return rows;
}
function snapshot(){
  const items=[...document.querySelectorAll("a[href]")].map(a=>({
    href:a.href,
    heading:a.querySelector("h1,h2,h3,h4,h5")?.textContent??"",
    text:(a.textContent||"").slice(0,240),
    alt:a.querySelector("img[alt]")?.getAttribute("alt")??""
  }));
  return {
    title:(document.title||"").slice(0,110),
    anchors:items,
    anchorCount:items.length,
    scriptCount:document.scripts.length,
    h3Count:document.querySelectorAll("h3,h4").length,
    visibleTextLength:(document.body?.innerText||"").length
  };
}
function articleCheck(){
  const text=(document.body?.innerText||"");
  const headings=[...document.querySelectorAll("h1")].map(h=>h.textContent.trim().slice(0,240));
  const ext=[...document.querySelectorAll("a[href]")].map(a=>a.href).filter(u=>{
    try{
      const x=new URL(u);
      return x.protocol==="https:"&&!["strolltimes.com","www.strolltimes.com"].includes(x.hostname)&&
        !["facebook.com","www.facebook.com","instagram.com","www.instagram.com","youtube.com"].includes(x.hostname);
    }catch{return false;}
  });
  return {h1:headings.slice(0,3),visibleTextLength:text.length,
          outboundSourceLinkCount:ext.length,
          outboundSampleHostnames:[...new Set(ext.map(u=>new URL(u).hostname))].slice(0,8)};
}
function clock(){return new Date().toISOString();}
export async function run(out,opts={}){
  const dir=resolve(out),docs=resolve("docs");
  if(dir===docs||dir.startsWith(docs+"/"))throw Error("HOLD_WRITER_SCOPE");
  const metrics={allowedRequests:0,blockedOtherHosts:0,blockedAssets:0,blockedBudget:0,
                 pageErrors:0,requestFailures:0,homepageHttp:null,articleHttp:null};
  let rows=[],home=null,detail={state:"NOT_ATTEMPTED"},failure=null;
  const browser=await chromium.launch({headless:true});
  try{
    const ctx=await browser.newContext({javaScriptEnabled:true,serviceWorkers:"block",
                 permissions:[],acceptDownloads:false});
    const page=await ctx.newPage();
    page.on("pageerror",()=>metrics.pageErrors++);
    page.on("requestfailed",()=>metrics.requestFailures++);
    await page.route("**/*",async route=>{
      const req=route.request(),u=req.url();
      if(!safeAssetHost(u)){metrics.blockedOtherHosts++;return route.abort("blockedbyclient");}
      if(["image","media","font"].includes(req.resourceType())){
        metrics.blockedAssets++;return route.abort("blockedbyclient");
      }
      if(metrics.allowedRequests>=MAX_REQUESTS){
        metrics.blockedBudget++;return route.abort("blockedbyclient");
      }
      metrics.allowedRequests++;return route.continue();
    });
    try{
      const r=await page.goto(HOME,{waitUntil:"domcontentloaded",timeout:25000});
      metrics.homepageHttp=r?.status()??null;
      await page.waitForTimeout(4500);
      home=await page.evaluate(snapshot);
      rows=candidatesFromLinks(home.anchors);
      if(rows.length){
        const pick=rows[0];
        const s=await page.goto(pick.aggregatorUrl,{waitUntil:"domcontentloaded",timeout:20000});
        metrics.articleHttp=s?.status()??null;
        await page.waitForTimeout(1500);
        const observed=await page.evaluate(articleCheck);
        // This is an aggregator article. A matching h1 supports same-site
        // page identity, not a primary event authority.
        const exact=observed.h1.some(h=>articleHeadingMatches(pick.title,h));
        detail={
          state:metrics.articleHttp===200&&exact?"AGGREGATOR_ARTICLE_TITLE_MATCH":"AGGREGATOR_ARTICLE_TITLE_HOLD",
          aggregatorUrl:pick.aggregatorUrl,homepageCandidateTitle:pick.title,
          h1:observed.h1,visibleTextLength:observed.visibleTextLength,
          outboundSourceLinkCount:observed.outboundSourceLinkCount,
          outboundSampleHostnames:observed.outboundSampleHostnames,
          originalOfficialUrl:null,originalOfficialIdentityState:"NOT_VERIFIED",
          titleExactMatched:exact
        };
        pick.detailIdentityState=detail.state;
      }
    }catch(e){
      failure={name:String(e.name||"Error"),message:String(e.message||"").slice(0,180)};
    }
    await ctx.close();
  }finally{await browser.close();}
  const diag={
    kind:KIND,observedAtUTC:clock(),
    userVisibleHomepage:HOME,
    sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",
    sourceRoleBasis:"strolltimes.com/about independently describes curated external activities",
    metrics,homepage:home?{title:home.title,anchorCount:home.anchorCount,
       scriptCount:home.scriptCount,h3Count:home.h3Count,visibleTextLength:home.visibleTextLength}:null,
    article:detail,error:failure,counts:{uniqueAggregatorArticles:rows.length},
    onlyPublicRenderedPages:true,maxNavigation:2,maxRequests:MAX_REQUESTS,
    retries:0,noLogin:true,noCaptchaBypass:true,noStealth:true,
    goldenAccepted:false,published:false,writerExecuted:false,
    notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT",
    officialEventDataProven:0,fullCatalogProven:false
  };
  await mkdir(dir,{recursive:true});
  await writeFile(dir+"/candidate.json",JSON.stringify(rows,null,2)+"\n");
  await writeFile(dir+"/diagnostics.json",JSON.stringify(diag,null,2)+"\n");
  console.log("STROLLTIMES_HOME_HTTP",metrics.homepageHttp,
              "HOME_ANCHORS",home?.anchorCount??0,"HOME_H3",home?.h3Count??0,
              "SCRIPTS",home?.scriptCount??0);
  console.log("STROLLTIMES_AGGREGATOR_LIST",rows.length,"DETAIL",detail.state,
              "DETAIL_HTTP",metrics.articleHttp);
  console.log("STROLLTIMES_SAMPLE_TITLE",JSON.stringify(detail.homepageCandidateTitle??null),
              "AGGREGATOR_H1",JSON.stringify(detail.h1??[]));
  console.log("STROLLTIMES_METRICS",JSON.stringify(metrics));
  if(!rows.length){console.log("HOLD P30_L3BC_AGGREGATOR_LIST_EMPTY");process.exitCode=2;}
  else console.log("PASS P30_L3BC_AGGREGATOR_LIST_IDENTITY_ONLY");
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const k=process.argv.indexOf("--out-dir");
  if(k<0||!process.argv[k+1]){console.error("HOLD_OUTDIR_REQUIRED");process.exitCode=2;}
  else await run(process.argv[k+1]);
}
