"""Replay-only, bounded source acquisition root-cause repair (NO GET / NO PUBLISH).

A prior native TPAC HTTP200 exceeded the old 512 KiB cap. This module can
consume a *caller-owned* complete response stream without retaining raw HTML.
It never performs HTTP, attests a native fetch, or accepts a formal field.
B prior Songshan native evidence can be independently classified without
reissuing its already-consumed one-shot GET.
"""
from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

TPAC_URL = "https://tpac.org.taipei/program/2088"
TICKET_URL = "https://www.opentix.life/event/2072516129034670080"
TITLE = "C MUSICAL 音樂劇《小王子》"
SONGSHAN_UUID = "3b2101fd-cbb3-48ec-b23c-496880df5626"
SONGSHAN_LIST = "https://www.songshanculturalpark.org/exhibition"
SONGSHAN_DETAIL = SONGSHAN_LIST + "/activity/" + SONGSHAN_UUID
MAX_BODY = 4 * 1024 * 1024


class EventLocalHTML(HTMLParser):
    """Bounded MAIN-local title, direct event href, and room signals."""
    VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img",
                      "input", "link", "meta", "param", "source", "track", "wbr"))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.main_depth = None
        self.node_count = 0
        self.capture = []
        self.headings = []
        self.anchors = []
        self.room_text = []
        self.visible_text_size = 0
        self.section_stack = []
        self.section_text = {}
        self.section_tags = {}
        self.next_section_id = 0

    def handle_starttag(self, tag, attrs):
        self.node_count += 1
        if self.node_count > 120000 or len(self.stack) > 100:
            raise ValueError("TPAC_STREAM_DOM_BOUNDS_HOLD")
        attrs = dict(attrs)
        if tag not in self.VOID:
            self.stack.append(tag)
        if tag == "main" and self.main_depth is None:
            self.main_depth = len(self.stack)
        if self.main_depth is None or tag in self.VOID:
            return
        if tag in ("section", "article"):
            self.next_section_id += 1
            self.section_stack.append((len(self.stack), self.next_section_id))
            self.section_text[self.next_section_id] = ""
            self.section_tags[self.next_section_id] = tag
        kind = "heading" if tag in ("h1", "h2", "h3") else (
            "anchor" if tag == "a" else None)
        if kind:
            self.capture.append([len(self.stack), kind, attrs, "",
                                 tuple(section_id for _, section_id in self.section_stack)])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_data(self, value):
        if self.main_depth is None or any(
                tag in ("script", "style", "noscript", "template")
                for tag in self.stack):
            return
        self.visible_text_size += len(value)
        if self.visible_text_size > 400000:
            raise ValueError("TPAC_STREAM_VISIBLE_TEXT_BOUNDS_HOLD")
        self.room_text.append(value)
        for _, section_id in self.section_stack:
            self.section_text[section_id] += value
            if len(self.section_text[section_id]) > 100000:
                raise ValueError("TPAC_STREAM_SECTION_TEXT_BOUNDS_HOLD")
        for item in self.capture:
            item[3] += value
            if len(item[3]) > 4000:
                raise ValueError("TPAC_STREAM_EVENT_NODE_TEXT_BOUNDS_HOLD")

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if tag not in self.stack:
            raise ValueError("TPAC_STREAM_UNBALANCED_DOM_HOLD")
        while self.stack:
            depth = len(self.stack)
            current = self.stack.pop()
            for item in list(self.capture):
                if item[0] == depth:
                    record = (item[2], " ".join(item[3].split()), item[4])
                    (self.headings if item[1] == "heading"
                     else self.anchors).append(record)
                    self.capture.remove(item)
            if self.section_stack and self.section_stack[-1][0] == depth:
                self.section_stack.pop()
            if self.main_depth == depth and current == "main":
                self.main_depth = None
            if current == tag:
                break


def inspect_tpac_complete_stream(stream, *, status, content_type, final_url,
                                 observed_at_utc, max_bytes=MAX_BODY):
    """Read one existing response in chunks, hash only COMPLETE bytes.

    No network, no disk writes, no raw-page output. A truncated body is
    explicitly marked prefix-only, never falsely attested as a full hash.
    """
    report = {
        "kind": "P30_TPAC_STREAMED_SOURCE_DIAGNOSIS_V1",
        "source_url": TPAC_URL, "ticket_event_url": TICKET_URL,
        "transport": "CALLER_SUPPLIED_STREAM_NOT_NATIVE_ATTESTED",
        "native_get_this_call": 0, "native_same_id_lkg": 0,
        "decision": "HOLD", "first_failure": "SOURCE_NOT_VALIDATED",
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION",
        "raw_html_saved": False,
    }
    try:
        if status != 200 or final_url != TPAC_URL:
            raise ValueError("TPAC_EXACT_URL_OR_HTTP_HOLD")
        if not isinstance(content_type, str) or (
                content_type.split(";", 1)[0].strip().lower() != "text/html"):
            raise ValueError("TPAC_HTML_CONTENT_TYPE_HOLD")
        charset = re.search(r"(?:^|;)\s*charset\s*=\s*([^;]+)", content_type, re.I)
        if charset and charset.group(1).strip().strip('"').lower() != "utf-8":
            raise ValueError("TPAC_UTF8_CHARSET_HOLD")
        stamp = datetime.fromisoformat(observed_at_utc.replace("Z", "+00:00"))
        if stamp.utcoffset() is None or stamp > datetime.now(timezone.utc):
            raise ValueError("TPAC_OBSERVATION_TIME_HOLD")
        if type(max_bytes) is not int or not 524289 <= max_bytes <= MAX_BODY:
            raise ValueError("TPAC_STREAM_BOUND_POLICY_HOLD")
        if not callable(getattr(stream, "read", None)):
            raise ValueError("TPAC_STREAM_REQUIRED_HOLD")
        parser, decoder, digest = EventLocalHTML(), codecs.getincrementaldecoder("utf-8")("strict"), hashlib.sha256()
        size = 0
        while True:
            chunk = stream.read(min(65536, max_bytes + 1 - size))
            if not isinstance(chunk, bytes):
                raise ValueError("TPAC_STREAM_NON_BYTES_HOLD")
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
            if size > max_bytes:
                report.update(bytes_read_capped=size, prefix_sha256=digest.hexdigest(),
                              body_truncated=True)
                raise ValueError("TPAC_STREAM_COMPLETE_BODY_EXCEEDS_POLICY_HOLD")
            parser.feed(decoder.decode(chunk))
        parser.feed(decoder.decode(b"", final=True))
        parser.close()
        if size == 0:
            raise ValueError("TPAC_EMPTY_COMPLETE_BODY_HOLD")
        report.update(body_bytes=size, body_sha256=digest.hexdigest(),
                      body_truncated=False, observed_at_utc=stamp.isoformat())
        # Source DOM can place a unique title and direct ticket edge in sibling
        # sections of ONE event article. Compare full ancestor paths instead of
        # requiring identical innermost section IDs. Never fall back to MAIN:
        # distinct event articles or sibling root sections remain HOLD.
        headings = [path for _, text, path in parser.headings if text == TITLE]
        anchors = [path for attrs, _, path in parser.anchors
                   if urljoin(TPAC_URL, attrs.get("href", "")) == TICKET_URL]
        shared_scope = None
        article_identity = False
        if len(headings) == len(anchors) == 1:
            title_articles = tuple(x for x in headings[0]
                                   if parser.section_tags[x] == "article")
            ticket_articles = tuple(x for x in anchors[0]
                                    if parser.section_tags[x] == "article")
            article_identity = title_articles == ticket_articles
            if article_identity:
                shared_scope = next((x for x in reversed(headings[0])
                                     if x in anchors[0]), None)
        shared_section = shared_scope is not None
        room_in_shared_section = bool(shared_section and "藍盒子" in
                                      " ".join(parser.section_text[shared_scope].split()))
        report["event_local_checks"] = {
            "exact_title_heading_count": len(headings),
            "direct_ticket_href_count": len(anchors),
            "same_section_identity": bool(shared_section),
            "room_in_same_section": room_in_shared_section,
            "article_ancestor_parity": article_identity,
            "shared_event_ancestor_kind": parser.section_tags.get(shared_scope),
            "cross_article_fallback_used": False,
            "event_id": "2072516129034670080",
        }
        if not shared_section or not room_in_shared_section:
            raise ValueError("TPAC_EVENT_LOCAL_TITLE_LINK_ROOM_HOLD")
        report.update(decision="REVIEW_DIRECT_EDGE_ONLY",
                      first_failure="INDEPENDENT_FIELD_AUTHORITY_AND_TICKET_SESSION_HOLD")
    except (ValueError, TypeError, UnicodeError, AttributeError, OSError) as exc:
        if report["first_failure"] == "SOURCE_NOT_VALIDATED":
            report["first_failure"] = str(exc)[:160]
    return report


