"""Reusable A/B source HTML -> strict identity -> isolated REVIEW snapshot bridge.

Caller-supplied HTML is never native HTTP evidence. This module cannot GET,
publish, create a Golden, or mutate the formal docs/ data pipeline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from scripts import p30_ab_kktix_fuzhong_native as ticket
from scripts import p30_ntpc_artcenter_source as venue
from scripts import p30_tpac_event_source as tpac_event
from scripts import p30_cloudgate_native_gate as cloudgate
from scripts import p30_ab_opentix_ticc_native_once as opentix
from scripts import p30_candidate_review_pipeline as preview

MAX_HTML = 2 * 1024 * 1024
ATTESTATION = "CALLER_SUPPLIED_NOT_NATIVE"
# Explicit reuse of existing exact-ID parsers; caller bytes never attest native GET.
ADAPTER_LINES = {"A_KIMU": "A", "A_UDN": "A", "A_ACCUPASS": "A", "A_OPENTIX": "A",
                 "B_NTPC": "B", "B_CERAMICS": "B", "B_ZEPP_TAKASE": "B",
                 "B_TPAC_EVENT2072": "B", "B_CLOUDGATE": "B",
                 "B_TAINEX": "B"}
DEFAULT_ADAPTER = {"A": "A_KIMU", "B": "B_NTPC"}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _observed(value):
    if not isinstance(value, str):
        raise ValueError("REVIEW_OBSERVED_AT_MISSING_HOLD")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Manifest timestamps are explicitly UTC; a local offset must not
        # silently enter source provenance as observed_at_utc.
        if (date.tzinfo is None or date.utcoffset() is None or
                date.utcoffset().total_seconds() != 0):
            raise ValueError("timezone")
    except (ValueError, OverflowError) as exc:
        raise ValueError("REVIEW_OBSERVED_AT_INVALID_HOLD") from exc
    return value


def build_review_envelope(line, list_body, detail_body, observed_at_utc, adapter_key=None):
    """Run existing A KKTIX / B NTPC exact-ID parsers and preview normalizer.

    Returned hashes bind caller bytes, not a native fetch. No dates, room,
    ticket sessions or prices are promoted into preview display fields.
    """
    if line not in ("A", "B"):
        raise ValueError("REVIEW_SOURCE_LINE_HOLD")
    adapter_key = adapter_key or DEFAULT_ADAPTER[line]
    if ADAPTER_LINES.get(adapter_key) != line:
        raise ValueError("REVIEW_ADAPTER_LINE_HOLD")
    stamp = _observed(observed_at_utc)
    for body in (list_body, detail_body):
        if not isinstance(body, bytes) or not 0 < len(body) <= MAX_HTML:
            raise ValueError("REVIEW_BODY_TYPE_OR_CAP_HOLD")
    try:
        listing, detail = list_body.decode("utf-8"), detail_body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("REVIEW_BODY_UTF8_HOLD") from exc
    # Official OPENTIX identity is source #05; caller HTML is never native.
    if adapter_key == "A_OPENTIX":
        source = opentix.SOURCES["A"]
        verdict = opentix.inspect_pair("A", listing, detail)
        list_url, detail_url = source["list"], source["detail"]
        title, source_id, event_id = (
            source["title"], source["source_id"], source["event_id"])
        # Preserve source-owned event-local roles, never native attestation
        # from caller-provided HTML.
        roles = list(verdict.get("field_roles", []))
        platform, kind = "OPENTIX", "活動"
    elif adapter_key not in ("B_NTPC", "B_TPAC_EVENT2072", "B_CLOUDGATE"):
        # The same source-local parser also handles alternate A/B official
        # LIST→DETAIL identities. Never promote LIST roles as DETAIL receipts.
        source = ticket.SOURCES[adapter_key]
        verdict = ticket.inspect_pair(adapter_key, listing, detail)
        list_url, detail_url = source["list"], source["detail"]
        title, source_id, event_id = (source["title"], source["source_id"],
                                      source["event_id"])
        roles = list(verdict.get("field_roles", []))
        platform, kind = {
            "A_KIMU": ("KKTIX", "活動"),
            "A_UDN": ("UDN售票網", "活動"),
            "A_ACCUPASS": ("ACCUPASS", "活動"),
            "B_CERAMICS": ("鶯歌陶瓷博物館", "展覽"),
            "B_ZEPP_TAKASE": ("Zepp New Taipei", "活動"),
            # Reuse the proven first-party exact-/event/691 parser; this is
            # caller-body REVIEW only, not the prior one-shot native receipt.
            "B_TAINEX": ("南港展覽館", "展覽"),
        }[adapter_key]
    elif adapter_key == "B_CLOUDGATE":
        # Reuse the existing official exact-1680 parser; the postponement
        # remains a REVIEW role, never a verified performance Session/date.
        verdict = cloudgate.inspect_pair(listing, detail)
        list_url = cloudgate.LIST_URL
        # Exact official LIST href owns REVIEW provenance, not a title alias.
        detail_url = verdict.get("list_derived_detail_url", cloudgate.DETAIL_URL)
        title, source_id, event_id = (
            cloudgate.TITLE,
            "CLOUDGATE_THEATER_OFFICIAL_NOT_FORMAL_19_PLATFORM",
            cloudgate.SOURCE_EVENT_ID)
        roles = ["EVENT_LOCAL_TITLE_REVIEW"] if verdict["same_id_review"] else []
        if verdict.get("postponement_review") == 1:
            roles.append("VENUE_POSTPONEMENT_REVIEW_NOT_SESSION")
        platform, kind = "雲門劇場", "活動"
    elif adapter_key == "B_TPAC_EVENT2072":
        verdict = tpac_event.inspect_caller_html(listing, detail)
        list_url, detail_url = tpac_event.LIST_URL, tpac_event.DETAIL_URL
        title, source_id, event_id = (tpac_event.TITLE, tpac_event.SOURCE_ID,
                                      tpac_event.EVENT_ID)
        roles = list(verdict["field_roles"])
        platform, kind = "臺北表演藝術中心", "活動"
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
        "line": line, "adapter_key": adapter_key,
        "source_id": source_id, "source_event_id": event_id,
        "list_url": list_url, "detail_url": detail_url,
        "observed_at_utc": stamp, "body_digests": digests,
        "source_attestation": ATTESTATION, "native_get": 0,
        "native_body_lkg": 0, "formal_accepted_fields": 0,
        "golden": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
        "decision": "HOLD", "first_failure": verdict["first_failure"],
        "role_receipts": [], "direct_ticket_edge": None, "candidate": None,
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
    if adapter_key in ("B_TPAC_EVENT2072", "B_CLOUDGATE"):
        # Source-owned conflict or postponement remains REVIEW, never a Session.
        # The disagreement is a HOLD, not a Session/date/price receipt.
        raw["_candidate"]["hold_reasons"].append(verdict["first_failure"])
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
    # Zepp venue rid is NOT the KKTIX ticket event ID. Preserve the exact
    # official event-local outbound link as a separate REVIEW edge, never
    # infer ticket Session, performance date, availability or eligible price.
    if (adapter_key == "B_ZEPP_TAKASE"
            and verdict.get("ticket_event_edge_review") == 1):
        envelope["direct_ticket_edge"] = {
            "role": "VENUE_TO_TICKET_EVENT_EDGE_REVIEW_NOT_SESSION",
            "source_url": detail_url,
            "target_url": ticket.SOURCES[adapter_key]["public_ticket_event"],
            "body_sha256": digests["detail_sha256"],
            "observed_at_utc": stamp,
            "native_attested": False, "formal_accepted": False,
        }
    envelope["decision"] = "REVIEW_ONLY_NOT_NATIVE"
    envelope["first_failure"] = (verdict["first_failure"]
        if adapter_key in ("B_TPAC_EVENT2072", "B_CLOUDGATE")
        else "NATIVE_ATTESTATION_AND_FIELD_AUTHORITY_PENDING")
    return envelope


def _validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != {"payload", "sha256"}:
        raise ValueError("REVIEW_SNAPSHOT_SCHEMA_HOLD")
    payload = snapshot["payload"]
    if not isinstance(payload, dict) or payload.get("decision") != "REVIEW_ONLY_NOT_NATIVE":
        raise ValueError("REVIEW_SNAPSHOT_NON_REVIEW_HOLD")
    adapter = payload.get("adapter_key")
    if ADAPTER_LINES.get(adapter) != payload.get("line"):
        raise ValueError("REVIEW_SNAPSHOT_ADAPTER_IDENTITY_HOLD")
    if adapter == "A_OPENTIX":
        source = opentix.SOURCES["A"]
        expected = (source["list"], source["detail"],
                    source["source_id"], source["event_id"])
    elif adapter == "B_NTPC":
        expected = (venue.LIST_URL, venue.exact_detail(
            "/artcenter_chi/xmdoc/cont?sid=" + venue.SID +
            "&sq=&xsmsid=" + venue.XSMSID),
            "NTPC_ARTCENTER_OFFICIAL_NOT_FORMAL_19_PLATFORM", venue.SID)
    elif adapter == "B_CLOUDGATE":
        if payload.get("detail_url") not in cloudgate.DETAIL_URLS:
            raise ValueError("REVIEW_SNAPSHOT_SOURCE_IDENTITY_HOLD")
        expected = (cloudgate.LIST_URL, payload["detail_url"],
                    "CLOUDGATE_THEATER_OFFICIAL_NOT_FORMAL_19_PLATFORM",
                    cloudgate.SOURCE_EVENT_ID)
    elif adapter == "B_TPAC_EVENT2072":
        expected = (tpac_event.LIST_URL, tpac_event.DETAIL_URL,
                    tpac_event.SOURCE_ID, tpac_event.EVENT_ID)
    else:
        source = ticket.SOURCES[adapter]
        expected = (source["list"], source["detail"],
                    source["source_id"], source["event_id"])
    if tuple(payload.get(k) for k in ("list_url", "detail_url",
            "source_id", "source_event_id")) != expected:
        raise ValueError("REVIEW_SNAPSHOT_SOURCE_IDENTITY_HOLD")
    if (payload.get("source_attestation") != ATTESTATION or
            payload.get("native_get") != 0 or
            payload.get("native_body_lkg") != 0 or
            payload.get("formal_accepted_fields") != 0 or
            payload.get("golden") != 0 or payload.get("published") != 0 or
            payload.get("release_state") != "HARD_HOLD_NO_PUBLICATION"):
        raise ValueError("REVIEW_SNAPSHOT_AUTHORITY_HOLD")
    # The durable REVIEW envelope is a security boundary: top-level HOLD
    # cannot mask a nested candidate that claims formal publication.
    candidate = payload.get("candidate")
    meta = candidate.get("_candidate") if isinstance(candidate, dict) else None
    if (not isinstance(meta, dict) or
            meta.get("scope") != "CANDIDATE_PREVIEW_ONLY" or
            meta.get("decision") not in ("REVIEW", "REVIEW_WITH_HOLD") or
            meta.get("platform_id") != payload.get("source_id") or
            meta.get("source_event_id") != payload.get("source_event_id") or
            meta.get("record_id") != str(payload.get("source_id")) + ":" +
                str(payload.get("source_event_id")) or
            candidate.get("url") != payload.get("detail_url") or
            any(meta.get(k) is not False for k in
                ("formal_field_pass", "golden_accepted", "published")) or
            meta.get("sessions") != [] or meta.get("ticket_session_id") is not None or
            meta.get("inventory") is not None):
        raise ValueError("REVIEW_SNAPSHOT_NESTED_AUTHORITY_HOLD")
    # Caller HTML is not independent field provenance. Even a recomputed
    # checksum cannot authorize a price, show date, venue, remote image or
    # arbitrary preview property in this non-native bridge.
    allowed_preview_keys = {
        "title", "url", "platform", "type", "scraped_at",
        "date", "location", "price", "description", "region",
        "img_url", "_candidate",
    }
    expected_title = (
        opentix.SOURCES["A"]["title"] if adapter == "A_OPENTIX" else
        venue.TITLE if adapter == "B_NTPC" else
        tpac_event.TITLE if adapter == "B_TPAC_EVENT2072" else
        cloudgate.TITLE if adapter == "B_CLOUDGATE" else
        ticket.SOURCES[adapter]["title"]
    )
    if (set(candidate) != allowed_preview_keys or
            candidate.get("title") != expected_title or
            candidate.get("scraped_at") != payload.get("observed_at_utc") or
            any(candidate.get(key) != "未確認" for key in
                ("date", "location", "price", "description", "region")) or
            candidate.get("img_url") is not None or
            meta.get("field_evidence") != {} or
            meta.get("sources") != [payload.get("list_url"),
                                   payload.get("detail_url")]):
        raise ValueError("REVIEW_SNAPSHOT_PREVIEW_FIELD_AUTHORITY_HOLD")
    receipts = payload.get("role_receipts")
    if not isinstance(receipts, list) or any(
            not isinstance(item, dict) or
            item.get("source_url") != payload.get("detail_url") or
            item.get("body_sha256") != payload.get("body_digests", {}).get("detail_sha256") or
            item.get("observed_at_utc") != payload.get("observed_at_utc") or
            item.get("decision") != "REVIEW" or
            item.get("native_attested") is not False or
            item.get("formal_accepted") is not False or
            not isinstance(item.get("role"), str) or not item["role"]
            for item in receipts):
        raise ValueError("REVIEW_SNAPSHOT_ROLE_PROVENANCE_HOLD")
    # A ticket link is a separately scoped venue edge; its target is never
    # treated as this venue's event ID or as a verified ticket Session.
    edge = payload.get("direct_ticket_edge")
    if edge is not None:
        if adapter != "B_ZEPP_TAKASE" or edge != {
                "role": "VENUE_TO_TICKET_EVENT_EDGE_REVIEW_NOT_SESSION",
                "source_url": payload["detail_url"],
                "target_url": ticket.SOURCES[adapter]["public_ticket_event"],
                "body_sha256": payload.get("body_digests", {}).get("detail_sha256"),
                "observed_at_utc": payload.get("observed_at_utc"),
                "native_attested": False, "formal_accepted": False}:
            raise ValueError("REVIEW_SNAPSHOT_TICKET_EDGE_AUTHORITY_HOLD")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    if snapshot["sha256"] != digest:
        raise ValueError("REVIEW_SNAPSHOT_CHECKSUM_HOLD")
    return digest


def preflight_review_lkg_transition(prior, envelope, expected_sha=None):
    """Pure A/B per-slot transition guard; shared by pair preflight and writer.

    The prior snapshot must be checksum-valid. A mismatched CAS, identity,
    timestamp or role set is HOLD before any durable pair slot is touched.
    A second check under the per-slot writer lease still protects TOCTOU.
    """
    if prior is not None:
        current = _validate_snapshot(prior)
        if expected_sha != current:
            raise ValueError("REVIEW_LKG_CAS_MISMATCH_HOLD")
        # An acknowledged checksum is not permission to replace a different
        # source/event, roll back observation time, or silently rewrite bytes
        # at the same observation instant. Preserve the original LKG on HOLD.
        previous = prior["payload"]
        identity = ("line", "adapter_key", "source_id", "source_event_id",
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
        # A later same-ID source observation may add verified REVIEW roles,
        # but cannot silently downgrade an already durable role. This is an
        # incremental diff gate, not independent FIELD acceptance.
        prior_roles = {item["role"] for item in previous["role_receipts"]}
        next_roles = {item["role"] for item in envelope["role_receipts"]}
        if not prior_roles.issubset(next_roles):
            raise ValueError("REVIEW_LKG_ROLE_REGRESSION_HOLD")
        if next_time == prior_time and prior_roles != next_roles:
            raise ValueError("REVIEW_LKG_SAME_INSTANT_ROLE_DRIFT_HOLD")
    elif expected_sha is not None:
        raise ValueError("REVIEW_LKG_CAS_MISSING_HOLD")

def write_isolated_review_lkg(envelope, target, repo_root, expected_sha=None):
    """Serialize read/CAS/replace per slot; atomic replace alone is not CAS.

    Exclusive mkdir is cross-process and fail-closed. A stale or occupied
    lease is HOLD (no retry/steal). Separate A/B slots have separate leases.
    """
    root = Path(repo_root).resolve()
    dest = Path(target).absolute()
    isolation = root / "_isolated_review"
    line, adapter = envelope.get("line"), envelope.get("adapter_key")
    if ADAPTER_LINES.get(adapter) != line:
        raise ValueError("REVIEW_TARGET_ADAPTER_HOLD")
    allowed = {
        isolation / "review_snapshot.json",
        isolation / line / "review_snapshot.json",
        isolation / line / adapter / "review_snapshot.json",
    }
    if (dest not in allowed or isolation.is_symlink()
            or (isolation / line).is_symlink()
            or dest.parent.is_symlink() or dest.is_symlink()
            or not dest.parent.resolve().is_relative_to(root)):
        raise ValueError("REVIEW_TARGET_ISOLATION_HOLD")
    dest.parent.mkdir(parents=True, exist_ok=True)
    lease = dest.parent / ".review_snapshot.lock"
    try:
        lease.mkdir()
    except FileExistsError as exc:
        raise ValueError("REVIEW_LKG_CONCURRENT_WRITER_HOLD") from exc
    try:
        return _write_isolated_review_lkg_locked(
            envelope, dest, root, expected_sha)
    finally:
        lease.rmdir()


def _write_isolated_review_lkg_locked(envelope, target, repo_root, expected_sha=None):
    """One-file checksum+atomic replace with fail-closed expected-content CAS.

    Only _isolated_review/ under the repo root is writable. HOLD never
    replaces last-known-good; existing files require their verified SHA.
    """
    root = Path(repo_root).resolve()
    dest = Path(target).absolute()
    isolation = root / "_isolated_review"
    # A and B require distinct durable LKG slots: one global file made the
    # second stream fail CROSS_IDENTITY despite a valid same-event REVIEW.
    # Preserve the legacy single-slot path for existing callers, but require
    # an exact line-owned slot for the executable manifest bridge.
    line, adapter = envelope.get("line"), envelope.get("adapter_key")
    if ADAPTER_LINES.get(adapter) != line:
        raise ValueError("REVIEW_TARGET_ADAPTER_HOLD")
    allowed = {
        isolation / "review_snapshot.json",
        isolation / line / "review_snapshot.json",
        isolation / line / adapter / "review_snapshot.json",
    }
    if dest.name != "review_snapshot.json":
        raise ValueError("REVIEW_TARGET_NAME_HOLD")
    if (dest not in allowed or isolation.is_symlink()
            or (isolation / line).is_symlink()
            or dest.parent.is_symlink() or dest.is_symlink()
            or not dest.parent.resolve().is_relative_to(root)):
        raise ValueError("REVIEW_TARGET_ISOLATION_HOLD")
    digest = _validate_snapshot({
        "payload": envelope, "sha256": hashlib.sha256(_canonical(envelope)).hexdigest()
    })
    prior = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else None
    preflight_review_lkg_transition(prior, envelope, expected_sha)
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

# A caller manifest binds bytes and exact event identity, but cannot attest
# native transport. No network, production feed or publisher is reachable here.
MANIFEST_KEYS = frozenset((
    "line", "source_id", "source_event_id", "list_url", "detail_url",
    "list_sha256", "detail_sha256", "observed_at_utc", "source_attestation"))
ALT_MANIFEST_KEYS = MANIFEST_KEYS | {"adapter_key"}


def replay_manifest_to_isolated_lkg(manifest, list_body, detail_body,
                                    repo_root, expected_sha=None):
    """Executable A/B parser -> preview normalizer -> checksum/CAS REVIEW."""
    if not isinstance(manifest, dict) or set(manifest) not in (
            MANIFEST_KEYS, ALT_MANIFEST_KEYS):
        raise ValueError("REVIEW_MANIFEST_SCHEMA_HOLD")
    adapter = manifest.get("adapter_key")
    if adapter is not None and ADAPTER_LINES.get(adapter) != manifest.get("line"):
        raise ValueError("REVIEW_MANIFEST_ADAPTER_LINE_HOLD")
    if manifest["source_attestation"] != ATTESTATION:
        raise ValueError("REVIEW_MANIFEST_NATIVE_CLAIM_HOLD")
    for body in (list_body, detail_body):
        if not isinstance(body, bytes) or not 0 < len(body) <= MAX_HTML:
            raise ValueError("REVIEW_MANIFEST_BODY_CAP_HOLD")
    envelope = build_review_envelope(
        manifest["line"], list_body, detail_body,
        manifest["observed_at_utc"], adapter_key=adapter)
    for key in ("line", "source_id", "source_event_id", "list_url", "detail_url"):
        if manifest[key] != envelope[key]:
            raise ValueError("REVIEW_MANIFEST_EVENT_IDENTITY_HOLD")
    for key in ("list_sha256", "detail_sha256"):
        if manifest[key] != envelope["body_digests"][key]:
            raise ValueError("REVIEW_MANIFEST_BODY_SHA_HOLD")
    if envelope["decision"] != "REVIEW_ONLY_NOT_NATIVE":
        return {"decision": "HOLD", "first_failure": envelope["first_failure"],
                "snapshot_sha256": None, "native_get": 0,
                "formal_accepted_fields": 0, "golden": 0, "published": 0}
    root = Path(repo_root).resolve()
    # An alternate source in the same line gets its own durable CAS slot.
    slot = root / "_isolated_review" / manifest["line"]
    if adapter is not None:
        slot = slot / envelope["adapter_key"]
    target = slot / "review_snapshot.json"
    digest = write_isolated_review_lkg(envelope, target, root, expected_sha)
    saved = json.loads(target.read_text(encoding="utf-8"))
    if _validate_snapshot(saved) != digest:
        raise ValueError("REVIEW_LKG_READBACK_HOLD")
    return {"decision": "REVIEW_ONLY_NOT_NATIVE", "snapshot_sha256": digest,
            "native_get": 0, "source_event_id": envelope["source_event_id"],
            "role_receipts": len(envelope["role_receipts"]),
            "direct_ticket_edge_review": int(envelope["direct_ticket_edge"] is not None),
            "formal_accepted_fields": 0, "golden": 0, "published": 0}


def _isolated_inbox_file(repo_root, supplied, max_bytes):
    root = Path(repo_root).resolve()
    isolation = root / "_isolated_review"
    inbox = isolation / "inbox"
    path = Path(supplied).absolute()
    # The inbox is read-only input but remains a trust boundary. A symlinked
    # isolation ancestor otherwise permits reading files outside repo_root.
    if (isolation.is_symlink() or inbox.is_symlink() or
            path.is_symlink() or not inbox.resolve().is_relative_to(root) or
            path.parent.resolve() != inbox.resolve() or
            not path.resolve().is_relative_to(root) or
            not path.is_relative_to(root) or not path.is_file()):
        raise ValueError("REVIEW_INBOX_PATH_HOLD")
    with path.open("rb") as stream:
        data = stream.read(max_bytes + 1)
    if not 0 < len(data) <= max_bytes:
        raise ValueError("REVIEW_INBOX_SIZE_HOLD")
    return data


def main(argv=None):
    """Offline CLI: input files restricted to _isolated_review/inbox."""
    parser = argparse.ArgumentParser(description="A/B REVIEW replay, NO GET/NO PUBLISH")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--list-html", required=True)
    parser.add_argument("--detail-html", required=True)
    parser.add_argument("--expected-sha")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    manifest = json.loads(_isolated_inbox_file(root, args.manifest, 8192))
    listing = _isolated_inbox_file(root, args.list_html, MAX_HTML)
    detail = _isolated_inbox_file(root, args.detail_html, MAX_HTML)
    result = replay_manifest_to_isolated_lkg(
        manifest, listing, detail, root, args.expected_sha)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["decision"] == "REVIEW_ONLY_NOT_NATIVE" else 49


if __name__ == "__main__":
    raise SystemExit(main())
