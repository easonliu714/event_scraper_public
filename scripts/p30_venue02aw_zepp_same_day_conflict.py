"""Zepp New Taipei same-date two distinct rid; canceled != other event, KKTIX label != ticket URL."""
import datetime
INDEX="https://www.zepp.co.jp/hall/newtaipei/schedule/?_m=11&_y=2026"
CANCEL_URL="https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160673"
ACTIVE_URL="https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=169301"
DATE="2026-11-28"
def inspect(x,observed_at):
    out={"gate":"P30-VENUE-02AW","acceptedFields":0,"goldenAccepted":0,"published":False,"provenance":[]}
    try:datetime.date.fromisoformat(observed_at)
    except (ValueError,TypeError):return dict(out,decision="HOLD_OBSERVATION")
    if not isinstance(x,dict) or x.get("index_url")!=INDEX:return dict(out,decision="HOLD_LIST_URL")
    rows=x.get("rows")
    if not isinstance(rows,list) or len(rows)!=2:return dict(out,decision="HOLD_LIST_ROW_COUNT")
    a,b=rows
    if not isinstance(a,dict) or a.get("rid")!="160673" or a.get("url")!=CANCEL_URL or a.get("title")!='AKASAKI 1st WORLD TOUR "ONIGIRI"':
        return dict(out,decision="HOLD_CANCEL_IDENTITY")
    if not isinstance(b,dict) or b.get("rid")!="169301" or b.get("url")!=ACTIVE_URL or b.get("title")!="ALL PIECES, ONE PERSES":
        return dict(out,decision="HOLD_OTHER_IDENTITY")
    if any(r.get("date")!=DATE or r.get("start")!="18:00" for r in rows):
        return dict(out,decision="HOLD_SAME_DAY_START")
    if a.get("status")!="CANCELLED_SOURCE_LABEL" or b.get("status")!="NOT_MARKED_CANCELLED":
        return dict(out,decision="HOLD_STATUS_SCOPE")
    if a.get("door")!="17:00" or b.get("door") is not None:
        return dict(out,decision="HOLD_DOOR_ROLE")
    if b.get("declared_platform")!="KKTIX" or b.get("ticket_text")!="Link in Bio":
        return dict(out,decision="HOLD_PLATFORM_DECLARATION")
    if any(r.get("ticket_event_id") is not None or r.get("ticket_url") is not None for r in rows):
        return dict(out,decision="HOLD_UNVERIFIED_TICKET_LINK")
    if x.get("auto_resolve_schedule_conflict") is not False or x.get("assume_other_event_cancelled") is not False:
        return dict(out,decision="HOLD_SHARED_VENUE_CONFLICT")
    for r in rows:
        out["provenance"].append({"source":"ZEPP_NEW_TAIPEI_OFFICIAL","source_url":r["url"],
          "observed_at":observed_at,"role":"VENUE_LIST_DETAIL_STATUS_NOT_TICKET_ID",
          "rid":r["rid"],"status":r["status"],"decision":"REVIEW"})
    return dict(out,decision="HOLD_TWO_DISTINCT_RIDS_SAME_DAY_VENUE_CONFLICT")
