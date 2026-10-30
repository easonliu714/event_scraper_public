#!/usr/bin/env python3
"""VENUE-02AA: source-local leaf text role diagnosis; strict REVIEW, never publish."""
import re
from datetime import date
from bs4 import BeautifulSoup
from p30_venue02z_ceramics_fields import DATE, VENUE, norm
from p30_venue02y_ceramics_role import inspect

def leaf_role_candidates(detail_html):
    soup = BeautifulSoup(detail_html, "html.parser")
    dates, places = [], []
    truncated = 0
    for node in soup.find_all(string=True, limit=5000):
        if node.parent.name in ("script","style","noscript","title"):
            continue
        raw = norm(str(node))
        if not raw or not ("展覽日期" in raw or "展覽地點" in raw):
            continue
        if len(raw) > 4000:
            truncated += 1
            continue
        for label, pattern, target in (("展覽日期",DATE,dates),("展覽地點",VENUE,places)):
            if label not in raw:
                continue
            pos = raw.find(label)
            local = raw[pos:pos+220]
            for m in pattern.finditer(local):
                if label == "展覽日期":
                    try:
                        y,mo,d,ey,em,ed=m.groups()
                        first=date(int(y),int(mo),int(d))
                        last=date(int(ey or y),int(em),int(ed))
                        target.append((first.isoformat(),last.isoformat()) if first <= last else None)
                    except ValueError:
                        target.append(None)
                else:
                    value=norm(m.group(1))
                    target.append(value if 2 <= len(value) <= 80 and not any(x in value for x in ("報名","售票","日期")) else None)
    return dates,places,truncated

def diagnose(index_html, detail_html):
    prior=inspect(index_html,detail_html)
    result={"gate":"P30-VENUE-02AA","source":"CERAMICS_P0_NEW_TAIPEI",
            "priorDecision":prior["decision"],"exactTitleMatches":prior["exactTitleMatches"],
            "acceptedFields":0,"goldenAccepted":0,"published":False,
            "releaseState":"HARD_HOLD_NO_PUBLICATION","ticketEventId":None}
    if prior["decision"]!="REVIEW_EXHIBITION_IDENTITY_ROLE_NO_FIELDS":
        return dict(result,decision="HOLD_PRIOR_IDENTITY_OR_ROLE")
    dates,places,truncated=leaf_role_candidates(detail_html)
    result.update(dateRoleCandidateCount=len(dates),venueRoleCandidateCount=len(places),
                  oversizedLeafCount=truncated,distinctVenueCandidateCount=len(set(str(x) for x in places)))
    if truncated or len(dates)!=1 or dates[0] is None:
        return dict(result,decision="HOLD_DATE_RANGE_LEAF_MISSING_INVALID_OR_AMBIGUOUS")
    if len(places)!=1 or places[0] is None:
        return dict(result,decision="HOLD_VENUE_LEAF_MISSING_OR_AMBIGUOUS")
    return dict(result,decision="REVIEW_LEAF_LOCAL_RANGE_VENUE_NOT_ACCEPTED")
