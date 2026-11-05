"""A FamiTicket #07 and B New Taipei Art Center official native source rotation.

One bounded public robots/LIST/exact-detail sequence per line. No checkout,
redirects, retries, raw HTML persistence, LKG promotion, Golden or publishing.
A CI-run source receipt is evidence only when that exact run actually executes.
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
from urllib.parse import urljoin, urlsplit
from scripts import p30_ntpc_artcenter_source as ntpc

FAMI_LIST = "https://www.famiticket.com.tw/Home"
FAMI_DETAIL = ("https://www.famiticket.com.tw/Home/Activity/Info/"
    "RgBhADYAOABvAGoANQBDAEYAdQB0AEIAbwBVACsAOAB0AGUAUgBkADUAMABrADUAVABiAE0AMwB4ADcAcABMAHoAUgB2AGMAVABSAFEAbQB3AG8ARQA9AA2")
FAMI_TITLE = "Ultra Taiwan 2026 超世代音樂節"
UA = "EventRadarPublicSourceAudit/1.0"
CAP = 2 * 1024 * 1024


def norm(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


class LocalHTML(HTMLParser):
    """Collect complete anchor label/IMG ALT and MAIN/ARTICLE headings only."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.anchors = []
        self.headings = []
        self.anchor = None
        self.heading = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in ("br", "img", "meta", "link", "input", "hr", "source"):
            self.stack.append(tag)
        if tag == "a":
            self.anchor = [attrs.get("href", ""), []]
        if tag == "img" and self.anchor is not None:
            self.anchor[1].append(attrs.get("alt", ""))
        if tag in ("h1", "h2", "h3") and any(
                x in ("main", "article") for x in self.stack[:-1]):
            self.heading = [tag, []]

    def handle_data(self, data):
        if self.anchor is not None:
            self.anchor[1].append(data)
        if self.heading is not None:
            self.heading[1].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            self.anchors.append((self.anchor[0], norm("".join(self.anchor[1]))))
            self.anchor = None
        if self.heading is not None and tag == self.heading[0]:
            self.headings.append(norm("".join(self.heading[1])))
            self.heading = None
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break


def fami_exact_link(href):
    if not isinstance(href, str) or not href:
        return None
    try:
        u = urljoin(FAMI_LIST, href)
        p, e = urlsplit(u), urlsplit(FAMI_DETAIL)
        if (p.scheme == e.scheme == "https" and p.hostname == e.hostname
                and p.path == e.path and p.query == e.query and not p.fragment
                and p.port is None and not p.username and not p.password):
            return u
    except ValueError:
        pass
    return None


