#!/usr/bin/env node
/**
 * P30-L4-D2 ibon public activity detail identity / date-role evidence.
 * Never open checkout or query undocumented APIs. Standard Playwright browser,
 * one entertainment list and at most 2 validated numeric-ID details. Source
 * role evidence does NOT equal verified event date, venue, price or sale state.
 */
import {chromium} from "playwright";
import {mkdir,writeFile} from "node:fs/promises";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {LIST,canonicalDetail,allowedHost,candidateTitle} from "./p30_l3bb_ibon_browser.mjs";

export const KIND="EVENTRADAR_P30_L4D2_IBON_PUBLIC_DETAIL_ROLE_EVIDENCE_NOT_GOLDEN";
const MAX_NAV=3,MAX_REQUESTS=130;
const roles=new Map([
  ["活動日期","EVENT_DATE_LABEL_ONLY"],["活動時間","EVENT_DATE_LABEL_ONLY"],
  ["演出日期","EVENT_DATE_LABEL_ONLY"],["演出時間","EVENT_DATE_LABEL_ONLY"],
  ["比賽日期","EVENT_DATE_LABEL_ONLY"],["展覽日期","EVENT_DATE_LABEL_ONLY"],
  ["活動地點","VENUE_LABEL_ONLY"],
  ["演出地點","VENUE_LABEL_ONLY"],
  ["售票時間","SALE_WINDOW_NOT_EVENT"],["售票期間","SALE_WINDOW_NOT_EVENT"],
  ["售票日期","SALE_WINDOW_NOT_EVENT"],["開賣時間","SALE_WINDOW_NOT_EVENT"],
  ["報名期間","REGISTRATION_WINDOW_NOT_EVENT"],
  ["使用期限","VOUCHER_VALIDITY_NOT_EVENT"],
  ["票券使用期間","VOUCHER_VALIDITY_NOT_EVENT"]
]);
const datetoken=/(?<!\d)20\d{2}[\/.\-](?:0?[1-9]|1[0-2])[\/.\-](?:0?[1-9]|[12]\d|3[01])(?!\d)/g;
export function labels(lines){
  const found=[];
  for(const line of lines.slice(0,300)){
    let v=String(line??"").replace(/\s+/g," ").trim().slice(0,200);
    const m=/^([^:：]{2,10})\s*[:：]\s*(.*)$/.exec(v);
    if(!m||!roles.has(m[1]))continue;
    const evidence=[...m[2].matchAll(datetoken)].map(x=>x[0]).slice(0,3);
    found.push({label:m[1],role:roles.get(m[1]),
                observedDateTokens:evidence,evidenceExcerpt:m[2].slice(0,150),
                status:"RAW_UNPROMOTED_EVIDENCE"});
    if(found.length>=30)break;
  }
  return found;
}
export function listRows(raw){
  const seen=new Set(),rows=[];
  for(const a of raw){
    const url=canonicalDetail(a.href);
    if(!url||seen.has(url))continue;
    const title=candidateTitle(a.heading||a.text||a.alt);
    if(!title)continue;
    seen.add(url);
    rows.push({platform:"ibon",title,officialUrl:url,dateStart:null,dateEnd:null,
      dateRole:"UNKNOWN",venue:null,ticketStatus:"UNKNOWN",price:null,
      detailIdentity:"NOT_CHECKED",eventTimeVerified:false,
      goldenVerified:false,published:false});
    if(rows.length>=80)break;
  }
  return rows;
}
function listDom(){
  return [...document.querySelectorAll("a[href]")].map(a=>({
    href:a.href,heading:a.querySelector("h2,h3,h4,h5")?.textContent??"",
    text:(a.textContent||"").slice(0,230),
    alt:a.querySelector("img[alt]")?.getAttribute("alt")??""
  }));
}
function detailDom(){
  // Body text / headings ONLY. Don't interact with buttons, date pickers or cart.
  return {
    headings:[...document.querySelectorAll("h1,h2,h3")].map(e=>e.textContent.replace(/\s+/g," ").trim()).filter(Boolean).slice(0,40),
    lines:(document.body?.innerText||"").split("\n").map(s=>s.trim()).filter(Boolean).slice(0,300),
    pageTitle:document.title.slice(0,140),
    bodyTextLength:(document.body?.innerText||"").length,
    iframeCount:document.querySelectorAll("iframe").length,
    roleHintLines:(document.body?.innerText||"").split("\n")
      .map(s=>s.replace(/\s+/g," ").trim()).filter(s=>/日期|時間|場次|演出|售票|開賣|使用期限|票券|入場|活動資訊/.test(s))
      .slice(0,16).map(s=>s.slice(0,120))
  };
}
export function assess(row,observed,network){
  const exact=observed.headings.some(h=>h===row.title);
  return {requestedOfficialUrl:row.officialUrl,listTitle:row.title,
    responseStatus:network.status??null,responseUrl:network.url??null,
    headingCount:observed.headings.length,
    roleHintLines:(observed.roleHintLines||[]).slice(0,16).map(s=>String(s).slice(0,120)),
    identity:network.status===200&&exact?"EXACT_LIST_DETAIL_HEADING":"DETAIL_TITLE_OR_HTTP_HOLD",
    roleEvidence:network.status===200&&exact?labels(observed.lines):[],
    dateStart:null,dateEnd:null,venue:null,price:null,ticketStatus:"UNKNOWN",
    officialActivityScheduleVerified:false,goldenVerified:false};
}
function allowedResource(url){
  try {
    const x=new URL(url);
    return allowedHost(url)&&x.protocol==="https:"&&!x.username&&!x.password&&!x.port;
  }catch{return false;}
}
export async function run(out){
  const dir=resolve(out),docs=resolve("docs");
  if(dir===docs||dir.startsWith(docs+"/"))throw new Error("HOLD_OFFICIAL_DOC_WRITER");
  const stats={allowedRequests:0,blockedOutsideIbon:0,blockedAssets:0,blockedBudget:0,
    jsPageErrors:0,networkErrors:0,listStatus:null,listAnchors:null};
  let output=[],sample=[],fatal=null;
  const browser=await chromium.launch({headless:true});
  try{
    const context=await browser.newContext({serviceWorkers:"block",javaScriptEnabled:true,
      permissions:[],acceptDownloads:false});
    const page=await context.newPage();
    page.on("pageerror",()=>stats.jsPageErrors++);
    page.on("requestfailed",()=>stats.networkErrors++);
    await page.route("**/*",async route=>{
      const url=route.request().url(),type=route.request().resourceType();
      if(!allowedResource(url)){
        stats.blockedOutsideIbon++;return route.abort("blockedbyclient");
      }
      if(["image","font","media"].includes(type)){
        stats.blockedAssets++;return route.abort("blockedbyclient");
      }
      if(stats.allowedRequests>=MAX_REQUESTS){
        stats.blockedBudget++;return route.abort("blockedbyclient");
      }
      stats.allowedRequests++;
      return route.continue();
    });
    try{
      const response=await page.goto(LIST,{waitUntil:"domcontentloaded",timeout:23000});
      stats.listStatus=response?.status()??null;
      await page.waitForTimeout(6500);
      const raw=await page.evaluate(listDom);
      stats.listAnchors=raw.length;
      output=listRows(raw);
      // Independent identity samples: only already-seen exact numeric detail ID,
      // one second minimum between each; no login, checkout or extra pages.
      for(const row of output.slice(0,2)){
        await page.waitForTimeout(1100);
        try {
          const res=await page.goto(row.officialUrl,{waitUntil:"domcontentloaded",timeout:16000});
          const status=res?.status()??null;
          const observedUrl=page.url();
          // Never parse or certify a cross-origin or wrong-role landing page.
          if(!allowedResource(observedUrl)||canonicalDetail(observedUrl)!==row.officialUrl){
            const evidence={requestedOfficialUrl:row.officialUrl,listTitle:row.title,
              responseStatus:status,responseUrl:observedUrl,
              identity:"DETAIL_URL_REDIRECT_ROLE_HOLD",roleEvidence:[],
              dateStart:null,dateEnd:null,venue:null,price:null,
              ticketStatus:"UNKNOWN",goldenVerified:false};
            sample.push(evidence);row.detailIdentity=evidence.identity;
            continue;
          }
          await page.waitForTimeout(1400);
          const view=await page.evaluate(detailDom);
          const result=assess(row,view,{status,url:observedUrl});
          sample.push(result);row.detailIdentity=result.identity;
        }catch(err){
          sample.push({requestedOfficialUrl:row.officialUrl,listTitle:row.title,
            identity:"DETAIL_NAVIGATION_HOLD",errorType:String(err.name||"Error"),
            roleEvidence:[],dateStart:null,dateEnd:null,
            ticketStatus:"UNKNOWN",goldenVerified:false});
          row.detailIdentity="DETAIL_NAVIGATION_HOLD";
        }
      }
    }catch(e){fatal={errorType:String(e.name||"Error"),message:String(e.message||"").slice(0,180)};}
    await context.close();
  }finally{await browser.close();}
  const diagnostic={kind:KIND,observedAtUTC:new Date().toISOString(),
    listURL:LIST,listCount:output.length,sourceRole:"OFFICIAL_TICKET_PLATFORM",
    stats,details:sample,fatal,maxNavigation:MAX_NAV,maxNetworkRequests:MAX_REQUESTS,
    noPrivateAPI:true,noCheckout:true,noLogin:true,noCaptchaBypass:true,
    noRetries:true,verifiedDateCount:0,goldenAccepted:false,
    published:false,writerExecuted:false,notifierExecuted:false,
    autoHidden:0,sourceRuntime:"DORMANT",completeCatalogProven:false};
  await mkdir(dir,{recursive:true});
  await writeFile(dir+"/sample_candidates.json",JSON.stringify(output.slice(0,2),null,2)+"\n");
  await writeFile(dir+"/diagnostics.json",JSON.stringify(diagnostic,null,2)+"\n");
  console.log("IBON_L4D2_LIST",stats.listStatus,"CANDIDATES",output.length,
              "SAMPLED_DETAILS",sample.length);
  for(const x of sample)console.log("IBON_L4D2_DETAIL",x.responseStatus,x.identity,
    "ROLE_LABELS",x.roleEvidence?.map(x=>x.label).join("|")??"",
    "PAGE_FIELD_HINTS",JSON.stringify((x.roleHintLines||[]).slice(0,9)));
  if(!output.length||sample.length!==2){
    console.log("HOLD P30_L4D2_LIST_OR_TWO_SAMPLE_DETAILS");process.exitCode=2;
  }else{
    console.log("PASS P30_L4D2_PUBLIC_DETAIL_AUDIT_ONLY");
    if(sample.some(x=>x.identity!=="EXACT_LIST_DETAIL_HEADING"))
      console.log("HOLD P30_L4D2_OFFICIAL_DETAIL_IDENTITY_QUALITY");
  }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const k=process.argv.indexOf("--out-dir");
  if(k<0||!process.argv[k+1]){
    console.error("HOLD_OUT_DIR_REQUIRED");process.exitCode=2;
  }else await run(process.argv[k+1]);
}
