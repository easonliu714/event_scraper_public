"""P30-VENUE-02BC: New Taipei Art Center official November bulletin -> OPENTIX #05 event edge.
Evidence-only; venue bulletin sid is NOT a ticket Event ID. Per-performance ticket sessions HOLD.
"""
from datetime import date
from urllib.parse import urlsplit

INDEX = "https://www.culture.ntpc.gov.tw/artcenter_chi/sitesearch"
BULLETIN = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168"
OPENTIX = "https://www.opentix.life/event/2086734015886159873"
VENUE_TITLE = "《屁屁偵探》南方島嶼的神秘遺跡"
OPENTIX_TITLE = "銀河谷音劇團《屁屁偵探》南方島嶼的神秘遺跡"
SHOWS = ("2026-11-07T14:30", "2026-11-08T10:30", "2026-11-08T14:30")
CONFLICT_DATE = "2026-11-10"
CONFLICT_LABEL = "日"  # source bulletin says Sunday, calendar date is Tuesday

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BC", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": [], "conflicts": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("index_url"), INDEX):
        return dict(out, decision="HOLD_VENUE_INDEX")
    if not exact_url(x.get("index_bulletin_href"), BULLETIN) or not exact_url(x.get("bulletin_url"), BULLETIN):
        return dict(out, decision="HOLD_SAME_SID_BULLETIN")
    if x.get("venue_title") != VENUE_TITLE or x.get("opentix_title") != OPENTIX_TITLE:
        return dict(out, decision="HOLD_EXPLICIT_CROSS_SOURCE_TITLE")
    if not exact_url(x.get("venue_ticket_href"), OPENTIX) or not exact_url(x.get("opentix_detail_url"), OPENTIX):
        return dict(out, decision="HOLD_CANONICAL_OPENTIX_EVENT_URL")
    if x.get("venue_name") != "新北市藝文中心演藝廳" or x.get("opentix_venue") != "新北市藝文中心演藝廳":
        return dict(out, decision="HOLD_VENUE_MATCH")
    if x.get("venue_showtimes") != SHOWS:
        return dict(out, decision="HOLD_VENUE_SHOWTIME_SET")
    if (x.get("conflict_date"), x.get("conflict_weekday")) != (CONFLICT_DATE, CONFLICT_LABEL):
        return dict(out, decision="HOLD_BULLETIN_CONFLICT_EVIDENCE")
    if date.fromisoformat(CONFLICT_DATE).weekday() != 1:
        return dict(out, decision="HOLD_CALENDAR_CALCULATION")
    if any(x.get(k) is not None for k in ("ticket_session_ids", "ticket_session_prices", "inventory", "published_event")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    out["candidateFields"] = [
        {"field": "opentix_event_url", "value": OPENTIX, "source": "NTPC_ARTCENTER_VENUE",
         "source_url": BULLETIN, "observed_at": observed_at, "role": "VENUE_DIRECT_OPENTIX_EVENT_HREF", "decision": "REVIEW"},
        {"field": "venue_showtimes", "value": list(SHOWS), "source": "NTPC_ARTCENTER_VENUE",
         "source_url": BULLETIN, "observed_at": observed_at, "role": "VENUE_BULLETIN_SHOWS_NOT_TICKET_SESSIONS", "decision": "REVIEW"},
        {"field": "ticket_event_id", "value": "2086734015886159873", "source": "OPENTIX_05",
         "source_url": OPENTIX, "observed_at": observed_at, "role": "OPENTIX_EVENT_PATH_NOT_SESSION_ID", "decision": "REVIEW"}]
    out["conflicts"] = [{"source": "NTPC_ARTCENTER_VENUE", "source_url": BULLETIN,
                         "observed_at": observed_at, "role": "OTHER_EVENT_2026_11_10_WEEKDAY",
                         "observed": "11/10〔日〕", "calendar": "Tuesday", "decision": "HOLD_WEEKDAY_CONFLICT"}]
    return dict(out, decision="REVIEW_EVENT_LINK_HOLD_TICKET_SESSIONS_AND_OTHER_ROW_WEEKDAY")
