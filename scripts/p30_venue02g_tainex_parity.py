#!/usr/bin/env python3
"""P30-VENUE-02G: TAINEX same-source list/detail identity and field-role REVIEW.

Source-backed public text diagnostic; no CI network, no event publication.
TAINEX numeric /event/<id> is a venue-local record ID, never a ticket ID.
"""
from __future__ import annotations
import re
from datetime import date, datetime, timezone
from urllib.parse import urlsplit

LIST_URL = "https://www.tainex.com.tw/event"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
DETAIL_PATH = re.compile(r"/event/([1-9][0-9]{0,7})")
HALLS = ("1館", "2館")

def norm(s):
    return " ".join(s.split())

def local_id(url):
    if not isinstance(url, str) or len(url) > 180:
        return None
    u = urlsplit(url)
    if (u.scheme != "https" or u.netloc != "www.tainex.com.tw"
            or u.query or u.fragment or u.username or u.password):
        return None
    m = DETAIL_PATH.fullmatch(u.path)
    return m.group(1) if m else None

def period(value):
    if not isinstance(value, list) or len(value) != 2:
        return None
    try:
        if not all(isinstance(x, str) and re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", x) for x in value):
            return None
        start, end = (date.fromisoformat(x) for x in value)
        if start > end:
            return None
        return (start.isoformat(), end.isoformat())
    except ValueError:
        return None

def inspect_pair(list_card, detail, observed_at):
    base = dict(source="TAINEX_OFFICIAL_VENUE", decision="HOLD_INPUT",
                identity="UNKNOWN", venueLocalIdReview=None, ticketEventId=None,
                sourceRole="VENUE_OFFICIAL_EXHIBITION", provenance={},
                acceptedFields=0, goldenAccepted=0, published=False,
                eventDateAccepted=False, sessionAccepted=False,
                releaseState=RELEASE, liveHttpGetThisCI=0)
    if (not isinstance(list_card, dict) or not isinstance(detail, dict)
            or not isinstance(observed_at, str) or not observed_at.endswith("Z")
            or not 10 <= len(observed_at) <= 40):
        return base
    try:
        datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError:
        return base
    allowed_card = {"title","url","period","hall"}
    allowed_detail = {"title","url","period","hall","venue","organizer_url"}
    if set(list_card) != allowed_card or not set(detail).issubset(allowed_detail) or not (allowed_detail - {"organizer_url"}).issubset(detail):
        return base
    a = local_id(list_card["url"])
    b = local_id(detail["url"])
    if a is None or a != b or list_card["url"] != detail["url"]:
        return dict(base, decision="HOLD_SOURCE_PATH_IDENTITY")
    if (not all(isinstance(x, str) for x in (list_card["title"],detail["title"]))
            or not 4 <= len(norm(list_card["title"])) <= 180
            or norm(list_card["title"]) != norm(detail["title"])):
        return dict(base, decision="HOLD_EXACT_TITLE_PARITY")
    base["identity"] = "REVIEW_EXACT_SAME_SOURCE_URL_AND_TITLE"
    base["venueLocalIdReview"] = a
    lp, dp = period(list_card["period"]), period(detail["period"])
    if lp is None or dp is None or lp != dp:
        return dict(base, decision="HOLD_EXHIBITION_PERIOD_PARITY")
    if (list_card["hall"] not in HALLS or detail["hall"] not in HALLS
            or list_card["hall"] != detail["hall"]):
        return dict(base, decision="HOLD_HALL_IDENTITY")
    if (not isinstance(detail["venue"], str) or not 2 <= len(norm(detail["venue"])) <= 120
            or not any(x in detail["venue"] for x in ("展場", "會議室"))):
        return dict(base, decision="HOLD_VENUE_ROLE")
    org = detail.get("organizer_url")
    if org is not None:
        if not isinstance(org, str) or len(org) > 200:
            return dict(base, decision="HOLD_EXTERNAL_ORGANIZER_LINK")
        u = urlsplit(org)
        if u.scheme != "https" or not u.hostname or u.username or u.password:
            return dict(base, decision="HOLD_EXTERNAL_ORGANIZER_LINK")
    def ev(role):
        return dict(source="https://www.tainex.com.tw/event/"+a,
                    observed_at=observed_at, role=role,
                    decision="REVIEW_ONLY_NOT_FORMAL_FIELD")
    base["provenance"] = {
        "exhibitionPeriod": ev("EXHIBITION_PERIOD_NOT_SESSION_START"),
        "hall": ev("VENUE_HALL"),
        "venue": ev("VENUE_FLOOR_AREA"),
        "organizerLink": ev("ORGANIZER_REFERENCE_NOT_TICKET_ID")
    }
    return dict(base, decision="REVIEW_EXACT_VENUE_LIST_DETAIL_ROLES_NO_PROMOTION")

if __name__ == "__main__":
    raise SystemExit("NO_DIRECT_EXECUTION: offline identity only, no publication")