def inspect_pair(line, listing, detail):
    """No native attestation from caller HTML; exact event-local identity."""
    if line not in ("A", "B"):
        raise ValueError("ROTATION_LINE_HOLD")
    lp, dp = LocalHTML(), LocalHTML()
    lp.feed(listing)
    dp.feed(detail)
    if line == "A":
        edges = [(fami_exact_link(h), t) for h, t in lp.anchors
                 if fami_exact_link(h)]
        title, role = FAMI_TITLE, "TICKET_EVENT_TITLE_REVIEW"
    else:
        edges = [(ntpc.exact_detail(h), t) for h, t in lp.anchors
                 if ntpc.exact_detail(h)]
        title, role = ntpc.TITLE, "VENUE_EXHIBITION_TITLE_REVIEW"
    if len(edges) != 1 or edges[0][1] != norm(title):
        return {"decision": "HOLD", "first_failure": "ROTATION_LIST_EXACT_EDGE_TITLE_HOLD",
                "same_id_review": 0, "field_review": 0}
    if dp.headings.count(norm(title)) != 1:
        return {"decision": "HOLD", "first_failure": "ROTATION_DETAIL_MAIN_LOCAL_TITLE_HOLD",
                "same_id_review": 0, "field_review": 0}
    if line == "B":
        strict = ntpc.inspect_caller_html(listing, detail)
        if strict["same_id_review"] != 1:
            return {"decision": "HOLD", "first_failure": strict["first_failure"],
                    "same_id_review": 0, "field_review": 0}
    return {"decision": "REVIEW_NON_SESSION_ONLY",
            "first_failure": "INDEPENDENT_FIELD_AUTHORITY_AND_NATIVE_LKG_PENDING",
            "same_id_review": 1, "field_review": 1 if line == "A" else 2,
            "detail_url": edges[0][0], "title_role": role,
            "formal_accepted_fields": 0}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_public(opener, url, content_type):
    request = urllib.request.Request(url, method="GET", headers={
        "User-Agent": UA, "Accept": content_type, "Accept-Encoding": "identity"})
    with opener.open(request, timeout=10) as response:
        raw = response.read(CAP + 1)
        status, final, ctype = response.status, response.geturl(), response.headers.get("Content-Type", "")
    if status != 200 or final != url:
        raise ValueError("ROTATION_STATUS_REDIRECT_HOLD")
    if not 0 < len(raw) <= CAP:
        raise ValueError("ROTATION_EMPTY_OR_BODY_CAP_HOLD")
    # A robots.txt request returning the HTML HOME body is NOT policy authority.
    # Enforce the requested media role before treating robots as an allow.
    media = ctype.split(";", 1)[0].strip().lower()
    expected = ("text/plain",) if content_type == "text/plain" else (
        "text/html", "application/xhtml+xml")
    if media not in expected:
        raise ValueError("ROTATION_ROBOTS_MIME_HOLD" if content_type == "text/plain"
                         else "ROTATION_HTML_MIME_HOLD")
    stamp = datetime.now(timezone.utc).isoformat()
    receipt = {"url": url, "http_status": status, "body_bytes": len(raw),
               "body_sha256": hashlib.sha256(raw).hexdigest(),
               "content_type": media,
               "observed_at_utc": stamp, "transport": "NATIVE_NO_REDIRECT_NO_RETRY"}
    return raw.decode("utf-8", "strict"), receipt


def run_native_once(line):
    """Exactly robots then LIST, and DETAIL only after exact local edge."""
    if line not in ("A", "B"):
        raise ValueError("ROTATION_LINE_HOLD")
    listing = FAMI_LIST if line == "A" else ntpc.LIST_URL
    detail = FAMI_DETAIL if line == "A" else (
        "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?"
        "sid=" + ntpc.SID + "&sq=&xsmsid=" + ntpc.XSMSID)
    origin = "https://www.famiticket.com.tw" if line == "A" else "https://www.culture.ntpc.gov.tw"
    out = {"kind": "P30_AB_OFFICIAL_NATIVE_ROTATION_V1", "line": line,
           "source_id": "07" if line == "A" else "NTPC_ARTCENTER_OFFICIAL",
           "native_get_attempted": 0, "native_http200": 0, "native_list": 0,
           "native_detail": 0, "native_same_id_review": 0,
           "native_same_id_lkg": 0, "formal_accepted_fields": 0,
           "golden": 0, "published": 0,
           "release_state": "HARD_HOLD_NO_PUBLICATION",
           "raw_html_saved": False, "source_receipts": [],
           "decision": "HOLD", "first_failure": "NOT_STARTED"}
    opener = urllib.request.build_opener(NoRedirect())
    try:
        out["native_get_attempted"] += 1
        robots, receipt = read_public(opener, origin + "/robots.txt", "text/plain")
        out["robots_receipt"] = receipt
        # Explicit user-agent directive is mandatory: empty/HTML fallback fails closed.
        if not re.search(r"(?im)^\s*user-agent\s*:\s*[^\s#]+", robots):
            raise ValueError("ROTATION_ROBOTS_NO_USER_AGENT_HOLD")
        if re.search(r"(?i)<(?:!doctype\s+html|html|head|body)(?:\s|>)", robots[:2048]):
            raise ValueError("ROTATION_ROBOTS_HTML_FALLBACK_HOLD")
        policy = urllib.robotparser.RobotFileParser()
        policy.parse(robots.splitlines())
        if not policy.can_fetch(UA, listing) or not policy.can_fetch(UA, detail):
            raise ValueError("ROTATION_ROBOTS_DISALLOW_HOLD")
        out["policy_decision"] = "ROBOTS_ALLOW"
        out["native_get_attempted"] += 1
        list_html, lr = read_public(opener, listing, "text/html")
        if receipt["body_sha256"] == lr["body_sha256"]:
            raise ValueError("ROTATION_ROBOTS_LIST_IDENTICAL_BODY_HOLD")
        out["source_receipts"].append(lr)
        out["native_http200"] += 1
        out["native_list"] = 1
        parsed = LocalHTML()
        parsed.feed(list_html)
        edges = [(fami_exact_link(h), t) for h, t in parsed.anchors if fami_exact_link(h)] if line == "A" else [
            (ntpc.exact_detail(h), t) for h, t in parsed.anchors if ntpc.exact_detail(h)]
        if len(edges) != 1 or edges[0][1] != norm(FAMI_TITLE if line == "A" else ntpc.TITLE):
            raise ValueError("ROTATION_NATIVE_LIST_EXACT_EDGE_TITLE_HOLD")
        if not policy.can_fetch(UA, edges[0][0]):
            raise ValueError("ROTATION_ROBOTS_LIST_DERIVED_DETAIL_DISALLOW")
        out["native_get_attempted"] += 1
        detail_html, dr = read_public(opener, edges[0][0], "text/html")
        out["source_receipts"].append(dr)
        out["native_http200"] += 1
        out["native_detail"] = 1
        result = inspect_pair(line, list_html, detail_html)
        out["decision"], out["first_failure"] = result["decision"], result["first_failure"]
        out["native_same_id_review"] = result["same_id_review"]
        out["field_review"] = result["field_review"]
    except (ValueError, UnicodeError, OSError, TimeoutError, urllib.error.URLError) as exc:
        out["first_failure"] = type(exc).__name__ + ":" + str(exc)[:160]
    return out



