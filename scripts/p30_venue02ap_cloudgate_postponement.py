"""P30-VENUE-02AP: Cloud Gate four venue showtimes and OPENTIX postponement roles.

Source-bound candidate receipts only; no network, no publication, no formal acceptance.
"""
import datetime
import hashlib
import re
from urllib.parse import urlsplit, parse_qs

VENUE_URL = "https://www.cloudgate.org.tw/cgt/theater-event/1680"
TICKET_URL = "https://www.opentix.life/event/2086059234803216385"
EVENT_ID = "2086059234803216385"
TITLE = "來雲門共學 2026系列講座"
VENUE = "雲門劇場"
SHOWTIMES = (
    ("2026-10-17", "13:30"),
    ("2026-10-17", "16:30"),
    ("2026-12-19", "13:30"),
    ("2026-12-19", "16:30"),
)
POSTPONED = (
    ("2026-11-14", "13:30", "2026-12-19", "13:30"),
    ("2026-11-14", "16:30", "2026-12-19", "16:30"),
)

def _valid_ticket_link(url):
    """Allow only the exact first-party event path and the observed previewTime key."""
    if not isinstance(url, str):
        return False
    parts = urlsplit(url)
    if (parts.scheme, parts.netloc, parts.path, parts.fragment) != (
        "https", "www.opentix.life", "/event/" + EVENT_ID, ""
    ):
        return False
    if not parts.query:
        return True
    try:
        values = parse_qs(parts.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return False
    return set(values) == {"previewTime"} and len(values["previewTime"]) == 1 and bool(re.fullmatch(r"\d{13}", values["previewTime"][0]))

def inspect(venue, ticket, observed_at):
    """Reject unsupported identity, dates, status and ticket-session inference."""
    out = dict(gate="P30-VENUE-02AP", source="CLOUD_GATE_P0_NEW_TAIPEI",
               ticketSource="OPENTIX_CANONICAL_05", acceptedFields=0,
               goldenAccepted=0, published=False, candidateProvenance=[],
               ticketSessionIdsVerified=False)
    try:
        if not isinstance(observed_at, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except ValueError:
        return dict(out, decision="HOLD_OBSERVED_AT")
    if venue.get("url") != VENUE_URL or venue.get("venue_id") != "1680":
        return dict(out, decision="HOLD_VENUE_DETAIL_ID")
    if not _valid_ticket_link(venue.get("ticket_url")):
        return dict(out, decision="HOLD_DIRECT_TICKET_URL")
    if ticket.get("url") != TICKET_URL or ticket.get("event_id") != EVENT_ID:
        return dict(out, decision="HOLD_TICKET_EVENT_ID")
    if venue.get("title") != TITLE or ticket.get("title") != TITLE:
        return dict(out, decision="HOLD_CROSS_SOURCE_EXACT_TITLE")
    if venue.get("venue") != VENUE or ticket.get("venue") != VENUE:
        return dict(out, decision="HOLD_CROSS_SOURCE_VENUE")
    if tuple(map(tuple, venue.get("showtimes", []))) != SHOWTIMES:
        return dict(out, decision="HOLD_FOUR_VENUE_SHOWTIMES")
    if tuple(map(tuple, venue.get("postponements", []))) != POSTPONED:
        return dict(out, decision="HOLD_POSTPONEMENT_OLD_NEW_ROLE")
    if tuple(map(tuple, ticket.get("postponements", []))) != POSTPONED:
        return dict(out, decision="HOLD_TICKET_POSTPONEMENT_PARITY")
    if venue.get("price_label") != "400" or ticket.get("ticket_session_ids") not in (None, []):
        return dict(out, decision="HOLD_PRICE_OR_TICKET_SESSION_INFERENCE")
    if ticket.get("session_inventory") is not None or ticket.get("session_prices") is not None:
        return dict(out, decision="HOLD_INVENTORY_OR_SESSION_PRICE_INFERENCE")
    # Do not mistake previewTime, postponement date, or package sale dates for session IDs.
    receipts = (
        ("VENUE", VENUE_URL, "VENUE_DETAIL_ID_NOT_TICKET_EVENT_ID", "1680"),
        ("VENUE", VENUE_URL, "EXACT_TITLE", TITLE),
        ("VENUE", VENUE_URL, "VENUE_NAME", VENUE),
        ("VENUE", VENUE_URL, "FOUR_CURRENT_SHOWTIMES", repr(SHOWTIMES)),
        ("VENUE", VENUE_URL, "TWO_OLD_TO_NEW_POSTPONEMENTS", repr(POSTPONED)),
        ("VENUE", VENUE_URL, "VENUE_DECLARED_PRICE_NOT_SESSION_PRICE", "400"),
        ("VENUE", VENUE_URL, "DIRECT_OPENTIX_EVENT_LINK", TICKET_URL),
        ("TICKET_05", TICKET_URL, "EXACT_TICKET_EVENT_ID_NOT_SESSION_ID", EVENT_ID),
        ("TICKET_05", TICKET_URL, "EXACT_TITLE", TITLE),
        ("TICKET_05", TICKET_URL, "VENUE_NAME", VENUE),
        ("TICKET_05", TICKET_URL, "POSTPONEMENT_PARITY", repr(POSTPONED)),
    )
    for source, url, role, value in receipts:
        out["candidateProvenance"].append(dict(
            source=source, source_url=url, observed_at=observed_at, role=role,
            valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_TICKET_SESSION_ID_AND_INVENTORY_UNVERIFIED")
