"""P30-VENUE-02BB: Zepp 2026-11-01 exact rid to Ticket Plus href; JS detail HOLD.

Source-bound evidence-only; never treat venue ticket-platform claim or JS shell as a ticket session.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.zepp.co.jp/hall/newtaipei/"
DETAIL = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=163838"
TICKET = "https://ticketplus.com.tw/activity/993e73c01ab8d4c4380cc62bf1f203fe"
TITLE = "JUST YOU & WIN 1ST SOLO FAN MEETING IN TAIPEI"
SHOW = "2026-11-01T18:30"
SALE = "2026-09-05T14:00"
BENEFIT = "2026-10-16T23:59"
TIERS = (8500, 8000, 7000, 6500, 4500, 4000, 3500, 2500, 1500)

def _exact(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BB", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": [], "provenance": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not _exact(x.get("list_url"), LIST):
        return dict(out, decision="HOLD_ZEPP_LIST_URL")
    if not _exact(x.get("list_detail_href"), DETAIL) or not _exact(x.get("detail_url"), DETAIL):
        return dict(out, decision="HOLD_ZEPP_RID_DETAIL")
    if x.get("list_title") != TITLE or x.get("detail_title") != TITLE or x.get("rid") != "163838":
        return dict(out, decision="HOLD_ZEPP_TITLE_RID")
    if not _exact(x.get("detail_ticket_href"), TICKET):
        return dict(out, decision="HOLD_TICKETPLUS_DIRECT_HREF")
    if x.get("ticket_platform_label") != "Ticket Plus" or x.get("venue_text_ticket_url_status") != "網頁建置中":
        return dict(out, decision="HOLD_VENUE_TICKET_ROLE_CONFLICT")
    if x.get("ticket_response_kind") != "JS_SHELL_WITHOUT_EVENT_DETAIL":
        return dict(out, decision="HOLD_TICKETPLUS_JS_DETAIL_UNVERIFIED")
    if (x.get("show_datetime"), x.get("sale_start"), x.get("benefit_cutoff"), x.get("product_price_tiers")) != (SHOW, SALE, BENEFIT, TIERS):
        return dict(out, decision="HOLD_PERFORMANCE_SALE_BENEFIT_PRICE_ROLES")
    if any(x.get(k) is not None for k in ("ticket_event_id", "ticket_session_id", "ticket_session_price",
                                          "inventory", "published_event")):
        return dict(out, decision="HOLD_TICKET_SESSION_PROMOTION")
    out["candidateFields"] = [
        {"field": k, "value": v, "source": "ZEPP_NEW_TAIPEI_VENUE", "source_url": DETAIL,
         "observed_at": observed_at, "role": role, "decision": "REVIEW"}
        for k, v, role in (
            ("performance_datetime", SHOW, "VENUE_SHOW_START"),
            ("product_price_tiers", TIERS, "VENUE_PRODUCT_TIERS_NOT_SESSION_PRICE"),
            ("sale_start", SALE, "VENUE_CLAIMED_SALE_START_NOT_SHOW"),
            ("benefit_cutoff", BENEFIT, "PROMOTION_ELIGIBILITY_NOT_SALE_OR_SHOW"),
            ("ticket_link", TICKET, "VENUE_DIRECT_HREF_NOT_VERIFIED_TICKET_EVENT"))]
    out["provenance"] = [
        {"source": "ZEPP_NEW_TAIPEI_VENUE", "source_url": DETAIL, "observed_at": observed_at,
         "role": "RID_163838_VENUE_DETAIL_AND_TICKET_HREF", "decision": "REVIEW"},
        {"source": "TICKETPLUS_19_CANONICAL", "source_url": TICKET, "observed_at": observed_at,
         "role": "PUBLIC_JS_APP_SHELL_NOT_EVENT_DETAIL", "decision": "HOLD_TICKETPLUS_JS_DETAIL_UNVERIFIED"}]
    return dict(out, decision="REVIEW_VENUE_HREF_HOLD_TICKETPLUS_JS_DETAIL_AND_SESSION")
