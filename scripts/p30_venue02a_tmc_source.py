#!/usr/bin/env python3
"""P30-VENUE-02A: Taipei Music Center public list/detail topology, review only.
Exactly one public list GET and at most one identity-bound detail GET; no redirect,
login, cookies, purchase, query guessing, raw HTML/title/URL persistence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

LIST_URL = "https://www.tmc.taipei/tw/blog/show"
KIND = "EVENTRADAR_P30_VENUE02A_TMC_SOURCE_DISCOVERY_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_BYTES = 800_000
MAX_LINKS = 80
SLUG = re.compile(r"/tw/blog/show/[A-Za-z0-9_-]{3,100}")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def safe_detail(url: str) -> bool:
    if not isinstance(url, str):
        return False
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return (p.scheme == "https" and p.netloc == "www.tmc.taipei"
            and not p.query and not p.fragment and
            bool(SLUG.fullmatch(p.path)))

class LinksAndHeadings(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.headings = []
        self.current_link = None
        self.current_heading = None
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.ignore += 1
        if self.ignore:
            return
        if tag == "a":
            self.current_link = [a.get("href", ""), []]
        if tag in ("h1", "h2", "h3"):
            self.current_heading = []

    def handle_data(self, data):
        if self.ignore:
            return
        if self.current_link is not None:
            self.current_link[1].append(data)
        if self.current_heading is not None:
            self.current_heading.append(data)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignore = max(0, self.ignore - 1)
            return
        if tag == "a" and self.current_link is not None:
            self.links.append((self.current_link[0], " ".join("".join(self.current_link[1]).split())))
            self.current_link = None
        if tag in ("h1", "h2", "h3") and self.current_heading is not None:
            self.headings.append(" ".join("".join(self.current_heading).split()))
            self.current_heading = None

def assess_list(body: bytes | None, status: int | None, final_url: str, redirected: bool) -> dict:
    base = {"decision": "HOLD_LIST_INPUT", "http": status, "listCandidateCount": 0,
            "distinctDetailPaths": 0, "detailUrl": None}
    if status != 200 or redirected or final_url != LIST_URL or not isinstance(body, bytes) or len(body) > MAX_BYTES:
        return base
    try:
        html = body.decode("utf-8-sig")
    except UnicodeError:
        return dict(base, decision="HOLD_LIST_ENCODING")
    parser = LinksAndHeadings()
    parser.feed(html)
    if len(parser.links) > 500:
        return dict(base, decision="HOLD_LINK_SCOPE_CAP")
    paths = []
    for href, title in parser.links:
        target = urllib.parse.urljoin(LIST_URL, href)
        if safe_detail(target) and title:
            paths.append(target)
    distinct = list(dict.fromkeys(paths))
    if len(distinct) > MAX_LINKS:
        return dict(base, decision="HOLD_CANDIDATE_CAP", listCandidateCount=len(paths))
    if not distinct:
        return dict(base, decision="HOLD_NO_OFFICIAL_DETAIL_LINK")
    return dict(base, decision="REVIEW_OFFICIAL_LIST_LINKS_NOT_EVENT_IDENTITY",
                listCandidateCount=len(paths), distinctDetailPaths=len(distinct),
                detailUrl=distinct[0])

def assess_detail(body: bytes | None, status: int | None, final_url: str,
                  expected_url: str, redirected: bool) -> dict:
    base = {"decision": "HOLD_DETAIL_INPUT", "http": status, "headingCount": 0,
            "sameOfficialPath": False}
    if not safe_detail(expected_url) or final_url != expected_url or redirected:
        return dict(base, decision="HOLD_DETAIL_URL_OR_REDIRECT")
    if status != 200 or not isinstance(body, bytes) or len(body) > MAX_BYTES:
        return dict(base, decision="HOLD_DETAIL_HTTP_OR_CAP")
    try:
        html = body.decode("utf-8-sig")
    except UnicodeError:
        return dict(base, decision="HOLD_DETAIL_ENCODING")
    parser = LinksAndHeadings()
    parser.feed(html)
    headings = [x for x in parser.headings if x]
    return dict(base, decision=("REVIEW_SAME_OFFICIAL_DETAIL_PATH_HEADING_PRESENT_NOT_TITLE_PARITY"
                                if headings else "HOLD_NO_DETAIL_HEADING"),
                headingCount=min(len(headings), 100), sameOfficialPath=True)

def get_once(url: str):
    if url != LIST_URL and not safe_detail(url):
        return None, None, url, False
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "EventRadarPublicSourceReview/1.0",
        "Accept": "text/html"}, method="GET")
    try:
        with opener.open(req, timeout=12) as response:
            status = response.status
            final = response.geturl()
            content_type = response.headers.get("Content-Type", "").lower()
            body = response.read(MAX_BYTES + 1)
        return (body if content_type.startswith("text/html") else None), status, final, False
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None, None, url, False

def probe():
    body, status, url, redir = get_once(LIST_URL)
    listing = assess_list(body, status, url, redir)
    detail = {"decision": "HOLD_LIST_NOT_READY", "http": None,
              "headingCount": 0, "sameOfficialPath": False}
    if listing["decision"].startswith("REVIEW_"):
        target = listing.pop("detailUrl")
        body, status, url, redir = get_once(target)
        detail = assess_detail(body, status, url, target, redir)
    else:
        listing.pop("detailUrl", None)
    return {"kind": KIND, "releaseState": RELEASE,
        "observedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "TAIPEI_MUSIC_CENTER_OFFICIAL", "list": listing, "detail": detail,
        "decision": ("REVIEW_OFFICIAL_LIST_AND_DETAIL_TOPOLOGY_NOT_TITLE_PARITY"
                     if listing["decision"].startswith("REVIEW_") and detail["decision"].startswith("REVIEW_")
                     else "HOLD_LIST_OR_DETAIL_TOPOLOGY"),
        "httpRequestsMax": 2, "acceptedFields": 0, "goldenAccepted": 0,
        "published": False, "rawHtmlPersisted": False, "rawTitlesPersisted": False,
        "rawUrlsPersisted": False, "ticketEventId": None}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    if not a.live:
        p.error("explicit --live required")
    out = Path(a.out)
    if out.resolve() != (Path.cwd() / "p30-venue02a-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    report = probe()
    out.mkdir(exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "source_review.json").write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps({
        "kind": KIND, "releaseState": RELEASE,
        "filesSHA256": {"source_review.json": hashlib.sha256(raw).hexdigest()}
    }, sort_keys=True, indent=2) + "\n")
    print("VENUE02A_DECISION=" + report["decision"])
    print("HOLD_NO_FORMAL_FIELD_GOLDEN_PUBLICATION")

if __name__ == "__main__":
    main()
