#!/usr/bin/env node
/** P30-L4-D3 FamiTicket standard public browser: distinguish HTTP shell from JS detail.
 * One homepage, one title/opaque-ID bound detail; zero checkout, authentication,
 * hidden APIs, anti-bot bypass, retries, publication, or event-date promotion.
 */
import { chromium } from "playwright";
import { mkdir,writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const KIND="EVENTRADAR_P30_L4D3_FAMITICKET_PUBLIC_BROWSER_DETAIL_NOT_GOLDEN";
export const HOME="https://www.famiticket.com.tw/Home";
export const TITLE="2026 ITF 台灣國際旅展";
const HOST="www.famiticket.com.tw",DETAIL="/Home/Activity/Info/";
const CDNS=new Set(["cdnjs.cloudflare.com","cdn.jsdelivr.net","ajax.googleapis.com"]);
const MAX_REQ=100;
export function clean(s){return String(s??"").replace(/\s+/g," ").trim().slice(0,240);}
export function officialDetail(href,base=HOME){
  try{
    const u=new URL(href,base);
    if(u.protocol!=="https:"||u.hostname!==HOST||u.port||u.username||u.password||u.search||u.hash)return null;
    if(!u.pathname.startsWith(DETAIL))return null;
    const id=u.pathname.slice(DETAIL.length);
    if(!/^[A-Za-z0-9_+=-]{20,500}$/.test(id))return null;
    return "https://"+HOST+DETAIL+id;
  }catch{return null;}
}
export function allowedResource(url){
  try{
    const u=new URL(url);
    return u.protocol==="https:"&&!u.username&&!u.password&&!u.port&&
      (u.hostname===HOST||u.hostname==="famiticket.com.tw"||CDNS.has(u.hostname));
  }catch{return false;}
}
export function selectExact(list){
  const seen=new Map();
  for(const a of list){
    const url=officialDetail(a.href);
    if(!url)continue;
    const text=clean(a.heading||a.label||a.text||a.alt);
    if(text!==TITLE)continue;
    if(seen.has(url))continue;
    seen.set(url,{title:TITLE,url});
  }
  // A single matching event is required; selecting first silently is unsafe.
  return seen.size===1?[...seen.values()][0]:null;
}
function listing(){
  const anchors=[...document.querySelectorAll("a[href]")].map(a=>({
    href:a.href,
    heading:a.querySelector("h1,h2,h3,h4,h5")?.textContent??"",
    label:a.getAttribute("title")||a.getAttribute("aria-label")||"",
    text:(a.textContent||"").slice(0,220),
    alt:a.querySelector("img[alt]")?.getAttribute("alt")||""
  }));
  return {anchors,pageTitle:document.title.slice(0,120),
          anchorCount:anchors.length,visibleChars:(document.body?.innerText||"").length};
}
function detail(){
  const headings=[...document.querySelectorAll("h1,h2,h3,h4")]
    .map(x=>x.textContent.replace(/\s+/g," ").trim()).filter(Boolean).slice(0,45);
  const txt=(document.body?.innerText||"");
  const lines=txt.split("\n").map(x=>x.replace(/\s+/g," ").trim()).filter(Boolean);
  const hints=lines.filter(x=>/活動日期|展演|展出日期|展出時間|演出時間|演出日期|票券使用|售票期間|2026 ITF/.test(x))
    .slice(0,14).map(s=>s.slice(0,140));
  return {pageTitle:document.title.slice(0,120),headings,visibleChars:txt.length,
    exactBodyContainsTitle:txt.includes("2026 ITF 台灣國際旅展"),
    hints,scriptCount:document.scripts.length};
}
export function classify(row,data,meta){
  if(!row)return {state:"LIST_EXACT_UNIQUE_IDENTITY_HOLD"};
  if(!data)return {state:"DETAIL_HTTP_OR_HTML_HOLD",title:row.title,officialUrl:row.url};
  const exactHeading=data.headings.some(x=>clean(x)===row.title);
  return {state:meta.status===200&&exactHeading?"PUBLIC_BROWSER_EXACT_HEADING_PASS":"BROWSER_DETAIL_IDENTITY_HOLD",
    listTitle:row.title,officialUrl:row.url,status:meta.status,
    observedURL:meta.url,pageTitle:data.pageTitle,
    headingCount:data.headings.length,
    bodyContainsTitle:data.exactBodyContainsTitle,visibleChars:data.visibleChars,
    scriptCount:data.scriptCount,hints:data.hints.slice(0,14),
    eventDateStart:null,eventDateEnd:null,ticketStatus:"UNKNOWN",
    price:null,fieldPromotion:0,goldenVerified:false};
}
export async function run(out){
  const dir=resolve(out),docs=resolve("docs");
  if(dir===docs||dir.startsWith(docs+"/"))throw Error("HOLD_PRODUCTION_WRITER");
  const browser=await chromium.launch({headless:true});
  let selected=null,record=null,summary=null,issue=null;
  const net={allowedRequests:0,blockedExternal:0,blockedAssets:0,blockedBudget:0,
    javascriptErrors:0,homeHttp:null,detailHttp:null};
  try {
    const ctx=await browser.newContext({serviceWorkers:"block",javaScriptEnabled:true,
      acceptDownloads:false,permissions:[]});
    const page=await ctx.newPage();
    page.on("pageerror",()=>{net.javascriptErrors++;});
    await page.route("**/*",async route=>{
      const req=route.request();
      if(!allowedResource(req.url())){
        net.blockedExternal++;return route.abort("blockedbyclient");
      }
      if(["image","font","media"].includes(req.resourceType())){
        net.blockedAssets++;return route.abort("blockedbyclient");
      }
      if(net.allowedRequests>=MAX_REQ){
        net.blockedBudget++;return route.abort("blockedbyclient");
      }
      net.allowedRequests++;return route.continue();
    });
    try{
      const r=await page.goto(HOME,{waitUntil:"domcontentloaded",timeout:23000});
      net.homeHttp=r?.status()??null;
      await page.waitForTimeout(2800);
      const cards=await page.evaluate(listing);
      summary={anchorCount:cards.anchorCount,visibleChars:cards.visibleChars,
               pageTitle:cards.pageTitle};
      selected=selectExact(cards.anchors);
      if(selected){
        await page.waitForTimeout(1300);
        const r2=await page.goto(selected.url,{waitUntil:"domcontentloaded",timeout:23000});
        net.detailHttp=r2?.status()??null;
        const url=page.url();
        if(officialDetail(url)!==selected.url){
          record={state:"DETAIL_REDIRECT_ROLE_HOLD",officialUrl:selected.url,
            observedURL:url,eventDateStart:null,eventDateEnd:null,
            ticketStatus:"UNKNOWN",price:null,goldenVerified:false};
        }else{
          await page.waitForTimeout(2200);
          const seen=await page.evaluate(detail);
          record=classify(selected,seen,{status:net.detailHttp,url});
        }
      }else{
        record={state:"LIST_EXACT_UNIQUE_IDENTITY_HOLD"};
      }
    }catch(e){issue={type:String(e.name||"Error"),message:String(e.message||"").slice(0,130)};
      record={state:"PUBLIC_BROWSER_NAVIGATION_HOLD",eventDateStart:null,eventDateEnd:null,goldenVerified:false};
    }
    await ctx.close();
  }finally{await browser.close();}
  const d={kind:KIND,observedAtUTC:new Date().toISOString(),
    homepage:HOME,targetTitle:TITLE,listing:summary,detail:record,
    net,issue,maxNavigation:2,maxNetworkRequests:MAX_REQ,
    sourceRole:"OFFICIAL_TICKET_PLATFORM",noLogin:true,noStealth:true,
    noCaptchaBypass:true,noCheckout:true,noRetries:true,
    acceptedEventDates:0,goldenAccepted:false,published:false,
    writerExecuted:false,notifierExecuted:false,autoHidden:0,
    sourceRuntime:"DORMANT",completeCatalogProven:false};
  await mkdir(dir,{recursive:true});
  await writeFile(dir+"/diagnostics.json",JSON.stringify(d,null,2)+"\n");
  console.log("FAMI_BROWSER_HOME",net.homeHttp,"ANCHORS",summary?.anchorCount??-1,
    "TARGET",selected?"UNIQUE_ID":"HOLD");
  console.log("FAMI_BROWSER_DETAIL",net.detailHttp,record.state,
    "HEADINGS",record.headingCount??0,"BODY_TITLE",record.bodyContainsTitle??false,
    "HINTS",JSON.stringify(record.hints??[]));
  if(net.homeHttp!==200||!selected||net.detailHttp!==200){console.log("HOLD P30_L4D3_PUBLIC_BROWSER_OR_TARGET");process.exitCode=2;}
  else{
    console.log("PASS P30_L4D3_FAMITICKET_BROWSER_EVIDENCE_CAPTURED");
    if(record.state!=="PUBLIC_BROWSER_EXACT_HEADING_PASS")
      console.log("HOLD P30_L4D3_DETAIL_IDENTITY_QUALITY");
  }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const i=process.argv.indexOf("--out-dir");
  if(i<0||!process.argv[i+1]){console.error("HOLD_OUTDIR");process.exitCode=2;}
  else await run(process.argv[i+1]);
}