# Distinct native rotation: indexed public discovery only, not prior native PASS.
# Existing Fami/Cloud Gate probes remain immutable and are never repeated here.
NEXT = {
 "A":dict(id="26_minhyun",source="03",origin="https://tixcraft.com",
          listing="https://tixcraft.com/activity",
          detail="https://tixcraft.com/activity/detail/26_minhyun",
          title="2026 HWANG MIN HYUN FANMEETING [PEACH-BLOSSOM] - TAIPEI",
          venue="Legacy TERA"),
 "B":dict(id="167511",source="ZEPP_NEWTAIPEI_OFFICIAL",
          origin="https://www.zepp.co.jp",
          listing="https://www.zepp.co.jp/hall/newtaipei/schedule/",
          detail="https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=167511",
          title="Karencici The Loser Concert 2026",venue="Zepp New Taipei"),
}

class NextScoped(LocalHTML):
    def __init__(self):
        super().__init__()
        self.local_text, self.local_size = [], 0

    def handle_data(self, value):
        super().handle_data(value)
        if any(t in ("main", "article") for t in self.stack) and not any(
                t in ("script", "style", "noscript", "template") for t in self.stack):
            self.local_size += len(value)
            if self.local_size > 200000:
                raise ValueError("NEXT_LOCAL_TEXT_CAP_HOLD")
            self.local_text.append(value)

def exact_next_href(line, href):
    from urllib.parse import parse_qsl
    if line not in NEXT or not isinstance(href, str) or not href:
        return None
    cfg = NEXT[line]
    try:
        url = urljoin(cfg["listing"], href)
        p, e = urlsplit(url), urlsplit(cfg["detail"])
        if (p.scheme != "https" or p.netloc != e.netloc or p.path != e.path
                or p.username or p.password or p.fragment or p.port is not None):
            return None
        if line == "A" and p.query:
            return None
        if line == "B" and parse_qsl(p.query, keep_blank_values=True) != [("rid","167511")]:
            return None
        return url
    except (TypeError, ValueError):
        return None

def inspect_next_pair(line, listing_html, detail_html):
    """Caller HTML cannot claim native provenance; event-local only."""
    if line not in NEXT:
        raise ValueError("NEXT_LINE_HOLD")
    cfg = NEXT[line]
    lp, dp = NextScoped(), NextScoped()
    lp.feed(listing_html)
    dp.feed(detail_html)
    edges = [(exact_next_href(line,h),norm(t)) for h,t in lp.anchors if exact_next_href(line,h)]
    if len(edges) != 1 or norm(cfg["title"]) not in edges[0][1]:
        return dict(decision="HOLD",reason="NEXT_LIST_EXACT_ID_TITLE_HOLD",identity=0,fields=0)
    if dp.headings.count(norm(cfg["title"])) != 1:
        return dict(decision="HOLD",reason="NEXT_DETAIL_MAIN_TITLE_HOLD",identity=0,fields=0)
    if norm(cfg["venue"]).casefold() not in norm(" ".join(dp.local_text)).casefold():
        return dict(decision="HOLD",reason="NEXT_EVENT_LOCAL_VENUE_HOLD",identity=1,fields=1)
    return dict(decision="REVIEW_NON_SESSION_ONLY",reason="INDEPENDENT_ACCEPTANCE_AND_LKG_HOLD",
                identity=1,fields=2,roles=["SOURCE_EVENT_TITLE_REVIEW","SOURCE_VENUE_REVIEW"])

