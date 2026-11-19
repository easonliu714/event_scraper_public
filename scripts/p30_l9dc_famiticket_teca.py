"""P30-L9-DC FamiTicket #07 TECA: bounded official LIST→DETAIL source evidence.
Source reader 2026-11-02. REVIEW only; no ticket Session, checkout, inventory or publication.
"""
from datetime import datetime
from urllib.parse import urlsplit

LIST = "https://www.famiticket.com.tw/Home"
DETAIL = "https://www.famiticket.com.tw/Home/Activity/Info/MABvAE4ALwBxAEkAcQB3ADkAawB0AHUASgBlAGwAZwA3AGkAOQBsAEwATwBsAHIAOQBpADIANQBuAEkAcQBmAHYAZwBOADAAegBlAE0AQQBtAEwAZwA9AA2"
TITLE = "2026TECA台北國際音響大展｜超越雙11音響週年慶"
PERIOD = ("2026-11-19", "2026-11-22")
VENUE = "台北圓山大飯店"
PRICES = {"presale_single_day": 150, "standard_single_day": 250,
          "presale_two_day": 250, "standard_two_day": 500}

def exact_url(value, expected):
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
    out = {"gate": "P30-L9-DC", "decision": "REVIEW_WITH_HOLD", "candidateFields": [],
           "acceptedFields": 0, "ticketSessionIdsVerified": 0, "goldenAccepted": 0,
           "published": False, "releaseState": "HARD_HOLD_NO_PUBLICATION"}
    try:
        t = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if t.tzinfo is None or t.utcoffset() is None:
            raise ValueError("naive")
    except (AttributeError, ValueError, TypeError, OverflowError):
        out["decision"] = "HOLD_OBSERVATION"; return out
    if not isinstance(obs, dict):
        out["decision"] = "HOLD_SOURCE"; return out
    for key, expected in (("list_url", LIST), ("list_detail_href", DETAIL), ("detail_url", DETAIL)):
        if not exact_url(obs.get(key), expected):
            out["decision"] = "HOLD_" + key.upper(); return out
    if obs.get("list_title") != TITLE or obs.get("detail_title") != TITLE:
        out["decision"] = "HOLD_TITLE_PARITY"; return out
    if (obs.get("period_start"), obs.get("period_end")) != PERIOD:
        out["decision"] = "HOLD_EXHIBITION_PERIOD"; return out
    if obs.get("exhibition_hours") != "10:00-18:00" or obs.get("venue") != VENUE:
        out["decision"] = "HOLD_VENUE_OR_EXHIBITION_HOURS"; return out
    if not isinstance(obs.get("prices"), dict) or obs["prices"].keys() != PRICES.keys():
        out["decision"] = "HOLD_PRICE_CATEGORIES"; return out
    if any(type(obs["prices"][k]) is not int or obs["prices"][k] != v for k, v in PRICES.items()):
        out["decision"] = "HOLD_PRICE_CATEGORIES"; return out
    if obs.get("purchase_control") != "我要購票":
        out["decision"] = "HOLD_BUTTON_ROLE"; return out
    for key in ("checkout_href", "ticket_session_id", "inventory", "showtime",
                "general_admission_price", "published_event", "golden_accepted"):
        value = obs.get(key)
        flag = key in ("published_event", "golden_accepted")
        missing = value is None or (flag and value is False) or (isinstance(value, str) and value == "")
        if not missing:
            out["decision"] = "HOLD_UNVERIFIED_TICKET_CLAIM"; return out
    facts = [("title", TITLE, "TICKET_DETAIL_TITLE"),
             ("period_start", PERIOD[0], "EXHIBITION_PERIOD_START_NOT_SHOWTIME"),
             ("period_end", PERIOD[1], "EXHIBITION_PERIOD_END_NOT_SHOWTIME"),
             ("hours", "10:00-18:00", "EXHIBITION_OPEN_HOURS_NOT_SHOWTIME"),
             ("venue", VENUE, "VENUE_TEXT_NOT_SESSION")]
    facts.extend((k, v, "PRESALE_PRICE" if k.startswith("presale") else "STANDARD_PRICE")
                 for k, v in PRICES.items())
    out["candidateFields"] = [{"field": k, "value": v, "role": role, "source": DETAIL,
                                "observed_at": observed_at, "decision": "REVIEW"}
                               for k, v, role in facts]
    return out
