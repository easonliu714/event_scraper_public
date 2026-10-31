"""P30-VENUE-02AZ: Zepp 2 distinct rid performances cross-link to one KKTIX organizer event, no session promotion."""
from datetime import date
from urllib.parse import urlsplit,parse_qs
VENUE_HOME="https://www.zepp.co.jp/hall/newtaipei/"
VENUE_URLS=("https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160668","https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=165132")
KKTIX="https://freeplanetml.kktix.cc/events/takasetoya202611"
RID=("160668","165132")
SHOW_DATES=("2026-11-07","2026-11-08")
OPEN=("17:00","16:00")
START=("18:00","17:00")
def inspect(x,observed_at):
    out={"gate":"P30-VENUE-02AZ","acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try:date.fromisoformat(observed_at)
    except (ValueError,TypeError):return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or x.get("venue_list_url")!=VENUE_HOME or x.get("venue_detail_urls")!=VENUE_URLS:
        return dict(out,decision="HOLD_VENUE_LIST_DETAIL_EDGE")
    for u,r in zip(VENUE_URLS,RID):
        p=urlsplit(u)
        if p.scheme!="https" or p.netloc!="www.zepp.co.jp" or p.path!="/hall/newtaipei/schedule/single/" or parse_qs(p.query)!={"rid":[r]}:
            return dict(out,decision="HOLD_VENUE_RID_POLICY")
    if x.get("venue_rids")!=RID or x.get("dates")!=SHOW_DATES or x.get("open_times")!=OPEN or x.get("start_times")!=START:
        return dict(out,decision="HOLD_VENUE_PERFORMANCE_IDENTITY")
    if x.get("title")!='TAKASE TOYA 5th Album “♾️” Release Live in Taipei' or x.get("venue")!="Zepp New Taipei":
        return dict(out,decision="HOLD_EXACT_VENUE_TITLE")
    if x.get("ticket_edge")!=KKTIX or x.get("kktix_title")!='TAKASE TOYA 5th Album “∞” Release Live in Taipei':
        return dict(out,decision="HOLD_KKTIX_DIRECT_EDGE")
    if x.get("kktix_roles")!=("TWO_DAY_PASS","NOV07_SINGLE_DAY","NOV08_SINGLE_DAY"):
        return dict(out,decision="HOLD_BUNDLE_NOT_THIRD_SHOW")
    if x.get("single_day_price_band")!=(900,5880) or x.get("two_day_pass_price_band")!=(2600,10800):
        return dict(out,decision="HOLD_DISTINCT_PRICE_ROLES")
    if any(x.get(k) is not None for k in ("ticket_session_id","inventory","ticket_event_id","confirmed_ticket_session_price","published_event")):
        return dict(out,decision="HOLD_UNVERIFIED_TICKET_ID")
    out["provenance"]=[{"source":"ZEPP_NEW_TAIPEI_VENUE","source_url":u,"observed_at":observed_at,"role":"VENUE_LOCAL_RID_SHOW_DATE_OPEN_START","decision":"REVIEW"} for u in VENUE_URLS]
    out["provenance"].append({"source":"KKTIX_01","source_url":KKTIX,"observed_at":observed_at,"role":"DIRECT_VENUE_LINK_TO_ORGANIZER_EVENT_AND_BUNDLE","decision":"REVIEW"})
    return dict(out,decision="HOLD_CROSS_SOURCE_NO_TICKET_SESSION_ID")
