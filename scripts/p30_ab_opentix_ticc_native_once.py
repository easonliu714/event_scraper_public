"""One-shot A OPENTIX / B TICC official HOME -> exact DETAIL identity gate.

A is existing ticket platform #05. B is first-party Taipei venue TICC, not
an added formal platform. No checkout, redirects, retries, raw HTML storage,
Session/date/price inference, LKG, Golden, publication or production writes.
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
from urllib.parse import parse_qsl, urljoin, urlsplit

UA = "EventRadarPublicSourceAudit/1.0"
CAP = 3 * 1024 * 1024
ROBOTS_CAP = 256 * 1024
SOURCES = {
    "A": {
        "source_id": "05", "event_id": "2070446724700692480",
        "list": "https://www.opentix.life/",
        "detail": "https://www.opentix.life/event/2070446724700692480",
        "title": "2026秋天藝術節 巴奈《流浪邊界》",
        "host": "www.opentix.life",
        "robots": "https://www.opentix.life/robots.txt",
    },
    "B": {
        "source_id": "TICC_OFFICIAL_NOT_FORMAL_PLATFORM",
        "event_id": "7806",  # TICC first-party bId, never a ticket Session.
        "list": "https://www.ticc.com.tw/wSite/mp?mp=1",
        "detail": ("https://www.ticc.com.tw/wSite/sp?bId=7806&ctNode=318"
                   "&mp=1&xdUrl=/wSite/ap/cp_Activity.jsp"),
        "title": "Quantum Taiwan 2026",
        "host": "www.ticc.com.tw",
        "robots": "https://www.ticc.com.tw/robots.txt",
    },
}


def norm(value):
    return " ".join(value.split())


def exact_href(line, href):
    source = SOURCES[line]
    if not isinstance(href, str) or not href or href.startswith("//"):
        return None
    try:
        parsed = urlsplit(urljoin(source["list"], href))
        if (parsed.scheme != "https" or parsed.hostname != source["host"]
                or parsed.port is not None or parsed.username or parsed.password
                or parsed.fragment):
            return None
        if line == "A":
            if parsed.path != "/event/" + source["event_id"] or parsed.query:
                return None
        else:
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            expected = {"bId": "7806", "ctNode": "318", "mp": "1",
                        "xdUrl": "/wSite/ap/cp_Activity.jsp"}
            if (parsed.path != "/wSite/sp" or len(pairs) != 4
                    or dict(pairs) != expected):
                return None
    except ValueError:
        return None
    return source["detail"]


class EventLocal(HTMLParser):
    VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img",
                      "input", "link", "meta", "param", "source", "track", "wbr"))
    INERT = frozenset(("script", "style", "template", "noscript"))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.anchors = []
        self.headings = []
        self.anchor = None
        self.heading = None

    def handle_starttag(self, tag, attrs):
        inert = any(x in self.INERT for x in self.stack)
        if not inert and tag == "a" and self.anchor is None:
            hrefs = [v for k, v in attrs if k == "href"]
            if len(hrefs) == 1:
                self.anchor = [hrefs[0], [], len(self.stack)]
        if not inert and tag in ("h1", "h2", "h3") and self.heading is None:
            self.heading = [tag, [], any(x in ("main", "article", "section")
                                          for x in self.stack), len(self.stack)]
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_data(self, value):
        if any(x in self.INERT for x in self.stack):
            return
        if self.anchor is not None:
            self.anchor[1].append(value)
        if self.heading is not None:
            self.heading[1].append(value)

    def handle_endtag(self, tag):
        if self.anchor is not None and tag == "a":
            self.anchors.append((self.anchor[0], norm("".join(self.anchor[1]))))
            self.anchor = None
        if self.heading is not None and tag == self.heading[0]:
            self.headings.append((norm("".join(self.heading[1])), self.heading[2]))
            self.heading = None
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]


def inspect_pair(line, listing, detail):
    source = SOURCES[line]
    lp, dp = EventLocal(), EventLocal()
    lp.feed(listing)
    dp.feed(detail)
    matches = [(url, label) for href, label in lp.anchors
               if (url := exact_href(line, href)) == source["detail"]
               and source["title"] in label
               and len(label) <= len(source["title"]) + 50]
    if len(matches) != 1:
        return {"decision": "HOLD", "first_failure": "AB_NATIVE_LIST_EXACT_LOCAL_EDGE_HOLD",
                "same_id_review": 0, "role_review": 0}
    titles = [title for title, local in dp.headings
              if local and title == source["title"]]
    if len(titles) != 1:
        return {"decision": "HOLD", "first_failure": "AB_NATIVE_DETAIL_LOCAL_HEADING_HOLD",
                "same_id_review": 0, "role_review": 0}
    return {"decision": "NATIVE_SAME_ID_REVIEW_ONLY",
            "first_failure": "INDEPENDENT_FIELD_AUTHORITY_PENDING",
            "same_id_review": 1, "role_review": 1}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_public(line, url, mime, cap):
    source = SOURCES[line]
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname != source["host"]
            or p.port is not None or p.username or p.password or p.fragment):
        raise ValueError("AB_NATIVE_ORIGIN_HOLD")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": mime,
                                               "Accept-Encoding": "identity"})
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=12) as resp:
        body = resp.read(cap + 1)
        if (resp.status != 200 or resp.geturl() != url or
                resp.headers.get_content_type() != mime or
                not 0 < len(body) <= cap):
            raise ValueError("AB_NATIVE_STATUS_MIME_CAP_OR_REDIRECT_HOLD")
    return body, {"url": url, "http_status": 200, "content_type": mime,
                  "body_bytes": len(body), "body_sha256": hashlib.sha256(body).hexdigest(),
                  "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                  "transport": "NATIVE_NO_REDIRECT_NO_RETRY"}


def explicit_robots_allow(line, body):
    try:
        value = body.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("AB_NATIVE_ROBOTS_UTF8_HOLD") from exc
    groups = re.findall(r"(?im)^\s*user-agent\s*:\s*([^#\r\n]+)", value)
    if not any(x.strip().lower() in ("*", UA.lower()) for x in groups):
        raise ValueError("AB_NATIVE_ROBOTS_NO_APPLICABLE_GROUP_HOLD")
    policy = urllib.robotparser.RobotFileParser()
    policy.parse(value.splitlines())
    if not all(policy.can_fetch(UA, SOURCES[line][k]) for k in ("list", "detail")):
        raise ValueError("AB_NATIVE_ROBOTS_PATH_DENIED_HOLD")


def run_line_once(line):
    source = SOURCES[line]
    out = {"kind": "P30_AB_OPENTIX_TICC_NATIVE_ONESHOT_V1", "line": line,
           "source_id": source["source_id"], "source_event_id": source["event_id"],
           "list_url": source["list"], "detail_url": source["detail"],
           "decision": "HOLD", "first_failure": "ROBOTS_NOT_CHECKED_HOLD",
           "robots_get_attempted": 0, "native_event_get_attempted": 0,
           "native_list": 0, "native_detail": 0, "native_same_id_review": 0,
           "native_role_review": 0, "native_body_lkg": 0, "receipt_only_lkg": 0,
           "formal_accepted_fields": 0, "golden": 0, "published": 0,
           "raw_html_saved": False, "release_state": "HARD_HOLD_NO_PUBLICATION",
           "receipts": []}
    try:
        out["robots_get_attempted"] = 1
        robots, receipt = read_public(line, source["robots"], "text/plain", ROBOTS_CAP)
        out["receipts"].append(receipt)
        explicit_robots_allow(line, robots)
        out["native_event_get_attempted"] = 1
        listing, receipt = read_public(line, source["list"], "text/html", CAP)
        out["receipts"].append(receipt)
        out["native_list"] = 1
        lp = EventLocal()
        lp.feed(listing.decode("utf-8"))
        if not any(exact_href(line, href) == source["detail"]
                   and source["title"] in label
                   for href, label in lp.anchors):
            raise ValueError("AB_NATIVE_LIST_EXACT_LOCAL_EDGE_HOLD")
        out["native_event_get_attempted"] = 2
        detail, receipt = read_public(line, source["detail"], "text/html", CAP)
        out["receipts"].append(receipt)
        out["native_detail"] = 1
        verdict = inspect_pair(line, listing.decode("utf-8"), detail.decode("utf-8"))
        out["decision"], out["first_failure"] = verdict["decision"], verdict["first_failure"]
        out["native_same_id_review"] = verdict["same_id_review"]
        out["native_role_review"] = verdict["role_review"]
    except (ValueError, UnicodeError, OSError, TimeoutError,
            urllib.error.URLError, urllib.error.HTTPError) as exc:
        out["first_failure"] = type(exc).__name__ + ":" + str(exc)[:180]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-shot A OPENTIX/B TICC source evidence, NO PUBLISH")
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)
    results = {line: run_line_once(line) for line in ("A", "B")}
    with open(args.evidence, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps(results, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
