"""P30-L9-CI: Official OPENTIX #05 event/venue direct-link parity.
Source: https://www.opentix.life/event/2086734015886159873
Venue: https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168
Independent public source read 2026-11-01; no CI network or publication.
"""
import datetime
from urllib.parse import urlsplit

GATE = "P30-L9-CI"
VENUE_URL = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866&sq=&xsmsid=0G269629106251547168"
OPENTIX_URL = "https://www.opentix.life/event/2086734015886159873"
EVENT_ID = "2086734015886159873"
TITLE = "銀河谷音劇團《屁屁偵探》南方島嶼的神秘遺跡"
VENUE = "新北市藝文中心演藝廳"
SHOWS = (("2026-11-07", "14:30", "六"), ("2026-11-08", "10:30", "日"), ("2026-11-08", "14:30", "日"))
WEEKDAYS = "一二三四五六日"

def exact(url, expected):
    if not isinstance(url, str):
        return False
    a, b = urlsplit(url), urlsplit(expected)
    return (a.scheme, a.netloc, a.path, a.query, a.fragment) == (b.scheme, b.netloc, b.path, b.query, b.fragment)

def inspect(record, observed_at):
    out = {"gate": GATE, "acceptedFields": 0, "goldenAccepted": 0, "published": False, "provenance": []}
    try:
        datetime.date.fromisoformat(observed_at)
    except (ValueError, TypeError):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if not isinstance(record, dict) or not exact(record.get("venue_url"), VENUE_URL):
        return dict(out, decision="HOLD_VENUE_SOURCE")
    if not exact(record.get("opentix_url"), OPENTIX_URL) or record.get("event_id") != EVENT_ID:
        return dict(out, decision="HOLD_CANONICAL_EVENT_ID")
    if record.get("linked_event_canonical_url") != OPENTIX_URL:
        return dict(out, decision="HOLD_DIRECT_LINK_PARITY")
    if record.get("venue_title") != TITLE or record.get("opentix_title") != TITLE:
        return dict(out, decision="HOLD_CROSS_SOURCE_TITLE")
    if record.get("venue") != VENUE or record.get("opentix_venue") != VENUE:
        return dict(out, decision="HOLD_CROSS_SOURCE_VENUE")
    venues = record.get("opentix_venues")
    if not isinstance(venues, list) or len(venues) != 9 or len(set(venues)) != 9 or VENUE not in venues:
        return dict(out, decision="HOLD_NINE_DISTINCT_VENUES")
    if record.get("ticket_session_ids") is not None or record.get("inventory") is not None or record.get("session_price") is not None:
        return dict(out, decision="HOLD_NO_STATIC_TICKET_SESSION")
    if record.get("venues_are_sessions") is not False or record.get("sale_is_showtime") is not False:
        return dict(out, decision="HOLD_VENUE_SALE_ROLE")
    rows = record.get("shows")
    if not isinstance(rows, list) or len(rows) != len(SHOWS):
        return dict(out, decision="HOLD_SHOW_COUNT")
    for i, (date, time, day) in enumerate(SHOWS):
        row = rows[i]
        if not isinstance(row, dict) or (row.get("date"), row.get("time"), row.get("weekday")) != (date, time, day):
            return dict(out, decision="HOLD_SHOW_LOCAL_TEXT")
        if WEEKDAYS[datetime.date.fromisoformat(date).weekday()] != day:
            return dict(out, decision="HOLD_WEEKDAY_CONFLICT")
        if row.get("role") != "VENUE_DESCRIPTIVE_PERFORMANCE" or row.get("ticket_session_id") is not None:
            return dict(out, decision="HOLD_SHOW_NOT_TICKET_SESSION")
        out["provenance"].append({"source": "NTPC_ARTCENTER_OFFICIAL", "source_url": VENUE_URL,
            "observed_at": observed_at, "role": "VENUE_DESCRIPTIVE_PERFORMANCE",
            "date": date, "time": time, "decision": "REVIEW"})
    out["provenance"].append({"source": "OPENTIX_CANONICAL_05", "source_url": OPENTIX_URL,
        "observed_at": observed_at, "role": "MULTI_VENUE_EVENT_ID_NOT_SESSION",
        "event_id": EVENT_ID, "venue_count": 9, "decision": "REVIEW"})
    return dict(out, decision="HOLD_EVENT_PARITY_NO_TICKET_SESSION_IDS")
