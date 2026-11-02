"""P30-VENUE-02BT: TICC official LIST→DETAIL identity, generic event and room-role HOLD."""
from datetime import datetime
from urllib.parse import urlsplit,parse_qs
LIST="https://www.ticc.com.tw/wSite/sp?BaseDSD=7&CtUnit=152&ctNode=385&mp=2&nowpage=7&s_datetype=1&s_enddate=2026-11-01&s_keywords=&s_order=1&s_roomId=0&s_startdate=2026-10-03&xdUrl=%2FwSite%2Fap%2Flp_Activity_3.jsp"
DETAIL_GENERIC="https://www.ticc.com.tw/wSite/sp?bId=7416&ctNode=385&mp=2&xdUrl=%2FwSite%2Fap%2Fcp_Activity.jsp"
DETAIL_TOPBS="https://www.ticc.com.tw/wSite/sp?bId=8229&ctNode=385&mp=2&xdUrl=%2FwSite%2Fap%2Fcp_Activity.jsp"
def exact_url(url,expected):
    if not isinstance(url,str):return False
    try:
        a,b=urlsplit(url),urlsplit(expected)
        return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.path==b.path and parse_qs(a.query,keep_blank_values=True)==parse_qs(b.query,keep_blank_values=True) and not a.fragment
    except ValueError:return False
def inspect(row, observed_at):
    out={"gate":"P30-VENUE-02BT","decision":"HOLD_SOURCE","candidateFields":[],
         "acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,
         "published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.utcoffset() is None:raise ValueError()
    except (ValueError,TypeError,AttributeError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(row,dict):return out
    if not exact_url(row.get("list_url"),LIST) or not exact_url(row.get("generic_detail_url"),DETAIL_GENERIC) or not exact_url(row.get("topbs_detail_url"),DETAIL_TOPBS):
        out["decision"]="HOLD_LIST_DETAIL_ID";return out
    if row.get("generic_list_title")!="寬宏演唱會" or row.get("generic_detail_title")!="寬宏演唱會":
        out["decision"]="HOLD_GENERIC_TITLE";return out
    if row.get("generic_date")!="2026-11-14" or row.get("generic_room")!="大會堂" or row.get("generic_organizer")!="寬宏藝術經紀股份有限公司":
        out["decision"]="HOLD_GENERIC_ROLE";return out
    if row.get("topbs_list_title")!="TOPBS 2026年會" or row.get("topbs_detail_title")!="TOPBS 2026年會":
        out["decision"]="HOLD_TOPBS_TITLE";return out
    if row.get("topbs_period")!=["2026-11-14","2026-11-15"] or row.get("topbs_setup_date")!="2026-11-13" or row.get("topbs_rooms")!=["101","102","105","106(會前會議室)"]:
        out["decision"]="HOLD_ROOM_SETUP_ROLE";return out
    for key in ("ticket_url","ticket_event_id","session_id","ticket_price","show_time","golden_accepted"):
        if key in row and row[key] is not None:
            out["decision"]="HOLD_UNVERIFIED_TICKET_CLAIM";return out
    fields=(("generic_detail_url","VENUE_LIST_TO_EXACT_DETAIL_ID_NOT_TICKET_EVENT",LIST),
            ("generic_date","VENUE_BOOKING_DAY_NOT_VERIFIED_SHOW_TIME",DETAIL_GENERIC),
            ("generic_room","VENUE_ROOM",DETAIL_GENERIC),
            ("generic_organizer","VENUE_ORGANIZER_NOT_EVENT_ID",DETAIL_GENERIC),
            ("topbs_detail_url","VENUE_DISTINCT_DETAIL_ID",LIST),
            ("topbs_period","CONFERENCE_PERIOD_NOT_TICKET_SESSION",DETAIL_TOPBS),
            ("topbs_setup_date","SETUP_DAY_NOT_EVENT_START",DETAIL_TOPBS),
            ("topbs_rooms","MULTI_ROOM_NOT_MULTIPLE_TICKET_SESSIONS",DETAIL_TOPBS))
    out["candidateFields"]=[{"field":key,"value":row[key],"source":source,"role":role,
                              "observed_at":observed_at,"decision":"REVIEW"} for key,role,source in fields]
    out["decision"]="REVIEW_TWO_VENUE_DETAILS_HOLD_GENERIC_TICKET_IDENTITY"
    return out
