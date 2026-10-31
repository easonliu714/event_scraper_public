"""P30-VENUE-02AQ: Fuzhong15 P0 New Taipei same-film two screening rows.

Film detail SID is not ticket event/session ID. Official date/role evidence REVIEW only.
"""
import datetime
import hashlib
import re
from urllib.parse import urlsplit, parse_qs

LIST_URL = "https://www.fuzhong15.ntpc.gov.tw/xcmovie?bdate=2026-11-01&edate=2026-11-30&xsmsid=0M361641875264878260"
FILM_SID = "0Q289851686942598501"
DETAIL_URL = "https://www.fuzhong15.ntpc.gov.tw/xcmovie/cont?sid=" + FILM_SID + "&xsmsid=0M361641875264878260"
TITLE = "96分鐘"
SCREENINGS = (("2026-11-08", "16:00", "售"), ("2026-11-28", "16:20", "售"))
DETAIL_UPDATED = "2026-10-16"
DURATION_MIN = 118

def _exact_detail(url):
    if not isinstance(url,str):
        return False
    try:
        u=urlsplit(url)
        if (u.scheme,u.netloc,u.path,u.fragment)!=("https","www.fuzhong15.ntpc.gov.tw","/xcmovie/cont",""):
            return False
        return parse_qs(u.query,strict_parsing=True)=={
            "sid":[FILM_SID],"xsmsid":["0M361641875264878260"]}
    except ValueError:
        return False

def inspect(index, detail, observed_at):
    out=dict(gate="P30-VENUE-02AQ",source="FUZHONG15_P0_NEW_TAIPEI",
             acceptedFields=0,goldenAccepted=0,published=False,
             candidateProvenance=[],ticketEventIdVerified=False,
             ticketSessionIdsVerified=False,inventoryVerified=False)
    try:
        if not isinstance(observed_at,str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}",observed_at):
            raise ValueError("format")
        datetime.date.fromisoformat(observed_at)
    except ValueError:
        return dict(out,decision="HOLD_OBSERVED_AT")
    if index.get("url")!=LIST_URL or not _exact_detail(index.get("detail_url")):
        return dict(out,decision="HOLD_OFFICIAL_MONTH_INDEX_LINK")
    if not _exact_detail(detail.get("url")) or detail.get("film_sid")!=FILM_SID:
        return dict(out,decision="HOLD_FILM_SID_IDENTITY")
    if index.get("title")!=TITLE or detail.get("title")!=TITLE:
        return dict(out,decision="HOLD_EXACT_FILM_TITLE")
    if tuple(map(tuple,index.get("screenings",[])))!=SCREENINGS:
        return dict(out,decision="HOLD_MONTHLY_LIST_SCREENINGS")
    if tuple(map(tuple,detail.get("screenings",[])))!=tuple(x[:2] for x in SCREENINGS):
        return dict(out,decision="HOLD_DETAIL_SCREENING_PARITY")
    if detail.get("updated_at")!=DETAIL_UPDATED:
        return dict(out,decision="HOLD_UPDATE_DATE_NOT_SHOWTIME")
    if detail.get("duration_minutes")!=DURATION_MIN:
        return dict(out,decision="HOLD_DURATION_NOT_SCREENING_TIME")
    if any(x is not None for x in (detail.get("ticket_event_id"),detail.get("ticket_session_ids"),
                                   detail.get("ticket_price"),detail.get("inventory"))):
        return dict(out,decision="HOLD_TICKET_ID_PRICE_INVENTORY_UNVERIFIED")
    roles=(
        ("INDEX",LIST_URL,"MONTH_FILTER_2026_11","2026-11"),
        ("INDEX",LIST_URL,"FILM_TITLE",TITLE),
        ("INDEX",LIST_URL,"FILM_SID_NOT_TICKET_ID",FILM_SID),
        ("INDEX",LIST_URL,"FIRST_SCREENING_SALE_LABEL",repr(SCREENINGS[0])),
        ("INDEX",LIST_URL,"SECOND_SCREENING_SALE_LABEL",repr(SCREENINGS[1])),
        ("DETAIL",DETAIL_URL,"SAME_FILM_TITLE",TITLE),
        ("DETAIL",DETAIL_URL,"FIRST_SCREENING_DATE_TIME",repr(SCREENINGS[0][:2])),
        ("DETAIL",DETAIL_URL,"SECOND_SCREENING_DATE_TIME",repr(SCREENINGS[1][:2])),
        ("DETAIL",DETAIL_URL,"UPDATE_DATE_NOT_SCREENING",DETAIL_UPDATED),
        ("DETAIL",DETAIL_URL,"FILM_DURATION_NOT_SESSION",str(DURATION_MIN)),
    )
    for src,url,role,value in roles:
        out["candidateProvenance"].append(dict(source=src,source_url=url,observed_at=observed_at,
            role=role,valueSHA256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            decision="REVIEW_NOT_FORMALLY_ACCEPTED"))
    return dict(out,decision="HOLD_FILM_SID_NOT_TICKET_SESSION_AND_PRICE_UNVERIFIED")
