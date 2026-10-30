#!/usr/bin/env python3
"""VENUE-02Q: classify one source-derived Xinzhuang 302 Location; NEVER follow redirects."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime,timezone
from urllib.parse import urljoin,urlsplit,parse_qsl
import requests
from p30_venue02m_xinzhuang_discovery import HOLD,get_one
from p30_venue02o_xinzhuang_submenu_role import CANDIDATE_URL
from p30_venue02p_xinzhuang_detail_parity import select_candidate

def classify_location(location,source_url):
    if not location: return dict(locationClass="MISSING_LOCATION")
    try:
        p=urlsplit(urljoin(source_url,location))
        s=urlsplit(source_url)
        if p.scheme!="https": c="NON_HTTPS_SCHEME"
        elif p.username is not None or p.password is not None: c="USERINFO_PRESENT"
        elif p.port not in (None,443): c="NONDEFAULT_PORT"
        elif p.hostname!=s.hostname: c="EXTERNAL_HOST"
        elif p.geturl()==source_url: c="SELF_REDIRECT"
        elif not p.path or p.path=="/": c="NON_DETAIL_TARGET"
        else: c="HTTPS_SAME_ORIGIN_UNFOLLOWED"
        return dict(locationClass=c,locationPathClass=("DETAIL_PATH" if "/xmdoc/" in p.path else "OTHER_PATH"),
                    locationQueryKeys=sorted({k for k,_ in parse_qsl(p.query)})[:15],
                    locationSHA256=hashlib.sha256(p.geturl().encode()).hexdigest())
    except ValueError: return dict(locationClass="MALFORMED_LOCATION")

def inspect_response(status,location,source_url):
    if status not in (301,302,303,307,308):
        return dict(decision="HOLD_NOT_REDIRECT",detailHTTPStatus=status)
    x=classify_location(location,source_url)
    x["detailHTTPStatus"]=status
    x["decision"]=("REVIEW_SAME_ORIGIN_REDIRECT_UNFOLLOWED_NO_IDENTITY"
                   if x["locationClass"]=="HTTPS_SAME_ORIGIN_UNFOLLOWED"
                   else "HOLD_UNSAFE_OR_MISSING_REDIRECT_TARGET")
    return x

def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-VENUE-02Q",source="XINZHUANG_ARTS_CENTER_VENUE",
             observed_at=observed,requestBudget=2,requestCount=1,
             acceptedFields=0,goldenAccepted=0,published=False,
             releaseState=HOLD,ticketEventId=None,
             sourceQuality="SOURCE_DERIVED_REDIRECT_LOCATION_CLASSIFICATION")
    receipt,index=get_one(CANDIDATE_URL)
    out["indexReceipt"]=receipt
    if index is None: return dict(out,decision="HOLD_INDEX_HTTP_OR_BODY")
    selected,meta=select_candidate(index)
    out.update(meta)
    if not selected: return out
    url,_=selected
    out["requestCount"]=2
    try:
        with requests.get(url,headers={"User-Agent":"EventRadar-SourceQuality/1.0 (read-only)"},
                          timeout=(6,12),allow_redirects=False,stream=True) as response:
            out["detailReceipt"]=dict(status=response.status_code,bytes=0)
            out.update(inspect_response(response.status_code,response.headers.get("Location"),url))
    except requests.RequestException as e:
        out["detailReceipt"]=dict(status="NETWORK_HOLD",errorClass=type(e).__name__)
        out["decision"]="HOLD_DETAIL_NETWORK"
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
