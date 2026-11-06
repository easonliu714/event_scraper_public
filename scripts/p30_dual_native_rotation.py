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
    """Bind event field text to an event-local ARTICLE/SECTION, not MAIN-wide."""
    def __init__(self):
        super().__init__()
        self.local_text, self.local_size = [], 0
        self.scopes, self.active_scopes = [], []

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        if tag in ("main", "article", "section"):
            if len(self.scopes) >= 256:
                raise ValueError("NEXT_EVENT_SCOPE_CAP_HOLD")
            self.scopes.append(dict(tag=tag, depth=len(self.stack),
                                    texts=[], headings=[]))
            self.active_scopes.append(len(self.scopes) - 1)

    def handle_data(self, value):
        super().handle_data(value)
        if any(t in ("main", "article") for t in self.stack) and not any(
                t in ("script", "style", "noscript", "template") for t in self.stack):
            self.local_size += len(value)
            if self.local_size > 200000:
                raise ValueError("NEXT_LOCAL_TEXT_CAP_HOLD")
            self.local_text.append(value)
            for idx in self.active_scopes:
                self.scopes[idx]["texts"].append(value)

    def handle_endtag(self, tag):
        if self.heading is not None and tag == self.heading[0]:
            heading = norm("".join(self.heading[1]))
            for idx in self.active_scopes:
                self.scopes[idx]["headings"].append(heading)
        super().handle_endtag(tag)
        self.active_scopes = [idx for idx in self.active_scopes
                              if self.scopes[idx]["depth"] <= len(self.stack)]

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
    # MAIN-wide venue text could belong to another event's sibling article.
    owned_scopes = [scope for scope in dp.scopes
                    if norm(cfg["title"]) in scope["headings"]]
    if any(scope["tag"] in ("article", "section") for scope in owned_scopes):
        owned_scopes = [scope for scope in owned_scopes
                        if scope["tag"] in ("article", "section")]
    if not any(norm(cfg["venue"]).casefold() in
               norm(" ".join(scope["texts"])).casefold()
               for scope in owned_scopes):
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



