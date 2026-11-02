"""Read-only P30-VENUE-02BS TMC official event identity and role checks."""
from datetime import datetime
from urllib.parse import urlsplit
LIST="https://www.tmc.taipei/tw/blog/show"
DETAIL="https://www.tmc.taipei/tw/blog/show/2026SungNien-Yu"
TICKET="https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2"
TICKET_SESSION_LIST="https://kham.com.tw/application/UTK02/UTK0201_00.aspx?PRODUCT_ID=P1DF32E2"
TITLE="小宇 宋念宇 《不，完美的人》 演唱會"
def exact(actual, expected):
    if not isinstance(actual,str): return False
    try:
        a,b=urlsplit(actual),urlsplit(expected)
        return a.scheme==b.scheme=="https" and a.netloc==b.netloc and a.path==b.path and a.query==b.query and not a.fragment
    except ValueError: return False
def inspect(row, observed_at):
    out={"gate":"P30-VENUE-02BS","decision":"HOLD_SOURCE","candidateFields":[],
         "acceptedFields":0,"goldenAccepted":0,"published":False,
         "releaseState":"HARD_HOLD_NO_PUBLICATION"}
    try:
        t=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
        if t.utcoffset() is None: raise ValueError()
    except (ValueError,TypeError,AttributeError):
        out["decision"]="HOLD_TIME";return out
    if not isinstance(row,dict): return out
    for key,expected in (("list_url",LIST),("list_detail_href",DETAIL),
                         ("detail_url",DETAIL),("ticket_href",TICKET)):
        if not exact(row.get(key),expected):
            out["decision"]="HOLD_URL";return out
    if row.get("list_title")!=TITLE or row.get("detail_title")!=TITLE:
        out["decision"]="HOLD_TITLE";return out
    if row.get("list_date")!="2026-11-07" or row.get("show")!="2026-11-07T19:30+08:00":
        out["decision"]="HOLD_DATE";return out
    if row.get("venue")!="臺北流行音樂中心 表演廳":
        out["decision"]="HOLD_VENUE";return out
    if row.get("prices")!=[4280,3880,3480,2880,2480,1880]:
        out["decision"]="HOLD_PRICE";return out
    if row.get("published_at")!="2026-08-11":
        out["decision"]="HOLD_PUBLICATION_ROLE";return out
    # Corroborate venue show against the public KHAM session-selection page.
    # Two rows share show time but differ by wheelchair admission role; do not
    # combine prices or infer availability from struck-through text.
    if not exact(row.get("ticket_session_list_url"),TICKET_SESSION_LIST):
        out["decision"]="HOLD_TICKET_SESSION_LIST_URL";return out
    if row.get("ticket_session_list_title")!="2026 小宇 宋念宇《不，完美的人》演唱會":
        out["decision"]="HOLD_TICKET_SESSION_LIST_TITLE";return out
    standard={"show":"2026-11-07T19:30+08:00","venue":"臺北流行音樂中心 表演廳",
              "label":"","displayed_prices":[1880,2480,2880,3480,3880,4280],
              "struck_through":True}
    wheelchair={"show":"2026-11-07T19:30+08:00","venue":"臺北流行音樂中心 表演廳",
                "label":"輪椅席","displayed_prices":[3480,4280],"struck_through":False}
    if row.get("ticket_standard_row")!=standard or row.get("ticket_wheelchair_row")!=wheelchair:
        out["decision"]="HOLD_TICKET_ROW_ROLE";return out
    for key in ("ticket_session_id","checkout_url","inventory","golden_accepted"):
        if key in row and row[key] is not None:
            out["decision"]="HOLD_UNVERIFIED_CLAIM";return out
    for field,role,source in [
        ("list_date","VENUE_LIST_DATE",LIST),
        ("show","VENUE_SHOW_NOT_SALE",DETAIL),
        ("venue","VENUE",DETAIL),
        ("prices","VENUE_PRICE_BANDS_NOT_CHECKOUT",DETAIL),
        ("published_at","BULLETIN_DATE_NOT_SALE",DETAIL),
        ("ticket_href","DIRECT_KHAM_PRODUCT_NOT_TICKET_SESSION",DETAIL),
        ("ticket_session_list_url","TICKET_PRODUCT_SESSION_SELECTION_NOT_SESSION_ID",TICKET_SESSION_LIST),
        ("ticket_standard_row","KHAM_STANDARD_STRUCK_PRICE_NOT_INVENTORY",TICKET_SESSION_LIST),
        ("ticket_wheelchair_row","KHAM_ACCESSIBLE_ROW_NOT_GENERAL_ADMISSION",TICKET_SESSION_LIST)]:
        out["candidateFields"].append({"field":field,"value":row[field],"role":role,
                                       "source":source,"observed_at":observed_at,"decision":"REVIEW"})
    out["decision"]="REVIEW_EXACT_LIST_DETAIL_HOLD_TICKET_SESSION"
    return out