def audit_songshan_prior_native_receipt(report):
    """Check prior two-URL native receipt provenance; no HTML identity upgrade."""
    out = {
        "kind": "P30_SONGSHAN_PRIOR_NATIVE_RECEIPT_REPLAY_V1",
        "target_uuid": SONGSHAN_UUID, "native_get_this_call": 0,
        "replayed_prior_http200": 0, "native_same_uuid_lkg_new": 0,
        "decision": "HOLD", "first_failure": "PRIOR_EVIDENCE_INVALID",
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "release_state": "HARD_HOLD_NO_PUBLICATION",
    }
    try:
        if not isinstance(report, dict) or report.get("target_uuid") != SONGSHAN_UUID:
            raise ValueError("SONGSHAN_EXACT_UUID_EVIDENCE_HOLD")
        if report.get("same_uuid_review_lkg") != 0 or report.get("persisted") is not False:
            raise ValueError("SONGSHAN_NATIVE_LKG_NOT_VERIFIED_HOLD")
        if report.get("native_get_200_count") != 2:
            raise ValueError("SONGSHAN_PRIOR_HTTP_COUNT_HOLD")
        receipts = report.get("source_receipts")
        if not isinstance(receipts, list) or len(receipts) != 2:
            raise ValueError("SONGSHAN_PRIOR_RECEIPT_COUNT_HOLD")
        sealed = ((SONGSHAN_LIST, 34242,
                   "de3df20bcd78e264c7f0eff8bafedbeb39aa580d7892e738bb2eb792c68e33cb"),
                  (SONGSHAN_DETAIL, 26506,
                   "1226b2f61dd328c08a2ff456e4f36dcc20dd23ce9d18219e377bafa4d404e02d"))
        for receipt, (expected, size, digest) in zip(receipts, sealed):
            if (receipt.get("url") != expected or receipt.get("http_status") != 200
                or receipt.get("bytes") != size
                or receipt.get("body_sha256") != digest
                or receipt.get("transport") != "BUILTIN_NATIVE_GET"):
                raise ValueError("SONGSHAN_PRIOR_RECEIPT_URL_SHA_BODY_HOLD")
        failure = report.get("reason", "")
        if not isinstance(failure, str) or not failure.startswith(
                "SONGSHAN_DETAIL_EXACT_HEADING_HOLD"):
            raise ValueError("SONGSHAN_PRIOR_FIRST_FAILURE_CHANGED_HOLD")
        out.update(replayed_prior_http200=2,
                   first_failure=failure[:160],
                   decision="PRIOR_NATIVE_HTTP_CONFIRMED_IDENTITY_STILL_HOLD")
    except (TypeError, ValueError, AttributeError) as exc:
        out["first_failure"] = str(exc)[:160]
    return out



