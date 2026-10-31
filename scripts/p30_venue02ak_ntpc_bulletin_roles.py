#!/usr/bin/env python3
"""P30-VENUE-02AK: New Taipei Art Center monthly bulletin is not an event ID.

Official search index -> same bulletin SID. The bulletin contains multiple
performances, ticket-platform claims and one calendar weekday contradiction.
No event ID, ticket URL parity, price or formal FIELD is inferred.
"""
import datetime
import hashlib
import re

INDEX = "https://www.culture.ntpc.gov.tw/artcenter_chi/sitesearch"
SID = "0Q152372523738311866"
DETAIL = ("https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?"
          "sid=" + SID + "&sq=&xsmsid=0G269629106251547168")
HEADING = "〖演出預告〗115年11月演出節目"
HOLD = "HARD_HOLD_NO_PUBLICATION"
WEEKDAY = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6}

def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def inspect(index, detail, observed_at):
    out = dict(gate="P30-VENUE-02AK", source="New Taipei Art Center P0 venue",
               officialGETinCI=0, candidateProvenance=[], acceptedFields=0,
               goldenAccepted=0, published=False, releaseState=HOLD,
               bulletinSidNotEventId=True, verifiedTicketEventIds=0)
    if not isinstance(index, dict) or not isinstance(detail, dict):
        return dict(out, decision="HOLD_UNSTRUCTURED")
    if index.get("url") != INDEX or detail.get("url") != DETAIL:
        return dict(out, decision="HOLD_FIRST_PARTY_BULLETIN_LINK")
    if index.get("bulletin_sid") != SID or detail.get("sid") != SID:
        return dict(out, decision="HOLD_BULLETIN_SID")
    if index.get("heading") != HEADING or detail.get("heading") != HEADING:
        return dict(out, decision="HOLD_BULLETIN_TITLE_PARITY")
    if not isinstance(observed_at, str) or not re.fullmatch(r"20\d\d-\d\d-\d\d", observed_at):
        return dict(out, decision="HOLD_OBSERVED_AT")
    items = detail.get("performances")
    if not isinstance(items, list) or len(items) != 8:
        return dict(out, decision="HOLD_BULLETIN_GROUP_COUNT")
    names = set()
    conflicts = []
    for i, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("title"), str) or not item["title"].strip():
            return dict(out, decision="HOLD_GROUP_TITLE")
        if item["title"] in names:
            return dict(out, decision="HOLD_DUPLICATE_GROUP_TITLE")
        names.add(item["title"])
        if item.get("ticket_role") not in ("OPENTIX_CLAIM", "ERA_CLAIM", "SELF_SALE", "NO_TICKET", "ONLINE_CLAIM"):
            return dict(out, decision="HOLD_TICKET_ROLE")
        if item.get("ticket_event_id") is not None or item.get("price") is not None:
            return dict(out, decision="HOLD_UNVERIFIED_TICKET_ID_OR_PRICE")
        shows = item.get("shows")
        if not isinstance(shows, list) or not shows:
            return dict(out, decision="HOLD_MISSING_SHOW_ROWS")
        for show in shows:
            if not isinstance(show, tuple) or len(show) != 3:
                return dict(out, decision="HOLD_SHOW_SHAPE")
            date, time, weekday = show
            try:
                actual = datetime.date.fromisoformat(date).weekday()
            except (TypeError, ValueError):
                return dict(out, decision="HOLD_INVALID_DATE")
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time) or weekday not in WEEKDAY:
                return dict(out, decision="HOLD_INVALID_TIME_WEEKDAY")
            if actual != WEEKDAY[weekday]:
                conflicts.append(dict(group=i + 1, date=date, assertedWeekday=weekday,
                                      actualWeekday=actual))
            out["candidateProvenance"].append(dict(source=out["source"],
                source_url=DETAIL, bulletin_sid=SID, group=i + 1,
                observed_at=observed_at, role="VENUE_BULLETIN_SHOW_REVIEW",
                valueSHA256=sha("|".join(show)), decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    out["groupCount"] = len(items)
    out["calendarConflicts"] = conflicts
    return dict(out, decision="HOLD_BULLETIN_NOT_EVENT_ID_AND_WEEKDAY_CONFLICT" if conflicts
                else "HOLD_BULLETIN_NOT_EVENT_ID_NO_TICKET_PARITY")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_NETWORK")
