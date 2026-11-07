"""One-shot robots-gated A KKTIX/UDN and B Fuzhong15/Yingge venue adapters.

Only first-party public LIST -> exact same-source DETAIL. Caller HTML and
browser/indexed evidence are never native provenance. No checkout, redirects,
retries, Session/availability inference, raw-body persistence or publication.
"""
from __future__ import annotations
import hashlib
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
    "A_UDN": {
        "source_id": "06", "event_id": "P1AEBJG5",
        "list": "https://tickets.udnfunlife.com/Application/UTK01/UTK0101_.aspx",
        "detail": ("https://tickets.udnfunlife.com/Application/UTK02/"
                   "UTK0201_.aspx?PRODUCT_ID=P1AEBJG5"),
        "title": "倫敦全本音樂劇《史瑞克》",
        "origin": "https://tickets.udnfunlife.com",
    },
    "A_ACCUPASS": {
        # Existing canonical platform #02; one new public search-card hypothesis.
        # This is an indexed discovery only until a separately gated native run.
        "source_id": "02", "event_id": "2610261742421131142843",
        "list": "https://www.accupass.com/search",
        "detail": "https://www.accupass.com/event/2610261742421131142843",
        "title": "讀書會－〖讀品交義〗11月份｜台北場",
        "origin": "https://www.accupass.com",
    },
    "A_TIXCRAFT": {
        # Existing platform #03; fresh public indexed discovery, NOT native evidence.
        "source_id": "03", "event_id": "26_aftp",
        "list": "https://tixcraft.com/activity",
        "detail": "https://tixcraft.com/activity/detail/26_aftp",
        "title": "凱基金控xAccusefive告五人 [在這裡 @century] 世界巡迴演唱會",
        "origin": "https://tixcraft.com",
    },
    "A_KIMU": {
        # Fresh public organizer LIST -> one exact KKTIX event; no checkout.
        # Indexed discovery is not native evidence until one-shot CI executes.
        "source_id": "01", "event_id": "2026itmgameforum",
        "list": "https://kimu.kktix.cc/",
        "detail": "https://kimu.kktix.cc/events/2026itmgameforum",
        "title": "2026資訊月x臺灣教育科技展 ： 數位遊戲主題論壇",
        "origin": "https://kimu.kktix.cc",
    },
    "B_NTCAM": {
        # New Taipei City Art Museum official public event; not platform #20.
        # A dynamic JS-only index must HOLD rather than invent a LIST edge.
        "source_id": "NEW_TAIPEI_ART_MUSEUM_OFFICIAL", "event_id": "E2609013",
        "list": "https://ntcart.museum/event.aspx?kind=current",
        "detail": "https://ntcart.museum/event_content.aspx?id=E2609013",
        "title": "新生地藝術節 𓆸 𝐅𝐥𝐨𝐰𝐞𝐫 𝐄𝐩𝐢𝐬𝐨𝐝𝐞 小插花 𓆹",
        "origin": "https://ntcart.museum",
    },
    "B_ZEPP_TAKASE": {
        # New event rid under existing Zepp New Taipei canonical venue source.
        # Official homepage event card -> exact rid; never infer KKTIX Session.
        "source_id": "ZEPP_NEWTAIPEI_OFFICIAL", "event_id": "160668",
        "list": "https://www.zepp.co.jp/hall/newtaipei/",
        "detail": "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160668",
        "title": "TAKASE TOYA 5th Album “♾️” Release Live in Taipei",
        "origin": "https://www.zepp.co.jp",
        # Official venue DETAIL directly links this public organizer EVENT,
        # not a KKTIX registration/checkout Session or inventory receipt.
        "public_ticket_event": "https://freeplanetml.kktix.cc/events/takasetoya202611",
    },
    "B_KKTIX_TAKASE_DAY1": {
        # Canonical KKTIX platform #01, not a new venue platform.
        # Public organizer index advertises separate -1 (two-day pass),
        # -2 (Nov 7) and -3 (Nov 8) registration event IDs. A Zepp
        # rid=160668 is not any of these ticket event IDs or Sessions.
        "source_id": "01", "event_id": "takasetoya202611-2",
        "list": "https://freeplanetml.kktix.cc/",
        "detail": "https://freeplanetml.kktix.cc/events/takasetoya202611-2",
        "title": "〖11/07場〗TAKASE TOYA 5th Album “∞” Release Live in Taipei",
        "origin": "https://freeplanetml.kktix.cc",
    },
    "B_CERAMICS": {
        "source_id": "YINGGE_CERAMICS_NEWTIPEI_OFFICIAL",
        "event_id": "0Q218346582180038351",
        "list": "https://www.ceramics.ntpc.gov.tw/sitesearch?sq=2026",
        "detail": ("https://www.ceramics.ntpc.gov.tw/xmdoc/cont?"
                   "sid=0Q218346582180038351&sq=2026&xsmsid=0J148497613881029302"),
        "title": "無形之源：道的流動與生成-楊逸雪個展",
        "origin": "https://www.ceramics.ntpc.gov.tw",
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
        # ACCUPASS search cards may append only the three observed
        # discovery UTM tags; no sale/session/checkout parameters survive.
        # The returned URL is always the canonical source event URL.
        query = parse_qsl(actual.query, keep_blank_values=True)
        expected_query = parse_qsl(expected.query, keep_blank_values=True)
        if line == "A_ACCUPASS" and query:
            allowed = {"utm_campaign": "accu_e_", "utm_medium": "search_result_",
                       "utm_source": "web"}
            if (len(query) != len(set(k for k, _ in query))
                    or any(allowed.get(k) != v for k, v in query)):
                return None
            query = []
        if (actual.scheme != "https" or actual.hostname != expected.hostname
                or actual.port is not None or actual.username or actual.password
                or actual.path != expected.path or actual.fragment
                or sorted(query) != sorted(expected_query)):
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
        # A/B identity must be visible event-local DOM, not inert template
        # markup. Never create a LIST anchor, title heading, scope or TR
        # inside SCRIPT/STYLE/NOSCRIPT/TEMPLATE (including nested elements).
        if any(t in IGNORE for t in self.stack):
            return
        if tag in ("article", "section"):
            if len(self.scopes) >= 128:
                raise ValueError("AB_EVENT_LOCAL_SCOPE_CAP_HOLD")
            self.scopes.append(dict(tag=tag, depth=len(self.stack),
                                    headings=[], texts=[], edges=[]))
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
        # Mirror the start-tag inert guard: nested template ARTICLE/TR/A/H
        # must not close or emit evidence for a visible event-local owner.
        if any(t in IGNORE for t in self.stack):
            if tag in self.stack:
                while self.stack:
                    if self.stack.pop() == tag:
                        break
            return
        if tag == "a" and self.anchor is not None:
            edge = (self.anchor[0], norm("".join(self.anchor[1])))
            self.anchors.append(edge)
            for index in self.active_rows:
                self.rows[index]["edges"].append(edge)
            for index in self.active:
                self.scopes[index]["edges"].append(edge)
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
    # UDN HOME cards carry dates/venue/price after the exact event title.
    # A prefixed "四人套票-" is a different PRODUCT and cannot pass.
    return [(exact_detail(line, href), label) for href, label in p.anchors
            if exact_detail(line, href) and
            (label == title or (line == "A_UDN" and label.startswith(title + " ")) or
             (line == "B_ZEPP_TAKASE" and label.count(title) == 1
              and "2026 11.7" in label and "18:00" in label))]

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



def foreign_same_source_event_edges(line, scope):
    """Detect a sibling event/product URL inside the title-owned DOM scope.

    A valid event heading alone does not own a neighboring event's SHOW/HALL.
    Reject same-origin sibling detail paths and same-path different event IDs,
    but never treat a cross-source ticket edge as the venue's event ID.
    """
    expected = urlsplit(SOURCES[line]["detail"])
    parent = expected.path.rsplit("/", 1)[0] + "/"
    foreign = 0
    for href, _ in scope["edges"]:
        if not isinstance(href, str) or not href:
            continue
        try:
            u = urlsplit(urljoin(SOURCES[line]["detail"], href))
        except ValueError:
            return 1
        if (u.scheme != "https" or u.hostname != expected.hostname
                or u.port is not None or u.username or u.password):
            continue
        # KKTIX's exact event URL may expose an English/localized view.
        # A locale-only link is still this event, never a new event ID;
        # all other query differences (including duplicate locale keys)
        # remain foreign and fail closed.
        same_event_locale = (
            line == "B_KKTIX_TAKASE_DAY1"
            and u.path == expected.path and not expected.query
            and parse_qsl(u.query, keep_blank_values=True)
            in ([("locale", "en")], [("locale", "zh-TW")]))
        same_path_different_id = (u.path == expected.path and
                                  u.query != expected.query and
                                  not same_event_locale)
        sibling_detail_path = (u.path.startswith(parent) and
                               u.path != expected.path)
        if same_path_different_id or sibling_detail_path:
            foreign += 1
    return foreign


def inspect_pair(line, listing, detail):
    """Offline/caller HTML never establishes a native GET or a formal FIELD."""
    if line not in SOURCES:
        raise ValueError("AB_SOURCE_LINE_HOLD")
    result = dict(decision="HOLD", first_failure="AB_LIST_EXACT_EDGE_HOLD",
                  same_id_review=0, field_roles=[], ticket_event_edge_review=0,
                  formal_accepted_fields=0)
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
    # Field roles must not borrow dates or halls from a sibling event's
    # same-source DETAIL link within an otherwise title-owned container.
    foreign = foreign_same_source_event_edges(line, owned[0])
    if foreign:
        result["first_failure"] = "AB_EVENT_LOCAL_FOREIGN_SAME_SOURCE_EVENT_HOLD"
        result["foreign_event_edge_count"] = foreign
        return result
    local = norm(" ".join(owned[0]["texts"]))
    # Only a digest and role names leave the native reader, never raw HTML.
    result["event_local_scope"] = {
        "tag": owned[0]["tag"],
        "normalized_text_sha256": hashlib.sha256(local.encode("utf-8")).hexdigest(),
        "foreign_event_edge_count": 0,
        "raw_scope_saved": False,
    }
    if line == "A_UDN":
        # Range and hall are non-session REVIEW only, and only from an
        # unambiguous exact-title-owned ARTICLE/SECTION (not global HOME).
        if len(re.findall(r"2026/11/20\s*[~～]\s*2026/11/29", local)) == 1:
            result["field_roles"].append("ADVERTISED_SHOW_RANGE_REVIEW_NO_SESSION")
        if local.count("臺北表演藝術中心 大劇院") == 1:
            result["field_roles"].append("VENUE_TPAC_GRAND_THEATER_REVIEW")
    elif line == "A_ACCUPASS":
        # Explicit event-local advertised date and venue, never registration
        # inventory or an independently accepted ticket Session.
        if len(re.findall(r"2026[./]11[./]22\s*(?:\(Sun\)\s*)?13:45\s*[-–]\s*17:00", local)) == 1:
            result["field_roles"].append("ADVERTISED_EVENT_RANGE_REVIEW_NO_SESSION")
        if local.count("植境plantārium-複合式空間") == 1:
            result["field_roles"].append("VENUE_PLANTARIUM_REVIEW")
    elif line == "A_KIMU":
        # Only the event-local organizer text, not the KKTIX checkout or
        # ticket availability, may establish non-session REVIEW roles.
        if len(re.findall(
                r"2026/11/14\s*(?:\(六\))?\s*10:00\s*[-–]\s*16:30", local)) == 1:
            result["field_roles"].append("FORUM_TIME_RANGE_REVIEW_NOT_TICKET_SESSION")
        if local.count("世貿展覽館一館 / 1F數發部數產署主題館舞台區") == 1:
            result["field_roles"].append("VENUE_TWTC_HALL1_STAGE_REVIEW")
    elif line == "B_NTCAM":
        # Museum indexed page may be client-rendered. Identity is REVIEW
        # only if a unique exact native LIST edge and DETAIL heading exist.
        # No inferred date, price, registration or Session from SEO metadata.
        pass
    elif line == "B_ZEPP_TAKASE":
        # Independent public reader saw this exact organizer EVENT link on
        # Zepp rid=160668. Only a uniquely title-owned ARTICLE/SECTION may
        # attest the edge in a future native body. Do not borrow global nav,
        # sibling-event anchors, duplicate edges, or registration Sessions.
        expected = SOURCES[line]["public_ticket_event"]
        matches = [edge for edge in owned[0]["edges"]
                   if edge == (expected, "KKTIX")]
        if len(matches) == 1 and len(owned[0]["edges"]) <= 32:
            result["ticket_event_edge_review"] = 1
            result["ticket_event_url"] = expected
            result["decision"] = "REVIEW_SOURCE_DIRECT_TICKET_EDGE_NO_SESSION"
            result["first_failure"] = "AB_EVENT_LOCAL_DATE_HALL_AUTHORITY_HOLD"
        # The source page describes TWO days; rid=160668 does not attest
        # both event-local sessions or an eligible price. DATE/HALL stay HOLD.
    elif line == "B_KKTIX_TAKASE_DAY1":
        # An organizer LIST edge to its own exact registration event ID
        # plus an exact DETAIL heading is identity REVIEW, not a Session.
        # DAY1 show start must be explicitly event-local and may never be
        # borrowed from DAY2, the two-day pass or a ticket sale deadline.
        # A title-owned article may still contain DAY2 or a two-day
        # ticket description. In that case neither SHOW nor HALL is
        # attributable to DAY1, even when one DAY1 time is present.
        mixed_day = re.search(
            r"(?i)\[DAY\s*2\]|(?:2026\s*[年./-]\s*)?11\s*(?:月|[./-])\s*0?8(?:\s*日|(?!\d))|兩日(?:通票|票)|雙日(?:通票|票)",
            local)
        if mixed_day:
            result["first_failure"] = "AB_KKTIX_DAY1_MIXED_EVENT_LOCAL_DAY_HOLD"
            return result
        if (len(re.findall(r"\[DAY1\]\s*SETLIST\s*A", local)) == 1
                and len(re.findall(r"日期\s*:\s*2026年11月7日", local)) == 1
                and len(re.findall(
                    r"時間\s*:\s*開場\s*17:00\s*/\s*開演\s*18:00", local)) == 1):
            result["field_roles"].append("KKTIX_DAY1_SHOW_START_REVIEW_NOT_SESSION")
        if len(re.findall(r"會場\s*:\s*Zepp New Taipei", local)) == 1:
            result["field_roles"].append("KKTIX_DAY1_HALL_REVIEW")
        # This KKTIX source does not independently attest the Zepp rid.
    elif line == "B_CERAMICS":
        if len(re.findall(r"展覽時間\s*[:：]\s*2026年11月20日至2026年12月20日", local)) == 1:
            result["field_roles"].append("EXHIBITION_RANGE_REVIEW_NO_SESSION")
        if len(re.findall(r"展覽地點\s*[:：]\s*[Bb]1陶藝長廊", local)) == 1:
            result["field_roles"].append("VENUE_B1_CERAMICS_GALLERY_REVIEW")
    elif line == "A":
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



def adjudicate_robots_policy(body, agent, urls):
    """Fail-closed policy authority; retain only rule counts, never robots body.

    A generic robots HTTP200 or an unrelated User-agent is not an applicable
    permission. The sealed native receipt supplies bytes/SHA/UTC separately.
    """
    out = dict(kind="P30_AB_ROBOTS_APPLICABLE_AUTHORITY_V1",
               decision="HOLD", first_failure="AB_ROBOTS_UNREADABLE_HOLD",
               applicable_groups=0, applicable_rulelines=0,
               checked_urls=0, raw_policy_saved=False)
    if (not isinstance(body, str) or not isinstance(agent, str)
            or not isinstance(urls, (tuple, list)) or len(urls) not in (1, 2)):
        return out
    if not body or len(body.encode("utf-8")) > 65536:
        out["first_failure"] = "AB_ROBOTS_EMPTY_OR_BOUNDS_HOLD"
        return out
    if re.search(r"(?i)<(?:!doctype\s+html|html|head|body)(?:\s|>)",
                 body[:2048]):
        out["first_failure"] = "AB_ROBOTS_HTML_FALLBACK_HOLD"
        return out
    if not re.search(r"(?im)^\s*user-agent\s*:\s*[^\s#]+", body):
        out["first_failure"] = "AB_ROBOTS_NO_USER_AGENT_HOLD"
        return out
    if any(not isinstance(u, str) or urlsplit(u).scheme != "https"
           for u in urls):
        out["first_failure"] = "AB_ROBOTS_TARGET_URL_HOLD"
        return out
    policy = urllib.robotparser.RobotFileParser()
    policy.parse(body.splitlines())
    groups = [entry for entry in policy.entries
              if entry.applies_to(agent)]
    if policy.default_entry is not None and policy.default_entry.applies_to(agent):
        groups.append(policy.default_entry)
    out["applicable_groups"] = len(groups)
    out["applicable_rulelines"] = sum(len(e.rulelines) for e in groups)
    if not groups or not out["applicable_rulelines"]:
        out["first_failure"] = "AB_ROBOTS_APPLICABLE_RULE_MISSING_HOLD"
        return out
    out["checked_urls"] = len(urls)
    if not all(policy.can_fetch(agent, u) for u in urls):
        out["first_failure"] = "AB_ROBOTS_DISALLOW_HOLD"
        return out
    out.update(decision="ALLOW", first_failure=None)
    return out

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
               field_roles=[], list_row_roles=[], field_receipts=[], native_lkg=0,
               formal_accepted_fields=0, golden=0, published=0,
               raw_html_saved=False, release_state="HARD_HOLD_NO_PUBLICATION",
               source_receipts=[], decision="HOLD", first_failure="NOT_STARTED")
    opener = urllib.request.build_opener(NoRedirect())
    try:
        out["native_get_attempted"] += 1
        robots, rr = read_public(opener, source["origin"] + "/robots.txt", "text/plain")
        out["robots_receipt"] = rr
        audit = adjudicate_robots_policy(
            robots, UA, (source["list"], source["detail"]))
        out["robots_policy_audit"] = audit
        if audit["decision"] != "ALLOW":
            raise ValueError(audit["first_failure"])
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
        if "event_local_scope" in verdict:
            out["event_local_scope"] = verdict["event_local_scope"]
        out["ticket_event_edge_review"] = verdict.get("ticket_event_edge_review", 0)
        if out["ticket_event_edge_review"]:
            out["ticket_event_url"] = verdict["ticket_event_url"]
        out["list_row_roles"] = verdict.get("list_row_roles", [])
        if verdict["same_id_review"]:
            roles = ["SOURCE_EXACT_TITLE_REVIEW"] + verdict["field_roles"]
            out["field_receipts"] = [
                dict(source_id=source["source_id"], event_id=source["event_id"],
                     source_url=source["detail"], body_sha256=dr["body_sha256"],
                     observed_at_utc=dr["observed_at_utc"],
                     role=role, decision="REVIEW", formal_accepted=False,
                     event_local_scope_sha256=(
                         verdict["event_local_scope"]["normalized_text_sha256"]
                         if "event_local_scope" in verdict else None))
                for role in roles]
            # LIST row roles are bound to LIST bytes/clock, never DETAIL.
            out["field_receipts"].extend(
                dict(source_id=source["source_id"], event_id=source["event_id"],
                     source_url=source["list"], body_sha256=lr["body_sha256"],
                     observed_at_utc=lr["observed_at_utc"], role=role,
                     decision="REVIEW", formal_accepted=False)
                for role in out["list_row_roles"])
    except (ValueError, UnicodeError, OSError, TimeoutError, urllib.error.URLError) as exc:
        out["first_failure"] = type(exc).__name__ + ":" + str(exc)[:180]
    return out


if __name__ == "__main__":
    # Explicit native one-shot sources are selected by the CI gate; never
    # silently repeat previously consumed KKTIX/Fuzhong probes.
    for stream in ("A_UDN", "B_CERAMICS"):
        print(json.dumps(run_native_once(stream), ensure_ascii=False, sort_keys=True))
