#!/usr/bin/env python3
"""P30-VENUE-02B: exact same-path TMC list/detail title parity, REVIEW only.

At most one official list and one official detail HTTPS GET. No redirect,
retry, login, booking, external ticket URL, or raw title/page persistence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import p30_venue02a_tmc_source as prior

KIND = "EVENTRADAR_P30_VENUE02B_TMC_EXACT_TITLE_REVIEW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_TITLE = 180
MAX_HEADINGS = 40
GENERIC = {"more", "read more", "details", "詳細", "更多", "了解更多", "活動詳情"}

def normalize(value):
    if not isinstance(value, str):
        return ""
    return " ".join(unicodedata.normalize("NFC", value).split())

def candidate_title(body, status, final_url, redirected):
    listing = prior.assess_list(body, status, final_url, redirected)
    target = listing.pop("detailUrl", None)
    if not listing["decision"].startswith("REVIEW_") or not target:
        return listing, None, None
    parser = prior.LinksAndHeadings()
    try:
        parser.feed(body.decode("utf-8-sig"))
    except (UnicodeError, ValueError):
        return dict(listing, decision="HOLD_LIST_PARSE"), None, None
    labels = set()
    for href, label in parser.links:
        resolved = prior.urllib.parse.urljoin(prior.LIST_URL, href)
        if resolved == target and prior.safe_detail(resolved):
            title = normalize(label)
            if title:
                labels.add(title)
    if len(labels) != 1:
        return dict(listing, decision="HOLD_LIST_TITLE_AMBIGUOUS"), None, None
    title = next(iter(labels))
    if not (3 <= len(title) <= MAX_TITLE) or title.casefold() in GENERIC:
        return dict(listing, decision="HOLD_LIST_TITLE_GENERIC_OR_CAP"), None, None
    return dict(listing, decision="REVIEW_ONE_EXACT_SOURCE_PATH_TITLE"), target, title

class VisibleHeadings(HTMLParser):
    """Only visible H1/H2; do not borrow H3, script or hidden ancestors."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.current = None
        self.headings = []
        self.invalid = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        hidden = (bool(self.stack and self.stack[-1][1])
                  or tag in ("script", "style", "template")
                  or "hidden" in a or a.get("aria-hidden", "").lower() == "true"
                  or "display:none" in a.get("style", "").replace(" ", "").lower()
                  or "visibility:hidden" in a.get("style", "").replace(" ", "").lower())
        self.stack.append((tag, hidden))
        if tag in ("h1", "h2") and not hidden:
            if self.current is not None:
                self.invalid = True
            else:
                self.current = []

    def handle_data(self, data):
        if self.current is not None and self.stack and not self.stack[-1][1]:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag in ("h1", "h2") and self.current is not None:
            self.headings.append(normalize("".join(self.current)))
            self.current = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return
        self.invalid = True

def assess_exact_detail(body, status, final_url, expected_url, redirected, list_title):
    base = prior.assess_detail(body, status, final_url, expected_url, redirected)
    result = {"http": base["http"], "sameOfficialPath": base["sameOfficialPath"],
              "headingCount": 0, "exactTitleMatches": 0, "acceptedFields": 0,
              "decision": "HOLD_DETAIL_INPUT"}
    if not base["decision"].startswith("REVIEW_"):
        return dict(result, decision=base["decision"])
    if not isinstance(list_title, str) or not (3 <= len(list_title) <= MAX_TITLE):
        return dict(result, decision="HOLD_LIST_TITLE_INVALID")
    parser = VisibleHeadings()
    try:
        parser.feed(body.decode("utf-8-sig"))
    except (UnicodeError, ValueError):
        return dict(result, decision="HOLD_DETAIL_PARSE")
    count = len(parser.headings)
    if parser.invalid or parser.current is not None or count > MAX_HEADINGS:
        return dict(result, decision="HOLD_DETAIL_HEADING_STRUCTURE_OR_CAP",
                    headingCount=min(count, MAX_HEADINGS + 1))
    matches = sum(title == list_title for title in parser.headings)
    decision = ("REVIEW_EXACT_LIST_DETAIL_TITLE_NOT_FORMAL_IDENTITY" if matches == 1
                else "HOLD_MULTIPLE_EXACT_HEADINGS" if matches > 1
                else "HOLD_LIST_DETAIL_TITLE_MISMATCH")
    return dict(result, decision=decision, headingCount=count,
                exactTitleMatches=matches)

def probe():
    body, status, url, redir = prior.get_once(prior.LIST_URL)
    listing, target, title = candidate_title(body, status, url, redir)
    detail = {"http": None, "sameOfficialPath": False, "headingCount": 0,
              "exactTitleMatches": 0, "acceptedFields": 0,
              "decision": "HOLD_LIST_NOT_READY"}
    if target and title:
        dbody, dstatus, durl, dredir = prior.get_once(target)
        detail = assess_exact_detail(dbody, dstatus, durl, target, dredir, title)
    return {"kind": KIND, "releaseState": RELEASE,
            "observedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "TAIPEI_MUSIC_CENTER_OFFICIAL",
            "list": listing, "detail": detail,
            "decision": ("REVIEW_EXACT_SAME_SOURCE_TITLE_NOT_FORMAL_IDENTITY"
                         if detail["decision"].startswith("REVIEW_")
                         else "HOLD_TITLE_IDENTITY"),
            "httpRequestsMax": 2, "acceptedFields": 0, "goldenAccepted": 0,
            "published": False, "ticketEventId": None,
            "rawHtmlPersisted": False, "rawTitlesPersisted": False,
            "rawUrlsPersisted": False, "rawEventIdsPersisted": False,
            "rawFieldValuesPersisted": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if not args.live:
        p.error("explicit --live required")
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-venue02b-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    report = probe()
    out.mkdir(exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "title_review.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"title_review.json": hashlib.sha256(raw).hexdigest()}
    }, sort_keys=True, indent=2) + "\n")
    print("VENUE02B_DECISION=" + report["decision"])
    print("VENUE02B_EXACT_MATCHES=" + str(report["detail"]["exactTitleMatches"]))
    print("HOLD_NO_FORMAL_FIELD_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
