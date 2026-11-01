"""P30-VENUE-02BD: NTPC Art Center direct link to multi-venue OPENTIX Murray Event ID.
Venue bulletin showtimes are not independently verified OPENTIX ticket sessions.
"""
from datetime import date
from urllib.parse import urlsplit

BULLETIN = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168"
OPENTIX = "https://www.opentix.life/event/2087017782302437377"
VENUE_TITLE = "《海象莫雷的漂流日誌》親子音樂劇"
TICKET_TITLE = "極致藝術《海象莫雷的漂流日誌》親子音樂劇"
SHOWS = ("2026-11-14T15:00", "2026-11-14T19:30",
         "2026-11-15T11:00", "2026-11-15T15:00")
TICKET_VENUES = ("新北市藝文中心演藝廳", "衛武營國家藝術文化中心戲劇院", "臺中市中山堂")

def exact_url(value, expected):
    if not isinstance(value, str):
        return False
    p, e = urlsplit(value), urlsplit(expected)
    return (p.scheme == e.scheme == "https" and p.netloc == e.netloc
            and p.username is None and p.password is None and p.port is None
            and p.path == e.path and p.query == e.query and not p.fragment)

def inspect(x, observed_at):
    out = {"gate": "P30-VENUE-02BD", "acceptedFields": 0, "ticketSessionIdsVerified": 0,
           "goldenAccepted": 0, "published": False, "candidateFields": []}
    try:
        date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVATION")
    if not isinstance(x, dict) or not exact_url(x.get("venue_bulletin"), BULLETIN):
        return dict(out, decision="HOLD_VENUE_BULLETIN")
    if not exact_url(x.get("venue_ticket_href"), OPENTIX) or not exact_url(x.get("ticket_detail"), OPENTIX):
        return dict(out, decision="HOLD_DIRECT_OPENTIX_EVENT_URL")
    if (x.get("venue_title"), x.get("ticket_title"), x.get("ticket_event_id")) != (VENUE_TITLE, TICKET_TITLE, "2087017782302437377"):
        return dict(out, decision="HOLD_TITLE_EVENT_ID")
    if x.get("venue_showtimes") != SHOWS or x.get("venue_name") != TICKET_VENUES[0]:
        return dict(out, decision="HOLD_LOCAL_VENUE_SHOWTIMES")
    if x.get("ticket_page_venue_choices") != TICKET_VENUES:
        return dict(out, decision="HOLD_MULTIVENUE_EVENT_SCOPE")
    if x.get("venue_showtimes_are_ticket_sessions") is not False:
        return dict(out, decision="HOLD_UNVERIFIED_SESSION_MAPPING")
    if any(x.get(k) is not None for k in ("ticket_session_ids", "session_prices", "inventory",
                                         "published_event", "ticket_button_href")):
        return dict(out, decision="HOLD_UNVERIFIED_TICKET_SESSION")
    out["candidateFields"] = [
        {"field": "venue_showtimes", "value": list(SHOWS), "source": "NTPC_ARTCENTER_VENUE",
         "source_url": BULLETIN, "observed_at": observed_at,
         "role": "VENUE_SHOWS_NOT_TICKET_SESSIONS", "decision": "REVIEW"},
        {"field": "ticket_event_id", "value": "2087017782302437377", "source": "OPENTIX_05",
         "source_url": OPENTIX, "observed_at": observed_at,
         "role": "MULTIVENUE_EVENT_NOT_SESSION_ID", "decision": "REVIEW"},
        {"field": "venue_selection", "value": list(TICKET_VENUES), "source": "OPENTIX_05",
         "source_url": OPENTIX, "observed_at": observed_at,
         "role": "EVENT_VENUE_CHOICES_NOT_CONFIRMED_PERFORMANCE_MAPPING", "decision": "REVIEW"}]
    return dict(out, decision="REVIEW_NTPC_SHOWS_OPENTIX_MULTIVENUE_HOLD_SESSION_MAPPING")
