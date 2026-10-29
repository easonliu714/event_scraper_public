#!/usr/bin/env python3
"""VENUE-01C: Taipei Arena title vs explicitly labeled activity date refusal.

Offline-only diagnostic contract. Never infers performance dates from an
announcement timestamp, platform claim or a date in unrelated prose.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path

KIND = "EVENTRADAR_P30_VENUE01C_DATE_ROLE_CONFLICT_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "f2654b0ed7284eb67403bd969ba84dd68c751d2a"
MAX_TEXT = 100_000
DATE = re.compile(
    r"(?<!\d)(20\d{2})/(\d{1,2})/(\d{1,2})"
    r"(?:\s*[-–~～至]\s*(?:(\d{1,2})/)?(\d{1,2}))?(?!\d)"
)
ACTIVITY_LABEL = re.compile(
    r"(?:活動日期/時間|活動日期|演出日期)\s*[:：]\s*([^\n]{1,120})"
)
ANNOUNCEMENT_LABELS = ("日期時間", "公告日期", "發佈日期", "發布日期")


def _date_span(text: str):
    found = list(DATE.finditer(text))
    if len(found) != 1:
        return None
    y, m, d, end_month, end_day = found[0].groups()
    y, m, d = int(y), int(m), int(d)
    try:
        start = dt.date(y, m, d)
        end = dt.date(y, int(end_month) if end_month else m, int(end_day)) if end_day else start
    except ValueError:
        return None
    if end < start:
        return None
    return (start.isoformat(), end.isoformat())


def _body_text(value: str) -> str:
    # Preserve explicit label-line boundaries; no global date stitching.
    value = re.sub(r"(?i)<br\s*/?>|</p\s*>|</div\s*>", "\n", value)
    value = re.sub(r"<[^>]{0,300}>", " ", value)
    return html.unescape(value)


def inspect_date_role(title: object, body: object) -> dict:
    base = {"acceptedFields": 0, "goldenAccepted": 0, "published": False,
            "rawDatesPersisted": False, "eventDate": None, "ticketEventId": None}
    if not isinstance(title, str) or not isinstance(body, str) or len(title) > 250 or len(body) > MAX_TEXT:
        return dict(base, decision="HOLD_INPUT_SHAPE_OR_CAP")
    if not title.strip():
        return dict(base, decision="HOLD_EMPTY_TITLE")
    title_date = _date_span(title)
    if title_date is None:
        return dict(base, decision="HOLD_TITLE_DATE_MISSING_OR_AMBIGUOUS")
    body_text = _body_text(body)
    labels = ACTIVITY_LABEL.findall(body_text)
    if len(labels) != 1:
        return dict(base, decision="HOLD_EXPLICIT_ACTIVITY_LABEL_MISSING_OR_AMBIGUOUS")
    body_date = _date_span(labels[0])
    if body_date is None:
        return dict(base, decision="HOLD_LABELED_ACTIVITY_DATE_MISSING_OR_AMBIGUOUS")
    if title_date != body_date:
        return dict(base, decision="HOLD_TITLE_BODY_ACTIVITY_DATE_CONFLICT",
                    titleBodyDateParity=False)
    return dict(base, decision="REVIEW_TITLE_BODY_ACTIVITY_DATE_PARITY_NOT_ACCEPTED",
                titleBodyDateParity=True)


def offline_contract_report() -> dict:
    return {"kind": KIND, "parentHead": PARENT, "releaseState": RELEASE,
            "sourceStatus": "NOT_PROBED_THIS_GATE",
            "scope": "TITLE_DATE_VS_EXPLICIT_ACTIVITY_LABEL_ONLY",
            "dateRoleStatus": "REVIEW_OR_HOLD_ONLY",
            "ticketPlatformClaimIsTicketId": False,
            "venueDataSNIsTicketEventId": False,
            "announcementTimestampIsEventDate": False,
            "httpRequests": 0, "acceptedFields": 0, "goldenAccepted": 0,
            "published": False, "productionModified": False,
            "rawHtmlPersisted": False, "rawUrlsPersisted": False,
            "rawTitlesPersisted": False, "rawDatesPersisted": False,
            "decision": "REVIEW_OFFLINE_DATE_CONFLICT_REFUSAL_ONLY"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--offline-contract", action="store_true")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if not args.offline_contract:
        p.error("explicit --offline-contract required; no live GET")
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-venue01c-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    out.mkdir(exist_ok=True)
    raw = (json.dumps(offline_contract_report(), sort_keys=True, indent=2) + "\n").encode()
    (out / "date_conflict_contract.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"date_conflict_contract.json": hashlib.sha256(raw).hexdigest()},
    }, sort_keys=True, indent=2) + "\n")
    print("PASS_VENUE01C_OFFLINE_DATE_CONFLICT_NO_PUBLICATION")


if __name__ == "__main__":
    main()
