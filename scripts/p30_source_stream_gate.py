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
        kind = "heading" if tag in ("h1", "h2", "h3") else (
            "anchor" if tag == "a" else None)
        if kind:
            self.capture.append([len(self.stack), kind, attrs, "",
                                 self.section_stack[-1][1] if self.section_stack else None])

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
        headings = [scope for _, text, scope in parser.headings if text == TITLE]
        anchors = [scope for attrs, _, scope in parser.anchors
                   if urljoin(TPAC_URL, attrs.get("href", "")) == TICKET_URL]
        shared_section = (len(headings) == len(anchors) == 1
                          and headings[0] is not None
                          and headings[0] == anchors[0])
        room_in_shared_section = bool(shared_section and "藍盒子" in
                                      " ".join(parser.section_text[headings[0]].split()))
        report["event_local_checks"] = {
            "exact_title_heading_count": len(headings),
            "direct_ticket_href_count": len(anchors),
            "same_section_identity": bool(shared_section),
            "room_in_same_section": room_in_shared_section,
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


def main():
    parser = argparse.ArgumentParser(description="Offline source replay only; never HTTP")
    parser.add_argument("--tpac-html", type=Path)
    parser.add_argument("--songshan-evidence", type=Path)
    args = parser.parse_args()
    if bool(args.tpac_html) == bool(args.songshan_evidence):
        parser.error("supply exactly one offline input")
    if args.tpac_html:
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
