"""P30-L9-CS: source-bound iNDIEVOX Bridge Dog LIST→DETAIL→GAME; prices vs time roles.

Read-only evidence candidate gate. No purchase, availability, session or production write.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.indievox.com/activity"
DETAIL = "https://www.indievox.com/activity/detail/26_iv0425761"
GAME = "https://www.indievox.com/activity/game/26_iv0425761"
TITLE = "南半球的夢幻女聲 Bridge Dog 台北演唱會"
SHOW = "2026-11-12T19:30"
ADMISSION = "2026-11-12T19:00"
SALE_START = "2026-10-14T11:00"
REFUND = "2026-11-02"
VENUE = "野地方 Wildlab"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CS", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("list_url"), LIST):
        return dict(out, decision="HOLD_CANONICAL_LIST")
    if not exact_url(x.get("list_detail_href"), DETAIL) or not exact_url(x.get("detail_url"), DETAIL):
        return dict(out, decision="HOLD_LIST_DETAIL_ID")
    if not exact_url(x.get("detail_game_href"), GAME) or not exact_url(x.get("game_url"), GAME):
        return dict(out, decision="HOLD_DETAIL_GAME_ID")
    if (x.get("event_path_id"), x.get("list_title"), x.get("detail_title"), x.get("game_title")) != (
        "26_iv0425761", TITLE, TITLE, TITLE):
        return dict(out, decision="HOLD_SAME_ID_TITLE")
    if (x.get("detail_show"), x.get("game_show"), x.get("detail_venue"),
        x.get("game_venue")) != (SHOW, SHOW, VENUE, "野地方"):
        return dict(out, decision="HOLD_GAME_SHOW_VENUE")
    if x.get("admission_open") != ADMISSION or x.get("admission_is_show") is not False:
        return dict(out, decision="HOLD_ADMISSION_SHOW_ROLE")
    if (x.get("presale_price"), x.get("door_price"), x.get("door_price_is_inventory")) != (1250, 1500, False):
        return dict(out, decision="HOLD_PRESALE_DOOR_PRICE_ROLE")
    if x.get("sale_start") != SALE_START or x.get("sale_is_show") is not False:
        return dict(out, decision="HOLD_SALE_ROLE")
    if x.get("refund_deadline") != REFUND or x.get("refund_is_show") is not False:
        return dict(out, decision="HOLD_REFUND_ROLE")
    if x.get("presale_end_exact") is not None or x.get("door_sales_guaranteed") is not False:
        return dict(out, decision="HOLD_CONDITIONAL_SALE_POLICY")
    if x.get("game_button_is_inventory") is not False:
        return dict(out, decision="HOLD_GAME_BUTTON_ROLE")
    if any(x.get(k) is not None for k in ("ticket_session_id", "ticket_inventory",
                                          "verified_checkout_url", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    def candidate(field, value, url, role):
        return {"field": field, "value": value, "source": "INDIEVOX_18",
                "source_url": url, "observed_at": observed_at, "role": role, "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("event_path_id", "26_iv0425761", DETAIL, "EVENT_NOT_TICKET_SESSION"),
        candidate("showtime", SHOW, GAME, "DESCRIPTIVE_SHOWTIME"),
        candidate("admission_open", ADMISSION, DETAIL, "ADMISSION_NOT_SHOW"),
        candidate("price_tiers", {"presale": 1250, "door": 1500}, DETAIL, "DESCRIPTIVE_PRICE_NOT_AVAILABILITY"),
        candidate("sale_start", SALE_START, DETAIL, "SALE_START_NOT_SHOW"),
        candidate("refund_deadline", REFUND, DETAIL, "REFUND_NOT_SHOW")]
    return dict(out, decision="REVIEW_BRIDGE_DOG_PRICE_ADMISSION_SALE_REFUND_HOLD_SESSION")
