"""P30-VENUE-02AR: Shulin Art Center direct OPENTIX event and two shows.
Venue SID != OPENTIX event ID != ticket session ID; all fields REVIEW only.
"""
import datetime
import hashlib
import re
from urllib.parse import parse_qs, urlsplit

INDEX_URL = "https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc?XsmSId=0J080506169482009359"
VENUE_SID = "0Q280506243680043606"
DETAIL_URL = "https://www.culture.ntpc.gov.tw/shulin_artcenter_chi/xmdoc/cont?sid=" + VENUE_SID + "&xsmsid=0J080506169482009359"
TICKET_EVENT_ID = "2079784321891332096"
TICKET_URL = "https://www.opentix.life/event/" + TICKET_EVENT_ID
TITLE_CORE = "酷麗鳥搞砸了"
VENUE = "樹林藝文中心演藝廳"
SHOWS = (("2026-11-14", "14:30"), ("2026-11-14", "19:30"))
VENUE_PRICE = 400
UPDATE_DATE = "2026-10-13"
PACKAGE_SALE = ("2026-08-01", "2026-11-14")

def exact_venue_detail(url):
    if not isinstance(url, str):
        return False
    try:
        u = urlsplit(url)
        return ((u.scheme, u.netloc, u.path, u.fragment) ==
                ("https", "www.culture.ntpc.gov.tw", "/shulin_artcenter_chi/xmdoc/cont", "") and
                parse_qs(u.query, strict_parsing=True) ==
                {"sid": [VENUE_SID], "xsmsid": ["0J080506169482009359"]})
    except ValueError:
        return False

def exact_ticket(url):
    if not isinstance(url, str):
        return False
    try:
        u = urlsplit(url)
        return (u.scheme, u.netloc, u.path, u.query, u.fragment) == (
            "https", "www.opentix.life", "/event/" + TICKET_EVENT_ID, "", "")
    except ValueError:
        return False

def inspect(index, venue, ticket, observed_at):
    out = dict(gate="P30-VENUE-02AR", source="SHULIN_P0_NEW_TAIPEI",
               ticketPlatform="OPENTIX_CANONICAL_05", acceptedFields=0,
               goldenAccepted=0, published=False, candidateProvenance=[],
               ticketSessionIdsVerified=False, inventoryVerified=False)
    try:
        if not isinstance(observed_at, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except ValueError:
        return dict(out, decision="HOLD_OBSERVED_AT")
    if not all(isinstance(x, dict) for x in (index, venue, ticket)):
        return dict(out, decision="HOLD_SOURCE_SHAPE")
    if index.get("url") != INDEX_URL or not exact_venue_detail(index.get("detail_url")):
        return dict(out, decision="HOLD_OFFICIAL_INDEX_TO_SID")
    if not exact_venue_detail(venue.get("url")) or venue.get("sid") != VENUE_SID:
        return dict(out, decision="HOLD_VENUE_SID")
    if not exact_ticket(venue.get("ticket_url")) or not exact_ticket(ticket.get("url")):
        return dict(out, decision="HOLD_DIRECT_OPENTIX_EVENT_LINK")
    if not all(isinstance(x.get("title"), str) and TITLE_CORE in x["title"] for x in (index, venue, ticket)):
        return dict(out, decision="HOLD_CROSS_SOURCE_TITLE")
    if venue.get("venue") != VENUE or ticket.get("venue") != VENUE:
        return dict(out, decision="HOLD_CROSS_SOURCE_VENUE")
    if tuple(map(tuple, venue.get("shows", ()))) != SHOWS or tuple(map(tuple, ticket.get("description_shows", ()))) != SHOWS:
        return dict(out, decision="HOLD_TWO_SHOW_DESCRIPTION_PARITY")
    if venue.get("update_date") != UPDATE_DATE:
        return dict(out, decision="HOLD_UPDATE_DATE_NOT_SHOW")
    if venue.get("listed_price") != VENUE_PRICE or tuple(ticket.get("package_sale_period", ())) != PACKAGE_SALE:
        return dict(out, decision="HOLD_PRICE_VS_PACKAGE_SALE")
    if any(x is not None for x in (ticket.get("ticket_session_ids"), ticket.get("per_session_price"), ticket.get("inventory"))):
        return dict(out, decision="HOLD_TICKET_SESSION_PRICE_INVENTORY")
    roles = (
        ("INDEX", INDEX_URL, "DIRECT_VENUE_SID_LINK", VENUE_SID),
        ("VENUE", DETAIL_URL, "TITLE", TITLE_CORE),
        ("VENUE", DETAIL_URL, "VENUE_SID_NOT_TICKET_ID", VENUE_SID),
        ("VENUE", DETAIL_URL, "DIRECT_OPENTIX_EVENT_LINK", TICKET_EVENT_ID),
        ("VENUE", DETAIL_URL, "FIRST_SHOW", repr(SHOWS[0])),
        ("VENUE", DETAIL_URL, "SECOND_SHOW", repr(SHOWS[1])),
        ("VENUE", DETAIL_URL, "VENUE_PRICE_NOT_PER_SESSION", str(VENUE_PRICE)),
        ("VENUE", DETAIL_URL, "UPDATE_DATE_NOT_SHOW", UPDATE_DATE),
        ("TICKET", TICKET_URL, "OPENTIX_EVENT_ID_NOT_SESSION", TICKET_EVENT_ID),
        ("TICKET", TICKET_URL, "DESCRIPTION_SHOWS_NOT_TICKET_SESSION_IDS", repr(SHOWS)),
        ("TICKET", TICKET_URL, "PACKAGE_SALE_PERIOD_NOT_SHOW", repr(PACKAGE_SALE)),
    )
    for source, url, role, value in roles:
        out["candidateProvenance"].append(dict(
            source=source, source_url=url, observed_at=observed_at, role=role,
            valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_OPENTIX_STATIC_CHOOSER_NO_TICKET_SESSION_IDS")
