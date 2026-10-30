#!/usr/bin/env python3
"""VENUE-02S: one bounded official Shulin index-to-detail edge; no venue/event promotion."""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qsl
from bs4 import BeautifulSoup
from p30_venue02r_shulin_discovery import URL,safe_link,get_one,HOLD
def norm(s): return " ".join(str(s).split())
def detail_candidates(html):
    soup=BeautifulSoup(html,"html.parser");found={}
    for a in soup.find_all("a",href=True,limit=450):
        url=safe_link(a["href"])
        if url is None: continue
        p=urlsplit(url);keys={k for k,_ in parse_qsl(p.query,keep_blank_values=True)}
        if not p.path.endswith("/xmdoc/cont") or not {"sid","xsmsid"}.issubset(keys): continue
        label=norm(a.get_text(" ",strip=True))
        if not 6<=len(label)<=120 or label in ("詳細內容","詳細資訊","更多資訊","閱讀更多"): continue
        found.setdefault(url,set()).add(label)
    return [(url,next(iter(labels))) for url,labels in sorted(found.items()) if len(labels)==1]
def inspect_detail(html,label):
    soup=BeautifulSoup(html,"html.parser")
    heads=[norm(h.get_text(" ",strip=True)) for h in soup.find_all(["h1","h2","h3"],limit=80)]
    exact=sum(h==label for h in heads)
    return dict(detailHeadingMatches=exact,decision=("REVIEW_EXACT_INDEX_DETAIL_TITLE_NO_EVENT_ID" if exact==1 else "HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY"),
                acceptedFields=0,venueEventId=None,ticketEventId=None)
def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-VENUE-02S",source="SHULIN_ARTS_CENTER_VENUE",observed_at=observed,
             requestBudget=2,requestCount=1,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD,venueEventId=None,ticketEventId=None)
    receipt,html=get_one(URL);out["indexReceipt"]=receipt
    if html is None: return dict(out,decision="HOLD_INDEX_HTTP_OR_BODY")
    candidates=detail_candidates(html);out["candidateDetailLinks"]=len(candidates)
    if not candidates: return dict(out,decision="HOLD_NO_UNAMBIGUOUS_DETAIL_EDGE")
    url,label=candidates[0]
    out["selectedDetailURLSHA256"]=hashlib.sha256(url.encode()).hexdigest()
    out["indexTitleSHA256"]=hashlib.sha256(label.encode()).hexdigest()
    out["requestCount"]=2
    receipt,detail=get_one(url);out["detailReceipt"]=receipt
    if detail is None: return dict(out,decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(inspect_detail(detail,label))
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--live-one",action="store_true");p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f: json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
