#!/usr/bin/env python3
"""VENUE-02R: one bounded official Shulin Arts Center index discovery, no detail navigation."""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from urllib.parse import urlsplit,urljoin,parse_qsl
from bs4 import BeautifulSoup
from p30_venue02m_xinzhuang_discovery import get_one,HOLD
URL="https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc?XsmSId=0J080506169482009359"
HOST="www.culture.ntpc.gov.tw"
def safe_link(href):
    if not href or href.lstrip().startswith(("#","javascript:","data:","mailto:")): return None
    try:
        u=urljoin(URL,href);p=urlsplit(u)
        if p.scheme!="https" or p.hostname!=HOST or p.username or p.password or p.port not in (None,443): return None
        return u
    except ValueError: return None

def inspect_index(html):
    soup=BeautifulSoup(html,"html.parser")
    links={}
    for a in soup.find_all("a",href=True,limit=450):
        u=safe_link(a["href"])
        if not u: continue
        p=urlsplit(u)
        if "/xmdoc" not in p.path: continue
        label=" ".join(a.get_text(" ",strip=True).split())
        if not label or len(label)>180: continue
        keys=tuple(sorted({k for k,_ in parse_qsl(p.query)}))
        links.setdefault((p.path,keys),0)
        links[(p.path,keys)]+=1
    roles=[dict(pathClass=("XMDOC" if x[0].endswith("/xmdoc") else "OTHER_XMDOC"),
                queryKeys=list(x[1]),count=n)
           for x,n in sorted(links.items())[:20]]
    return dict(decision="REVIEW_INDEX_LINK_ROLES_NO_LIST_OR_DETAIL_IDENTITY" if roles else "HOLD_NO_SOURCE_LOCAL_LINKS",
                linkRoleGroups=roles,roleGroupCount=len(links),acceptedFields=0,
                sourceRole="VENUE_INDEX_DISCOVERY_ONLY")

def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-VENUE-02R",source="SHULIN_ARTS_CENTER_VENUE",observed_at=observed,
             requestBudget=1,requestCount=1,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD,ticketEventId=None,venueEventId=None)
    receipt,html=get_one(URL)
    out["indexReceipt"]=receipt
    if html is None: return dict(out,decision="HOLD_INDEX_HTTP_OR_BODY")
    out.update(inspect_index(html))
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--live-one",action="store_true");p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f: json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
