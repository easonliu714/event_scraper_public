"""P30-L9-DA: FamiTicket #07 official LIST->same href DETAIL role separation.

Source-reader 2026-11-02: /Home LIST links directly to Ultra Taiwan 2026
detail; detail contains event date Nov 14, conditional EEGA 15:30 entry
deadline, NT$1000 late-upgrade surcharge, HSR discount, VIP benefits.
None establishes show start time, face-value price, inventory or ticket Session.
"""
from datetime import datetime
from urllib.parse import urlsplit

LIST = "https://www.famiticket.com.tw/Home"
DETAIL = "https://www.famiticket.com.tw/Home/Activity/Info/RgBhADYAOABvAGoANQBDAEYAdQB0AEIAbwBVACsAOAB0AGUAUgBkADUAMABrADUAVABiAE0AMwB4ADcAcABMAHoAUgB2AGMAVABSAFEAbQB3AG8ARQA9AA2"
TITLE = "Ultra Taiwan 2026 超世代音樂節"
EVENT_DATE = "2026-11-14"
VENUE = "台北大佳河濱公園"
ENTRY_CUTOFF = "15:30"
LATE_UPGRADE_SURCHARGE = 1000
HSR_DISCOUNT_FROM = 65

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

def inspect(observation, observed_at):
    out={"gate":"P30-L9-DA","decision":"REVIEW","candidateFields":[],
         "acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,
         "published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.tzinfo is None or t.utcoffset() is None: raise ValueError("naive")
    except (AttributeError,ValueError,TypeError,OverflowError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(observation,dict):
        out["decision"]="HOLD_SOURCE";return out
    for key,expected,reason in (
        ("list_url",LIST,"HOLD_LIST_URL"),
        ("list_detail_href",DETAIL,"HOLD_LIST_DETAIL_EDGE"),
        ("detail_url",DETAIL,"HOLD_DETAIL_URL"),
    ):
        if not exact_url(observation.get(key),expected):
            out["decision"]=reason;return out
    if observation.get("list_title")!=TITLE or observation.get("detail_title")!=TITLE:
        out["decision"]="HOLD_TITLE_IDENTITY";return out
    if observation.get("event_date")!=EVENT_DATE or observation.get("venue")!=VENUE:
        out["decision"]="HOLD_EVENT_DATE_VENUE";return out
    if observation.get("ee_ga_cutoff")!=ENTRY_CUTOFF or observation.get("late_upgrade_surcharge")!=LATE_UPGRADE_SURCHARGE:
        out["decision"]="HOLD_ENTRY_CONDITION";return out
    if observation.get("hsr_discount_from")!=HSR_DISCOUNT_FROM:
        out["decision"]="HOLD_HSR_DISCOUNT_ROLE";return out
    if observation.get("ee_ga_role")!="CONDITIONAL_ENTRY_DEADLINE" or observation.get("upgrade_role")!="LATE_ENTRY_UPGRADE_SURCHARGE":
        out["decision"]="HOLD_ROLE_CONFUSION";return out
    if observation.get("hsr_role")!="TRANSPORT_BUNDLE_DISCOUNT":
        out["decision"]="HOLD_ROLE_CONFUSION";return out
    # A conditional cutoff, surcharge, HSR discount and VIP perks are NOT
    # performance start time, general face-value admission, or availability.
    for key in ("showtime","admission_price","ticket_session_id","inventory","published_event"):
        if observation.get(key) not in (None,""):
            out["decision"]="HOLD_UNVERIFIED_SESSION_PRICE_OR_PUBLICATION";return out
    out["candidateFields"]=[
        {"field":"title","value":TITLE,"role":"TICKET_EVENT_TITLE"},
        {"field":"event_date","value":EVENT_DATE,"role":"EVENT_DATE_ONLY_NOT_SHOWTIME"},
        {"field":"venue","value":VENUE,"role":"EVENT_VENUE"},
        {"field":"ee_ga_cutoff","value":ENTRY_CUTOFF,"role":"CONDITIONAL_ENTRY_DEADLINE_NOT_SHOWTIME"},
        {"field":"late_upgrade_surcharge","value":LATE_UPGRADE_SURCHARGE,"role":"SURCHARGE_NOT_FACE_VALUE"},
        {"field":"hsr_discount_from","value":HSR_DISCOUNT_FROM,"role":"TRANSPORT_DISCOUNT_NOT_TICKET_PRICE"},
    ]
    for f in out["candidateFields"]:
        f.update(source=DETAIL,observed_at=observed_at,decision="REVIEW")
    return out
