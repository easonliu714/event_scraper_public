#!/usr/bin/env python3
"""P30-VENUE-02W: reject duplicate Fuzhong15 film showings; no ticket identity."""
import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from p30_venue02u_fuzhong15_sessions import HOME, HOLD, get_one
from p30_venue02v_fuzhong15_row_parity import index_rows, year_hint, inspect_pair

def showing_groups(index_html):
    rows=index_rows(index_html)
    hint=year_hint(index_html)
    result={"rowLocalCandidates":len(rows), "sameFilmRowCount":0, "distinctShowingCount":0,
            "duplicateShowingCount":0, "conflictingFilmTitleCount":0,
            "acceptedFields":0, "venueScreeningId":None, "ticketEventId":None}
    if hint is None:
        return result, None, "HOLD_INDEX_YEAR_MONTH_AMBIGUOUS"
    eligible=[r for r in rows if r["month"]==int(hint[1])]
    groups=defaultdict(list)
    for row in eligible:
        groups[row["url"]].append(row)
    if not groups:
        return result, None, "HOLD_NO_ELIGIBLE_SCREENING_ROW"
    url, group=sorted(groups.items(),key=lambda p:(-len(p[1]),p[0]))[0]
    unique={(r["month"],r["day"],r["time"]) for r in group}
    result["sameFilmRowCount"]=len(group)
    result["distinctShowingCount"]=len(unique)
    result["duplicateShowingCount"]=len(group)-len(unique)
    result["conflictingFilmTitleCount"]=max(0,len({r["title"] for r in group})-1)
    if result["duplicateShowingCount"] or result["conflictingFilmTitleCount"]:
        return result, None, "HOLD_DUPLICATE_SHOWING_OR_FILM_TITLE"
    return result, group[0], None

def inspect_multishow(index_html, detail_html):
    group, selected, error=showing_groups(index_html)
    if error:
        return dict(group,decision=error)
    parity=inspect_pair(index_html,detail_html,selected)
    group.update(parity)
    if not parity["decision"].startswith("REVIEW_"):
        group["decision"]="HOLD_DETAIL_ROW_PARITY"
    elif group["sameFilmRowCount"]>1:
        group["decision"]="REVIEW_MULTISHOWING_FILM_NOT_UNIQUE_SESSION"
    else:
        group["decision"]="REVIEW_ONE_SHOWING_NO_TICKET_ID"
    group["acceptedFields"]=0
    group["venueScreeningId"]=None
    group["ticketEventId"]=None
    return group

def live():
    audit={"gate":"P30-VENUE-02W","source":"FUZHONG15_P0_NEW_TAIPEI",
           "observed_at":datetime.now(timezone.utc).isoformat(),
           "requestBudget":2,"requestCount":1,"acceptedFields":0,
           "goldenAccepted":0,"published":False,"releaseState":HOLD}
    receipt,index=get_one(HOME)
    audit["indexReceipt"]=receipt
    if index is None:
        return dict(audit,decision="HOLD_INDEX_HTTP_OR_BODY")
    groups,selected,error=showing_groups(index)
    audit.update(groups)
    if error:
        return dict(audit,decision=error)
    audit["selectedDetailURLSHA256"]=hashlib.sha256(selected["url"].encode()).hexdigest()
    audit["requestCount"]=2
    receipt,detail=get_one(selected["url"])
    audit["detailReceipt"]=receipt
    if detail is None:
        return dict(audit,decision="HOLD_DETAIL_HTTP_OR_BODY")
    audit.update(inspect_multishow(index,detail))
    return audit

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
