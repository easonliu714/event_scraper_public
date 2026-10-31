"""P30-L9-CE: TixFun #09 official index -> same PRODUCT_ID detail role boundary.
Public source observations only; no network, checkout, or publication.
"""
import datetime
import hashlib
import re
from urllib.parse import parse_qs, urlsplit

INDEX_URL = "https://tixfun.com/"
PRODUCT_ID = "Q029ZSDJ"
DETAIL_URL = "https://tixfun.com/UTK0201_?PRODUCT_ID=" + PRODUCT_ID
TITLE_CORE = "恐龍復活了2：勇闖神秘島"
RANGE = ("2026-12-19", "2026-12-20")
PRICE_RANGE = (600, 3000)
EARLY_BIRD = ("2026-10-13 12:00", "2026-10-28 23:59")
GENERAL_ONSALE = "2026-10-29 00:00"
DISCOUNT_DEADLINE = "2026-11-02 23:59"

def exact_detail(url):
    if not isinstance(url, str):
        return False
    try:
        u = urlsplit(url)
        return ((u.scheme, u.netloc, u.path, u.fragment) ==
                ("https", "tixfun.com", "/UTK0201_", "") and
                parse_qs(u.query, strict_parsing=True) == {"PRODUCT_ID": [PRODUCT_ID]})
    except ValueError:
        return False

def inspect(index, detail, observed_at):
    out = dict(gate="P30-L9-CE", source="TIXFUN_CANONICAL_09",
               candidateProvenance=[], acceptedFields=0, goldenAccepted=0,
               published=False, ticketSessionIdVerified=False,
               inventoryVerified=False)
    try:
        if not isinstance(observed_at, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except ValueError:
        return dict(out, decision="HOLD_OBSERVED_AT")
    if not isinstance(index, dict) or not isinstance(detail, dict):
        return dict(out, decision="HOLD_SOURCE_SHAPE")
    if index.get("url") != INDEX_URL or not exact_detail(index.get("detail_url")):
        return dict(out, decision="HOLD_OFFICIAL_INDEX_LINK")
    if not exact_detail(detail.get("url")) or detail.get("product_id") != PRODUCT_ID:
        return dict(out, decision="HOLD_PRODUCT_ID")
    if not all(isinstance(x.get("title"), str) and TITLE_CORE in x["title"]
               for x in (index, detail)):
        return dict(out, decision="HOLD_SOURCE_LOCAL_TITLE_CORE")
    if tuple(detail.get("date_range", ())) != RANGE:
        return dict(out, decision="HOLD_PRODUCT_DATE_RANGE")
    if tuple(detail.get("price_range", ())) != PRICE_RANGE:
        return dict(out, decision="HOLD_PRODUCT_PRICE_BAND")
    if tuple(detail.get("early_bird", ())) != EARLY_BIRD or detail.get("general_onsale") != GENERAL_ONSALE:
        return dict(out, decision="HOLD_SALE_PERIOD_ROLE")
    if detail.get("discount_deadline") != DISCOUNT_DEADLINE:
        return dict(out, decision="HOLD_DISCOUNT_NOT_SHOWTIME")
    if detail.get("session_rows") not in (None, []) or any(
        detail.get(x) is not None for x in ("ticket_session_id", "session_price", "inventory")):
        return dict(out, decision="HOLD_NO_PUBLIC_SESSION_ALLOCATION")
    evidence = (
        ("INDEX", INDEX_URL, "DIRECT_PRODUCT_LINK", PRODUCT_ID),
        ("INDEX", INDEX_URL, "TITLE_CORE", TITLE_CORE),
        ("DETAIL", DETAIL_URL, "PRODUCT_ID_NOT_SESSION_ID", PRODUCT_ID),
        ("DETAIL", DETAIL_URL, "PRODUCT_DATE_RANGE_NOT_SESSION_ROWS", repr(RANGE)),
        ("DETAIL", DETAIL_URL, "PRODUCT_PRICE_BAND_NOT_SESSION_PRICE", repr(PRICE_RANGE)),
        ("DETAIL", DETAIL_URL, "EARLY_BIRD_SALE_PERIOD", repr(EARLY_BIRD)),
        ("DETAIL", DETAIL_URL, "GENERAL_ONSALE_NOT_SHOWTIME", GENERAL_ONSALE),
        ("DETAIL", DETAIL_URL, "DISCOUNT_DEADLINE_NOT_SHOWTIME", DISCOUNT_DEADLINE),
    )
    for source, url, role, value in evidence:
        out["candidateProvenance"].append(dict(
            source=source, source_url=url, observed_at=observed_at, role=role,
            valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out, decision="HOLD_PRODUCT_RANGE_AND_DYNAMIC_SESSION_CHOOSER")
