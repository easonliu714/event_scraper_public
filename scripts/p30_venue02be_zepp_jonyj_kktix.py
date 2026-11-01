"""P30-VENUE-02BE: Zepp rid 166457→KKTIX Jony J two ticket categories, one show.

Venue and organizer pages are separate source roles. No purchase/registration GET.
"""
from datetime import date
from urllib.parse import urlsplit

VENUE_LIST = "https://www.zepp.co.jp/hall/newtaipei/"
VENUE_DETAIL = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=166457"
KKTIX = "https://spaceport.kktix.cc/events/jonyj"
VENUE_TITLE = "Jony J 2026「本命」TOUR IN TAIPEI"
TICKET_TITLE = "Jony J 2026《本命》 台北站"
SHOW = "2026-11-06T20:00"
CATEGORY_ROWS = ("1樓站席", "2樓座席、站席")
ENTRY_TIMES = ("18:30", "19:00", "19:30")

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BE", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("venue_list"), VENUE_LIST):
        return dict(out, decision="HOLD_VENUE_LIST")
    if not exact_url(x.get("list_detail_href"), VENUE_DETAIL) or not exact_url(x.get("venue_detail"), VENUE_DETAIL):
        return dict(out, decision="HOLD_RID_DETAIL_IDENTITY")
    if not exact_url(x.get("venue_ticket_href"), KKTIX) or not exact_url(x.get("ticket_organizer_page"), KKTIX):
        return dict(out, decision="HOLD_DIRECT_KKTIX_ORGANIZER_EDGE")
    if (x.get("venue_title"), x.get("ticket_title"), x.get("venue_rid")) != (VENUE_TITLE, TICKET_TITLE, "166457"):
        return dict(out, decision="HOLD_SOURCE_LOCAL_TITLE_RID")
    if x.get("venue_show") != SHOW or x.get("ticket_show") != SHOW or x.get("venue_name") != "Zepp New Taipei":
        return dict(out, decision="HOLD_SAME_SHOWTIME_VENUE")
    if x.get("ticket_category_rows") != CATEGORY_ROWS or x.get("ticket_row_showtimes") != (SHOW, SHOW):
        return dict(out, decision="HOLD_TWO_CATEGORY_ROWS_SAME_SHOW")
    if x.get("category_rows_are_two_performances") is not False:
        return dict(out, decision="HOLD_CATEGORY_ROW_ROLE")
    if (x.get("sale_start"), x.get("vip_eligibility_cutoff"),
        x.get("queue_time"), x.get("entry_times")) != (
            "2026-07-27T19:00", "2026-11-01T23:59", "18:00", ENTRY_TIMES):
        return dict(out, decision="HOLD_SALE_VIP_QUEUE_ENTRY_ROLES")
    if x.get("upgrade_addon") != 680 or x.get("business_ticket") != 3000 or x.get("bundle_price") != 3680:
        return dict(out, decision="HOLD_UPGRADE_ADDON_BUNDLE_ROLES")
    if x.get("upgrade_is_separate_performance") is not False or x.get("sale_is_showtime") is not False:
        return dict(out, decision="HOLD_ROLE_PROMOTION")
    if any(x.get(k) is not None for k in ("ticket_session_ids", "verified_registration_url",
                                         "session_inventory", "session_prices", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    out["candidateFields"] = [
        {"field": "venue_show", "value": SHOW, "source": "ZEPP_NEW_TAIPEI_OFFICIAL",
         "source_url": VENUE_DETAIL, "observed_at": observed_at, "role": "VENUE_DESCRIPTIVE_SHOW", "decision": "REVIEW"},
        {"field": "ticket_category_rows", "value": list(CATEGORY_ROWS), "source": "KKTIX_01",
         "source_url": KKTIX, "observed_at": observed_at, "role": "TWO_TICKET_CATEGORIES_ONE_SHOW_NOT_SESSIONS", "decision": "REVIEW"},
        {"field": "vip_cutoff", "value": "2026-11-01T23:59", "source": "KKTIX_01",
         "source_url": KKTIX, "observed_at": observed_at, "role": "ADDON_LOTTERY_ELIGIBILITY_NOT_SHOWTIME", "decision": "REVIEW"},
        {"field": "upgrade_addon", "value": 680, "source": "KKTIX_01",
         "source_url": KKTIX, "observed_at": observed_at, "role": "OPTIONAL_ADDON_NOT_STANDALONE_TICKET_SESSION", "decision": "REVIEW"}]
    return dict(out, decision="REVIEW_ZEPP_TO_KKTIX_ONE_SHOW_TWO_CATEGORY_ROWS_HOLD_SESSION_IDS")
