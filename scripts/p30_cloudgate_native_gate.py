"""B Cloud Gate New Taipei official LIST -> exact event DETAIL; no publishing.

The 11/14 -> 12/19 postponement is source-owned indexed discovery, NOT native
until this exact one-shot probe succeeds. Strict robots, MIME, no redirects,
bounded bytes, no retries, login, checkout, raw HTML or Session inference.
"""
from __future__ import annotations
import json
import re
import urllib.error
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from scripts.p30_dual_native_rotation import NoRedirect, read_public, norm, UA

LIST_URL = "https://www.cloudgate.org.tw/cgt/latest-program"
DETAIL_URL = "https://www.cloudgate.org.tw/cgt/theater-event/1680"
TITLE = "來雲門共學 2026系列講座"
SOURCE_EVENT_ID = "1680"

def exact_detail(href):
    if not href or not isinstance(href, str):
        return None
    try:
        u = urljoin(LIST_URL, href)
        p = urlsplit(u)
        if (p.scheme == "https" and p.hostname == "www.cloudgate.org.tw"
                and p.port is None and not p.username and not p.password
                and not p.query and not p.fragment
                and p.path == "/cgt/theater-event/1680"):
            return u
    except ValueError:
        pass
    return None

class LocalEvent(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.anchors, self.headings, self.local_text = [], [], [], []
        self.anchor, self.heading = None, None
        # MAIN-wide text cannot establish the identity of an event.
        self.scopes, self.active_scopes = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in ("img", "br", "meta", "link", "input", "hr", "source"):
            self.stack.append(tag)
        if tag in ("article", "section"):
            if len(self.scopes) >= 128:
                raise ValueError("CLOUDGATE_EVENT_SCOPE_CAP_HOLD")
            self.scopes.append(dict(tag=tag, depth=len(self.stack),
                                    headings=[], texts=[]))
            self.active_scopes.append(len(self.scopes) - 1)
        if tag == "a":
            self.anchor = [attrs.get("href", ""), []]
        if tag in ("h1", "h2", "h3") and any(
                t in ("main", "article") for t in self.stack[:-1]):
            self.heading = [tag, []]

    def handle_data(self, value):
        if self.anchor is not None:
            self.anchor[1].append(value)
        if self.heading is not None:
            self.heading[1].append(value)
        if any(t in ("main", "article") for t in self.stack) and not any(
                t in ("script", "style", "noscript", "template") for t in self.stack):
            self.local_text.append(value)
            for index in self.active_scopes:
                self.scopes[index]["texts"].append(value)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            self.anchors.append((self.anchor[0], norm("".join(self.anchor[1]))))
            self.anchor = None
        if self.heading is not None and tag == self.heading[0]:
            heading = norm("".join(self.heading[1]))
            self.headings.append(heading)
            for index in self.active_scopes:
                self.scopes[index]["headings"].append(heading)
            self.heading = None
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break
        self.active_scopes = [index for index in self.active_scopes
                              if self.scopes[index]["depth"] <= len(self.stack)]

def inspect_pair(list_html, detail_html):
    listing, detail = LocalEvent(), LocalEvent()
    listing.feed(list_html)
    detail.feed(detail_html)
    edges = [(exact_detail(href), label) for href, label in listing.anchors
             if exact_detail(href)]
    if len(edges) != 1 or not edges[0][1].startswith(norm(TITLE)):
        return {"decision":"HOLD","first_failure":"CLOUDGATE_LIST_EXACT_ID_TITLE_HOLD",
                "same_id_review":0,"postponement_review":0}
    if detail.headings.count(norm(TITLE)) != 1:
        return {"decision":"HOLD","first_failure":"CLOUDGATE_DETAIL_MAIN_LOCAL_TITLE_HOLD",
                "same_id_review":0,"postponement_review":0}
    # Require the exact title and postponement in the same event-local scope.
    # An ARTICLE outranks its containing SECTION; sibling text never qualifies.
    owned = [scope for scope in detail.scopes
             if norm(TITLE) in scope["headings"]]
    articles = [scope for scope in owned if scope["tag"] == "article"]
    owned = articles or [scope for scope in owned if scope["tag"] == "section"]
    if len(owned) != 1:
        return {"decision":"HOLD",
                "first_failure":"CLOUDGATE_EVENT_LOCAL_TITLE_SCOPE_HOLD",
                "same_id_review":0,"postponement_review":0}
    local = norm(" ".join(owned[0]["texts"]))
    if not (re.search(r"原\s*11/14.*?延期至\s*12/19", local)
            and "12月19日" in local):
        return {"decision":"HOLD","first_failure":"CLOUDGATE_POSTPONEMENT_LOCAL_AUTHORITY_HOLD",
                "same_id_review":1,"postponement_review":0}
    return {"decision":"REVIEW_NON_SESSION_ONLY",
            "first_failure":"INDEPENDENT_FIELD_ADJUDICATION_PENDING",
            "same_id_review":1,"postponement_review":1,
            "date_role":"POSTPONED_SHOW_DATE_REVIEW_NOT_TICKET_SESSION",
            "formal_accepted_fields":0}

def run_native_once():
    out = {"kind":"P30_B_CLOUDGATE_NEWTAIPEI_NATIVE_ONESHOT_V1",
           "source_id":"CLOUDGATE_THEATER_OFFICIAL_NOT_FORMAL_19_PLATFORM",
           "source_event_id":SOURCE_EVENT_ID,"native_get_attempted":0,
           "native_http200":0,"native_list":0,"native_detail":0,
           "native_same_id_review":0,"native_same_id_lkg":0,
           "postponement_review":0,"formal_accepted_fields":0,
           "golden":0,"published":0,"raw_html_saved":False,
           "release_state":"HARD_HOLD_NO_PUBLICATION",
           "source_receipts":[],"decision":"HOLD","first_failure":"NOT_STARTED"}
    opener = urllib.request.build_opener(NoRedirect())
    try:
        out["native_get_attempted"] += 1
        robots, rr = read_public(opener,
            "https://www.cloudgate.org.tw/robots.txt","text/plain")
        out["robots_receipt"] = rr
        if not re.search(r"(?im)^\s*user-agent\s*:\s*[^\s#]+",robots):
            raise ValueError("CLOUDGATE_ROBOTS_MISSING_DIRECTIVE_HOLD")
        policy = urllib.robotparser.RobotFileParser()
        policy.parse(robots.splitlines())
        if not policy.can_fetch(UA,LIST_URL) or not policy.can_fetch(UA,DETAIL_URL):
            raise ValueError("CLOUDGATE_ROBOTS_DISALLOW_HOLD")
        out["policy_decision"]="ALLOW_ROBOTS_200"
        out["native_get_attempted"] += 1
        listing, lr = read_public(opener,LIST_URL,"text/html")
        if rr["body_sha256"] == lr["body_sha256"]:
            raise ValueError("CLOUDGATE_ROBOTS_LIST_IDENTICAL_BODY_HOLD")
        out["native_http200"] += 1
        out["native_list"] = 1
        out["source_receipts"].append(lr)
        lp = LocalEvent()
        lp.feed(listing)
        edges = [(exact_detail(h), t) for h,t in lp.anchors if exact_detail(h)]
        if len(edges)!=1 or not edges[0][1].startswith(norm(TITLE)):
            raise ValueError("CLOUDGATE_NATIVE_LIST_EXACT_EDGE_HOLD")
        out["native_get_attempted"] += 1
        detail, dr = read_public(opener,edges[0][0],"text/html")
        out["native_http200"] += 1
        out["native_detail"] = 1
        out["source_receipts"].append(dr)
        decision = inspect_pair(listing,detail)
        out["decision"],out["first_failure"]=decision["decision"],decision["first_failure"]
        out["native_same_id_review"]=decision["same_id_review"]
        out["postponement_review"]=decision["postponement_review"]
    except (ValueError, UnicodeError, OSError, TimeoutError, urllib.error.URLError) as exc:
        out["first_failure"]=type(exc).__name__+":"+str(exc)[:180]
    return out

if __name__ == "__main__":
    print(json.dumps(run_native_once(),ensure_ascii=False,sort_keys=True))
