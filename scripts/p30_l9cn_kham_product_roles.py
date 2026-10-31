"""P30-L9-CN: KHAM #04 same-product public description/order page field roles, no ticket-session promotion."""
from datetime import date
from urllib.parse import urlsplit, parse_qs

DETAIL = "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1FRRCZ9"
ORDER = "https://kham.com.tw/application/UTK02/UTK0201_00.aspx?PRODUCT_ID=P1FRRCZ9"
TITLE = "2026 JEONG EUNJI SOLO CONCERT‘SUMMER, I’ASIA TOUR in TAIPEI"
SHOW = "2026-11-14T18:00"
SALE = "2026-09-23T12:00"
VENUE = "台北國際會議中心 大會堂"
TIERS = (3280, 3880, 4880, 5880)

def valid_product_url(url, path):
    if not isinstance(url, str):
        return False
    p = urlsplit(url)
    return (p.scheme == "https" and p.netloc == "kham.com.tw"
            and p.path == path and not p.fragment
            and parse_qs(p.query, keep_blank_values=True) == {"PRODUCT_ID": ["P1FRRCZ9"]}
            and p.query == "PRODUCT_ID=P1FRRCZ9")

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CN", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": [], "provenance": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not valid_product_url(x.get("detail_url"), "/application/UTK02/UTK0201_.aspx"):
        return dict(out, decision="HOLD_KHAM_DETAIL_ID")
    if not valid_product_url(x.get("order_url"), "/application/UTK02/UTK0201_00.aspx"):
        return dict(out, decision="HOLD_KHAM_ORDER_ID")
    if x.get("title") != TITLE or x.get("product_id") != "P1FRRCZ9":
        return dict(out, decision="HOLD_PRODUCT_TITLE_ID")
    if x.get("show_datetime") != SHOW or x.get("venue") != VENUE:
        return dict(out, decision="HOLD_SHOW_DATE_VENUE_ROLE")
    if x.get("sale_start") != SALE or x.get("sale_start_role") != "TICKET_SALE_START_NOT_PERFORMANCE":
        return dict(out, decision="HOLD_SALE_DATE_ROLE")
    if x.get("price_tiers") != TIERS or x.get("price_role") != "PRODUCT_ROW_TIERS_NOT_VERIFIED_SESSION_PRICE":
        return dict(out, decision="HOLD_PRICE_ROLE")
    if x.get("order_button_present") is not True or x.get("direct_detail_to_order_href_verified") is not False:
        return dict(out, decision="HOLD_ORDER_LINK_UNVERIFIED")
    if any(x.get(k) is not None for k in ("ticket_session_id", "inventory", "available_for_purchase",
                                          "confirmed_ticket_session_price", "canonical_published_event_id")):
        return dict(out, decision="HOLD_UNVERIFIED_PROMOTION")
    roles = (("title", TITLE, DETAIL, "PRODUCT_TITLE"),
             ("show_datetime", SHOW, ORDER, "PERFORMANCE_DATE_TIME"),
             ("venue", VENUE, ORDER, "PERFORMANCE_VENUE"),
             ("price_tiers", TIERS, ORDER, "PRODUCT_ROW_PRICE_TIERS"),
             ("sale_start", SALE, DETAIL, "TICKET_SALE_START"))
    out["candidateFields"] = [{"field": k, "value": v, "role": role, "source": "KHAM_04",
                               "source_url": url, "observed_at": observed_at, "decision": "REVIEW"}
                              for k, v, url, role in roles]
    out["provenance"] = [{"source": "KHAM_04", "source_url": url, "observed_at": observed_at,
                          "role": "SAME_PRODUCT_ID_PUBLIC_PAGE_NOT_SESSION_ID", "decision": "REVIEW"}
                         for url in (DETAIL, ORDER)]
    return dict(out, decision="REVIEW_PRODUCT_FIELDS_HOLD_SESSION_AND_DIRECT_LINK")
