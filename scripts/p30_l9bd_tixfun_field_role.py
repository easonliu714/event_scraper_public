#!/usr/bin/env python3
"""L9-BD TixFun same-product local field-label role diagnostic; never promote fields."""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from p30_l9bc_tixfun_identity import HOME,PRODUCT,MARKER,HOLD,get_one,safe_product,detail_identity

URL=f"https://tixfun.com/UTK0201_?PRODUCT_ID={PRODUCT}"
CAP_NODES=250
ROLE_PATTERNS={
    "PERFORMANCE_DATE":re.compile(r"^(演出日期|演出時間|活動日期|表演時間)[：:]?$"),
    "PRICE":re.compile(r"^(票價|票價資訊|票種票價|票價說明)[：:]?$"),
    "SALE_TIME":re.compile(r"^(售票時間|開賣時間|啟售時間|售票日期)[：:]?$"),
    "REFUND":re.compile(r"^(退票期限|退票時間|退款期限|退票辦法)[：:]?$"),
}
def role_of(label):
    s=" ".join(str(label).split())
    found=[name for name,p in ROLE_PATTERNS.items() if p.fullmatch(s)]
    return found[0] if len(found)==1 else None

def inspect_local(html):
    soup=BeautifulSoup(html,"html.parser")
    heads=[h for h in soup.find_all(["h1","h2","h3"],limit=80)
           if MARKER in h.get_text(" ",strip=True)]
    if len(heads)!=1:
        return dict(decision="HOLD_TITLE_HEADING_NOT_UNIQUE",headingMatches=len(heads),acceptedFields=0)
    h=heads[0]
    parent=h.parent
    # Only heading-owned local container, never global regex over full document.
    for _ in range(2):
        if parent is not None and parent.name not in ("body","html"):
            parent=parent.parent
        else: break
    if parent is None or parent.name in ("body","html"):
        parent=h.parent
    nodes=parent.find_all(["th","dt","strong","b","label","span","div","p"],limit=CAP_NODES)
    counts={k:0 for k in ROLE_PATTERNS}
    for node in nodes:
        if node.find(["th","dt","strong","b","label","span","div","p"]): continue
        role=role_of(node.get_text(" ",strip=True))
        if role: counts[role]+=1
    return dict(decision="REVIEW_LOCAL_ROLE_COUNTS_NO_FIELD_VALUES",
                headingMatches=1,roleLabelCounts=counts,scannedNodes=len(nodes),
                acceptedFields=0,sourceRole="TICKET_DETAIL_LOCAL_ROLE_ONLY")

def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-L9-BD",source="TIXFUN_PLATFORM_09",observed_at=observed,
             requestBudget=1,requestCount=1,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD,ticketEventId=None,sessionId=None)
    if safe_product(URL)!=URL:
        return dict(out,decision="HOLD_UNSAFE_SOURCE_URL")
    receipt,html=get_one(URL)
    out["detailReceipt"]=receipt
    if html is None: return dict(out,decision="HOLD_DETAIL_HTTP_OR_BODY")
    if detail_identity(html)["decision"]!="REVIEW_SAME_PRODUCT_TITLE_HEADING_NO_FIELDS":
        return dict(out,decision="HOLD_IDENTITY_PRECONDITION")
    out.update(inspect_local(html))
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--live-one",action="store_true");p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f: json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
