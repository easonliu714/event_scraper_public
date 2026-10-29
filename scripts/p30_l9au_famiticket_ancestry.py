#!/usr/bin/env python3
"""L9-AU: bounded FamiTicket common-div ancestry diagnostic, never promote fields."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import p30_l9as_famiticket_live_dom as frozen

RELEASE="HARD_HOLD_NO_PUBLICATION"
LABELS=("活動時間","活動地點","活動票價")
MAX_HOPS=6
MAX_REGION_CHARS=4500

def ancestor_chain(node):
    out=[]
    for parent in node.parents:
        if getattr(parent,"name",None) in ("div","section","article") and not frozen.hidden(parent):
            out.append(parent)
    return out

def inspect_ancestry(html):
    out=dict(source="FAMITICKET_07",decision="HOLD_INPUT",identity="UNKNOWN",
             commonAncestorTag=None,headingHops=None,markerHops=None,
             regionChars=None,roleLabelCounts={},sourceQuality="UNKNOWN",
             acceptedFields=0,goldenAccepted=0,published=False,
             ticketEventId=None,releaseState=RELEASE)
    prior=frozen.inspect_html(html,frozen.URL,frozen.TITLE)
    out["priorDecision"]=prior["decision"]
    if not prior["decision"].startswith("REVIEW_"):
        return dict(out,decision="HOLD_PRIOR_IDENTITY")
    soup=BeautifulSoup(html,"html.parser")
    heads=[t for t in soup.find_all(["h1","h2","h3","h4"])
           if frozen.norm(t.get_text(" ",strip=True))==frozen.TITLE and not frozen.hidden(t)]
    marks=[t for t in soup.find_all("img")
           if frozen.norm(t.get("alt",""))=="《活動資訊》" and not frozen.hidden(t)]
    marks += [t.parent for t in soup.find_all(string=True)
              if t.parent and frozen.norm(t)=="《活動資訊》" and not frozen.hidden(t.parent)]
    if len(heads)!=1 or len(marks)!=1:
        return dict(out,decision="HOLD_NONUNIQUE_ANCHORS")
    hchain,mchain=ancestor_chain(heads[0]),ancestor_chain(marks[0])
    matches=[(node,hi,mi) for hi,node in enumerate(hchain) for mi,other in enumerate(mchain) if node is other]
    if not matches:
        return dict(out,decision="HOLD_NO_COMMON_VISIBLE_CONTAINER")
    node,hh,mh=min(matches,key=lambda v:(max(v[1],v[2]),v[1]+v[2]))
    out.update(commonAncestorTag=node.name,headingHops=hh,markerHops=mh)
    if max(hh,mh)>MAX_HOPS:
        return dict(out,decision="HOLD_COMMON_ANCESTOR_TOO_DISTANT")
    content=frozen.norm(node.get_text(" ",strip=True))
    out["regionChars"]=len(content)
    if not 15<=len(content)<=MAX_REGION_CHARS:
        return dict(out,decision="HOLD_REGION_SIZE_OR_GLOBAL_WRAPPER")
    local_heads=[t for t in node.find_all(["h1","h2","h3","h4"]) if not frozen.hidden(t)]
    if len(local_heads)!=1 or frozen.norm(local_heads[0].get_text(" ",strip=True))!=frozen.TITLE:
        return dict(out,decision="HOLD_OTHER_HEADINGS_IN_REGION")
    counts={x:content.count(x) for x in LABELS}
    out["roleLabelCounts"]=counts
    if any(v!=1 for v in counts.values()):
        return dict(out,decision="HOLD_NONUNIQUE_ROLE_LABELS",sourceQuality="REVIEW_LOCAL_ANCESTRY")
    if "退票" in content or "退款" in content:
        return dict(out,decision="HOLD_REFUND_MIXED_IN_REGION",sourceQuality="REVIEW_LOCAL_ANCESTRY")
    return dict(out,decision="REVIEW_BOUNDED_COMMON_ANCESTRY_NO_FIELDS",
                identity="REVIEW_SAME_LOCAL_TITLE_MARKER",
                sourceQuality="REVIEW_LOCAL_ANCESTRY")

def live_one():
    import requests
    out=dict(observedAtUTC=datetime.now(timezone.utc).isoformat(),
             requestCount=1,httpStatus=None,bodyBytes=0,bodySHA256=None,
             decision="HOLD_NETWORK",sourceQuality="HOLD_NETWORK",
             acceptedFields=0,goldenAccepted=0,published=False,releaseState=RELEASE)
    try:
        with requests.get(frozen.URL,headers={"User-Agent":"EventRadar-ReadOnly/1.0"},
                          timeout=(6,12),allow_redirects=False,stream=True) as r:
            out["httpStatus"]=r.status_code
            if r.status_code!=200:
                return dict(out,decision="HOLD_HTTP_STATUS")
            if r.headers.get("Content-Type","").split(";")[0].lower() not in ("text/html","application/xhtml+xml"):
                return dict(out,decision="HOLD_CONTENT_TYPE")
            parts=[]; size=0
            for chunk in r.iter_content(32768):
                size+=len(chunk)
                if size>frozen.MAX_HTML_BYTES:
                    return dict(out,decision="HOLD_BODY_CAP",bodyBytes=size)
                parts.append(chunk)
            raw=b"".join(parts)
            out.update(bodyBytes=len(raw),bodySHA256=hashlib.sha256(raw).hexdigest())
            out.update(inspect_ancestry(raw.decode(r.encoding or "utf-8",errors="replace")))
    except Exception as exc:
        out["networkErrorClass"]=type(exc).__name__
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--live-one",action="store_true")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    if not args.live_one: raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live_one(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
