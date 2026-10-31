"""OPENTIX #05 event BODY: two descriptive performances, eight internal
program blocks and three ticket price tiers. Program blocks are NOT ticket
session IDs, and event-level discounts are NOT verified per-session prices.
Source https://www.opentix.life/event/2099688567429373953
"""
import datetime
from urllib.parse import urlsplit

SOURCE = "https://www.opentix.life/event/2099688567429373953"
EVENT_ID = "2099688567429373953"
SHOWS = {
    "2026-11-28": (("13:00", "14:20"), ("14:35", "15:50"), ("16:20", "17:35"), ("17:50", "19:05")),
    "2026-11-29": (("11:00", "12:20"), ("12:35", "13:50"), ("14:50", "16:05"), ("16:20", "17:35")),
}

def exact_source(value):
    if not isinstance(value, str):
        return False
    x = urlsplit(value)
    return (x.scheme, x.netloc, x.path, x.query, x.fragment) == ("https", "www.opentix.life", "/event/" + EVENT_ID, "", "")

def inspect(record, observed_at):
    out = {"gate": "P30-VENUE-02AU", "acceptedFields": 0, "goldenAccepted": 0,
           "published": False, "provenance": []}
    try:
        datetime.date.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return dict(out, decision="HOLD_OBSERVED_AT")
    if not isinstance(record, dict) or not exact_source(record.get("url")) or record.get("event_id") != EVENT_ID:
        return dict(out, decision="HOLD_CANONICAL_EVENT_ID")
    if record.get("ticket_session_ids") is not None or record.get("inventory") is not None or record.get("shortlink_redirect_verified") is not False:
        return dict(out, decision="HOLD_TICKET_SESSION_OR_REDIRECT_UNVERIFIED")
    if record.get("venue") != "樹林藝文中心演藝廳" or record.get("title") != "身體我的名片":
        return dict(out, decision="HOLD_TITLE_VENUE")
    if record.get("artist_count") != 16 or record.get("artist_role") != "PROGRAM_ARTISTS_NOT_TICKETS":
        return dict(out, decision="HOLD_ARTIST_COUNT_ROLE")
    if record.get("price_role") != "EVENT_FACE_AND_LIMITED_DISCOUNT" or record.get("face_price_ntd") != 1000 or record.get("limited_prices_ntd") != [650, 800]:
        return dict(out, decision="HOLD_PRICE_TIER_ROLE")
    if record.get("per_session_price") is not None or record.get("bundle_price") is not None:
        return dict(out, decision="HOLD_PRICE_NOT_SESSION_OR_BUNDLE")
    shows = record.get("description_shows")
    if not isinstance(shows, dict) or set(shows) != set(SHOWS):
        return dict(out, decision="HOLD_TWO_DESCRIPTION_SHOWS")
    for date, expected in SHOWS.items():
        blocks = shows[date]
        if not isinstance(blocks, list) or len(blocks) != 4:
            return dict(out, decision="HOLD_FOUR_PROGRAM_BLOCKS")
        for i, expected_times in enumerate(expected):
            row = blocks[i]
            if not isinstance(row, dict) or row.get("role") != "INTERNAL_PROGRAM_BLOCK" or (row.get("start"), row.get("end")) != expected_times:
                return dict(out, decision="HOLD_PROGRAM_BLOCK_LOCAL_TIME")
            if row.get("ticket_session_id") is not None or row.get("ticket_inventory") is not None:
                return dict(out, decision="HOLD_PROGRAM_BLOCK_NOT_TICKET_SESSION")
            out["provenance"].append({"source": "OPENTIX_CANONICAL_05", "source_url": SOURCE,
                                      "observed_at": observed_at, "date": date,
                                      "role": "INTERNAL_PROGRAM_BLOCK_NOT_TICKET_SESSION",
                                      "start": expected_times[0], "end": expected_times[1],
                                      "decision": "REVIEW"})
    out["provenance"].append({"source": "OPENTIX_CANONICAL_05", "source_url": SOURCE,
                              "observed_at": observed_at, "role": "EVENT_PRICE_TIERS_NOT_SESSION_PRICE",
                              "face_price": 1000, "limited_prices": [650, 800], "decision": "REVIEW"})
    return dict(out, decision="HOLD_EIGHT_PROGRAM_BLOCKS_NOT_TICKET_SESSIONS")
