#!/usr/bin/env python3
"""VENUE-02H: two bounded TAINEX official GETs; exact list/detail local identity.

Distinct /event/<id> records must not collapse by common date, hall, or organizer.
All fields REVIEW only. No ticket URL/ID, raw HTML retention, or publication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from p30_venue02g_tainex_parity import local_id

LIST_URL="https://www.tainex.com.tw/event"
DETAIL_URL="https://www.tainex.com.tw/event/689"
TITLE="2026臺灣國際咖啡展"
RELEASE="HARD_HOLD_NO_PUBLICATION"
MAX_BYTES=180000

def inspect_html_pair(list_html,detail_html):
    base=dict(source="TAINEX_OFFICIAL_VENUE",decision="HOLD_INPUT",
              listExactAnchors=0,detailExactHeadings=0,
              venueLocalIdReview=None,ticketEventId=None,
              identity="UNKNOWN",acceptedFields=0,goldenAccepted=0,
              published=False,releaseState=RELEASE,
              sourceQuality="UNKNOWN")
    if not all(isinstance(x,str) and x and len(x.encode("utf-8"))<=MAX_BYTES
               for x in (list_html,detail_html)):
        return base
    ls=BeautifulSoup(list_html,"html.parser")
    ds=BeautifulSoup(detail_html,"html.parser")
    anchors=[a for a in ls.find_all("a",href=True)
             if urljoin(LIST_URL,a["href"])==DETAIL_URL and TITLE in " ".join(a.get_text(" ",strip=True).split())]
    base["listExactAnchors"]=len(anchors)
    if len(anchors)!=1:
        return dict(base,decision="HOLD_LIST_ANCHOR_NOT_UNIQUE")
    heads=[h for h in ds.find_all(["h1","h2"])
           if " ".join(h.get_text(" ",strip=True).split())==TITLE]
    base["detailExactHeadings"]=len(heads)
    if len(heads)!=1:
        return dict(base,decision="HOLD_DETAIL_TITLE_NOT_UNIQUE")
    local=local_id(DETAIL_URL)
    if local is None:
        return dict(base,decision="HOLD_LOCAL_SOURCE_ID")
    base["venueLocalIdReview"]=local
    base["identity"]="REVIEW_SAME_ORIGIN_PATH_AND_EXACT_TITLE"
    text=" ".join(ds.get_text(" ",strip=True).split())
    base["roleLabelPresence"]={
        "exhibitionPeriod": "展覽活動期間" in text,
        "venue": "活動地點" in text,
        "organizer": "主辦單位" in text,
    }
    if not all(base["roleLabelPresence"].values()):
        return dict(base,decision="HOLD_MISSING_DETAIL_ROLE_LABEL",
                    sourceQuality="REVIEW_LIST_DETAIL_IDENTITY")
    return dict(base,decision="REVIEW_LIVE_LIST_DETAIL_IDENTITY_NO_PROMOTION",
                sourceQuality="REVIEW_LIVE_TWO_HTTP_SOURCES")

def compare_distinct_records(a,b):
    """Explicit anti-collapse for two venue-local records sharing time and hall."""
    if not isinstance(a,dict) or not isinstance(b,dict):
        return "HOLD_INPUT"
    ids=[local_id(x.get("url")) for x in (a,b)]
    if any(x is None for x in ids):
        return "HOLD_SOURCE_URL"
    if ids[0]==ids[1]:
        return "HOLD_SAME_VENUE_LOCAL_ID"
    return "REVIEW_DISTINCT_VENUE_LOCAL_IDS_NO_MERGE"

def bounded_get(url):
    import requests
    info=dict(urlRole="LIST" if url==LIST_URL else "DETAIL",
              httpStatus=None,bodyBytes=0,bodySHA256=None,
              decision="HOLD_NETWORK")
    try:
        with requests.get(url,headers={"User-Agent":"EventRadar-ReadOnly/1.0"},
                          timeout=(6,12),allow_redirects=False,stream=True) as resp:
            info["httpStatus"]=resp.status_code
            if resp.status_code!=200:
                return info,None
            if resp.headers.get("Content-Type","").split(";")[0].lower() not in ("text/html","application/xhtml+xml"):
                return dict(info,decision="HOLD_CONTENT_TYPE"),None
            parts,size=[],0
            for chunk in resp.iter_content(32768):
                size+=len(chunk)
                if size>MAX_BYTES:
                    return dict(info,decision="HOLD_BODY_CAP",bodyBytes=size),None
                parts.append(chunk)
            raw=b"".join(parts)
            info.update(bodyBytes=len(raw),bodySHA256=hashlib.sha256(raw).hexdigest(),
                        decision="REVIEW_HTTP_200_HTML")
            return info,raw.decode(resp.encoding or "utf-8",errors="replace")
    except Exception as exc:
        return dict(info,networkErrorClass=type(exc).__name__),None

def fetch_two():
    out=dict(observedAtUTC=datetime.now(timezone.utc).isoformat(),
             requestBudget=2,requestCount=0,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=RELEASE,
             decision="HOLD_NETWORK",sourceQuality="HOLD_NETWORK")
    receipts=[]
    docs=[]
    for url in (LIST_URL,DETAIL_URL):
        receipt,html=bounded_get(url)
        receipts.append(receipt)
        docs.append(html)
        out["requestCount"]+=1
        if html is None:
            break
    out["receipts"]=receipts
    if len(docs)==2 and all(x is not None for x in docs):
        out.update(inspect_html_pair(*docs))
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-two",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_two:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(fetch_two(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
