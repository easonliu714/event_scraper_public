"""B P0 NTCH one-use robots-gated public LIST -> exact local DETAIL, NO PUBLISH.

This is independent venue evidence, not OPENTIX event identity. A JS-only
index, absent local event ID, disallowed path or HTTP error fails closed.
Raw HTML is processed in memory, never persisted. One request per path,
no redirect, retry, login, checkout, scheduler, Golden or formal feed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

HOST = "npac-ntch.org"
LIST_URL = "https://npac-ntch.org/programs"
ROBOTS_URL = "https://npac-ntch.org/robots.txt"
TITLE = "2026秋天藝術節 巴奈《流浪邊界》"
UA = "EventRadarPublicSourceAudit/1.0"
MAX_BODY = 2 * 1024 * 1024
MAX_ROBOTS = 128 * 1024
INERT = frozenset(("script", "style", "template", "noscript"))
VOID = frozenset(("br", "img", "meta", "link", "hr", "input", "source", "wbr"))


def norm(value):
    return " ".join(value.split())


def exact_venue_detail(href):
    if not isinstance(href, str) or not href or href.startswith("//"):
        return None
    try:
        p = urlsplit(urljoin(LIST_URL, href))
        if (p.scheme != "https" or p.hostname != HOST or p.port is not None
                or p.username or p.password or p.query or p.fragment
                or not re.fullmatch(r"/(?:zh/)?programs/[A-Za-z0-9_-]{6,160}", p.path)):
            return None
    except ValueError:
        return None
    return p.geturl()


class EventHTML(HTMLParser):
    """Only event-local links and article/section headings; inert content ignored."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.anchors, self.headings = [], [], []
        self.anchor, self.heading = None, None
        self.malformed = False

    def handle_starttag(self, tag, attrs):
        inert = any(x in INERT for x in self.stack)
        if not inert and tag == "a":
            if self.anchor is not None:
                self.malformed = True
            hrefs = [v for k, v in attrs if k == "href"]
            if len(hrefs) == 1:
                self.anchor = [hrefs[0], [], len(self.stack)]
        if not inert and tag in ("h1", "h2", "h3"):
            if self.heading is not None:
                self.malformed = True
            self.heading = [tag, [], len(self.stack),
                            any(x in ("article", "section") for x in self.stack)]
        if tag not in VOID:
            self.stack.append(tag)

    def handle_data(self, data):
        if any(x in INERT for x in self.stack):
            return
        if self.anchor is not None:
            self.anchor[1].append(data)
        if self.heading is not None:
            self.heading[1].append(data)

    def handle_endtag(self, tag):
        inert = any(x in INERT for x in self.stack)
        if not inert and tag == "a" and self.anchor is not None:
            self.anchors.append((self.anchor[0], norm("".join(self.anchor[1]))))
            self.anchor = None
        if not inert and self.heading is not None and tag == self.heading[0]:
            self.headings.append((norm("".join(self.heading[1])),
                                  self.heading[3]))
            self.heading = None
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]
        else:
            self.malformed = True


def unique_list_detail(html):
    page = EventHTML()
    page.feed(html)
    if page.malformed or page.anchor or page.heading:
        return None
    matches = [u for href, label in page.anchors
               if (u := exact_venue_detail(href)) and label == TITLE]
    return matches[0] if len(matches) == 1 else None


def inspect_pair(list_html, detail_html, detail_url):
    if unique_list_detail(list_html) != detail_url:
        return {"decision": "HOLD", "first_failure": "NTCH_LIST_EVENT_ID_HOLD",
                "same_id_review": 0}
    page = EventHTML()
    page.feed(detail_html)
    headings = [title for title, local in page.headings if local and title == TITLE]
    if page.malformed or page.anchor or page.heading or len(headings) != 1:
        return {"decision": "HOLD", "first_failure": "NTCH_DETAIL_EVENT_LOCAL_HEADING_HOLD",
                "same_id_review": 0}
    return {"decision": "REVIEW_ONLY_NOT_NATIVE_BODY_LKG",
            "first_failure": "INDEPENDENT_VENUE_FIELD_AUTHORITY_HOLD",
            "same_id_review": 1}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_public(url, mime, cap):
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname != HOST or p.port is not None
            or p.username or p.password or p.fragment):
        raise ValueError("NTCH_ORIGIN_HOLD")
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": mime, "Accept-Encoding": "identity"})
    # Check response authority before reading any body. The first native
    # NTCH robots attempt collapsed MIME/status/redirect into one HOLD; this
    # preserves the exact safe failure class without repeating that probe.
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=12) as response:
        status = response.status
        final_url = response.geturl()
        actual_mime = response.headers.get_content_type()
        if status != 200:
            raise ValueError("NTCH_HTTP_STATUS_HOLD:" + str(status))
        if final_url != url:
            raise ValueError("NTCH_REDIRECT_HOLD")
        if actual_mime != mime:
            raise ValueError("NTCH_CONTENT_TYPE_HOLD:expected=" + mime +
                             ":actual=" + actual_mime)
        body = response.read(cap + 1)
        if not 0 < len(body) <= cap:
            raise ValueError("NTCH_BODY_CAP_HOLD")
    receipt = {"url": url, "http_status": 200, "body_bytes": len(body),
               "body_sha256": hashlib.sha256(body).hexdigest(),
               "observed_at_utc": datetime.now(timezone.utc).isoformat(),
               "transport": "NATIVE_NO_REDIRECT_NO_RETRY"}
    return body, receipt


