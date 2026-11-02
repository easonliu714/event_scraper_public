"""P30-L9-DH: OPENTIX #05 same-event sale/discount roles, public reader only."""
from datetime import datetime
from urllib.parse import urlsplit

EVENT="https://www.opentix.life/event/2072516129034670080"
TITLE="C MUSICAL 音樂劇《小王子》"
VENUE="臺北表演藝術中心 藍盒子"
MARKERS=("07/10(五) 12:00","07/14(二) 12:00","07/15(三) 12:00全面啟售")
DISCOUNTS=(("身心障礙人士及陪同者1名",50),("C+會員",85),("粉C會員",88),
           ("兩廳院會員",90),("我的第612號清單",86))

def exact(url):
    if not isinstance(url,str):return False
    try:
        a,b=urlsplit(url),urlsplit(EVENT)
        return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.path==b.path and not a.query and not a.fragment and not a.username and not a.password
    except ValueError:return False

def inspect(row, observed_at):
    out={"gate":"P30-L9-DH","canonicalPlatformId":"05","decision":"HOLD_SOURCE",
         "candidateFields":[],"acceptedFields":0,"ticketSessionIdsVerified":0,
         "goldenAccepted":0,"published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        ts=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if ts.utcoffset() is None:raise ValueError()
    except (ValueError,TypeError,AttributeError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(row,dict):return out
    if not exact(row.get("ticket_event_url")):
        out["decision"]="HOLD_EXACT_OPENTIX_EVENT";return out
    if row.get("title")!=TITLE or row.get("venue")!=VENUE or row.get("age_min")!=7:
        out["decision"]="HOLD_EVENT_TITLE_VENUE_AGE";return out
    # Official public text gives month/day sale markers, not an explicit year.
    # Never invent a year or associate adjacent marker with a discount tier.
    if row.get("sale_markers_unbound")!=list(MARKERS) or row.get("sale_year_explicit") is not False:
        out["decision"]="HOLD_SALE_MARKER_YEAR_OR_BINDING";return out
    if row.get("conditional_discounts")!=[{"name":n,"percent":p} for n,p in DISCOUNTS]:
        out["decision"]="HOLD_DISCOUNT_ROLE_PARITY";return out
    # Public text-reader shows a session-picker heading, not ticket session rows.
    # It does NOT establish that browser JS has no sessions.
    if row.get("session_picker_heading")!="選擇場次" or row.get("reader_session_rows_exposed") is not False:
        out["decision"]="HOLD_READER_SESSION_VISIBILITY";return out
    if row.get("change_notice_city")!="嘉義市" or row.get("change_notice_show_date")!="2026-11-01":
        out["decision"]="HOLD_NOTICE_NOT_TAIPEI_SHOW";return out
    for key in ("sale_year","sale_marker_discount_mapping","ticket_session_ids","checkout_url",
                "inventory","ticket_base_price","formal_min_price","golden_accepted"):
        if key in row and row[key] is not None:
            out["decision"]="HOLD_UNPROVEN_TICKET_CLAIM";return out
    fields=(("ticket_event_url","EVENT_ID_NOT_SESSION_ID"),
            ("sale_markers_unbound","MONTH_DAY_SALE_MARKERS_NO_EXPLICIT_YEAR"),
            ("conditional_discounts","ELIGIBILITY_DISCOUNTS_NOT_BASE_ADMISSION_PRICE"),
            ("session_picker_heading","READER_HEADING_NO_TICKET_SESSION_ROWS"),
            ("reader_session_rows_exposed","TEXT_READER_LIMIT_NOT_JS_SESSION_ABSENCE"),
            ("change_notice_city","CHIAYI_CAST_CHANGE_NOT_TAIPEI_SESSION"))
    out["candidateFields"]=[{"field":k,"value":row[k],"source":EVENT,"observed_at":observed_at,
                             "role":role,"decision":"REVIEW"} for k,role in fields]
    out["decision"]="REVIEW_OPENTIX_SALE_DISCOUNT_SESSION_HOLD"
    return out