def acquire_tpac_native_once():
    """One explicitly gated public TPAC DETAIL GET; never retry/redirect/publish.

    A new, separately testable 4 MiB complete-stream hypothesis after the
    historic 524289-byte capped-prefix HOLD. CI calls this only for a unique
    exact-head one-shot marker and first run attempt. No OPENTIX/checkout GET.
    """
    import socket
    import ssl
    import urllib.error
    import urllib.request

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    out = {
        "kind": "P30_TPAC_NATIVE_COMPLETE_STREAM_ONESHOT_V1",
        "source_url": TPAC_URL,
        "ticket_event_url": TICKET_URL,
        "native_get_this_call": 1,
        "native_detail_get_attempted": 1,
        "native_list_get_this_call": 0,
        "native_http200_this_call": 0,
        "native_same_id_lkg": 0,
        "transport": "BUILTIN_NATIVE_GET_NO_REDIRECT_NO_RETRY",
        "timeout_seconds": 8,
        "max_body_bytes": MAX_BODY,
        "decision": "HOLD",
        "first_failure": "NATIVE_SOURCE_UNAVAILABLE",
        "formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
        "raw_html_saved": False,
    }
    request = urllib.request.Request(
        TPAC_URL, method="GET",
        headers={"User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
                 "Accept": "text/html,application/xhtml+xml",
                 "Accept-Encoding": "identity"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=8) as response:
            stamp = datetime.now(timezone.utc).isoformat()
            out["observed_at_utc"] = stamp
            out["native_http_status"] = response.status
            out["native_http200_this_call"] = int(response.status == 200)
            result = inspect_tpac_complete_stream(
                response, status=response.status,
                content_type=response.headers.get("Content-Type", ""),
                final_url=response.geturl(), observed_at_utc=stamp)
            for key in ("body_bytes", "body_sha256", "body_truncated",
                        "bytes_read_capped", "prefix_sha256", "event_local_checks"):
                if key in result:
                    out[key] = result[key]
            out["decision"] = result["decision"]
            out["first_failure"] = result["first_failure"]
    except urllib.error.HTTPError as exc:
        out["native_http_status"] = exc.code
        out["first_failure"] = ("TPAC_REDIRECT_BLOCKED_HOLD" if 300 <= exc.code < 400
                                else "TPAC_NATIVE_HTTP_ERROR_HOLD")
    except urllib.error.URLError as exc:
        out["network_error_type"] = type(exc.reason).__name__
        out["first_failure"] = ("TPAC_DNS_EGRESS_HOLD" if isinstance(exc.reason, socket.gaierror)
                                else "TPAC_NATIVE_NETWORK_HOLD")
    except (OSError, TimeoutError, ssl.SSLError, UnicodeError, ValueError) as exc:
        out["network_error_type"] = type(exc).__name__
        out["first_failure"] = "TPAC_NATIVE_STREAM_TRANSPORT_OR_PARSE_HOLD"
    return out



# Reuse the two existing A/B canonical adapters as one repeatable, non-network
# CLI. This is an executable integration, NOT a new source/native observation.
# Original caller observation timestamps and SHA256 must bind both complete
# source bodies. Invalid or stale source cannot overwrite the sealed LKG.
def read_preacquired_ab_manifest(manifest_path, repo_root, line, now_utc=None):
    from scripts.p30_l7_field_golden_readiness import (
        OPENTIX_ROTATION_LIST, OPENTIX_ROTATION_DETAIL, SONGSHAN_PUBLIC_LIST)
    root = Path(repo_root).resolve(strict=True)
    def source_file(value):
        path = Path(value)
        if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("REPLAY_INPUT_ABSOLUTE_NON_SYMLINK_REQUIRED")
        resolved = path.resolve(strict=True)
        if resolved == root or resolved.is_relative_to(root):
            raise ValueError("REPLAY_RAW_SOURCE_INSIDE_REPO_HOLD")
        if not resolved.is_file() or not 0 < resolved.stat().st_size <= 524288:
            raise ValueError("REPLAY_INPUT_FILE_SIZE_OR_TYPE_HOLD")
        return resolved
    manifest = json.loads(source_file(manifest_path).read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict)
            or set(manifest) != {"kind", "transport", "sources"}
            or manifest["kind"] != "P30_PREACQUIRED_OFFICIAL_HTML_V1"
            or manifest["transport"] != "CALLER_SUPPLIED_NOT_NATIVE_ATTESTED"
            or not isinstance(manifest["sources"], list)
            or len(manifest["sources"]) != 2):
        raise ValueError("REPLAY_MANIFEST_SHAPE_OR_TRANSPORT_HOLD")
    urls = ((OPENTIX_ROTATION_LIST, OPENTIX_ROTATION_DETAIL) if line == "A"
            else (SONGSHAN_PUBLIC_LIST, SONGSHAN_DETAIL))
    now = now_utc or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("REPLAY_CLOCK_HOLD")
    result, stamps, receipts = {}, [], []
    for item, url in zip(manifest["sources"], urls):
        if (not isinstance(item, dict)
                or set(item) != {"url", "path", "sha256", "observed_at_utc"}
                or item["url"] != url or not isinstance(item["sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None):
            raise ValueError("REPLAY_EXACT_URL_OR_SHA_MANIFEST_HOLD")
        stamp_raw = item["observed_at_utc"]
        if not isinstance(stamp_raw, str):
            raise ValueError("REPLAY_OBSERVATION_TIME_HOLD")
        stamp = datetime.fromisoformat(stamp_raw.replace("Z", "+00:00"))
        if stamp.utcoffset() is None or not 0 <= (now - stamp).total_seconds() <= 86400:
            raise ValueError("REPLAY_STALE_FUTURE_OR_NAIVE_TIME_HOLD")
        raw = source_file(item["path"]).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != item["sha256"]:
            raise ValueError("REPLAY_SOURCE_BYTES_SHA256_MISMATCH_HOLD")
        stamps.append(stamp)
        receipts.append({"url": url, "body_sha256": digest,
                         "body_bytes": len(raw), "observed_at_utc": stamp.isoformat(),
                         "transport": "CALLER_SUPPLIED_NOT_NATIVE_ATTESTED"})
        result[url] = (200, "text/html; charset=utf-8", raw, url, stamp.isoformat())
    if (max(stamps) - min(stamps)).total_seconds() > 600:
        raise ValueError("REPLAY_LIST_DETAIL_OBSERVATION_SKEW_HOLD")
    return result, receipts, max(stamps)


def replay_preacquired_ab_to_review_lkg(line, manifest, destination, repo_root,
                                        now_utc=None):
    """Source Adapter -> same ID DETAIL -> role -> provenance -> atomic LKG."""
    from scripts.p30_l7_field_golden_readiness import (
        run_opentix_existing_id_review_lkg, run_songshan_uuid_review_lkg,
        load_isolated_review_lkg)
    out = {"kind": "P30_A_B_OFFLINE_SOURCE_REPLAY_V1", "line": line,
           "native_get_this_call": 0, "native_get_attested": False,
           "same_id_review_lkg": 0, "formal_accepted_fields": 0,
           "golden_accepted_events": 0, "published_events": 0,
           "release_state": "HARD_HOLD_NO_PUBLICATION",
           "decision": "HOLD", "first_failure": "REPLAY_NOT_VALIDATED",
           "source_receipts": []}
    try:
        if line not in ("A", "B"):
            raise ValueError("REPLAY_LINE_HOLD")
        bodies, receipts, stamp = read_preacquired_ab_manifest(
            manifest, repo_root, line, now_utc=now_utc)
        out["source_receipts"] = receipts
        if line == "A":
            result = run_opentix_existing_id_review_lkg(
                destination, repo_root, source_bodies=bodies,
                now_utc=now_utc or datetime.now(timezone.utc))
            success = result.get("same_id_review_lkg") == 1
        else:
            result = run_songshan_uuid_review_lkg(
                destination, repo_root,
                fetcher=lambda url: bodies[url][:4], now_utc=stamp,
                event_uuid=SONGSHAN_UUID,
                event_title="STAR ON THE MOVE 2026 臺北採購媒合與展售會",
                event_type="展覽")
            success = result.get("same_uuid_review_lkg") == 1 and result.get("persisted") is True
        out["first_failure"] = result.get("first_failure", result.get("reason", "UNKNOWN"))
        if not success:
            return out
        snapshot = load_isolated_review_lkg(destination, repo_root)
        if snapshot is None or snapshot["rows"][0]["_candidate"]["platform_id"] != (
                "05" if line == "A" else "14"):
            raise ValueError("REPLAY_LKG_IDENTITY_READBACK_HOLD")
        if snapshot["rows"][0]["scraped_at"] != stamp.isoformat():
            raise ValueError("REPLAY_LKG_ORIGINAL_TIMESTAMP_HOLD")
        out.update(decision="REVIEW_ONLY_NONPUBLISHING",
                   first_failure="INDEPENDENT_NATIVE_FIELD_AUTHORITY_HOLD",
                   same_id_review_lkg=1,
                   last_known_good_sha256=snapshot["last_known_good_sha256"],
                   lkg_envelope_readback=True)
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            json.JSONDecodeError, AttributeError) as exc:
        out["first_failure"] = type(exc).__name__ + ":" + str(exc)[:140]
    return out



# B source rotation: one new canonical venue in New Taipei, not a 20th
# production platform. This bounded native receipt never infers a ticket
# session, never visits the linked KKTIX checkout, and never writes LKG.
# Official schedule is the LIST authority; venue HOME is not a LIST receipt.
# Indexed official schedule -> exact rid=166457; native bytes still HOLD.
ZEPP_LIST = "https://www.zepp.co.jp/hall/newtaipei/schedule/"
ZEPP_DETAIL = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=166457"
ZEPP_TITLE = "Jony J 2026「本命」TOUR IN TAIPEI"
ZEPP_SOURCE_KEY = "venue:zepp-newtaipei"
ZEPP_MAX_BYTES = 1048576


class ZeppLocalHTML(HTMLParser):
    """Bounded same-anchor title and DETAIL heading, never cross-card joins."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.headings = []
        self._anchor = None
        self._heading = None
        self._nodes = 0
        # DETAIL heading must belong to the exact rid page's MAIN region;
        # a matching global navigation/footer heading is not event identity.
        self._main_level = 0

    def handle_starttag(self, tag, attrs):
        self._nodes += 1
        if self._nodes > 20000:
            raise ValueError("ZEPP_DOM_NODE_LIMIT_HOLD")
        attributes = dict(attrs)
        if tag == "main":
            self._main_level += 1
        if tag == "a":
            if self._anchor is not None:
                raise ValueError("ZEPP_NESTED_ANCHOR_HOLD")
            self._anchor = [attributes.get("href", ""), []]
        if tag in ("h1", "h2", "h3"):
            if self._heading is not None:
                raise ValueError("ZEPP_NESTED_HEADING_HOLD")
            self._heading = [tag, [], self._main_level > 0]

    def handle_data(self, data):
        for current in (self._anchor, self._heading):
            if current is not None:
                current[1].append(data)
                if sum(map(len, current[1])) > 4000:
                    raise ValueError("ZEPP_LOCAL_TEXT_LIMIT_HOLD")

    def handle_endtag(self, tag):
        if tag == "a" and self._anchor is not None:
            self.anchors.append((self._anchor[0], " ".join(
                "".join(self._anchor[1]).split())))
            self._anchor = None
        if tag in ("h1", "h2", "h3") and self._heading is not None:
            if self._heading[0] != tag:
                raise ValueError("ZEPP_HEADING_STRUCTURE_HOLD")
            if self._heading[2]:
                self.headings.append(" ".join("".join(self._heading[1]).split()))
            self._heading = None
        if tag == "main":
            if self._main_level == 0:
                raise ValueError("ZEPP_UNBALANCED_MAIN_HOLD")
            self._main_level -= 1


def inspect_zepp_same_id_pages(list_body, detail_body, *,
                               detail_url=ZEPP_DETAIL, expected_title=ZEPP_TITLE):
    """Reusable official venue same-rid LIST->DETAIL parser, REVIEW only.

    No cross-event title joins, checkout, Session or accepted fields. Caller
    must separately attest native transport and original body SHA/time.
    """
    from urllib.parse import parse_qsl
    if (not isinstance(detail_url, str) or
            not isinstance(expected_title, str) or
            not 4 <= len(expected_title) <= 180 or
            expected_title != expected_title.strip()):
        raise ValueError("ZEPP_TARGET_IDENTITY_INPUT_HOLD")
    parts = urlsplit(detail_url)
    if (parts.scheme != "https" or parts.netloc != "www.zepp.co.jp" or
            parts.path != "/hall/newtaipei/schedule/single/" or
            parts.fragment or parts.username or parts.password):
        raise ValueError("ZEPP_TARGET_EXACT_OFFICIAL_URL_HOLD")
    params = parse_qsl(parts.query, keep_blank_values=True)
    if (len(params) != 1 or params[0][0] != "rid" or
            re.fullmatch(r"[1-9][0-9]{0,8}", params[0][1]) is None):
        raise ValueError("ZEPP_TARGET_RID_QUERY_HOLD")
    if any(not isinstance(raw, bytes) or not 0 < len(raw) <= ZEPP_MAX_BYTES
           for raw in (list_body, detail_body)):
        raise ValueError("ZEPP_BODY_BOUND_HOLD")
    listing, detail = ZeppLocalHTML(), ZeppLocalHTML()
    listing.feed(list_body.decode("utf-8", errors="strict"))
    detail.feed(detail_body.decode("utf-8", errors="strict"))
    exact_edges = [(href, title) for href, title in listing.anchors
                   if urljoin(ZEPP_LIST, href) == detail_url]
    if (len(exact_edges) != 1 or
            exact_edges[0][1].count(expected_title) != 1):
        raise ValueError("ZEPP_LIST_EXACT_RID_TITLE_EDGE_HOLD")
    if detail.headings.count(expected_title) != 1:
        raise ValueError("ZEPP_DETAIL_EVENT_LOCAL_HEADING_HOLD")
    return {"exact_rid": params[0][1], "list_exact_edge_count": 1,
            "detail_exact_heading_count": 1, "title": expected_title,
            "source_key": ZEPP_SOURCE_KEY,
            "date_role": "UNVERIFIED_NOT_SESSION",
            "start_role": "UNVERIFIED_NOT_SESSION",
            "formal_accepted_fields": 0}


def probe_zepp_newtaipei_native_once():
    """At most two official public GETs, 8s each, no redirect/retry/login."""
    import socket
    import ssl
    import urllib.error
    import urllib.request
    import urllib.robotparser

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    result = {
        "kind": "P30_B_ZEPP_NEWTIPEI_NATIVE_SAME_ID_ONESHOT_V1",
        "line": "B", "source_key": ZEPP_SOURCE_KEY,
        "source_event_id": "166457",
        "policy_get_attempted": 0, "policy_decision": "UNKNOWN",
        "native_get_attempted": 0, "native_http200": 0,
        "native_list_get_attempted": 0, "native_detail_get_attempted": 0,
        "native_same_id_review": 0, "same_id_review_lkg": 0,
        "source_receipts": [], "decision": "HOLD",
        "first_failure": "ZEPP_SOURCE_NOT_ACQUIRED",
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "raw_html_saved": False,
        "release_state": "HARD_HOLD_NO_PUBLICATION"}
    bodies = []
    opener = urllib.request.build_opener(NoRedirect)
    # Fail closed when site policy cannot be checked. 404 means no robots
    # restrictions per REP; all other policy/network failures stop the probe.
    # This single robots request is counted separately from LIST/DETAIL.
    robots_url = "https://www.zepp.co.jp/robots.txt"
    result["policy_get_attempted"] = 1
    try:
        request = urllib.request.Request(
            robots_url, method="GET", headers={
                "User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
                "Accept": "text/plain", "Accept-Encoding": "identity"})
        try:
            with opener.open(request, timeout=8) as response:
                result["policy_http_status"] = response.status
                if response.status != 200 or response.geturl() != robots_url:
                    raise ValueError("ZEPP_ROBOTS_STATUS_OR_REDIRECT_HOLD")
                raw_policy = response.read(65537)
                if len(raw_policy) > 65536:
                    raise ValueError("ZEPP_ROBOTS_SIZE_HOLD")
                # A policy verdict without the policy bytes' SHA cannot be
                # independently audited; no raw robots file is persisted.
                result["policy_observed_at_utc"] = datetime.now(timezone.utc).isoformat()
                result["policy_body_bytes"] = len(raw_policy)
                result["policy_body_sha256"] = hashlib.sha256(raw_policy).hexdigest()
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(raw_policy.decode("utf-8", errors="strict").splitlines())
                if not all(parser.can_fetch("EventRadarSourceAudit", url)
                           for url in (ZEPP_LIST, ZEPP_DETAIL)):
                    raise ValueError("ZEPP_ROBOTS_DISALLOW_HOLD")
                result["policy_decision"] = "ALLOW_ROBOTS_200"
        except urllib.error.HTTPError as exc:
            result["policy_http_status"] = exc.code
            if exc.code != 404:
                raise ValueError("ZEPP_ROBOTS_HTTP_HOLD_" + str(exc.code))
            result["policy_decision"] = "ALLOW_ROBOTS_404"
    except (ValueError, UnicodeError, OSError, TimeoutError,
            urllib.error.URLError) as exc:
        result["first_failure"] = "ZEPP_SITE_POLICY_HOLD:" + type(exc).__name__ + ":" + str(exc)[:90]
        return result
    for index, url in enumerate((ZEPP_LIST, ZEPP_DETAIL)):
        result["native_get_attempted"] += 1
        result["native_list_get_attempted" if index == 0
               else "native_detail_get_attempted"] += 1
        stamp = datetime.now(timezone.utc).isoformat()
        receipt = {"url": url, "observed_at_utc": stamp,
                   "http_status": None, "body_sha256": None,
                   "transport": "BUILTIN_NATIVE_GET_NO_REDIRECT_NO_RETRY"}
        try:
            request = urllib.request.Request(
                url, method="GET", headers={
                    "User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Encoding": "identity"})
            with opener.open(request, timeout=8) as response:
                receipt["http_status"] = response.status
                if response.status == 200:
                    result["native_http200"] += 1
                if response.status != 200 or response.geturl() != url:
                    raise ValueError("ZEPP_STATUS_OR_REDIRECT_HOLD")
                mime = response.headers.get("Content-Type", "")
                if mime.split(";", 1)[0].strip().lower() != "text/html":
                    raise ValueError("ZEPP_CONTENT_TYPE_HOLD")
                charset = [v.split("=", 1)[1].strip().strip('"').lower()
                           for v in mime.split(";")[1:]
                           if v.strip().lower().startswith("charset=")]
                if charset and charset != ["utf-8"]:
                    raise ValueError("ZEPP_CHARSET_HOLD")
                body = response.read(ZEPP_MAX_BYTES + 1)
                receipt["body_bytes_read"] = len(body)
                if not 0 < len(body) <= ZEPP_MAX_BYTES:
                    raise ValueError("ZEPP_EMPTY_OR_TRUNCATED_BODY_HOLD")
                receipt["body_sha256"] = hashlib.sha256(body).hexdigest()
                bodies.append(body)
        except urllib.error.HTTPError as exc:
            receipt["http_status"] = exc.code
            result["first_failure"] = ("ZEPP_REDIRECT_BLOCKED_HOLD"
                                       if 300 <= exc.code < 400
                                       else "ZEPP_HTTP_ERROR_HOLD")
        except urllib.error.URLError as exc:
            result["network_error_type"] = type(exc.reason).__name__
            result["first_failure"] = ("ZEPP_DNS_EGRESS_HOLD"
                                       if isinstance(exc.reason, socket.gaierror)
                                       else "ZEPP_NETWORK_HOLD")
        except (ValueError, UnicodeError, OSError, TimeoutError,
                ssl.SSLError) as exc:
            result["first_failure"] = type(exc).__name__ + ":" + str(exc)[:100]
        result["source_receipts"].append(receipt)
        if receipt["body_sha256"] is None:
            break
    if len(bodies) == 2:
        try:
            result["identity_checks"] = inspect_zepp_same_id_pages(*bodies)
            result["native_same_id_review"] = 1
            result["decision"] = "REVIEW_NATIVE_SAME_ID_ONLY"
            result["first_failure"] = "INDEPENDENT_FIELD_AUTHORITY_AND_LKG_HOLD"
        except (ValueError, UnicodeError) as exc:
            result["first_failure"] = type(exc).__name__ + ":" + str(exc)[:100]
    return result



# A new canonical #05 OPENTIX public DETAIL (distinct from prior consumed
# TPAC/OPENTIX ID). No checkout, Session, LIST edge, or formal publication.
OPENTIX_FRESH_DETAIL = "https://www.opentix.life/event/2054505084713033728"
OPENTIX_FRESH_TITLE = "《神隱少女》舞台劇"
OPENTIX_FRESH_MAX_BYTES = 4 * 1024 * 1024


class OpentixDetailLocalHTML(HTMLParser):
    """Exact MAIN-local heading only, never global SEO/header/footer."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main_depth = 0
        self.heading = None
        self.headings = []
        self.nodes = 0

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > 120000:
            raise ValueError("OPENTIX_FRESH_DOM_NODE_BOUND_HOLD")
        if tag == "main":
            self.main_depth += 1
        if tag in ("h1", "h2", "h3") and self.main_depth:
            if self.heading is not None:
                raise ValueError("OPENTIX_FRESH_NESTED_HEADING_HOLD")
            self.heading = [tag, ""]

    def handle_data(self, value):
        if self.heading is not None:
            self.heading[1] += value
            if len(self.heading[1]) > 1000:
                raise ValueError("OPENTIX_FRESH_HEADING_BOUND_HOLD")

    def handle_endtag(self, tag):
        if self.heading is not None and tag == self.heading[0]:
            self.headings.append(" ".join(self.heading[1].split()))
            self.heading = None
        if tag == "main" and self.main_depth:
            self.main_depth -= 1


def inspect_opentix_fresh_detail_body(raw):
    """Offline body parser; no claim of native provenance."""
    if not isinstance(raw, bytes) or not 0 < len(raw) <= OPENTIX_FRESH_MAX_BYTES:
        raise ValueError("OPENTIX_FRESH_BODY_BOUND_HOLD")
    parser = OpentixDetailLocalHTML()
    parser.feed(raw.decode("utf-8", errors="strict"))
    parser.close()
    count = parser.headings.count(OPENTIX_FRESH_TITLE)
    return {"exact_main_heading_count": count,
            "event_local_title_review": count == 1,
            "source_event_id": "2054505084713033728",
            "list_same_id_edge_attested": False,
            "formal_accepted_fields": 0}


def probe_opentix_fresh_detail_native_once():
    """Robots-checked, one GET, no redirect/retry/raw HTML persistence."""
    import socket
    import urllib.error
    import urllib.request
    import urllib.robotparser

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    out = {
        "kind": "P30_A_OPENTIX_DISTINCT_DETAIL_NATIVE_ONESHOT_V1",
        "line": "A", "platform_id": "05",
        "source_event_id": "2054505084713033728",
        "source_url": OPENTIX_FRESH_DETAIL,
        "policy_get_attempted": 1, "policy_decision": "UNKNOWN",
        "native_get_attempted": 0, "native_http200": 0,
        "native_list_get_attempted": 0, "native_detail_get_attempted": 0,
        "native_same_id_review_lkg": 0, "formal_accepted_fields": 0,
        "golden_accepted_events": 0, "published_events": 0,
        "raw_html_saved": False, "decision": "HOLD",
        "first_failure": "OPENTIX_NEW_SOURCE_NOT_ACQUIRED",
        "release_state": "HARD_HOLD_NO_PUBLICATION"}
    opener = urllib.request.build_opener(NoRedirect)
    robots_url = "https://www.opentix.life/robots.txt"
    try:
        request = urllib.request.Request(robots_url, method="GET",
            headers={"User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
                     "Accept": "text/plain", "Accept-Encoding": "identity"})
        try:
            with opener.open(request, timeout=8) as response:
                out["policy_http_status"] = response.status
                if response.status != 200 or response.geturl() != robots_url:
                    raise ValueError("OPENTIX_ROBOTS_STATUS_REDIRECT_HOLD")
                policy = response.read(65537)
                if len(policy) > 65536:
                    raise ValueError("OPENTIX_ROBOTS_SIZE_HOLD")
                out["policy_observed_at_utc"] = datetime.now(timezone.utc).isoformat()
                out["policy_body_sha256"] = hashlib.sha256(policy).hexdigest()
                out["policy_body_bytes"] = len(policy)
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(policy.decode("utf-8", errors="strict").splitlines())
                if not parser.can_fetch("EventRadarSourceAudit", OPENTIX_FRESH_DETAIL):
                    raise ValueError("OPENTIX_ROBOTS_DISALLOW_HOLD")
                out["policy_decision"] = "ALLOW_ROBOTS_200"
        except urllib.error.HTTPError as exc:
            out["policy_http_status"] = exc.code
            if exc.code != 404:
                raise ValueError("OPENTIX_ROBOTS_HTTP_HOLD_" + str(exc.code))
            out["policy_decision"] = "ALLOW_ROBOTS_404"
    except (ValueError, UnicodeError, OSError, TimeoutError,
            urllib.error.URLError) as exc:
        out["first_failure"] = "OPENTIX_SITE_POLICY_HOLD:" + type(exc).__name__ + ":" + str(exc)[:100]
        return out

    out["native_get_attempted"] = 1
    out["native_detail_get_attempted"] = 1
    out["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
    try:
        request = urllib.request.Request(OPENTIX_FRESH_DETAIL, method="GET",
            headers={"User-Agent": "EventRadarSourceAudit/1.0 (public read-only)",
                     "Accept": "text/html,application/xhtml+xml",
                     "Accept-Encoding": "identity"})
        with opener.open(request, timeout=8) as response:
            out["http_status"] = response.status
            out["native_http200"] = int(response.status == 200)
            if response.status != 200 or response.geturl() != OPENTIX_FRESH_DETAIL:
                raise ValueError("OPENTIX_DETAIL_STATUS_REDIRECT_HOLD")
            mime = response.headers.get("Content-Type", "")
            if mime.split(";", 1)[0].strip().lower() != "text/html":
                raise ValueError("OPENTIX_DETAIL_MIME_HOLD")
            charsets = [p.split("=", 1)[1].strip().strip('"').lower()
                        for p in mime.split(";")[1:]
                        if p.strip().lower().startswith("charset=")]
            if charsets and charsets != ["utf-8"]:
                raise ValueError("OPENTIX_DETAIL_CHARSET_HOLD")
            raw = response.read(OPENTIX_FRESH_MAX_BYTES + 1)
            out["body_bytes_read"] = len(raw)
            if not 0 < len(raw) <= OPENTIX_FRESH_MAX_BYTES:
                raise ValueError("OPENTIX_DETAIL_TRUNCATED_OR_EMPTY_HOLD")
            out["body_sha256"] = hashlib.sha256(raw).hexdigest()
            out["detail_checks"] = inspect_opentix_fresh_detail_body(raw)
            if not out["detail_checks"]["event_local_title_review"]:
                raise ValueError("OPENTIX_DETAIL_EXACT_MAIN_TITLE_HOLD")
            out["decision"] = "REVIEW_NATIVE_DETAIL_ONLY"
            out["first_failure"] = "LIST_SAME_ID_AND_INDEPENDENT_FIELD_AUTHORITY_HOLD"
    except urllib.error.HTTPError as exc:
        out["http_status"] = exc.code
        out["first_failure"] = ("OPENTIX_DETAIL_REDIRECT_HOLD" if 300 <= exc.code < 400
                                else "OPENTIX_DETAIL_HTTP_ERROR_HOLD")
    except urllib.error.URLError as exc:
        out["network_error_type"] = type(exc.reason).__name__
        out["first_failure"] = ("OPENTIX_DETAIL_DNS_EGRESS_HOLD"
                                if isinstance(exc.reason, socket.gaierror)
                                else "OPENTIX_DETAIL_NETWORK_HOLD")
    except (ValueError, UnicodeError, OSError, TimeoutError) as exc:
        out["first_failure"] = type(exc).__name__ + ":" + str(exc)[:120]
    return out



# A sealed GitHub CI artifact authenticates a PRIOR native observation; it is
# NOT the original HTML, a new GET, a body-reparsed event, or a formal field.
ZEPP_PRIOR_ARTIFACT_SHA256 = "6dc82ab41c1599a841c950d7416f27c310439b5360a69d758ebca52ae51cc58e"
ZEPP_PRIOR_RECEIPT_SHA256 = "d00bd5a0c1e87dd9c141f7ae69d8c8b9f167c0207f4c11d0f4c6e3a8fbfb6656"


def audit_zepp_sealed_receipt_archive(archive_bytes, expected_artifact_sha256):
    """Validate all packaged evidence and exact native receipt, without HTTP.

    expected_artifact_sha256 is an explicit trust root. Only the durable
    handoff below is permitted to use the pinned, independently read-back
    production artifact digest. This audit function is also unit-testable.
    """
    import io
    import zipfile
    if (not isinstance(archive_bytes, bytes) or
            not 0 < len(archive_bytes) <= 131072 or
            not isinstance(expected_artifact_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected_artifact_sha256) is None or
            hashlib.sha256(archive_bytes).hexdigest() != expected_artifact_sha256):
        raise ValueError("ZEPP_ARTIFACT_EXACT_SHA_HOLD")
    evidence = {
        "readiness.txt", "field_subset_review_proposal.json",
        "tmc_field_authority_contract.json",
        "canonical_field_authority_contract.json",
        "zepp_newtaipei_native_once.json"}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
        names = z.namelist()
        if (len(names) != 6 or len(set(names)) != 6 or
                set(names) != evidence | {"SHA256SUMS.txt"} or
                any(z.getinfo(name).file_size > 16384 for name in names) or
                z.testzip() is not None):
            raise ValueError("ZEPP_ARTIFACT_MEMBERS_CRC_HOLD")
        manifest = z.read("SHA256SUMS.txt").decode("ascii", errors="strict")
        lines = [line.split("  ", 1) for line in manifest.splitlines()]
        if (len(lines) != 11 or any(len(pair) != 2 for pair in lines)
                or len({pair[1] for pair in lines}) != 11):
            raise ValueError("ZEPP_ARTIFACT_MANIFEST_SHAPE_HOLD")
        packaged = {}
        for digest, name in lines:
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("ZEPP_ARTIFACT_MANIFEST_SHA_HOLD")
            if name.startswith("evidence/"):
                flat = name.removeprefix("evidence/")
                if flat not in evidence:
                    raise ValueError("ZEPP_ARTIFACT_UNKNOWN_EVIDENCE_HOLD")
                packaged[flat] = digest
        if set(packaged) != evidence or any(
                hashlib.sha256(z.read(name)).hexdigest() != packaged[name]
                for name in evidence):
            raise ValueError("ZEPP_ARTIFACT_EVIDENCE_SHA_HOLD")
        raw = z.read("zepp_newtaipei_native_once.json")
    receipt_sha = hashlib.sha256(raw).hexdigest()
    if receipt_sha != ZEPP_PRIOR_RECEIPT_SHA256 and (
            expected_artifact_sha256 == ZEPP_PRIOR_ARTIFACT_SHA256):
        raise ValueError("ZEPP_PINNED_RECEIPT_SHA_HOLD")
    receipt = json.loads(raw)
    if (not isinstance(receipt, dict)
            or receipt.get("kind") != "P30_B_ZEPP_NEWTIPEI_NATIVE_SAME_ID_ONESHOT_V1"
            or receipt.get("line") != "B"
            or receipt.get("source_key") != ZEPP_SOURCE_KEY
            or receipt.get("source_event_id") != "166457"
            or receipt.get("policy_decision") != "ALLOW_ROBOTS_200"
            or receipt.get("native_get_attempted") != 2
            or receipt.get("native_http200") != 2
            or receipt.get("native_list_get_attempted") != 1
            or receipt.get("native_detail_get_attempted") != 1
            or receipt.get("native_same_id_review") != 1
            or receipt.get("same_id_review_lkg") != 0
            or receipt.get("decision") != "REVIEW_NATIVE_SAME_ID_ONLY"
            or receipt.get("raw_html_saved") is not False
            or receipt.get("formal_accepted_fields") != 0
            or receipt.get("golden_accepted_events") != 0
            or receipt.get("published_events") != 0
            or receipt.get("release_state") != "HARD_HOLD_NO_PUBLICATION"):
        raise ValueError("ZEPP_NATIVE_RECEIPT_AUTHORITY_HOLD")
    checks = receipt.get("identity_checks")
    if (not isinstance(checks, dict)
            or checks.get("exact_rid") != "166457"
            or checks.get("title") != ZEPP_TITLE
            or checks.get("source_key") != ZEPP_SOURCE_KEY
            or checks.get("list_exact_edge_count") != 1
            or checks.get("detail_exact_heading_count") != 1
            or checks.get("date_role") != "UNVERIFIED_NOT_SESSION"
            or checks.get("start_role") != "UNVERIFIED_NOT_SESSION"):
        raise ValueError("ZEPP_NATIVE_SAME_RID_IDENTITY_HOLD")
    sources = receipt.get("source_receipts")
    if not isinstance(sources, list) or len(sources) != 2:
        raise ValueError("ZEPP_NATIVE_RECEIPT_PAIR_HOLD")
    expected = (
        (ZEPP_LIST, 343607, "1632f6235bc4a9365c2569697e50f2612e4165dfabee16bc4134f6fddbd497bf"),
        (ZEPP_DETAIL, 310512, "66750b7e3f39e7ec84c4de2b630517b9c39d4171bc305d7c0f7ca72e732aa67d"))
    from datetime import datetime, timezone
    for item, (url, count, sha) in zip(sources, expected):
        if (not isinstance(item, dict) or item.get("url") != url
                or item.get("body_bytes_read") != count
                or item.get("body_sha256") != sha
                or item.get("http_status") != 200
                or item.get("transport") != "BUILTIN_NATIVE_GET_NO_REDIRECT_NO_RETRY"):
            raise ValueError("ZEPP_NATIVE_SOURCE_RECEIPT_HOLD")
        try:
            stamp = datetime.fromisoformat(item["observed_at_utc"].replace("Z", "+00:00"))
        except (TypeError, KeyError, ValueError, AttributeError) as exc:
            raise ValueError("ZEPP_NATIVE_OBSERVATION_CLOCK_HOLD") from exc
        if stamp.utcoffset() is None or stamp.astimezone(timezone.utc).year != 2026:
            raise ValueError("ZEPP_NATIVE_OBSERVATION_CLOCK_HOLD")
    return {
        "kind": "P30_B_ZEPP_RECEIPT_IDENTITY_LKG_V1",
        "decision": "RECEIPT_ONLY_IDENTITY_REVIEW_NOT_BODY_REPLAY",
        "source_key": ZEPP_SOURCE_KEY,
        "source_event_id": "166457",
        "title": ZEPP_TITLE,
        "source_receipts": sources,
        "source_receipt_sha256": receipt_sha,
        "artifact_sha256": expected_artifact_sha256,
        "historical_native_http200": 2,
        "historical_native_same_id_review": 1,
        "native_get_this_call": 0,
        "native_same_id_review_this_call": 0,
        "receipt_only_identity_lkg": 1,
        "same_id_review_lkg": 0,
        "formal_accepted_fields": 0,
        "golden_accepted_events": 0,
        "published_events": 0,
        "raw_html_saved": False,
        "release_state": "HARD_HOLD_NO_PUBLICATION"}


def persist_zepp_receipt_identity_lkg(archive_bytes, destination, repo_root,
                                      expected_previous_sha256=None):
    """Pinned prior-artifact handoff; separate from the body-based REVIEW LKG.

    Exact isolated path, full-envelope CAS, exclusive lock and atomic fsync.
    Never creates a formal event row or upgrades prior native observations.
    """
    import os
    import tempfile
    target = Path(destination)
    root = Path(repo_root).resolve(strict=True)
    if (target.name != "zepp_receipt_identity_lkg.json"
            or any(part.is_symlink() for part in (target, *target.parents))
            or not target.parent.is_dir()):
        raise ValueError("ZEPP_RECEIPT_ISOLATED_PATH_HOLD")
    parent = target.parent.resolve(strict=True)
    if parent == root or root in parent.parents:
        raise ValueError("ZEPP_RECEIPT_REPOSITORY_PATH_HOLD")
    snapshot = audit_zepp_sealed_receipt_archive(
        archive_bytes, ZEPP_PRIOR_ARTIFACT_SHA256)
    digest = hashlib.sha256(json.dumps(
        snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False).encode("utf-8")).hexdigest()
    lock = target.with_name(target.name + ".lock")
    lock_fd, temp_path = None, None
    try:
        lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        if target.exists():
            prior_bytes = target.read_bytes()
            if len(prior_bytes) > 32768:
                raise ValueError("ZEPP_RECEIPT_PRIOR_SIZE_HOLD")
            prior = json.loads(prior_bytes)
            if (set(prior) != {"kind", "snapshot", "sha256"}
                    or prior["kind"] != "P30_B_ZEPP_DURABLE_RECEIPT_LKG_V1"
                    or prior["sha256"] != hashlib.sha256(json.dumps(
                        prior["snapshot"], sort_keys=True, ensure_ascii=False,
                        separators=(",", ":"), allow_nan=False
                    ).encode("utf-8")).hexdigest()):
                raise ValueError("ZEPP_RECEIPT_PRIOR_ENVELOPE_HOLD")
            if prior["sha256"] == digest:
                return {"persisted": False, "idempotent": True,
                        "snapshot_sha256": digest, "receipt_only_identity_lkg": 1}
            if prior["sha256"] != expected_previous_sha256:
                raise ValueError("ZEPP_RECEIPT_FULL_ENVELOPE_CAS_HOLD")
        elif expected_previous_sha256 is not None:
            raise ValueError("ZEPP_RECEIPT_MISSING_PRIOR_CAS_HOLD")
        envelope = {"kind": "P30_B_ZEPP_DURABLE_RECEIPT_LKG_V1",
                    "snapshot": snapshot, "sha256": digest}
        data = (json.dumps(envelope, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False) + "\n").encode()
        fd, temp_path = tempfile.mkstemp(prefix=".zepp_receipt.", suffix=".tmp",
                                         dir=str(parent))
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, target)
        temp_path = None
        if os.name == "posix":
            directory_fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        return {"persisted": True, "idempotent": False,
                "snapshot_sha256": digest, "receipt_only_identity_lkg": 1}
    finally:
        if temp_path is not None:
            os.unlink(temp_path)
        if lock_fd is not None:
            os.close(lock_fd)
            os.unlink(lock)



# B Zepp rid=160668 is a PRIOR, source-owned same-ID native REVIEW. The
# original HTML was not retained; this never reparses it or promotes a field.
ZEPP_TAKASE_ARTIFACT_SHA256 = "00bbdbbf0361e81a172aa3286b876181614865650eb3daf5747de52c07ea4e87"
ZEPP_TAKASE_RECEIPT_SHA256 = "c54f0cbcd182295f9eff509a800032d619dac407058c007cc6878a2f526b50ba"


def audit_zepp_takase_sealed_archive(archive_bytes, expected_artifact_sha256):
    """Audit an immutable native CI receipt, not a native GET or body replay.

    The caller-supplied digest supports isolated tests; only the pinned real
    digest is accepted by the durable handoff below.
    """
    import io
    import zipfile
    from scripts.p30_ab_kktix_fuzhong_native import SOURCES
    source = SOURCES["B_ZEPP_TAKASE"]
    if (not isinstance(archive_bytes, bytes) or not 0 < len(archive_bytes) <= 131072
            or not isinstance(expected_artifact_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_artifact_sha256) is None
            or hashlib.sha256(archive_bytes).hexdigest() != expected_artifact_sha256):
        raise ValueError("TAKASE_ARTIFACT_SHA_HOLD")
    names_expected = {"SHA256SUMS.txt", "readiness.txt",
                      "field_subset_review_proposal.json",
                      "canonical_field_authority_contract.json",
                      "tmc_field_authority_contract.json",
                      "zepp_takase_160668_native_once.json"}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
        names = z.namelist()
        if (len(names) != 6 or set(names) != names_expected
                or len(set(names)) != len(names)
                or any(z.getinfo(n).file_size > 16384 for n in names)
                or z.testzip() is not None):
            raise ValueError("TAKASE_ZIP_CRC_MEMBERS_HOLD")
        manifest = z.read("SHA256SUMS.txt").decode("ascii", "strict")
        pairs = [line.split("  ", 1) for line in manifest.splitlines()]
        if (len(pairs) != 21 or any(len(pair) != 2 for pair in pairs)
                or len({pair[1] for pair in pairs}) != 21
                or any(re.fullmatch(r"[0-9a-f]{64}", pair[0]) is None
                       for pair in pairs)):
            raise ValueError("TAKASE_MANIFEST_SHAPE_HOLD")
        evidence = {name: digest for digest, name in pairs
                    if name.startswith("evidence/")}
        expected_evidence = {"evidence/" + n for n in names_expected
                             if n != "SHA256SUMS.txt"}
        if (set(evidence) != expected_evidence
                or any(hashlib.sha256(z.read(name.removeprefix("evidence/")))
                       .hexdigest() != digest for name, digest in evidence.items())):
            raise ValueError("TAKASE_MANIFEST_EVIDENCE_SHA_HOLD")
        raw = z.read("zepp_takase_160668_native_once.json")
    receipt_sha = hashlib.sha256(raw).hexdigest()
    if (expected_artifact_sha256 == ZEPP_TAKASE_ARTIFACT_SHA256
            and receipt_sha != ZEPP_TAKASE_RECEIPT_SHA256):
        raise ValueError("TAKASE_PINNED_RECEIPT_SHA_HOLD")
    receipt = json.loads(raw)
    if (not isinstance(receipt, dict)
            or receipt.get("kind") != "P30_AB_KKTIX_FUZHONG_NATIVE_ONESHOT_V1"
            or receipt.get("line") != "B_ZEPP_TAKASE"
            or receipt.get("source_id") != source["source_id"]
            or receipt.get("source_event_id") != source["event_id"]
            or receipt.get("decision") != "REVIEW_IDENTITY_ONLY"
            or receipt.get("first_failure") != "AB_EVENT_LOCAL_FIELD_SCOPE_HOLD"
            or receipt.get("native_get_attempted") != 3
            or receipt.get("native_http200") != 2
            or receipt.get("native_list") != 1
            or receipt.get("native_detail") != 1
            or receipt.get("native_same_id_review") != 1
            or receipt.get("native_lkg") != 0
            or receipt.get("field_roles") != []
            or receipt.get("list_row_roles") != []
            or receipt.get("raw_html_saved") is not False
            or any(receipt.get(k) != 0 for k in
                   ("formal_accepted_fields", "golden", "published"))
            or receipt.get("release_state") != "HARD_HOLD_NO_PUBLICATION"):
        raise ValueError("TAKASE_NATIVE_IDENTITY_AUTHORITY_HOLD")
    robots = receipt.get("robots_receipt")
    if (not isinstance(robots, dict)
            or robots.get("url") != "https://www.zepp.co.jp/robots.txt"
            or robots.get("http_status") != 200
            or robots.get("body_bytes") != 160
            or robots.get("body_sha256") !=
               "f85c8154288b52d4d691b12fa3d0df1bec3f51cba30933d11eb9d20b3d99d6cd"
            or robots.get("transport") != "NATIVE_NO_REDIRECT_NO_RETRY"):
        raise ValueError("TAKASE_ROBOTS_RECEIPT_HOLD")
    sources = receipt.get("source_receipts")
    expected = (
        (source["list"], 336693,
         "890893c79a796f222f52d4ad628edae2da273be73a7e033ef4ea95d992ebd657"),
        (source["detail"], 313606,
         "d78ae5cedcd1089619b28c55b4fadff1ac1b66946de79551c52fa7bc6d93a4f6"))
    if not isinstance(sources, list) or len(sources) != 2:
        raise ValueError("TAKASE_SOURCE_PAIR_HOLD")
    times = []
    for item, (url, count, digest) in zip(sources, expected):
        if (not isinstance(item, dict) or item.get("url") != url
                or item.get("http_status") != 200
                or item.get("content_type") != "text/html"
                or item.get("body_bytes") != count
                or item.get("body_sha256") != digest
                or item.get("transport") != "NATIVE_NO_REDIRECT_NO_RETRY"):
            raise ValueError("TAKASE_SOURCE_SHA_IDENTITY_HOLD")
        try:
            stamp = datetime.fromisoformat(
                item["observed_at_utc"].replace("Z", "+00:00"))
        except (TypeError, KeyError, ValueError, AttributeError) as exc:
            raise ValueError("TAKASE_SOURCE_CLOCK_HOLD") from exc
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("TAKASE_SOURCE_CLOCK_HOLD")
        times.append(stamp)
    if not 0 <= (times[1] - times[0]).total_seconds() <= 120:
        raise ValueError("TAKASE_LIST_DETAIL_CLOCK_SKEW_HOLD")
    fields = receipt.get("field_receipts")
    if (not isinstance(fields, list) or len(fields) != 1
            or not isinstance(fields[0], dict)
            or fields[0].get("source_id") != source["source_id"]
            or fields[0].get("event_id") != source["event_id"]
            or fields[0].get("source_url") != source["detail"]
            or fields[0].get("body_sha256") != expected[1][2]
            or fields[0].get("observed_at_utc") != sources[1]["observed_at_utc"]
            or fields[0].get("role") != "SOURCE_EXACT_TITLE_REVIEW"
            or fields[0].get("decision") != "REVIEW"
            or fields[0].get("formal_accepted") is not False):
        raise ValueError("TAKASE_FIELD_RECEIPT_AUTHORITY_HOLD")
    return {
        "kind": "P30_B_ZEPP_TAKASE_SEALED_RECEIPT_REVIEW_V1",
        "decision": "RECEIPT_ONLY_SAME_ID_REVIEW_NOT_BODY_REPLAY",
        "source_id": source["source_id"], "source_event_id": source["event_id"],
        "source_title_review": source["title"],
        "source_receipts": sources, "field_receipts": fields,
        "artifact_sha256": expected_artifact_sha256,
        "receipt_sha256": receipt_sha,
        "observed_at_utc": sources[1]["observed_at_utc"],
        "native_get_this_call": 0, "historical_native_http200": 2,
        "historical_same_id_review": 1,
        "receipt_only_identity_lkg": 1, "body_review_lkg": 0,
        "field_authority": "EVENT_LOCAL_SCOPE_HOLD",
        "showtime_role": "UNKNOWN_NOT_SESSION",
        "venue_role": "UNKNOWN_NOT_ACCEPTED",
        "formal_accepted_fields": 0, "golden_accepted_events": 0,
        "published_events": 0, "raw_html_saved": False,
        "release_state": "HARD_HOLD_NO_PUBLICATION"}


def persist_sealed_receipt_review_lkg(snapshot, destination, repo_root,
                                      *, expected_filename, envelope_kind,
                                      expected_previous_sha256=None):
    """Reusable nonpublishing receipt-only durable CAS, never a formal row."""
    import os
    import tempfile
    if (not isinstance(snapshot, dict)
            or snapshot.get("receipt_only_identity_lkg") != 1
            or snapshot.get("body_review_lkg") != 0
            or snapshot.get("native_get_this_call") != 0
            or any(snapshot.get(k) != 0 for k in
                   ("formal_accepted_fields", "golden_accepted_events",
                    "published_events"))
            or snapshot.get("release_state") != "HARD_HOLD_NO_PUBLICATION"):
        raise ValueError("RECEIPT_LKG_NONPUBLISHING_CONTRACT_HOLD")
    target = Path(destination)
    root = Path(repo_root).resolve(strict=True)
    if (target.name != expected_filename
            or any(part.is_symlink() for part in (target, *target.parents))
            or not target.parent.is_dir()):
        raise ValueError("RECEIPT_LKG_ISOLATION_PATH_HOLD")
    parent = target.parent.resolve(strict=True)
    if parent == root or root in parent.parents:
        raise ValueError("RECEIPT_LKG_REPOSITORY_PATH_HOLD")
    serialized = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                            separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    envelope = {"kind": envelope_kind, "snapshot": snapshot, "sha256": digest}
    data = (json.dumps(envelope, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    if len(data) > 32768:
        raise ValueError("RECEIPT_LKG_SIZE_HOLD")
    lock = target.with_name(target.name + ".lock")
    lock_fd, temporary = None, None
    try:
        lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        if target.exists():
            old = target.read_bytes()
            if len(old) > 32768:
                raise ValueError("RECEIPT_LKG_PRIOR_SIZE_HOLD")
            prior = json.loads(old)
            if (not isinstance(prior, dict)
                    or set(prior) != {"kind", "snapshot", "sha256"}
                    or prior["kind"] != envelope_kind
                    or prior["sha256"] != hashlib.sha256(json.dumps(
                        prior["snapshot"], sort_keys=True, ensure_ascii=False,
                        separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                    or prior["snapshot"].get("release_state") !=
                       "HARD_HOLD_NO_PUBLICATION"):
                raise ValueError("RECEIPT_LKG_PRIOR_ENVELOPE_HOLD")
            if prior["sha256"] == digest:
                return {"persisted": False, "idempotent": True,
                        "snapshot_sha256": digest, "receipt_only_identity_lkg": 1}
            if prior["sha256"] != expected_previous_sha256:
                raise ValueError("RECEIPT_LKG_FULL_ENVELOPE_CAS_HOLD")
        elif expected_previous_sha256 is not None:
            raise ValueError("RECEIPT_LKG_MISSING_PRIOR_CAS_HOLD")
        fd, temporary = tempfile.mkstemp(prefix=".receipt_lkg.", suffix=".tmp",
                                         dir=str(parent))
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        temporary = None
        if os.name == "posix":
            dir_fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        if target.read_bytes() != data:
            raise ValueError("RECEIPT_LKG_ATOMIC_READBACK_HOLD")
        return {"persisted": True, "idempotent": False,
                "snapshot_sha256": digest, "receipt_only_identity_lkg": 1}
    finally:
        if temporary is not None:
            os.unlink(temporary)
        if lock_fd is not None:
            os.close(lock_fd)
            os.unlink(lock)


def persist_zepp_takase_receipt_lkg(archive_bytes, destination, repo_root,
                                    expected_previous_sha256=None):
    """Pinned prior native Zepp rid 160668 -> isolated receipt LKG only."""
    snapshot = audit_zepp_takase_sealed_archive(
        archive_bytes, ZEPP_TAKASE_ARTIFACT_SHA256)
    return persist_sealed_receipt_review_lkg(
        snapshot, destination, repo_root,
        expected_filename="zepp_takase_receipt_lkg.json",
        envelope_kind="P30_B_ZEPP_TAKASE_DURABLE_RECEIPT_LKG_V1",
        expected_previous_sha256=expected_previous_sha256)


def main():
    parser = argparse.ArgumentParser(description="Offline source replay only; never HTTP")
    parser.add_argument("--tpac-html", type=Path)
    parser.add_argument("--songshan-evidence", type=Path)
    parser.add_argument("--tpac-native-once", action="store_true")
    parser.add_argument("--zepp-native-once", action="store_true")
    parser.add_argument("--opentix-native-once", action="store_true")
    parser.add_argument("--ab-replay-manifest", type=Path)
    parser.add_argument("--ab-line", choices=("A", "B"))
    parser.add_argument("--ab-isolated-output", type=Path)
    parser.add_argument("--ab-repo-root", type=Path)
    args = parser.parse_args()
    if sum((bool(args.tpac_html), bool(args.songshan_evidence), args.tpac_native_once, args.zepp_native_once, args.opentix_native_once, bool(args.ab_replay_manifest))) != 1:
        parser.error("supply exactly one input; native is a CI one-shot only")
    if args.ab_replay_manifest:
        if not all((args.ab_line, args.ab_isolated_output, args.ab_repo_root)):
            parser.error("A/B replay requires --ab-line, --ab-isolated-output and --ab-repo-root")
        result = replay_preacquired_ab_to_review_lkg(
            args.ab_line, args.ab_replay_manifest, args.ab_isolated_output,
            args.ab_repo_root)
    elif args.tpac_native_once:
        result = acquire_tpac_native_once()
    elif args.zepp_native_once:
        result = probe_zepp_newtaipei_native_once()
    elif args.opentix_native_once:
        result = probe_opentix_fresh_detail_native_once()
    elif args.tpac_html:
        with args.tpac_html.open("rb") as stream:
            result = inspect_tpac_complete_stream(
                stream, status=200, content_type="text/html; charset=utf-8",
                final_url=TPAC_URL, observed_at_utc=datetime.now(timezone.utc).isoformat())
    else:
        result = audit_songshan_prior_native_receipt(
            json.loads(args.songshan_evidence.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["decision"].startswith(("REVIEW_", "PRIOR_NATIVE_")) else 49


if __name__ == "__main__":
    raise SystemExit(main())
