#!/usr/bin/env python3
"""VENUE-02AE: bounded leaf-text root cause for the exact official Ceramics SID.
Diagnostic only; no field promotion or raw HTML persistence.
"""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from bs4 import BeautifulSoup
from p30_venue02ad_ceramics_live_sid_probe import URL, TITLE, HOLD, inspect_detail
from p30_venue02z_ceramics_fields import DATE, VENUE, norm

def diagnose(html):
    prior=inspect_detail(html)
    out={"gate":"P30-VENUE-02AE","source":"CERAMICS_P0_NEW_TAIPEI",
         "selectedSIDBound":prior["sidBound"],"headingMatches":prior["headingMatches"],
         "priorDecision":prior["decision"],"priorFieldRoleDecision":prior["fieldRoleDecision"],
         "dateRoleTextNodes":0,"venueRoleTextNodes":0,"inlineBothRoleNodes":0,
         "dateRegexMissNodes":0,"venueRegexMissNodes":0,"mixedSaleOrRegistrationNodes":0,
         "longRoleTextNodes":0,"roleParentTagCounts":{},"roleTextSHA256":[],
         "acceptedFields":0,"goldenAccepted":0,"published":False,
         "ticketEventId":None,"releaseState":HOLD}
    if not prior["sidBound"] or prior["headingMatches"]!=1:
        return dict(out,decision="HOLD_SID_OR_TITLE_IDENTITY")
    soup=BeautifulSoup(html,"html.parser")
    tags=Counter()
    digests=set()
    for node in soup.find_all(string=True,limit=5000):
        if node.parent.name in ("script","style","noscript","title"):
            continue
        value=norm(str(node))
        if not value or ("展覽日期" not in value and "展覽地點" not in value):
            continue
        tags[node.parent.name]+=1
        digests.add(hashlib.sha256(value.encode()).hexdigest())
        has_date="展覽日期" in value
        has_venue="展覽地點" in value
        out["dateRoleTextNodes"]+=int(has_date)
        out["venueRoleTextNodes"]+=int(has_venue)
        out["inlineBothRoleNodes"]+=int(has_date and has_venue)
        out["longRoleTextNodes"]+=int(len(value)>4000)
        out["dateRegexMissNodes"]+=int(has_date and len(DATE.findall(value))!=1)
        out["venueRegexMissNodes"]+=int(has_venue and len(VENUE.findall(value))!=1)
        out["mixedSaleOrRegistrationNodes"]+=int(any(x in value for x in ("報名日期","報名期間","售票日期","售票期間")))
    out["roleParentTagCounts"]=dict(sorted(tags.items()))
    out["roleTextSHA256"]=sorted(digests)[:12]
    if prior["fieldRoleDecision"].startswith("REVIEW_"):
        return dict(out,decision="REVIEW_SOURCE_LOCAL_ROLES_NO_FIELD_ACCEPTANCE")
    if out["mixedSaleOrRegistrationNodes"]:
        return dict(out,decision="HOLD_MIXED_ROLE_TEXT_NODE")
    if out["dateRegexMissNodes"] or out["venueRegexMissNodes"]:
        return dict(out,decision="HOLD_REGEX_OR_INLINE_NODE_OWNERSHIP")
    if out["dateRoleTextNodes"]>1 or out["venueRoleTextNodes"]>1:
        return dict(out,decision="HOLD_DUPLICATE_ROLE_NODE_OWNERSHIP")
    return dict(out,decision="HOLD_FIELD_ROLE_UNRESOLVED_NO_PROMOTION")

def live_one():
    out={"gate":"P30-VENUE-02AE","mode":"ONE_BOUNDED_OFFICIAL_ROLE_NODE_DIAGNOSTIC",
         "requestBudget":1,"requestCount":1,"officialGET":1,
         "observedAtUTC":datetime.now(timezone.utc).isoformat(),
         "sourceQualityFromLive":False,"acceptedFields":0,
         "goldenAccepted":0,"published":False,"releaseState":HOLD}
    try:
        import requests
        with requests.get(URL,headers={"User-Agent":"EventRadarSourceAudit/1.0 (+https://github.com/easonliu714/event_scraper_public)",
            "Accept":"text/html"},timeout=(5,12),allow_redirects=False,stream=True) as r:
            out["httpStatus"]=r.status_code
            if r.status_code!=200:
                return dict(out,decision="HOLD_HTTP_NOT_200")
            if "html" not in r.headers.get("Content-Type","").lower():
                return dict(out,decision="HOLD_NON_HTML")
            parts=[];size=0
            for chunk in r.iter_content(chunk_size=16384):
                size+=len(chunk)
                if size>1500000:
                    return dict(out,decision="HOLD_BODY_SIZE_LIMIT")
                parts.append(chunk)
        body=b"".join(parts)
        out["bodyByteCount"]=len(body)
        out["bodySHA256"]=hashlib.sha256(body).hexdigest()
        out["sourceQualityFromLive"]=True
        return dict(out,**diagnose(body.decode("utf-8",errors="replace")))
    except Exception as exc:
        return dict(out,errorType=type(exc).__name__,decision="HOLD_SAFE_NETWORK_OR_PARSE")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(live_one(),ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
