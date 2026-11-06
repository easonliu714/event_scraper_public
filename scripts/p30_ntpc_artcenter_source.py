"""New Taipei Art Center official exhibition LIST/DETAIL local review adapter.

Consumes caller-provided HTML only. No network, publication, Golden, or date
inference from the bulletin publication date or title-embedded month/day.
"""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, parse_qs
import re
import unicodedata

LIST_URL = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc?xsmsid=0G269629197439395113"
SID = "0Q293634176769376687"
XSMSID = "0G269629197439395113"
TITLE = "〖展覽預告〗12/09-12/27綺景 | 療癒-2026謝慧綺油畫創作展"
VENUE = "新北市藝文中心第三展覽室"


def norm(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


def exact_detail(href):
    url = urljoin(LIST_URL, href)
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname != "www.culture.ntpc.gov.tw"
            or p.port is not None or p.username or p.password or p.fragment
            or p.path != "/artcenter_chi/xmdoc/cont"):
        return None
    q = parse_qs(p.query, keep_blank_values=True)
    if set(q) - {"sid", "xsmsid", "sq"}:
        return None
    if q.get("sid") != [SID] or q.get("xsmsid") != [XSMSID]:
        return None
    if q.get("sq", [""]) != [""]:
        return None
    return url


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.anchor = None
        self.heading = None
        self.anchors = []
        self.headings = []
        self.texts = []
        # Bind a title and venue label to the smallest enclosing event scope.
        # Aggregating all MAIN text can borrow a venue from a sibling event.
        self.event_scopes = []
        self.active_event_scopes = []
        self.scope_malformed = False

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)
        if tag in ("main", "article", "section"):
            scope = {"tag": tag, "depth": len(self.active_event_scopes),
                     "headings": [], "texts": []}
            self.event_scopes.append(scope)
            self.active_event_scopes.append(scope)
        if tag == "a":
            self.anchor = [dict(attrs).get("href", ""), []]
        if tag in ("h1", "h2", "h3") and any(
                t in ("main", "article") for t in self.stack[:-1]):
            self.heading = [tag, []]

    def handle_data(self, value):
        if self.anchor is not None:
            self.anchor[1].append(value)
        if self.heading is not None:
            self.heading[1].append(value)
        if any(t in ("main", "article") for t in self.stack):
            self.texts.append(value)
        for scope in self.active_event_scopes:
            scope["texts"].append(value)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            self.anchors.append((self.anchor[0], norm("".join(self.anchor[1]))))
            self.anchor = None
        if tag in ("h1", "h2", "h3") and self.heading is not None:
            if tag == self.heading[0]:
                heading = norm("".join(self.heading[1]))
                self.headings.append(heading)
                for scope in self.active_event_scopes:
                    scope["headings"].append(heading)
                self.heading = None
        if tag in ("main", "article", "section"):
            if (not self.active_event_scopes or
                    self.active_event_scopes[-1]["tag"] != tag):
                self.scope_malformed = True
            else:
                self.active_event_scopes.pop()
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break


def inspect_caller_html(list_html, detail_html):
    """No native receipt is generated from injected HTML; strict same-sid only."""
    out = {"kind": "P30_B_NTPC_ARTCENTER_LIST_DETAIL_REVIEW_V1",
           "source": "NTPC_ARTCENTER_OFFICIAL_NOT_FORMAL_19_PLATFORM",
           "sid": SID, "decision": "HOLD",
           "first_failure": "LIST_EDGE_MISSING",
           "same_id_review": 0, "venue_room_review": 0,
           "native_get": 0, "native_body_provenance": False,
           "date_role": "SHOW_DATE_HOLD_TITLE_MONTH_DAY_ONLY",
           "bulletin_date_role": "PUBLICATION_DATE_NOT_SHOW_DATE",
           "formal_accepted_fields": 0, "golden": 0, "published": 0,
           "release_state": "HARD_HOLD_NO_PUBLICATION"}
    listing = Page()
    listing.feed(list_html)
    edges = [(exact_detail(href), title) for href, title in listing.anchors
             if exact_detail(href) is not None]
    if not edges or {title for _, title in edges} != {norm(TITLE)} or len(
            {url for url, _ in edges}) != 1:
        out["first_failure"] = "NTPC_LIST_SID_TITLE_EDGE_HOLD"
        return out
    detail = Page()
    detail.feed(detail_html)
    if detail.headings.count(norm(TITLE)) != 1:
        out["first_failure"] = "NTPC_DETAIL_EVENT_LOCAL_TITLE_HOLD"
        return out
    # A matching heading in one ARTICLE/SECTION cannot borrow the venue
    # from another sibling or from the whole MAIN. Caller HTML is not native.
    title = norm(TITLE)
    owners = [scope for scope in detail.event_scopes
              if scope["headings"].count(title) == 1]
    if detail.scope_malformed or not owners:
        out["first_failure"] = "NTPC_EVENT_LOCAL_SCOPE_HOLD"
        return out
    deepest = max(scope["depth"] for scope in owners)
    owners = [scope for scope in owners if scope["depth"] == deepest]
    if len(owners) != 1:
        out["first_failure"] = "NTPC_EVENT_LOCAL_SCOPE_AMBIGUOUS_HOLD"
        return out
    text = norm(" ".join(owners[0]["texts"]))
    if not re.search(r"展覽地點\s*[：:]\s*" + re.escape(VENUE), text):
        out["first_failure"] = "NTPC_DETAIL_EXACT_VENUE_LABEL_HOLD"
        return out
    out.update(decision="REVIEW_NON_SESSION_ONLY",
               first_failure="NATIVE_RECEIPT_AND_DATE_ROLE_AUTHORITY_PENDING",
               same_id_review=1, venue_room_review=1,
               list_derived_detail_url=edges[0][0],
               field_roles=["EVENT_TITLE_REVIEW", "VENUE_ROOM_REVIEW"])
    return out
