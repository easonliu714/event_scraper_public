"""P30-VENUE-02BO: TaiNEX official LIST -> exact exhibition DETAIL, REVIEW only.

Evidence from bounded public source-reader 2026-11-02:
  https://www.tainex.com.tw/event
    -> https://www.tainex.com.tw/event/691
  Official detail labels: 展覽活動期間 / 活動地點 / 主辦單位 / 官方網站.
No ticket Event ID, showtime, admission price, or publication is established.
"""
from datetime import datetime
from urllib.parse import urlsplit

LIST = "https://www.tainex.com.tw/event"
DETAIL = "https://www.tainex.com.tw/event/691"
TITLE = "2026臺灣國際食品暨設備展"
START = "2026-11-13"
END = "2026-11-16"
HALL = "南港展覽館1館"
FLOORS = ("一樓展場", "四樓展場")
ORGANIZER = "展昭國際企業股份有限公司"
ORGANIZER_SITE = "www.chanchao.com.tw/food/"

def exact_url(value, expected):
    """No host-only/fuzzy URL identity; malformed authority must fail closed."""
    if not isinstance(value, str):
        return False
    try:
        a, b = urlsplit(value), urlsplit(expected)
        return (a.scheme == b.scheme == "https" and a.netloc == b.netloc
                and a.username is None and a.password is None and a.port is None
                and a.path == b.path and a.query == b.query and not a.fragment)
    except ValueError:
        return False

def inspect(observation, observed_at):
    """Classify one source-bound evidence candidate; never accept formal fields."""
    out = {"gate": "P30-VENUE-02BO", "decision": "REVIEW", "candidateFields": [],
           "acceptedFields": 0, "ticketEventIdsVerified": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False,
           "releaseState": "HARD_HOLD_NO_PUBLICATION"}
    try:
        stamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("naive")
    except (AttributeError, ValueError, TypeError, OverflowError):
        out["decision"] = "HOLD_OBSERVATION"
        return out
    if not isinstance(observation, dict):
        out["decision"] = "HOLD_SOURCE_EVIDENCE"
        return out
    for key, expected, reason in (
        ("list_url", LIST, "HOLD_LIST_URL"),
        ("list_detail_href", DETAIL, "HOLD_LIST_DETAIL_EDGE"),
        ("detail_url", DETAIL, "HOLD_DETAIL_URL"),
    ):
        if not exact_url(observation.get(key), expected):
            out["decision"] = reason
            return out
    if observation.get("list_title") != TITLE or observation.get("detail_title") != TITLE:
        out["decision"] = "HOLD_LIST_DETAIL_TITLE"
        return out
    if observation.get("period_label") != "展覽活動期間":
        out["decision"] = "HOLD_PERIOD_ROLE"
        return out
    if observation.get("period_start") != START or observation.get("period_end") != END:
        out["decision"] = "HOLD_PERIOD_RANGE"
        return out
    if observation.get("venue_label") != "活動地點" or observation.get("venue_hall") != HALL:
        out["decision"] = "HOLD_VENUE_ROLE"
        return out
    if observation.get("floors") != list(FLOORS):
        out["decision"] = "HOLD_FLOOR_AMBIGUITY"
        return out
    if observation.get("organizer_label") != "主辦單位" or observation.get("organizer") != ORGANIZER:
        out["decision"] = "HOLD_ORGANIZER_ROLE"
        return out
    if observation.get("external_website_label") != "官方網站" or observation.get("external_website") != ORGANIZER_SITE:
        out["decision"] = "HOLD_EXTERNAL_WEBSITE_ROLE"
        return out
    # The venue's organizer website is NOT a ticket event link. A ticket,
    # showtime, inventory or price claim requires a separate exact source edge.
    for k in ("ticket_event_id", "ticket_url", "ticket_session_id",
              "showtime", "admission_price", "inventory", "published_event"):
        if observation.get(k) not in (None, ""):
            out["decision"] = "HOLD_UNVERIFIED_TICKET_OR_PUBLICATION"
            return out
    out["candidateFields"] = [
        {"field": "title", "value": TITLE, "source": DETAIL, "role": "VENUE_EXHIBITION_TITLE",
         "observed_at": observed_at, "decision": "REVIEW"},
        {"field": "period_start", "value": START, "source": DETAIL, "role": "EXHIBITION_PERIOD_START",
         "observed_at": observed_at, "decision": "REVIEW"},
        {"field": "period_end", "value": END, "source": DETAIL, "role": "EXHIBITION_PERIOD_END",
         "observed_at": observed_at, "decision": "REVIEW"},
        {"field": "venue", "value": HALL, "source": DETAIL, "role": "VENUE_HALL",
         "observed_at": observed_at, "decision": "REVIEW"},
        {"field": "floors", "value": list(FLOORS), "source": DETAIL, "role": "EXHIBITION_FLOOR",
         "observed_at": observed_at, "decision": "REVIEW"},
        {"field": "organizer", "value": ORGANIZER, "source": DETAIL, "role": "ORGANIZER_NOT_TICKET",
         "observed_at": observed_at, "decision": "REVIEW"},
    ]
    return out
