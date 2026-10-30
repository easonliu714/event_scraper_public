#!/usr/bin/env python3
"""P30-L9-AV: ERA platform #08 exact public list/detail role-boundary review only."""
from __future__ import annotations
import argparse, hashlib, json, re, unicodedata
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, parse_qs
from bs4 import BeautifulSoup

HOME="https://ticket.com.tw/application/UTK01/UTK0101_.aspx"
DETAIL="https://ticket.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1GFK34F"
PRODUCT="P1GFK34F"
TITLE="『鼓聚台灣‧和響世界』 第十九次全台灣太鼓聯合公演"
HOLD="HARD_HOLD_NO_PUBLICATION"
CAP=220000

def norm(s):
    return " ".join(unicodedata.normalize("NFKC",str(s)).split())

def inspect(home, detail, observed):
    out=dict(source="ERA_TICKET_PLATFORM_08",sourceURL=HOME,detailURL=DETAIL,
             observedAtUTC=observed,productIdReview=None,decision="HOLD_INPUT",
             roleDecisions={},acceptedFields=0,goldenAccepted=0,
             published=False,ticketEventId=None,releaseState=HOLD)
    if not home or not detail or len(home.encode())>CAP or len(detail.encode())>CAP:
        return out
    hs=BeautifulSoup(home,"html.parser")
    links=[]
    for a in hs.find_all("a",href=True):
        url=urljoin(HOME,a["href"])
        p=urlsplit(url)
        if p.scheme=="https" and p.netloc.lower()=="ticket.com.tw" and p.path.lower().endswith("/utk0201_.aspx") and parse_qs(p.query).get("PRODUCT_ID")==[PRODUCT]:
            links.append((url,norm(a.get_text(" ",strip=True))))
    out["sameProductLinks"]=len(links)
    if len(links)!=1 or links[0][0]!=DETAIL or norm(TITLE) not in links[0][1]:
        return dict(out,decision="HOLD_LIST_PRODUCT_TITLE_OR_URL")
    ds=BeautifulSoup(detail,"html.parser")
    titles=[h for h in ds.find_all("h1") if norm(h.get_text(" ",strip=True))==norm(TITLE)]
    if len(titles)!=1:
        return dict(out,decision="HOLD_DETAIL_EXACT_H1")
    out["productIdReview"]=PRODUCT
    heads=[norm(h.get_text(" ",strip=True)) for h in ds.find_all(["h2","h3","h4","h5"])]
    out["sessionHeadingCount"]=heads.count("場次列表")
    out["refundHeadingCount"]=heads.count("退票方式")
    if out["sessionHeadingCount"]!=1:
        return dict(out,decision="HOLD_SESSION_SECTION_NOT_UNIQUE")
    out["roleDecisions"]={
        "EVENT_TITLE":"REVIEW_EXACT_SAME_PRODUCT_H1_NOT_GOLDEN",
        "SESSION":"REVIEW_SECTION_PRESENT_NO_ROW_VALUE_ACCEPTED",
        "REFUND":"REFUND_DEADLINE_NOT_EVENT_DATE",
        "PRICE":"TICKET_PRICE_NOT_ADMISSION_OR_SALE_TIME",
        "SALE":"ORDER_BUTTON_NOT_VERIFIED_SALE_STATE"
    }
    return dict(out,decision="REVIEW_SAME_PRODUCT_LIST_DETAIL_ROLE_BOUNDARY_NO_FIELDS")

def get_one(url):
    import requests
    receipt=dict(url=url,httpStatus=None,bodyBytes=0,bodySHA256=None,decision="HOLD_NETWORK")
    try:
        with requests.get(url,headers={"User-Agent":"EventRadar-ReadOnly/1.0"},timeout=(6,12),
                          allow_redirects=False,stream=True) as r:
            receipt["httpStatus"]=r.status_code
            if r.status_code!=200:
                return receipt,None
            if r.headers.get("Content-Type","").split(";")[0].lower() not in ("text/html","application/xhtml+xml"):
                receipt["decision"]="HOLD_CONTENT_TYPE"
                return receipt,None
            chunks=[]; size=0
            for chunk in r.iter_content(32768):
                size+=len(chunk)
                if size>CAP:
                    receipt.update(decision="HOLD_BODY_CAP",bodyBytes=size)
                    return receipt,None
                chunks.append(chunk)
            raw=b"".join(chunks)
            receipt.update(decision="REVIEW_HTML_READ",bodyBytes=len(raw),bodySHA256=hashlib.sha256(raw).hexdigest())
            return receipt,raw.decode(r.encoding or "utf-8",errors="replace")
    except Exception as exc:
        receipt["networkErrorClass"]=type(exc).__name__
    return receipt,None

def live():
    stamp=datetime.now(timezone.utc).isoformat()
    out=dict(observedAtUTC=stamp,requestBudget=2,requestCount=0,
             acceptedFields=0,goldenAccepted=0,published=False,releaseState=HOLD)
    r,home=get_one(HOME);out["requestCount"]+=1;out["listReceipt"]=r
    if home is None:
        return dict(out,decision="HOLD_OFFICIAL_LIST_UNAVAILABLE")
    r,detail=get_one(DETAIL);out["requestCount"]+=1;out["detailReceipt"]=r
    if detail is None:
        return dict(out,decision="HOLD_OFFICIAL_DETAIL_UNAVAILABLE")
    out.update(inspect(home,detail,stamp))
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--live-one",action="store_true");p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
