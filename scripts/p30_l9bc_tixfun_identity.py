#!/usr/bin/env python3
"""L9-BC: rotate to TixFun #09; bounded first-party list/detail identity, never publish."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, parse_qs
import requests
from bs4 import BeautifulSoup

HOME="https://tixfun.com/"
HOST="tixfun.com"
PRODUCT="Q01ZROKD"  # source-derived public example, not a Golden event
MARKER="灣聲映像館VIII"
HOLD="HARD_HOLD_NO_PUBLICATION"
CAP=512000

def safe_product(href):
    if not href or href.startswith(("#","javascript:","data:","mailto:")): return None
    try:
        u=urljoin(HOME,href)
        p=urlsplit(u)
        if (p.scheme!="https" or p.hostname!=HOST or p.username or p.password
                or p.port not in (None,443) or p.path!="/UTK0201_"): return None
        q=parse_qs(p.query,keep_blank_values=True)
        if q.get("PRODUCT_ID")!=[PRODUCT]: return None
        return u
    except ValueError: return None

def list_identity(html):
    soup=BeautifulSoup(html,"html.parser")
    matches={}
    for a in soup.find_all("a",href=True,limit=600):
        u=safe_product(a["href"])
        if not u: continue
        label=" ".join(a.get_text(" ",strip=True).split())
        if MARKER in label and len(label)<=500:
            matches.setdefault(u,set()).add(label)
    if len(matches)!=1: return None,dict(decision="HOLD_LIST_IDENTITY_ZERO_OR_MULTIPLE",listLinks=len(matches))
    url=next(iter(matches))
    if len(matches[url])>3: return None,dict(decision="HOLD_LIST_LABEL_CONFLICT",listLinks=1)
    return url,dict(decision="REVIEW_ONE_LIST_PRODUCT_LINK",listLinks=1,
                    productId=PRODUCT,sourceURLSHA256=hashlib.sha256(url.encode()).hexdigest())

def detail_identity(html):
    soup=BeautifulSoup(html,"html.parser")
    heads=[" ".join(x.get_text(" ",strip=True).split())
           for x in soup.find_all(["h1","h2","h3"],limit=80)]
    exact=sum(MARKER in x for x in heads if len(x)<=500)
    return dict(decision=("REVIEW_SAME_PRODUCT_TITLE_HEADING_NO_FIELDS" if exact==1
                          else "HOLD_DETAIL_TITLE_NOT_UNIQUE_OR_ABSENT"),
                titleHeadingMatches=exact,sourceRole="TICKET_DETAIL_IDENTITY_ONLY")

def get_one(url):
    try:
        with requests.get(url,headers={"User-Agent":"EventRadar-SourceQuality/1.0 (read-only)"},
                          timeout=(6,12),allow_redirects=False,stream=True) as response:
            status=response.status_code
            if status!=200: return dict(status=status,bytes=0),None
            chunks=[]; n=0
            for c in response.iter_content(16384):
                n+=len(c)
                if n>CAP: return dict(status=status,bytes=n,capExceeded=True),None
                chunks.append(c)
            raw=b"".join(chunks)
            return dict(status=status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),raw.decode(response.encoding or "utf-8",errors="replace")
    except requests.RequestException as e:
        return dict(status="NETWORK_HOLD",errorClass=type(e).__name__),None

def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-L9-BC",source="TIXFUN_PLATFORM_09",observed_at=observed,
             requestBudget=2,requestCount=1,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD,ticketEventId=None,sessionId=None,
             sourceQuality="SOURCE_FIRST_LIST_DETAIL_IDENTITY_REVIEW")
    receipt,html=get_one(HOME)
    out["listReceipt"]=receipt
    if html is None: return dict(out,decision="HOLD_LIST_HTTP_OR_BODY")
    url,meta=list_identity(html)
    out.update(meta)
    if not url: return out
    if safe_product(url)!=url: return dict(out,decision="HOLD_NAVIGATION_SECURITY")
    out["requestCount"]=2
    receipt,detail=get_one(url)
    out["detailReceipt"]=receipt
    if detail is None: return dict(out,decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(detail_identity(detail))
    out["provenance"]=dict(source=HOME,observed_at=observed,
                            role="SOURCE_LOCAL_PRODUCT_ID_AND_TITLE_REVIEW",
                            decision=out["decision"])
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