def run_next_native_once(line):
    """One robots+LIST+conditional DETAIL, bounded, no redirect/retry/checkout."""
    if line not in NEXT:
        raise ValueError("NEXT_LINE_HOLD")
    cfg=NEXT[line]
    out=dict(kind="P30_AB_DISTINCT_NATIVE_ONESHOT_V1",line=line,
             source_id=cfg["source"],event_id=cfg["id"],attempted=0,
             http200=0,native_list=0,native_detail=0,native_identity=0,
             review_fields=0,field_receipts=[],source_receipts=[],native_lkg=0,
             formal_fields=0,golden=0,published=0,raw_html_saved=False,
             release_state="HARD_HOLD_NO_PUBLICATION",decision="HOLD",
             first_failure="NOT_STARTED")
    opener=urllib.request.build_opener(NoRedirect())
    try:
        out["attempted"]+=1
        robots,rr=read_public(opener,cfg["origin"]+"/robots.txt","text/plain")
        out["robots_receipt"]=rr
        if not re.search(r"(?im)^\s*user-agent\s*:\s*[^\s#]+",robots):
            raise ValueError("NEXT_ROBOTS_NO_DIRECTIVE_HOLD")
        if re.search(r"(?i)<(?:!doctype\s+html|html|head|body)(?:\s|>)",robots[:2048]):
            raise ValueError("NEXT_ROBOTS_HTML_FALLBACK_HOLD")
        policy=urllib.robotparser.RobotFileParser()
        policy.parse(robots.splitlines())
        if not all(policy.can_fetch(UA,url) for url in (cfg["listing"],cfg["detail"])):
            raise ValueError("NEXT_ROBOTS_DISALLOW_HOLD")
        out["policy"]="ROBOTS_ALLOW"
        out["attempted"]+=1
        listing,lr=read_public(opener,cfg["listing"],"text/html")
        if rr["body_sha256"]==lr["body_sha256"]:
            raise ValueError("NEXT_ROBOTS_LIST_SAME_BODY_HOLD")
        out["source_receipts"].append(lr)
        out["http200"]+=1
        out["native_list"]=1
        parsed=NextScoped()
        parsed.feed(listing)
        edges=[(exact_next_href(line,h),norm(t)) for h,t in parsed.anchors
               if exact_next_href(line,h)]
        if len(edges)!=1 or norm(cfg["title"]) not in edges[0][1]:
            raise ValueError("NEXT_NATIVE_LIST_EXACT_EDGE_HOLD")
        out["attempted"]+=1
        detail,dr=read_public(opener,edges[0][0],"text/html")
        out["source_receipts"].append(dr)
        out["http200"]+=1
        out["native_detail"]=1
        parsed=inspect_next_pair(line,listing,detail)
        out["decision"],out["first_failure"]=parsed["decision"],parsed["reason"]
        out["native_identity"],out["review_fields"]=parsed["identity"],parsed["fields"]
        if parsed["decision"]=="REVIEW_NON_SESSION_ONLY":
            out["field_receipts"]=[dict(source_url=dr["url"],event_id=cfg["id"],
                body_sha256=dr["body_sha256"],observed_at_utc=dr["observed_at_utc"],
                role=role,decision="REVIEW",formal_accepted=False)
                for role in parsed["roles"]]
    except (ValueError,UnicodeError,OSError,TimeoutError,urllib.error.URLError) as exc:
        out["first_failure"]=type(exc).__name__+":"+str(exc)[:180]
    return out

if __name__ == "__main__":
    for line in ("A", "B"):
        print(json.dumps(run_native_once(line), ensure_ascii=False, sort_keys=True))
