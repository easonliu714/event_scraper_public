"""One-shot, robots-gated A KKTIX #01 and B Fuzhong15 venue source adapter.

Only first-party public LIST -> exact same-source DETAIL. Caller HTML and
browser/indexed evidence are never native provenance. No checkout, redirects,
retries, Session/availability inference, raw-body persistence or publication.
"""
from __future__ import annotations
import json
import re
import urllib.error
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urljoin, urlsplit
from scripts.p30_dual_native_rotation import NoRedirect, read_public, norm, UA

SOURCES = {
    "A": {
        "source_id": "01", "event_id": "myds2026",
        "list": "https://gutspromotion.kktix.cc/",
        "detail": "https://gutspromotion.kktix.cc/events/myds2026",
        "title": "名譽傳說 1st ONEMAN TOUR 2026",
        "origin": "https://gutspromotion.kktix.cc",
    },
    "B": {
        "source_id": "FUZHONG15_NEWTIPEI_OFFICIAL",
        "event_id": "0Q289834314351531469",
        "list": "https://www.fuzhong15.ntpc.gov.tw/xcmovie?XsmSId=0M361641875264878260",
        "detail": ("https://www.fuzhong15.ntpc.gov.tw/xcmovie/cont?"
                   "sid=0Q289834314351531469&xsmsid=0M361641875264878260"),
        "title": "時間暫停的季節",
        "origin": "https://www.fuzhong15.ntpc.gov.tw",
    },
}
VOID = {"br", "img", "meta", "link", "input", "hr", "source", "wbr"}
IGNORE = {"script", "style", "noscript", "template"}


def exact_detail(line, href):
    """Only the known official event URL, never checkout or an extra query."""
    if line not in SOURCES:
        raise ValueError("AB_SOURCE_LINE_HOLD")
    if not isinstance(href, str) or not href or href.startswith("//"):
        return None
    try:
        actual = urlsplit(urljoin(SOURCES[line]["list"], href))
        expected = urlsplit(SOURCES[line]["detail"])
        if (actual.scheme != "https" or actual.hostname != expected.hostname
                or actual.port is not None or actual.username or actual.password
                or actual.path != expected.path or actual.fragment
                or sorted(parse_qsl(actual.query, keep_blank_values=True))
                != sorted(parse_qsl(expected.query, keep_blank_values=True))):
            return None
        return SOURCES[line]["detail"]
    except ValueError:
        return None


