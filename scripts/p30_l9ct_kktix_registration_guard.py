"""P30-L9-CT: KKTIX #01 event -> public registration href, 403 is not session proof.
Source observation only; do not GET registration in CI or claim ticket inventory.
"""
from datetime import date
from urllib.parse import urlsplit

EVENT = "https://sharalinmusic.kktix.cc/events/fdef73bb"
REGISTRATION = "https://kktix.com/events/fdef73bb/registrations/new"
TITLE = "林逸欣2026生日音樂會"
SHOW = "2026-11-07T14:30"
SALE = "2026-10-06T12:00"
VENUE = "Corner Max"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CT", "acceptedFields": 0,
           "ticketSessionIdsVerified": 0, "goldenAccepted": 0,
           "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("event_url"), EVENT):
        return dict(out, decision="HOLD_EVENT_URL")
    if x.get("event_id") != "fdef73bb" or x.get("event_title") != TITLE:
        return dict(out, decision="HOLD_EVENT_ID_TITLE")
    if not exact_url(x.get("registration_href"), REGISTRATION):
        return dict(out, decision="HOLD_REGISTRATION_HREF")
    if x.get("registration_http") != 403 or x.get("registration_accessible") is not False:
        return dict(out, decision="HOLD_REGISTRATION_HTTP_ROLE")
    if (x.get("show"), x.get("venue"), x.get("sale_start"),
            x.get("sale_is_show")) != (SHOW, VENUE, SALE, False):
        return dict(out, decision="HOLD_SHOW_SALE_ROLE")
    if (x.get("standard_price"), x.get("accessible_price"),
            x.get("accessible_is_standard")) != (980, 490, False):
        return dict(out, decision="HOLD_PRICE_ELIGIBILITY")
    if x.get("pickup_fee") != 30 or x.get("pickup_fee_is_ticket_price") is not False:
        return dict(out, decision="HOLD_PICKUP_FEE_ROLE")
    if any(x.get(k) is not None for k in (
        "ticket_session_id", "inventory", "checkout", "published_event",
        "registration_response_body")):
        return dict(out, decision="HOLD_UNVERIFIED_REGISTRATION_SESSION")
    def candidate(field, value, source_url, role):
        return {"field": field, "value": value, "source": "KKTIX_01",
                "source_url": source_url, "observed_at": observed_at,
                "role": role, "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("event_id", "fdef73bb", EVENT, "EVENT_NOT_SESSION"),
        candidate("show", SHOW, EVENT, "DESCRIPTIVE_SHOWTIME"),
        candidate("sale_start", SALE, EVENT, "SALE_NOT_SHOW"),
        candidate("ticket_prices", {"standard": 980, "accessible": 490}, EVENT,
                  "DESCRIPTIVE_PRICE_ELIGIBILITY"),
        candidate("registration_href", REGISTRATION, EVENT,
                  "DIRECT_HREF_BUT_HTTP403_NO_SESSION"),
        candidate("pickup_fee", 30, EVENT, "PICKUP_FEE_NOT_TICKET_PRICE")]
    return dict(out, decision="REVIEW_KKTIX_DIRECT_REGISTRATION_HREF_403_HOLD_SESSION")
