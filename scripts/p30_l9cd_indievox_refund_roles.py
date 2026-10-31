"""P30-L9-CD: canonical iNDIEVOX #18 public detail/game same-ID role audit.

Only bounded, independently observed public evidence; no network or publication.
"""
import datetime
import hashlib
import re
from urllib.parse import urlsplit

EVENT_ID = "26_iv0424581"
DETAIL_URL = "https://www.indievox.com/activity/detail/" + EVENT_ID
GAME_URL = "https://www.indievox.com/activity/game/" + EVENT_ID
TITLE = "2026 魏品勻 David Wei 《還好我們都被生出來了》 Full Band 發片專場"
VENUE = "凝聚力展演空間"
PERFORMANCE = ("2026-12-12", "19:30")
DOOR_TIME = "19:00"
PRICE_TIERS = (("PRESALE", 850), ("AT_DOOR_CONDITIONAL", 900))
SALE_START = "2026-10-20 12:00"
PRESALE_END = "2026-12-11 23:59"
REFUND_CUTOFF = "2026-12-02"
REFUND_NO_ACCEPT_FROM = "2026-11-03"

def _exact(url, kind):
    if not isinstance(url, str):
        return False
    try:
        u = urlsplit(url)
        return (u.scheme, u.netloc, u.path, u.query, u.fragment) == (
            "https", "www.indievox.com", "/activity/" + kind + "/" + EVENT_ID, "", "")
    except ValueError:
        return False

def inspect(detail, game, observed_at):
    out = dict(gate="P30-L9-CD", source="INDIEVOX_CANONICAL_18",
               acceptedFields=0, goldenAccepted=0, published=False,
               candidateProvenance=[], ticketSessionIdVerified=False,
               inventoryVerified=False)
    try:
        if not isinstance(observed_at, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except ValueError:
        return dict(out, decision="HOLD_OBSERVED_AT")
    if not _exact(detail.get("url"), "detail") or not _exact(game.get("url"), "game"):
        return dict(out, decision="HOLD_SAME_EVENT_PATH_ID")
    if detail.get("title") != TITLE or game.get("title") != TITLE:
        return dict(out, decision="HOLD_SAME_EVENT_TITLE")
    if detail.get("venue") != VENUE or game.get("venue") != VENUE:
        return dict(out, decision="HOLD_VENUE_PARITY")
    if tuple(detail.get("performance", ())) != PERFORMANCE or tuple(game.get("performance", ())) != PERFORMANCE:
        return dict(out, decision="HOLD_PERFORMANCE_PARITY")
    if detail.get("door_time") != DOOR_TIME:
        return dict(out, decision="HOLD_DOOR_NOT_SHOWTIME")
    if tuple(map(tuple, detail.get("price_tiers", []))) != PRICE_TIERS:
        return dict(out, decision="HOLD_PRICE_TIER_ROLES")
    if detail.get("sale_start") != SALE_START or detail.get("presale_end") != PRESALE_END:
        return dict(out, decision="HOLD_SALE_PERIOD_NOT_PERFORMANCE")
    if detail.get("refund_cutoff") != REFUND_CUTOFF or detail.get("refund_no_accept_from") != REFUND_NO_ACCEPT_FROM:
        return dict(out, decision="HOLD_REFUND_SOURCE_EVIDENCE")
    if game.get("action") != "Start ordering":
        return dict(out, decision="HOLD_GAME_ACTION_ROLE")
    if any(x is not None for x in (
        game.get("ticket_session_id"), game.get("inventory"),
        game.get("checkout_price"), detail.get("ticket_session_id"))):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION_OR_INVENTORY")
    evidence = (
        ("DETAIL", DETAIL_URL, "EVENT_ID_NOT_TICKET_SESSION", EVENT_ID),
        ("DETAIL", DETAIL_URL, "TITLE", TITLE),
        ("GAME", GAME_URL, "SAME_EVENT_TITLE", TITLE),
        ("GAME", GAME_URL, "DATED_GAME_ROW_NOT_SESSION_ID", repr(PERFORMANCE)),
        ("DETAIL", DETAIL_URL, "DOOR_TIME_NOT_PERFORMANCE", DOOR_TIME),
        ("DETAIL", DETAIL_URL, "VENUE", VENUE),
        ("DETAIL", DETAIL_URL, "PRESALE_AND_CONDITIONAL_AT_DOOR_PRICE", repr(PRICE_TIERS)),
        ("DETAIL", DETAIL_URL, "SALE_START_NOT_EVENT_DATE", SALE_START),
        ("DETAIL", DETAIL_URL, "PRESALE_END_NOT_EVENT_DATE", PRESALE_END),
        ("DETAIL", DETAIL_URL, "REFUND_CUTOFF_CLAIM", REFUND_CUTOFF),
        ("DETAIL", DETAIL_URL, "CONFLICTING_NO_REFUND_FROM_CLAIM", REFUND_NO_ACCEPT_FROM),
    )
    for src, url, role, value in evidence:
        out["candidateProvenance"].append(dict(source=src, source_url=url,
            observed_at=observed_at, role=role,
            valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    # Same official detail has contradictory refund cutoff text. Do not choose one.
    return dict(out, decision="HOLD_REFUND_DEADLINE_CONTRADICTION_AND_NO_TICKET_SESSION_ID")
