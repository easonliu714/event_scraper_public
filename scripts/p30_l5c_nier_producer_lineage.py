#!/usr/bin/env python3
"""P30-L5-C: independent NieR producer itinerary vs ibon two-session evidence.

Public producer schedule is not an official timestamped 'added show' press notice.
A ticket resale/aggregator listing is not a ticket seller/organiser authority.
A mismatch in *sales opening* must NEVER be called a show-time difference.
Read-only: no login, checkout, retries, production writer, notification or auto-hide.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

KIND="EVENTRADAR_P30_L5C_NIER_PRODUCER_CROSS_SOURCE_REVIEW_ONLY"
PARENT_KIND="EVENTRADAR_P30_L5B_IBON_CHANGE_NOTICE_CROSSCHECK_NOT_GOLDEN"
SCHEDULE_URL="https://www.nierconcert.com/12026"
ADDED_DETAIL_URL="https://www.nierconcert.com/12026/taipei-2"
SECONDARY_URL="https://itix2go.com/guest/program/detail/ncrp0"
# The 3 public pages have distinct provenance; do not treat itix2go as organiser.
KNOWN={SCHEDULE_URL:"PRODUCER_TOUR_LIST",
       ADDED_DETAIL_URL:"PRODUCER_EVENT_DETAIL",
       SECONDARY_URL:"THIRD_PARTY_TICKET_RESALE_LISTING"}
EXPECTED={
  "2027-02-20T18:00":"Saturday, February 20, 2027",
  "2027-02-21T14:00":"Sunday, February 21, 2027"
}
EVENT_TITLE="NieR:Orchestra Concert 12026"
VENUE="Taipei International Convention Center"
MAX_BYTES=2_500_000
USER_AGENT="EventRadar Taiwan P30-L5C official-producer-crosscheck/1.0"
TIME_SIGNALS=(
 ("SATURDAY_20","Saturday, February 20, 2027","6:00 PM","2027-02-20T18:00"),
 ("SUNDAY_21","Sunday, February 21, 2027","2:00 PM","2027-02-21T14:00")
)

def clean(s):
    return re.sub(r"\s+"," ",s).strip()

def allow_url(url):
    return url in KNOWN and urlsplit(url).scheme=="https"

def fetch_html(session,url):
    if not allow_url(url):
        raise ValueError("HOLD_NON_ALLOWLISTED_SOURCE")
    try:
        with session.get(url,timeout=(6,16),allow_redirects=False,stream=True,
                         headers={"User-Agent":USER_AGENT,"Accept":"text/html"}) as res:
            result={"sourceUrl":url,"sourceRole":KNOWN[url],
                    "status":res.status_code,
                    "contentType":res.headers.get("content-type","")[:110],
                    "httpState":"HTTP_ERROR"}
            if res.status_code!=200:
                return None,result
            if "text/html" not in result["contentType"].lower():
                result["httpState"]="NON_HTML_HOLD"
                return None,result
            data=bytearray()
            for part in res.iter_content(chunk_size=32768):
                data.extend(part)
                if len(data)>MAX_BYTES:
                    result["httpState"]="SIZE_LIMIT_HOLD"
                    return None,result
            if not data:
                result["httpState"]="EMPTY_HTML_HOLD"
                return None,result
            result.update(httpState="HTTP200_HTML",bytes=len(data),
                          sha256=hashlib.sha256(data).hexdigest())
            html=bytes(data).decode(res.encoding or "utf-8",errors="replace")
            return BeautifulSoup(html,"html.parser"),result
    except requests.RequestException as ex:
        return None,{"sourceUrl":url,"sourceRole":KNOWN[url],
                     "httpState":"NETWORK_HOLD","exceptionType":type(ex).__name__}

def text_source(soup):
    if soup is None:return ""
    for tag in soup(["script","style","noscript"]):tag.decompose()
    return clean(soup.get_text(" ",strip=True))

def contains_date_time_near_taipei(text,day,time_text):
    """Same card, tightly scoped. A Bangkok date and Taipei venue is NOT Taipei."""
    s=clean(text)
    indices=[x.start() for x in re.finditer(r"Taipei,\s*Taiwan",s,re.I)]
    for idx in indices:
        # Must occur after Taipei marker before another city's event.
        block=s[idx:idx+290]
        found=re.search(re.escape(day)+r"\s+"+re.escape(time_text),block,re.I)
        if found and VENUE in block[found.end():found.end()+150]:
            return {"city":"Taipei, Taiwan","sourceDateText":day,
                    "sourceStartText":time_text,"venue":VENUE,
                    "eventStartLocal":next(x[3] for x in TIME_SIGNALS if x[1]==day),
                    "identity":"CITY_DAY_TIME_VENUE_BOUND"}
    return None

def producer_schedule(text):
    records={}
    for _,day,clock,iso in TIME_SIGNALS:
        evidence=contains_date_time_near_taipei(text,day,clock)
        if evidence:records[iso]=evidence
    return records

def producer_added_event(text):
    t=clean(text)
    ok=all(x in t for x in ("Taipei, Taiwan","Sunday, February 21, 2027",
                              "2:00 PM",VENUE,"NieR:Orchestra Concert 12026"))
    add_sale=re.search(r"On Sale\s+Oct\.?\s*21,\s*9\s*AM\s*\(?UTC\+8\)?",t,re.I)
    return {"detailIdentity":"ADDED_TAIPEI_EVENT_DETAIL_MATCH" if ok else
            "DETAIL_IDENTITY_INCOMPLETE_HOLD",
            "eventStartLocal":"2027-02-21T14:00" if ok else None,
            "producerAddedShowSaleTime":"2026-10-21T09:00+08:00" if add_sale else None,
            "saleEvidenceRole":"PRODUCER_EVENT_PAGE_SALE_BANNER" if add_sale else "NOT_CAPTURED",
            "announcementPublishedAt":None,
            "announcementPublishTimeVerified":False}

def secondary_sale(text):
    """A ticket RESALE LISTING never becomes a primary sale-opening source."""
    t=clean(text)
    add=bool(re.search(
        r"加場售票時間\s*[⎪|｜:：]?\s*2026\s*[/.-]\s*10\s*[/.-]\s*21"
        r".{0,12}?(?:12:00|12：00)",t))
    return {"sourceRole":"THIRD_PARTY_TICKET_RESALE_LISTING",
            "addedShowSaleTime":"2026-10-21T12:00" if add else None,
            "publisherTimestamp":None,"publisherTimestampVerified":False,
            "notOriginalOrganiser":True}

def vet_parent(parent):
    if parent.get("kind")!=PARENT_KIND or parent.get("sourceCount")!=2 or \
       len(parent.get("details",[]))!=2 or parent.get("published") is not False or \
       parent.get("goldenAccepted") is not False or parent.get("sourceRuntime")!="DORMANT" or \
       parent.get("organiserConfirmationCount")!=0 or parent.get("formalDatePromotionCount")!=0:
        raise ValueError("HOLD_PARENT_GOVERNANCE")
    rows=parent["details"]
    nier=[x for x in rows if "NieR" in x.get("listTitle","")]
    if len(nier)!=1:raise ValueError("HOLD_NIER_IDENTITY_NOT_UNIQUE")
    row=nier[0]
    if row.get("officialUrl")!="https://ticket.ibon.com.tw/ActivityInfo/Details/39974":
        raise ValueError("HOLD_NOT_PINNED_NIER_OFFICIAL_URL")
    if row.get("httpStatus")!=200 or row.get("scheduleParity")!="EXACT_SAMPLED_EVENT_STARTS":
        raise ValueError("HOLD_NIER_BASE_SCHEDULE_NOT_ACCEPTED")
    if sorted(row.get("currentSampleEventStarts",[]))!=sorted(EXPECTED):
        raise ValueError("HOLD_PARENT_NIER_TWO_EVENT_TIMES_MISMATCH")
    if row.get("organiserChangeApproval")!="NOT_VERIFIED" or row.get("notice",{}).get("isNoChangesProven") is not False:
        raise ValueError("HOLD_PRIOR_NOTICE_NOT_FAIL_CLOSED")
    return row

def reconcile(parent, schedule, producer_detail, secondary):
    row=vet_parent(parent)
    expected=sorted(row["currentSampleEventStarts"])
    observed=sorted(schedule)
    parity=observed==expected and producer_detail.get("detailIdentity")=="ADDED_TAIPEI_EVENT_DETAIL_MATCH"
    producerSale=producer_detail.get("producerAddedShowSaleTime")
    secondarySale=secondary.get("addedShowSaleTime")
    # Resale listing shows 12:00 and producer page displays 09:00 UTC+8.
    # Treat as source disagreement, NOT as a proven change of official sale time.
    sale_conflict=bool(producerSale and secondarySale and
            producerSale[:16]!=secondarySale[:16])
    if not parity:
        status="HOLD_PRODUCER_SCHEDULE_PARITY_OR_DETAIL_IDENTITY"
    else:
        status="PRODUCER_TWO_TAIPEI_SESSIONS_CORROBORATED_REVIEW_ONLY"
    return {"kind":KIND,"status":status,"event":"NieR:Orchestra Concert 12026 [YoRHa]",
            "officialOriginalTicketUrl":row["officialUrl"],
            "producerSourceUrl":SCHEDULE_URL,"producerDetailUrl":ADDED_DETAIL_URL,
            "producerRole":"AWR_MUSIC_SQUARE_ENIX_ORIGINAL_PRODUCTION",
            "originalVendorRole":"IBON_AUTHORISED_TICKET_PLATFORM",
            "producerSessionCount":len(schedule),
            "producerSessionEvidence":[schedule[k] for k in sorted(schedule)],
            "originalOfficialStarts":expected,
            "producerOriginalTwoStartsSame":parity,
            "addedShowSource":"PRODUCER_OFFICIAL_EVENT_LISTING_2027_02_21",
            "originalAdditionalShowAnnouncementUrl":None,
            "announcementPublicationTimestamp":None,
            "announcementTimestampVerified":False,
            "addedShowPubliclyListedByProducer":parity,
            "additionalShowAnnouncementIndependentlyVerified":False,
            "ticketSaleEvidence":{"producer":producerSale,"secondary":secondarySale,
                "secondaryRole":secondary.get("sourceRole"),
                "saleTimeConflict":"SECONDARY_DISAGREEMENT_HOLD" if sale_conflict else
                  "NO_COMPARABLE_SALE_TIMES_OBSERVED",
                "salesTimeOfficiallyApproved":False},
            "ticketAvailability":"UNKNOWN",
            "organiserConfirmationStatus":"OFFICIAL_TOUR_SCHEDULE_CORROBORATED_ANNOUNCEMENT_TIMESTAMP_HOLD",
            "reviewOnly":True,"organiserChangeApproval":"NOT_VERIFIED",
            "dateStart":None,"dateEnd":None,"sourceTimeZoneBackfillCount":0,
            "ticketStatus":"UNKNOWN","price":None,
            "acceptedEventCount":0,"formalFieldPromotionCount":0,
            "goldenAccepted":False,"published":False,"writerExecuted":False,
            "notifierExecuted":False,"autoHidden":0,"sourceRuntime":"DORMANT",
            "originalAndroid44Preserved":True}

def run(parent_path,out_dir,sleep=time.sleep):
    destination=Path(out_dir).resolve()
    docs=Path("docs").resolve()
    if destination==docs or docs in destination.parents:
        raise ValueError("HOLD_PRODUCTION_PAGES_WRITER")
    raw=Path(parent_path).read_bytes()
    parent=json.loads(raw)
    vet_parent(parent)
    responses={}
    with requests.Session() as session:
        for idx,url in enumerate(KNOWN):
            if idx:sleep(1.2)
            soup,net=fetch_html(session,url)
            responses[url]={"net":net,"text":text_source(soup)}
    tour=producer_schedule(responses[SCHEDULE_URL]["text"])
    detail=producer_added_event(responses[ADDED_DETAIL_URL]["text"])
    secondary=secondary_sale(responses[SECONDARY_URL]["text"])
    result=reconcile(parent,tour,detail,secondary)
    result["observedAtUTC"]=datetime.now(timezone.utc).isoformat()
    result["inputParentSHA256"]=hashlib.sha256(raw).hexdigest()
    result["httpEvidence"]=[responses[u]["net"] for u in KNOWN]
    result["maxSourceGET"]=3;result["noRetries"]=True
    result["noLogin"]=True;result["noCheckout"]=True
    result["noCaptchaBypass"]=True;result["noUndocumentedAPI"]=True
    destination.mkdir(parents=True,exist_ok=True)
    (destination/"cross_source_review.json").write_text(
       json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("NIER_L5C_PRODUCER_TOUR",responses[SCHEDULE_URL]["net"].get("status"),
          "SESSIONS",len(tour),sorted(tour))
    print("NIER_L5C_PRODUCER_DETAIL",responses[ADDED_DETAIL_URL]["net"].get("status"),
          detail["detailIdentity"])
    print("NIER_L5C_SECONDARY_SALES",responses[SECONDARY_URL]["net"].get("status"),
          result["ticketSaleEvidence"]["saleTimeConflict"])
    print("NIER_L5C_STATUS",result["status"],
          "ANNOUNCEMENT_TIMESTAMP_VERIFIED",result["announcementTimestampVerified"])
    if result["status"]!="PRODUCER_TWO_TAIPEI_SESSIONS_CORROBORATED_REVIEW_ONLY":
        print("HOLD P30_L5C_PRIMARY_PRODUCER_SOURCE_PARITY")
        raise SystemExit(2)
    print("PASS P30_L5C_INDEPENDENT_OFFICIAL_TOUR_TWO_TAIPEI_SESSIONS_ONLY")
    print("HOLD P30_L5C_ANNOUNCEMENT_PUBLICATION_TIMESTAMP_AND_SECONDARY_SALE_TIME")
    print("GOLDEN=0 FORMAL_FIELD_PROMOTION=0")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--parent",required=True)
    parser.add_argument("--out-dir",required=True)
    args=parser.parse_args()
    run(args.parent,args.out_dir)
