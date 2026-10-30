#!/usr/bin/env python3
"""P30-VENUE-02J: Zepp New Taipei first-party list/detail source review only."""
from __future__ import annotations
import argparse,hashlib,json,unicodedata
from datetime import datetime,timezone
from urllib.parse import urljoin,urlsplit,parse_qs
from bs4 import BeautifulSoup

LIST="https://www.zepp.co.jp/hall/newtaipei/schedule/"
DETAIL="https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=162473"
RID="162473"
HOLD="HARD_HOLD_NO_PUBLICATION"
CAP=220000

def norm(s):
    return " ".join(unicodedata.normalize("NFKC",str(s)).split())

def inspect(list_html,detail_html,observed):
    out=dict(source="ZEPP_NEW_TAIPEI_OFFICIAL_VENUE",listURL=LIST,detailURL=DETAIL,
             observedAtUTC=observed,venueLocalIdReview=None,decision="HOLD_INPUT",
             roleDecisions={},ticketEventId=None,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD)
    if not list_html or not detail_html or len(list_html.encode())>CAP or len(detail_html.encode())>CAP:
        return out
    soup=BeautifulSoup(list_html,"html.parser")
    hits=[]
    for a in soup.find_all("a",href=True):
        u=urljoin(LIST,a["href"]);p=urlsplit(u)
        if p.scheme=="https" and p.netloc=="www.zepp.co.jp" and p.path=="/hall/newtaipei/schedule/single/" and parse_qs(p.query).get("rid")==[RID]:
            hits.append((u,norm(a.get_text(" ",strip=True))))
    out["listExactRidLinks"]=len(hits)
    if len(hits)!=1 or hits[0][0]!=DETAIL or "40 Fingers" not in hits[0][1]:
        return dict(out,decision="HOLD_LIST_RID_OR_TITLE")
    d=BeautifulSoup(detail_html,"html.parser")
    h=[x for x in d.find_all(["h2","h3"]) if norm(x.get_text(" ",strip=True))=="40 Fingers"]
    if len(h)!=1:
        return dict(out,decision="HOLD_DETAIL_ARTIST_NOT_UNIQUE")
    text=norm(d.get_text(" ",strip=True))
    if "[START]" not in text or "19:30" not in text:
        return dict(out,decision="HOLD_START_ROLE_UNVERIFIED")
    out["venueLocalIdReview"]=RID
    out["roleDecisions"]={
        "START":"REVIEW_LOCAL_VENUE_START_NOT_TICKET_SALE",
        "PRICE":"HOLD_EMPTY_OR_UNSCOPED_PRICE",
        "TICKET":"VENUE_CLAIMED_KKTIX_NOT_VERIFIED_TICKET_EVENT_ID",
        "SESSION":"REVIEW_ONE_VENUE_DAY_NOT_ACCEPTED_SESSION"
    }
    return dict(out,decision="REVIEW_ZEPP_SAME_RID_LIST_DETAIL_NO_FIELDS")

def get_one(url):
    import requests
    receipt=dict(url=url,httpStatus=None,bodyBytes=0,bodySHA256=None,decision="HOLD_NETWORK")
    try:
        with requests.get(url,headers={"User-Agent":"EventRadar-ReadOnly/1.0"},timeout=(6,12),allow_redirects=False,stream=True) as r:
            receipt["httpStatus"]=r.status_code
            if r.status_code!=200:return receipt,None
            if r.headers.get("Content-Type","").split(";")[0].lower() not in ("text/html","application/xhtml+xml"):
                receipt["decision"]="HOLD_CONTENT_TYPE";return receipt,None
            chunks=[];size=0
            for chunk in r.iter_content(32768):
                size+=len(chunk)
                if size>CAP:
                    receipt.update(decision="HOLD_BODY_CAP",bodyBytes=size);return receipt,None
                chunks.append(chunk)
            raw=b"".join(chunks)
            receipt.update(decision="REVIEW_HTML_READ",bodyBytes=len(raw),bodySHA256=hashlib.sha256(raw).hexdigest())
            return receipt,raw.decode(r.encoding or "utf-8",errors="replace")
    except Exception as exc:receipt["networkErrorClass"]=type(exc).__name__
    return receipt,None

def live():
    stamp=datetime.now(timezone.utc).isoformat()
    out=dict(observedAtUTC=stamp,requestBudget=2,requestCount=0,
             acceptedFields=0,goldenAccepted=0,published=False,releaseState=HOLD)
    r,listing=get_one(LIST);out["requestCount"]+=1;out["listReceipt"]=r
    if listing is None:return dict(out,decision="HOLD_OFFICIAL_LIST_UNAVAILABLE")
    r,detail=get_one(DETAIL);out["requestCount"]+=1;out["detailReceipt"]=r
    if detail is None:return dict(out,decision="HOLD_OFFICIAL_DETAIL_UNAVAILABLE")
    out.update(inspect(listing,detail,stamp))
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--live-one",action="store_true");p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
