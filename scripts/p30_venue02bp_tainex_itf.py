"""P30-VENUE-02BP: TaiNEX ITF venue bulletin identity/role REVIEW, not ticket merge.

Source-reader 2026-11-02: /event LIST -> /event/709 titled "旅展".
Organizer site is NOT a ticket Event URL; FamiTicket detail uses a different title.
No exact cross-source event ID, showtime, price, ticket Session or publication.
"""
from datetime import datetime
from urllib.parse import urlsplit
LIST = "https://www.tainex.com.tw/event"
DETAIL = "https://www.tainex.com.tw/event/709"
TICKET_DETAIL = "https://www.famiticket.com.tw/Home/Activity/Info/MABvAE4ALwBxAEkAcQB3ADkAawB0AHUASgBlAGwAZwA3AGkAOQBsAEwARgB2AE8ASwBTAGMAMQB5AEYAMQBOAE8AQgBBAHkAdwBaAEYAagBKAHMAawA9AA2"
TITLE = "旅展"
TICKET_TITLE = "2026 ITF 台灣國際旅展"
ORGANIZER = "財團法人台灣觀光協會"
ORGANIZER_SITE = "www.taiwanitf.org.tw/"
ORGANIZER_VISIT = "https://www.taiwanitf.org.tw/Information3"
PERIOD = ("2026-11-06", "2026-11-09")
FLOORS = ("一樓展場", "四樓展場")
def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    try:
        a,b=urlsplit(value),urlsplit(expected)
        return (a.scheme==b.scheme=="https" and a.netloc==b.netloc
                and a.username is None and a.password is None and a.port is None
                and a.path==b.path and a.query==b.query and not a.fragment)
    except ValueError:
        return False
def inspect(obs, observed_at):
    out={"gate":"P30-VENUE-02BP","decision":"REVIEW_WITH_HOLD",
         "candidateFields":[],"acceptedFields":0,"crossSourceIdentityVerified":False,
         "ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,
         "releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.tzinfo is None or t.utcoffset() is None: raise ValueError("naive")
    except (AttributeError,ValueError,TypeError,OverflowError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(obs,dict):
        out["decision"]="HOLD_SOURCE";return out
    for key,expected,reason in (
        ("list_url",LIST,"HOLD_LIST_URL"),
        ("list_detail_href",DETAIL,"HOLD_LIST_DETAIL_EDGE"),
        ("detail_url",DETAIL,"HOLD_DETAIL_URL"),
        ("ticket_detail_url",TICKET_DETAIL,"HOLD_TICKET_SOURCE_URL"),
    ):
        if not exact_url(obs.get(key),expected):
            out["decision"]=reason;return out
    if obs.get("list_title")!=TITLE or obs.get("detail_title")!=TITLE:
        out["decision"]="HOLD_VENUE_TITLE_PARITY";return out
    if obs.get("ticket_detail_title")!=TICKET_TITLE or obs.get("ticket_detail_title")==TITLE:
        out["decision"]="HOLD_CROSS_SOURCE_TITLE_ROLE";return out
    if obs.get("period_start")!=PERIOD[0] or obs.get("period_end")!=PERIOD[1]:
        out["decision"]="HOLD_PERIOD_ROLE";return out
    if obs.get("venue_hall")!="南港展覽館1館" or obs.get("floors")!=list(FLOORS):
        out["decision"]="HOLD_VENUE_ROLE";return out
    if obs.get("organizer")!=ORGANIZER or obs.get("organizer_site")!=ORGANIZER_SITE:
        out["decision"]="HOLD_ORGANIZER_ROLE";return out
    for key in ("ticket_event_id","ticket_session_id","ticket_href","showtime",
                "admission_price","inventory","cross_source_verified","published_event"):
        value = obs.get(key)
        # Numeric zero is a field claim, never equivalent to absent/False.
        if not (value is None or value is False or (isinstance(value,str) and value=="")):
            out["decision"]="HOLD_UNVERIFIED_TICKET_OR_CROSS_SOURCE";return out
    out["candidateFields"]=[
        {"field":"venue_title","value":TITLE,"role":"VENUE_GENERIC_EXHIBITION_TITLE"},
        {"field":"period_start","value":PERIOD[0],"role":"EXHIBITION_PERIOD_START"},
        {"field":"period_end","value":PERIOD[1],"role":"EXHIBITION_PERIOD_END"},
        {"field":"venue","value":obs["venue_hall"],"role":"VENUE_HALL"},
        {"field":"floors","value":list(FLOORS),"role":"VENUE_FLOORS"},
        {"field":"organizer","value":ORGANIZER,"role":"ORGANIZER_NOT_TICKET"},
    ]
    for row in out["candidateFields"]:
        row.update(source=DETAIL,observed_at=observed_at,decision="REVIEW")
    # Independently observed organizer information is a THIRD source, not
    # proof that TaiNEX /event/709 equals FamiTicket's ticket Event ID.
    extra = obs.get("organizer_visit")
    if extra is not None:
        if not isinstance(extra,dict) or not exact_url(extra.get("url"),ORGANIZER_VISIT):
            out["decision"]="HOLD_ORGANIZER_DETAIL_SOURCE";out["candidateFields"]=[];return out
        expected = {
            "date_start":"2026-11-06","date_end":"2026-11-09",
            "day1_hours":"12:00-18:00","later_hours":"10:00-18:00",
            "general_admission":200,"presale":180,"early_bird":150,
        }
        if any(type(extra.get(k)) is not type(v) or extra.get(k)!=v for k,v in expected.items()):
            out["decision"]="HOLD_ORGANIZER_DETAIL_ROLES";out["candidateFields"]=[];return out
        if extra.get("online_ticket_url") not in (None,""):
            out["decision"]="HOLD_ORGANIZER_UNVERIFIED_TICKET_URL";out["candidateFields"]=[];return out
        out["candidateFields"].extend([
            {"field":"organizer_day1_hours","value":expected["day1_hours"],"role":"EXHIBITION_OPEN_HOURS_NOT_SHOWTIME"},
            {"field":"organizer_later_hours","value":expected["later_hours"],"role":"EXHIBITION_OPEN_HOURS_NOT_SHOWTIME"},
            {"field":"organizer_general_admission","value":200,"role":"ORGANIZER_ONSITE_GENERAL_ADMISSION"},
            {"field":"organizer_presale","value":180,"role":"ORGANIZER_PRESALE_NOT_TICKET_SESSION"},
            {"field":"organizer_early_bird","value":150,"role":"ORGANIZER_EARLY_BIRD_NOT_TICKET_SESSION"},
        ])
        for row in out["candidateFields"][-5:]:
            row.update(source=ORGANIZER_VISIT,observed_at=observed_at,decision="REVIEW")
    return out
