#!/usr/bin/env node
/**
 * EventRadar P30-L5-D1: FamiTicket public browser official-detail field roles.
 *
 * One public homepage, at most 4 distinct official opaque-ID detail pages.
 * Only source-bound label/adjacent value evidence; never dateStart, venue,
 * price, sale availability, category, Golden, main Pages or Android writer.
 * NO login/checkout/stealth/CAPTCHA bypass/undocumented API/retries.
 */
import {chromium} from "playwright";
import {mkdir,writeFile} from "node:fs/promises";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {HOME,TITLE,clean,officialDetail,allowedResource} from "./p30_l4d3_famiticket_browser.mjs";
export const KIND="EVENTRADAR_P30_L5D1_FAMITICKET_OFFICIAL_FIELD_ROLES_REVIEW_ONLY";
const MAX_DETAILS=4,MAX_REQ=160;
export const ROLE={
  "活動日期":"EVENT_TIME_LABEL_ONLY","活動時間":"EVENT_TIME_LABEL_ONLY",
  "演出日期":"EVENT_TIME_LABEL_ONLY","演出時間":"EVENT_TIME_LABEL_ONLY",
  "展覽日期":"EVENT_TIME_LABEL_ONLY","展出日期":"EVENT_TIME_LABEL_ONLY",
  "展覽期間":"EVENT_TIME_LABEL_ONLY","展期":"EVENT_TIME_LABEL_ONLY",
  "展出期間":"EVENT_TIME_LABEL_ONLY","開放日期":"EVENT_TIME_LABEL_ONLY",
  "活動期間":"EVENT_TIME_LABEL_ONLY",
  "活動地點":"VENUE_LABEL_ONLY","活動場地":"VENUE_LABEL_ONLY",
  "演出地點":"VENUE_LABEL_ONLY","展覽地點":"VENUE_LABEL_ONLY",
  "展出地點":"VENUE_LABEL_ONLY","展覽場地":"VENUE_LABEL_ONLY",
  "入場時間":"ADMISSION_NOT_EVENT_START","開放入場":"ADMISSION_NOT_EVENT_START",
  "售票時間":"SALE_WINDOW_NOT_EVENT","售票期間":"SALE_WINDOW_NOT_EVENT",
  "售票日期":"SALE_WINDOW_NOT_EVENT","開賣時間":"SALE_WINDOW_NOT_EVENT",
  "購票期間":"SALE_WINDOW_NOT_EVENT",
  "報名時間":"REGISTRATION_WINDOW_NOT_EVENT","報名期間":"REGISTRATION_WINDOW_NOT_EVENT",
  "票券使用期間":"VOUCHER_VALIDITY_NOT_EVENT",
  "票券使用期限":"VOUCHER_VALIDITY_NOT_EVENT",
  "使用期限":"VOUCHER_VALIDITY_NOT_EVENT","兌換期限":"VOUCHER_VALIDITY_NOT_EVENT"
};
const LABELS=Object.keys(ROLE).sort((a,b)=>b.length-a.length);
const dateToken=/(?<!\d)(20\d{2})[./\-年](1[0-2]|0?[1-9])[./\-月](3[01]|[12]\d|0?[1-9])(?:日)?(?!\d)/g;
function norm(x){return String(x??"").replace(/\s+/g," ").trim().slice(0,360);}
export function parseDates(s){
  const result=[];
  for(const m of String(s??"").matchAll(dateToken)){
    const y=+m[1],mo=+m[2],d=+m[3];
    const calendar=new Date(Date.UTC(y,mo-1,d));
    if(calendar.getUTCFullYear()!==y||calendar.getUTCMonth()+1!==mo||calendar.getUTCDate()!==d)continue;
    const date=[y,String(mo).padStart(2,"0"),String(d).padStart(2,"0")].join("-");
    if(!result.includes(date))result.push(date);
    if(result.length>=6)break;
  }
  return result;
}
export function roleFields(lines){
  const data=[],all=(Array.isArray(lines)?lines:[]).map(norm).filter(Boolean).slice(0,280);
  for(let i=0;i<all.length&&data.length<35;i++){
    const line=all[i];
    let label=null,value=null,how=null;
    for(const key of LABELS){
      if(line===key||line===key+"："||line===key+":"){
        // Only the immediately adjacent field; never scan past navigation or a new section.
        const next=all[i+1]||"";
        if(next&&next.length<=220&&!(LABELS.some(k=>next===k||next.startsWith(k+"：")||next.startsWith(k+":")))){
          label=key;value=next;how="ADJACENT_VALUE";
        } else {
          label=key;value="";how="LABEL_NO_ADJACENT_VALUE_HOLD";
        }
        break;
      }
      if(line.startsWith(key+"：")||line.startsWith(key+":")){
        label=key;value=norm(line.slice(key.length+1));how="INLINE_LABEL";
        break;
      }
    }
    if(label===null)continue;
    const role=ROLE[label];
    const dates=role==="VENUE_LABEL_ONLY"?[]:parseDates(value);
    data.push({label,role,evidenceBinding:how,
      evidenceExcerpt:value.slice(0,180),fullYearDateTokens:dates,
      sourceQuality:!value?"EMPTY_ROLE_VALUE_HOLD":"LABELED_RAW_EVIDENCE_UNPROMOTED",
      officialEventDateAccepted:false});
  }
  return data;
}
const CATEGORY=new Set(["展覽","音樂會","演唱會","表演&劇場","樂園","運動賽事","電影","景點門票","戶外觀光","交通"]);
export function findDetailCards(anchors,max=MAX_DETAILS){
  const byUrl=new Map();
  for(const a of anchors){
    const url=officialDetail(a.href);
    if(!url)continue;
    const raw=[a.heading,a.alt,a.label,a.text].map(x=>clean(x));
    // A category-only anchor can hold an exact image-alt activity title.
    const title=raw.find(t=>t===TITLE)||
      raw.find(t=>t.length>=7&&t.length<=160&&!CATEGORY.has(t)&&
        !/^(?:立即購票|購票|即將開賣|活動詳情|查看詳情|更多)/.test(t)&&
        !/^(?:20\d\d[\/.-]\d\d[\/.-]\d\d|NT\$)/.test(t));
    if(!title)continue;
    if(byUrl.has(url)){
      const old=byUrl.get(url);
      if(old.title!==TITLE&&title===TITLE)byUrl.set(url,{title,url,cardEvidence:"EXACT_CARD_TEXT_OR_IMAGE_ALT"});
      continue;
    }
    byUrl.set(url,{title,url,cardEvidence:"EXACT_CARD_TEXT_OR_IMAGE_ALT"});
  }
  const rows=[...byUrl.values()];
  const itf=rows.filter(x=>x.title===TITLE);
  if(itf.length!==1)return {state:"ITF_UNIQUE_LIST_IDENTITY_HOLD",rows:[]};
  return {state:"UNIQUE_ITF_PLUS_DEDUP_OTHER_CARDS",rows:[itf[0],...rows.filter(x=>x.url!==itf[0].url)].slice(0,max)};
}
function homepageDOM(){
  return [...document.querySelectorAll("a[href]")].map(a=>({
    href:a.href,heading:a.querySelector("h1,h2,h3,h4,h5")?.textContent??"",
    alt:a.querySelector("img[alt]")?.getAttribute("alt")||"",
    label:a.getAttribute("title")||a.getAttribute("aria-label")||"",
    text:(a.textContent||"").slice(0,175)
  }));
}
function detailsDOM(){
  const text=document.body?.innerText||"";
  return {headings:[...document.querySelectorAll("h1,h2,h3,h4")]
    .map(n=>n.textContent.replace(/\s+/g," ").trim()).filter(Boolean).slice(0,50),
    lines:text.split("\n").map(x=>x.trim()).filter(Boolean).slice(0,280),
    visibleCharacters:text.length,scriptTags:document.scripts.length};
}
export function audit(row,page,http){
  const bound=http?.status===200&&http.url===row.url&&
    page?.headings.some(h=>clean(h)===row.title);
  return {listTitle:row.title,officialUrl:row.url,detailHttp:http.status,
    observedUrl:http.url,
    identity:bound?"EXACT_LIST_DETAIL_TITLE_PASS":"DETAIL_TITLE_OR_HTTP_HOLD",
    visibleCharacters:page?.visibleCharacters??0,headingCount:page?.headings.length??0,
    fields:bound?roleFields(page.lines):[],
    firstPartyPlatform:"OFFICIAL_TICKET_PLATFORM_NOT_ORGANISER",
    dateStart:null,dateEnd:null,venue:null,ticketStatus:"UNKNOWN",
    price:null,category:"待分類",fieldPromotionCount:0,
    goldenVerified:false,published:false};
}
export async function run(out){
  const target=resolve(out),docs=resolve("docs");
  if(target===docs||target.startsWith(docs+"/"))throw Error("HOLD_FORMAL_DOCS_WRITER");
  const network={allowed:0,blockedExternal:0,blockedAssets:0,blockedBudget:0,
    pageErrors:0,navigations:0,homepageStatus:null};
  let candidates=[],samples=[],selectionState="NOT_ATTEMPTED",fatal=null;
  const browser=await chromium.launch({headless:true});
  try{
    const context=await browser.newContext({serviceWorkers:"block",javaScriptEnabled:true,
      permissions:[],acceptDownloads:false});
    const page=await context.newPage();
    page.on("pageerror",()=>network.pageErrors++);
    await page.route("**/*",async route=>{
      const req=route.request();
      if(!allowedResource(req.url())){network.blockedExternal++;return route.abort("blockedbyclient");}
      if(["image","font","media"].includes(req.resourceType())){network.blockedAssets++;return route.abort("blockedbyclient");}
      if(network.allowed>=MAX_REQ){network.blockedBudget++;return route.abort("blockedbyclient");}
      network.allowed++;return route.continue();
    });
    try{
      const response=await page.goto(HOME,{waitUntil:"domcontentloaded",timeout:23000});
      network.navigations++;network.homepageStatus=response?.status()??null;
      await page.waitForTimeout(2700);
      const raw=await page.evaluate(homepageDOM);
      const picked=findDetailCards(raw);
      selectionState=picked.state;candidates=picked.rows;
      for(const row of candidates){
        await page.waitForTimeout(1250);
        let status=null,current=null,dom=null,error=null;
        try{
          const res=await page.goto(row.url,{waitUntil:"domcontentloaded",timeout:23000});
          network.navigations++;status=res?.status()??null;current=page.url();
          if(status===200&&officialDetail(current)===row.url){
            await page.waitForTimeout(1900);
            dom=await page.evaluate(detailsDOM);
          }
        }catch(e){error=String(e?.name||"NavigationError");}
        const sample=audit(row,dom,{status,url:current});
        if(error)sample.errorType=error;
        samples.push(sample);
      }
    }catch(e){fatal={type:String(e.name||"Error"),message:String(e.message||"").slice(0,150)};}
    await context.close();
  }finally{await browser.close();}
  const valid=samples.filter(x=>x.identity==="EXACT_LIST_DETAIL_TITLE_PASS");
  const roleCount=valid.reduce((sum,s)=>sum+s.fields.length,0);
  const doc={kind:KIND,observedAtUTC:new Date().toISOString(),sourceListUrl:HOME,
    selectionState,listedSampleCount:candidates.length,detailSamples:samples,
    exactTitleMatches:valid.length,labeledRoleEvidenceCount:roleCount,
    roleBreakdown:Object.fromEntries([...new Set(valid.flatMap(x=>x.fields.map(f=>f.role)))]
      .map(role=>[role,valid.reduce((sum,x)=>sum+x.fields.filter(f=>f.role===role).length,0)])),
    network,maxNavigation:1+MAX_DETAILS,maxApprovedRequests:MAX_REQ,
    noCheckout:true,noLogin:true,noStealth:true,noCaptchaBypass:true,noPrivateAPI:true,
    noRetries:true,sampledFullCatalog:false,acceptedEventDates:0,
    sourceRuntime:"DORMANT",goldenAccepted:false,published:false,
    writerExecuted:false,notifierExecuted:false,autoHidden:0,fatal};
  await mkdir(target,{recursive:true});
  await writeFile(target+"/role_evidence.json",JSON.stringify(doc,null,2)+"\n");
  console.log("FAMI_L5D_HOME",network.homepageStatus,"SELECTED",candidates.length,selectionState);
  console.log("FAMI_L5D_SAMPLES",samples.length,"MATCHED",valid.length,"ROLE_EVIDENCE",roleCount);
  for(const s of samples)console.log("FAMI_L5D_DETAIL",JSON.stringify({
    title:s.listTitle,http:s.detailHttp,identity:s.identity,roleLabels:s.fields.map(x=>x.label)}));
  if(network.homepageStatus!==200||candidates.length<2||samples.length<2){
    console.log("HOLD P30_L5D_INSUFFICIENT_PUBLIC_DETAIL_SAMPLES");process.exitCode=2;
  }else{
    console.log("PASS P30_L5D_PUBLIC_FAMITICKET_BOUNDED_SAMPLE_CAPTURE_ONLY");
    if(valid.length<2)console.log("HOLD P30_L5D_MULTI_DETAIL_IDENTITY_QUALITY");
    if(roleCount===0)console.log("HOLD P30_L5D_NO_STRUCTURED_OFFICIAL_FIELD_ROLES_FOUND");
  }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const i=process.argv.indexOf("--out-dir");
  if(i<0||!process.argv[i+1]){console.error("HOLD_OUT_DIR");process.exitCode=2;}
  else await run(process.argv[i+1]);
}
