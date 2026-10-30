#!/usr/bin/env python3
"""P30-L9-BQ: diagnose the BP zero-anchor root cause from one bounded static GET.
No event field or ticket ID accepted; no raw HTML retained.
"""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
from p30_l9bp_huashan_live_card_probe import INDEX, ROUTE, HOLD
from p30_l9bn_huashan_card_identity import classify_href

def diagnose(html, selected=ROUTE):
    kind, target = classify_href(selected)
    out={"gate":"P30-L9-BQ","source":"HUASHAN_PLATFORM_13",
         "selectedRouteSafe":target is not None,"totalAnchors":0,
         "exhibitionHrefAnchors":0,"strictDetailAnchors":0,
         "selectedExactAnchors":0,"selectedDecodedPathAnchors":0,
         "selectedTextOccurrences":0,"hrefClassCounts":{},
         "acceptedFields":0,"goldenAccepted":0,"published":False,
         "releaseState":HOLD}
    if target is None:
        return dict(out,decision="HOLD_UNSAFE_SELECTED_ROUTE")
    soup=BeautifulSoup(html,"html.parser")
    anchors=soup.find_all("a",href=True,limit=2500)
    out["totalAnchors"]=len(anchors)
    target_path=unquote(urlsplit(target).path)
    out["selectedTextOccurrences"]=html.count(target_path)+html.count(urlsplit(target).path)
    counts=Counter()
    for a in anchors:
        href=a.get("href","")
        if "exhibition" not in href.lower():
            continue
        out["exhibitionHrefAnchors"]+=1
        route_kind, canonical=classify_href(href)
        counts[route_kind]+=1
        if canonical is not None:
            out["strictDetailAnchors"]+=1
        if canonical==target:
            out["selectedExactAnchors"]+=1
        if unquote(urlsplit(href).path)==target_path:
            out["selectedDecodedPathAnchors"]+=1
    out["hrefClassCounts"]=dict(sorted(counts.items()))
    out["selectedRouteSHA256"]=hashlib.sha256(target.encode()).hexdigest()
    if out["selectedExactAnchors"]==1:
        return dict(out,decision="REVIEW_STATIC_ANCHOR_FOUND_BUT_FIELDS_HOLD")
    if out["selectedExactAnchors"]>1:
        return dict(out,decision="HOLD_DUPLICATE_SELECTED_ANCHORS")
    if out["selectedDecodedPathAnchors"]>0:
        return dict(out,decision="HOLD_URL_CANONICALIZATION_OR_QUERY")
    if out["selectedTextOccurrences"]>0:
        return dict(out,decision="HOLD_ROUTE_IN_NON_ANCHOR_STATIC_CONTENT")
    if out["exhibitionHrefAnchors"]>0:
        return dict(out,decision="HOLD_SELECTED_ROUTE_ABSENT_FROM_INDEX_ANCHORS")
    return dict(out,decision="HOLD_NO_STATIC_EXHIBITION_ANCHORS")

def live_one():
    out={"gate":"P30-L9-BQ","mode":"ONE_BOUNDED_STATIC_ROUTE_DIAGNOSTIC",
         "requestBudget":1,"requestCount":1,"officialGET":1,
         "observedAtUTC":datetime.now(timezone.utc).isoformat(),
         "sourceQualityFromLive":False,"acceptedFields":0,
         "goldenAccepted":0,"published":False,"releaseState":HOLD}
    try:
        import requests
        with requests.get(INDEX,headers={
            "User-Agent":"EventRadarSourceAudit/1.0 (+https://github.com/easonliu714/event_scraper_public)",
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
