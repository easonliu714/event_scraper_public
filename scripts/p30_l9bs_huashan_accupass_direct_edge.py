#!/usr/bin/env python3
"""L9-BS: direct official Huashan -> ACCUPASS link and field conflict receipt.

Consumes source-extracted, explicitly attributed evidence only; no GET, raw
HTML persistence, event creation, field acceptance, or publication.
"""
import hashlib
import re
from datetime import date
from urllib.parse import urlsplit
from p30_l9bn_huashan_card_identity import classify_href

HOLD = "HARD_HOLD_NO_PUBLICATION"
VENUE_SOURCE = "HUASHAN_PLATFORM_13"
TICKET_SOURCE = "ACCUPASS_PLATFORM_02"
TIME = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")
TICKET_PATH = re.compile(r"/event/[0-9]{12,24}")

def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def ticket_url_ok(url):
    try:
        u = urlsplit(url)
        return (u.scheme == "https" and u.hostname == "www.accupass.com"
                and u.port is None and not u.username and not u.password
                and not u.query and not u.fragment
                and bool(TICKET_PATH.fullmatch(u.path)) and u.geturl() == url)
    except (ValueError, TypeError):
        return False

def audit(venue, ticket):
    out = {"gate": "P30-L9-BS", "source": VENUE_SOURCE,
           "linkedTicketSource": TICKET_SOURCE, "directLinkBound": False,
           "sameSession": False, "sameCoreTitle": False,
           "venueConflict": None, "candidateProvenance": [],
           "acceptedFields": 0, "goldenAccepted": 0, "published": False,
           "ticketEventId": None, "releaseState": HOLD}
    if venue.get("source") != VENUE_SOURCE or ticket.get("source") != TICKET_SOURCE:
        return dict(out, decision="HOLD_SOURCE_ROLE")
    vurl, turl = venue.get("url"), ticket.get("url")
    if not isinstance(vurl, str) or not isinstance(turl, str):
        return dict(out, decision="HOLD_MISSING_SOURCE_URL")
    kind, normalized = classify_href(vurl)
    if normalized != vurl or not vurl.startswith("https://www.huashan1914.com/exhibition/"):
        return dict(out, decision="HOLD_VENUE_DETAIL_URL")
    if not ticket_url_ok(turl) or venue.get("ticketLinks") != [turl]:
        return dict(out, decision="HOLD_TICKET_URL_NOT_UNIQUE_DIRECT")
    out["directLinkBound"] = True
    core = venue.get("coreTitle")
    if (not isinstance(core, str) or len(core) < 12
            or core != ticket.get("coreTitle")
            or core not in venue.get("heading", "")
            or core not in ticket.get("heading", "")):
        return dict(out, decision="HOLD_CROSS_SOURCE_TITLE_CORE")
    out["sameCoreTitle"] = True
    if any(not isinstance(x.get("observed_at"), str) or
           not re.fullmatch(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ", x["observed_at"])
           for x in (venue, ticket)):
        return dict(out, decision="HOLD_OBSERVATION_PROVENANCE")
    for source in (venue, ticket):
        try:
            date.fromisoformat(source["eventDate"])
        except (KeyError, TypeError, ValueError):
            return dict(out, decision="HOLD_DATE_ROLE_INVALID")
        if source.get("dateRole") != "EVENT_SESSION":
            return dict(out, decision="HOLD_DATE_ROLE_NOT_EVENT_SESSION")
        if not all(isinstance(source.get(k), str) and TIME.fullmatch(source[k])
                   for k in ("start", "end")):
            return dict(out, decision="HOLD_SESSION_CLOCK_INVALID")
        if source["start"] >= source["end"] or source.get("timezone") != "Asia/Taipei":
            return dict(out, decision="HOLD_SESSION_CHRONOLOGY_OR_TIMEZONE")
    if any(venue[k] != ticket[k] for k in ("eventDate", "start", "end", "timezone")):
        return dict(out, decision="HOLD_SESSION_CROSS_SOURCE_MISMATCH")
    out["sameSession"] = True
    for source in (venue, ticket):
        for role, key in (("EVENT_DATE", "eventDate"), ("SESSION_START", "start"),
                          ("SESSION_END", "end"), ("VENUE_ROOM", "room")):
            value = source.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                return dict(out, decision="HOLD_MISSING_OR_OVERSIZED_FIELD")
            out["candidateProvenance"].append({
                "source": source["source"], "observed_at": source["observed_at"],
                "role": role, "decision": "REVIEW_CANDIDATE_NOT_ACCEPTED",
                "valueSHA256": sha(value)})
    out["venueConflict"] = venue["room"] != ticket["room"]
    if out["venueConflict"]:
        return dict(out, decision="HOLD_DIRECT_LINK_SESSION_MATCH_VENUE_ROOM_CONFLICT")
    return dict(out, decision="REVIEW_DIRECT_LINK_SESSION_AND_ROOM_NO_FORMAL_FIELDS")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
