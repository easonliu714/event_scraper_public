"""P30-L9-CU: tixCraft #03 same-activity detail/game role guard.
Public-source REVIEW evidence only; no GET/login/ticket inventory in CI.
"""
from datetime import date
from urllib.parse import urlsplit

DETAIL = "https://tixcraft.com/activity/detail/26_aftp"
GAME = "https://tixcraft.com/activity/game/26_aftp"
TITLE = "凱基金控xAccusefive告五人 [在這裡 @century] 世界巡迴演唱會"
SHOWS = ("2026-11-06T19:30", "2026-11-07T19:30", "2026-11-08T19:30")
RELEASE = "2026-11-01T11:00"
PRICES = (3850, 3250, 2950, 2450, 1950, 1550, 800)

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CU", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("detail_url"), DETAIL):
        return dict(out, decision="HOLD_DETAIL_URL")
    if not exact_url(x.get("game_url"), GAME):
        return dict(out, decision="HOLD_GAME_URL")
    if x.get("detail_activity_id") != "26_aftp" or x.get("game_activity_id") != "26_aftp":
        return dict(out, decision="HOLD_SAME_ACTIVITY_ID")
    if x.get("detail_title") != TITLE or x.get("game_title") != TITLE:
        return dict(out, decision="HOLD_TITLE_PARITY")
    if tuple(x.get("game_show_rows") or ()) != SHOWS:
        return dict(out, decision="HOLD_THREE_DISTINCT_SHOW_ROWS")
    if x.get("release_at") != RELEASE or x.get("release_is_show") is not False:
        return dict(out, decision="HOLD_RELEASE_NOT_SHOW")
    if tuple(x.get("descriptive_prices") or ()) != PRICES or x.get("accessible_price") != 400:
        return dict(out, decision="HOLD_PRICE_SCOPE")
    if x.get("accessible_is_general") is not False or x.get("price_is_inventory") is not False:
        return dict(out, decision="HOLD_PRICE_ELIGIBILITY_OR_INVENTORY")
    if any(x.get(k) is not None for k in ("ticket_session_ids", "inventory", "checkout",
                                         "published_event", "game_response_private")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    def candidate(field, value, url, role):
        return {"field": field, "value": value, "source": "TIXCRAFT_03",
                "source_url": url, "observed_at": observed_at, "role": role,
                "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("activity_id", "26_aftp", DETAIL, "EVENT_NOT_SESSION"),
        candidate("show_rows", list(SHOWS), GAME, "THREE_PERFORMANCES"),
        candidate("release_at", RELEASE, DETAIL, "RELEASE_NOT_SHOW"),
        candidate("descriptive_prices", list(PRICES), DETAIL, "PRICE_BANDS_NOT_INVENTORY"),
        candidate("accessible_price", 400, DETAIL, "ELIGIBILITY_ONLY_NOT_GENERAL"),
    ]
    return dict(out, decision="REVIEW_TIXCRAFT_THREE_SHOWS_RELEASE_HOLD_SESSIONS")
