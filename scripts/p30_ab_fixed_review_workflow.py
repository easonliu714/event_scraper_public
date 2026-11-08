"""Fixed A+B source-owned LIST -> same-ID DETAIL -> REVIEW LKG handoff.

This is an OFFLINE caller-body workflow, never a native HTTP receipt. It does
not touch docs/, Golden, the production scraper, or the publisher. Both lines
are preflighted before either durable REVIEW slot is modified; subsequent
per-slot commits retain the bridge's lease, CAS, checksum and atomic readback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from scripts import p30_review_bridge as bridge

MANIFEST_FIELDS = (
    "line", "adapter_key", "source_id", "source_event_id",
    "list_url", "detail_url", "observed_at_utc", "source_attestation",
    "list_sha256", "detail_sha256",
)


def _prepare_line(root, line, supplied):
    """Preflight one complete source-owned pair without mutating any LKG."""
    if not isinstance(supplied, dict) or set(supplied) != {
            "manifest", "list_html", "detail_html", "expected_sha"}:
        raise ValueError("AB_FIXED_INPUT_SCHEMA_HOLD")
    manifest = json.loads(bridge._isolated_inbox_file(
        root, supplied["manifest"], 8192))
    listing = bridge._isolated_inbox_file(
        root, supplied["list_html"], bridge.MAX_HTML)
    detail = bridge._isolated_inbox_file(
        root, supplied["detail_html"], bridge.MAX_HTML)
    if not isinstance(manifest, dict) or set(manifest) != set(MANIFEST_FIELDS):
        raise ValueError("AB_FIXED_MANIFEST_SCHEMA_HOLD")
    if (manifest["line"] != line or
            bridge.ADAPTER_LINES.get(manifest["adapter_key"]) != line or
            manifest["source_attestation"] != bridge.ATTESTATION):
        raise ValueError("AB_FIXED_SOURCE_AUTHORITY_HOLD")
    envelope = bridge.build_review_envelope(
        line, listing, detail, manifest["observed_at_utc"],
        adapter_key=manifest["adapter_key"])
    for key in ("line", "adapter_key", "source_id", "source_event_id",
                "list_url", "detail_url", "observed_at_utc",
                "source_attestation"):
        if manifest[key] != envelope[key]:
            raise ValueError("AB_FIXED_EXACT_IDENTITY_HOLD")
    for key, body in (("list_sha256", listing), ("detail_sha256", detail)):
        if manifest[key] != hashlib.sha256(body).hexdigest():
            raise ValueError("AB_FIXED_BODY_DIGEST_HOLD")
    if envelope["decision"] != "REVIEW_ONLY_NOT_NATIVE":
        raise ValueError("AB_FIXED_EVENT_LOCAL_HOLD:" + envelope["first_failure"])
    if (envelope["native_get"] != 0 or envelope["native_body_lkg"] != 0 or
            envelope["formal_accepted_fields"] != 0 or
            envelope["golden"] != 0 or envelope["published"] != 0):
        raise ValueError("AB_FIXED_RELEASE_AUTHORITY_HOLD")

    target = (root / "_isolated_review" / line /
              manifest["adapter_key"] / "review_snapshot.json")
    isolation = root / "_isolated_review"
    if (isolation.is_symlink() or (isolation / line).is_symlink() or
            target.parent.is_symlink() or target.is_symlink() or
            not target.parent.resolve().is_relative_to(root)):
        raise ValueError("AB_FIXED_TARGET_ISOLATION_HOLD")
    expected = supplied["expected_sha"]
    if expected is not None and (
            not isinstance(expected, str) or
            not re.fullmatch(r"[0-9a-f]{64}", expected)):
        raise ValueError("AB_FIXED_EXPECTED_SHA_HOLD")
    # Validate the candidate and BOTH transition contracts before A can commit.
    # The writer repeats the same transition check under its slot lease.
    bridge._validate_snapshot({
        "payload": envelope,
        "sha256": hashlib.sha256(bridge._canonical(envelope)).hexdigest(),
    })
    prior = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    try:
        bridge.preflight_review_lkg_transition(prior, envelope, expected)
    except ValueError as exc:
        # Preserve existing A/B CLI HOLD codes while sharing the strict writer
        # transition guard. New timestamp/role failures retain their codes.
        prior_codes = {
            "REVIEW_LKG_CAS_MISMATCH_HOLD": "AB_FIXED_PREFLIGHT_CAS_HOLD",
            "REVIEW_LKG_CAS_MISSING_HOLD": "AB_FIXED_PREFLIGHT_MISSING_LKG_HOLD",
            "REVIEW_LKG_CROSS_IDENTITY_HOLD": "AB_FIXED_PREFLIGHT_CROSS_ID_HOLD",
        }
        raise ValueError(prior_codes.get(str(exc), str(exc))) from exc
    return manifest, listing, detail, expected


def _write_pair_receipt(root, ready, results):
    """Seal historical A+B REVIEW LKG readbacks without claiming native source.

    A content-addressed receipt is immutable, binds both exact source IDs,
    manifests, body digests, role names and snapshot SHAs, and never asserts
    atomic two-slot publication. Any collision or drift is fail-closed.
    """
    isolation = root / "_isolated_review"
    directory = isolation / "_pair_receipts"
    if (isolation.is_symlink() or directory.is_symlink() or
            not directory.resolve().is_relative_to(root)):
        raise ValueError("AB_FIXED_PAIR_TARGET_ISOLATION_HOLD")
    evidence = {}
    for line in ("A", "B"):
        manifest, _, _, _ = ready[line]
        target = isolation / line / manifest["adapter_key"] / "review_snapshot.json"
        if (target.is_symlink() or
                not target.parent.resolve().is_relative_to(root)):
            raise ValueError("AB_FIXED_PAIR_TARGET_ISOLATION_HOLD")
        snapshot = json.loads(target.read_text(encoding="utf-8"))
        if bridge._validate_snapshot(snapshot) != results[line]["snapshot_sha256"]:
            raise ValueError("AB_FIXED_PAIR_READBACK_DRIFT_HOLD")
        payload = snapshot["payload"]
        identity = ("line", "adapter_key", "source_id", "source_event_id",
                    "list_url", "detail_url", "observed_at_utc",
                    "source_attestation")
        if (any(payload.get(key) != manifest[key] for key in identity) or
                payload.get("body_digests") != {
                    "list_sha256": manifest["list_sha256"],
                    "detail_sha256": manifest["detail_sha256"]}):
            raise ValueError("AB_FIXED_PAIR_MANIFEST_PARITY_HOLD")
        evidence[line] = {
            **{key: manifest[key] for key in identity},
            "body_digests": payload["body_digests"],
            "snapshot_sha256": results[line]["snapshot_sha256"],
            "roles": [item["role"] for item in payload["role_receipts"]],
        }
    payload = {
        "kind": "P30_AB_FIXED_IMMUTABLE_PAIR_RECEIPT_V1",
        "decision": "REVIEW_ONLY_NOT_NATIVE",
        "lines": evidence, "native_get": 0, "native_body_lkg": 0,
        "formal_accepted_fields": 0, "golden": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }
    digest = hashlib.sha256(bridge._canonical(payload)).hexdigest()
    blob = bridge._canonical({"payload": payload, "sha256": digest}) + b"\n"
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError("AB_FIXED_PAIR_TARGET_ISOLATION_HOLD")
    destination = directory / (digest + ".json")
    if destination.is_symlink():
        raise ValueError("AB_FIXED_PAIR_RECEIPT_COLLISION_HOLD")
    fd, temporary = tempfile.mkstemp(prefix=".pair-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.is_symlink() or destination.read_bytes() != blob:
                raise ValueError("AB_FIXED_PAIR_RECEIPT_COLLISION_HOLD")
    finally:
        os.unlink(temporary)
    if destination.read_bytes() != blob:
        raise ValueError("AB_FIXED_PAIR_RECEIPT_READBACK_HOLD")
    # Concurrent post-seal slot drift cannot be represented as a coherent pair.
    for line in ("A", "B"):
        manifest = ready[line][0]
        target = isolation / line / manifest["adapter_key"] / "review_snapshot.json"
        if (target.is_symlink() or bridge._validate_snapshot(json.loads(
                target.read_text(encoding="utf-8"))) !=
                results[line]["snapshot_sha256"]):
            raise ValueError("AB_FIXED_PAIR_POST_SEAL_DRIFT_HOLD")
    return {"pair_receipt_sha256": digest,
            "pair_receipt_path": str(destination.relative_to(root))}




def run_fixed_ab(repo_root, inputs):
    """Execute two exact-ID adapters; preflight both, then independent CAS writes.

    A post-preflight race may yield PARTIAL_HOLD. Never roll back another
    line's valid durable receipt or misrepresent the pair as atomic.
    """
    root = Path(repo_root).resolve(strict=True)
    if not isinstance(inputs, dict) or set(inputs) != {"A", "B"}:
        raise ValueError("AB_FIXED_TWO_LINES_REQUIRED_HOLD")
    ready = {line: _prepare_line(root, line, inputs[line])
             for line in ("A", "B")}
    results = {}
    for line in ("A", "B"):
        manifest, listing, detail, expected = ready[line]
        try:
            result = bridge.replay_manifest_to_isolated_lkg(
                manifest, listing, detail, root, expected)
        except (ValueError, OSError) as exc:
            results[line] = {"decision": "HOLD",
                             "first_failure": type(exc).__name__ + ":" + str(exc)}
            return {"kind": "P30_AB_FIXED_REVIEW_WORKFLOW_V1",
                    "decision": "PARTIAL_HOLD" if line == "B" else "HOLD",
                    "lines": results, "native_get": 0,
                    "native_body_lkg": 0, "formal_accepted_fields": 0,
                    "golden": 0, "published": 0,
                    "release_state": "HARD_HOLD_NO_PUBLICATION"}
        results[line] = {
            "decision": result["decision"],
            "adapter_key": manifest["adapter_key"],
            "source_id": manifest["source_id"],
            "source_event_id": result["source_event_id"],
            "snapshot_sha256": result["snapshot_sha256"],
            "role_receipts": result["role_receipts"],
            "native_get": 0, "native_body_lkg": 0,
        }
    try:
        pair_receipt = _write_pair_receipt(root, ready, results)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return {"kind": "P30_AB_FIXED_REVIEW_WORKFLOW_V1",
                "decision": "PARTIAL_HOLD",
                "first_failure": type(exc).__name__ + ":" + str(exc),
                "lines": results, "native_get": 0, "native_body_lkg": 0,
                "formal_accepted_fields": 0, "golden": 0, "published": 0,
                "release_state": "HARD_HOLD_NO_PUBLICATION"}
    return {"kind": "P30_AB_FIXED_REVIEW_WORKFLOW_V1",
            "decision": "REVIEW_ONLY_NOT_NATIVE", "lines": results,
            **pair_receipt, "native_get": 0, "native_body_lkg": 0,
            "formal_accepted_fields": 0, "golden": 0, "published": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION"}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Two source-owned A/B offline REVIEW handoffs; NO GET/PUBLISH")
    parser.add_argument("--repo-root", required=True)
    for line in ("a", "b"):
        for field in ("manifest", "list-html", "detail-html", "expected-sha"):
            parser.add_argument("--" + line + "-" + field,
                                required=field != "expected-sha")
    args = parser.parse_args(argv)
    inputs = {}
    for line in ("A", "B"):
        prefix = line.lower() + "_"
        inputs[line] = {
            "manifest": getattr(args, prefix + "manifest"),
            "list_html": getattr(args, prefix + "list_html"),
            "detail_html": getattr(args, prefix + "detail_html"),
            "expected_sha": getattr(args, prefix + "expected_sha"),
        }
    try:
        outcome = run_fixed_ab(args.repo_root, inputs)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        outcome = {"kind": "P30_AB_FIXED_REVIEW_WORKFLOW_V1",
                   "decision": "HOLD",
                   "first_failure": type(exc).__name__ + ":" + str(exc),
                   "native_get": 0, "formal_accepted_fields": 0,
                   "golden": 0, "published": 0,
                   "release_state": "HARD_HOLD_NO_PUBLICATION"}
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return 0 if outcome["decision"] == "REVIEW_ONLY_NOT_NATIVE" else 49


if __name__ == "__main__":
    raise SystemExit(main())
