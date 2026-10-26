#!/usr/bin/env node
/**
 * P30-L5-E3-A: StrollTimes homepage-card vs canonical article H1 relation.
 * Diagnose four previously held identities using exact prior article URLs.
 * Evidence can suggest SUBEVENT_OF; only explicit organiser/venue/date proof
 * can later approve an edge. Never fuzzy merge, delete or publish.
 */
import {chromium} from "playwright";
import {readFile, mkdir, writeFile} from "node:fs/promises";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {canonicalArticle,safeAssetHost,articleHeadingMatches} from "./p30_l3bc_strolltimes.mjs";
export const KIND="EVENTRADAR_P30_L5E3_STROLLTIMES_ARTICLE_H1_RELATION_REVIEW_ONLY";
export const PARENT_KIND="EVENTRADAR_P30_L5E1_STROLLTIMES_ATTRIBUTED_SOURCE_LINEAGE_NOT_GOLDEN";
export const MAX_HELD=4,MAX_NETWORK=240;
export function n(s){return String(s??"").replace(/[\u200b-\u200d\ufeff]/g,"").replace(/\s+/g," ").trim().slice(0,240);}
const childTerms=/(?:場次|展區|子活動|分場|分會場|場域|主題場|館別|巡迴站|系列活動)/u;
const danger=/(?:延期|取消|停辦|結束|停演|已售完|售罄)/u;
export function titleRelation(listTitle,h1){
 const a=n(listTitle),b=n(h1);
 if(!a||!b)return {kind:"NO_VISIBLE_H1_HOLD",edgeType:null,rationale:"missing_visible_h1"};
 if(articleHeadingMatches(a,b))return {kind:"EXACT_AGGREGATOR_ARTICLE_MATCH",edgeType:null,rationale:"same_site_title"};
 // Broad title similarity is insufficient. Qualifier requires an actual
 // content word and a full left-prefix parent title.
 if(a.startsWith(b+" ")||a.startsWith(b+"　")||a.startsWith(b+"－")||a.startsWith(b+"：")){
  const suffix=a.slice(b.length).trim().replace(/^[－：:—-]\s*/u,"");
  if(suffix.length>=3&&childTerms.test(suffix)&&!danger.test(suffix))
   return {kind:"POTENTIAL_PARENT_CHILD_SUFFIX_REVIEW",
      edgeType:"SUBEVENT_OF_UNVERIFIED",
      rationale:"list_name_contains_explicit_subevent_qualifier",
      suffix:suffix.slice(0,90)};
 }
 // The same root plus the word '展區' alone does not establish organiser
 // ownership, and year/location differences cannot be silently folded.
 return {kind:"UNRESOLVED_LIST_ARTICLE_H1_HOLD",edgeType:null,
         rationale:"no_safe_structural_relationship"};
}
export function validateParent(parent){
 if(parent?.kind!==PARENT_KIND||parent.sourceRuntime!=="DORMANT"||
    parent.published!==false||parent.goldenAccepted!==false||
    parent.fieldPromotionCount!==0||parent.firstPartyEventDetailsIndependentlyVerified!==0||
    parent.articleSamplesCount!==6||parent.listCandidateCount!==24||
    parent.originalOfficialEventUrl!==null||parent.mainAndroid44Preserved!==true)
   throw Error("HOLD_E1_BASELINE_INTEGRITY");
 const held=parent.samples.filter(s=>s.articleIdentity==="ARTICLE_TITLE_OR_HTTP_HOLD");
 if(held.length!==MAX_HELD||new Set(held.map(x=>x.aggregatorUrl)).size!==MAX_HELD)
   throw Error("HOLD_FOUR_HELD_SOURCE_IDENTITIES");
 for(const item of held){
  if(!canonicalArticle(item.aggregatorUrl)||item.observedArticleUrl!==item.aggregatorUrl||
      item.articleHttp!==200||item.originalOfficialUrl!==null||
      item.dateStart!==null||item.dateEnd!==null||item.published!==false||
      item.goldenVerified!==false)
   throw Error("HOLD_HELD_ARTICLE_PROVENANCE");
 }
 return held;
}
export function compare(parent,observations){
 const held=validateParent(parent);
 if(observations.length!==MAX_HELD)throw Error("HOLD_REVIEW_SCOPE");
 const out=[];
 for(const row of held){
  const live=observations.find(x=>x.aggregatorUrl===row.aggregatorUrl);
  if(!live||live.currentUrl!==row.aggregatorUrl||live.http!==200)
    throw Error("HOLD_EXACT_SOURCE_TRANSPORT");
  const title=live.h1.length===1?live.h1[0]:"";
  const relation=titleRelation(row.title,title);
  out.push({
   articleUrl:row.aggregatorUrl,cardTitle:row.title,
   actualH1:title,headingsCount:live.h1.length,
   articleHTTP:200, relation,
   breadcrumbText:live.breadcrumbText.slice(0,8),
   articleSectionLabels:live.sectionHeadings.slice(0,12),
   scope:"STROLLTIMES_AGGREGATOR_TEXT_ONLY",
   sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",
   explicitFirstPartySameEventProof:false,
   edgeApproval:"NOT_VERIFIED",
   parentOrSubeventAutoMerged:false,
   originalOfficialUrl:null,dateStart:null,dateEnd:null,
   ticketStatus:"UNKNOWN",price:null,classification:"待分類",
   goldenVerified:false,published:false
  });
 }
 const proposed=out.filter(x=>x.relation.edgeType==="SUBEVENT_OF_UNVERIFIED").length;
 return {kind:KIND,originalListCount:parent.listCandidateCount,
   reviewedHeldArticleCount:out.length,explicitParentChildCandidates:proposed,
   exactIdentityRecovered:out.filter(x=>x.relation.kind==="EXACT_AGGREGATOR_ARTICLE_MATCH").length,
   unresolvedArticleCount:out.filter(x=>x.relation.kind==="UNRESOLVED_LIST_ARTICLE_H1_HOLD"||
        x.relation.kind==="NO_VISIBLE_H1_HOLD").length,
   reviews:out,
   firstPartyNewEventConfirmations:0,canonicalParentAutoMergeCount:0,
   deleteCount:0,fieldPromotionCount:0,goldenAccepted:false,published:false,
   writerExecuted:false,notifierExecuted:false,autoHidden:0,
   originalAndroid44Preserved:true,sourceRuntime:"DORMANT",
   all24FullyVerified:false};
}
function readDom(){
 const head=[...document.querySelectorAll("main h1,article h1,h1")]
  .map(x=>(x.textContent||"").replace(/\s+/g," ").trim())
  .filter(Boolean);
 const unique=[...new Set(head)].slice(0,3);
 const breadcrumbs=[...document.querySelectorAll('nav[aria-label*="breadcrumb" i] a, [class*="breadcrumb" i] a')]
  .map(x=>(x.textContent||"").replace(/\s+/g," ").trim()).filter(Boolean).slice(0,8);
 const sections=[...document.querySelectorAll("main h2,main h3,article h2,article h3")]
  .map(x=>(x.textContent||"").replace(/\s+/g," ").trim()).filter(Boolean).slice(0,12);
 return {h1:unique,breadcrumbText:breadcrumbs,sectionHeadings:sections};
}
export async function run(parentPath,destination){
 const dir=resolve(destination),docs=resolve("docs");
 if(dir===docs||dir.startsWith(docs+"/"))throw Error("HOLD_PRODUCTION_WRITER_PATH");
 const parent=JSON.parse(await readFile(parentPath,"utf8"));
 const held=validateParent(parent);
 const metrics={navigationCount:0,requestCount:0,blockedOutside:0,
    blockedAssets:0,blockedBudget:0,pageErrors:0};
 const observations=[];
 const browser=await chromium.launch({headless:true});
 try {
  const ctx=await browser.newContext({serviceWorkers:"block",permissions:[],
      acceptDownloads:false,javaScriptEnabled:true});
  const page=await ctx.newPage();
  page.on("pageerror",()=>metrics.pageErrors++);
  await page.route("**/*",async route=>{
   const req=route.request();
   if(!safeAssetHost(req.url())){metrics.blockedOutside++;return route.abort("blockedbyclient");}
   if(["image","font","media"].includes(req.resourceType())){
    metrics.blockedAssets++;return route.abort("blockedbyclient");
   }
   if(metrics.requestCount>=MAX_NETWORK){metrics.blockedBudget++;return route.abort("blockedbyclient");}
   metrics.requestCount++;return route.continue();
  });
  for(const row of held){
   let status=null,url=null,dom=null,err=null;
   try{
    const response=await page.goto(row.aggregatorUrl,{waitUntil:"domcontentloaded",timeout:23000});
    metrics.navigationCount++;status=response?.status()??null;url=page.url();
    if(status===200&&canonicalArticle(url)===row.aggregatorUrl){
      await page.waitForTimeout(1300);
      dom=await page.evaluate(readDom);
    }
   }catch(e){err=String(e?.name||"Error");}
   observations.push({aggregatorUrl:row.aggregatorUrl,
     currentUrl:url,http:status,h1:dom?.h1||[],
     breadcrumbText:dom?.breadcrumbText||[],
     sectionHeadings:dom?.sectionHeadings||[],errorType:err});
  }
  await ctx.close();
 }finally{await browser.close();}
 let result=null,issue=null;
 try{result=compare(parent,observations);}catch(e){issue=String(e.message||e);}
 const final=result||{kind:KIND,reviewState:"SOURCE_OR_TRANSPORT_HOLD",
   observations:observations.map(x=>({aggregatorUrl:x.aggregatorUrl,currentUrl:x.currentUrl,
        http:x.http,h1:x.h1,errorType:x.errorType})),
   issue,fieldPromotionCount:0,goldenAccepted:false,published:false,
   writerExecuted:false,notifierExecuted:false,autoHidden:0,
   sourceRuntime:"DORMANT",originalAndroid44Preserved:true};
 final.network=metrics;final.maxNavigation=MAX_HELD;final.maxRequests=MAX_NETWORK;
 final.noLogin=true;final.noCheckout=true;final.noCaptchaBypass=true;
 final.noStealth=true;final.noPrivateAPI=true;final.noRetries=true;
 await mkdir(dir,{recursive:true});
 await writeFile(dir+"/article_hierarchy_review.json",JSON.stringify(final,null,2)+"\n");
 console.log("L5E3_ARTICLE_NAV",metrics.navigationCount,"REQUESTS",metrics.requestCount);
 if(result){
  for(const row of result.reviews)console.log("L5E3_HELD_ARTICLE",JSON.stringify({
    cardTitle:row.cardTitle,h1:row.actualH1,relation:row.relation,
    breadcrumbs:row.breadcrumbText,sections:row.articleSectionLabels}));
  console.log("PASS P30_L5E3_4_PREVIOUS_HELD_ARTICLE_HEADINGS_CAPTURED");
  console.log("L5E3_RELATIONS",result.explicitParentChildCandidates,
      result.unresolvedArticleCount,result.exactIdentityRecovered);
  console.log("HOLD P30_L5E3_NO_AUTOMERGE_NO_UNVERIFIED_SOURCE_PROMOTION");
 }else{
  console.log("HOLD P30_L5E3_REAL_ARTICLE_IDENTITY",issue);
  process.exitCode=2;
 }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const a=process.argv.indexOf("--parent"),b=process.argv.indexOf("--out-dir");
 if(a<0||b<0||!process.argv[a+1]||!process.argv[b+1]){
  console.error("HOLD_REQUIRED_ARGS");process.exitCode=2;
 }else await run(process.argv[a+1],process.argv[b+1]);
}
