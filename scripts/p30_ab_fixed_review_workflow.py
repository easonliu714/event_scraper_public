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
import re
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
    bridge.preflight_review_lkg_transition(prior, envelope, expected)
    return manifest, listing, detail, expected


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
    return {"kind": "P30_AB_FIXED_REVIEW_WORKFLOW_V1",
            "decision": "REVIEW_ONLY_NOT_NATIVE", "lines": results,
            "native_get": 0, "native_body_lkg": 0,
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
