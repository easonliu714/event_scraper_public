#!/usr/bin/env python3
"""VENUE-02AF: exact-SID adjacent span role/value topology, REVIEW only.
No network or implicit publication; cross-paragraph and cross-SID joins refused.
"""
import hashlib
from datetime import date
from bs4 import BeautifulSoup
from p30_venue02ad_ceramics_live_sid_probe import TITLE,HOLD,inspect_detail
from p30_venue02z_ceramics_fields import DATE,VENUE,norm

def diagnose(html):
    prior=inspect_detail(html)
    out={"gate":"P30-VENUE-02AF","source":"CERAMICS_P0_NEW_TAIPEI",
         "sidBound":prior["sidBound"],"headingMatches":prior["headingMatches"],
         "adjacentRolePairs":0,"datePairs":0,"venuePairs":0,"roleDigest":[],
         "acceptedFields":0,"goldenAccepted":0,"published":False,
         "ticketEventId":None,"releaseState":HOLD}
    if not prior["sidBound"] or prior["headingMatches"]!=1:
        return dict(out,decision="HOLD_SID_OR_TITLE")
    soup=BeautifulSoup(html,"html.parser")
    roles=[]
    for p in soup.find_all(["p","li"],limit=1200):
        spans=p.find_all("span",recursive=False,limit=8)
        if len(spans)!=2 or p.find(["p","li","table"]):
            continue
        label=norm(spans[0].get_text(" ",strip=True))
        value=norm(spans[1].get_text(" ",strip=True))
        if not value or len(value)>120 or len(label)>20:
            continue
        if label in ("展覽日期","展覽日期:","展覽日期："):
            kind="EXHIBITION_DATE_RANGE"
            m=DATE.fullmatch("展覽日期:"+value)
            if m:
                y,mo,d,ey,em,ed=m.groups()
                try:
                    start=date(int(y),int(mo),int(d))
                    end=date(int(ey or y),int(em),int(ed))
                    valid=start<=end
                except ValueError:
                    valid=False
            else:
                valid=False
        elif label in ("展覽地點","展覽地點:","展覽地點："):
            kind="EXHIBITION_VENUE"
            valid=bool(VENUE.fullmatch("展覽地點:"+value)) and not any(x in value for x in ("報名","售票","日期","時間"))
        else:
            continue
        roles.append((kind,valid,hashlib.sha256(value.encode()).hexdigest()))
    out["adjacentRolePairs"]=len(roles)
    out["datePairs"]=sum(k=="EXHIBITION_DATE_RANGE" for k,_,_ in roles)
    out["venuePairs"]=sum(k=="EXHIBITION_VENUE" for k,_,_ in roles)
    out["roleDigest"]=sorted(x[2] for x in roles)[:8]
    if out["datePairs"]>1 or out["venuePairs"]>1:
        return dict(out,decision="HOLD_DUPLICATE_ROLE_PAIRS")
    if any(not valid for _,valid,_ in roles):
        return dict(out,decision="HOLD_INVALID_ADJACENT_ROLE_VALUE")
    if out["datePairs"]==1 and out["venuePairs"]==1:
        return dict(out,decision="REVIEW_ADJACENT_SOURCE_LOCAL_ROLES_NO_FIELD_ACCEPTANCE")
    return dict(out,decision="HOLD_MISSING_OR_NONADJACENT_ROLE_VALUE")

if __name__=="__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
