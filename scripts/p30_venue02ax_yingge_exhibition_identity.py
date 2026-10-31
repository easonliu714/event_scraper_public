"""P30-VENUE-02AX: Yingge official exhibition LIST->same sid DETAIL, venue/date roles only."""
from datetime import date
from urllib.parse import urlsplit,parse_qs
INDEX="https://www.ceramics.ntpc.gov.tw/xmdoc?XsmSId=0j148497613881029302"
ROOT="https://www.ceramics.ntpc.gov.tw/xmdoc/cont"
RECORDS=(
 ("0Q218341727998294094","形象與意境：泥塑的藝術語言-臺灣陶瓷雕塑學會聯展","2026-11-13","2026-12-13","陽光特展室"),
 ("0Q218346582180038351","無形之源：道的流動與生成-楊逸雪個展","2026-11-20","2026-12-20","b1陶藝長廊"))
def detail_url(sid):
    return ROOT+"?sid="+sid+"&xsmsid=0j148497613881029302"
def inspect(x,observed_at):
    out={"gate":"P30-VENUE-02AX","acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try: date.fromisoformat(observed_at)
    except (ValueError,TypeError): return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or x.get("index_url")!=INDEX:
        return dict(out,decision="HOLD_INDEX_URL")
    rows=x.get("rows")
    if not isinstance(rows,list) or len(rows)!=2:
        return dict(out,decision="HOLD_ROW_COUNT")
    for i,(sid,title,start,end,room) in enumerate(RECORDS):
        r=rows[i]
        if not isinstance(r,dict) or r.get("sid")!=sid or r.get("list_title")!=title or r.get("detail_url")!=detail_url(sid):
            return dict(out,decision="HOLD_LIST_DETAIL_IDENTITY")
        u=urlsplit(r["detail_url"])
        if u.netloc!="www.ceramics.ntpc.gov.tw" or u.path!="/xmdoc/cont" or parse_qs(u.query)!={"sid":[sid],"xsmsid":["0j148497613881029302"]}:
            return dict(out,decision="HOLD_DETAIL_URL")
        if r.get("detail_title")!=title or r.get("date_start")!=start or r.get("date_end")!=end:
            return dict(out,decision="HOLD_DETAIL_TITLE_DATE")
        if r.get("room")!=room or r.get("date_role")!="EXHIBITION_DATE_RANGE_NOT_TICKET_SESSION":
            return dict(out,decision="HOLD_EXHIBITION_ROLE")
        if any(r.get(k) is not None for k in ("ticket_platform_id","ticket_event_url","ticket_session_id","price","inventory")):
            return dict(out,decision="HOLD_UNVERIFIED_TICKET_FIELDS")
        out["provenance"].append({"source":"YINGGE_MUSEUM_OFFICIAL","source_url":detail_url(sid),
          "observed_at":observed_at,"sid":sid,"role":"LIST_DETAIL_EXHIBITION_RANGE_AND_ROOM","decision":"REVIEW"})
    return dict(out,decision="HOLD_TWO_EXHIBITIONS_SOURCE_BOUND_NOT_TICKET_EVENTS")
