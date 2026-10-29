#!/usr/bin/env python3
"""P30-L9-AR: bounded FamiTicket public-text role diagnostic, no promotion.

Source evidence is a public detail text view, not a live HTML adapter run.
An event-date line, an event-hours label, ticket variants, and a refund
deadline have different semantic roles. Never conflate these as a sale date,
one performance session, or one canonical price.
"""
from __future__ import annotations
import re
from datetime import date
import p30_l3b_a_famiticket as frozen

RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_LINES = 240
MAX_CHARS = 16000
EVENT_RANGE = re.compile(r"^(20\d{2})\.(\d{2})\.(\d{2})[-~～](\d{2})$")
HOURS = re.compile(r"^活動時間[│|]\s*\d{2}:\d{2}\s*[-~～]\s*\d{2}:\d{2}$")
VENUE = re.compile(r"^活動地點[│|]\s*\S.{1,120}$")
TICKET_VARIANT = re.compile(r"^(單日票|雙日票)\s*\d{1,6}\s*元$")

def inspect_public_text(lines: list[str], detail_url: str, expected_title: str) -> dict:
    """Review only the uniquely bounded 《活動資訊》 block of one official detail."""
    base = dict(decision="HOLD_INPUT", source="FAMITICKET_07",
                eventDateRole="UNKNOWN", hoursRole="UNKNOWN",
                venueRole="UNKNOWN", ticketVariantCount=0,
                refundCutoffOutsideEventBlock=False, identity="UNKNOWN",
                acceptedFields=0, goldenAccepted=0, published=False,
                releaseState=RELEASE, liveHttpGetThisRun=0)
    if (not isinstance(lines, list) or not lines or len(lines) > MAX_LINES
            or not all(isinstance(x, str) for x in lines)
            or sum(len(x) for x in lines) > MAX_CHARS
            or not isinstance(expected_title, str) or not 2 <= len(expected_title) <= 180
            or not frozen.allowed(detail_url, detail=True)):
        return base
    norm = lambda s: " ".join(s.split())
    clean = [norm(x) for x in lines]
    marks = [i for i, x in enumerate(clean) if "《活動資訊》" in x]
    if len(marks) != 1:
        return dict(base, decision="HOLD_ACTIVITY_SECTION_NOT_UNIQUE")
    start = marks[0] + 1
    ends = [i for i in range(start, len(clean)) if "《活動介紹》" in clean[i]]
    if len(ends) != 1 or not 2 <= ends[0] - start <= 16:
        return dict(base, decision="HOLD_SECTION_BOUNDARY")
    local = clean[start:ends[0]]
    if local[0] != norm(expected_title):
        return dict(base, decision="HOLD_TITLE_IDENTITY")
    base["identity"] = "REVIEW_EXACT_SECTION_TITLE"
    if len(local) < 5:
        return dict(base, decision="HOLD_LOCAL_ROLES_MISSING")
    d = EVENT_RANGE.fullmatch(local[1])
    if not d:
        return dict(base, decision="HOLD_UNLABELED_OR_AMBIGUOUS_EVENT_DATE")
    try:
        first = date(int(d[1]), int(d[2]), int(d[3]))
        last = date(int(d[1]), int(d[2]), int(d[4]))
    except ValueError:
        return dict(base, decision="HOLD_INVALID_EVENT_DATE")
    if last < first:
        return dict(base, decision="HOLD_REVERSED_EVENT_DATE")
    if sum(bool(HOURS.fullmatch(x)) for x in local) != 1:
        return dict(base, decision="HOLD_EVENT_HOURS_ROLE")
    if sum(bool(VENUE.fullmatch(x)) for x in local) != 1:
        return dict(base, decision="HOLD_VENUE_ROLE")
    labels = [i for i, x in enumerate(local) if x in ("活動票價│", "活動票價|")]
    if len(labels) != 1:
        return dict(base, decision="HOLD_TICKET_PRICE_LABEL")
    i = labels[0]
    variants = []
    for x in local[i + 1:]:
        if x.startswith(("活動內容", "活動網站", "活動時間", "活動地點")):
            break
        if not TICKET_VARIANT.fullmatch(x):
            return dict(base, decision="HOLD_AMBIGUOUS_TICKET_VARIANT")
        variants.append(x.split("票")[0] + "票")
    if not variants or len(variants) > 4 or len(set(variants)) != len(variants):
        return dict(base, decision="HOLD_TICKET_VARIANTS")
    refund = any("退票" in x and re.search(r"20\d{2}年\d{1,2}月\d{1,2}日", x)
                 for x in clean[ends[0]:])
    return dict(base, decision="REVIEW_DISTINCT_EVENT_AND_TICKET_ROLES_NO_ACCEPTANCE",
                eventDateRole="REVIEW_EVENT_DATE_RANGE_UNLABELED",
                hoursRole="REVIEW_EVENT_HOURS_NOT_SESSION_START",
                venueRole="REVIEW_EVENT_VENUE",
                ticketVariantCount=len(variants),
                refundCutoffOutsideEventBlock=refund)

if __name__ == "__main__":
    raise SystemExit("NO_DIRECT_EXECUTION: no official GET or publication")
