#!/usr/bin/env node
/** L7-C: immutable LIVE L7-B artifact -> independent mobile preview, NOT production. */
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {readFile,mkdir,copyFile,writeFile} from "node:fs/promises";
import {resolve,sep,basename} from "node:path";
import {fileURLToPath} from "node:url";
const hash=b=>createHash("sha256").update(b).digest("hex");
const ROOT=resolve(".");
export const KIND="EVENTRADAR_P30_L7C_ISOLATED_FRESH_REVIEW_PREVIEW_V1";
export const PARENT="EVENTRADAR_P30_L7B_FRESH_BOUNDED_CANDIDATES_V1";
export const PORTALS={
 "KKTIX":["kktix.com","kktix.cc"],"ACCUPASS":["accupass.com"],
 "拓元售票":["tixcraft.com"],"寬宏":["kham.com.tw"],"OPENTIX":["opentix.life"],
 "UDN售票網":["udnfunlife.com"],"FamiTicket":["famiticket.com.tw"],
 "年代售票":["ticket.com.tw"],"TixFun售票網":["tixfun.com"],
 "Event Go":["bnextmedia.com.tw"],"BeClass":["beclass.com"],
 "ibon":["ibon.com.tw"],"華山1914":["huashan1914.com"],
 "松山文創":["songshanculturalpark.org"],"KidsClub":["kidsclub.com.tw"],
 "台北世貿":["twtc.com.tw"],"中正紀念堂":["culture.tw"],
 "iNDIEVOX":["indievox.com"],"StrollTimes":["strolltimes.com"]
};
export function safeOfficialUrl(platform,value){
 try{
  const u=new URL(value);
  const known=PORTALS[platform];
  return !!known&&u.protocol==="https:"&&!u.username&&!u.password&&
   (!u.port||u.port==="443")&&known.some(h=>u.hostname===h||u.hostname.endsWith("."+h))&&
   !value.includes("\n")&&!value.includes("\r");
 }catch{return false;}
}
export function verifyParent(p,diag){
 assert.equal(p?.kind,PARENT);
 assert.equal(p?.candidateOrigin,"L7B_ACTUAL_NEW_PUBLIC_HTTP");
 assert.equal(diag?.kind,"EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1");
 assert.equal(diag.candidateOrigin,p.candidateOrigin);
 assert.equal(p.runId,diag.runId);
 assert.ok(/^P30-L7B-FRESH-[0-9]{8}-[0-9]{6}-[a-f0-9]{12}$/.test(p.runId));
 assert.ok(p.actualFreshHTTPRequests>0&&p.actualFreshHTTPRequests===diag.actualFreshHTTPRequests);
 assert.equal(diag.all19PlatformsAttempted,true);
 assert.equal(diag.platforms.length,19);
 assert.equal(p.fullPlatformCoverageVerified,false);
 assert.equal(diag.fullPlatformCoverageVerified,false);
 assert.equal(p.candidateCount,p.candidateEventRecords?.length);
 assert.equal(p.candidateCount,diag.counts.listCandidates);
 assert.equal(p.goldenAccepted,0);assert.equal(p.published,false);
 assert.equal(p.formalFieldPromotionCount,0);assert.equal(p.mergeAllowed,false);
 for(const [k,v] of [["writerExecuted",false],["schedulerExecuted",false],
  ["notifierExecuted",false],["published",false],["goldenAccepted",0],
  ["automaticMergeCount",0],["automaticHideCount",0],["deletedCount",0]])
    assert.equal(diag[k],v,k);
 const ids=new Set();
 for(const c of p.candidateEventRecords){
  assert.ok(c&&safeOfficialUrl(c.sourcePlatform,c.sourceUrl),"HOLD_FOREIGN_OR_UNTRUSTED_SOURCE_URL");
  assert.equal(c.candidateId,"er7b_"+hash(c.sourcePlatform+"\n"+c.sourceUrl).slice(0,24));
  assert.ok(!ids.has(c.candidateId),"HOLD_DUPLICATE_ID");
  ids.add(c.candidateId);
  assert.ok(typeof c.title==="string"&&c.title.length>=3&&c.title.length<=220);
  assert.equal(c.listEvidence?.provenance,"FRESH_HTML_ANCHOR");
  assert.equal(c.listEvidence?.listUrl?.startsWith("https://"),true);
  assert.equal(c.ticketStatus,"UNKNOWN");
  for(const field of ["dateStart","dateEnd","eventTimeZone","venue","price",
    "registrationPeriod","saleWindow","voucherValidity"])assert.equal(c[field],null,field);
  assert.equal(c.category,"待分類");
  assert.equal(c.mergeAllowed,false);assert.equal(c.goldenVerified,false);
  assert.equal(c.published,false);
  assert.equal(c.sourcePlatform==="StrollTimes",
   c.sourceRole==="THIRD_PARTY_AGGREGATOR_ARTICLE");
  if(c.detailIdentityVerified)assert.equal(c.detailStatus,"DETAIL_TITLE_PARITY_PASS");
  if(!c.detailIdentityVerified)assert.equal(c.fieldEvidence.length,0);
  for(const e of c.fieldEvidence){
   assert.equal(e.verification,"FRESH_LABEL_OBSERVED_REVIEW_REQUIRED");
   assert.equal(e.sourceUrl,c.detailHttp?.requestedUrl);
   assert.ok(e.observedValue.length<=110);
  }
 }
 return true;
}
export function convert(p,diag,sourceBytes){
 verifyParent(p,diag);
 const rootHash=hash(sourceBytes);
 const name="P30-L7C-REVIEW-"+rootHash.slice(0,16);
 const records=p.candidateEventRecords.map(c=>{
  const tier=c.detailIdentityVerified?"DETAIL_TITLE_PARITY_PASS":
      c.detailStatus==="NOT_SAMPLED"?"LIST_ONLY_UNVERIFIED":"DETAIL_IDENTITY_HOLD";
  return {
   candidateId:c.candidateId,sourcePlatform:c.sourcePlatform,sourceRole:c.sourceRole,
   sourceUrl:c.sourceUrl,title:c.title,qualityTier:tier,
   originalListUrl:c.listEvidence.listUrl,
   detailStatus:c.detailStatus,detailTitle:c.detailTitle,
   fieldEvidence:c.detailIdentityVerified?c.fieldEvidence:[],
   dateStart:null,dateEnd:null,venue:null,price:null,registrationPeriod:null,
   saleWindow:null,voucherValidity:null,ticketStatus:"UNKNOWN",
   category:"待分類",goldenVerified:false,published:false
  };
 }).sort((a,b)=>a.qualityTier.localeCompare(b.qualityTier)||a.sourcePlatform.localeCompare(b.sourcePlatform)||a.title.localeCompare(b.title));
 const verified=records.filter(x=>x.qualityTier==="DETAIL_TITLE_PARITY_PASS").length;
 const listOnly=records.filter(x=>x.qualityTier==="LIST_ONLY_UNVERIFIED").length;
 const hold=records.filter(x=>x.qualityTier==="DETAIL_IDENTITY_HOLD").length;
 return {kind:KIND,sourceKind:PARENT,sourceRunId:p.runId,
   sourceCandidateSHA256:rootHash,previewRunId:name,
   candidateOrigin:"L7C_PINNED_NEW_HTTP_ARTIFACT_PREVIEW_NOT_A_NEW_CRAWL",
   sourceCollectedAtUTC:p.collectedAtUTC,
   actualFreshHTTPRequestsInThisGate:0,sourceFreshHTTPRequests:p.actualFreshHTTPRequests,
   published:false,sourceRuntime:"DORMANT",goldenAccepted:0,
   acceptedAndroid44Preserved:true,previewOnly:true,
   counts:{total:records.length,verifiedDetail:verified,listOnly,identityHold:hold},
   items:records};
}
function safeDir(path){
 const d=resolve(path),d0=ROOT;
 if(d===d0||(!d.startsWith(d0+sep))||["docs",".git","scripts","tests",".github","schemas"].some(x=>
     d===resolve(x)||d.startsWith(resolve(x)+sep)))
  throw Error("HOLD_PREVIEW_OUTPUT_MUST_BE_ISOLATED");
 return d;
}
export async function run(parentFile,diagnosticFile,out){
 const bytes=await readFile(parentFile);
 const parent=JSON.parse(bytes),diag=JSON.parse(await readFile(diagnosticFile,"utf8"));
 const preview=convert(parent,diag,bytes);
 const dest=safeDir(out);
 await mkdir(dest,{recursive:true});
 const htmlSource=resolve("scripts/p30_l7c_isolated_index.html");
 await copyFile(htmlSource,dest+"/index.html");
 const data=JSON.stringify(preview,null,2)+"\n";
 await writeFile(dest+"/preview-data.json",data,"utf8");
 const md="P30-L7C isolated candidate UI preview from L7B fresh HTTP sealed artifact.\n"+
  "No new requests in this transform. NOT installed PWA, NOT production, NOT Golden.\n"+
  "Only "+preview.counts.verifiedDetail+" title-parity detail reviews; "+
  (preview.counts.listOnly+preview.counts.identityHold)+" others require review.\n"+
  "On Android Termux, from this extracted directory: python -m http.server 8766 --bind 127.0.0.1\n"+
  "Then open http://127.0.0.1:8766/index.html in the SAME phone browser.\n"+
  "Do not replace the historic accepted Android 44 or official Pages.\n";
 await writeFile(dest+"/README.txt",md,"utf8");
 const names=["index.html","preview-data.json","README.txt"];
 const shaLines=[];
 for(const file of names)shaLines.push(hash(await readFile(dest+"/"+file))+"  "+file);
 await writeFile(dest+"/SHA256SUMS.txt",shaLines.join("\n")+"\n","utf8");
 console.log("PASS P30_L7C_PINNED_FRESH_PARENT_REVIEW_ONLY",JSON.stringify(preview.counts));
 console.log("SOURCE_RUN",preview.sourceRunId,"SOURCE_SHA",preview.sourceCandidateSHA256);
 console.log("PASS P30_L7C_SHA_SEALED_ISOLATED_MOBILE_PREVIEW_NO_WRITES");
 return preview;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args={};for(let i=2;i<process.argv.length;i+=2)args[process.argv[i]]=process.argv[i+1];
 if(!args["--input"]||!args["--diagnostics"]||!args["--out"]){
  console.error("HOLD_L7C_INPUT_AND_OUTPUT_REQUIRED");process.exitCode=2;
 }else await run(args["--input"],args["--diagnostics"],args["--out"]);
}
