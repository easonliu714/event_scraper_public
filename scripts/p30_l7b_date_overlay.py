#!/usr/bin/env python3
"""P30-L7-B: overlay STRICT official-detail date evidence into frozen Android smoke JSON.

NO network clients. No Pages data path, no PWA deploy, no notifications.
Require the exact L3-A candidate digest embedded in the old accepted L7-A artifact.
"""
import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

SOURCE_KIND = "EVENTRADAR_P30_ANDROID_SMOKE_CANDIDATE_NOT_GOLDEN"
EVIDENCE_KIND = "EVENTRADAR_P30_L4A_TWTC_DETAIL_DATE_EVIDENCE_NOT_GOLDEN"
VERIFIED = "DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE"
SOURCE_RUN = "40270383643"
EVIDENCE_RUN = "40273199767"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    data = Path(path).read_bytes()
    return json.loads(data.decode("utf-8")), sha(data)


def key(title, official_url, raw_period):
    return (title.strip() if isinstance(title, str) else title, official_url, raw_period)


def gate_flags(data, schema):
    if data.get("kind") != schema:
        raise ValueError("HOLD_SOURCE_SCHEMA")
    flags = (("published", False), ("goldenAccepted", False), ("writerExecuted", False),
             ("notificationExecuted", False), ("autoHidden", 0), ("sourceRuntime", "DORMANT")) \
            if schema == SOURCE_KIND else \
            (("app_data_published", False), ("golden_accepted", False),
             ("writer_executed", False), ("notification_executed", False),
             ("auto_hidden", 0), ("source_runtime", "DORMANT"))
    for name, value in flags:
        if data.get(name) != value:
            raise ValueError("HOLD_SOURCE_FLAG_" + name)


