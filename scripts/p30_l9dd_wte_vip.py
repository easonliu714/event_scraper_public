"""P30-L9-DD tixCraft WTE exact related detail pages; REVIEW-only source observations."""
from datetime import datetime
from urllib.parse import urlsplit
STANDARD="https://tixcraft.com/activity/detail/26_wte"
VIP="https://tixcraft.com/activity/detail/26_wte_v"
TITLE="wave to earth - the pieces tour"
def same_url(value, expected):
    if not isinstance(value,str): return False
    try:
        a,b=urlsplit(value),urlsplit(expected)
        return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.path==b.path and a.query==b.query and not a.fragment and a.username is None and a.password is None and a.port is None
    except ValueError: return False
def inspect(obs, observed_at):
    out={"gate":"P30-L9-DD","decision":"HOLD_SOURCE","candidateFields":[],"acceptedFields":0,"ticketSessionIdsVerified":0,"goldenAccepted":0,"published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.tzinfo is None or t.utcoffset() is None: raise ValueError("naive")
    except (ValueError,AttributeError,TypeError,OverflowError):
        out["decision"]="HOLD_OBSERVATION";return out
    if not isinstance(obs,dict): return out
    for k,expected in (("standard_url",STANDARD),("vip_url",VIP),("vip_links_standard",STANDARD)):
        if not same_url(obs.get(k),expected):out["decision"]="HOLD_"+k.upper();return out
    if obs.get("title")!=TITLE or obs.get("vip_title")!=TITLE:
        out["decision"]="HOLD_TITLE";return out
    if obs.get("show")!="2026-11-24T19:30+08:00" or obs.get("venue")!="TICC":
        out["decision"]="HOLD_SHOW_VENUE";return out
    if obs.get("standard_price_range")!=[2300,6300] or obs.get("service_fee")!=200:
        out["decision"]="HOLD_GENERAL_PRICE";return out
    if obs.get("vip_addons")!={"M_AND_G":4800,"SOUNDCHECK":2900} or obs.get("vip_requires_general") is not True:
        out["decision"]="HOLD_ADDON_ROLE";return out
    if obs.get("standard_presale")!="2026-05-25" or obs.get("vip_sale_claim")!="2025-05-25":
        out["decision"]="HOLD_SALE_EVIDENCE";return out
    for k in ("checkout_url","ticket_session_id","inventory","published_event","golden_accepted"):
        if k in obs and not (obs[k] is None or obs[k] is False or (isinstance(obs[k],str) and obs[k]=="")):
            out["decision"]="HOLD_UNVERIFIED_CLAIM";return out
    facts=[("show","2026-11-24T19:30+08:00","SHOW"),("venue","TICC","VENUE"),
           ("general_price_min",2300,"GENERAL_PRICE_RANGE"),("general_price_max",6300,"GENERAL_PRICE_RANGE"),
           ("service_fee",200,"SERVICE_FEE"),("vip_m_and_g",4800,"VIP_ADDON_NOT_ADMISSION"),
           ("vip_soundcheck",2900,"VIP_ADDON_NOT_ADMISSION")]
    out["candidateFields"]=[{"field":k,"value":v,"role":role,"source":STANDARD if k in ("show","venue","general_price_min","general_price_max","service_fee") else VIP,"observed_at":observed_at,"decision":"REVIEW"} for k,v,role in facts]
    out["decision"]="HOLD_SALE_YEAR_CONFLICT"
    return out
