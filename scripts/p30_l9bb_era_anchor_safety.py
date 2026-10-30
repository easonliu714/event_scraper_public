#!/usr/bin/env python3
"""P30-L9-BB: classify one source-local ERA unsafe anchor; never navigate or publish."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from p30_l9ba_era_row_anchor import inspect as predecessor, DATE, TIME
from p30_l9av_era_source_role import DETAIL, HOLD, norm, get_one

def classify_href(href):
    """Return sanitized reason only. Never expose raw href, query or host."""
    if not href or not href.strip():
        return "EMPTY"
    href = href.strip()
    if href.lower().startswith(("javascript:", "data:", "mailto:", "#")):
        return "NON_NAVIGABLE"
    try:
        p = urlsplit(urljoin(DETAIL, href))
        if p.scheme.lower() != "https":
            return "NON_HTTPS_SCHEME"
        if p.username is not None or p.password is not None:
            return "USERINFO_PRESENT"
        if p.port not in (None, 443):
            return "NONDEFAULT_PORT"
        if not p.hostname:
            return "MISSING_HOST"
        if p.hostname.lower() != urlsplit(DETAIL).hostname.lower():
            return "EXTERNAL_HOST"
        return "HTTPS_SAME_ORIGIN"
    except ValueError:
        return "MALFORMED_AUTHORITY_OR_PORT"

def inspect(html, observed):
    prior = predecessor(html, observed)
    out = dict(gate="P30-L9-BB", source="ERA_TICKET_PLATFORM_08",
               sourceURL=DETAIL, observed_at=observed, releaseState=HOLD,
               acceptedFields=0, goldenAccepted=0, published=False,
               ticketEventId=None, sessionId=None,
               predecessorDecision=prior["decision"], anchorSafetyClass="UNKNOWN",
               sourceQuality="OFFICIAL_ROW_ANCHOR_SAFETY_DIAGNOSIS_ONLY")
    if prior["decision"] != "HOLD_UNSAFE_ANCHOR_URL":
        return dict(out, decision="HOLD_PREDECESSOR_NOT_UNSAFE_ANCHOR")
    soup = BeautifulSoup(html, "html.parser")
    headings = [h for h in soup.find_all(["h2","h3","h4","h5"])
                if norm(h.get_text(" ",strip=True)) == "場次列表"]
    if len(headings) != 1:
        return dict(out, decision="HOLD_HEADING_NOT_UNIQUE")
    h = headings[0]
    tables = {}
    parent = h.parent
    for _ in range(3):
        if parent is None or parent.name in ("body","html","[document]"):
            break
        children = parent.find_all(recursive=False)
        if len(children) > 80:
            return dict(out, decision="HOLD_SCOPE_BOUND")
        pos = next((i for i,c in enumerate(children) if c is h or h in c.descendants), -1)
        if pos < 0:
            break
        for child in children[pos+1:pos+9]:
            if child.name in ("h1","h2","h3","h4","h5","h6") or child.find(["h1","h2","h3","h4","h5","h6"]):
                break
            txt = norm(child.get_text(" ",strip=True))
            if "退票方式" in txt or len(txt)>5000:
                break
            for t in ([child] if child.name=="table" else [])+child.find_all("table",limit=3):
                tables[id(t)]=t
        parent=parent.parent
    if len(tables)!=1:
        return dict(out,decision="HOLD_TABLE_NOT_UNIQUE")
    rows = [r for r in next(iter(tables.values())).find_all("tr",limit=41)
            if DATE.search(norm(r.get_text(" ",strip=True)))
            and TIME.search(norm(r.get_text(" ",strip=True)))]
    if len(rows)!=1:
        return dict(out,decision="HOLD_ROW_NOT_UNIQUE")
    links=rows[0].find_all("a",href=True,limit=3)
    if len(links)!=1:
        return dict(out,decision="HOLD_ANCHOR_NOT_UNIQUE")
    safety=classify_href(links[0]["href"])
    out["anchorSafetyClass"]=safety
    return dict(out,decision="HOLD_UNSAFE_ANCHOR_CLASSIFIED" if safety!="HTTPS_SAME_ORIGIN"
                else "HOLD_PREDECESSOR_SAFETY_INCONSISTENCY")

def live():
    observed=datetime.now(timezone.utc).isoformat()
    receipt,html=get_one(DETAIL)
    out=dict(gate="P30-L9-BB",observedAtUTC=observed,requestBudget=1,requestCount=1,
             detailReceipt=receipt,acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=HOLD)
    if html is None:
        return dict(out,decision="HOLD_OFFICIAL_DETAIL_UNAVAILABLE")
    out.update(inspect(html,observed))
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
