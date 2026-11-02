"""P30-VENUE-02BR Taipei Performing Arts Center same-ID LIST/DETAIL date conflict."""
from datetime import datetime
from urllib.parse import urlsplit
LIST="https://tpac.org.taipei/event"
DETAIL="https://tpac.org.taipei/event/2072"
TICKET="https://www.opentix.life/event/2090253659181064193"
TITLE="2026北藝夜遊：Beats到天臺"
SHOWS=["2026-11-11T19:00+08:00","2026-11-12T19:00+08:00","2026-11-13T19:00+08:00"]
def exact(value,expected):
    if not isinstance(value,str):return False
    try:
        a,b=urlsplit(value),urlsplit(expected)
        return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.path==b.path and a.query==b.query and not a.fragment and a.username is None and a.password is None and a.port is None
    except ValueError:return False
def inspect(obs,observed_at):
    out={"gate":"P30-VENUE-02BR","decision":"HOLD_SOURCE","candidateFields":[],"acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.tzinfo is None or t.utcoffset() is None:raise ValueError("naive")
    except (ValueError,AttributeError,TypeError,OverflowError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(obs,dict):return out
    for key,url in (("list_url",LIST),("list_detail_href",DETAIL),("detail_url",DETAIL),("ticket_href",TICKET)):
        if not exact(obs.get(key),url):out["decision"]="HOLD_"+key.upper();return out
    if obs.get("list_title")!=TITLE or obs.get("detail_title")!=TITLE or obs.get("ticket_title")!=TITLE:
        out["decision"]="HOLD_TITLE_PARITY";return out
    if obs.get("list_period")!=["2026-11-10","2026-11-12"] or obs.get("detail_period")!=["2026-11-11","2026-11-13"]:
        out["decision"]="HOLD_PERIOD_EVIDENCE";return out
    if obs.get("shows")!=SHOWS or obs.get("price")!=600 or obs.get("venue")!="臺北表演藝術中心":
        out["decision"]="HOLD_DETAIL_ROLES";return out
    for key in ("ticket_session_id","ticket_inventory","published_event","golden_accepted"):
        if key in obs and not (obs[key] is None or obs[key] is False or (isinstance(obs[key],str) and obs[key]=="")):
            out["decision"]="HOLD_UNVERIFIED_TICKET_CLAIM";return out
    facts=[("title",TITLE,"VENUE_DETAIL_TITLE"),("detail_period_start","2026-11-11","DETAIL_PERIOD"),
           ("detail_period_end","2026-11-13","DETAIL_PERIOD"),("price",600,"VENUE_ADVERTISED_PRICE")]
    facts.extend(("venue_show_"+str(i+1),value,"VENUE_ANNOUNCED_SESSION_NOT_TICKET_ID") for i,value in enumerate(SHOWS))
    out["candidateFields"]=[{"field":key,"value":value,"role":role,"source":DETAIL,"observed_at":observed_at,"decision":"REVIEW"} for key,value,role in facts]
    out["decision"]="HOLD_LIST_DETAIL_DATE_CONFLICT"
    return out
