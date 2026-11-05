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


def main():
    parser = argparse.ArgumentParser(description="Offline source replay only; never HTTP")
    parser.add_argument("--tpac-html", type=Path)
    parser.add_argument("--songshan-evidence", type=Path)
    parser.add_argument("--tpac-native-once", action="store_true")
    parser.add_argument("--ab-replay-manifest", type=Path)
    parser.add_argument("--ab-line", choices=("A", "B"))
    parser.add_argument("--ab-isolated-output", type=Path)
    parser.add_argument("--ab-repo-root", type=Path)
    args = parser.parse_args()
    if sum((bool(args.tpac_html), bool(args.songshan_evidence), args.tpac_native_once, bool(args.ab_replay_manifest))) != 1:
        parser.error("supply exactly one input; native is a CI one-shot only")
    if args.ab_replay_manifest:
        if not all((args.ab_line, args.ab_isolated_output, args.ab_repo_root)):
            parser.error("A/B replay requires --ab-line, --ab-isolated-output and --ab-repo-root")
        result = replay_preacquired_ab_to_review_lkg(
            args.ab_line, args.ab_replay_manifest, args.ab_isolated_output,
            args.ab_repo_root)
    elif args.tpac_native_once:
        result = acquire_tpac_native_once()
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
