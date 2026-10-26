#!/usr/bin/env node
/**
 * P30-L6-A / G5J: reversible, offline event identity and classification review.
 * Consumes a SHA-pinned L5-E3 graph. These are six aggregator ARTICLE identities
 * NOT six verified first-party events. Similar titles/date/venue are not merges.
 *
 * Outputs a deterministic 6-node classification review, 15 pairwise evidence
 * assessments and an exact reversible 7-edge audit. ALL decisions no-write.
 */
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
export const KIND="EVENTRADAR_P30_L6A_G5J_REVERSIBLE_CLASSIFICATION_AND_DEDUP_REVIEW_ONLY";
export const PARENT="EVENTRADAR_P30_L5E3_STROLLTIMES_REVERSIBLE_ARTICLE_GRAPH_REVIEW_ONLY";
export const BITAN="https://strolltimes.com/events/new-taipei/261016084730/";
export const CAL="https://newtaipei.travel/zh-tw/calendar/detail/4058";
const count=(arr,fn)=>arr.filter(fn).length;
const norm=s=>String(s??"").normalize("NFKC").replace(/[\u200B-\u200D\uFEFF]/g,"").replace(/[\s\p{P}\p{S}]/gu,"").trim();
const stripDates=s=>norm(s).replace(/20\d{2}/g,"").replace(/(?:\d{1,2}月\d{1,2}日?)/g,"");
export function classificationHint(title){
  const t=String(title??"");
  if(!t.trim())return {categoryHint:"待分類",matchedKeywords:[],reason:"EMPTY_TITLE_HOLD"};
  // Keyword evidence is NOT first-party activity classification.
  const rules=[
    ["文化節慶",["萬聖節","文化節","藝術季","晴空季"]],
    ["藝文展覽",["展覽","裝置展","藝術展","展期"]],
    ["戶外自然",["步道","登山","賞鳥","健行","自然生態"]],
    ["音樂演出",["音樂會","演唱會","演出"]],
  ];
  const hits=rules.flatMap(([cat,words])=>words.filter(w=>t.includes(w)).map(w=>({cat,word:w})));
  if(!hits.length)return {categoryHint:"待分類",matchedKeywords:[],reason:"NO_ALLOWED_KEYWORD"};
  const distinct=[...new Set(hits.map(x=>x.cat))];
  if(distinct.length!==1)return {categoryHint:"待分類",matchedKeywords:hits.map(x=>x.word),
    reason:"COMPETING_CATEGORY_KEYWORDS_HOLD"};
  return {categoryHint:distinct[0],matchedKeywords:hits.map(x=>x.word),
    reason:"TITLE_KEYWORD_PROPOSAL_ONLY"};
}
export function pairEvidence(a,b){
 const ta=stripDates(a.homepageCardTitle),tb=stripDates(b.homepageCardTitle);
 // URL equality is checked as a hard graph invalidity; matching fragments
 // on distinct URLs never establish duplicate activity, organiser or season.
 let overlap=null;
 if(ta&&tb&&(ta===tb||ta.includes(tb)||tb.includes(ta))){
  if(Math.min(ta.length,tb.length)>=5)overlap=ta.length<=tb.length?ta:tb;
 }
 return {a:a.id,b:b.id,
   articleUrlsDifferent:a.id!==b.id,
   titleRelationship:overlap?"TITLE_OVERLAP_REVIEW_ONLY":"NO_SUBSTANTIVE_TITLE_OVERLAP_OBSERVED",
   sharedTitleEvidence:overlap,
   primarySourceCrossIdentity:"NOT_PROVEN",
   organiserSame:"NOT_PROVEN",
   venueSame:"NOT_PROVEN",
   dateOrSessionSame:"NOT_PROVEN",
   editionSame:"NOT_PROVEN",
   relationship:"UNKNOWN_NOT_MERGED",
   proposedAction:"KEEP_SEPARATE_PENDING_EVIDENCE",
   mergeAllowed:false,autoHideAllowed:false,deleteAllowed:false};
}
export function verifyGraph(graph){
 if(!graph||graph.kind!==PARENT||graph.sourceRole!=="THIRD_PARTY_EVENT_AGGREGATOR"||
    graph.sourceRuntime!=="DORMANT"||graph.published!==false||
    graph.goldenAccepted!==false||graph.writerExecuted!==false||
    graph.notifierExecuted!==false||graph.autoHidden!==0||
    graph.accepted44AndroidPreserved!==true||
    graph.sourceEventPromotionCount!==0||graph.formalDatePromotionCount!==0||
    graph.automaticDedupMergeCount!==0||graph.confirmedParentChildEventEdges!==0||
    graph.graphReversible!==true||
    graph.all24AggregatorDetailsVerified!==false||
    graph.all23OthersOriginalSourcesVerified!==false||
    graph.oneIndependentGovReferenceCount!==1||
    graph.currentSampleCount!==6||graph.priorArticleSampleCount!==6||
    graph.priorE1ExactH1Count!==2||graph.currentExactH1Count!==2||
    graph.nodes?.length!==6||graph.edges?.length!==7)
   throw Error("HOLD_L5E3_PARENT_GOVERNANCE");
 const nodes=graph.nodes,ids=nodes.map(n=>n.id);
 if(new Set(ids).size!==6||ids.some(id=>!/^https:\/\/strolltimes\.com\/events\/[a-z-]+\/\d{12}\/$/.test(id)))
   throw Error("HOLD_GRAPH_CANONICAL_URL_IDENTITY");
 const exactStates=new Set([
  "AGGREGATOR_TITLE_IDENTITY_MATCH",
  "TITLE_OVERLAP_RELATIONSHIP_REVIEW",
  "EDITORIAL_HEADLINE_EXTENSION_REVIEW",
  "DISJOINT_TITLE_IDENTITY_HOLD",
  "HTTP_OR_REDIRECT_HOLD",
  "ARTICLE_H1_EMPTY_HOLD"
 ]);
 for(const n of nodes){
  if(n.role!=="THIRD_PARTY_EVENT_AGGREGATOR"||n.platform!=="StrollTimes"||
     !n.homepageCardTitle||!n.articleH1||!exactStates.has(n.currentTitleState)||
     n.mergeAllowed!==false||n.sourceEventDateStart!==null||
     n.sourceEventDateEnd!==null||n.price!==null||n.ticketStatus!=="UNKNOWN"||
     n.goldenVerified!==false||n.published!==false||
     !["ONE_INDEPENDENT_GOV_EVENT_CORROBORATED_REVIEW_ONLY","NOT_VERIFIED"].includes(n.officialGovernmentProof))
   throw Error("HOLD_UNTRUSTED_GRAPH_NODE_PROMOTION");
  if((n.id===BITAN)!==(n.officialGovernmentProof==="ONE_INDEPENDENT_GOV_EVENT_CORROBORATED_REVIEW_ONLY"))
   throw Error("HOLD_FALSE_GOV_CORROBORATION_ON_OTHER_NODE");
 }
 const home=graph.edges.filter(e=>e.kind==="AGGREGATOR_LIST_CARD_POINTS_TO_SAME_ARTICLE");
 const gov=graph.edges.filter(e=>e.kind==="ONE_EVENT_OFFICIAL_GOV_CALENDAR_CORROBORATED");
 if(home.length!==6||gov.length!==1||count(graph.edges,e=>e.mergeAllowed!==false)>0||
    new Set(home.map(e=>e.to)).size!==6||
    home.some(e=>!ids.includes(e.to)||e.from!=="strolltimes-home-card:"+e.to||
      e.originalOrganiserProven!==false||e.state!=="OBSERVED_SAME_ARTICLE_URL")||
    gov[0].from!==BITAN||gov[0].to!==CAL||
    gov[0].source!=="P30_L5E2_PINNED_GOV_ARTIFACT"||
    JSON.stringify(gov[0].eventPeriodReviewOnly)!==JSON.stringify(["2026-10-17","2026-12-13"])||
    gov[0].state!=="INDEPENDENT_FIRST_PARTY_EVIDENCE_FOR_ONE_EVENT"||
    gov[0].organisationAndUpdatesFullyVerified!==false)
   throw Error("HOLD_SEVEN_SOURCE_EDGE_IDENTITY");
 const held=(graph.notesRequiringReview||[]);
 if(held.length!==4||new Set(held.map(x=>x.articleUrl)).size!==4||
    held.some(x=>!ids.includes(x.articleUrl)||x.autoMergeAllowed!==false))
   throw Error("HOLD_E3_FOUR_REVIEW_NOTES");
 return true;
}
export function buildReview(graph){
 verifyGraph(graph);
 const ordered=[...graph.nodes].sort((a,b)=>a.id.localeCompare(b.id,"en"));
 const candidates=ordered.map(n=>{
  const hint=classificationHint(n.homepageCardTitle);
  const editorial=n.currentTitleState==="EDITORIAL_HEADLINE_EXTENSION_REVIEW";
  const series=n.currentTitleState==="TITLE_OVERLAP_RELATIONSHIP_REVIEW";
  const eventSource=n.id===BITAN?"ONE_FIRST_PARTY_CALENDAR_CORROBORATED_REVIEW_ONLY":"AGGREGATOR_ONLY";
  // Evidence rank describes SOURCE QUALITY only, never likelihood of duplicate.
  const provenanceRank=n.id===BITAN?3:n.currentTitleState==="AGGREGATOR_TITLE_IDENTITY_MATCH"?2:1;
  return {id:n.id,homepageCardTitle:n.homepageCardTitle,
    observedArticleH1:n.articleH1,sourceRole:"THIRD_PARTY_EVENT_AGGREGATOR",
    provenance: eventSource,provenanceRank,
    identityReview:n.currentTitleState,
    relationshipRisk:series?"POSSIBLE_SERIES_SUBEVENT_HOLD":editorial?
      "EDITORIAL_TITLE_SUFFIX_REVIEW":"NO_CONFIRMED_PARENT_SUBEVENT",
    categoryHint:hint.categoryHint,categoryEvidence:hint.matchedKeywords,
    classificationReason:hint.reason,
    officialCategoryVerified:false,officialOriginalEventDetailVerified:n.id===BITAN,
    // Government calendar period is only review evidence, not default event fields.
    referenceOfficialUrl:n.id===BITAN?CAL:null,
    referenceOfficialPeriod:n.id===BITAN?["2026-10-17","2026-12-13"]:null,
    dateStart:null,dateEnd:null,venue:null,
    ticketStatus:"UNKNOWN",price:null,mergedWith:[],
    proposedAction:"RETAIN_AS_UNPUBLISHED_CANDIDATE",
    goldenVerified:false,published:false,autoMergeAllowed:false,
    autoHideAllowed:false,deleteAllowed:false};
 });
 const pairs=[];
 for(let i=0;i<ordered.length;i++)for(let j=i+1;j<ordered.length;j++)
   pairs.push(pairEvidence(ordered[i],ordered[j]));
 const sortedEdges=graph.edges.map(e=>({
    from:e.from,to:e.to,kind:e.kind,reviewOnly:true,mergeAllowed:false
 })).sort((a,b)=>(a.from+"|"+a.to).localeCompare(b.from+"|"+b.to,"en"));
 return {kind:KIND,sourceParentKind:PARENT,
   policy:"EXPLICIT_ORIGINAL_EVENT_ID_AND_COMPATIBLE_EDITION_SESSION_REQUIRED_FOR_FUTURE_MERGE",
   inputNodes:6,reviewedCandidates:candidates,reviewPairs:pairs,
   sourceEvidenceEdges:sortedEdges,
   pairedReviewCount:pairs.length,oneGovernmentReferenceCount:1,
   provisionalClassificationCount:count(candidates,x=>x.categoryHint!=="待分類"),
   officialClassificationPromotions:0,confirmedDuplicatePairs:0,
   tentativeCrossPlatformDuplicates:0,automaticMergeCount:0,
   automaticHideCount:0,deleteCount:0,manuallyApprovedMergeCount:0,
   actualMergedRecords:0,
   originalFirstPartyArticleProofsForOther23:0,
   firstPartyGovEvidenceLimitedToBitan:true,
   graphReversible:true,restorePlan:"NO_MUTATIONS_WERE_PERFORMED",
   accepted44AndroidPreserved:true,
   formalDatePromotionCount:0,formalFieldPromotionCount:0,
   goldenAccepted:false,published:false,writerExecuted:false,
   notifierExecuted:false,autoHidden:0,sourceRuntime:"DORMANT"};
}
export async function run(input,outdir){
 const path=resolve(outdir),docs=resolve("docs");
 if(path===docs||path.startsWith(docs+"/"))throw Error("HOLD_PRODUCTION_WRITER");
 const raw=await readFile(input);
 const result=buildReview(JSON.parse(raw));
 result.inputGraphSHA256=createHash("sha256").update(raw).digest("hex");
 await mkdir(path,{recursive:true});
 await writeFile(path+"/dedup_classification_review.json",JSON.stringify(result,null,2)+"\n");
 console.log("L6A_G5J_INPUT",result.inputNodes,"PAIRWISE",result.pairedReviewCount,
   "EDGES",result.sourceEvidenceEdges.length,"PROVISIONAL_CATEGORY",result.provisionalClassificationCount);
 for(const x of result.reviewedCandidates)
  console.log("L6A_G5J_CANDIDATE",JSON.stringify({title:x.homepageCardTitle,
    category:x.categoryHint,provenance:x.provenance,risk:x.relationshipRisk,
    approval:"REVIEW_ONLY"}));
 console.log("PASS L6A_G5J_6_CANDIDATES_15_PAIRS_7_REVERSIBLE_EDGES");
 console.log("PASS L6A_G5J_ZERO_AUTOMATIC_MERGE_HIDE_DELETE_OR_FIELD_PROMOTION");
 console.log("HOLD L6A_G5J_UNVERIFIED_CROSS_EVENT_PARENT_CHILD_AND_ORIGINAL_SOURCE");
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const a=process.argv.indexOf("--input"),b=process.argv.indexOf("--out-dir");
 if(a<0||b<0||!process.argv[a+1]||!process.argv[b+1]){
   console.error("HOLD_REQUIRED_PINNED_E3_INPUT_OUTPUT");process.exitCode=2;
 }else await run(process.argv[a+1],process.argv[b+1]);
}
