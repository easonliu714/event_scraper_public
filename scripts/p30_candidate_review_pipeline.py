#!/usr/bin/env python3
"""P30 L7 isolated candidate JSON builder. Never publishes to docs/data.json.

Input must be provenance-tagged review records. All outputs are REVIEW-only.
No network, login, scheduler, data feed mutation or notification is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

REVIEW_SCOPE = "CANDIDATE_PREVIEW_ONLY"
FORBIDDEN_OUTPUTS = {"docs/data.json", "docs/platform_status.json"}
REQUIRED = ("title", "url", "platform", "type", "scraped_at", "_candidate")
MAX_ROWS = 2000


def _https(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        p = urlparse(value)
        return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False


def normalize_record(raw: object) -> tuple[dict | None, list[str]]:
    """Validate provenance and classify a single original record; never invent fields."""
    reasons: list[str] = []
    if not isinstance(raw, dict):
        return None, ["RECORD_NOT_OBJECT"]
    for k in REQUIRED:
        if k not in raw:
            reasons.append("MISSING_" + k.upper())
    m = raw.get("_candidate", {})
    if not isinstance(m, dict):
        return None, ["CANDIDATE_METADATA_INVALID"]
    if m.get("scope") != REVIEW_SCOPE or m.get("decision") not in ("REVIEW", "REVIEW_WITH_HOLD"):
        reasons.append("NOT_REVIEW_SCOPE")
    for key in ("published", "golden_accepted", "formal_field_pass"):
        if m.get(key) is not False:
            reasons.append("NOT_EXPLICITLY_UNPUBLISHED_" + key.upper())
    if not _https(raw.get("url")):
        reasons.append("INVALID_OFFICIAL_URL")
    title = raw.get("title")
    if not isinstance(title, str) or not (3 <= len(title.strip()) <= 180):
        reasons.append("INVALID_TITLE")
    if not isinstance(raw.get("platform"), str) or not raw["platform"].strip():
        reasons.append("PLATFORM_UNKNOWN")
    if not isinstance(raw.get("type"), str) or not raw["type"].strip():
        reasons.append("TYPE_INVALID")
    stamp = raw.get("scraped_at")
    try:
        # Freshness must be independently evaluated later; a naive or malformed
        # timestamp cannot even serve as a REVIEW observation timestamp.
        if not isinstance(stamp, str):
            raise ValueError("not a string")
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timezone missing")
    except (ValueError, TypeError, OverflowError):
        reasons.append("OBSERVATION_TIME_UNVERIFIED")
    # A nested REVIEW flag must not conceal a top-level publication claim.
    for key in ("published", "golden_accepted", "formal_field_pass"):
        if key in raw and raw[key] is not False:
            reasons.append("TOP_LEVEL_PUBLICATION_CLAIM_" + key.upper())
    if not isinstance(m.get("platform_id"), str) or not m["platform_id"].strip():
        reasons.append("CANONICAL_PLATFORM_ID_UNKNOWN")
    if not isinstance(m.get("source_event_id"), str) or not m["source_event_id"].strip():
        reasons.append("SOURCE_ID_UNVERIFIED")
    if not isinstance(m.get("record_id"), str) or not m["record_id"].strip():
        reasons.append("RECORD_ID_MISSING")
    sources = m.get("sources")
    if not isinstance(sources, list) or not sources or not all(_https(x) for x in sources):
        reasons.append("OFFICIAL_SOURCE_EVIDENCE_MISSING")
    elif raw.get("url") not in sources:
        # Fail closed: a plausible HTTPS event URL is not field-level evidence
        # unless the exact linked detail URL is among the source receipts.
        # Venue index links and a different event ID cannot silently qualify it.
        reasons.append("DETAIL_URL_NOT_IN_SOURCE_EVIDENCE")
    if (not isinstance(m.get("hold_reasons"), list) or not m["hold_reasons"]
            or not all(isinstance(v, str) and v.strip() for v in m["hold_reasons"])):
        reasons.append("MISSING_OR_INVALID_HOLD_REASON")
    if reasons:
        return None, reasons

    # Allowlist only PWA fields and explicit candidate diagnostics. No supplied
    # arbitrary DOM/HTML, no inferred date, ticket status, price or availability.
    result = {k: raw[k] for k in ("title", "url", "platform", "type", "scraped_at")}
    # Every displayed optional field must carry independent, exact source
    # provenance. A row-level URL is not evidence for arbitrary dates/prices.
    # Missing or contradictory receipts remain visible only as UNKNOWN/HOLD.
    field_roles = {
        "date": {"EVENT_DATE", "VENUE_EVENT_DATE"},
        "location": {"EVENT_VENUE"},
        "price": {"EVENT_ADMISSION_PRICE"},
        "description": {"EVENT_DESCRIPTION"},
        "region": {"EVENT_REGION"},
    }
    field_evidence = m.get("field_evidence")
    field_evidence = field_evidence if isinstance(field_evidence, dict) else {}
    verified_fields = {}
    field_holds = []
    for k, allowed_roles in field_roles.items():
        v = raw.get(k)
        v = v.strip() if isinstance(v, str) else ""
        receipt = field_evidence.get(k)
        valid = False
        if v and v != "未確認" and isinstance(receipt, dict):
            stamp = receipt.get("observed_at")
            try:
                if not isinstance(stamp, str):
                    raise ValueError("missing field observation")
                observed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                valid_stamp = observed.tzinfo is not None and observed.utcoffset() is not None
            except (ValueError, TypeError, OverflowError):
                valid_stamp = False
            valid = (
                valid_stamp
                and receipt.get("value") == v
                # A sources[] membership proves only that the URL was listed,
                # not that two distinct event/product URLs share field ownership.
                # Until a separately verified cross-source identity edge exists,
                # an optional REVIEW field must be certified by this exact row URL.
                # A tixCraft VIP add-on price must not become base admission;
                # an OPENTIX multi-venue Event date must not become venue showtime.
                and receipt.get("source") == raw["url"]
                and receipt.get("source") in sources
                and isinstance(receipt.get("role"), str)
                and receipt.get("role") in allowed_roles
                and receipt.get("decision") == "REVIEW"
            )
        if valid:
            result[k] = v
            verified_fields[k] = {
                "value": v, "source": receipt["source"],
                "observed_at": receipt["observed_at"],
                "role": receipt["role"], "decision": "REVIEW",
            }
        else:
            result[k] = "未確認"
            if v and v != "未確認":
                field_holds.append("FIELD_" + k.upper() + "_PROVENANCE_HOLD")
    result["img_url"] = None  # no remote tracking images in local review
    result["_candidate"] = {
        "scope": REVIEW_SCOPE,
        "decision": m["decision"],
        "record_id": m["record_id"],
        "platform_id": m["platform_id"],
        "source_event_id": m["source_event_id"],
        "source_class": m.get("source_class", "UNKNOWN"),
        "sources": sources,
        "field_evidence": verified_fields,
        "hold_reasons": list(m["hold_reasons"]) + field_holds,
        # Input sessions have no independent ticket Session ID/role evidence
        # contract in this L7 review schema. Never forward arbitrary objects
        # as if they were source-validated showtimes or purchasable sessions.
        "sessions": [],
        "formal_field_pass": False,
        "golden_accepted": False,
        "published": False,
        "ticket_session_id": None,
        "inventory": None,
    }
    if m.get("sessions"):
        result["_candidate"]["hold_reasons"].append("UNVERIFIED_SESSIONS_QUARANTINED")
    # Suspected title contaminated with date/location must be quarantined
    # instead of stripping an unverified substring and pretending certainty.
    if isinstance(title, str):
        import re
        if re.search(r"\d{4}-\d{2}-\d{2}", title) and len(title) > 45:
            result["_candidate"]["hold_reasons"].append("TITLE_MIXED_WITH_DATE_REQUIRES_SOURCE_RECHECK")
    return result, []


def build_candidate_dataset(rows: object) -> tuple[list[dict], dict]:
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError("INPUT_MUST_BE_BOUNDED_ARRAY")
    accepted: list[dict] = []
    rejected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    input_by_platform: Counter[str] = Counter()
    rejected_by_platform: Counter[str] = Counter()
    rejected_reasons: Counter[str] = Counter()
    for index, raw in enumerate(rows):
        # Preserve the input platform label for diagnostics only; never infer a
        # canonical ID or promote an unverified record into the preview feed.
        label = raw.get("platform") if isinstance(raw, dict) else None
        label = label.strip() if isinstance(label, str) and label.strip() else "UNKNOWN"
        input_by_platform[label] += 1
        row, problems = normalize_record(raw)
        if problems:
            rejected.append({"index": index, "reasons": problems})
            rejected_by_platform[label] += 1
            rejected_reasons.update(problems)
            continue
        key = (row["_candidate"]["platform_id"], row["_candidate"]["source_event_id"])
        if key in seen:
            rejected.append({"index": index, "reasons": ["DUPLICATE_CANONICAL_ID"]})
            rejected_by_platform[label] += 1
            rejected_reasons["DUPLICATE_CANONICAL_ID"] += 1
            continue
        seen.add(key)
        accepted.append(row)
    report = {
        "kind": "EVENTRADAR_ISOLATED_CANDIDATE_QUALITY_V1",
        "scope": REVIEW_SCOPE,
        "inputRows": len(rows),
        "previewRows": len(accepted),
        "rejectedRows": len(rejected),
        "platformCounts": dict(sorted(Counter(x["platform"] for x in accepted).items())),
        "inputPlatformCounts": dict(sorted(input_by_platform.items())),
        "rejectedPlatformCounts": dict(sorted(rejected_by_platform.items())),
        "rejectionReasonCounts": dict(sorted(rejected_reasons.items())),
        "rejected": rejected,
        "formalFieldAccepted": 0,
        "goldenAccepted": 0,
        "published": 0,
        "releaseState": "HARD_HOLD_NO_PUBLICATION",
        "note": "PREVIEW only, not a live full-platform scrape or publication",
    }
    return accepted, report


def write_isolated_outputs(
    rows: object, dest: Path, repo_root: Path,
    *, audit_only: bool = False, expected_rows: int | None = None
) -> dict:
    root = repo_root.resolve()
    target = dest.resolve()
    if target == root or target == (root / "docs").resolve():
        raise ValueError("FORBIDDEN_PUBLIC_OUTPUT_DIR")
    for forbidden in FORBIDDEN_OUTPUTS:
        if target == (root / forbidden).resolve().parent:
            raise ValueError("FORBIDDEN_PUBLICATION_PATH")
    if target.is_relative_to((root / "docs").resolve()):
        raise ValueError("NO_CANDIDATES_UNDER_PUBLIC_PAGES_DOCS")
    if expected_rows is not None and (
        expected_rows < 1 or not isinstance(rows, list) or len(rows) != expected_rows
    ):
        raise ValueError("EXPECTED_INPUT_ROW_COUNT_MISMATCH")
    candidates, report = build_candidate_dataset(rows)
    if not candidates and not audit_only:
        raise ValueError("EMPTY_REVIEW_CANDIDATES_NOT_PUBLISHED")
    # Audit-only is deliberately usable for 18 legacy/untrusted rows with
    # zero provenance-qualified candidates. It must not create a PWA import.
    if audit_only and (target / "data.json").exists():
        raise ValueError("AUDIT_ONLY_OUTPUT_HAS_STALE_PREVIEW_DATA")
    target.mkdir(parents=True, exist_ok=True)
    report["auditOnly"] = audit_only
    report["previewImportAllowed"] = not audit_only
    names = ["quality_report.json"]
    if not audit_only:
        data = json.dumps(candidates, ensure_ascii=False, indent=2) + "\n"
        (target / "data.json").write_text(data, encoding="utf-8")
        names.append("data.json")
    stats = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (target / "quality_report.json").write_text(stats, encoding="utf-8")
    manifest = {}
    for name in names:
        b = (target / name).read_bytes()
        manifest[name] = hashlib.sha256(b).hexdigest()
    (target / "SHA256SUMS.txt").write_text(
        "".join(f"{manifest[k]}  {k}\n" for k in sorted(manifest)), encoding="utf-8")
    return report


def main() -> None:
    p = argparse.ArgumentParser(description="Build non-published EventRadar candidate preview")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--audit-only", action="store_true",
                   help="Write rejection/quality report only; never create preview data.json")
    p.add_argument("--expected-rows", type=int, default=None,
                   help="Fail closed unless the input has exactly this many rows")
    args = p.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = write_isolated_outputs(
        data, args.output_dir, args.repo_root,
        audit_only=args.audit_only, expected_rows=args.expected_rows
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
