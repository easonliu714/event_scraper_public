#!/usr/bin/env python3
"""P30-VENUE-02Y: New Taipei Ceramics exhibition vs application role; NO PUBLISH."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, parse_qs
import requests
from bs4 import BeautifulSoup

HOME = "https://www.ceramics.ntpc.gov.tw/xmdoc?XsmSId=0J148497613881029302"
HOST = "www.ceramics.ntpc.gov.tw"
XSM = "0J148497613881029302"
HOLD = "HARD_HOLD_NO_PUBLICATION"

def norm(s):
    return " ".join(str(s).split())

def safe_detail(raw):
    if not raw or raw.startswith("//"):
        return None
    p = urlsplit(urljoin(HOME,raw))
    q = parse_qs(p.query,keep_blank_values=True)
    if p.scheme!="https" or p.hostname!=HOST or p.username or p.password or p.port or p.fragment or p.path!="/xmdoc/cont":
        return None
    if set(q)!={"sid","xsmsid"} or q["xsmsid"]!=[XSM] or len(q["sid"])!=1 or not re.fullmatch(r"0[0-9A-Za-z]{19}",q["sid"][0]):
        return None
    return p.geturl()

def index_edges(html):
    soup=BeautifulSoup(html,"html.parser")
    edges={}
    conflict=0
    for a in soup.find_all("a",href=True,limit=1200):
        url=safe_detail(a["href"])
        if not url:
            continue
        title=norm(a.get_text(" ",strip=True))
        if not title:
            imgs=a.find_all("img",alt=True,limit=3)
            title=norm(imgs[0]["alt"]) if len(imgs)==1 else ""
        title=re.sub(r"^標題[：:]\s*","",title)
        if not 3<=len(title)<=160:
            continue
        role="REGISTRATION" if any(w in title for w in ("申請","徵件簡章","報名")) else "EXHIBITION_CANDIDATE"
        if url in edges and edges[url]!=(title,role):
            conflict+=1
        edges.setdefault(url,(title,role))
    return [(url,*v) for url,v in list(edges.items())[:40]],conflict

def inspect(index_html,detail_html):
    edges,conflict=index_edges(index_html)
    eligible=[(url,title) for url,title,role in edges if role=="EXHIBITION_CANDIDATE"]
    result={"sourceDerivedDetailEdges":len(edges),"registrationExcludedCount":len(edges)-len(eligible),
            "exactTitleMatches":0,"detailExhibitionDateRoleCount":0,
            "detailRegistrationRoleCount":0,"acceptedFields":0,"ticketEventId":None}
    if conflict or not eligible:
        return dict(result,decision="HOLD_ZERO_OR_CONFLICTING_EXHIBITION_EDGES")
    _,title=eligible[0]
    soup=BeautifulSoup(detail_html,"html.parser")
    headings=[norm(h.get_text(" ",strip=True)) for h in soup.find_all(["h1","h2","h3","h4"],limit=100)]
    result["exactTitleMatches"]=headings.count(title)
    txt=norm(soup.get_text(" ",strip=True))
    result["detailExhibitionDateRoleCount"]=len(re.findall(r"展覽日期\s*[：:]",txt))
    result["detailRegistrationRoleCount"]=len(re.findall(r"報名期間\s*[：:]",txt))
    if result["exactTitleMatches"]!=1:
        return dict(result,decision="HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    if result["detailRegistrationRoleCount"] or result["detailExhibitionDateRoleCount"]>1:
        return dict(result,decision="HOLD_DATE_ROLE_MIXED_OR_AMBIGUOUS")
    return dict(result,decision="REVIEW_EXHIBITION_IDENTITY_ROLE_NO_FIELDS")

def get_one(url):
    receipt={"urlSHA256":hashlib.sha256(url.encode()).hexdigest(),"httpStatus":None,"bodyBytes":0}
    try:
        r=requests.get(url,timeout=15,allow_redirects=False,headers={"User-Agent":"EventRadar-SourceQuality/1.0"})
        receipt["httpStatus"]=r.status_code
        receipt["bodyBytes"]=len(r.content)
        if r.status_code!=200 or len(r.content)>1500000 or "text/html" not in r.headers.get("Content-Type","").lower():
            return receipt,None
        return receipt,r.text
    except requests.RequestException as e:
        receipt["errorType"]=type(e).__name__
        return receipt,None

def live():
    audit={"gate":"P30-VENUE-02Y","source":"CERAMICS_P0_NEW_TAIPEI",
           "observed_at":datetime.now(timezone.utc).isoformat(),
           "requestBudget":2,"requestCount":1,"acceptedFields":0,
           "goldenAccepted":0,"published":False,"releaseState":HOLD}
    receipt,index=get_one(HOME)
    audit["indexReceipt"]=receipt
    if index is None:
        return dict(audit,decision="HOLD_INDEX_HTTP_OR_BODY")
    edges,conflict=index_edges(index)
    eligible=[(url,title) for url,title,role in edges if role=="EXHIBITION_CANDIDATE"]
    audit.update(sourceDerivedDetailEdges=len(edges),registrationExcludedCount=len(edges)-len(eligible),titleConflicts=conflict)
    if conflict or not eligible:
        return dict(audit,decision="HOLD_ZERO_OR_CONFLICTING_EXHIBITION_EDGES")
    url,_=eligible[0]
    audit["selectedDetailURLSHA256"]=hashlib.sha256(url.encode()).hexdigest()
    audit["requestCount"]=2
    receipt,detail=get_one(url)
    audit["detailReceipt"]=receipt
    if detail is None:
        return dict(audit,decision="HOLD_DETAIL_HTTP_OR_BODY")
    audit.update(inspect(index,detail))
    return audit

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
