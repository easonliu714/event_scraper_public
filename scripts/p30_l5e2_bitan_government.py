#!/usr/bin/env python3
"""P30-L5-E2 BItan independent New Taipei government organiser event identity.

Read-only against exact allowlist one govt calendar, one municipal news;
does not follow social credits nor promote to production/GOLDEN.
"""
import argparse
from datetime import datetime, timezone
import hashlib, json, re, time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup

KIND="EVENTRADAR_P30_L5E2_BITAN_GOV_EVENT_IDENTITY_REVIEW_ONLY"
PARENT="EVENTRADAR_P30_L5E1_STROLLTIMES_ATTRIBUTED_SOURCE_LINEAGE_NOT_GOLDEN"
AGG_URL="https://strolltimes.com/events/new-taipei/261016084730/"
CALENDAR="https://newtaipei.travel/zh-tw/calendar/detail/4058"
MUNICIPAL="https://www.ntpc.gov.tw/ch/home.jsp?dataserno=66daa0e44fad9dd95b5b7e5ece1bf28d&id=e8ca970cde5c00e1"
URLS={CALENDAR:"ORGANISER_OFFICIAL_EVENT_CALENDAR",MUNICIPAL:"GOV_OFFICIAL_NEWS_CORROBORATION"}
OFFICIAL_NAME="碧潭地景裝置展-遇見小王子 漫遊碧潭間"
VENUE="新北市新店區碧潭風景區"
PERIOD=("2026-10-17","2026-12-13")
MAX_HTML=3_000_000
def norm(s):return re.sub(r"[\W_]+","",str(s),flags=re.UNICODE)
def exact_url(url):
 try:
  u=urlsplit(url)
  return u.scheme=="https" and u.username is None and u.password is None and u.port is None and url in URLS
 except ValueError:return False
def vet_parent(p):
 if p.get("kind")!=PARENT or p.get("sourceRuntime")!="DORMANT" or \
    p.get("published") is not False or p.get("goldenAccepted") is not False or \
    p.get("firstPartyEventDetailsIndependentlyVerified")!=0 or \
    p.get("fieldPromotionCount")!=0 or p.get("articleSamplesCount")!=6:
  raise ValueError("HOLD_L5E1_GOVERNANCE")
 hit=[x for x in p["samples"] if x.get("aggregatorUrl")==AGG_URL]
 if len(hit)!=1:raise ValueError("HOLD_BITAN_AGGREGATOR_IDENTITY")
 row=hit[0]
 if row.get("articleIdentity")!="AGGREGATOR_ARTICLE_H1_MATCH" or \
    row.get("firstPartyVerified") is not False or row.get("originalOfficialUrl") is not None or \
    row.get("dateStart") is not None or row.get("dateEnd") is not None or \
    norm(row.get("title"))!=norm(OFFICIAL_NAME):
  raise ValueError("HOLD_BITAN_UNVERIFIED_AGGREGATOR_ARTICLE")
 if row.get("sourceSectionFound") is not True:return row
 if any(c.get("originalOfficialEventDetailVerified") is not False for c in row.get("credits",[])):
  raise ValueError("HOLD_FORGED_PARENT_ORIGIN_PROOF")
 return row
def fetch(sess,url):
 if not exact_url(url):raise ValueError("HOLD_NONALLOWLISTED_GOV_URL")
 try:
  with sess.get(url,timeout=(6,18),allow_redirects=False,stream=True,
    headers={"User-Agent":"EventRadar Taiwan P30-L5E2 read-only government source QA/1.0",
             "Accept":"text/html"}) as r:
   meta={"requestedUrl":url,"role":URLS[url],"status":r.status_code,
         "contentType":r.headers.get("content-type","")[:90]}
   if r.status_code!=200 or "text/html" not in meta["contentType"].lower():
    meta["responseState"]="HTTP_OR_TYPE_HOLD";return "",meta
   buf=bytearray()
   for v in r.iter_content(chunk_size=32768):
    buf.extend(v)
    if len(buf)>MAX_HTML:
     meta["responseState"]="OVERSIZE_HOLD";return "",meta
   if not buf:meta["responseState"]="EMPTY_HOLD";return "",meta
   meta.update(responseState="HTTP200_HTML",bytes=len(buf),
        sha256=hashlib.sha256(buf).hexdigest())
   bs=BeautifulSoup(bytes(buf),"html.parser",from_encoding="utf-8")
   for tag in bs(["script","style","noscript"]):tag.decompose()
   text=bs.get_text(" ",strip=True)
   return re.sub(r"\s+"," ",text),meta
 except requests.RequestException as e:
  return "",{"requestedUrl":url,"role":URLS[url],"responseState":"NETWORK_HOLD",
              "errorType":type(e).__name__}
