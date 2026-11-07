"""Reusable A/B source HTML -> strict identity -> isolated REVIEW snapshot bridge.

Caller-supplied HTML is never native HTTP evidence. This module cannot GET,
publish, create a Golden, or mutate the formal docs/ data pipeline.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from scripts import p30_ab_kktix_fuzhong_native as ticket
from scripts import p30_ntpc_artcenter_source as venue
from scripts import p30_candidate_review_pipeline as preview

MAX_HTML = 2 * 1024 * 1024
ATTESTATION = "CALLER_SUPPLIED_NOT_NATIVE"


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _observed(value):
    if not isinstance(value, str):
        raise ValueError("REVIEW_OBSERVED_AT_MISSING_HOLD")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None or date.utcoffset() is None:
            raise ValueError("timezone")
    except (ValueError, OverflowError) as exc:
        raise ValueError("REVIEW_OBSERVED_AT_INVALID_HOLD") from exc
    return value


def build_review_envelope(line, list_body, detail_body, observed_at_utc):
    """Run existing A KKTIX / B NTPC exact-ID parsers and preview normalizer.

    Returned hashes bind caller bytes, not a native fetch. No dates, room,
    ticket sessions or prices are promoted into preview display fields.
    """
    if line not in ("A", "B"):
        raise ValueError("REVIEW_SOURCE_LINE_HOLD")
    stamp = _observed(observed_at_utc)
    for body in (list_body, detail_body):
        if not isinstance(body, bytes) or not 0 < len(body) <= MAX_HTML:
            raise ValueError("REVIEW_BODY_TYPE_OR_CAP_HOLD")
    try:
        listing, detail = list_body.decode("utf-8"), detail_body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("REVIEW_BODY_UTF8_HOLD") from exc
    if line == "A":
        source = ticket.SOURCES["A_KIMU"]
        verdict = ticket.inspect_pair("A_KIMU", listing, detail)
        list_url, detail_url = source["list"], source["detail"]
        title, source_id, event_id = (source["title"], source["source_id"],
                                      source["event_id"])
        roles = list(verdict.get("field_roles", []))
        platform, kind = "KKTIX", "活動"
    else:
        verdict = venue.inspect_caller_html(listing, detail)
        list_url = venue.LIST_URL
        detail_url = venue.exact_detail(
            "/artcenter_chi/xmdoc/cont?sid=" + venue.SID +
            "&sq=&xsmsid=" + venue.XSMSID)
        title, source_id, event_id = (venue.TITLE,
            "NTPC_ARTCENTER_OFFICIAL_NOT_FORMAL_19_PLATFORM", venue.SID)
        roles = ["VENUE_ROOM_REVIEW"] if verdict["venue_room_review"] else []
        platform, kind = "新北市藝文中心", "展覽"
    digests = {"list_sha256": hashlib.sha256(list_body).hexdigest(),
               "detail_sha256": hashlib.sha256(detail_body).hexdigest()}
    envelope = {
        "kind": "EVENTRADAR_AB_ISOLATED_REVIEW_BRIDGE_V1",
        "line": line, "source_id": source_id, "source_event_id": event_id,
        "list_url": list_url, "detail_url": detail_url,
        "observed_at_utc": stamp, "body_digests": digests,
        "source_attestation": ATTESTATION, "native_get": 0,
        "native_body_lkg": 0, "formal_accepted_fields": 0,
        "golden": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
        "decision": "HOLD", "first_failure": verdict["first_failure"],
        "role_receipts": [], "candidate": None,
    }
    if verdict.get("same_id_review") != 1:
        return envelope
    raw = {
        "title": title, "url": detail_url, "platform": platform,
        "type": kind, "scraped_at": stamp,
        "_candidate": {
            "scope": "CANDIDATE_PREVIEW_ONLY",
            "decision": "REVIEW_WITH_HOLD",
            "record_id": source_id + ":" + event_id,
            "platform_id": source_id, "source_event_id": event_id,
            "source_class": "TICKET_PLATFORM" if line == "A" else "VENUE",
            "sources": [list_url, detail_url],
            "hold_reasons": [
                "CALLER_HTML_NOT_NATIVE_ATTESTED",
                "INDEPENDENT_FIELD_AUTHORITY_PENDING",
                "SHOW_DATE_SESSION_PRICE_NOT_VERIFIED",
            ],
            "formal_field_pass": False, "golden_accepted": False,
            "published": False,
        },
    }
    candidate, reasons = preview.normalize_record(raw)
    if reasons:
        envelope["first_failure"] = "PREVIEW_NORMALIZER_HOLD:" + ",".join(reasons)
        return envelope
    envelope["candidate"] = candidate
    envelope["role_receipts"] = [
        {"role": role, "source_url": detail_url,
         "body_sha256": digests["detail_sha256"],
         "observed_at_utc": stamp, "decision": "REVIEW",
         "native_attested": False, "formal_accepted": False}
        for role in sorted(set(roles))
    ]
    envelope["decision"] = "REVIEW_ONLY_NOT_NATIVE"
    envelope["first_failure"] = "NATIVE_ATTESTATION_AND_FIELD_AUTHORITY_PENDING"
    return envelope


def _validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != {"payload", "sha256"}:
        raise ValueError("REVIEW_SNAPSHOT_SCHEMA_HOLD")
    payload = snapshot["payload"]
    if not isinstance(payload, dict) or payload.get("decision") != "REVIEW_ONLY_NOT_NATIVE":
        raise ValueError("REVIEW_SNAPSHOT_NON_REVIEW_HOLD")
    if (payload.get("source_attestation") != ATTESTATION or
            payload.get("native_get") != 0 or
            payload.get("formal_accepted_fields") != 0 or
            payload.get("golden") != 0 or payload.get("published") != 0 or
            payload.get("release_state") != "HARD_HOLD_NO_PUBLICATION"):
        raise ValueError("REVIEW_SNAPSHOT_AUTHORITY_HOLD")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    if snapshot["sha256"] != digest:
        raise ValueError("REVIEW_SNAPSHOT_CHECKSUM_HOLD")
    return digest


def write_isolated_review_lkg(envelope, target, repo_root, expected_sha=None):
    """One-file checksum+atomic replace with fail-closed expected-content CAS.

    Only _isolated_review/ under the repo root is writable. HOLD never
    replaces last-known-good; existing files require their verified SHA.
    """
    root = Path(repo_root).resolve()
    dest = Path(target)
    if dest.name != "review_snapshot.json":
        raise ValueError("REVIEW_TARGET_NAME_HOLD")
    dest = dest.absolute()
    if (not dest.is_relative_to(root) or
            dest.relative_to(root).parts[:1] != ("_isolated_review",) or
            dest.is_symlink() or dest.parent.is_symlink()):
        raise ValueError("REVIEW_TARGET_ISOLATION_HOLD")
    if dest.parent.resolve() != (root / "_isolated_review").resolve():
        raise ValueError("REVIEW_TARGET_PARENT_HOLD")
    digest = _validate_snapshot({
        "payload": envelope, "sha256": hashlib.sha256(_canonical(envelope)).hexdigest()
    })
    if dest.exists():
        old = json.loads(dest.read_text(encoding="utf-8"))
        current = _validate_snapshot(old)
        if expected_sha != current:
            raise ValueError("REVIEW_LKG_CAS_MISMATCH_HOLD")
        # An acknowledged checksum is not permission to replace a different
        # source/event, roll back observation time, or silently rewrite bytes
        # at the same observation instant. Preserve the original LKG on HOLD.
        previous = old["payload"]
        identity = ("line", "source_id", "source_event_id",
                    "list_url", "detail_url")
        if any(previous.get(key) != envelope.get(key) for key in identity):
            raise ValueError("REVIEW_LKG_CROSS_IDENTITY_HOLD")
        prior_time = datetime.fromisoformat(
            _observed(previous.get("observed_at_utc")).replace("Z", "+00:00"))
        next_time = datetime.fromisoformat(
            _observed(envelope.get("observed_at_utc")).replace("Z", "+00:00"))
        if next_time < prior_time:
            raise ValueError("REVIEW_LKG_STALE_OBSERVATION_HOLD")
        if (next_time == prior_time and
                previous.get("body_digests") != envelope.get("body_digests")):
            raise ValueError("REVIEW_LKG_SAME_INSTANT_BODY_DRIFT_HOLD")
    elif expected_sha is not None:
        raise ValueError("REVIEW_LKG_CAS_MISSING_HOLD")
    dest.parent.mkdir(parents=True, exist_ok=True)
    blob = _canonical({"payload": envelope, "sha256": digest}) + b"\n"
    fd, temp = tempfile.mkstemp(prefix=".review-", dir=str(dest.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, dest)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return digest
