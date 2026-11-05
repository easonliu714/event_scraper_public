"""Offline A/B official-source replay into the existing sealed REVIEW LKG.

No network, checkout, publisher, or formal field acceptance. A caller-owned
manifest binds two exact public URLs, complete HTML bytes, SHA256 and original
observation timestamps; this CLI cannot attest a native GET.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from scripts.p30_l7_field_golden_readiness import (
    OPENTIX_ROTATION_DETAIL,
    OPENTIX_ROTATION_LIST,
    SONGSHAN_PUBLIC_LIST,
    load_isolated_review_lkg,
    run_opentix_existing_id_review_lkg,
    run_songshan_uuid_review_lkg,
)

SECOND_UUID = "3b2101fd-cbb3-48ec-b23c-496880df5626"
SECOND_TITLE = "STAR ON THE MOVE 2026 臺北採購媒合與展售會"
MAX_SOURCE_BYTES = 524288
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def _safe_input_file(value, repo_root):
    path = Path(value)
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("REPLAY_INPUT_ABSOLUTE_NON_SYMLINK_REQUIRED")
    resolved = path.resolve(strict=True)
    if resolved == repo_root or resolved.is_relative_to(repo_root):
        raise ValueError("REPLAY_RAW_SOURCE_INSIDE_REPO_HOLD")
    if not resolved.is_file() or not 0 < resolved.stat().st_size <= MAX_SOURCE_BYTES:
        raise ValueError("REPLAY_INPUT_FILE_SIZE_OR_TYPE_HOLD")
    return resolved


def read_preacquired_manifest(manifest_file, repo_root, line, now_utc=None):
    """Validate complete caller-owned bytes, original clock, exact URL and SHA."""
    root = Path(repo_root).resolve(strict=True)
    manifest_path = _safe_input_file(manifest_file, root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or
            set(manifest) != {"kind", "transport", "sources"} or
            manifest["kind"] != "P30_PREACQUIRED_OFFICIAL_HTML_V1" or
            manifest["transport"] != "CALLER_SUPPLIED_NOT_NATIVE_ATTESTED" or
            not isinstance(manifest["sources"], list) or
            len(manifest["sources"]) != 2):
        raise ValueError("REPLAY_MANIFEST_SHAPE_OR_TRANSPORT_HOLD")
    urls = ((OPENTIX_ROTATION_LIST, OPENTIX_ROTATION_DETAIL)
            if line == "A" else
            (SONGSHAN_PUBLIC_LIST,
             SONGSHAN_PUBLIC_LIST + "/activity/" + SECOND_UUID))
    now = now_utc or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("REPLAY_CLOCK_HOLD")
    result, stamps, receipts = {}, [], []
    for item, url in zip(manifest["sources"], urls):
        if (not isinstance(item, dict) or
                set(item) != {"url", "path", "sha256", "observed_at_utc"} or
                item["url"] != url or not isinstance(item["sha256"], str) or
                not SHA_PATTERN.fullmatch(item["sha256"])):
            raise ValueError("REPLAY_EXACT_URL_OR_SHA_MANIFEST_HOLD")
        stamp_raw = item["observed_at_utc"]
        if not isinstance(stamp_raw, str):
            raise ValueError("REPLAY_OBSERVATION_TIME_HOLD")
        stamp = datetime.fromisoformat(stamp_raw.replace("Z", "+00:00"))
        if stamp.utcoffset() is None or not 0 <= (now - stamp).total_seconds() <= 86400:
            raise ValueError("REPLAY_STALE_FUTURE_OR_NAIVE_TIME_HOLD")
        raw = _safe_input_file(item["path"], root).read_bytes()
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


def replay(line, manifest, destination, repo_root, now_utc=None):
    """Run existing canonical A/B adapters; never overwrite an invalid prior LKG."""
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
        bodies, receipts, stamp = read_preacquired_manifest(
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
                event_uuid=SECOND_UUID, event_title=SECOND_TITLE,
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline exact-source A/B replay; NO GET")
    parser.add_argument("--line", choices=("A", "B"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--isolated-output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = replay(args.line, args.manifest, args.isolated_output, args.repo_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["decision"] == "REVIEW_ONLY_NONPUBLISHING" else 49


if __name__ == "__main__":
    raise SystemExit(main())
