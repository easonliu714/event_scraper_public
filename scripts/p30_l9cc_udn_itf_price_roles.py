"""P30-L9-CC: UDN #06 exact ITF list/detail, price-period and visit-hour roles.

Candidate provenance only; sale windows are not exhibition sessions or inventory.
"""
import datetime
import hashlib
import re
from urllib.parse import urlsplit, parse_qs

LIST_URL = "https://tickets.udnfunlife.com/application/UTK01/UTK0101_.aspx?+=+$"
DETAIL_URL = "https://tickets.udnfunlife.com/Application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1FSZGF7"
PRODUCT_ID = "P1FSZGF7"
TITLE = "2026 ITF台灣國際旅展"
VENUE = "南港展覽館 一館"
EVENT_DATES = ("2026-11-06", "2026-11-09")
PRICE_PERIODS = (
    ("2026-10-13", "2026-10-14", 150, "EARLY_BIRD"),
    ("2026-10-15", "2026-11-05", 180, "PRESALE"),
    ("2026-11-06", "2026-11-09", 200, "EXHIBITION_PERIOD"),
)
VISIT_HOURS = (("2026-11-06", "12:00", "18:00"), ("2026-11-07/09", "10:00", "18:00"))

def _detail_url_valid(value):
    if not isinstance(value, str):
        return False
    u = urlsplit(value)
    if (u.scheme, u.netloc, u.path, u.fragment) != (
        "https", "tickets.udnfunlife.com", "/Application/UTK02/UTK0201_.aspx", ""
    ):
        return False
    try:
        return parse_qs(u.query, strict_parsing=True) == {"PRODUCT_ID": [PRODUCT_ID]}
    except ValueError:
        return False

def inspect(row, detail, observed_at):
    out = dict(gate="P30-L9-CC", source="UDN_CANONICAL_06", acceptedFields=0,
               goldenAccepted=0, published=False, candidateProvenance=[],
               ticketSessionIdVerified=False, inventoryVerified=False)
    try:
        if not isinstance(observed_at, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except ValueError:
        return dict(out, decision="HOLD_OBSERVED_AT")
    if row.get("url") != LIST_URL or not _detail_url_valid(row.get("detail_url")):
        return dict(out, decision="HOLD_OFFICIAL_LIST_DETAIL_LINK")
    if not _detail_url_valid(detail.get("url")) or detail.get("product_id") != PRODUCT_ID:
        return dict(out, decision="HOLD_PRODUCT_ID_URL")
    if row.get("title") != TITLE or detail.get("title") != TITLE:
        return dict(out, decision="HOLD_SAME_PRODUCT_EXACT_TITLE")
    if row.get("venue") != VENUE or detail.get("venue") != VENUE:
        return dict(out, decision="HOLD_VENUE")
    if tuple(row.get("event_dates", ())) != EVENT_DATES or tuple(detail.get("event_dates", ())) != EVENT_DATES:
        return dict(out, decision="HOLD_EXHIBITION_DATE_RANGE")
    if row.get("display_price") != 180 or detail.get("display_price") != 180:
        return dict(out, decision="HOLD_INDEX_DETAIL_PRICE_BANNER")
    if tuple(map(tuple, detail.get("price_periods", []))) != PRICE_PERIODS:
        return dict(out, decision="HOLD_PRICE_PERIOD_ROLE")
    if tuple(map(tuple, detail.get("visit_hours", []))) != VISIT_HOURS:
        return dict(out, decision="HOLD_DAY_SPECIFIC_VISIT_HOURS")
    if detail.get("session_id") is not None or detail.get("inventory") is not None or detail.get("ticket_checkout_price") is not None:
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_INVENTORY_CHECKOUT")
    receipts = (
        ("LIST_TITLE", TITLE), ("DETAIL_TITLE", TITLE), ("PRODUCT_ID_NOT_SESSION_ID", PRODUCT_ID),
        ("EXHIBITION_DATE_RANGE", repr(EVENT_DATES)), ("VENUE", VENUE),
        ("DISPLAY_PRICE_NOT_CHECKOUT", "180"),
        ("EARLY_BIRD_SALE_PERIOD_NOT_EVENT_DATE", repr(PRICE_PERIODS[0])),
        ("PRESALE_PERIOD_NOT_EVENT_DATE", repr(PRICE_PERIODS[1])),
        ("EXHIBITION_PERIOD_PRICE_NOT_INVENTORY", repr(PRICE_PERIODS[2])),
        ("FIRST_DAY_VISIT_HOURS", repr(VISIT_HOURS[0])),
        ("LATER_DAYS_VISIT_HOURS", repr(VISIT_HOURS[1])),
    )
    for role, value in receipts:
        url = LIST_URL if role == "LIST_TITLE" else DETAIL_URL
        out["candidateProvenance"].append(dict(source="UDN_CANONICAL_06", source_url=url,
            observed_at=observed_at, role=role, valueSHA256=hashlib.sha256(value.encode()).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_PRODUCT_NOT_SESSION_AND_CHECKOUT_UNVERIFIED")
