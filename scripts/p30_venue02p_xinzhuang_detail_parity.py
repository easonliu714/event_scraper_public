#!/usr/bin/env python3
"""P30-VENUE-02P: one first-party index and at most one detail GET; no publishing."""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qsl
from bs4 import BeautifulSoup
from p30_venue02m_xinzhuang_discovery import HOLD,norm,same_origin,get_one
from p30_venue02o_xinzhuang_submenu_role import CANDIDATE_URL,DETAIL_PATH,EVENT_WORD,EXCLUDE

def select_candidate(index_html):
    """Only source-local event-labelled detail links, bounded and deterministic."""
    soup=BeautifulSoup(index_html,"html.parser")
    candidates={}
    for a in soup.find_all("a",href=True,limit=600):
        try: url=same_origin(a["href"],CANDIDATE_URL)
        except ValueError: continue
        if not url: continue
        p=urlsplit(url)
        label=norm(a.get_text(" ",strip=True))
        if not (8<=len(label)<=160 and DETAIL_PATH.search(p.path)
                and EVENT_WORD.search(label) and not EXCLUDE.search(label)):
            continue
        # Conflicting titles for the same URL are ambiguous; never silently choose.
        candidates.setdefault(url,set()).add(label)
    if not candidates:
        return None,dict(decision="HOLD_NO_TITLE_BOUND_DETAIL_LINK",candidateLinks=0)
    if len(candidates)>40:
        return None,dict(decision="HOLD_DETAIL_LINK_BOUND",candidateLinks=len(candidates))
    conflicts=sum(len(v)!=1 for v in candidates.values())
    if conflicts:
        return None,dict(decision="HOLD_LINK_TITLE_CONFLICT",candidateLinks=len(candidates),conflictingLinks=conflicts)
    url=sorted(candidates)[0]
    label=next(iter(candidates[url]))
    p=urlsplit(url)
    return (url,label),dict(decision="REVIEW_ONE_SOURCE_DERIVED_DETAIL_CANDIDATE",
                            candidateLinks=len(candidates),candidatePath=p.path,
                            candidateQueryKeys=sorted({k for k,_ in parse_qsl(p.query)})[:20],
                            candidateURLSHA256=hashlib.sha256(url.encode()).hexdigest(),
                            candidateTitleSHA256=hashlib.sha256(label.encode()).hexdigest())

def inspect_detail(html,expected_title):
    soup=BeautifulSoup(html,"html.parser")
    heads=[norm(h.get_text(" ",strip=True)) for h in soup.find_all(["h1","h2","h3"],limit=80)]
    if any(len(x)>500 for x in heads):
        return dict(decision="HOLD_DETAIL_HEADING_BOUND",exactTitleHeadingCount=0)
    exact=sum(h==expected_title for h in heads)
    if exact!=1:
        return dict(decision="HOLD_INDEX_DETAIL_TITLE_NOT_EXACT_UNIQUE",exactTitleHeadingCount=exact)
    return dict(decision="REVIEW_EXACT_INDEX_DETAIL_TITLE_NO_EVENT_ID_NO_FIELDS",
                exactTitleHeadingCount=exact,
                sourceRole="VENUE_DETAIL_TITLE_ONLY")

def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-VENUE-02P",source="XINZHUANG_ARTS_CENTER_VENUE",
             sourceURL=CANDIDATE_URL,observed_at=observed,requestBudget=2,
             requestCount=1,acceptedFields=0,goldenAccepted=0,published=False,
             ticketEventId=None,releaseState=HOLD,
             sourceQuality="BOUNDED_INDEX_TO_DETAIL_IDENTITY_DIAGNOSTIC")
    receipt,index=get_one(CANDIDATE_URL)
    out["indexReceipt"]=receipt
    if index is None:
        return dict(out,decision="HOLD_INDEX_HTTP_OR_BODY")
    selected,meta=select_candidate(index)
    out.update(meta)
    if selected is None:
        return out
    url,title=selected
    # Validate again at navigation boundary; never follow redirects.
    try: verified=same_origin(url,CANDIDATE_URL)
    except ValueError: verified=None
    if verified!=url:
        return dict(out,decision="HOLD_DETAIL_URL_SECURITY")
    out["requestCount"]=2
    receipt,detail=get_one(url)
    out["detailReceipt"]=receipt
    if detail is None:
        return dict(out,decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(inspect_detail(detail,title))
    out["provenance"]=dict(source=CANDIDATE_URL,observed_at=observed,
                           role="SOURCE_LOCAL_INDEX_DETAIL_TITLE_EDGE",
                           decision=out["decision"])
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
