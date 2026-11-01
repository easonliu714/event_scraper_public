"""P30-L9-CO: source-observed KHAM category LIST → exact PRODUCT_ID DETAIL edge.

Evidence-only gate; no network, production scraping, sale automation or publication.
"""
from datetime import date
from urllib.parse import urlsplit, parse_qs

LIST = "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?CATEGORY=205&TYPE=1"
DETAIL = "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1FRRCZ9"
ORDER = "https://kham.com.tw/application/UTK02/UTK0201_00.aspx?PRODUCT_ID=P1FRRCZ9"
TITLE = "2026 JEONG EUNJI SOLO CONCERT‘SUMMER, I’ASIA TOUR in TAIPEI"

def _url(value, path, query):
    if not isinstance(value, str):
        return False
    p = urlsplit(value)
    return (p.scheme == "https" and p.netloc == "kham.com.tw"
            and p.username is None and p.password is None and p.port is None
            and p.path == path and not p.fragment and p.query == query
            and parse_qs(p.query, keep_blank_values=True) ==
            parse_qs(query, keep_blank_values=True))

def inspect(x, observed_at):
    out = {"gate": "P30-L9-CO", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": [], "provenance": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not _url(x.get("list_url"), "/application/UTK01/UTK0101_06.aspx", "CATEGORY=205&TYPE=1"):
        return dict(out, decision="HOLD_LIST_URL")
    if not _url(x.get("list_detail_href"), "/application/UTK02/UTK0201_.aspx", "PRODUCT_ID=P1FRRCZ9"):
        return dict(out, decision="HOLD_LIST_DETAIL_HREF")
    if not _url(x.get("detail_url"), "/application/UTK02/UTK0201_.aspx", "PRODUCT_ID=P1FRRCZ9"):
        return dict(out, decision="HOLD_DETAIL_URL")
    if not _url(x.get("order_url"), "/application/UTK02/UTK0201_00.aspx", "PRODUCT_ID=P1FRRCZ9"):
        return dict(out, decision="HOLD_ORDER_URL")
    if x.get("list_title") != TITLE or x.get("detail_title") != TITLE or x.get("product_id") != "P1FRRCZ9":
        return dict(out, decision="HOLD_LIST_DETAIL_TITLE_IDENTITY")
    if x.get("purchase_button_present") is not True or x.get("purchase_button_href") is not None:
        return dict(out, decision="HOLD_BUTTON_HREF_UNVERIFIED")
    if any(x.get(k) is not None for k in ("ticket_session_id", "session_price", "inventory",
                                          "canonical_event_id", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_OR_PUBLICATION")
    out["candidateFields"] = [
        {"field": "product_detail_url", "value": DETAIL, "source": "KHAM_04", "source_url": LIST,
         "observed_at": observed_at, "role": "CATEGORY_LIST_DIRECT_HREF", "decision": "REVIEW"},
        {"field": "product_title", "value": TITLE, "source": "KHAM_04", "source_url": DETAIL,
         "observed_at": observed_at, "role": "SAME_PRODUCT_DETAIL_TITLE", "decision": "REVIEW"}]
    out["provenance"] = [
        {"source": "KHAM_04", "source_url": LIST, "observed_at": observed_at,
         "role": "PUBLIC_CATEGORY_LIST_NOT_TICKET_SESSION", "decision": "REVIEW"},
        {"source": "KHAM_04", "source_url": ORDER, "observed_at": observed_at,
         "role": "SAME_PRODUCT_ORDER_ROW_NOT_BUTTON_HREF", "decision": "HOLD_BUTTON_HREF_UNVERIFIED"}]
    return dict(out, decision="REVIEW_LIST_TO_PRODUCT_DETAIL_HOLD_TICKET_SESSION")
