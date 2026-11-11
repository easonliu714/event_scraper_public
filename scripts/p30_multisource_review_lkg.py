"""Deterministic two-source REVIEW/LKG bridge; never a native GET or Publisher.

Ports independently developed TaiNEX #217 and FamiTicket #221 source-reader
contracts to the existing main candidate Core. Source-reader records are
historical, reconstructed observations, NOT independently reattested HTML.
No field is promoted to formal ACCEPTED; exhibition periods are not showtimes.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from scripts import p30_venue02bo_tainex_exhibition as tainex
from scripts import p30_l9dc_famiticket_teca as famiticket
from scripts.p30_candidate_review_pipeline import build_candidate_dataset
from scripts.p30_tainex_archived_native_bridge import (
    SOURCE_CLASS as NATIVE_AUDIT_CLASS, archived_inputs,
    inspect_archived_native, validate_archived_prior,
)

HOLD = "HARD_HOLD_NO_PUBLICATION"
# Both reused readers are 2026-11-02 historical observations, not live adapters.
# The next local midnight is an upper bound, NOT a native evidence timestamp.
# Reject later caller-supplied clocks rather than laundering a replay into a
# newer LKG revision; fresh source data requires a separately attested adapter.
HISTORICAL_REPLAY_END_UTC = datetime(2026, 11, 2, 16, 0, tzinfo=timezone.utc)
REGISTRY = {
    "tainex": {"module": tainex, "platform_id": "TAINEX",
               "platform": "台北南港展覽館", "gate": "P30-VENUE-02BO",
               "expected_decision": "REVIEW", "expected_fields": 6,
               "namespace": "event", "source_pr": 217,
               "replay_clock": "2026-11-02T06:57:00+08:00"},
    "famiticket": {"module": famiticket, "platform_id": "FAMITICKET",
                   "platform": "FamiTicket", "gate": "P30-L9-DC",
                   "expected_decision": "REVIEW_WITH_HOLD", "expected_fields": 9,
                   "namespace": "Home/Activity/Info", "source_pr": 221,
                   "replay_clock": "2026-11-02T06:55:00+08:00"},
}


def utc(value):
    if not isinstance(value, str):
        raise ValueError("OBSERVED_AT_MISSING_HOLD")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("OBSERVED_AT_TIMEZONE_HOLD")
    return t.astimezone(timezone.utc)


def inspect_one(packet, as_of):
    """Reuse exact legacy source readers, then enforce a common role boundary."""
    if not isinstance(packet, dict) or packet.get("source") not in REGISTRY:
        raise ValueError("UNREGISTERED_SOURCE_HOLD")
    spec = REGISTRY[packet["source"]]
    obs = packet.get("observation")
    observed_at = packet.get("observed_at")
    seen_at = utc(observed_at)
    if seen_at > as_of:
        raise ValueError("FUTURE_OBSERVATION_HOLD")
    if seen_at >= HISTORICAL_REPLAY_END_UTC:
        raise ValueError("HISTORICAL_REPLAY_CLOCK_ESCALATION_HOLD")
    # A caller cannot backdate or advance the old reconstructed observation
    # within the historical day to replace a retained LKG. This clock is a
    # fixed replay reference, NOT an independently attested HTTP timestamp.
    if seen_at != utc(spec["replay_clock"]):
        raise ValueError("HISTORICAL_REPLAY_CLOCK_BINDING_HOLD")
    inspected = spec["module"].inspect(obs, observed_at)
    if (inspected.get("decision") != spec["expected_decision"]
            or inspected.get("acceptedFields") != 0
            or inspected.get("goldenAccepted") != 0
            or inspected.get("published") is not False
            or inspected.get("releaseState") != HOLD):
        raise ValueError("SOURCE_READER_ROLE_OR_IDENTITY_HOLD")
    fields = inspected.get("candidateFields")
    if not isinstance(fields, list) or len(fields) != spec["expected_fields"]:
        raise ValueError("SOURCE_FIELD_COUNT_HOLD")
    if (not isinstance(obs, dict) or obs.get("list_url") != spec["module"].LIST
            or obs.get("list_detail_href") != spec["module"].DETAIL
            or obs.get("detail_url") != spec["module"].DETAIL):
        raise ValueError("LIST_DETAIL_IDENTITY_HOLD")
    if any(not isinstance(f, dict) or f.get("decision") != "REVIEW"
           or f.get("observed_at") != observed_at or
           f.get("source") not in (spec["module"].DETAIL, spec["module"].LIST)
           for f in fields):
        raise ValueError("SOURCE_FIELD_PROVENANCE_HOLD")
    # A ticket product, presale or exhibition period cannot be promoted into
    # a showtime, available inventory or general minimum admission price.
    if any(f.get("role") in ("SHOW_START", "TICKET_SESSION_ID",
                             "EVENT_GENERAL_ADMISSION_MIN_PRICE")
           for f in fields):
        raise ValueError("UNAUTHORIZED_FIELD_ROLE_HOLD")
    u = urlsplit(spec["module"].DETAIL)
    if u.scheme != "https" or u.query or u.fragment:
        raise ValueError("DETAIL_NAMESPACE_HOLD")
    prefix = "/" + spec["namespace"] + "/"
    if not u.path.startswith(prefix):
        raise ValueError("DETAIL_NAMESPACE_HOLD")
    event_id = u.path[len(prefix):]
    if not event_id or "/" in event_id:
        raise ValueError("SOURCE_ID_HOLD")
    # Only the exact original source-reader's same-ID title is carried into
    # the review card. Optional PWA fields stay unknown until role acceptance.
    title = obs["detail_title"]
    candidate = {
        "title": title, "url": spec["module"].DETAIL,
        "platform": spec["platform"], "type": "展覽",
        "scraped_at": observed_at, "date": "未確認",
        "location": "未確認", "price": "未確認",
        "_candidate": {
            "scope": "CANDIDATE_PREVIEW_ONLY",
            "decision": "REVIEW_WITH_HOLD",
            "platform_id": spec["platform_id"],
            "source_event_id": event_id,
            "record_id": spec["platform_id"] + ":" + spec["namespace"] + ":" + event_id,
            "source_class": "HISTORICAL_SOURCE_READER_REPLAY",
            "sources": [spec["module"].LIST, spec["module"].DETAIL],
            "hold_reasons": [
                "SOURCE_READER_NOT_INDEPENDENT_NATIVE_ATTESTATION",
                "HISTORICAL_OBSERVATION_NOT_CURRENT_SOURCE",
                "EXHIBITION_PERIOD_NOT_SHOW_START",
                "TICKET_SESSION_AND_GENERAL_MIN_PRICE_NOT_ACCEPTED",
            ],
            "field_evidence": {},
            "formal_field_pass": False, "golden_accepted": False,
            "published": False, "ticket_session_id": None, "inventory": None,
        },
    }
    return {"candidate": candidate, "gate": spec["gate"],
            "source_pr": spec["source_pr"],
            "source_reader_fields": fields,
            "source_reader_decision": inspected["decision"],
            "freshness": "HISTORICAL_REPLAY_ONLY",
            "native_http_attested": False}


def validate_prior_binding(row, as_of):
    """Reject forged/stale historical LKG even if the generic preview schema accepts it."""
    meta = row["_candidate"]
    if meta.get("source_class") == NATIVE_AUDIT_CLASS:
        validate_archived_prior(row, as_of)
        return
    specs = [spec for spec in REGISTRY.values()
             if spec["platform_id"] == meta.get("platform_id")]
    if len(specs) != 1:
        raise ValueError("PRIOR_LKG_SOURCE_BINDING_HOLD")
    spec = specs[0]
    detail = spec["module"].DETAIL
    url = urlsplit(detail)
    event_id = url.path[len("/" + spec["namespace"] + "/"):]
    required_holds = {
        "SOURCE_READER_NOT_INDEPENDENT_NATIVE_ATTESTATION",
        "HISTORICAL_OBSERVATION_NOT_CURRENT_SOURCE",
        "EXHIBITION_PERIOD_NOT_SHOW_START",
        "TICKET_SESSION_AND_GENERAL_MIN_PRICE_NOT_ACCEPTED",
    }
    if (row.get("url") != detail or row.get("title") != spec["module"].TITLE
            or row.get("platform") != spec["platform"]
            or row.get("type") != "展覽"
            or meta.get("source_event_id") != event_id
            or meta.get("record_id") != (
                spec["platform_id"] + ":" + spec["namespace"] + ":" + event_id)
            or meta.get("source_class") != "HISTORICAL_SOURCE_READER_REPLAY"
            or meta.get("sources") != [spec["module"].LIST, detail]
            or not required_holds.issubset(set(meta.get("hold_reasons", [])))
            or meta.get("field_evidence") != {}
            or any(row.get(k) != "未確認" for k in ("date", "price", "location"))
            or utc(row["scraped_at"]) > as_of
            or utc(row["scraped_at"]) >= HISTORICAL_REPLAY_END_UTC
            or utc(row["scraped_at"]) != utc(spec["replay_clock"])):
        raise ValueError("PRIOR_LKG_SOURCE_BINDING_HOLD")



class _RawPairHTML(HTMLParser):
    """Parse visible source LIST links and DETAIL headings only.

    Hidden DOM cannot attest identity. Supplied bytes remain UNATTESTED,
    with no native HTTP, field acceptance, LKG or publication authority.
    """
    _VOID = frozenset(("area", "base", "br", "col", "embed", "hr",
                       "img", "input", "link", "meta", "param", "source",
                       "track", "wbr"))
    _NON_RENDERED = frozenset(("script", "style", "noscript", "template"))
    _HIDDEN_CLASSES = frozenset(("hidden", "sr-only", "visually-hidden",
                                 "d-none", "display-none", "invisible",
                                 "is-hidden", "ng-hide"))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.headings, self.stack = [], [], []
        self.blocked_stack = []

    @classmethod
    def _not_visible(cls, tag, attrs):
        attributes = dict(attrs)
        style = attributes.get("style") or ""
        classes = set((attributes.get("class") or "").lower().split())
        return (
            tag in cls._NON_RENDERED
            or "hidden" in attributes or "inert" in attributes
            or (attributes.get("aria-hidden") or "").strip().lower() == "true"
            or bool(classes & cls._HIDDEN_CLASSES)
            or bool(re.search(
                r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden|"
                r"content-visibility\s*:\s*hidden)\b",
                style, flags=re.IGNORECASE,
            ))
        )

    def handle_starttag(self, tag, attrs):
        if self.blocked_stack or self._not_visible(tag, attrs):
            # Void elements must not swallow later visible source edges.
            if tag not in self._VOID:
                self.blocked_stack.append(tag)
            return
        if tag == "a":
            self.stack.append((tag, dict(attrs).get("href"), []))
        elif tag in ("h1", "h2", "h3"):
            self.stack.append((tag, None, []))

    def handle_data(self, data):
        if not self.blocked_stack:
            for item in self.stack:
                item[2].append(data)

    def handle_endtag(self, tag):
        if self.blocked_stack:
            if tag in self.blocked_stack:
                while self.blocked_stack:
                    if self.blocked_stack.pop() == tag:
                        break
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                kind, href, chunks = self.stack.pop(i)
                value = " ".join("".join(chunks).split())
                if kind == "a":
                    self.links.append((href, value))
                else:
                    self.headings.append(value)
                break



def _raw_source_detail_id(spec, detail_url):
    """Validate a source-local event ID, not a caller-asserted ticket identity.

    Unlike historical frozen readers, this isolated raw-byte adapter accepts
    additional IDs under the exact official host and source-specific namespace.
    No HTTP origin, freshness, field, LKG, or publication authority is granted.
    """
    if not isinstance(detail_url, str):
        raise ValueError("RAW_DETAIL_ID_NAMESPACE_HOLD")
    try:
        actual = urlsplit(detail_url)
        expected = urlsplit(spec["module"].DETAIL)
        prefix = "/" + spec["namespace"] + "/"
        if (actual.scheme != "https" or actual.netloc != expected.netloc
                or actual.username is not None or actual.password is not None
                or actual.port is not None or actual.query or actual.fragment
                or not actual.path.startswith(prefix)
                or detail_url != "https://" + expected.netloc + actual.path):
            raise ValueError("RAW_DETAIL_ID_NAMESPACE_HOLD")
        event_id = actual.path[len(prefix):]
        pattern = (r"[0-9]{1,8}" if spec["platform_id"] == "TAINEX"
                   else r"[A-Za-z0-9_-]{16,256}")
        if not re.fullmatch(pattern, event_id, flags=re.ASCII):
            raise ValueError("RAW_DETAIL_ID_NAMESPACE_HOLD")
        return event_id
    except (ValueError, TypeError) as exc:
        raise ValueError("RAW_DETAIL_ID_NAMESPACE_HOLD") from exc


def inspect_raw_pair(packet, as_of):
    """Parse caller-supplied raw LIST/DETAIL bytes without claiming HTTP provenance.

    The raw bytes and clock are not an independently attested native capture.
    Never merge this result into accepted fields or REVIEW LKG. A separate
    source collector must preserve original bytes and prove origin, timing,
    source-specific policy and cross-host Claim before any promotion.
    """
    if not isinstance(packet, dict) or packet.get("source") not in REGISTRY:
        raise ValueError("RAW_SOURCE_ALLOWLIST_HOLD")
    spec = REGISTRY[packet["source"]]
    list_url, detail_url = spec["module"].LIST, packet.get("detail_url")
    if packet.get("list_url") != list_url:
        raise ValueError("RAW_URL_EXACT_HOLD")
    event_id = _raw_source_detail_id(spec, detail_url)
    if not isinstance(packet.get("observed_at"), str):
        raise ValueError("RAW_CLOCK_MISSING_HOLD")
    seen = utc(packet["observed_at"])
    if as_of.tzinfo is None or as_of.utcoffset() is None or seen > as_of.astimezone(timezone.utc):
        raise ValueError("RAW_CLOCK_FUTURE_HOLD")
    bodies, parsed = [], []
    for role in ("list", "detail"):
        encoded = packet.get(role + "_html_b64")
        if not isinstance(encoded, str):
            raise ValueError("RAW_BODY_MISSING_HOLD")
        try:
            raw = base64.b64decode(encoded, validate=True)
            if not 0 < len(raw) <= 1048576 or b"\x00" in raw:
                raise ValueError("RAW_BODY_SIZE_OR_BINARY_HOLD")
            html = raw.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError, base64.binascii.Error) as exc:
            raise ValueError("RAW_BODY_ENCODING_HOLD") from exc
        p = _RawPairHTML()
        p.feed(html)
        p.close()
        bodies.append({"role": role.upper(), "sha256": hashlib.sha256(raw).hexdigest(),
                       "bytes": len(raw)})
        parsed.append(p)
    exact_links = [
        label for href, label in parsed[0].links
        if isinstance(href, str) and urljoin(list_url, href) == detail_url
    ]
    # Title is derived from the actual supplied LIST bytes, never from
    # caller metadata or the frozen historical single-event constants.
    if len(exact_links) != 1 or not 0 < len(exact_links[0]) <= 200:
        raise ValueError("RAW_LIST_EXACT_ID_TITLE_HOLD")
    title = exact_links[0]
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in title):
        raise ValueError("RAW_LIST_EXACT_ID_TITLE_HOLD")
    if parsed[1].headings.count(title) != 1:
        raise ValueError("RAW_DETAIL_EXACT_TITLE_HOLD")
    return {
        "source": packet["source"], "record_id": spec["platform_id"] + ":" +
        spec["namespace"] + ":" + event_id, "source_event_id": event_id,
        "list_url": list_url, "detail_url": detail_url,
        "source_title_unattested": title, "raw_bodies": bodies,
        "observed_at_claimed": packet["observed_at"],
        "decision": "REVIEW_RAW_PAIR_IDENTITY_ONLY",
        "source_authority": "CALLER_SUPPLIED_UNATTESTED_BYTES",
        "source_time_authority": "UNATTESTED",
        "raw_html_retention_verified": False, "native_http_attested": False,
        "accepted_fields": 0, "lkg_promoted": False, "published": False,
        "commit_permitted": False,
    }


def _raw_archive_directory(repo_root, archive_id):
    """Return an isolated unique archive path, never a formal or shared path."""
    if not isinstance(archive_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9_-]{0,63}", archive_id, flags=re.ASCII):
        raise ValueError("RAW_ARCHIVE_ID_HOLD")
    root = Path(repo_root).resolve(strict=True)
    isolated = root / "_isolated_review"
    if isolated.is_symlink():
        raise ValueError("RAW_ARCHIVE_SYMLINK_HOLD")
    isolated.mkdir(exist_ok=True)
    base = isolated / "raw_pairs"
    if base.is_symlink():
        raise ValueError("RAW_ARCHIVE_SYMLINK_HOLD")
    base.mkdir(exist_ok=True)
    if not base.resolve().is_relative_to(root) or base.resolve() == root:
        raise ValueError("RAW_ARCHIVE_ISOLATION_HOLD")
    target = base / archive_id
    if target.is_symlink():
        raise ValueError("RAW_ARCHIVE_SYMLINK_HOLD")
    return target


def verify_raw_pair_archive(repo_root, archive_id, as_of):
    """Independently read back exact retained bytes; HTTP origin remains UNATTESTED."""
    target = _raw_archive_directory(repo_root, archive_id)
    if not target.is_dir() or target.is_symlink():
        raise ValueError("RAW_ARCHIVE_MISSING_HOLD")
    names = {"list.html", "detail.html", "manifest.json"}
    if {p.name for p in target.iterdir()} != names:
        raise ValueError("RAW_ARCHIVE_MEMBER_SET_HOLD")
    if any((target / name).is_symlink() for name in names):
        raise ValueError("RAW_ARCHIVE_SYMLINK_HOLD")
    try:
        raw_manifest = (target / "manifest.json").read_bytes()
        if len(raw_manifest) > 8192:
            raise ValueError("RAW_ARCHIVE_MANIFEST_SIZE_HOLD")
        manifest = json.loads(raw_manifest.decode("utf-8"))
        if not isinstance(manifest, dict) or manifest.get("kind") != (
                "EVENTRADAR_ISOLATED_RAW_PAIR_RETENTION_V1"):
            raise ValueError("RAW_ARCHIVE_MANIFEST_HOLD")
        if manifest.get("archive_id") != archive_id:
            raise ValueError("RAW_ARCHIVE_ID_MISMATCH_HOLD")
        if (manifest.get("native_http_attested") is not False
                or manifest.get("source_authority") != "CALLER_SUPPLIED_UNATTESTED_BYTES"
                or manifest.get("commit_permitted") is not False
                or manifest.get("published") is not False
                or manifest.get("accepted_fields") != 0):
            raise ValueError("RAW_ARCHIVE_AUTHORITY_HOLD")
        packet = {key: manifest[key] for key in
                  ("source", "list_url", "detail_url", "observed_at")}
        for role in ("list", "detail"):
            raw = (target / (role + ".html")).read_bytes()
            packet[role + "_html_b64"] = base64.b64encode(raw).decode("ascii")
        inspected = inspect_raw_pair(packet, as_of)
        if (manifest.get("record_id") != inspected["record_id"]
                or manifest.get("raw_bodies") != inspected["raw_bodies"]):
            raise ValueError("RAW_ARCHIVE_HASH_OR_ID_HOLD")
    except (OSError, UnicodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("RAW_ARCHIVE_UNREADABLE_HOLD") from exc
    return {
        "archive_id": archive_id,
        "record_id": inspected["record_id"],
        "raw_bodies": inspected["raw_bodies"],
        "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
        "raw_html_retention_verified": True,
        "native_http_attested": False,
        "source_authority": "CALLER_SUPPLIED_UNATTESTED_BYTES",
        "independently_accepted_fields": 0,
        "lkg_promoted": False,
        "commit_permitted": False,
        "published": False,
    }


def archive_raw_pair(packet, *, repo_root, archive_id, as_of):
    """Persist exact supplied LIST/DETAIL bytes in a new isolated directory.

    This closes the missing *byte-retention mechanism*, not the independent
    HTTP provenance/Claim Gate. A future authorized collector must attest
    source response, rate budget and cross-host Claim separately. Never GET.
    """
    import os
    inspected = inspect_raw_pair(packet, as_of)
    target = _raw_archive_directory(repo_root, archive_id)
    try:
        target.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise ValueError("RAW_ARCHIVE_REPLAY_OR_COLLISION_HOLD") from exc
    manifest = {
        "kind": "EVENTRADAR_ISOLATED_RAW_PAIR_RETENTION_V1",
        "archive_id": archive_id,
        "source": packet["source"],
        "list_url": inspected["list_url"],
        "detail_url": inspected["detail_url"],
        "observed_at": packet["observed_at"],
        "record_id": inspected["record_id"],
        "raw_bodies": inspected["raw_bodies"],
        "source_authority": "CALLER_SUPPLIED_UNATTESTED_BYTES",
        "native_http_attested": False,
        "accepted_fields": 0,
        "commit_permitted": False,
        "published": False,
    }
    for role in ("list", "detail"):
        raw = base64.b64decode(packet[role + "_html_b64"], validate=True)
        # Exclusive creation and fsync prevent silently replacing evidence.
        with (target / (role + ".html")).open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    encoded = (json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")) + "\n").encode("utf-8")
    with (target / "manifest.json").open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return verify_raw_pair_archive(repo_root, archive_id, as_of)


def plan(packets, *, previous=None, as_of, archived_native=None, raw_pairs=None):
    """Pure multi-source REVIEW merge, with fail-closed non-destructive LKG."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("CLOCK_TIMEZONE_HOLD")
    now = as_of.astimezone(timezone.utc)
    if not isinstance(packets, list) or len(packets) > 2000:
        raise ValueError("SOURCE_INPUT_CAP_HOLD")
    if previous is None:
        previous = []
    if not isinstance(previous, list):
        raise ValueError("PRIOR_LKG_SCHEMA_HOLD")
    prior, prior_report = build_candidate_dataset(previous)
    if prior_report["rejectedRows"] or len(prior) != len(previous):
        raise ValueError("PRIOR_LKG_INTEGRITY_HOLD")
    # The generic candidate Core may intentionally strip unsupported keys.
    # For a durable LKG input, silent sanitization would conceal a forged
    # field receipt or publication claim. Require exact canonical round-trip.
    for raw_row, old_row in zip(previous, prior):
        if raw_row != old_row:
            raise ValueError("PRIOR_LKG_NONCANONICAL_HOLD")
        validate_prior_binding(old_row, now)
    receipts, rejected = [], []
    for index, packet in enumerate(packets):
        try:
            receipts.append(inspect_one(packet, now))
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            rejected.append({"index": index, "reason": str(exc)})
    # Historical official native audit JSON, SHA-pinned to two independent
    # earlier GitHub artifacts. Original HTML was NOT retained; REVIEW only.
    if archived_native is None:
        archived_native = []
    if not isinstance(archived_native, list) or len(archived_native) > 2:
        raise ValueError("ARCHIVED_NATIVE_INPUT_CAP_HOLD")
    native_receipts = []
    for index, item in enumerate(archived_native):
        try:
            if not isinstance(item, dict):
                raise ValueError("ARCHIVED_NATIVE_INPUT_HOLD")
            native_receipts.append(inspect_archived_native(
                item.get("id"), item.get("audit_bytes"), now))
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            rejected.append({"index": "native:" + str(index), "reason": str(exc)})
    # Raw HTML parsing is a real adapter capability, but caller-supplied
    # bytes cannot establish origin or retention. Do not add these records to
    # REVIEW LKG or independently accepted fields without a separate Gate.
    if raw_pairs is None:
        raw_pairs = []
    if not isinstance(raw_pairs, list) or len(raw_pairs) > 20:
        raise ValueError("RAW_PAIR_INPUT_CAP_HOLD")
    raw_pair_reviews, raw_seen = [], set()
    for index, pair in enumerate(raw_pairs):
        try:
            parsed_pair = inspect_raw_pair(pair, now)
            if parsed_pair["record_id"] in raw_seen:
                raise ValueError("RAW_PAIR_DUPLICATE_ID_HOLD")
            raw_seen.add(parsed_pair["record_id"])
            raw_pair_reviews.append(parsed_pair)
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            rejected.append({"index": "raw:" + str(index), "reason": str(exc)})
    candidates, quality = build_candidate_dataset(
        [r["candidate"] for r in receipts + native_receipts])
    if quality["rejectedRows"]:
        rejected.extend({"index": x["index"], "reason": ",".join(x["reasons"])}
                        for x in quality["rejected"])
    # Keep the source reader's role/value/URL/observed_at receipts in the
    # isolated plan. The generic PWA Core deliberately drops unsupported
    # roles; these receipts are REVIEW only, not native HTML attestation.
    qualified_ids = {x["_candidate"]["record_id"] for x in candidates}
    source_receipts, audited_ids = [], set()
    for receipt in receipts:
        meta = receipt["candidate"]["_candidate"]
        record_id = meta["record_id"]
        if record_id not in qualified_ids or record_id in audited_ids:
            continue
        audited_ids.add(record_id)
        fields = receipt["source_reader_fields"]
        encoded = json.dumps(fields, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        source_receipts.append({
            "record_id": record_id,
            "source_gate": receipt["gate"],
            "source_pr": receipt["source_pr"],
            "source_reader_decision": receipt["source_reader_decision"],
            "source_reader_fields": fields,
            "source_reader_fields_sha256": hashlib.sha256(encoded).hexdigest(),
            "native_http_attested": False,
            "formal_field_accepted": False,
        })
    source_receipts.sort(key=lambda x: x["record_id"])
    old = {(x["_candidate"]["platform_id"], x["_candidate"]["source_event_id"]): x
           for x in prior}
    merged = dict(old)
    added = changed = unchanged = retained = 0
    for candidate in candidates:
        key = (candidate["_candidate"]["platform_id"],
               candidate["_candidate"]["source_event_id"])
        before = merged.get(key)
        if before is None:
            merged[key] = candidate
            added += 1
        elif utc(candidate["scraped_at"]) > utc(before["scraped_at"]):
            merged[key] = candidate
            changed += 1
        else:
            unchanged += 1
    retained = sum(key not in {(x["_candidate"]["platform_id"],
                                x["_candidate"]["source_event_id"]) for x in candidates}
                   for key in old)
    rows = [merged[k] for k in sorted(merged)]
    return {
        "kind": "EVENTRADAR_MULTISOURCE_HISTORICAL_REVIEW_LKG_V1",
        "decision": "REVIEW_ONLY" if candidates else "HOLD_NO_VALID_NEW_SOURCE",
        "source_reader_qualified": len({
            r["candidate"]["_candidate"]["record_id"] for r in receipts
            if r["candidate"]["_candidate"]["record_id"] in qualified_ids
        }),
        "archived_native_receipt_qualified": len({
            r["candidate"]["_candidate"]["record_id"] for r in native_receipts
            if r["candidate"]["_candidate"]["record_id"] in qualified_ids
        }),
        "source_platforms": sorted({x["_candidate"]["platform_id"] for x in candidates}),
        "source_gates": sorted({r["gate"] for r in receipts + native_receipts}),
        "new_review": added, "changed_review": changed,
        "unchanged_review": unchanged, "retained_lkg": retained,
        "review_rows": rows, "rejected": rejected,
        "raw_pair_reviews_unattested": raw_pair_reviews,
        "raw_pair_identity_parsed_unattested": len(raw_pair_reviews),
        "source_review_receipts": source_receipts,
        "archived_native_receipts": [
            {k: v for k, v in r.items() if k != "candidate"}
            for r in native_receipts
            if r["candidate"]["_candidate"]["record_id"] in qualified_ids
        ],
        "source_review_field_count": sum(
            len(x["source_reader_fields"]) for x in source_receipts),
        "independent_native_detail_new": 0,
        "independently_accepted_fields": 0,
        "published_delta": 0, "native_get": 0,
        "cross_host_cas_attested": False,
        "commit_permitted": False, "scheduler_enabled": False,
        "formal_data_mutated": False,
        "release_state": HOLD,
    }


def write_isolated(plan_data, out, repo_root):
    """Atomic local artifact only; explicitly NOT a cross-host CAS/claim."""
    import os
    import tempfile
    root = Path(repo_root).resolve()
    target = Path(out).resolve()
    allowed = (root / "_isolated_review").resolve()
    if not target.is_relative_to(allowed) or target == allowed:
        raise ValueError("ISOLATED_OUTPUT_ONLY_HOLD")
    if plan_data.get("commit_permitted") is not False:
        raise ValueError("PUBLICATION_AUTHORITY_HOLD")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(plan_data, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".review-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return hashlib.sha256(data).hexdigest()


def load_previous_snapshot(path, expected_sha256, repo_root):
    """Load a SHA-pinned isolated LKG snapshot; never treat it as global CAS."""
    root = Path(repo_root).resolve()
    allowed = (root / "_isolated_review").resolve()
    target = Path(path).resolve()
    if not target.is_relative_to(allowed) or target == allowed:
        raise ValueError("PRIOR_SNAPSHOT_ISOLATION_HOLD")
    if (not isinstance(expected_sha256, str)
            or len(expected_sha256) != 64
            or any(c not in "0123456789abcdef" for c in expected_sha256)):
        raise ValueError("PRIOR_SNAPSHOT_SHA_FORMAT_HOLD")
    try:
        if target.stat().st_size > 10_000_000:
            raise ValueError("PRIOR_SNAPSHOT_SIZE_HOLD")
        raw = target.read_bytes()
    except OSError as exc:
        raise ValueError("PRIOR_SNAPSHOT_UNREADABLE_HOLD") from exc
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("PRIOR_SNAPSHOT_SHA_MISMATCH_HOLD")
    try:
        previous = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("PRIOR_SNAPSHOT_JSON_HOLD") from exc
    if (not isinstance(previous, dict)
            or previous.get("kind") != "EVENTRADAR_MULTISOURCE_HISTORICAL_REVIEW_LKG_V1"
            or previous.get("release_state") != HOLD
            or previous.get("decision") not in ("REVIEW_ONLY", "HOLD_NO_VALID_NEW_SOURCE")
            or any(previous.get(k) is not False for k in
                   ("commit_permitted", "scheduler_enabled", "formal_data_mutated",
                    "cross_host_cas_attested"))
            or any(type(previous.get(k)) is not int or previous[k] != 0
                   for k in ("native_get", "published_delta",
                             "independently_accepted_fields"))
            or not isinstance(previous.get("review_rows"), list)
            or len(previous["review_rows"]) > 2000):
        raise ValueError("PRIOR_SNAPSHOT_AUTHORITY_HOLD")
    rows = previous["review_rows"]
    ids = [r.get("_candidate", {}).get("record_id") for r in rows
           if isinstance(r, dict) and isinstance(r.get("_candidate"), dict)]
    if len(ids) != len(rows) or len(set(ids)) != len(ids):
        raise ValueError("PRIOR_SNAPSHOT_IDENTITY_HOLD")
    # plan() independently revalidates each retained row's source binding.
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--tainex-native-audits-dir", type=Path, default=None,
                    help="Local archived SHA-pinned audit.json copies only; no GET")
    ap.add_argument("--previous-plan", type=Path, default=None,
                    help="Previous isolated plan.json, never formal data")
    ap.add_argument("--previous-sha256", default=None,
                    help="Exact SHA256 of previous isolated plan.json")
    args = ap.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    if (args.previous_plan is None) != (args.previous_sha256 is None):
        raise ValueError("PRIOR_SNAPSHOT_PAIR_HOLD")
    if args.previous_plan is not None and "previous" in source:
        raise ValueError("AMBIGUOUS_PRIOR_LKG_HOLD")
    previous = (load_previous_snapshot(args.previous_plan, args.previous_sha256,
                                       Path.cwd())
                if args.previous_plan is not None
                else source.get("previous", []))
    result = plan(source["packets"], previous=previous,
                  as_of=utc(source["as_of"]),
                  archived_native=(archived_inputs(args.tainex_native_audits_dir)
                                   if args.tainex_native_audits_dir else []),
                  raw_pairs=source.get("raw_pairs", []))
    digest = write_isolated(result, args.output, Path.cwd())
    print(json.dumps({"decision": result["decision"],
                      "source_reader_qualified": result["source_reader_qualified"],
                      "independently_accepted_fields": 0,
                      "archived_native_receipt_qualified": result["archived_native_receipt_qualified"],
                      "native_get": 0, "published_delta": 0,
                      "raw_pair_identity_parsed_unattested": result["raw_pair_identity_parsed_unattested"],
                      "isolated_sha256": digest}, sort_keys=True))
    return 0 if (result["source_reader_qualified"] or
                 result["archived_native_receipt_qualified"]) else 49



# Source-claim blocker resolution: GitHub protected-ref reservation, not GET authority.
# A six-hour sliding exclusion cannot be enforced by ONE six-hour bucket ref:
# attempts on opposite sides of a bucket boundary would both succeed.
# Reserve current AND next buckets. Any two starts <6h apart overlap at
# least one ref; create-ref uniqueness makes at most one pair complete.
# A crash/partial reservation is NEVER cleaned up: availability loses to safety.
# This is a staging provider; live HTTP remains HOLD until independent ruleset
# rejection and cross-host tests are witnessed on real GitHub.
CLAIM_SLOT_SECONDS = 6 * 3600
CLAIM_REPO = "easonliu714/event_scraper_public"
CLAIM_SOURCES = frozenset(("tainex", "famiticket", "tmc", "opentix", "ticc", "tpac"))
CLAIM_RULESET_INCLUDE = "refs/heads/source-claims/*"
CLAIM_REQUIRED_RULES = frozenset(("update", "deletion", "non_fast_forward"))


def claim_ref_plan(source, github_server_at):
    """Two intersecting immutable reservations; not a permit for official GET."""
    if source not in CLAIM_SOURCES:
        raise ValueError("CLAIM_UNREGISTERED_SOURCE_HOLD")
    at = github_server_at
    if (type(at) is not datetime or at.tzinfo is None or
            at.utcoffset() is None):
        raise ValueError("CLAIM_SERVER_CLOCK_HOLD")
    bucket = int(at.astimezone(timezone.utc).timestamp()) // CLAIM_SLOT_SECONDS
    if bucket < 0:
        raise ValueError("CLAIM_SERVER_CLOCK_HOLD")
    return tuple("refs/heads/source-claims/" + source + "-b" +
                 str(i).zfill(10) for i in (bucket, bucket + 1))


def _claim_ruleset_verified(api):
    """Inspect actual active branch ruleset; absence or ambiguity is HOLD."""
    status, rows, _ = api("GET", "/repos/" + CLAIM_REPO + "/rulesets", None)
    if status != 200 or not isinstance(rows, list):
        raise ValueError("CLAIM_RULESET_LIST_HOLD")
    qualified = 0
    for row in rows:
        if not isinstance(row, dict) or type(row.get("id")) is not int:
            continue
        status, rule, _ = api(
            "GET", "/repos/" + CLAIM_REPO + "/rulesets/" + str(row["id"]), None)
        if status != 200 or not isinstance(rule, dict):
            raise ValueError("CLAIM_RULESET_DETAIL_HOLD")
        if rule.get("enforcement") != "active" or rule.get("target") != "branch":
            continue
        cond = rule.get("conditions")
        names = cond.get("ref_name") if isinstance(cond, dict) else None
        if not isinstance(names, dict):
            continue
        if CLAIM_RULESET_INCLUDE not in names.get("include", []):
            continue
        if rule.get("bypass_actors") not in ([], None):
            raise ValueError("CLAIM_RULESET_BYPASS_HOLD")
        types = {r.get("type") for r in rule.get("rules", [])
                 if isinstance(r, dict)}
        if not CLAIM_REQUIRED_RULES.issubset(types) or "creation" in types:
            raise ValueError("CLAIM_RULESET_RULES_HOLD")
        qualified += 1
    if qualified != 1:
        raise ValueError("CLAIM_RULESET_NOT_EXACTLY_ONE_ACTIVE_HOLD")


def reserve_protected_claim(source, anchor_sha, api):
    """Reserve two protected refs, with no retries/deletion and NO live GET permit.

    api(method, repository-relative path, JSON payload) must use authenticated
    GitHub REST and return (HTTP status, parsed JSON, GitHub HTTP Date as aware
    datetime). Only a controlled engineering host may supply it. This module
    does NOT provide a network transport, GitHub credential or public dispatch.
    """
    if (not isinstance(anchor_sha, str) or
            re.fullmatch(r"[0-9a-f]{40}", anchor_sha, re.ASCII) is None):
        raise ValueError("CLAIM_ANCHOR_SHA_HOLD")
    _claim_ruleset_verified(api)
    status, head, server_at = api(
        "GET", "/repos/" + CLAIM_REPO + "/git/ref/heads/main", None)
    if (status != 200 or not isinstance(head, dict) or
            not isinstance(head.get("object"), dict) or
            head["object"].get("sha") != anchor_sha):
        raise ValueError("CLAIM_ANCHOR_MAIN_DRIFT_HOLD")
    refs = claim_ref_plan(source, server_at)
    for ref in refs:
        status, created, at = api(
            "POST", "/repos/" + CLAIM_REPO + "/git/refs",
            {"ref": ref, "sha": anchor_sha})
        if status != 201 or not isinstance(created, dict) or created.get("ref") != ref:
            raise ValueError("CLAIM_CREATE_REF_COLLISION_OR_DENIED_HOLD")
        if claim_ref_plan(source, at) != refs:
            raise ValueError("CLAIM_SERVER_CLOCK_CROSSED_BUCKET_HOLD")
    for ref in refs:
        status, got, at = api(
            "GET", "/repos/" + CLAIM_REPO + "/git/ref/" +
            ref.removeprefix("refs/"), None)
        if (status != 200 or not isinstance(got, dict) or
                got.get("ref") != ref or
                not isinstance(got.get("object"), dict) or
                got["object"].get("sha") != anchor_sha or
                claim_ref_plan(source, at) != refs):
            raise ValueError("CLAIM_REF_READBACK_OR_CLOCK_HOLD")
    _claim_ruleset_verified(api)
    return {
        "source": source, "refs": list(refs), "anchor_sha": anchor_sha,
        "reserved_ref_count": 2,
        "decision": "HOLD_REAL_RULESET_NEGATIVE_AND_TWO_HOST_VERIFICATION",
        "claim_provider_candidate": True,
        "independent_cross_host_verified": False,
        "native_get_allowed": False, "source_ready": False,
        "published": False, "cleanup_allowed": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
