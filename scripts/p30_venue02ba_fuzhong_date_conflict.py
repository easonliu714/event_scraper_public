"""P30-VENUE-02BA: Fuzhong15 11/29 short-film schedule versus official activity announcement conflict."""
from datetime import date
from urllib.parse import urlsplit, parse_qs

LIST = "https://www.fuzhong15.ntpc.gov.tw/xcmovie?xsmsid=0M361641875264878260"
DETAIL = "https://www.fuzhong15.ntpc.gov.tw/xcmovieintro?xsmsid=0Q292499123701779627"
ANNOUNCE = "https://www.fuzhong15.ntpc.gov.tw/xmdoc/cont?sid=0Q292625317919000726&xsmsid=0N018386180292978812"
LIST_ROWS = (("無塵之地", "2026-11-29T16:00", "索"),
             ("抓耙仔", "2026-11-29T16:00", "索"),
             ("五花肉", "2026-11-22T16:00", "索"))
DETAIL_ROWS = (("無塵之地", "2026-11-29T16:00"),
               ("抓耙仔", "2026-11-29T16:00"),
               ("五花肉", "2026-11-22T16:00"))
ANNOUNCEMENT = ("無塵之地", "五花肉", "抓耙仔")
ANNOUNCEMENT_TIME = "2026-11-29T16:00"

def valid_url(url, path, query):
    if not isinstance(url, str):
        return False
    p = urlsplit(url)
    return (p.scheme == "https" and p.netloc == "www.fuzhong15.ntpc.gov.tw"
            and p.path == path and not p.fragment and p.query == query
            and parse_qs(p.query, keep_blank_values=True) ==
            parse_qs(query, keep_blank_values=True))

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BA", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": [], "provenance": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not valid_url(x.get("list_url"), "/xcmovie", "xsmsid=0M361641875264878260"):
        return dict(out, decision="HOLD_FUZHONG_LIST_SOURCE")
    if not valid_url(x.get("detail_url"), "/xcmovieintro", "xsmsid=0Q292499123701779627"):
        return dict(out, decision="HOLD_FUZHONG_COLLECTION_DETAIL")
    if not valid_url(x.get("announcement_url"), "/xmdoc/cont", "sid=0Q292625317919000726&xsmsid=0N018386180292978812"):
        return dict(out, decision="HOLD_FUZHONG_ANNOUNCEMENT")
    if x.get("list_rows") != LIST_ROWS or x.get("detail_rows") != DETAIL_ROWS:
        return dict(out, decision="HOLD_LIST_DETAIL_FILM_DATE_PARITY")
    if x.get("announcement_titles") != ANNOUNCEMENT or x.get("announcement_datetime") != ANNOUNCEMENT_TIME:
        return dict(out, decision="HOLD_ANNOUNCEMENT_CONTENT")
    if x.get("list_role") != "索_IS_TICKET_REQUEST_NOT_SALE" or x.get("detail_id_role") != "COLLECTION_PAGE_NOT_INDIVIDUAL_FILM_ID":
        return dict(out, decision="HOLD_ADMISSION_OR_COLLECTION_ROLE")
    if any(x.get(k) is not None for k in ("ticket_session_id", "verified_ticket_url", "canonical_screening_id",
                                          "available_for_purchase", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_PROMOTION")
    out["candidateFields"] = [
        {"field": "film_screening_datetime", "film": title, "value": dt, "source": "FUZHONG15_VENUE",
         "source_url": LIST, "observed_at": observed_at, "role": "LIST_SCREENING_ROW", "decision": "REVIEW"}
        for title, dt, _ in LIST_ROWS]
    out["provenance"] = [
        {"source": "FUZHONG15_VENUE", "source_url": DETAIL, "observed_at": observed_at,
         "role": "COLLECTION_DETAIL_FILM_DATES", "decision": "REVIEW"},
        {"source": "FUZHONG15_VENUE", "source_url": ANNOUNCE, "observed_at": observed_at,
         "role": "EVENT_ANNOUNCEMENT_CLAIMS_THREE_FILMS_NOV29", "decision": "HOLD_CONFLICT_WITH_FILM_INTRO_NOV22"}]
    return dict(out, decision="HOLD_NOV29_ANNOUNCEMENT_VS_NOV22_FILM_DETAIL_CONFLICT")
