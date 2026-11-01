"""P30-L9-CR: iNDIEVOX #18 public LIST→same-ID DETAIL→GAME role boundary.

Source-bound REVIEW evidence, not a production scraper, ticket Session ID or release.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.indievox.com/activity"
DETAIL = "https://www.indievox.com/activity/detail/26_iv04215c4"
GAME = "https://www.indievox.com/activity/game/26_iv04215c4"
TITLE = "青虫aoi 2026 冬季小巡迴《Before Sunrise》高雄場"
SHOW = "2026-11-08T19:30"
REFUND_CUTOFF = "2026-10-29"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CR", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("list_url"), LIST):
        return dict(out, decision="HOLD_CANONICAL_LIST")
    if not exact_url(x.get("list_detail_href"), DETAIL) or not exact_url(x.get("detail_url"), DETAIL):
        return dict(out, decision="HOLD_LIST_TO_DETAIL_LINK")
    if not exact_url(x.get("detail_game_href"), GAME) or not exact_url(x.get("game_url"), GAME):
        return dict(out, decision="HOLD_DETAIL_TO_GAME_LINK")
    if (x.get("event_path_id"), x.get("list_title"), x.get("detail_title"), x.get("game_title")) != (
            "26_iv04215c4", TITLE, TITLE, TITLE):
        return dict(out, decision="HOLD_SAME_ID_TITLE_PARITY")
    if (x.get("detail_show"), x.get("game_row_show"), x.get("detail_venue"),
        x.get("game_row_venue")) != (SHOW, SHOW, "LIVE WAREHOUSE 小庫", "LIVE WAREHOUSE"):
        return dict(out, decision="HOLD_SHOWTIME_VENUE_LOCAL_PARITY")
    if x.get("refund_deadline") != REFUND_CUTOFF or x.get("refund_is_showtime") is not False:
        return dict(out, decision="HOLD_REFUND_DATE_ROLE")
    if x.get("pickup_fee_ibon") != 30 or x.get("pickup_fee_e_ticket") != 10 or x.get("fees_are_ticket_prices") is not False:
        return dict(out, decision="HOLD_PICKUP_FEE_ROLE")
    if x.get("game_button_is_availability") is not False:
        return dict(out, decision="HOLD_GAME_BUTTON_ROLE")
    if any(x.get(k) is not None for k in ("ticket_session_id", "ticket_session_price",
                                         "inventory", "checkout_url", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    out["candidateFields"] = [
        {"field": "event_identity", "value": "26_iv04215c4", "source": "INDIEVOX_18",
         "source_url": DETAIL, "observed_at": observed_at, "role": "EVENT_PATH_ID_NOT_TICKET_SESSION", "decision": "REVIEW"},
        {"field": "showtime", "value": SHOW, "source": "INDIEVOX_18",
         "source_url": GAME, "observed_at": observed_at, "role": "GAME_ROW_DESCRIPTIVE_SHOWTIME", "decision": "REVIEW"},
        {"field": "refund_deadline", "value": REFUND_CUTOFF, "source": "INDIEVOX_18",
         "source_url": DETAIL, "observed_at": observed_at, "role": "REFUND_CUTOFF_NOT_SHOWTIME", "decision": "REVIEW"},
        {"field": "pickup_fees", "value": [30, 10], "source": "INDIEVOX_18",
         "source_url": DETAIL, "observed_at": observed_at, "role": "PICKUP_FEES_NOT_TICKET_PRICE", "decision": "REVIEW"}]
    return dict(out, decision="REVIEW_SAME_ID_GAME_ROW_REFUND_ROLE_HOLD_TICKET_SESSION")
