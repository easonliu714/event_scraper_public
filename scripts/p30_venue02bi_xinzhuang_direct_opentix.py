"""P30-VENUE-02BI: New Taipei Xinzhuang Hall LIST→DETAIL→OPENTIX exact Event edge.
This is source-bound REVIEW, not production scraping or ticket Session acceptance.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.culture.ntpc.gov.tw/xzcac_chi/xmdoc?XsmSId=0G286655201682579075"
DETAIL = "https://www.culture.ntpc.gov.tw/xzcac_chi/xmdoc/cont?sid=0Q252550255605202263&xsmsid=0G286655201682579075"
TICKET = "https://www.opentix.life/event/2089995501384269825"
PAST = "https://www.opentix.life/event/2071939794940801025"
TITLE = "「Da Capo」2026年彩虹城市管樂團年度音樂會"
SHOW = "2026-12-05T14:00"
VENUE = "新莊文化藝術中心演藝廳"

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BI", "acceptedFields": 0,
           "ticketSessionIdsVerified": 0, "goldenAccepted": 0,
           "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("venue_list_url"), LIST):
        return dict(out, decision="HOLD_VENUE_LIST")
    if not exact_url(x.get("venue_detail_url"), DETAIL):
        return dict(out, decision="HOLD_VENUE_DETAIL")
    if x.get("venue_sid") != "0Q252550255605202263" or x.get("venue_title") != TITLE:
        return dict(out, decision="HOLD_VENUE_ID_TITLE")
    if x.get("venue_show") != SHOW or x.get("venue_price_bands") != [400, 500]:
        return dict(out, decision="HOLD_VENUE_SHOW_PRICE_SCOPE")
    if not exact_url(x.get("venue_ticket_href"), TICKET) or not exact_url(x.get("ticket_event_url"), TICKET):
        return dict(out, decision="HOLD_DIRECT_OPENTIX_EVENT_EDGE")
    if x.get("ticket_event_id") != "2089995501384269825" or x.get("ticket_title") != TITLE:
        return dict(out, decision="HOLD_TICKET_EVENT_ID_TITLE")
    if x.get("ticket_venue") != VENUE or x.get("ticket_show") != SHOW or x.get("ticket_open") != "2026-12-05T13:30":
        return dict(out, decision="HOLD_TICKET_VENUE_SHOW_OPEN")
    if x.get("earlybird_end") != "2026-10-11T23:59" or x.get("earlybird_is_regular_price") is not False:
        return dict(out, decision="HOLD_DISCOUNT_NOT_GENERAL_PRICE")
    if not exact_url(x.get("past_event_href"), PAST) or x.get("past_event_off_shelf") is not True:
        return dict(out, decision="HOLD_PAST_EVENT_OFF_SHELF")
    if any(x.get(k) is not None for k in ("ticket_session_id", "inventory", "checkout",
                                         "published_event", "past_event_as_future")):
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_OR_PAST_PROMOTION")
    def candidate(field, value, source, url, role):
        return {"field": field, "value": value, "source": source,
                "source_url": url, "observed_at": observed_at, "role": role,
                "decision": "REVIEW"}
    out["candidateFields"] = [
        candidate("venue_bulletin_sid", x["venue_sid"], "XINZHUANG_OFFICIAL", DETAIL, "BULLETIN_NOT_TICKET_EVENT"),
        candidate("venue_show", SHOW, "XINZHUANG_OFFICIAL", DETAIL, "SHOW_NOT_BULLETIN_UPDATE"),
        candidate("ticket_event_id", x["ticket_event_id"], "OPENTIX_05", TICKET, "EVENT_NOT_SESSION"),
        candidate("ticket_venue_open", x["ticket_open"], "OPENTIX_05", TICKET, "OPEN_NOT_SHOW"),
        candidate("price_bands", [400, 500], "XINZHUANG_OFFICIAL", DETAIL, "DESCRIPTIVE_NOT_DISCOUNT"),
        candidate("earlybird_end", x["earlybird_end"], "OPENTIX_05", TICKET, "DISCOUNT_DEADLINE_NOT_SHOW"),
        candidate("past_event_off_shelf", True, "OPENTIX_05", PAST, "PAST_OFF_SHELF_NOT_ACTIVE"),
    ]
    return dict(out, decision="REVIEW_XINZHUANG_DIRECT_OPENTIX_EVENT_HOLD_SESSION")
