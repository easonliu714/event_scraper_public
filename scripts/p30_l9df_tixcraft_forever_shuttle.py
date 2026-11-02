"""P30-L9-DF: read-only source-bound tixCraft concert versus shuttle receipts."""
from datetime import datetime
from urllib.parse import urlsplit
CONCERT="https://tixcraft.com/activity/detail/26_forever"
SHUTTLE="https://tixcraft.com/activity/detail/26_busffdome"
SHOWS=("2026-11-28T19:00:00+08:00","2026-11-29T19:00:00+08:00")
GENERAL=(5880,5280,4880,4280,3680,3280,2680,1680)
ACCESSIBLE=(2440,1840)
def exact(url, expected):
    if not isinstance(url,str): return False
    try:
        a,b=urlsplit(url),urlsplit(expected)
        return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.path==b.path and a.query==b.query and not a.fragment
    except ValueError: return False
def inspect(row, observed_at):
    result={"gate":"P30-L9-DF","canonicalPlatformId":"03","decision":"HOLD_SOURCE",
            "candidateFields":[],"acceptedFields":0,"ticketSessionIdsVerified":0,
            "goldenAccepted":0,"published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.utcoffset() is None: raise ValueError()
    except (ValueError,TypeError,AttributeError):
        result["decision"]="HOLD_OBSERVATION";return result
    if not isinstance(row,dict): return result
    if not exact(row.get("concert_url"),CONCERT) or not exact(row.get("shuttle_url"),SHUTTLE):
        result["decision"]="HOLD_EXACT_ACTIVITY_URL";return result
    if row.get("concert_title")!="F✦FOREVER恆星之城 光年赴約・臺北・限定場演唱會":
        result["decision"]="HOLD_CONCERT_TITLE";return result
    if row.get("shuttle_type")!="返鄉專車" or row.get("shuttle_routes")!=["A","B","K"]:
        result["decision"]="HOLD_DISTINCT_TRANSPORT_PRODUCT";return result
    if row.get("show_times")!=list(SHOWS) or row.get("venue")!="臺北大巨蛋":
        result["decision"]="HOLD_SHOW_OR_VENUE";return result
    if row.get("general_prices")!=list(GENERAL) or row.get("accessible_prices")!=list(ACCESSIBLE):
        result["decision"]="HOLD_PRICE_ROLE";return result
    if row.get("general_sale")!="2026-10-04T14:00:00+08:00" or row.get("ticket_release")!="2026-10-13T18:00:00+08:00":
        result["decision"]="HOLD_SALE_RELEASE_ROLE";return result
    if row.get("shuttle_sale")!="2026-10-11T12:00:00+08:00":
        result["decision"]="HOLD_SHUTTLE_SALE_ROLE";return result
    for key in ("ticket_session_id","checkout_url","inventory","formal_accepted","golden_accepted","shuttle_is_concert_admission"):
        if key in row and row[key] is not None:
            result["decision"]="HOLD_UNVERIFIED_CLAIM";return result
    roles=(("show_times","SHOW_TIME_NOT_SALE",CONCERT),
           ("venue","VENUE_NOT_TRANSPORT_PICKUP",CONCERT),
           ("general_prices","CONCERT_ADVERTISED_GENERAL_PRICE_NOT_STOCK",CONCERT),
           ("accessible_prices","ACCESSIBLE_ADMISSION_NOT_GENERAL_MIN",CONCERT),
           ("general_sale","GENERAL_SALE_START_NOT_SHOW",CONCERT),
           ("ticket_release","HISTORICAL_RELEASE_NOT_CURRENT_STOCK",CONCERT),
           ("shuttle_routes","SEPARATE_TRANSPORT_PRODUCT_NOT_ADMISSION",SHUTTLE),
           ("shuttle_sale","TRANSPORT_SALE_NOT_CONCERT_SALE",SHUTTLE))
    result["candidateFields"]=[{"field":key,"value":row[key],"role":role,
        "source":source,"observed_at":observed_at,"decision":"REVIEW"} for key,role,source in roles]
    result["decision"]="REVIEW_TWO_DISTINCT_ACTIVITY_PATHS_NO_TICKET_SESSION"
    return result
