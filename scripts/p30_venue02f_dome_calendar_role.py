#!/usr/bin/env python3
"""P30-VENUE-02F: Taipei Dome official calendar text-role refusal.

One official calendar cell is not one verified public event. Occupancy is not
an event, combined names can contain multiple subevents, and the calendar
date is not a verified show start. No live GET, ticket link, or publication.
"""
from __future__ import annotations
import re
from datetime import date
from urllib.parse import urlsplit

RELEASE = "HARD_HOLD_NO_PUBLICATION"
CALENDAR = "https://www.taipeidome.com.tw/Web/dome/"
OCCUPANCY = ("場館已安排使用", "場館已承租")
CATEGORIES = ("演唱會", "球賽", "展覽", "活動")
MAX_CELL_CHARS = 400

def inspect_calendar_cell(day: str, entries: list[str], source_url: str = CALENDAR) -> dict:
    """Classify one bounded cell from the official calendar, never accept fields."""
    base = dict(source="TAIPEI_DOME_OFFICIAL", decision="HOLD_INPUT",
                calendarRole="UNKNOWN", identity="UNKNOWN",
                officialDetailVerified=False, eventDateAccepted=False,
                ticketEventId=None, acceptedFields=0, goldenAccepted=0,
                published=False, liveHttpGetThisCI=0, releaseState=RELEASE)
    if (not isinstance(day, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", day)
            or not isinstance(entries, list) or not 1 <= len(entries) <= 5
            or not all(isinstance(x, str) and x.strip() for x in entries)
            or sum(len(x) for x in entries) > MAX_CELL_CHARS
            or source_url != CALENDAR):
        return base
    try:
        date.fromisoformat(day)
    except ValueError:
        return dict(base, decision="HOLD_INVALID_CALENDAR_DAY")
    entries = [" ".join(x.split()) for x in entries]
    if len(entries) == 2 and tuple(entries) == OCCUPANCY:
        return dict(base, decision="REVIEW_OCCUPANCY_ONLY_NOT_PUBLIC_EVENT",
                    calendarRole="VENUE_OCCUPANCY_ONLY")
    if any(x in OCCUPANCY for x in entries):
        return dict(base, decision="HOLD_MIXED_OCCUPANCY_AND_EVENT")
    if len(entries) != 2 or entries[0] not in CATEGORIES:
        return dict(base, decision="HOLD_UNKNOWN_CALENDAR_CARD_ROLE")
    title = entries[1]
    if len(title) < 4 or len(title) > 220 or title in CATEGORIES:
        return dict(base, decision="HOLD_UNIDENTIFIABLE_PUBLIC_TITLE")
    if "、" in title and ("總決賽" in title and "演唱會" in title):
        return dict(base, decision="HOLD_POSSIBLE_MULTIPLE_EVENTS_ONE_CELL",
                    calendarRole="PUBLIC_EVENT_CANDIDATE_MULTI",
                    identity="UNKNOWN_MULTI_EVENT")
    return dict(base, decision="REVIEW_NAMED_PUBLIC_EVENT_DETAIL_NOT_VERIFIED",
                calendarRole="PUBLIC_EVENT_CANDIDATE",
                identity="REVIEW_CALENDAR_TITLE_ONLY")

if __name__ == "__main__":
    raise SystemExit("NO_DIRECT_EXECUTION: no live GET, publisher or ticket purchase")
