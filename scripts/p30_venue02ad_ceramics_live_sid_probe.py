#!/usr/bin/env python3
"""P30-VENUE-02AD: one bounded official Ceramics SID detail GET.

Corrects cross-SID fixture provenance; no event identity inferred from a
title alone, no ticket Event ID, no Golden, no formal field publication.
Never retain raw HTML in audit artifacts.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from p30_venue02ac_ceramics_sid_title import audit_sid_title

SID="0Q218338899799849722"
TITLE="山彩疊疊-唐榕個展"
URL="https://www.ceramics.ntpc.gov.tw/xmdoc/cont?sid="+SID+"&xsmsid=0J148497613881029302"
HOLD="HARD_HOLD_NO_PUBLICATION"

def inspect_detail(html, detail_url=URL):
    prior=audit_sid_title(detail_url,html,SID,TITLE)
    out={"gate":"P30-VENUE-02AD","source":"CERAMICS_P0_NEW_TAIPEI",
         "sourceRole":"OFFICIAL_VENUE","selectedSID":SID,
         "sidBound":prior["sidBound"],"headingMatches":prior["detailHeadingMatches"],
         "fieldRoleDecision":prior["fieldRoleDecision"],
         "predecessorDecision":prior["decision"],
         "acceptedFields":0,"goldenAccepted":0,"published":False,
         "ticketEventId":None,"releaseState":HOLD}
    if prior["decision"] != "REVIEW_SAME_SID_TITLE_FIELD_ROLES_NOT_ACCEPTED":
        return dict(out,decision="HOLD_SOURCE_IDENTITY_OR_FIELD_ROLE")
    return dict(out,decision="REVIEW_EXACT_SID_TITLE_FIELD_CANDIDATES_NOT_ACCEPTED")

def live_one():
    out={"gate":"P30-VENUE-02AD","mode":"ONE_NORMAL_OFFICIAL_DETAIL_GET",
         "source":"CERAMICS_P0_NEW_TAIPEI","requestBudget":1,"requestCount":1,
         "officialGET":1,"observedAtUTC":datetime.now(timezone.utc).isoformat(),
         "sourceQualityFromLive":False,"acceptedFields":0,"goldenAccepted":0,
         "published":False,"releaseState":HOLD}
    try:
        import requests
        with requests.get(URL,headers={"User-Agent":"EventRadarSourceAudit/1.0 (+https://github.com/easonliu714/event_scraper_public)",
             "Accept":"text/html"},timeout=(5,12),allow_redirects=False,stream=True) as response:
            out["httpStatus"]=response.status_code
            if response.status_code != 200:
                return dict(out,decision="HOLD_HTTP_NOT_200")
            if "html" not in response.headers.get("Content-Type","").lower():
                return dict(out,decision="HOLD_NON_HTML_RESPONSE")
            chunks,size=[],0
            for part in response.iter_content(chunk_size=16384):
                size+=len(part)
                if size>1500000:
                    return dict(out,decision="HOLD_BODY_SIZE_LIMIT")
                chunks.append(part)
            body=b"".join(chunks)
        out["bodyByteCount"]=len(body)
        out["bodySHA256"]=hashlib.sha256(body).hexdigest()
        out["sourceQualityFromLive"]=True
        return dict(out,**inspect_detail(body.decode("utf-8",errors="replace")))
    except Exception as exc:
        out["errorType"]=type(exc).__name__
        return dict(out,decision="HOLD_SAFE_HTTP_OR_PARSE_FAILURE")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(live_one(),sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
