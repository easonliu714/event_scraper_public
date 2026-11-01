"""P30-L9-CY: first-party tixCraft #03 LIST->same-path Young K detail.
Evidence-bound REVIEW only. Distinguish show, sale, VIP package and service fee.
No network, ticket checkout, guessed Session ID, Golden or publication.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://tixcraft.com/activity"
DETAIL = "https://tixcraft.com/activity/detail/26_youngk"
TITLE = "Young K Solo Tour <YOUNGEST> in TAIPEI"
VENUE = "Taipei International Convention Center (TICC)"
SHOWS = ("2026-11-28T19:00", "2026-11-29T18:00")
GENERAL = (4880, 3880, 3380, 2880)
VIP = (6880, 5880)

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    a, b = urlsplit(value), urlsplit(expected)
    return (a.scheme == b.scheme == "https" and a.netloc == b.netloc
            and a.username is None and a.password is None and a.port is None
            and a.path == b.path and a.query == b.query and not a.fragment)

def inspect(row, observed_at):
    result = {"gate": "P30-L9-CY", "candidateFields": [],
              "acceptedFields": 0, "ticketSessionIdsVerified": 0,
              "goldenAccepted": 0, "published": False}
    try:
        if date.fromisoformat(observed_at).isoformat() != observed_at:
            raise ValueError("noncanonical")
    except (TypeError, ValueError):
        return dict(result, decision="HOLD_OBSERVATION")
    if not isinstance(row, dict) or not exact_url(row.get("list_url"), LIST):
        return dict(result, decision="HOLD_LIST_SOURCE")
    if row.get("list_title") != TITLE or not exact_url(row.get("list_detail_href"), DETAIL):
        return dict(result, decision="HOLD_LIST_DETAIL_IDENTITY")
    if not exact_url(row.get("detail_url"), DETAIL) or row.get("detail_title") != TITLE:
        return dict(result, decision="HOLD_DETAIL_IDENTITY")
    if row.get("venue") != VENUE or tuple(row.get("showtimes") or ()) != SHOWS:
        return dict(result, decision="HOLD_TWO_SHOWS_OR_VENUE")
    if tuple(row.get("general_prices") or ()) != GENERAL or tuple(row.get("vip_package_prices") or ()) != VIP:
        return dict(result, decision="HOLD_PRICE_CATEGORY")
    if row.get("service_fee") != 200 or row.get("service_fee_role") != "ADDITIONAL_PER_TICKET":
        return dict(result, decision="HOLD_SERVICE_FEE_NOT_ADMISSION")
    if (row.get("original_general_sale") != "2026-08-27T11:00"
            or row.get("added_show_general_sale") != "2026-09-01T15:00"
            or row.get("added_show_date") != "2026-11-28"):
        return dict(result, decision="HOLD_SHOW_SPECIFIC_SALE_ROLE")
    if row.get("sale_is_show") is not False or row.get("pickup_is_show") is not False:
        return dict(result, decision="HOLD_DATE_ROLE")
    if any(row.get(k) is not None for k in ("ticket_session_id", "inventory",
                                            "checkout_url", "published_event")):
        return dict(result, decision="HOLD_UNVERIFIED_SESSION_OR_PUBLICATION")
    def c(field, value, role):
        return {"field": field, "value": value, "source": "TIXCRAFT_03",
                "source_url": DETAIL, "observed_at": observed_at,
                "role": role, "decision": "REVIEW"}
    result["candidateFields"] = [
        c("title", TITLE, "EVENT_TITLE"),
        c("showtimes", list(SHOWS), "TWO_DESCRIBED_SHOWS_NOT_SESSION_IDS"),
        c("general_prices", list(GENERAL), "GENERAL_ADMISSION_FACE_VALUE"),
        c("vip_package_prices", list(VIP), "VIP_PACKAGE_NOT_GENERAL_PRICE"),
        c("service_fee", 200, "ADDITIONAL_FEE_NOT_FACE_VALUE"),
        c("added_show_sale", "2026-09-01T15:00", "SALE_NOT_SHOW"),
    ]
    return dict(result, decision="REVIEW_YOUNGK_HOLD_TICKET_SESSION")
