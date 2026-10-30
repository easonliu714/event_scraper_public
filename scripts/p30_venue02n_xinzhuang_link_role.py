#!/usr/bin/env python3
"""P30-VENUE-02N: classify two first-party Xinzhuang candidate index link roles; NO PUBLISH."""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from p30_venue02m_xinzhuang_discovery import HOME,HOLD,POSITIVE,NEGATIVE,norm,same_origin,get_one

def inspect(html,observed):
    out=dict(gate="P30-VENUE-02N",source="XINZHUANG_ARTS_CENTER_VENUE",
             sourceURL=HOME,observed_at=observed,role="FIRST_PARTY_INDEX_LINK_DIAGNOSTIC",
             acceptedFields=0,goldenAccepted=0,published=False,ticketEventId=None,
             releaseState=HOLD,sourceQuality="HOME_CANDIDATE_LINK_ROLES",
             candidateCount=0,candidates=[],sameOriginLinks=0)
    soup=BeautifulSoup(html,"html.parser")
    seen=set()
    candidates={}
    for a in soup.find_all("a",href=True,limit=600):
        url=same_origin(a["href"])
        if url is None:
            continue
        seen.add(url)
        label=norm(a.get_text(" ",strip=True))
        if not POSITIVE.search(label) or NEGATIVE.search(label):
            continue
        if len(label)>120:
            return dict(out,decision="HOLD_OVERSIZE_LINK_LABEL")
        if url in candidates:
            candidates[url]["occurrences"]+=1
            continue
        parent=a.find_parent(["nav","header","main","section","article","footer"])
        container=parent.name if parent else "UNKNOWN"
        path=urlsplit(url).path
        candidates[url]=dict(url=url,path=path,label=label,
                             containerRole=container,occurrences=1,
                             ariaLabelPresent=bool(a.get("aria-label")),
                             titleAttributePresent=bool(a.get("title")))
    out["sameOriginLinks"]=len(seen)
    out["candidateCount"]=len(candidates)
    if len(candidates)>8:
        return dict(out,decision="HOLD_TOO_MANY_CANDIDATES")
    out["candidates"]=sorted(candidates.values(),key=lambda x:x["url"])
    if not candidates:
        return dict(out,decision="HOLD_NO_OFFICIAL_INDEX_CANDIDATE")
    if len(candidates)>1:
        return dict(out,decision="HOLD_MULTIPLE_INDEX_ROLES_REQUIRE_SOURCE_DETAIL")
    return dict(out,decision="REVIEW_SINGLE_LINK_ROLE_NOT_LIST_PASS")

def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-VENUE-02N",observedAtUTC=observed,
             requestBudget=1,requestCount=1,acceptedFields=0,
             goldenAccepted=0,published=False,releaseState=HOLD)
    receipt,html=get_one(HOME)
    out["homeReceipt"]=receipt
    if html is None:
        return dict(out,decision="HOLD_HOME_HTTP_OR_BODY")
    out.update(inspect(html,observed))
    return out

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
