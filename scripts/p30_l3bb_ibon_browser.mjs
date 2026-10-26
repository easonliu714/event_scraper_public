#!/usr/bin/env node
/**
 * P30-L3-B-B2 public ibon JavaScript render probe (diagnostic only).
 * Runs stock Chromium. No anti-bot/stealth, login, captcha, checkout, credential
 * storage, purchase, private APIs, publication, or official JSON writer.
 */
import { chromium } from "playwright";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const KIND="EVENTRADAR_P30_L3BB2_IBON_PUBLIC_BROWSER_DIAGNOSTIC_NOT_GOLDEN";
export const LIST="https://ticket.ibon.com.tw/Index/entertainment";
const MAX_REQUESTS=90;
const WORDS=new Set(["購票","立即購票","查看活動","詳情","更多","最新開賣","登入","立即預訂","售票中","即將開賣","已售完"]);
export function allowedHost(url){
  try {
    const u=new URL(url);
    if(u.protocol!=="https:"||u.username||u.password||u.port) return false;
    return u.hostname==="ibon.com.tw"||u.hostname.endsWith(".ibon.com.tw");
  } catch{return false;}
}
export function canonicalDetail(url){
  try {
    const u=new URL(url,LIST);
    if(!allowedHost(u.href)||u.hostname!=="ticket.ibon.com.tw"||u.search||u.hash)return null;
    const m=/^\/(?:Web\/|WebV3\/)?ActivityInfo\/Details\/([0-9]{3,8})\/?$/.exec(u.pathname);
    return m?"https://ticket.ibon.com.tw/ActivityInfo/Details/"+m[1]:null;
  } catch{return null;}
}
export function candidateTitle(raw){
  if(typeof raw!=="string")return null;
  const value=raw.replace(/\s+/g," ").trim().slice(0,200);
  return value.length>=4&&!WORDS.has(value)&&!/^https?:\/\//.test(value)?value:null;
}
function extractDom(){
  const seen=new Set(),items=[];
  const anchors=[...document.querySelectorAll("a[href]")];
  const bad=new Set(["購票","立即購票","查看活動","詳情","更多","最新開賣","登入","立即預訂","售票中","即將開賣","已售完"]);
  for(const a of anchors){
    let u;try{u=new URL(a.getAttribute("href"),location.href);}catch{continue;}
    if(u.protocol!=="https:"||u.hostname!=="ticket.ibon.com.tw"||u.search||u.hash)continue;
    let match=/^\/(?:Web\/|WebV3\/)?ActivityInfo\/Details\/([0-9]{3,8})\/?$/.exec(u.pathname);
    if(!match)continue;
    const url="https://ticket.ibon.com.tw/ActivityInfo/Details/"+match[1];
    if(seen.has(url))continue;
    const near=a.querySelector("h2,h3,h4,h5");
    const title=(near?.textContent||a.getAttribute("title")||a.getAttribute("aria-label")||a.textContent||a.querySelector("img[alt]")?.getAttribute("alt")||"").replace(/\s+/g," ").trim().slice(0,200);
    if(title.length<4||bad.has(title)||title.startsWith("http"))continue;
    seen.add(url);
    items.push({platform:"ibon",title,officialUrl:url,
      dateStart:null,dateEnd:null,dateRole:"UNKNOWN",
      ticketStatus:"UNKNOWN",price:null,category:"待分類",
      sourceLevel:"PUBLIC_BROWSER_RENDER_LIST_ONLY",
      classificationEvidence:"UNVERIFIED",detailStatus:"NOT_CHECKED",
      goldenVerified:false,published:false});
    if(items.length>=80)break;
  }
  return {candidates:items,anchorsSeen:anchors.length,scriptTags:document.scripts.length,
    pageTitle:(document.title||"").slice(0,100),bodyTextCharacters:(document.body?.innerText||"").length};
}
export async function run(out){
  const dir=resolve(out);
  const docs=resolve("docs");
  if(dir===docs||dir.startsWith(docs+"/"))throw Error("HOLD_PRODUCTION_DOCS");
  const browser=await chromium.launch({headless:true});
  let report,rows=[];
  const stats={allowed:0,blockedExternal:0,blockedBudget:0,blockedResources:0,
    pageHttpStatus:null,pageURL:null,pageErrors:0,resourceFailures:0};
  try{
    const context=await browser.newContext({serviceWorkers:"block",
      permissions:[],acceptDownloads:false,javaScriptEnabled:true});
    const page=await context.newPage();
    page.on("pageerror",()=>{stats.pageErrors++;});
    page.on("requestfailed",()=>{stats.resourceFailures++;});
    await page.route("**/*",async route=>{
      const request=route.request(),url=request.url(),typ=request.resourceType();
      if(!allowedHost(url)){
        stats.blockedExternal++;return route.abort("blockedbyclient");
      }
      if(["image","font","media"].includes(typ)){
        stats.blockedResources++;return route.abort("blockedbyclient");
      }
      if(stats.allowed>=MAX_REQUESTS){
        stats.blockedBudget++;return route.abort("blockedbyclient");
      }
      stats.allowed++;return route.continue();
    });
    try{
      const response=await page.goto(LIST,{waitUntil:"domcontentloaded",timeout:20000});
      stats.pageHttpStatus=response?.status()??null;
      stats.pageURL=page.url();
      await page.waitForTimeout(8500);
      const dom=await page.evaluate(extractDom);
      rows=dom.candidates;
      report={kind:KIND,source:LIST,headlessBrowser:"stock Chromium with JavaScript",
        observedAtUTC:new Date().toISOString(),http:stats,dom:{
        anchorsSeen:dom.anchorsSeen,scriptTags:dom.scriptTags,
        pageTitle:dom.pageTitle,bodyTextCharacters:dom.bodyTextCharacters,
        listCandidates:rows.length},
        goldenAccepted:false,published:false,writerExecuted:false,
        notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT",
        completeCatalogProven:false,detailIdentityVerified:0,maxNavigation:1,
        maxRequests:MAX_REQUESTS,noCaptchaBypass:true,noLogin:true,
        status:rows.length?"RENDERED_EVENT_LINK_CANDIDATES":"BROWSER_RENDERED_LIST_EMPTY_OR_RESTRICTED_HOLD"};
    }catch(error){
      report={kind:KIND,source:LIST,observedAtUTC:new Date().toISOString(),
        http:stats,errorClass:error?.name||"UnknownError",
        errorMessage:String(error?.message||"").slice(0,140),status:"BROWSER_HOLD",
        goldenAccepted:false,published:false,writerExecuted:false,
        notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT",
        completeCatalogProven:false,detailIdentityVerified:0,maxNavigation:1,
        maxRequests:MAX_REQUESTS,noCaptchaBypass:true,noLogin:true};
    }
    await context.close();
  }finally{await browser.close();}
  await mkdir(dir,{recursive:true});
  await writeFile(dir+"/candidate.json",JSON.stringify(rows,null,2)+"\n");
  await writeFile(dir+"/diagnostics.json",JSON.stringify(report,null,2)+"\n");
  console.log("IBON_BROWSER",report.status,"HTTP",report.http.pageHttpStatus,
    "ANCHORS",report.dom?.anchorsSeen??-1,"LIST",rows.length,"TITLE",report.dom?.pageTitle);
  console.log("IBON_BROWSER_REQUESTS",JSON.stringify(stats));
  if(!rows.length){console.log("HOLD P30_L3BB2_OFFICIAL_BROWSER_LIST_EMPTY");process.exitCode=2;}
  else console.log("PASS P30_L3BB2_PUBLIC_RENDERED_LIST_CANDIDATES_NOT_GOLDEN");
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const idx=process.argv.indexOf("--out-dir");
  if(idx<0||!process.argv[idx+1]){console.error("HOLD_OUTPUT_REQUIRED");process.exitCode=2;}
  else await run(process.argv[idx+1]);
}