def parse_calendar(text):
 # Source anchor must be the real government activity title. Do not borrow
 # dates from sidebar lists or adjacent unrelated event cards.
 idx=text.find(OFFICIAL_NAME)
 if idx<0:
  return {"identity":"OFFICIAL_TITLE_MISSING_HOLD","officialDateRole":None}
 s=text[idx:idx+1600]
 # Exact explicit Gregorian interval and official role label in the same
 # bounded official event details, not a title date or a non-Gregorian year.
 m=re.search(r"活動日期[：:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*[~～-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",s)
 interval=tuple(m.groups()) if m else None
 venueOk=("活動地點" in s and VENUE in s)
 orgOk=bool(re.search(r"主辦單位[：:\s]*觀光旅遊局",s))
 same=(interval==PERIOD)
 return {"identity":"OFFICIAL_EVENT_TITLE_BOUND" if norm(OFFICIAL_NAME) in norm(s[:130]) else "OFFICIAL_TITLE_BINDING_HOLD",
   "dateRole":"OFFICIAL_ORGANISER_EVENT_PERIOD" if same else "PERIOD_NOT_BOUND_HOLD",
   "observedPeriod":list(interval) if interval else None,
   "venueEvidence":VENUE if venueOk else None,
   "organiser":"新北市政府觀光旅遊局" if orgOk else None,
   "calendarSource":"NEW_TAIPEI_GOVERNMENT_TOURISM_EVENT_CALENDAR",
   "completeIdentity":bool(same and venueOk and orgOk)}
def parse_news(text):
 m=re.search(r"發佈日期[：:\s]*(20\d\d-\d\d-\d\d)",text)
 published=m.group(1) if m else None
 unitOk=bool(re.search(r"發佈單位[：:\s]*新北市政府觀光旅遊局",text))
 topic=all(word in text for word in ("小王子出版80周年降臨碧潭","10月17日","12月13日"))
 return {"sourceRole":"INDEPENDENT_GOVERNMENT_NEWS_CONTEXT",
   "publishedAtDate":published,"publisherVerifiedFromPage":unitOk,
   "sameEventHeadlineAndPeriodInNews":topic,
   "dateRole":"NEWS_PUBLICATION_DATE_NOT_EVENT_START",
   "sufficientAdditionalContext":bool(published=="2026-10-14" and unitOk and topic)}
def assemble(parent,calendar,news):
 source=vet_parent(parent)
 valid=calendar.get("completeIdentity") is True and news.get("sufficientAdditionalContext") is True
 return {"kind":KIND,"sourceAggregatorUrl":AGG_URL,"sourceAggregatorTitle":source["title"],
   "sourceRole":"THIRD_PARTY_EVENT_AGGREGATOR","primaryCalendarUrl":CALENDAR,
   "independentMunicipalNewsUrl":MUNICIPAL,
   "officialEventSourceMatchState":"FIRST_PARTY_ORGANISER_EVENT_IDENTITY_CORROBORATED_REVIEW_ONLY" if valid else
       "HOLD_FIRST_PARTY_GOV_SOURCE_INCOMPLETE",
   "primaryOfficialCalendar":calendar,"secondaryGovernmentNews":news,
   "reviewOnlyOfficialEventUrl":CALENDAR if valid else None,
   "reviewOnlyOfficialEventPeriod":list(PERIOD) if valid else None,
   "officialFirstPartyIndependentEventIdentityCount":1 if valid else 0,
   "strolltimesOriginalFacebookCreditsUnverified":True,
   "allOtherAggregatorArticlesVerified":False,"noChangeNoticeProven":False,
   "finalDatePromotionCount":0,"dateStart":None,"dateEnd":None,
   "ticketStatus":"UNKNOWN","price":None,"goldenAccepted":False,
   "published":False,"writerExecuted":False,"notifierExecuted":False,
   "sourceRuntime":"DORMANT","autoHidden":0,"original44AndroidPreserved":True}
def run(inp,out):
 dst=Path(out).resolve();docs=Path("docs").resolve()
 if dst==docs or docs in dst.parents:raise ValueError("HOLD_PRODUCTION_WRITER")
 raw=Path(inp).read_bytes();parent=json.loads(raw);vet_parent(parent)
 with requests.Session() as ss:
  data1,net1=fetch(ss,CALENDAR);time.sleep(1.2);data2,net2=fetch(ss,MUNICIPAL)
 c=parse_calendar(data1);n=parse_news(data2)
 result=assemble(parent,c,n);result.update(
  inputEvidenceSHA256=hashlib.sha256(raw).hexdigest(),httpEvidence=[net1,net2],
  observedAtUTC=datetime.now(timezone.utc).isoformat(),
  maxPublicGET=2,noRetries=True,noLogin=True,noCheckout=True,noStealth=True,
  noCaptchaBypass=True,noUndocumentedAPI=True)
 dst.mkdir(parents=True,exist_ok=True)
 (dst/"independent_gov_event_review.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("BITAN_L5E2_HTTP",net1.get("status"),net2.get("status"))
 print("BITAN_L5E2_PRIMARY",c,"NEWS",n)
 print("BITAN_L5E2_STATE",result["officialEventSourceMatchState"])
 if result["officialFirstPartyIndependentEventIdentityCount"]!=1:
  print("HOLD P30_L5E2_FIRST_PARTY_IDENTITY");raise SystemExit(2)
 print("PASS P30_L5E2_PRIMARY_GOV_CALENDAR_AND_MUNICIPAL_RELEASE_SAME_EVENT")
 print("PASS P30_L5E2_OFFICIAL_PERIOD_FIRST_PARTY_EVIDENCE_REVIEW_ONLY")
 print("HOLD P30_L5E2_SOCIAL_ACCOUNT_AUTHENTICITY_AND_DYNAMIC_EVENT_CHANGES")
 print("GOLDEN=0 APP_DATA_PUBLISHED=false")
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--parent",required=True);a.add_argument("--out-dir",required=True)
 x=a.parse_args();run(x.parent,x.out_dir)
