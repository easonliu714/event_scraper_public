"""P30-VENUE-02BJ: NTPC Art Center hall bulletin → multi-venue OPENTIX Event.
Source-bound REVIEW only. Quarantine incorrect printed weekdays; no session inference.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.culture.ntpc.gov.tw/artcenter_chi/sitesearch"
DETAIL = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168"
TICKET = "https://www.opentix.life/event/2086734015886159873"
VENUE_TITLE = "《屁屁偵探》南方島嶼的神秘遺跡"
TICKET_TITLE = "銀河谷音劇團《屁屁偵探》南方島嶼的神秘遺跡"
VENUE = "新北市藝文中心演藝廳"
SHOWS = ("2026-11-07T14:30", "2026-11-08T10:30", "2026-11-08T14:30")
# Printed 11/10(日) and 11/20(六) conflict with 2026 calendar Tue/Fri.
CONFLICTS = (("2026-11-10", "日"), ("2026-11-20", "六"))
WEEKDAY = "一二三四五六日"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BJ", "acceptedFields": 0,
           "ticketSessionIdsVerified": 0, "goldenAccepted": 0,
           "published": False, "candidateFields": [], "quarantinedRows": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("venue_list_url"), LIST):
        return dict(out, decision="HOLD_VENUE_LIST")
    if not exact_url(x.get("venue_detail_url"), DETAIL):
        return dict(out, decision="HOLD_VENUE_DETAIL")
    if x.get("venue_bulletin_sid") != "0Q152372523738311866" or x.get("venue_title") != VENUE_TITLE:
        return dict(out, decision="HOLD_BULLETIN_ID_TITLE")
    if tuple(x.get("show_rows") or ()) != SHOWS:
        return dict(out, decision="HOLD_THREE_VENUE_SHOW_ROWS")
    if (x.get("venue") != VENUE or x.get("ticket_venue") != VENUE
            or x.get("ticket_title") != TICKET_TITLE):
        return dict(out, decision="HOLD_VENUE_TICKET_TITLE")
    if not exact_url(x.get("venue_ticket_href"), TICKET) or not exact_url(x.get("ticket_event_url"), TICKET):
        return dict(out, decision="HOLD_DIRECT_OPENTIX_EDGE")
    if x.get("ticket_event_id") != "2086734015886159873":
        return dict(out, decision="HOLD_OPENTIX_EVENT_ID")
    if x.get("ticket_is_multivenue") is not True or x.get("ticket_venue_count") != 9:
        return dict(out, decision="HOLD_MULTIVENUE_EVENT_SCOPE")
    if tuple(tuple(z) for z in (x.get("weekday_conflicts") or ())) != CONFLICTS:
        return dict(out, decision="HOLD_WEEKDAY_EVIDENCE")
    for day, printed in CONFLICTS:
        if WEEKDAY[date.fromisoformat(day).weekday()] == printed:
            return dict(out, decision="HOLD_WEEKDAY_EVIDENCE")
    if x.get("quarantine_weekday_mismatches") is not True or x.get("bulk_accept_all_bulletin_rows") is not False:
        return dict(out, decision="HOLD_WEEKDAY_QUARANTINE")
    if x.get("ticket_show_rows_verified") is not False:
        return dict(out, decision="HOLD_TICKET_SHOW_NOT_VERIFIED")
    if any(x.get(k) is not None for k in ("ticket_session_ids", "inventory", "checkout",
                                         "published_event", "other_venue_as_same_session")):
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_OR_CROSS_VENUE")
    def candidate(field, value, source, url, role):
        return {"field": field, "value": value, "source": source,
                "source_url": url, "observed_at": observed_at, "role": role,
                "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("bulletin_sid", x["venue_bulletin_sid"], "NTPC_ARTCENTER_OFFICIAL", DETAIL, "BULLETIN_NOT_EVENT"),
        candidate("show_rows", list(SHOWS), "NTPC_ARTCENTER_OFFICIAL", DETAIL, "VENUE_SHOW_CANDIDATES"),
        candidate("ticket_event_id", x["ticket_event_id"], "OPENTIX_05", TICKET, "MULTIVENUE_EVENT_NOT_SESSION"),
        candidate("ticket_venue", VENUE, "OPENTIX_05", TICKET, "VENUE_NOT_SESSION"),
        candidate("printed_weekday_conflicts", list(CONFLICTS), "NTPC_ARTCENTER_OFFICIAL", DETAIL, "QUARANTINED_NOT_SHOW"),
    ]
    out["quarantinedRows"] = [{"date": day, "printed": printed, "calendar": WEEKDAY[date.fromisoformat(day).weekday()]}
                              for day, printed in CONFLICTS]
    return dict(out, decision="REVIEW_NTPC_MULTIVENUE_EVENT_HOLD_WEEKDAY_AND_SESSIONS")
