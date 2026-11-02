"""P30-VENUE-02BU: TPAC exact show schedule and direct OPENTIX Event edge, age conflict HOLD."""
from datetime import datetime
from urllib.parse import urlsplit
LIST="https://tpac.org.taipei/program"
DETAIL="https://tpac.org.taipei/program/2088"
TICKET="https://www.opentix.life/event/2072516129034670080"
TITLE="C MUSICAL 音樂劇《小王子》"
SHOWS=("2026-11-05T19:30:00+08:00","2026-11-06T19:30:00+08:00",
       "2026-11-07T14:30:00+08:00","2026-11-07T19:30:00+08:00",
       "2026-11-08T14:30:00+08:00","2026-11-10T19:30:00+08:00",
       "2026-11-11T19:30:00+08:00","2026-11-12T19:30:00+08:00",
       "2026-11-13T19:30:00+08:00","2026-11-14T14:30:00+08:00",
       "2026-11-14T19:30:00+08:00","2026-11-15T14:30:00+08:00")
def exact(url, expected):
    if not isinstance(url,str): return False
    try:
        a,b=urlsplit(url),urlsplit(expected)
        return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.path==b.path and not a.query and not a.fragment
    except ValueError:return False
def inspect(row, observed_at):
    out={"gate":"P30-VENUE-02BU","venueSource":"TPAC_OFFICIAL","ticketPlatformId":"05",
         "decision":"HOLD_SOURCE","candidateFields":[],"acceptedFields":0,
         "ticketEventIdsVerified":0,"ticketSessionIdsVerified":0,
         "goldenAccepted":0,"published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.utcoffset() is None:raise ValueError()
    except (ValueError,TypeError,AttributeError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(row,dict):return out
    if not exact(row.get("list_url"),LIST) or not exact(row.get("venue_detail_url"),DETAIL) or not exact(row.get("direct_ticket_url"),TICKET):
        out["decision"]="HOLD_EXACT_VENUE_TICKET_EDGE";return out
    if row.get("list_title")!=TITLE or row.get("venue_title")!=TITLE or row.get("ticket_title")!=TITLE:
        out["decision"]="HOLD_THREE_SOURCE_TITLE_PARITY";return out
    if row.get("venue_room")!="藍盒子" or row.get("ticket_venue")!="臺北表演藝術中心 藍盒子":
        out["decision"]="HOLD_VENUE_ROOM_PARITY";return out
    if row.get("show_times")!=list(SHOWS) or len(set(row["show_times"]))!=12:
        out["decision"]="HOLD_TWELVE_VENUE_SHOWS";return out
    if row.get("venue_advertised_price_range")!=[1200,2200]:
        out["decision"]="HOLD_ADVERTISED_PRICE_NOT_CHECKOUT";return out
    if row.get("venue_age_min")!=6 or row.get("ticket_age_min")!=7:
        out["decision"]="HOLD_EXPLICIT_AGE_CONFLICT";return out
    if row.get("ticket_notice_city")!="嘉義市" or row.get("ticket_notice_date")!="2026-11-01":
        out["decision"]="HOLD_NOTICE_SCOPE";return out
    for key in ("ticket_session_ids","checkout_url","stock","inventory","formal_age_min","ticket_prices_verified","golden_accepted"):
        if key in row and row[key] is not None:
            out["decision"]="HOLD_UNVERIFIED_SESSION_OR_CONFLICT_OVERRIDE";return out
    fields=(("venue_detail_url",LIST,"VENUE_LIST_TO_EXACT_DETAIL"),
            ("direct_ticket_url",DETAIL,"VENUE_DIRECT_OPENTIX_EVENT_URL_NOT_SESSION_ID"),
            ("show_times",DETAIL,"TWELVE_VENUE_SHOW_TIMES_NOT_TICKET_SESSION_IDS"),
            ("venue_advertised_price_range",DETAIL,"VENUE_ADVERTISED_RANGE_NOT_CHECKOUT_PRICE"),
            ("venue_age_min",DETAIL,"AGE_CONFLICT_6_VENUE_VS_7_TICKET_HOLD"),
            ("ticket_age_min",TICKET,"AGE_CONFLICT_7_TICKET_VS_6_VENUE_HOLD"),
            ("ticket_notice_city",TICKET,"CHIAYI_NOTICE_NOT_TAIPEI_SHOW_CHANGE"))
    out["candidateFields"]=[{"field":field,"value":row[field],"source":source,
         "observed_at":observed_at,"role":role,"decision":"REVIEW"} for field,source,role in fields]
    out["ticketEventIdsVerified"]=1
    out["decision"]="REVIEW_EXACT_TICKET_EVENT_EDGE_AGE_CONFLICT_SESSION_HOLD"
    return out
