#!/usr/bin/env node
/** P30-L5-E3: bound homepage card -> exact aggregator article URL,
 * observe H1 without conflating a parent event, venue subevent, or date suffix.
 * One original government corroborated Bitan node is REFERENCE-ONLY.
 * Reversible graph proposals only; no automatic merge/Golden/app writer.
 */
import {chromium} from "playwright";
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {HOME,canonicalArticle,articleHeadingMatches,safeAssetHost,normalize} from "./p30_l3bc_strolltimes.mjs";
export const KIND="EVENTRADAR_P30_L5E3_STROLLTIMES_REVERSIBLE_ARTICLE_GRAPH_REVIEW_ONLY";
export const PARENT_E1="EVENTRADAR_P30_L5E1_STROLLTIMES_ATTRIBUTED_SOURCE_LINEAGE_NOT_GOLDEN";
export const PARENT_E2="EVENTRADAR_P30_L5E2_BITAN_GOV_EVENT_IDENTITY_REVIEW_ONLY";
export const BITAN="https://strolltimes.com/events/new-taipei/261016084730/";
const MAX_SAMPLES=6,MAX_REQUESTS=300;
const take=s=>String(s??"").replace(/[\u200B-\u200D\uFEFF]/g,"").replace(/\s+/g," ").trim().slice(0,220);
export function lexicalIdentity(cardTitle,h1) {
 const a=take(cardTitle),b=take(h1);
 if(!a||!b)return {state:"ARTICLE_H1_EMPTY_HOLD",commonTitleEvidence:null,
   parentChildRelationship:"NOT_PROVEN",mergeAllowed:false};
 if(articleHeadingMatches(a,b))
   return {state:"AGGREGATOR_TITLE_IDENTITY_MATCH",commonTitleEvidence:a,
     parentChildRelationship:"NOT_PROVEN",mergeAllowed:false};
 // Meaningful shared Han phrase is only a discovery hint. The repeated
 // calendar year "2026", city name or common "活動" alone proves nothing.
 const cn=s=>s.replace(/20\d{2}/g,"").replace(/[^\p{Script=Han}]/gu,"");
 const aa=cn(a),bb=cn(b);
 let overlap="";
 for(let n=Math.min(aa.length,bb.length,24);n>=5;n--){
  for(let i=0;i+n<=aa.length;i++){
   const chunk=aa.slice(i,i+n);
   if(bb.includes(chunk)){overlap=chunk;break;}
  }
  if(overlap)break;
 }
 return {state:overlap?"TITLE_OVERLAP_RELATIONSHIP_REVIEW":"DISJOINT_TITLE_IDENTITY_HOLD",
   commonTitleEvidence:overlap||null,
   parentChildRelationship:"POSSIBLE_PARENT_OR_SUBEVENT_NOT_VERIFIED",
   mergeAllowed:false};
}
export function validateParents(e1,e2){
 if(e1?.kind!==PARENT_E1||e1.sourceRuntime!=="DORMANT"||
    e1.published!==false||e1.goldenAccepted!==false||
    e1.fieldPromotionCount!==0||e1.firstPartyEventDetailsIndependentlyVerified!==0||
    e1.listCandidateCount!==24||e1.articleSamplesCount!==6||
    !Array.isArray(e1.samples)||e1.samples.length!==6)
     throw Error("HOLD_E1_GOVERNANCE_OR_SAMPLE_SET");
 const urls=e1.samples.map(x=>x.aggregatorUrl);
 if(new Set(urls).size!==6||urls.some(u=>canonicalArticle(u)!==u))
   throw Error("HOLD_E1_SOURCE_ARTICLE_URL_IDENTITY");
 for(const x of e1.samples){
  if(!x.title||x.published!==false||x.goldenVerified!==false||
     x.originalOfficialUrl!==null||x.dateStart!==null||x.dateEnd!==null)
   throw Error("HOLD_E1_SAMPLE_FIELD_PROMOTION");
 }
 if(e2?.kind!==PARENT_E2||e2.sourceRuntime!=="DORMANT"||
    e2.published!==false||e2.goldenAccepted!==false||
    e2.finalDatePromotionCount!==0||
    e2.sourceAggregatorUrl!==BITAN||
    e2.officialFirstPartyIndependentEventIdentityCount!==1||
    e2.reviewOnlyOfficialEventUrl!=="https://newtaipei.travel/zh-tw/calendar/detail/4058"||
    JSON.stringify(e2.reviewOnlyOfficialEventPeriod)!==JSON.stringify(["2026-10-17","2026-12-13"])||
    e2.original44AndroidPreserved!==true||e2.allOtherAggregatorArticlesVerified!==false)
    throw Error("HOLD_E2_SINGLE_OFFICIAL_BITAN_PROOF");
 if(!urls.includes(BITAN))throw Error("HOLD_BITAN_NOT_IN_E1_SAMPLE");
 return true;
}
export function graphFromEvidence(e1,e2,observed,net){
 validateParents(e1,e2);
 if(!Array.isArray(observed)||observed.length!==6)throw Error("HOLD_SIX_OBSERVED_ARTICLE_COUNT");
 const observations=new Map();
 for(const x of observed){
  if(!x||canonicalArticle(x.aggregatorUrl)!==x.aggregatorUrl||
    observations.has(x.aggregatorUrl))throw Error("HOLD_DUPLICATE_OR_FOREIGN_OBSERVED_URL");
  observations.set(x.aggregatorUrl,x);
 }
 const nodes=[],edges=[],held=[];
 for(const source of e1.samples){
  const fresh=observations.get(source.aggregatorUrl);
  if(!fresh)throw Error("HOLD_MISSING_OBSERVED_SOURCE");
  const transport=Number(fresh.httpStatus)===200&&
     canonicalArticle(fresh.finalUrl)===source.aggregatorUrl;
  const h1=transport?take(fresh.h1):"";
  const title=transport?lexicalIdentity(source.title,h1):
     {state:"HTTP_OR_REDIRECT_HOLD",commonTitleEvidence:null,
       parentChildRelationship:"NOT_PROVEN",mergeAllowed:false};
  const e1Match=source.articleIdentity==="AGGREGATOR_ARTICLE_H1_MATCH";
  const oldH1=source.articleIdentity==="AGGREGATOR_ARTICLE_H1_MATCH"?"EXACT_AT_E1":"HOLD_AT_E1";
  const canonicalId=source.aggregatorUrl;
  const node={id:canonicalId,platform:"StrollTimes",role:"THIRD_PARTY_EVENT_AGGREGATOR",
    homepageCardTitle:source.title,articleH1:h1,
    priorE1TitleStatus:oldH1,currentTitleState:title.state,
    titleOverlapEvidence:title.commonTitleEvidence,
    currentHttpStatus:fresh.httpStatus,currentUrl:fresh.finalUrl,
    officialGovernmentProof:e2.sourceAggregatorUrl===canonicalId?
      "ONE_INDEPENDENT_GOV_EVENT_CORROBORATED_REVIEW_ONLY":"NOT_VERIFIED",
    originalOfficialUrl:null,sourceEventDateStart:null,sourceEventDateEnd:null,
    ticketStatus:"UNKNOWN",price:null,classification:"待分類",mergeAllowed:false,
    goldenVerified:false,published:false};
  nodes.push(node);
  // The only unconditional edge is homepage title pointing to the same
  // canonical article URL: it is NOT a claim these are duplicate events.
  edges.push({from:"strolltimes-home-card:"+canonicalId,to:canonicalId,
   kind:"AGGREGATOR_LIST_CARD_POINTS_TO_SAME_ARTICLE",
   state:transport?"OBSERVED_SAME_ARTICLE_URL":"HTTP_IDENTITY_HOLD",
   mergeAllowed:false,originalOrganiserProven:false});
  if(title.state!=="AGGREGATOR_TITLE_IDENTITY_MATCH"){
   held.push({articleUrl:canonicalId,homepageTitle:source.title,observedH1:h1,
     role:"PARENT_SUBEVENT_OR_TITLE_VARIANT_REVIEW_ONLY",
     proposedRelationship:title.parentChildRelationship,
     titleEvidence:title.commonTitleEvidence,
     priorE1State:oldH1,reviewStatus:"MANUAL_OR_PRIMARY_EVENT_IDENTITY_REQUIRED",
     autoMergeAllowed:false});
  }
  if(!e1Match&&title.state==="AGGREGATOR_TITLE_IDENTITY_MATCH"){
   // A newer DOM observation cannot erase previously recorded H1 drift.
   held.push({articleUrl:canonicalId,role:"HISTORICAL_TITLE_DRIFT_REVIEW_ONLY",
      priorE1State:oldH1,reviewStatus:"REQUIRES_STABLE_ORGANISER_PROOF",
      autoMergeAllowed:false});
  }
 }
 // First-party evidence from governmental calendar is independent from the
 // aggregator card and H1. It is an evidence edge, not automatic dedup.
 edges.push({from:BITAN,to:e2.reviewOnlyOfficialEventUrl,
  kind:"ONE_EVENT_OFFICIAL_GOV_CALENDAR_CORROBORATED",
  source:"P30_L5E2_PINNED_GOV_ARTIFACT",
  eventPeriodReviewOnly:e2.reviewOnlyOfficialEventPeriod,
  state:"INDEPENDENT_FIRST_PARTY_EVIDENCE_FOR_ONE_EVENT",
  mergeAllowed:false,organisationAndUpdatesFullyVerified:false});
 const exact=nodes.filter(x=>x.currentTitleState==="AGGREGATOR_TITLE_IDENTITY_MATCH").length;
 return {kind:KIND,sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",
  priorArticleSampleCount:6,currentSampleCount:6,
  priorE1ExactH1Count:e1.exactAggregatorArticleCount,
  currentExactH1Count:exact,notesRequiringReview:held,
  nodes,edges,
  oneIndependentGovReferenceCount:1,
  confirmedParentChildEventEdges:0,automaticDedupMergeCount:0,
  all24AggregatorDetailsVerified:false,all23OthersOriginalSourcesVerified:false,
  graphReversible:true,sourceEventPromotionCount:0,
  formalDatePromotionCount:0,accepted44AndroidPreserved:true,
  goldenAccepted:false,published:false,writerExecuted:false,
  notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT",
  network:net||null};
}
function articleDOM(){
 const root=document.querySelector("main")||document.querySelector("article")||document.body;
 return {h1:[...root.querySelectorAll("h1")].map(x=>x.textContent.replace(/\s+/g," ").trim()).filter(Boolean).slice(0,3),
   headings:[...root.querySelectorAll("h2,h3")].map(x=>x.textContent.replace(/\s+/g," ").trim()).filter(Boolean).slice(0,7),
   textLength:(root.innerText||"").length};
}
export async function run(e1Path,e2Path,outDir){
 const target=resolve(outDir),docs=resolve("docs");
 if(target===docs||target.startsWith(docs+"/"))throw Error("HOLD_PRODUCTION_WRITER");
 const bytes1=await readFile(e1Path),bytes2=await readFile(e2Path);
 const e1=JSON.parse(bytes1),e2=JSON.parse(bytes2);
 validateParents(e1,e2);
 const net={navigationCount:0,allowedRequests:0,blockedExternal:0,blockedAssets:0,
  blockedBudget:0,pageErrors:0};
 const obs=[];
 const browser=await chromium.launch({headless:true});
 try{
  const ctx=await browser.newContext({serviceWorkers:"block",javaScriptEnabled:true,
    acceptDownloads:false,permissions:[]});
  const page=await ctx.newPage();
  page.on("pageerror",()=>net.pageErrors++);
  await page.route("**/*",async route=>{
   const q=route.request();
   if(!safeAssetHost(q.url())){net.blockedExternal++;return route.abort("blockedbyclient");}
   if(["image","media","font"].includes(q.resourceType())){net.blockedAssets++;return route.abort("blockedbyclient");}
   if(net.allowedRequests>=MAX_REQUESTS){net.blockedBudget++;return route.abort("blockedbyclient");}
   net.allowedRequests++;return route.continue();
  });
  for(const src of e1.samples){
   let httpStatus=null,finalUrl=null,dom=null,error=null;
   try{
    const response=await page.goto(src.aggregatorUrl,{waitUntil:"domcontentloaded",timeout:20000});
    net.navigationCount++;httpStatus=response?.status()??null;finalUrl=page.url();
    if(httpStatus===200&&canonicalArticle(finalUrl)===src.aggregatorUrl){
     await page.waitForTimeout(950);dom=await page.evaluate(articleDOM);
    }
   }catch(e){error=String(e?.name||"NavigationError");}
   obs.push({aggregatorUrl:src.aggregatorUrl,httpStatus,finalUrl,h1:dom?.h1[0]||"",
      sampledHeadings:dom?.headings||[],visibleChars:dom?.textLength||0,
      exceptionType:error});
  }
  await ctx.close();
 }finally{await browser.close();}
 const result=graphFromEvidence(e1,e2,obs,net);
 result.observedAtUTC=new Date().toISOString();
 result.e1ArtifactInputSHA256=createHash("sha256").update(bytes1).digest("hex");
 result.e2ArtifactInputSHA256=createHash("sha256").update(bytes2).digest("hex");
 result.maxArticleNavigation=MAX_SAMPLES;result.maxApprovedRequests=MAX_REQUESTS;
 result.noCheckout=true;result.noLogin=true;result.noStealth=true;
 result.noCaptchaBypass=true;result.noUndocumentedAPI=true;result.noRetries=true;
 await mkdir(target,{recursive:true});
 await writeFile(target+"/identity_graph_review.json",JSON.stringify(result,null,2)+"\n");
 console.log("STROLL_L5E3_GRAPH_SAMPLES",result.currentSampleCount,"EXACT",result.currentExactH1Count,
  "PRIOR_E1_EXACT",result.priorE1ExactH1Count,
  "REVIEW_RECORDS",result.notesRequiringReview.length);
 for(const x of result.nodes)console.log("STROLL_L5E3_TITLE",JSON.stringify({
   homepage:x.homepageCardTitle,h1:x.articleH1,state:x.currentTitleState,
   overlap:x.titleOverlapEvidence,old:x.priorE1TitleStatus,http:x.currentHttpStatus}));
 console.log("STROLL_L5E3_EDGES",result.edges.length,
  "PARENT_CHILD_CONFIRMED",result.confirmedParentChildEventEdges,
  "GOV_CORROBORATED",result.oneIndependentGovReferenceCount);
 if(net.navigationCount!==6||result.currentExactH1Count<2){
  console.log("HOLD P30_L5E3_ARTICLE_REOBSERVATION_INCOMPLETE");process.exitCode=2;
 }else{
  console.log("PASS P30_L5E3_6_SOURCE_BOUND_REOBSERVED_AND_REVERSIBLE_GRAPH");
  console.log("HOLD P30_L5E3_UNVERIFIED_PARENT_SUBEVENT_OR_TITLE_DRIFT");
  console.log("PASS P30_L5E3_ZERO_AUTO_MERGE_ZERO_PUBLISHED_DATA");
 }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const a=process.argv.indexOf("--e1"),b=process.argv.indexOf("--e2"),c=process.argv.indexOf("--out-dir");
 if(a<0||b<0||c<0||!process.argv[a+1]||!process.argv[b+1]||!process.argv[c+1]){
  console.error("HOLD_REQUIRED_E1_E2_OUTPUT");process.exitCode=2;
 }else await run(process.argv[a+1],process.argv[b+1],process.argv[c+1]);
}
