"""P30-VENUE-02BH: two Zepp rid show dates, one KKTIX event with bundle row.
The bundle Event Dates row spans two days; it is NOT a third performance.
"""
from datetime import date
from urllib.parse import urlsplit

LIST="https://www.zepp.co.jp/hall/newtaipei/"
D1="https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160668"
D2="https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=165132"
TICKET="https://freeplanetml.kktix.cc/events/takasetoya202611"
TITLE="TAKASE TOYA 5th Album “♾️” Release Live in Taipei"
SHOWS=("2026-11-07T18:00","2026-11-08T17:00")
OPENS=("2026-11-07T17:00","2026-11-08T16:00")

def exact_url(value,expected):
    if not isinstance(value,str):return False
    p,e=urlsplit(value),urlsplit(expected)
    return (p.scheme==e.scheme=="https" and p.netloc==e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path==e.path and p.query==e.query and not p.fragment)

def inspect(x,observed_at):
    out={"gate":"P30-VENUE-02BH","acceptedFields":0,"ticketSessionIdsVerified":0,
         "goldenAccepted":0,"published":False,"candidateFields":[]}
    try:date.fromisoformat(observed_at)
    except (TypeError,ValueError):return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or not exact_url(x.get("venue_list_url"),LIST):
        return dict(out,decision="HOLD_VENUE_LIST")
    if tuple(x.get("detail_urls") or ())!=(D1,D2):
        return dict(out,decision="HOLD_TWO_DISTINCT_RIDS")
    if tuple(x.get("detail_titles") or ())!=(TITLE,TITLE):
        return dict(out,decision="HOLD_TITLE_PARITY")
    if tuple(x.get("venue_shows") or ())!=SHOWS or tuple(x.get("venue_opens") or ())!=OPENS:
        return dict(out,decision="HOLD_TWO_SHOW_OPEN_ROLES")
    if not exact_url(x.get("venue_ticket_href"),TICKET) or not exact_url(x.get("ticket_event_url"),TICKET):
        return dict(out,decision="HOLD_DIRECT_TICKET_EVENT_LINK")
    if x.get("ticket_event_title")!=TITLE or x.get("ticket_event_id")!="takasetoya202611":
        return dict(out,decision="HOLD_TICKET_EVENT_ID_TITLE")
    rows=x.get("ticket_event_dates")
    expected=[
        {"role":"BUNDLE","start":"2026-11-07T18:00","end":"2026-11-08T17:00","label":"兩日通票"},
        {"role":"SHOW","start":SHOWS[0],"end":None,"label":"11/07場"},
        {"role":"SHOW","start":SHOWS[1],"end":None,"label":"11/08場"}]
    if rows!=expected:
        return dict(out,decision="HOLD_BUNDLE_NOT_THIRD_SHOW")
    if x.get("single_day_vvip_price")!=5880 or x.get("two_day_vvip_price")!=10800:
        return dict(out,decision="HOLD_PRICE_CATEGORY_SCOPE")
    if x.get("bundle_is_single_day_price") is not False or x.get("sale_is_show") is not False:
        return dict(out,decision="HOLD_BUNDLE_SALE_ROLES")
    if x.get("general_sale_start")!="2026-09-23T20:00":
        return dict(out,decision="HOLD_GENERAL_SALE_ROLE")
    if any(x.get(k) is not None for k in ("ticket_session_ids","inventory","checkout","published_event")):
        return dict(out,decision="HOLD_UNVERIFIED_TICKET_SESSION")
    def c(field,value,source,url,role):
        return {"field":field,"value":value,"source":source,"source_url":url,
                "observed_at":observed_at,"role":role,"decision":"REVIEW"}
    out["candidateFields"]=[
        c("venue_rids",["160668","165132"],"ZEPP_NEW_TAIPEI_OFFICIAL",LIST,"TWO_VENUE_EVENT_IDS"),
        c("venue_shows",list(SHOWS),"ZEPP_NEW_TAIPEI_OFFICIAL",D1,"TWO_PERFORMANCES_NOT_BUNDLE"),
        c("ticket_event_id","takasetoya202611","KKTIX_01",TICKET,"TICKET_EVENT_NOT_SESSION"),
        c("event_dates_roles",["BUNDLE","SHOW","SHOW"],"KKTIX_01",TICKET,"BUNDLE_NOT_THIRD_SHOW"),
        c("vvip_prices",{"single":5880,"bundle":10800},"KKTIX_01",TICKET,"CONDITIONAL_TICKET_CATEGORY_PRICES"),
        c("general_sale_start","2026-09-23T20:00","KKTIX_01",TICKET,"SALE_NOT_SHOW")]
    return dict(out,decision="REVIEW_ZEPP_TWO_SHOWS_KKTIX_BUNDLE_HOLD_SESSIONS")
