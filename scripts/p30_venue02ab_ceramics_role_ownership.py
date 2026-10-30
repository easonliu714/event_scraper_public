#!/usr/bin/env python3
"""VENUE-02AB: source-observed Ceramics field-label ownership and duplicates.

The official museum uses both inline slash-separated and separate-line
exhibition date/location labels. This audit never promotes a field.
"""
import hashlib
from datetime import date
from bs4 import BeautifulSoup
from p30_venue02z_ceramics_fields import DATE, VENUE, norm

def classify_field_ownership(detail_html, expected_title):
    soup = BeautifulSoup(detail_html, "html.parser")
    headings = [norm(x.get_text(" ", strip=True)) for x in soup.find_all("h3", limit=30)]
    out = {"gate":"P30-VENUE-02AB","source":"CERAMICS_P0_NEW_TAIPEI",
           "titleMatches":headings.count(expected_title),
           "dateRoleNodes":0,"venueRoleNodes":0,"distinctDateValues":0,
           "distinctVenueValues":0,"acceptedFields":0,"goldenAccepted":0,
           "published":False,"ticketEventId":None,
           "releaseState":"HARD_HOLD_NO_PUBLICATION"}
    if len(headings) != 1 or out["titleMatches"] != 1:
        return dict(out, decision="HOLD_DETAIL_HEADING_IDENTITY")
    dates, venues = [], []
    invalid = mixed = 0
    for node in soup.find_all(string=True, limit=5000):
        if node.parent.name in ("script","style","noscript","title"):
            continue
        raw = norm(str(node))
        if not raw or len(raw)>4000:
            continue
        if "展覽日期" not in raw and "展覽地點" not in raw:
            continue
        if any(x in raw for x in ("報名日期","報名期間","售票日期","售票期間")):
            mixed += 1
            continue
        if "展覽日期" in raw:
            out["dateRoleNodes"] += 1
            matches = list(DATE.finditer(raw))
            if len(matches) != 1:
                invalid += 1
            else:
                try:
                    y,mo,d,ey,em,ed = matches[0].groups()
                    start=date(int(y),int(mo),int(d))
                    end=date(int(ey or y),int(em),int(ed))
                    if start > end:
                        invalid += 1
                    else:
                        dates.append(start.isoformat()+"/"+end.isoformat())
                except ValueError:
                    invalid += 1
        if "展覽地點" in raw:
            out["venueRoleNodes"] += 1
            matches = list(VENUE.finditer(raw))
            if len(matches) != 1:
                invalid += 1
            else:
                v=norm(matches[0].group(1))
                if not 2 <= len(v) <= 80 or any(x in v for x in ("報名","售票","日期")):
                    invalid += 1
                else:
                    venues.append(v)
    out["distinctDateValues"] = len(set(dates))
    out["distinctVenueValues"] = len(set(venues))
    out["dateValueSHA256"] = [hashlib.sha256(v.encode()).hexdigest() for v in sorted(set(dates))]
    out["venueValueSHA256"] = [hashlib.sha256(v.encode()).hexdigest() for v in sorted(set(venues))]
    if invalid or mixed:
        return dict(out, decision="HOLD_INVALID_OR_MIXED_FIELD_ROLE")
    if not dates or not venues:
        return dict(out, decision="HOLD_MISSING_EXHIBITION_FIELD_ROLE")
    if len(set(dates)) > 1 or len(set(venues)) > 1:
        return dict(out, decision="HOLD_CONFLICTING_ROLE_VALUES")
    if len(dates) != 1 or len(venues) != 1:
        return dict(out, decision="HOLD_DUPLICATE_SAME_VALUE_OWNERSHIP")
    return dict(out, decision="REVIEW_SINGLE_LEAF_ROLE_NOT_ACCEPTED")
