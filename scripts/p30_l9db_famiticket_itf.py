"""P30-L9-DB: FamiTicket ITF LIST→DETAIL evidence; venue cross-source identity HOLD.

Bounded official source-reader 2026-11-02, no CI network:
  FamiTicket Home -> ITF official detail; date range is exhibition, not ticket Session.
  TaiNEX /event/709 says "旅展", not exact "2026 ITF 台灣國際旅展".
Never infer ticket Session, checkout URL, cross-source event ID or formal field PASS.
"""
from datetime import datetime
from urllib.parse import urlsplit

LIST = "https://www.famiticket.com.tw/Home"
DETAIL = "https://www.famiticket.com.tw/Home/Activity/Info/MABvAE4ALwBxAEkAcQB3ADkAawB0AHUASgBlAGwAZwA3AGkAOQBsAEwARgB2AE8ASwBTAGMAMQB5AEYAMQBOAE8AQgBBAHkAdwBaAEYAagBKAHMAawA9AA2"
VENUE_DETAIL = "https://www.tainex.com.tw/event/709"
TITLE = "2026 ITF 台灣國際旅展"
VENUE_TITLE = "旅展"
PERIOD = ("2026-11-06", "2026-11-09")

def exact_url(value, expected):
    """Reject host aliases, credentials, fragments, malformed authority and query drift."""
    if not isinstance(value, str):
        return False
    try:
        a, b = urlsplit(value), urlsplit(expected)
        return (a.scheme == b.scheme == "https" and a.netloc == b.netloc
                and a.username is None and a.password is None and a.port is None
                and a.path == b.path and a.query == b.query and not a.fragment)
    except ValueError:
        return False

def inspect(obs, observed_at):
    out = {"gate": "P30-L9-DB", "decision": "REVIEW_WITH_HOLD",
           "candidateFields": [], "acceptedFields": 0,
           "crossSourceIdentityVerified": False, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False,
           "releaseState": "HARD_HOLD_NO_PUBLICATION"}
    try:
        t = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if t.tzinfo is None or t.utcoffset() is None:
            raise ValueError("timezone required")
    except (AttributeError, ValueError, TypeError, OverflowError):
        out["decision"] = "HOLD_OBSERVATION"; return out
    if not isinstance(obs, dict):
        out["decision"] = "HOLD_SOURCE"; return out
    for key, expected, reason in (
        ("list_url", LIST, "HOLD_LIST_URL"),
        ("list_detail_href", DETAIL, "HOLD_LIST_DETAIL_EDGE"),
        ("detail_url", DETAIL, "HOLD_DETAIL_URL"),
        ("venue_detail_url", VENUE_DETAIL, "HOLD_VENUE_URL"),
    ):
        if not exact_url(obs.get(key), expected):
            out["decision"] = reason; return out
    if obs.get("list_title") != TITLE or obs.get("detail_title") != TITLE:
        out["decision"] = "HOLD_TICKET_TITLE_PARITY"; return out
    if obs.get("venue_title") != VENUE_TITLE or obs.get("venue_title") == TITLE:
        out["decision"] = "HOLD_VENUE_TITLE_ROLE"; return out
    if obs.get("period_start") != PERIOD[0] or obs.get("period_end") != PERIOD[1]:
        out["decision"] = "HOLD_EXHIBITION_PERIOD"; return out
    if obs.get("detail_venue") != "台北南港展覽館一館1、4樓":
        out["decision"] = "HOLD_TICKET_DETAIL_VENUE"; return out
    if obs.get("purchase_control") != "我要購票":
        out["decision"] = "HOLD_BUTTON_ROLE"; return out
    for key in ("ticket_href", "ticket_session_id", "showtime", "inventory",
                "admission_price", "cross_source_event_id", "cross_source_verified",
                "published_event"):
        if obs.get(key) not in (None, "", False):
            out["decision"] = "HOLD_UNVERIFIED_TICKET_OR_CROSS_SOURCE"; return out
    # The venue article has a generic title; matching dates/venue do not prove
    # an independently validated event ID, ticket session or cross-source merge.
    out["candidateFields"] = [
        {"field": "title", "value": TITLE, "role": "TICKET_LIST_DETAIL_TITLE"},
        {"field": "period_start", "value": PERIOD[0], "role": "EXHIBITION_PERIOD_NOT_SHOWTIME"},
        {"field": "period_end", "value": PERIOD[1], "role": "EXHIBITION_PERIOD_NOT_SHOWTIME"},
        {"field": "venue_text", "value": obs["detail_venue"], "role": "TICKET_SOURCE_VENUE_TEXT"},
    ]
    for row in out["candidateFields"]:
        row.update(source=DETAIL, observed_at=observed_at, decision="REVIEW")
    return out
