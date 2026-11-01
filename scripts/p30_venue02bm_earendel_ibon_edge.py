"""P30-VENUE-02BM: Zepp New Taipei rid=160667 -> ibon redirect.
First-party venue LIST/DETAIL and observed link destination only.
No claim ibon ticket detail title, Session ID, inventory or Golden acceptance.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.zepp.co.jp/hall/newtaipei/"
DETAIL = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160667"
VENUE_LINK = "https://ibontw.com/26_Earendel"
REDIRECT = "https://ticket.ibon.com.tw/ActivityInfo/Details/39946"
TITLE = "厄倫蒂兒 Earendel 《THE SIGNAL》首場個人演唱會"
SHOW = "2026-11-14T19:00"
VENUE = "Zepp New Taipei"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    a, b = urlsplit(value), urlsplit(expected)
    return (a.scheme == b.scheme == "https" and a.netloc == b.netloc
            and a.username is None and a.password is None and a.port is None
            and a.path == b.path and a.query == b.query and not a.fragment)

def inspect(row, observed_at):
    result = {"gate": "P30-VENUE-02BM", "candidateFields": [],
              "acceptedFields": 0, "ticketSessionIdsVerified": 0,
              "ticketDetailTitleVerified": False, "goldenAccepted": 0,
              "published": False}
    try:
        if date.fromisoformat(observed_at).isoformat() != observed_at:
            raise ValueError("noncanonical")
    except (TypeError, ValueError):
        return dict(result, decision="HOLD_OBSERVATION")
    if not isinstance(row, dict) or not exact_url(row.get("venue_list"), LIST):
        return dict(result, decision="HOLD_VENUE_LIST")
    if not exact_url(row.get("list_detail_href"), DETAIL) or not exact_url(row.get("venue_detail"), DETAIL):
        return dict(result, decision="HOLD_RID_DETAIL_EDGE")
    if row.get("rid") != "160667" or row.get("title") != TITLE:
        return dict(result, decision="HOLD_VENUE_IDENTITY")
    if row.get("show") != SHOW or row.get("venue") != VENUE:
        return dict(result, decision="HOLD_VENUE_SHOW_ROLE")
    if not exact_url(row.get("ticket_href"), VENUE_LINK) or not exact_url(row.get("redirect_destination"), REDIRECT):
        return dict(result, decision="HOLD_TICKET_REDIRECT_CHAIN")
    if (row.get("sale") != "2026-09-19T13:00" or
            row.get("sale_is_show") is not False):
        return dict(result, decision="HOLD_SALE_NOT_SHOW")
    if (row.get("vip_total") != 3200 or row.get("vip_admission") != 3180
            or row.get("vip_benefit") != 20
            or row.get("vip_benefit_role") != "BUNDLE_COMPONENT_NOT_STANDALONE_ADMISSION"):
        return dict(result, decision="HOLD_VIP_SPLIT_AND_BENEFIT_ROLE")
    if tuple(row.get("other_prices") or ()) != (2600, 2000, 1600):
        return dict(result, decision="HOLD_PRICE_CATEGORIES")
    if row.get("ticket_detail_title_verified") is not False:
        return dict(result, decision="HOLD_IBON_DETAIL_UNVERIFIED")
    if any(row.get(k) is not None for k in ("ticket_detail_title", "ticket_session_id",
                                            "ticket_inventory", "checkout_url",
                                            "published_event", "ticket_price_from_ibon")):
        return dict(result, decision="HOLD_UNVERIFIED_IBON_FIELD_OR_SESSION")
    def c(field, value, url, role):
        return {"field": field, "value": value, "source": "ZEPP_NEW_TAIPEI_OFFICIAL",
                "source_url": url, "observed_at": observed_at,
                "role": role, "decision": "REVIEW"}
    result["candidateFields"] = [
        c("venue_rid", "160667", DETAIL, "VENUE_RECORD_NOT_TICKET_ID"),
        c("venue_show", SHOW, DETAIL, "VENUE_DESCRIBED_SHOW_NOT_TICKET_SESSION"),
        c("ticket_redirect", REDIRECT, DETAIL, "LINK_DESTINATION_NOT_VERIFIED_IBON_DETAIL"),
        c("vip_bundle", {"total": 3200, "admission": 3180, "benefit": 20}, DETAIL,
          "BENEFIT_NOT_STANDALONE_TICKET_PRICE"),
        c("sale", "2026-09-19T13:00", DETAIL, "SALE_NOT_SHOW"),
    ]
    return dict(result, decision="REVIEW_ZEPP_TO_IBON_HOLD_TICKET_DETAIL_SESSION")
