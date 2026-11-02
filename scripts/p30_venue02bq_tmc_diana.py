"""P30-VENUE-02BQ Taipei Music Center Diana Krall: two venue shows, not ticket Sessions.
Official TMC LIST→same-source DETAIL 2026-11-02; MNA ticket link reaches category
with distinct 11/28, 11/29 and member-package entries. No cross-source ID acceptance.
"""
from datetime import datetime
from urllib.parse import urlsplit
LIST = "https://www.tmc.taipei/tw/blog/show"
DETAIL = "https://www.tmc.taipei/tw/blog/show/DianaKrall2026"
TITLE = "爵士天后 戴安娜・克瑞兒 Diana Krall"
VENUE = "臺北流行音樂中心 表演廳"
SHOWS = ("2026-11-28T19:30:00+08:00", "2026-11-29T16:00:00+08:00")
PRICE_BANDS = (2580, 2980, 3280, 3680, 3980, 4280, 4980, 5980)
def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    try:
        a,b = urlsplit(value), urlsplit(expected)
        return (a.scheme == b.scheme == "https" and a.netloc == b.netloc
                and a.username is None and a.password is None and a.port is None
                and a.path == b.path and a.query == b.query and not a.fragment)
    except ValueError:
        return False
def inspect(obs, observed_at):
    out = {"gate":"P30-VENUE-02BQ","decision":"REVIEW_WITH_HOLD",
           "candidateFields":[],"acceptedFields":0,"ticketSessionIdsVerified":0,
           "crossSourceIdentityVerified":False,"goldenAccepted":0,"published":False,
           "releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.tzinfo is None or t.utcoffset() is None: raise ValueError("naive")
    except (AttributeError,ValueError,TypeError,OverflowError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(obs,dict):
        out["decision"]="HOLD_SOURCE";return out
    for key,expected in (("list_url",LIST),("list_detail_href",DETAIL),("detail_url",DETAIL)):
        if not exact_url(obs.get(key),expected):
            out["decision"]="HOLD_"+key.upper();return out
    if obs.get("list_title")!=TITLE or obs.get("detail_title")!=TITLE:
        out["decision"]="HOLD_TITLE_PARITY";return out
    if obs.get("venue")!=VENUE or obs.get("organizer")!="MNA牛耳藝術":
        out["decision"]="HOLD_VENUE_OR_ORGANIZER";return out
    if obs.get("showtimes")!=list(SHOWS):
        out["decision"]="HOLD_TWO_VENUE_SHOWS";return out
    if obs.get("sale_start")!="2026-09-17T12:00:00+08:00" or obs.get("published_date")!="2026-09-09":
        out["decision"]="HOLD_SALE_VS_PUBLICATION_ROLE";return out
    if (not isinstance(obs.get("price_bands"),list)
            or len(obs["price_bands"])!=len(PRICE_BANDS)
            or any(type(v) is not int or v!=PRICE_BANDS[i] for i,v in enumerate(obs["price_bands"]))):
        out["decision"]="HOLD_PRICE_BANDS";return out
    if obs.get("advertised_ticket_host")!="ticket.mna.com.tw":
        out["decision"]="HOLD_ADVERTISED_PLATFORM";return out
    for key in ("ticket_event_id","ticket_session_id","checkout_href","inventory",
                "cross_source_verified","published_event"):
        value=obs.get(key)
        flag=key in ("cross_source_verified","published_event")
        missing=value is None or (flag and value is False) or (isinstance(value,str) and value=="")
        if not missing:
            out["decision"]="HOLD_UNVERIFIED_TICKET_CLAIM";return out
    facts=[("title",TITLE,"VENUE_LIST_DETAIL_TITLE"),
           ("show_1",SHOWS[0],"VENUE_ANNOUNCED_SHOW_NOT_TICKET_SESSION"),
           ("show_2",SHOWS[1],"VENUE_ANNOUNCED_SHOW_NOT_TICKET_SESSION"),
           ("venue",VENUE,"VENUE_HALL"),
           ("sale_start","2026-09-17T12:00:00+08:00","SALE_START_NOT_SHOW"),
           ("published_date","2026-09-09","BULLETIN_PUBLICATION_NOT_SHOW"),
           ("price_bands",list(PRICE_BANDS),"VENUE_ADVERTISED_BANDS_NOT_INVENTORY"),
           ("advertised_ticket_host","ticket.mna.com.tw","VENUE_ADVERTISED_PLATFORM_NOT_EVENT_ID")]
    out["candidateFields"]=[{"field":k,"value":v,"role":role,"source":DETAIL,
                             "observed_at":observed_at,"decision":"REVIEW"}
                            for k,v,role in facts]
    return out