def overlay(original, evidence, evidence_digest):
    """Preserve 44 IDs and 5 CKSMH events; enrich ONLY 38 bound TWTC event dates."""
    if not isinstance(original, dict) or not isinstance(evidence, dict):
        raise ValueError("HOLD_OBJECT_SHAPE")
    gate_flags(original, SOURCE_KIND)
    gate_flags(evidence, EVIDENCE_KIND)
    if original.get("count") != 44 or len(original.get("items", [])) != 44:
        raise ValueError("HOLD_OLD_ANDROID_COUNT")
    if original.get("sourceFileSHA256", {}).get("twtcCandidate") != evidence.get("source_file_sha256", {}).get("candidate"):
        raise ValueError("HOLD_L3A_CANDIDATE_SHA_MISMATCH")
    if original.get("sourceFileSHA256", {}).get("twtcDiagnostics") != evidence.get("source_file_sha256", {}).get("diagnostics"):
        raise ValueError("HOLD_L3A_DIAGNOSTICS_SHA_MISMATCH")
    if evidence.get("source_run_id") != SOURCE_RUN or evidence.get("source_candidate_count") != 39:
        raise ValueError("HOLD_L4A_SOURCE_RUN")
    report = evidence.get("counts", {})
    if report.get("candidate_count") != 39 or len(evidence.get("records", [])) != 39:
        raise ValueError("HOLD_L4A_EVIDENCE_COUNT")
    if evidence.get("identity_gate") != "OFFICIAL_URL_ID+HEADING+RAW_PERIOD_PARITY":
        raise ValueError("HOLD_L4A_IDENTITY_GATE")
    records = {}
    for r in evidence["records"]:
        if not isinstance(r, dict):
            raise ValueError("HOLD_EVIDENCE_RECORD")
        identity = key(r.get("title"), r.get("official_url"), r.get("source_period_raw"))
        if identity in records:
            raise ValueError("HOLD_DUPLICATE_DETAIL_EVIDENCE")
        records[identity] = r
    data = json.loads(json.dumps(original, ensure_ascii=False))
    twtc_keys = set()
    converted, unresolved = 0, []
    for entry in data["items"]:
        if entry["platform"] != "台北世貿":
            if entry["platform"] != "中正紀念堂":
                raise ValueError("HOLD_PLATFORM_MIXING")
            continue
        identity = key(entry.get("title"), entry.get("officialUrl"), entry.get("rawPeriod"))
        if identity in twtc_keys:
            raise ValueError("HOLD_DUPLICATE_TWTC")
        twtc_keys.add(identity)
        r = records.get(identity)
        if r is None:
            raise ValueError("HOLD_TWTC_IDENTITY_NOT_IN_EVIDENCE")
        # Clear old sampled date first: only current identity-confirmed evidence may restore it.
        entry["dateStart"] = None
        entry["dateEnd"] = None
        entry["sourceLevel"] = "LIST_TABLE_ONLY"
        entry["timeRole"] = "EXHIBITION_PERIOD_RAW_UNNORMALIZED"
        entry["dateEvidenceStatus"] = r["state"]
        if r["state"] == VERIFIED:
            if r.get("detail_url") != entry.get("officialUrl") or \
                    r.get("source_time_role") != "OFFICIAL_EXHIBITION_DATE":
                raise ValueError("HOLD_VERIFIED_ROLE_URL_MISMATCH")
            try:
                start, end = date.fromisoformat(r["start"]), date.fromisoformat(r["end"])
            except (ValueError, KeyError, TypeError):
                raise ValueError("HOLD_VERIFIED_DATE_INVALID")
            if start > end or len(r.get("response_sha256", "")) != 64:
                raise ValueError("HOLD_DATE_OR_HTTP_EVIDENCE")
            entry["dateStart"] = start.isoformat()
            entry["dateEnd"] = end.isoformat()
            entry["sourceLevel"] = "DETAIL_DATE_CANDIDATE"
            entry["timeRole"] = "OFFICIAL_EXHIBITION_DATE"
            entry["dateEvidenceRunId"] = EVIDENCE_RUN
            entry["dateEvidenceSHA256"] = r["response_sha256"]
            converted += 1
        else:
            unresolved.append({"title": entry["title"], "url": entry["officialUrl"],
                               "reason": r["state"], "rawPeriod": entry.get("rawPeriod")})
    if len(twtc_keys) != 39 or converted != report.get("date_verified"):
        raise ValueError("HOLD_VERIFIED_COUNTS_MISMATCH")
    if len(unresolved) != report.get("remaining_unverified"):
        raise ValueError("HOLD_UNVERIFIED_COUNTS_MISMATCH")
    if sum(1 for row in data["items"] if row["platform"] == "中正紀念堂") != 5:
        raise ValueError("HOLD_CKSMH_MISSING")
    if converted < 1:
        raise ValueError("HOLD_NO_DATE_ENRICHMENT")
    data["generatedAtUTC"] = datetime.now(timezone.utc).isoformat()
    data["dateEvidenceRunId"] = EVIDENCE_RUN
    data["dateEvidenceArtifactSHA256"] = evidence_digest
    data["dateVerifiedCount"] = converted
    data["dateUnverifiedCount"] = len(unresolved)
    data["dateEvidenceKind"] = EVIDENCE_KIND
    data["dateEnrichmentStatus"] = "DETAIL_BOUND_PARTIAL_NOT_GOLDEN"
    data["fullPlatformCoverageProven"] = False
    data["published"] = False
    return data, unresolved


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True)
    ap.add_argument("--detail-evidence", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    target = Path(args.out_dir).resolve()
    formal = Path("docs").resolve()
    if target == formal or formal in target.parents:
        ap.error("HOLD_FORMAL_DATA_WRITE")
    data, _ = load(args.original)
    evidence, checksum = load(args.detail_evidence)
    merged, unresolved = overlay(data, evidence, checksum)
    target.mkdir(parents=True, exist_ok=True)
    (target / "data.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "date_hold_report.json").write_text(
        json.dumps({"kind": "P30_L7B_UNVERIFIED_DATE_REASONS",
                    "held_count": len(unresolved),
                    "held": unresolved}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("START P30_L7B_DATE_EVIDENCE_OVERLAY")
    print("TOTAL", merged["count"], "DATE_VERIFIED", merged["dateVerifiedCount"],
          "DATE_HOLD", merged["dateUnverifiedCount"])
    for v in unresolved:
        print("HOLD_TWTC_DATE", v["reason"], v["title"][:90], v["rawPeriod"])
    print("PASS P30_L7B_BOUNDED_DATE_ENRICHMENT_NO_PUBLISH")


if __name__ == "__main__":
    main()