# Offline-only sealed native artifact -> receipt identity LKG.  No raw HTML
# replay, no network, no FIELD/Golden/publication promotion.
def audit_next_native_receipt_archive(archive, *, expected_zip_sha256, expected_head):
    import io
    import zipfile
    from datetime import timedelta
    if not isinstance(archive, bytes) or not 0 < len(archive) <= 1048576:
        raise ValueError("NEXT_RECEIPT_ARCHIVE_BOUND_HOLD")
    if (not re.fullmatch(r"[0-9a-f]{64}", expected_zip_sha256 or "")
            or hashlib.sha256(archive).hexdigest() != expected_zip_sha256):
        raise ValueError("NEXT_RECEIPT_ARTIFACT_SHA_HOLD")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_head or ""):
        raise ValueError("NEXT_RECEIPT_HEAD_HOLD")
    required = {"SHA256SUMS.txt", "readiness.txt",
                "next_native_A.json", "next_native_B.json"}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names = z.namelist()
        if (len(names) != len(set(names)) or len(names) > 20
                or not required.issubset(names)
                or any("/" in n or "\\" in n or n.startswith(".") for n in names)
                or any(i.file_size > 131072 for i in z.infolist())
                or z.testzip() is not None):
            raise ValueError("NEXT_RECEIPT_ZIP_CRC_MEMBERS_HOLD")
        files = {n: z.read(n) for n in names}
    manifest = {}
    for line in files["SHA256SUMS.txt"].decode("utf-8", "strict").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\s]+)", line)
        if not match or match[2] in manifest:
            raise ValueError("NEXT_RECEIPT_MANIFEST_FORMAT_HOLD")
        manifest[match[2]] = match[1]
    for name in required - {"SHA256SUMS.txt"}:
        path = "evidence/" + name
        if (path not in manifest
                or hashlib.sha256(files[name]).hexdigest() != manifest[path]):
            raise ValueError("NEXT_RECEIPT_MANIFEST_SHA_HOLD")
    for name in names:
        if name != "SHA256SUMS.txt" and "evidence/" + name in manifest:
            if hashlib.sha256(files[name]).hexdigest() != manifest["evidence/" + name]:
                raise ValueError("NEXT_RECEIPT_EXTRA_MANIFEST_SHA_HOLD")
    readiness = files["readiness.txt"].decode("utf-8", "strict").splitlines()
    if ("head=" + expected_head not in readiness
            or not {"formal_fields=0", "golden=0", "published=0"}.issubset(readiness)):
        raise ValueError("NEXT_RECEIPT_EXACT_HEAD_RELEASE_HOLD")
    a = json.loads(files["next_native_A.json"])
    b = json.loads(files["next_native_B.json"])
    if (a.get("line") != "A" or a.get("event_id") != NEXT["A"]["id"]
            or a.get("native_lkg") != 0 or a.get("formal_fields") != 0
            or a.get("golden") != 0 or a.get("published") != 0):
        raise ValueError("NEXT_RECEIPT_A_RELEASE_PARITY_HOLD")
    expected = {"kind": "P30_AB_DISTINCT_NATIVE_ONESHOT_V1",
                "line": "B", "source_id": NEXT["B"]["source"],
                "event_id": NEXT["B"]["id"], "attempted": 3,
                "http200": 2, "native_list": 1, "native_detail": 1,
                "native_identity": 1, "review_fields": 2,
                "native_lkg": 0, "formal_fields": 0, "golden": 0,
                "published": 0, "raw_html_saved": False,
                "release_state": "HARD_HOLD_NO_PUBLICATION",
                "decision": "REVIEW_NON_SESSION_ONLY",
                "first_failure": "INDEPENDENT_ACCEPTANCE_AND_LKG_HOLD",
                "policy": "ROBOTS_ALLOW"}
    if any(type(b.get(k)) is not type(v) or b[k] != v for k, v in expected.items()):
        raise ValueError("NEXT_RECEIPT_B_IDENTITY_RELEASE_HOLD")
    robots, pages, fields = b.get("robots_receipt"), b.get("source_receipts"), b.get("field_receipts")
    if not isinstance(robots, dict) or not isinstance(pages, list) or len(pages) != 2:
        raise ValueError("NEXT_RECEIPT_MISSING_TRANSPORT_HOLD")
    if not isinstance(fields, list) or len(fields) != 2:
        raise ValueError("NEXT_RECEIPT_MISSING_FIELDS_HOLD")
    def check_receipt(rec, url, mime, cap):
        if (not isinstance(rec, dict) or rec.get("url") != url
                or rec.get("http_status") != 200
                or rec.get("content_type") != mime
                or rec.get("transport") != "NATIVE_NO_REDIRECT_NO_RETRY"
                or type(rec.get("body_bytes")) is not int
                or not 0 < rec["body_bytes"] <= cap
                or not isinstance(rec.get("body_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", rec["body_sha256"])):
            raise ValueError("NEXT_RECEIPT_SOURCE_ROLE_SHA_HOLD")
        try:
            stamp = datetime.fromisoformat(rec["observed_at_utc"].replace("Z", "+00:00"))
            if stamp.utcoffset() != timedelta(0):
                raise ValueError("UTC_REQUIRED")
        except (KeyError, AttributeError, TypeError, ValueError) as exc:
            raise ValueError("NEXT_RECEIPT_UTC_HOLD") from exc
        return stamp
    stamps = [check_receipt(robots, NEXT["B"]["origin"] + "/robots.txt",
                            "text/plain", 65536),
              check_receipt(pages[0], NEXT["B"]["listing"], "text/html", CAP),
              check_receipt(pages[1], NEXT["B"]["detail"], "text/html", CAP)]
    if not (stamps[0] <= stamps[1] <= stamps[2]
            and stamps[2] - stamps[0] <= timedelta(minutes=10)):
        raise ValueError("NEXT_RECEIPT_SOURCE_TIME_SKEW_HOLD")
    if len({r["body_sha256"] for r in [robots] + pages}) != 3:
        raise ValueError("NEXT_RECEIPT_SAME_BODY_FALLBACK_HOLD")
    roles = {"SOURCE_EVENT_TITLE_REVIEW", "SOURCE_VENUE_REVIEW"}
    if {r.get("role") for r in fields if isinstance(r, dict)} != roles:
        raise ValueError("NEXT_RECEIPT_FIELD_ROLES_HOLD")
    for f in fields:
        if (f.get("source_url") != NEXT["B"]["detail"]
                or f.get("event_id") != NEXT["B"]["id"]
                or f.get("body_sha256") != pages[1]["body_sha256"]
                or f.get("observed_at_utc") != pages[1]["observed_at_utc"]
                or f.get("decision") != "REVIEW"
                or f.get("formal_accepted") is not False):
            raise ValueError("NEXT_RECEIPT_FIELD_SOURCE_BINDING_HOLD")
    return {"kind": "P30_B_ZEPP_167511_SEALED_RECEIPT_ONLY_LKG_V1",
            "source_id": NEXT["B"]["source"], "source_event_id": NEXT["B"]["id"],
            "artifact_sha256": expected_zip_sha256, "exact_head": expected_head,
            "source_receipts": [robots] + pages, "field_receipts": fields,
            "native_list": 1, "native_detail": 1, "native_identity_review": 1,
            "receipt_only_identity_lkg": 1, "native_body_replay_lkg": 0,
            "formal_accepted_fields": 0, "golden": 0, "published": 0,
            "decision": "REVIEW_RECEIPT_ONLY_NO_RAW_BODY",
            "release_state": "HARD_HOLD_NO_PUBLICATION"}


def persist_next_native_receipt_lkg(archive, target, repo_root, *,
                                    expected_zip_sha256, expected_head,
                                    expected_previous_sha256=None):
    """Atomic, exclusive-lock CAS for an audited artifact; never write in repo."""
    import os
    import tempfile
    from pathlib import Path
    snapshot = audit_next_native_receipt_archive(
        archive, expected_zip_sha256=expected_zip_sha256,
        expected_head=expected_head)
    target, root = Path(target), Path(repo_root).resolve(strict=True)
    parent = target.parent.resolve(strict=True)
    if (not target.is_absolute() or target.is_symlink()
            or parent == root or root in parent.parents
            or target.name in ("", ".", "..")
            or (expected_previous_sha256 is not None
                and not re.fullmatch(r"[0-9a-f]{64}", expected_previous_sha256))):
        raise ValueError("NEXT_RECEIPT_ISOLATION_CAS_PATH_HOLD")
    canonical = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    lock, fd, tmp = target.with_name(target.name + ".lock"), None, None
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        if target.exists():
            prior_bytes = target.read_bytes()
            if len(prior_bytes) > 32768:
                raise ValueError("NEXT_RECEIPT_PRIOR_BOUND_HOLD")
            prior = json.loads(prior_bytes)
            if (set(prior) != {"kind", "snapshot", "sha256"}
                    or prior["kind"] != "P30_B_SEALED_RECEIPT_ENVELOPE_V1"
                    or prior["sha256"] != hashlib.sha256(json.dumps(
                        prior["snapshot"], sort_keys=True, ensure_ascii=False,
                        separators=(",", ":"), allow_nan=False
                    ).encode("utf-8")).hexdigest()):
                raise ValueError("NEXT_RECEIPT_PRIOR_ENVELOPE_HOLD")
            if prior["sha256"] == digest:
                return {"persisted": False, "idempotent": True,
                        "snapshot_sha256": digest, "receipt_only_identity_lkg": 1,
                        "native_body_replay_lkg": 0}
            if prior["sha256"] != expected_previous_sha256:
                raise ValueError("NEXT_RECEIPT_FULL_ENVELOPE_CAS_HOLD")
        elif expected_previous_sha256 is not None:
            raise ValueError("NEXT_RECEIPT_MISSING_PRIOR_CAS_HOLD")
        envelope = {"kind": "P30_B_SEALED_RECEIPT_ENVELOPE_V1",
                    "snapshot": snapshot, "sha256": digest}
        payload = (json.dumps(envelope, sort_keys=True, ensure_ascii=False,
                              separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        fd_tmp, tmp = tempfile.mkstemp(prefix=".next_receipt.", dir=str(parent))
        with os.fdopen(fd_tmp, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, target)
        tmp = None
        if os.name == "posix":
            dfd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        return {"persisted": True, "idempotent": False,
                "snapshot_sha256": digest, "receipt_only_identity_lkg": 1,
                "native_body_replay_lkg": 0}
    finally:
        if tmp is not None:
            os.unlink(tmp)
        if fd is not None:
            os.close(fd)
            os.unlink(lock)

if __name__ == "__main__":
    for line in ("A", "B"):
        print(json.dumps(run_native_once(line), ensure_ascii=False, sort_keys=True))
