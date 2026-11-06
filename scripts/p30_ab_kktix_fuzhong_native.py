"""One-shot robots-gated A KKTIX/UDN and B Fuzhong15/Yingge venue adapters.

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
    "B_ZEPP_TAKASE": {
        # New event rid under existing Zepp New Taipei canonical venue source.
        # Official homepage event card -> exact rid; never infer KKTIX Session.
        "source_id": "ZEPP_NEWTAIPEI_OFFICIAL", "event_id": "160668",
        "list": "https://www.zepp.co.jp/hall/newtaipei/",
        "detail": "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=160668",
        "title": "TAKASE TOYA 5th Album “♾️” Release Live in Taipei",
        "origin": "https://www.zepp.co.jp",
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
    elif line == "B_ZEPP_TAKASE":\n        # Multi-day copy in this page is not a single Session or FIELD.\n        # Only source-bound title/identity can be REVIEW pending native DOM.\n        pass\n    elif line == "B_CERAMICS":
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
        out["list_row_roles"] = verdict.get("list_row_roles", [])
        if verdict["same_id_review"]:
            roles = ["SOURCE_EXACT_TITLE_REVIEW"] + verdict["field_roles"]
            out["field_receipts"] = [
                dict(source_id=source["source_id"], event_id=source["event_id"],
                     source_url=source["detail"], body_sha256=dr["body_sha256"],
                     observed_at_utc=dr["observed_at_utc"],
                     role=role, decision="REVIEW", formal_accepted=False)
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
