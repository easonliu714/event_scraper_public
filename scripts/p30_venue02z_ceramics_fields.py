#!/usr/bin/env python3
"""P30-VENUE-02Z: Ceramics bounded exhibition range/location provenance, REVIEW only."""
import argparse
import hashlib
import json
import re
from datetime import date, datetime, timezone
from bs4 import BeautifulSoup
from p30_venue02y_ceramics_role import HOME,HOLD,index_edges,inspect,get_one

DATE = re.compile(r"展覽日期\s*[：:]\s*(20\d{2})年(\d{1,2})月(\d{1,2})日\s*(?:至|~|－|-)\s*(?:(20\d{2})年)?(\d{1,2})月(\d{1,2})日")
VENUE = re.compile(r"展覽地點\s*[：:]\s*([^/；;|]{2,80})")

def norm(s):
    return " ".join(str(s).split())

def bounded_roles(html):
    soup=BeautifulSoup(html,"html.parser")
    dates,places=[],[]
    for node in soup.find_all(["p","li","td","dd","span","div"],limit=1500):
        if node.find(["p","li","td","dd","div"]):
            continue
        txt=norm(node.get_text(" ",strip=True))
        if len(txt)>260:
            continue
        for m in DATE.finditer(txt):
            try:
                y,mo,d,ey,em,ed=m.groups()
                first=date(int(y),int(mo),int(d))
                last=date(int(ey or y),int(em),int(ed))
                dates.append((first,last))
            except ValueError:
                dates.append(None)
        for m in VENUE.finditer(txt):
            v=norm(m.group(1))
            if v:
                places.append(v)
    return dates,places

def inspect_range(index_html,detail_html,observed_at="OFFLINE_FIXTURE"):
    prior=inspect(index_html,detail_html)
    out={"priorDecision":prior["decision"],"exactTitleMatches":prior["exactTitleMatches"],
         "acceptedFields":0,"goldenAccepted":0,"ticketEventId":None,
         "fieldProvenance":[],"dateRangeCandidateCount":0,"venueCandidateCount":0}
    if prior["decision"]!="REVIEW_EXHIBITION_IDENTITY_ROLE_NO_FIELDS":
        return dict(out,decision="HOLD_PRIOR_IDENTITY_OR_ROLE")
    dates,places=bounded_roles(detail_html)
    out["dateRangeCandidateCount"]=len(dates)
    out["venueCandidateCount"]=len(places)
    if len(dates)!=1 or dates[0] is None or dates[0][0]>dates[0][1]:
        return dict(out,decision="HOLD_DATE_RANGE_MISSING_INVALID_OR_AMBIGUOUS")
    if len(places)!=1 or not 2<=len(places[0])<=80 or any(x in places[0] for x in ("報名","售票","日期")):
        return dict(out,decision="HOLD_VENUE_MISSING_OR_AMBIGUOUS")
    for role,val in (("EXHIBITION_DATE_RANGE",dates[0][0].isoformat()+"/"+dates[0][1].isoformat()),
                     ("EXHIBITION_VENUE",places[0])):
        out["fieldProvenance"].append({"source":"CERAMICS_P0_NEW_TAIPEI",
            "observed_at":observed_at,"role":role,"decision":"REVIEW_CANDIDATE_NOT_ACCEPTED",
            "valueSHA256":hashlib.sha256(val.encode()).hexdigest()})
    return dict(out,decision="REVIEW_EXACT_EXHIBITION_RANGE_VENUE_NO_FIELDS")

def live():
    a={"gate":"P30-VENUE-02Z","source":"CERAMICS_P0_NEW_TAIPEI",
       "observed_at":datetime.now(timezone.utc).isoformat(),
       "requestBudget":2,"requestCount":1,"acceptedFields":0,
       "goldenAccepted":0,"published":False,"releaseState":HOLD}
    a["indexReceipt"],index=get_one(HOME)
    if index is None:
        return dict(a,decision="HOLD_INDEX_HTTP_OR_BODY")
    edges,conflict=index_edges(index)
    eligible=[(u,t) for u,t,r in edges if r=="EXHIBITION_CANDIDATE"]
    a.update(sourceDerivedEdges=len(edges),registrationExcludedCount=len(edges)-len(eligible),
             titleConflicts=conflict)
    if conflict or not eligible:
        return dict(a,decision="HOLD_ZERO_OR_CONFLICTING_EDGES")
    url=eligible[0][0]
    a["selectedDetailURLSHA256"]=hashlib.sha256(url.encode()).hexdigest()
    a["requestCount"]=2
    a["detailReceipt"],detail=get_one(url)
    if detail is None:
        return dict(a,decision="HOLD_DETAIL_HTTP_OR_BODY")
    a.update(inspect_range(index,detail,a["observed_at"]))
    return a

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n")
