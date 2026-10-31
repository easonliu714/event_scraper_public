"""P30-VENUE-02AV: Official New Taipei November monthly bulletin weekday
conflicts quarantined per row; direct OPENTIX event link is not a ticket session.
https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168
https://www.opentix.life/event/2029816885442543616
"""
import datetime
from urllib.parse import urlsplit

GATE = "P30-VENUE-02AV"
VENUE_URL = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168"
OPENTIX_URL = "https://www.opentix.life/event/2029816885442543616"
EVENT_ID = "2029816885442543616"
TITLE = "親子音樂劇《阿甯咕的爸鼻不見了？》小兒子動畫劇場 ③"
VENUE = "新北市藝文中心演藝廳"
SHOWS = (("2026-11-21", "14:30", "六"), ("2026-11-22", "10:30", "日"), ("2026-11-22", "14:30", "日"))
CONFLICTS = (("海歸人聲合唱團 《詩劇迴影》", "2026-11-10", "日"),
             ("李昀芮18愛無限 大提琴獨奏會", "2026-11-20", "六"))
WEEKDAYS = "一二三四五六日"

def exact(url, expected):
    if not isinstance(url, str):
        return False
    a, b = urlsplit(url), urlsplit(expected)
    return (a.scheme, a.netloc, a.path, a.query, a.fragment) == (b.scheme, b.netloc, b.path, b.query, b.fragment)

def weekday(date):
    return WEEKDAYS[datetime.date.fromisoformat(date).weekday()]

def inspect(record, observed_at):
    out = {"gate": GATE, "acceptedFields": 0, "goldenAccepted": 0, "published": False,
           "provenance": [], "quarantined": []}
    try:
        datetime.date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if not isinstance(record, dict) or not exact(record.get("venue_url"), VENUE_URL) or record.get("venue_sid") != "0Q152372523738311866":
        return dict(out, decision="HOLD_BULLETIN_SID")
    if record.get("updated_at") != "2026-10-28" or record.get("update_role") != "BULLETIN_UPDATE_NOT_SHOW":
        return dict(out, decision="HOLD_UPDATE_DATE_ROLE")
    if not exact(record.get("opentix_url"), OPENTIX_URL) or record.get("event_id") != EVENT_ID or record.get("linked_event_canonical_url") != OPENTIX_URL:
        return dict(out, decision="HOLD_DIRECT_OPENTIX_EVENT_ID")
    if record.get("venue_title") != TITLE or record.get("opentix_title") != TITLE or record.get("venue") != VENUE or record.get("opentix_venue") != VENUE:
        return dict(out, decision="HOLD_TITLE_VENUE")
    if record.get("opentix_date_range") != ("2026-11-21", "2026-11-22"):
        return dict(out, decision="HOLD_EVENT_DATE_RANGE")
    if record.get("ticket_session_ids") is not None or record.get("inventory") is not None or record.get("per_session_price") is not None:
        return dict(out, decision="HOLD_NO_TICKET_SESSION_OR_PRICE")
    rows = record.get("shows")
    if not isinstance(rows, list) or len(rows) != len(SHOWS):
        return dict(out, decision="HOLD_THREE_SHOWS")
    for i, (date, time, day) in enumerate(SHOWS):
        r = rows[i]
        if not isinstance(r, dict) or (r.get("date"), r.get("time"), r.get("weekday")) != (date, time, day):
            return dict(out, decision="HOLD_SHOW_TEXT")
        if weekday(date) != day:
            return dict(out, decision="HOLD_SHOW_WEEKDAY")
        if r.get("role") != "VENUE_DESCRIPTIVE_PERFORMANCE" or r.get("ticket_session_id") is not None:
            return dict(out, decision="HOLD_SHOW_NOT_SESSION")
        out["provenance"].append({"source": "NTPC_ARTCENTER_OFFICIAL", "source_url": VENUE_URL,
            "observed_at": observed_at, "role": "VENUE_DESCRIPTIVE_PERFORMANCE",
            "date": date, "time": time, "decision": "REVIEW"})
    other = record.get("conflicts")
    if not isinstance(other, list) or len(other) != len(CONFLICTS):
        return dict(out, decision="HOLD_CONFLICT_ROW_COUNT")
    for i, (title, date, day) in enumerate(CONFLICTS):
        r = other[i]
        if not isinstance(r, dict) or (r.get("title"), r.get("date"), r.get("weekday")) != (title, date, day):
            return dict(out, decision="HOLD_CONFLICT_SOURCE_TEXT")
        if weekday(date) == day:
            return dict(out, decision="HOLD_CONFLICT_EXPECTATION")
        out["quarantined"].append({"source": "NTPC_ARTCENTER_OFFICIAL", "source_url": VENUE_URL,
            "observed_at": observed_at, "title": title, "raw_date": date,
            "raw_weekday": day, "calendar_weekday": weekday(date),
            "role": "DATE_WEEKDAY_CONFLICT", "decision": "HOLD_NO_AUTOCORRECTION"})
    out["provenance"].append({"source": "OPENTIX_CANONICAL_05", "source_url": OPENTIX_URL,
        "observed_at": observed_at, "role": "EVENT_ID_DATE_RANGE_NOT_TICKET_SESSIONS",
        "event_id": EVENT_ID, "decision": "REVIEW"})
    return dict(out, decision="HOLD_EVENT_ID_AND_TWO_WEEKDAY_CONFLICTS_NO_TICKET_SESSIONS")
