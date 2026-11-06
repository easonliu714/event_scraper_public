"""ACCUPASS canonical #02 public LIST -> same-ID DETAIL native diagnostic.

No checkout, retries, redirects, persistence, formal field acceptance or publishing.
A one-shot workflow marker is required; all HTML stays in process memory.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, parse_qsl

LIST_URL = "https://www.accupass.com/search"
EVENT_ID = "2606282259461938560271"
EXPECTED_TITLE = "〖城市故事行旅〗台北四國遍路 | 尋找消失的八十八石佛 × 百年朝聖之路"
DETAIL_PATH = "/event/" + EVENT_ID
USER_AGENT = "EventRadarPublicSourceAudit/1.0"
MAX_BODY = 2500000


def normalize(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


class LocalEvidence(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.anchor = None
        self.heading = None
        self.anchors = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.stack.append(tag)
        if tag == "a":
            self.anchor = [attrs.get("href", ""), []]
        if tag in ("h1", "h2") and any(
                ancestor in ("main", "article") for ancestor in self.stack[:-1]):
            self.heading = [tag, []]

    def handle_data(self, data):
        if self.anchor is not None:
            self.anchor[1].append(data)
        if self.heading is not None:
            self.heading[1].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            self.anchors.append((self.anchor[0], normalize("".join(self.anchor[1]))))
            self.anchor = None
        if tag in ("h1", "h2") and self.heading is not None:
            if self.heading[0] == tag:
                self.headings.append(normalize("".join(self.heading[1])))
                self.heading = None
        if tag in self.stack:
            while self.stack:
                last = self.stack.pop()
                if last == tag:
                    break


def exact_public_event_url(href):
    url = urljoin(LIST_URL, href)
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "www.accupass.com"
            or parsed.port is not None or parsed.path != DETAIL_PATH
            or parsed.username or parsed.password or parsed.fragment):
        return None
    if any(not key.startswith("utm_") for key, _ in parse_qsl(
            parsed.query, keep_blank_values=True)):
        return None
    return url


def inspect_same_id(list_html, detail_html):
    listing = LocalEvidence()
    listing.feed(list_html)
    matching = [(exact_public_event_url(href), title)
                for href, title in listing.anchors
                if exact_public_event_url(href) is not None]
    if not matching:
        return {"decision": "HOLD", "first_failure": "ACCUPASS_LIST_EXACT_ID_EDGE_NOT_FOUND",
                "same_id_review": 0, "field_title_review": 0}
    titles = {title for _, title in matching}
    urls = {url for url, _ in matching}
    if titles != {normalize(EXPECTED_TITLE)} or len(urls) != 1:
        return {"decision": "HOLD", "first_failure": "ACCUPASS_LIST_TITLE_OR_QUERY_AMBIGUOUS",
                "same_id_review": 0, "field_title_review": 0}
    detail = LocalEvidence()
    detail.feed(detail_html)
    headings = [title for title in detail.headings
                if title == normalize(EXPECTED_TITLE)]
    if len(headings) != 1:
        return {"decision": "HOLD", "first_failure": "ACCUPASS_DETAIL_MAIN_LOCAL_EXACT_TITLE_HOLD",
                "same_id_review": 0, "field_title_review": 0}
    return {"decision": "REVIEW_NON_SESSION_ONLY", "first_failure": "INDEPENDENT_FIELD_AUTHORITY_PENDING",
            "same_id_review": 1, "field_title_review": 1, "list_derived_detail_url": next(iter(urls)),
            "field_role": "EVENT_TITLE_NOT_SESSION", "formal_accepted_fields": 0}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def public_get(opener, url, cap, expected_media):
    """Role-bound response: robots must be plain text, event pages HTML."""
    if expected_media not in ("text/plain", "text/html"):
        raise ValueError("ACCUPASS_UNSUPPORTED_MEDIA_ROLE_HOLD")
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": expected_media,
        "Accept-Encoding": "identity"})
    with opener.open(request, timeout=12) as response:
        status = response.status
        final = response.geturl()
        ctype = response.headers.get("Content-Type", "")
        raw = response.read(cap + 1)
    if status != 200 or final != url:
        raise ValueError("ACCUPASS_HTTP_STATUS_OR_REDIRECT_HOLD")
    if not 0 < len(raw) <= cap:
        raise ValueError("ACCUPASS_EMPTY_OR_BODY_CAP_HOLD")
    media = ctype.split(";", 1)[0].strip().lower()
    accepted = ("text/plain",) if expected_media == "text/plain" else (
        "text/html", "application/xhtml+xml")
    if media not in accepted:
        raise ValueError("ACCUPASS_ROBOTS_MIME_HOLD" if expected_media == "text/plain"
                         else "ACCUPASS_HTML_MIME_HOLD")
    receipt = {"url": url, "http_status": status, "content_type": media,
               "body_bytes": len(raw), "body_sha256": hashlib.sha256(raw).hexdigest(),
               "observed_at_utc": datetime.now(timezone.utc).isoformat(),
               "transport": "NATIVE_NO_REDIRECT_NO_RETRY"}
    return raw.decode("utf-8", errors="strict"), receipt


def checked_robots_policy(robots_text, receipt):
    """Never infer an allow from a missing applicable robots group or HTML fallback."""
    if receipt.get("content_type") != "text/plain":
        raise ValueError("ACCUPASS_ROBOTS_MIME_HOLD")
    if re.search(r"(?i)<(?:!doctype\s+html|html|head|body)(?:\s|>)",
                 robots_text[:2048]):
        raise ValueError("ACCUPASS_ROBOTS_HTML_FALLBACK_HOLD")
    groups, agents, has_rule = [], [], False
    for raw_line in robots_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip().lower() for part in line.split(":", 1))
        if key == "user-agent":
            if has_rule:
                groups.append((tuple(agents), has_rule))
                agents, has_rule = [], False
            if value:
                agents.append(value)
        elif key in ("allow", "disallow") and agents:
            has_rule = True
    if agents:
        groups.append((tuple(agents), has_rule))
    agent_token = USER_AGENT.split("/", 1)[0].lower()
    if not any(has_rule and any(a in ("*", agent_token, USER_AGENT.lower())
                                for a in agents) for agents, has_rule in groups):
        raise ValueError("ACCUPASS_ROBOTS_APPLICABLE_RULES_HOLD")
    policy = urllib.robotparser.RobotFileParser()
    policy.parse(robots_text.splitlines())
    return policy

def run_native_once():
    result = {"kind": "P30_A_ACCUPASS_DISTINCT_NATIVE_LIST_DETAIL_V1",
              "platform_id": "02", "source_event_id": EVENT_ID,
              "native_get_attempted": 0, "native_http200": 0,
              "native_list": 0, "native_detail": 0,
              "native_same_id_review": 0, "native_same_id_lkg": 0,
              "formal_accepted_fields": 0, "golden": 0, "published": 0,
              "release_state": "HARD_HOLD_NO_PUBLICATION",
              "raw_html_saved": False, "source_receipts": [],
              "decision": "HOLD", "first_failure": "NOT_STARTED"}
    opener = urllib.request.build_opener(NoRedirect())
    try:
        robots_url = "https://www.accupass.com/robots.txt"
        result["native_get_attempted"] += 1
        robots_text, robots_receipt = public_get(opener, robots_url, 131072, "text/plain")
        result["robots_receipt"] = robots_receipt
        policy = checked_robots_policy(robots_text, robots_receipt)
        if not policy.can_fetch(USER_AGENT, LIST_URL):
            raise ValueError("ACCUPASS_ROBOTS_LIST_DISALLOW")
        if not policy.can_fetch(USER_AGENT, "https://www.accupass.com" + DETAIL_PATH):
            raise ValueError("ACCUPASS_ROBOTS_DETAIL_DISALLOW")
        result["policy_decision"] = "ALLOW_ROBOTS_200"
        result["native_get_attempted"] += 1
        list_html, list_receipt = public_get(opener, LIST_URL, MAX_BODY, "text/html")
        if robots_receipt["body_sha256"] == list_receipt["body_sha256"]:
            raise ValueError("ACCUPASS_ROBOTS_LIST_IDENTICAL_BODY_HOLD")
        result["native_http200"] += 1
        result["native_list"] = 1
        result["source_receipts"].append(list_receipt)
        listing = LocalEvidence()
        listing.feed(list_html)
        matched = [(exact_public_event_url(href), title)
                   for href, title in listing.anchors
                   if exact_public_event_url(href) is not None]
        if (not matched or {title for _, title in matched} != {normalize(EXPECTED_TITLE)}
                or len({url for url, _ in matched}) != 1):
            raise ValueError("ACCUPASS_LIST_EXACT_ID_TITLE_EDGE_HOLD")
        detail_url = matched[0][0]
        if not policy.can_fetch(USER_AGENT, detail_url):
            raise ValueError("ACCUPASS_ROBOTS_EXACT_DETAIL_DISALLOW")
        result["native_get_attempted"] += 1
        detail_html, detail_receipt = public_get(opener, detail_url, MAX_BODY, "text/html")
        result["native_http200"] += 1
        result["native_detail"] = 1
        result["source_receipts"].append(detail_receipt)
        identity = inspect_same_id(list_html, detail_html)
        result["decision"] = identity["decision"]
        result["first_failure"] = identity["first_failure"]
        result["native_same_id_review"] = identity["same_id_review"]
        result["field_title_review"] = identity["field_title_review"]
    except (ValueError, UnicodeError, OSError, TimeoutError, urllib.error.URLError) as exc:
        result["first_failure"] = str(exc)[:180]
    return result


if __name__ == "__main__":
    print(json.dumps(run_native_once(), ensure_ascii=False, sort_keys=True))