class LocalEventHTML(HTMLParser):
    """Unique title anchors/headings; ARTICLE/SECTION owns any field evidence."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.anchors, self.headings = [], [], []
        self.anchor, self.heading = None, None
        self.scopes, self.active = [], []
        self.rows, self.active_rows = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in VOID:
            self.stack.append(tag)
        if tag in ("article", "section"):
            if len(self.scopes) >= 128:
                raise ValueError("AB_EVENT_LOCAL_SCOPE_CAP_HOLD")
            self.scopes.append(dict(tag=tag, depth=len(self.stack),
                                    headings=[], texts=[]))
            self.active.append(len(self.scopes) - 1)
        if tag == "tr":
            if len(self.rows) >= 512:
                raise ValueError("AB_LIST_ROW_CAP_HOLD")
            self.rows.append(dict(depth=len(self.stack), texts=[], edges=[]))
            self.active_rows.append(len(self.rows) - 1)
        if tag == "a":
            self.anchor = [attrs.get("href", ""), []]
        if tag in ("h1", "h2", "h3"):
            self.heading = [tag, []]

    def handle_data(self, value):
        if any(tag in IGNORE for tag in self.stack):
            return
        if self.anchor is not None:
            self.anchor[1].append(value)
        if self.heading is not None:
            self.heading[1].append(value)
        for index in self.active:
            self.scopes[index]["texts"].append(value)
        for index in self.active_rows:
            self.rows[index]["texts"].append(value)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            edge = (self.anchor[0], norm("".join(self.anchor[1])))
            self.anchors.append(edge)
            for index in self.active_rows:
                self.rows[index]["edges"].append(edge)
            self.anchor = None
        if self.heading is not None and tag == self.heading[0]:
            title = norm("".join(self.heading[1]))
            self.headings.append(title)
            for index in self.active:
                self.scopes[index]["headings"].append(title)
            self.heading = None
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break
        self.active = [i for i in self.active
                       if self.scopes[i]["depth"] <= len(self.stack)]
        self.active_rows = [i for i in self.active_rows
                            if self.rows[i]["depth"] <= len(self.stack)]


def exact_list_edges(line, listing):
    p = LocalEventHTML()
    p.feed(listing)
    title = norm(SOURCES[line]["title"])
    return [(exact_detail(line, href), label) for href, label in p.anchors
            if exact_detail(line, href) and label == title]

def b_list_row_roles(listing):
    """Review-only exact same-TR SID/month-day/time, never infer a year."""
    p = LocalEventHTML()
    p.feed(listing)
    matched = []
    for row in p.rows:
        edges = [(exact_detail("B", href), label) for href, label in row["edges"]]
        if len(edges) != 1 or edges[0] != (SOURCES["B"]["detail"], norm(SOURCES["B"]["title"])):
            continue
        local = norm(" ".join(row["texts"]))
        dates = re.findall(r"(?<![0-9])11/06(?![0-9])", local)
        times = re.findall(r"(?<![0-9])19:00(?![0-9])", local)
        if len(dates) == len(times) == 1 and local.count(norm(SOURCES["B"]["title"])) == 1:
            matched.append(row)
    return ["LIST_11_06_19_00_REVIEW_NO_YEAR"] if len(matched) == 1 else []


def inspect_pair(line, listing, detail):
    """Offline/caller HTML never establishes a native GET or a formal FIELD."""
    if line not in SOURCES:
        raise ValueError("AB_SOURCE_LINE_HOLD")
    result = dict(decision="HOLD", first_failure="AB_LIST_EXACT_EDGE_HOLD",
                  same_id_review=0, field_roles=[], formal_accepted_fields=0)
    if len(exact_list_edges(line, listing)) != 1:
        return result
    p = LocalEventHTML()
    p.feed(detail)
    title = norm(SOURCES[line]["title"])
    if p.headings.count(title) != 1:
        result["first_failure"] = "AB_DETAIL_UNIQUE_EXACT_HEADING_HOLD"
        return result
    result.update(decision="REVIEW_IDENTITY_ONLY",
                  first_failure="AB_EVENT_LOCAL_FIELD_SCOPE_HOLD",
                  same_id_review=1)
    if line == "B":
        result["list_row_roles"] = b_list_row_roles(listing)
    owned = [s for s in p.scopes if title in s["headings"]]
    articles = [s for s in owned if s["tag"] == "article"]
    owned = articles or [s for s in owned if s["tag"] == "section"]
    if len(owned) != 1 or len(set(owned[0]["headings"])) != 1:
        if line == "B" and result.get("list_row_roles"):
            result.update(decision="REVIEW_LIST_ROW_ONLY",
                          first_failure="AB_DETAIL_EVENT_LOCAL_FIELD_SCOPE_HOLD")
        return result
    local = norm(" ".join(owned[0]["texts"]))
    if line == "A":
        if len(re.findall(r"日期\s*[|｜:]\s*2026\.11\.28.{0,75}?START\s*18:00", local)) == 1:
            result["field_roles"].append("SHOW_START_2026_11_28_1800_REVIEW")
        if len(re.findall(r"地點\s*[|｜:]\s*The Wall Live House", local, re.I)) == 1:
            result["field_roles"].append("VENUE_THE_WALL_REVIEW")
        # VIP, presale, onsite, concession and pickup fee are distinct roles;
        # no advertised tier becomes eligible general admission or inventory.
    else:
        dates = re.findall(r"2026/(?:11|12)/\d{2}\s+\d{2}:\d{2}", local)
        if (local.count("放映日期") == 1 and len(dates) == 2
                and set(dates) == {"2026/11/06 19:00", "2026/12/02 19:00"}):
            result["field_roles"].append("TWO_SCREENING_STARTS_REVIEW")
        # The page's updated-at date is not a screening or ticket Session.
    if result["field_roles"]:
        result.update(decision="REVIEW_NON_SESSION_ONLY",
                      first_failure="INDEPENDENT_FIELD_ADJUDICATION_PENDING")
    return result


def run_native_once(line):
    """One robots GET, one LIST GET, then one source-derived DETAIL GET at most."""
    if line not in SOURCES:
        raise ValueError("AB_SOURCE_LINE_HOLD")
    source = SOURCES[line]
    out = dict(kind="P30_AB_KKTIX_FUZHONG_NATIVE_ONESHOT_V1",
               line=line, source_id=source["source_id"],
               source_event_id=source["event_id"],
               native_get_attempted=0, native_http200=0,
               native_list=0, native_detail=0, native_same_id_review=0,
               field_roles=[], field_receipts=[], native_lkg=0,
               formal_accepted_fields=0, golden=0, published=0,
               raw_html_saved=False, release_state="HARD_HOLD_NO_PUBLICATION",
               source_receipts=[], decision="HOLD", first_failure="NOT_STARTED")
    opener = urllib.request.build_opener(NoRedirect())
    try:
        out["native_get_attempted"] += 1
        robots, rr = read_public(opener, source["origin"] + "/robots.txt", "text/plain")
        out["robots_receipt"] = rr
        if (not re.search(r"(?im)^\s*user-agent\s*:\s*[^\s#]+", robots)
                or re.search(r"(?i)<(?:!doctype\s+html|html|head|body)(?:\s|>)",
                             robots[:2048])):
            raise ValueError("AB_ROBOTS_POLICY_AUTHORITY_HOLD")
        policy = urllib.robotparser.RobotFileParser()
        policy.parse(robots.splitlines())
        if not policy.can_fetch(UA, source["list"]) or not policy.can_fetch(UA, source["detail"]):
            raise ValueError("AB_ROBOTS_DISALLOW_HOLD")
        out["native_get_attempted"] += 1
        listing, lr = read_public(opener, source["list"], "text/html")
        if rr["body_sha256"] == lr["body_sha256"]:
            raise ValueError("AB_ROBOTS_LIST_IDENTICAL_BODY_HOLD")
        out["native_http200"] += 1
        out["native_list"] = 1
        out["source_receipts"].append(lr)
        if len(exact_list_edges(line, listing)) != 1:
            raise ValueError("AB_NATIVE_LIST_EXACT_EDGE_HOLD")
        out["native_get_attempted"] += 1
        detail, dr = read_public(opener, source["detail"], "text/html")
        out["native_http200"] += 1
        out["native_detail"] = 1
        out["source_receipts"].append(dr)
        verdict = inspect_pair(line, listing, detail)
        out["decision"] = verdict["decision"]
        out["first_failure"] = verdict["first_failure"]
        out["native_same_id_review"] = verdict["same_id_review"]
        out["field_roles"] = verdict["field_roles"]
        if verdict["same_id_review"]:
            roles = ["SOURCE_EXACT_TITLE_REVIEW"] + verdict["field_roles"]
            out["field_receipts"] = [
                dict(source_id=source["source_id"], event_id=source["event_id"],
                     source_url=source["detail"], body_sha256=dr["body_sha256"],
                     observed_at_utc=dr["observed_at_utc"],
                     role=role, decision="REVIEW", formal_accepted=False)
                for role in roles]
    except (ValueError, UnicodeError, OSError, TimeoutError, urllib.error.URLError) as exc:
        out["first_failure"] = type(exc).__name__ + ":" + str(exc)[:180]
    return out


if __name__ == "__main__":
    for stream in ("A", "B"):
        print(json.dumps(run_native_once(stream), ensure_ascii=False, sort_keys=True))
