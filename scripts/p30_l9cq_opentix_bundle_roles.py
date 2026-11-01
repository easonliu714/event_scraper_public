"""P30-L9-CQ: OPENTIX #05 Event ID vs two distinct ticketpackage IDs.
Observed first-party public pages, REVIEW only. Never infer ticket sessions or availability.
"""
from datetime import date
from urllib.parse import urlsplit

EVENT = "https://www.opentix.life/event/2087017782302437377"
PACKAGE20 = "https://www.opentix.life/ticketpackage/2095777341620084737"
PACKAGE50 = "https://www.opentix.life/ticketpackage/2095778377743265793"
TITLE = "極致藝術《海象莫雷的漂流日誌》親子音樂劇"
SALE_START = "2026-09-10"
SALE_END = "2027-01-17"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CQ", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("event_url"), EVENT):
        return dict(out, decision="HOLD_CANONICAL_EVENT_URL")
    if x.get("event_title") != TITLE or x.get("event_id") != "2087017782302437377":
        return dict(out, decision="HOLD_EVENT_ID_TITLE")
    if not all((exact_url(x.get("package20_href"), PACKAGE20),
                exact_url(x.get("package20_detail"), PACKAGE20),
                exact_url(x.get("package50_href"), PACKAGE50),
                exact_url(x.get("package50_detail"), PACKAGE50))):
        return dict(out, decision="HOLD_TWO_DISTINCT_DIRECT_PACKAGE_LINKS")
    if (x.get("package20_threshold"), x.get("package20_discount"),
        x.get("package50_threshold"), x.get("package50_discount")) != (20, 75, 50, 70):
        return dict(out, decision="HOLD_PACKAGE_THRESHOLD_DISCOUNT")
    if (x.get("event_page_sale_start"), x.get("event_page_sale_end")) != (SALE_START, SALE_END):
        return dict(out, decision="HOLD_EVENT_PAGE_SALE_ROLE")
    if x.get("package_is_ticket_session") is not False or x.get("sale_window_is_showtime") is not False:
        return dict(out, decision="HOLD_PACKAGE_OR_SALE_ROLE_PROMOTION")
    if any(x.get(k) is not None for k in ("ticket_session_id", "ticket_session_price",
                                         "inventory", "published_event", "ticket_button_href")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    out["candidateFields"] = [
        {"field": "ticket_event_id", "value": "2087017782302437377", "source": "OPENTIX_05",
         "source_url": EVENT, "observed_at": observed_at, "role": "EVENT_ID_NOT_SESSION", "decision": "REVIEW"},
        {"field": "package20_id", "value": "2095777341620084737", "source": "OPENTIX_05",
         "source_url": PACKAGE20, "observed_at": observed_at, "role": "PACKAGE_20_NOT_EVENT_OR_SESSION", "decision": "REVIEW"},
        {"field": "package50_id", "value": "2095778377743265793", "source": "OPENTIX_05",
         "source_url": PACKAGE50, "observed_at": observed_at, "role": "PACKAGE_50_NOT_EVENT_OR_SESSION", "decision": "REVIEW"},
        {"field": "package_sale_window", "value": [SALE_START, SALE_END], "source": "OPENTIX_05",
         "source_url": EVENT, "observed_at": observed_at, "role": "EVENT_PAGE_PACKAGE_SALE_NOT_SHOWTIME", "decision": "REVIEW"}]
    return dict(out, decision="REVIEW_EVENT_AND_TWO_PACKAGE_IDS_HOLD_TICKET_SESSIONS")
