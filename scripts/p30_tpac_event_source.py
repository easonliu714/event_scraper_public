"""TPAC public /event LIST -> exact /event/2072 DETAIL REVIEW adapter.

The official index and detail have conflicting date ranges in indexed public
renderings. Never promote dates, Session, price or room from this conflict.
Caller HTML is NOT native HTTP evidence. This module performs NO GET.
"""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import re
import unicodedata

LIST_URL = "https://tpac.org.taipei/event?page=1"
DETAIL_URL = "https://tpac.org.taipei/event/2072"
TITLE = "2026北藝夜遊：Beats到天臺"
SOURCE_ID = "TPAC_OFFICIAL_EVENT_NOT_FORMAL_PLATFORM"
EVENT_ID = "2072"
INERT = {"script", "style", "template", "noscript"}
SCOPE = {"article", "section", "li"}
DATE_RANGE = re.compile(r"(?<!\d)(20\d{2}-\d{2}-\d{2})\s*[-–~]\s*(20\d{2}-\d{2}-\d{2})(?!\d)")


def norm(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


def exact_detail(href):
    if not isinstance(href, str) or not href or href.startswith("//"):
        return None
    try:
        p = urlsplit(urljoin(LIST_URL, href))
        if (p.scheme != "https" or p.hostname != "tpac.org.taipei"
                or p.port is not None or p.username or p.password
                or p.path != "/event/2072" or p.query or p.fragment):
            return None
    except ValueError:
        return None
    return DETAIL_URL


class EventScopes(HTMLParser):
    """Keep title, link and date inside their nearest semantic event owner."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.scopes, self.active = [], [], []
        self.anchor, self.heading, self.malformed = None, None, False

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)
        if any(t in INERT for t in self.stack):
            return
        if tag in SCOPE:
            scope = {"tag": tag, "depth": len(self.stack),
                     "texts": [], "links": [], "headings": []}
            self.scopes.append(scope)
            self.active.append(scope)
        if tag == "a":
            if self.anchor is not None:
                self.malformed = True
            self.anchor = [dict(attrs).get("href", ""), []]
        if tag in ("h1", "h2", "h3"):
            if self.heading is not None:
                self.malformed = True
            self.heading = [tag, []]

    def handle_data(self, data):
        if any(t in INERT for t in self.stack):
            return
        for scope in self.active:
            scope["texts"].append(data)
        if self.anchor is not None:
            self.anchor[1].append(data)
        if self.heading is not None:
            self.heading[1].append(data)

    def handle_endtag(self, tag):
        if any(t in INERT for t in self.stack):
            if tag in self.stack:
                while self.stack:
                    if self.stack.pop() == tag:
                        break
            return
        if tag == "a" and self.anchor is not None:
            if self.active:
                self.active[-1]["links"].append(
                    (self.anchor[0], norm("".join(self.anchor[1]))))
            self.anchor = None
        if tag in ("h1", "h2", "h3") and self.heading is not None:
            if tag == self.heading[0] and self.active:
                self.active[-1]["headings"].append(
                    norm("".join(self.heading[1])))
            self.heading = None
        if tag in SCOPE:
            if not self.active or self.active[-1]["tag"] != tag:
                self.malformed = True
            else:
                self.active.pop()
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break


def _unique_owner(page, kind):
    if page.malformed or page.active or page.anchor or page.heading:
        return None
    if kind == "list":
        matching = [s for s in page.scopes
                    if any(exact_detail(h) == DETAIL_URL and t == norm(TITLE)
                           for h, t in s["links"])]
    else:
        matching = [s for s in page.scopes
                    if s["headings"].count(norm(TITLE)) == 1]
    if not matching:
        return None
    depth = max(s["depth"] for s in matching)
    owners = [s for s in matching if s["depth"] == depth]
    if len(owners) != 1:
        return None
    if kind == "list":
        links = owners[0]["links"]
        if sum(exact_detail(h) == DETAIL_URL and t == norm(TITLE)
               for h, t in links) != 1:
            return None
        if any(exact_detail(h) == DETAIL_URL and t != norm(TITLE)
               for h, t in links):
            return None
    return owners[0]


def _range(scope):
    found = DATE_RANGE.findall(norm(" ".join(scope["texts"])))
    return tuple(found[0]) if len(found) == 1 else None


def inspect_caller_html(list_html, detail_html):
    """Same-ID REVIEW with local date disagreement fail-closed, never native."""
    out = {"kind": "P30_B_TPAC_EVENT_2072_REVIEW_V1",
           "source": SOURCE_ID, "source_event_id": EVENT_ID,
           "decision": "HOLD", "first_failure": "TPAC_EVENT_LIST_EDGE_HOLD",
           "same_id_review": 0, "date_conflict": False, "field_roles": [],
           "native_get": 0, "native_body_provenance": False,
           "formal_accepted_fields": 0, "golden": 0, "published": 0,
           "release_state": "HARD_HOLD_NO_PUBLICATION"}
    listing, detail = EventScopes(), EventScopes()
    listing.feed(list_html)
    detail.feed(detail_html)
    lo = _unique_owner(listing, "list")
    if lo is None:
        return out
    do = _unique_owner(detail, "detail")
    if do is None:
        out["first_failure"] = "TPAC_EVENT_DETAIL_LOCAL_TITLE_HOLD"
        return out
    out["same_id_review"] = 1
    out["field_roles"] = ["EVENT_TITLE_REVIEW"]
    left, right = _range(lo), _range(do)
    if left is None or right is None:
        out["first_failure"] = "TPAC_EVENT_DATE_RANGE_LOCAL_AUTHORITY_HOLD"
    elif left != right:
        out["date_conflict"] = True
        out["first_failure"] = "TPAC_EVENT_OFFICIAL_LIST_DETAIL_DATE_CONFLICT_HOLD"
    else:
        out["field_roles"].append("VENUE_EVENT_DATE_RANGE_REVIEW_NOT_SESSION")
        out["first_failure"] = "INDEPENDENT_NATIVE_FIELD_AUTHORITY_PENDING"
    out["decision"] = "REVIEW_IDENTITY_ONLY_NOT_NATIVE"
    return out
