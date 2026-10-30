#!/usr/bin/env python3
"""L9-BE: one TixFun detail DOM-scope root-cause probe, fail closed; rotate if no exact labels."""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from p30_l9bd_tixfun_field_role import URL,MARKER,HOLD,get_one,detail_identity,role_of,ROLE_PATTERNS
TOKENS=("演出日期","演出時間","活動日期","表演時間","票價","售票時間","開賣時間","退票期限")
def inspect_scopes(html):
    soup=BeautifulSoup(html,"html.parser")
    heads=[h for h in soup.find_all(["h1","h2","h3"],limit=80) if MARKER in h.get_text(" ",strip=True)]
    if len(heads)!=1:
        return dict(decision="HOLD_TITLE_HEADING_NOT_UNIQUE",headingMatches=len(heads),acceptedFields=0)
    parent=heads[0]
    scopes=[]
    for depth in range(1,6):
        parent=parent.parent
        if parent is None or parent.name in ("body","html","[document]"): break
        nodes=parent.find_all(["th","dt","strong","b","label","span","div","p","li"],limit=350)
        exact={k:0 for k in ROLE_PATTERNS}; hints=0
        for node in nodes:
            if node.find(["th","dt","strong","b","label","span","div","p","li"]): continue
            s=" ".join(node.get_text(" ",strip=True).split())
            if len(s)>80: continue
            role=role_of(s)
            if role: exact[role]+=1
            elif any(t in s for t in TOKENS): hints+=1
        scopes.append(dict(depth=depth,scannedNodes=len(nodes),exactLabelCounts=exact,nonExactRoleHints=hints))
        if parent.name=="main": break
    if not scopes:
        return dict(decision="HOLD_NO_BOUNDED_HEADING_SCOPE",acceptedFields=0)
    found=sum(sum(s["exactLabelCounts"].values()) for s in scopes)
    return dict(decision=("REVIEW_EXACT_SCOPE_LABELS_NO_VALUES" if found else "HOLD_NO_EXACT_SCOPE_LABELS_ROTATE_SOURCE"),
                headingMatches=1,scopes=scopes,acceptedFields=0,
                sourceRole="HEADING_ANCESTOR_DIAGNOSTIC_ONLY")
def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-L9-BE",source="TIXFUN_PLATFORM_09",observed_at=observed,
             requestBudget=1,requestCount=1,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD,ticketEventId=None,sessionId=None)
    receipt,html=get_one(URL);out["detailReceipt"]=receipt
    if html is None: return dict(out,decision="HOLD_DETAIL_HTTP_OR_BODY")
    if detail_identity(html)["decision"]!="REVIEW_SAME_PRODUCT_TITLE_HEADING_NO_FIELDS":
        return dict(out,decision="HOLD_IDENTITY_PRECONDITION")
    out.update(inspect_scopes(html))
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--live-one",action="store_true");p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f: json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
