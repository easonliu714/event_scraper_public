"""P30-L9-CZ: public tixCraft GAME table source review; no checkout, stock or Session claims."""
from datetime import date
from urllib.parse import urlsplit
DETAIL="https://tixcraft.com/activity/detail/26_youngk"
GAME="https://tixcraft.com/activity/game/26_youngk"
TITLE="Young K Solo Tour <YOUNGEST> in TAIPEI"
ROWS=(("2026-11-28T19:00","GENERAL","NO_TICKETS_AVAILABLE"),("2026-11-29T18:00","GENERAL","NO_TICKETS_AVAILABLE"),("2026-11-29T18:00","MYVIDEO","SALE_ENDED_2026-08-30T11:00"),("2026-11-29T18:00","TAIWAN_MOBILE","SALE_ENDED_2026-08-30T11:00"))
def exact_url(value,expected):
    if not isinstance(value,str): return False
    a,b=urlsplit(value),urlsplit(expected)
    return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.username is None and a.password is None and a.port is None and a.path==b.path and a.query==b.query and not a.fragment
def inspect(row,observed_at):
    result={"gate":"P30-L9-CZ","candidateFields":[],"acceptedFields":0,"ticketSessionIdsVerified":0,"inventoryVerified":False,"goldenAccepted":0,"published":False}
    try:
        if date.fromisoformat(observed_at).isoformat()!=observed_at: raise ValueError("date")
    except (TypeError,ValueError): return dict(result,decision="HOLD_OBSERVATION")
    if not isinstance(row,dict) or not exact_url(row.get("detail_url"),DETAIL): return dict(result,decision="HOLD_DETAIL_SOURCE")
    if not exact_url(row.get("buy_tickets_href"),GAME) or not exact_url(row.get("game_url"),GAME): return dict(result,decision="HOLD_DETAIL_GAME_EDGE")
    if row.get("detail_title")!=TITLE or row.get("game_title")!=TITLE: return dict(result,decision="HOLD_EVENT_IDENTITY")
    if row.get("venue")!="台北國際會議中心TICC": return dict(result,decision="HOLD_VENUE")
    # Source rows are untrusted: malformed shapes must HOLD, never crash or imply stock.
    rows=row.get("game_rows")
    if (not isinstance(rows,(list,tuple)) or len(rows)!=len(ROWS)
            or any(not isinstance(x,(list,tuple)) or len(x)!=3
                   or any(not isinstance(v,str) for v in x) for x in rows)):
        return dict(result,decision="HOLD_GAME_ROW_SHAPE")
    if tuple(tuple(x) for x in rows)!=ROWS: return dict(result,decision="HOLD_GAME_ROW_STATUS")
    if row.get("availability_scope")!="PUBLIC_DISPLAY_ONLY": return dict(result,decision="HOLD_DISPLAY_NOT_INVENTORY")
    if any(row.get(k) is not None for k in ("ticket_session_id","inventory_count","checkout_url","published_event")): return dict(result,decision="HOLD_UNVERIFIED_SESSION_OR_PUBLICATION")
    def f(name,value,role): return {"field":name,"value":value,"source":"TIXCRAFT_03","source_url":GAME,"observed_at":observed_at,"role":role,"decision":"REVIEW"}
    result["candidateFields"]=[f("game_rows",[list(x) for x in ROWS],"PUBLIC_GAME_TABLE"),f("general_display","NO_TICKETS_AVAILABLE","DISPLAY_NOT_STOCK"),f("promotion_end","2026-08-30T11:00","SALE_NOT_SHOW")]
    return dict(result,decision="REVIEW_GAME_STATUS_HOLD_SESSION_INVENTORY")
