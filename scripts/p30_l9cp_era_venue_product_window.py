"""P30-L9-CP: New Taipei venue bulletin -> canonical ERA #08 product identity.
Evidence-only. Source text is an observed candidate, not a live scraper or ticket availability.
"""
from datetime import date, datetime
from urllib.parse import urlsplit

VENUE = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168"
TICKET = "https://ticket.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1FKLQFW"
VENUE_TITLE = "《秋意濃》"
TICKET_TITLE = "紅瓦民族舞蹈團『秋意濃』"
VENUE_SHOW = "2026-11-01T14:30"
TICKET_HEADER_START = "2026-10-31T19:30"
TICKET_HEADER_END = "2026-11-01T23:59"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CP", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("venue_bulletin"), VENUE):
        return dict(out, decision="HOLD_VENUE_BULLETIN")
    if not exact_url(x.get("venue_ticket_href"), TICKET) or not exact_url(x.get("ticket_detail"), TICKET):
        return dict(out, decision="HOLD_DIRECT_ERA_PRODUCT_LINK")
    if (x.get("venue_title"), x.get("ticket_title"), x.get("ticket_product_id")) != (VENUE_TITLE, TICKET_TITLE, "P1FKLQFW"):
        return dict(out, decision="HOLD_EXPLICIT_TITLE_PRODUCT_ID")
    if (x.get("venue_show"), x.get("ticket_header_start"), x.get("ticket_header_end")) != (VENUE_SHOW, TICKET_HEADER_START, TICKET_HEADER_END):
        return dict(out, decision="HOLD_TIME_ROLE_SOURCE_MISMATCH")
    if not (datetime.fromisoformat(TICKET_HEADER_START) < datetime.fromisoformat(TICKET_HEADER_END)):
        return dict(out, decision="HOLD_INVALID_HEADER_RANGE")
    if x.get("ticket_header_is_session") is not False:
        return dict(out, decision="HOLD_PRODUCT_HEADER_NOT_SESSION")
    if any(x.get(k) is not None for k in ("ticket_session_id", "ticket_session_price", "inventory", "ticket_button_href", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    out["candidateFields"] = [
        {"field": "venue_performance_start", "value": VENUE_SHOW, "source": "NTPC_ARTCENTER_VENUE",
         "source_url": VENUE, "observed_at": observed_at, "role": "VENUE_BULLETIN_SHOW", "decision": "REVIEW"},
        {"field": "ticket_product_id", "value": "P1FKLQFW", "source": "ERA_08",
         "source_url": TICKET, "observed_at": observed_at, "role": "TICKET_PRODUCT_NOT_SESSION", "decision": "REVIEW"},
        {"field": "ticket_header_window", "value": [TICKET_HEADER_START, TICKET_HEADER_END],
         "source": "ERA_08", "source_url": TICKET, "observed_at": observed_at,
         "role": "PRODUCT_HEADER_WINDOW_NOT_PERFORMANCE_OR_SALE", "decision": "REVIEW"}]
    return dict(out, decision="REVIEW_CROSS_SOURCE_PRODUCT_HOLD_SESSION_AND_HEADER_ROLE")
