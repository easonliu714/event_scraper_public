"""P30-L9-DG: exact public tixCraft game rows; no checkout/session inference."""
from datetime import datetime
from urllib.parse import urlsplit
DETAIL = "https://tixcraft.com/activity/detail/26_forever"
GAME = "https://tixcraft.com/activity/game/26_forever"
SHOWS = ("2026-11-28T19:00:00+08:00", "2026-11-29T19:00:00+08:00")
TITLE = "新光人壽冠名贊助 F✦FOREVER 恆星之城・光年赴約・臺北 限定場演唱會"
def exact(url, expected):
    if not isinstance(url, str): return False
    try:
        a, b = urlsplit(url), urlsplit(expected)
        return a.scheme == b.scheme == "https" and a.netloc == b.netloc and a.path == b.path and not a.query and not a.fragment
    except ValueError: return False
def inspect(row, observed_at):
    out = {"gate":"P30-L9-DG","canonicalPlatformId":"03","decision":"HOLD_SOURCE",
           "candidateFields":[],"acceptedFields":0,"ticketSessionIdsVerified":0,
           "goldenAccepted":0,"published":False,"releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t = datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.utcoffset() is None: raise ValueError()
    except (ValueError,TypeError,AttributeError):
        out["decision"]="HOLD_OBSERVATION"; return out
    if not isinstance(row,dict): return out
    if not exact(row.get("detail_url"),DETAIL) or not exact(row.get("game_url"),GAME):
        out["decision"]="HOLD_EXACT_ACTIVITY_GAME_PATH"; return out
    if row.get("detail_title") != TITLE or row.get("game_title") != TITLE:
        out["decision"]="HOLD_SAME_EVENT_TITLE"; return out
    # Official activity terms require member registration and phone verification
    # before purchase. This is a checkout access gate, never a ticket Session ID.
    if row.get("purchase_requires_membership") is not True or row.get("purchase_requires_phone_verification") is not True:
        out["decision"]="HOLD_CHECKOUT_ACCESS_REQUIREMENTS_UNVERIFIED"; return out
    rows = row.get("rows")
    if not isinstance(rows,list) or len(rows)!=4:
        out["decision"]="HOLD_FOUR_GAME_ROWS"; return out
    expected=[(SHOWS[0],True),(SHOWS[0],False),(SHOWS[1],True),(SHOWS[1],False)]
    for actual,(show,priority) in zip(rows,expected):
        if not isinstance(actual,dict) or set(actual)!={"show","priority","venue","button"}:
            out["decision"]="HOLD_ROW_SCHEMA"; return out
        if actual["show"]!=show or type(actual["priority"]) is not bool or actual["priority"]!=priority or actual["venue"]!="臺北大巨蛋" or actual["button"]!="Find tickets":
            out["decision"]="HOLD_ROW_SHOW_PRIORITY"; return out
    for key in ("ticket_session_id","session_ids","checkout_url","inventory","sold_out","seat_status","golden_accepted"):
        if key in row and row[key] is not None:
            out["decision"]="HOLD_UNVERIFIED_GAME_CLAIM"; return out
    fields=[("purchase_requires_membership",DETAIL,"MEMBERSHIP_REQUIRED_NOT_SESSION_ACCESS"),
            ("purchase_requires_phone_verification",DETAIL,"PHONE_VERIFICATION_REQUIRED_NOT_CHECKOUT_PROOF"),
            ("game_url",GAME,"PUBLIC_GAME_ROUTE_NOT_CHECKOUT"),
            ("rows",GAME,"FOUR_SHOW_PRIORITY_ROWS_NOT_SESSION_IDS"),
            ("detail_title",DETAIL,"SAME_EVENT_IDENTITY_NOT_STOCK")]
    out["candidateFields"]=[{"field":field,"value":row[field],"source":source,
        "observed_at":observed_at,"role":role,"decision":"REVIEW"} for field,source,role in fields]
    out["decision"]="REVIEW_GAME_FOUR_ROWS_NO_SESSION_ID_OR_STOCK"
    return out
