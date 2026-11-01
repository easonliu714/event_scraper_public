"""P30-VENUE-02BG: Cloud Gate #1680 official LIST->DETAIL postponement.
Original November dates are superseded, not two extra current sessions.
"""
from datetime import date
from urllib.parse import urlsplit

LIST = "https://www.cloudgate.org.tw/cgt/latest-program"
DETAIL = "https://www.cloudgate.org.tw/cgt/theater-event/1680"
TITLE = "來雲門共學 2026系列講座"
ORIGINAL = ("2026-11-14T13:30", "2026-11-14T16:30")
REVISED = ("2026-12-19T13:30", "2026-12-19T16:30")
OCTOBER = ("2026-10-17T13:30", "2026-10-17T16:30")

def exact_url(value, expected):
    if not isinstance(value, str): return False
    p,e=urlsplit(value),urlsplit(expected)
    return (p.scheme==e.scheme=="https" and p.netloc==e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path==e.path and p.query==e.query and not p.fragment)

def inspect(x, observed_at):
    out={"gate":"P30-VENUE-02BG","acceptedFields":0,
         "ticketSessionIdsVerified":0,"goldenAccepted":0,
         "published":False,"candidateFields":[]}
    try: date.fromisoformat(observed_at)
    except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or not exact_url(x.get("list_url"),LIST):
        return dict(out,decision="HOLD_OFFICIAL_LIST")
    if not exact_url(x.get("list_detail_href"),DETAIL) or not exact_url(x.get("detail_url"),DETAIL):
        return dict(out,decision="HOLD_LIST_DETAIL_ID")
    if x.get("detail_id")!="1680" or x.get("title")!=TITLE:
        return dict(out,decision="HOLD_DETAIL_ID_TITLE")
    if (tuple(x.get("original_shows",[])),tuple(x.get("revised_shows",[])),
            tuple(x.get("october_shows",[]))) != (ORIGINAL,REVISED,OCTOBER):
        return dict(out,decision="HOLD_DATE_REVISION_PAIRING")
    if x.get("notice_date")!="2026-09-24" or x.get("notice_is_show") is not False:
        return dict(out,decision="HOLD_NOTICE_ROLE")
    if x.get("original_november_still_current") is not False:
        return dict(out,decision="HOLD_SUPERSEDED_NOVEMBER")
    if x.get("venue_unchanged") is not True or x.get("venue")!="雲門劇場":
        return dict(out,decision="HOLD_VENUE_SCOPE")
    if x.get("refund_grace_deadline")!="2026-11-14" or x.get("refund_is_show") is not False:
        return dict(out,decision="HOLD_REFUND_ROLE")
    if x.get("claimed_platform")!="OPENTIX" or x.get("opentix_event_url") is not None:
        return dict(out,decision="HOLD_PLATFORM_CLAIM_NO_DIRECT_ID")
    if x.get("descriptive_price")!=400 or x.get("discount_is_session_price") is not False:
        return dict(out,decision="HOLD_DESCRIPTIVE_PRICE_DISCOUNT")
    if any(x.get(k) is not None for k in (
        "ticket_session_id","inventory","checkout","published_event")):
        return dict(out,decision="HOLD_TICKET_SESSION")
    def candidate(field,value,role):
        return {"field":field,"value":value,"source":"CLOUDGATE_THEATER_OFFICIAL",
                "source_url":DETAIL,"observed_at":observed_at,"role":role,"decision":"REVIEW"}
    out["candidateFields"]=[
        candidate("detail_id","1680","VENUE_EVENT_NOT_TICKET_EVENT"),
        candidate("original_shows",list(ORIGINAL),"SUPERSEDED_SHOWS_NOT_CURRENT"),
        candidate("revised_shows",list(REVISED),"VENUE_POSTPONED_SHOWS"),
        candidate("notice_date","2026-09-24","ANNOUNCEMENT_NOT_SHOW"),
        candidate("refund_grace_deadline","2026-11-14","REFUND_NOT_SHOW"),
        candidate("claimed_platform","OPENTIX","CLAIM_NO_VERIFIED_EVENT_URL")]
    return dict(out,decision="REVIEW_CLOUDGATE_POSTPONEMENT_HOLD_OPENTIX_SESSION")
