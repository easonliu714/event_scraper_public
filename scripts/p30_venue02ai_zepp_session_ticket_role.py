#!/usr/bin/env python3
"""P30-VENUE-02AI: Zepp New Taipei official same-rid session evidence.

List advertises one START time; same-rid detail explicitly names two
showings. A venue-to-TicketPlus link is NOT verified ticket event identity,
and '購票網址｜網頁建置中' must not be silently overwritten by the link.
"""
import hashlib
import re
from datetime import date
from urllib.parse import urlsplit, parse_qs

SOURCE = "Zepp New Taipei P0 venue"
INDEX_URL = "https://www.zepp.co.jp/hall/newtaipei/schedule/"
HOLD = "HARD_HOLD_NO_PUBLICATION"
RID = re.compile(r"^[0-9]{5,9}$")
TICKET_ID = re.compile(r"^[a-f0-9]{32}$")
TIME = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def detail_rid(url):
    if not isinstance(url, str):
        return None
    try:
        p = urlsplit(url)
        q = parse_qs(p.query, keep_blank_values=True)
    except ValueError:
        return None
    if (p.scheme != "https" or p.netloc != "www.zepp.co.jp"
            or p.path != "/hall/newtaipei/schedule/single/"
            or p.fragment or set(q) != {"rid"} or len(q["rid"]) != 1):
        return None
    return q["rid"][0] if RID.fullmatch(q["rid"][0]) else None

def ticket_shape(url):
    if not isinstance(url, str):
        return False
    try:
        p = urlsplit(url)
    except ValueError:
        return False
    return (p.scheme == "https" and p.netloc == "ticketplus.com.tw"
            and not p.query and not p.fragment
            and p.path.startswith("/activity/")
            and bool(TICKET_ID.fullmatch(p.path[len("/activity/"):])))

def inspect(index, detail):
    out = {"gate": "P30-VENUE-02AI", "source": SOURCE,
           "candidateProvenance": [], "acceptedFields": 0,
           "goldenAccepted": 0, "published": False, "ticketEventId": None,
           "ticketIdentityVerified": False, "releaseState": HOLD,
           "officialGETinCI": 0}
    if not isinstance(index, dict) or not isinstance(detail, dict):
        return dict(out, decision="HOLD_UNSTRUCTURED_SOURCE")
    rid = detail_rid(index.get("detail_url"))
    if (index.get("index_url") != INDEX_URL or rid is None
            or detail.get("url") != index.get("detail_url")
            or detail_rid(detail.get("url")) != rid
            or index.get("title") != detail.get("title")
            or not isinstance(index.get("title"), str)
            or len(index["title"]) < 8):
        return dict(out, decision="HOLD_LIST_DETAIL_IDENTITY")
    try:
        day = date.fromisoformat(index["day"])
    except (KeyError, ValueError, TypeError):
        return dict(out, decision="HOLD_INVALID_EVENT_DATE")
    if (detail.get("day") != day.isoformat()
            or not TIME.fullmatch(index.get("start_time", ""))
            or not TIME.fullmatch(detail.get("header_start", ""))):
        return dict(out, decision="HOLD_INDEX_DETAIL_DATE_OR_START")
    sessions = detail.get("sessions")
    if (not isinstance(sessions, list) or len(sessions) != 2
            or any(not isinstance(s, dict) for s in sessions)):
        return dict(out, decision="HOLD_NOT_EXACT_TWO_EXPLICIT_SESSIONS")
    times = []
    for s in sessions:
        t = s.get("time")
        if (not isinstance(t, str) or not TIME.fullmatch(t)
                or s.get("label") != t + "場次"
                or not isinstance(s.get("performer"), str)
                or not s["performer"].strip()):
            return dict(out, decision="HOLD_SESSION_LABEL_OR_TIME")
        times.append(t)
    if (len(set(times)) != 2 or index["start_time"] not in times
            or detail["header_start"] != index["start_time"]):
        return dict(out, decision="HOLD_DUPLICATE_OR_INDEX_SESSION_MISMATCH")
    if detail.get("venue") != "Zepp New Taipei":
        return dict(out, decision="HOLD_VENUE_NOT_SOURCE_BOUND")
    if not ticket_shape(detail.get("ticket_url")):
        return dict(out, decision="HOLD_TICKET_URL_NOT_ALLOWLISTED")
    if detail.get("ticket_title_verified") is not False:
        return dict(out, decision="HOLD_TICKET_EVENT_IDENTITY_UNPROVEN")
    if detail.get("body_ticket_url_status") != "網頁建置中":
        return dict(out, decision="HOLD_TICKET_BODY_STATUS_NOT_VERIFIED")
    stamp = index.get("observed_at")
    if not isinstance(stamp, str) or not re.fullmatch(r"20\d\d-\d\d-\d\d", stamp):
        return dict(out, decision="HOLD_OBSERVATION_DATE")
    for role, value in (
        ("VENUE_EVENT_TITLE", detail["title"]),
        ("VENUE_EVENT_DAY", day.isoformat()),
        ("VENUE_SESSION_1", times[0]),
        ("VENUE_SESSION_2", times[1]),
        ("VENUE_TICKET_LINK_UNVERIFIED", detail["ticket_url"]),
        ("VENUE_TICKET_BODY_STATUS", detail["body_ticket_url_status"])):
        out["candidateProvenance"].append({
            "source": SOURCE, "source_url": detail["url"],
            "source_rid": rid, "observed_at": stamp,
            "role": role, "decision": "REVIEW_NOT_FORMALLY_ACCEPTED",
            "valueSHA256": digest(value)})
    out["sameRidTitleMatch"] = True
    out["explicitSessionCount"] = 2
    out["indexStartCoversOnlyOneSession"] = True
    out["ticketLinkShapeValid"] = True
    return dict(out, decision="HOLD_TWO_SESSIONS_TICKET_DETAIL_AND_BODY_STATUS_UNVERIFIED")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
