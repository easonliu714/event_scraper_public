"""P30-L9-CW: FamiTicket #07 LIST→same-title DETAIL, exchange voucher roles.
Public first-party evidence only. Opaque URL is not an Event/Session ID.
No network, login, booking, production writer, or publication.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.famiticket.com.tw/Home"
DETAIL = "https://www.famiticket.com.tw/Home/Activity/Info/RQA3AHUAbwBwAEgANwBzAFIAQQA1AGEAbABEADgAcABqAGMAbwBaAC8ATAB1AFAAWQBYAGIAMAA1ACsAMgBOAGYANgBwAFcAVABIAEoAUQBqADAATQA9AA2"
TITLE = "名偵探柯南 第30號殺人事件"

def exact_url(actual, expected):
    if not isinstance(actual, str):
        return False
    a, e = urlsplit(actual), urlsplit(expected)
    return (a.scheme == e.scheme == "https" and a.netloc == e.netloc
            and a.username is None and a.password is None and a.port is None
            and a.path == e.path and a.query == e.query and not a.fragment)

def inspect(record, observed_at):
    out = {"gate": "P30-L9-CW", "candidateFields": [], "acceptedFields": 0,
           "ticketSessionIdsVerified": 0, "goldenAccepted": 0, "published": False}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(record, dict) or not exact_url(record.get("list_url"), LIST):
        return dict(out, decision="HOLD_LIST_SOURCE")
    if record.get("list_category") != "交換票" or record.get("list_title") != TITLE:
        return dict(out, decision="HOLD_LIST_IDENTITY_OR_CATEGORY")
    if not exact_url(record.get("list_detail_href"), DETAIL) or not exact_url(record.get("detail_url"), DETAIL):
        return dict(out, decision="HOLD_DIRECT_DETAIL_EDGE")
    if record.get("detail_title") != TITLE or record.get("detail_kind") != "電影交換券":
        return dict(out, decision="HOLD_DETAIL_IDENTITY_OR_VOUCHER")
    if record.get("film_release_date") != "2026-11-06" or record.get("film_release_label") != "上映日期":
        return dict(out, decision="HOLD_RELEASE_ROLE")
    if record.get("refund_deadline") != "2026-11-05" or record.get("refund_label") != "退票收件截止":
        return dict(out, decision="HOLD_REFUND_ROLE")
    if record.get("exchange_for_one_cinema_admission") is not True or record.get("voucher_is_specific_screening") is not False:
        return dict(out, decision="HOLD_EXCHANGE_NOT_SESSION")
    if any(record.get(k) is not None for k in (
            "cinema_screening_time", "cinema_venue", "ticket_session_id",
            "ticket_inventory", "checkout_url", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_SCREENING_OR_CHECKOUT")
    def candidate(field, value, url, role):
        return {"field": field, "value": value, "source": "FAMITICKET_07",
                "source_url": url, "observed_at": observed_at,
                "role": role, "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("detail_href", DETAIL, LIST, "OPAQUE_PRODUCT_URL_NOT_EVENT_ID"),
        candidate("title", TITLE, DETAIL, "VOUCHER_PRODUCT_NOT_SCREENING"),
        candidate("film_release_date", "2026-11-06", DETAIL, "FILM_RELEASE_NOT_SHOW"),
        candidate("refund_deadline", "2026-11-05", DETAIL, "REFUND_NOT_SHOW"),
        candidate("redemption_right", "one admission at eligible cinema", DETAIL, "EXCHANGE_VOUCHER_NOT_SESSION"),
    ]
    return dict(out, decision="REVIEW_FAMITICKET_VOUCHER_HOLD_SCREENING_SESSION")