def explicit_robots_allow(body, urls):
    try:
        value = body.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("NTCH_ROBOTS_ENCODING_HOLD") from exc
    groups = re.findall(r"(?im)^\s*user-agent\s*:\s*([^#\r\n]+)", value)
    if not any(g.strip().lower() in ("*", UA.lower()) for g in groups):
        raise ValueError("NTCH_ROBOTS_NO_APPLICABLE_GROUP_HOLD")
    policy = urllib.robotparser.RobotFileParser()
    policy.parse(value.splitlines())
    if not all(policy.can_fetch(UA, url) for url in urls):
        raise ValueError("NTCH_ROBOTS_PATH_DENIED_HOLD")
    return policy


def run_native_once():
    out = {"kind": "P30_B_NTCH_OFFICIAL_NATIVE_ONESHOT_V1",
           "line": "B", "source_id": "NTCH_OFFICIAL_VENUE_NOT_OPENTIX",
           "list_url": LIST_URL, "source_event_id": None, "detail_url": None,
           "decision": "HOLD", "first_failure": "NTCH_ROBOTS_NOT_CHECKED_HOLD",
           "robots_get_attempted": 0, "native_event_get_attempted": 0,
           "native_list": 0, "native_detail": 0, "native_same_id_review": 0,
           "native_body_lkg": 0, "receipt_only_lkg": 0,
           "formal_accepted_fields": 0, "golden": 0, "published": 0,
           "raw_html_saved": False, "release_state": "HARD_HOLD_NO_PUBLICATION",
           "receipts": []}
    try:
        out["robots_get_attempted"] = 1
        robots, receipt = read_public(ROBOTS_URL, "text/plain", MAX_ROBOTS)
        out["receipts"].append(receipt)
        policy = explicit_robots_allow(robots, (LIST_URL,))
        out["native_event_get_attempted"] = 1
        listing, receipt = read_public(LIST_URL, "text/html", MAX_BODY)
        out["receipts"].append(receipt)
        out["native_list"] = 1
        listing_text = listing.decode("utf-8")
        detail_url = unique_list_detail(listing_text)
        if detail_url is None:
            raise ValueError("NTCH_NATIVE_LIST_EVENT_LOCAL_ID_HOLD")
        if not policy.can_fetch(UA, detail_url):
            raise ValueError("NTCH_ROBOTS_DETAIL_DENIED_HOLD")
        out["detail_url"] = detail_url
        out["source_event_id"] = urlsplit(detail_url).path.rsplit("/", 1)[-1]
        out["native_event_get_attempted"] = 2
        detail, receipt = read_public(detail_url, "text/html", MAX_BODY)
        out["receipts"].append(receipt)
        out["native_detail"] = 1
        verdict = inspect_pair(listing_text, detail.decode("utf-8"), detail_url)
        out["decision"] = verdict["decision"]
        out["first_failure"] = verdict["first_failure"]
        out["native_same_id_review"] = verdict["same_id_review"]
    except (ValueError, UnicodeError, OSError, TimeoutError,
            urllib.error.URLError) as exc:
        status = getattr(exc, "code", None)
        out["first_failure"] = type(exc).__name__ + (
            ":HTTP" + str(status) if status is not None else ":" + str(exc)[:140])
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="B NTCH one-shot, NO PUBLISH")
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)
    result = run_native_once()
    with open(args.evidence, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
