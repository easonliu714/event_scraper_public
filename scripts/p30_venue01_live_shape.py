#!/usr/bin/env python3
"""VENUE-01B: one explicitly scoped public GET, aggregate-only source-shape audit."""
import argparse
import hashlib
import json
from pathlib import Path
import p30_venue01_taipei_arena_readonly as prior

KIND = "EVENTRADAR_P30_VENUE01B_LIVE_SOURCE_SHAPE_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_ITEMS = prior.MAX_ITEMS

def assess(result):
    if not isinstance(result, dict) or result.get("gate") != "P30-VENUE-01":
        return {"decision": "HOLD_INVALID_ADAPTER_REPORT"}
    rows = result.get("records")
    if not isinstance(rows, list) or len(rows) > MAX_ITEMS:
        return {"decision": "HOLD_RECORDS_OR_CAP"}
    if len(rows) != result.get("announcement_count"):
        return {"decision": "HOLD_COUNT_MISMATCH"}
    hashes = []
    for row in rows:
        if not isinstance(row, dict):
            return {"decision": "HOLD_RECORD_SHAPE"}
        key = row.get("venue_source_key_hash")
        if not isinstance(key, str) or len(key) != 20 or any(c not in "0123456789abcdef" for c in key):
            return {"decision": "HOLD_SOURCE_HASH"}
        hashes.append(key)
        if row.get("ticket_event_id") is not None or row.get("ticket_event_url") is not None:
            return {"decision": "HOLD_TICKET_IDENTITY_PROMOTION"}
        if any(row.get(k) is not None for k in (
            "event_date", "sale_date", "admission_date", "registration_date",
            "voucher_date", "price", "session")):
            return {"decision": "HOLD_UNVERIFIED_FIELD_PROMOTION"}
        if row.get("field_status") != "HOLD_SEMANTIC_ROLES_NOT_VERIFIED":
            return {"decision": "HOLD_FIELD_STATUS"}
    if len(hashes) != len(set(hashes)):
        return {"decision": "HOLD_DUPLICATE_SOURCE_HASH"}
    if result.get("published") is not False or result.get("golden_accepted") != 0 or result.get("hard_hold_no_publication") is not True:
        return {"decision": "HOLD_RELEASE_CONTRACT"}
    return {"decision": "REVIEW_LIVE_OFFICIAL_SOURCE_SHAPE_ONLY",
            "announcementCount": len(rows),
            "platformClaimCounts": result.get("platform_claim_counts"),
            "uniqueVenueSourceHashes": len(hashes),
            "ticketEventIdentityAccepted": 0,
            "fieldsAccepted": 0, "goldenAccepted": 0, "published": False}

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--out", default="p30-venue01b-evidence")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required; never run in offline tests")
    out = Path(args.out)
    if out.resolve() != (Path.cwd() / "p30-venue01b-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    try:
        report = assess(prior.fetch_once())  # one HTTPS GET, no redirect or retry
    except prior.SourceHold as exc:
        report = {"decision": str(exc), "announcementCount": None}
    report.update(kind=KIND, releaseState=RELEASE, adapterExecuted=True,
                  source="TAIPEI_ARENA_OFFICIAL_OPENDATA",
                  dataSNIsTicketEventID=False, announcementTimeIsEventTime=False,
                  acceptedFields=0, goldenAccepted=0, published=False,
                  productionModified=False, rawHtmlPersisted=False,
                  rawTitlesPersisted=False, rawUrlsPersisted=False,
                  rawQueryValuesPersisted=False, cookiesPersisted=False)
    out.mkdir(exist_ok=True)
    payload = (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
    (out / "venue01b.json").write_bytes(payload)
    manifest = {"kind": KIND, "filesSHA256": {"venue01b.json": hashlib.sha256(payload).hexdigest()},
                "releaseState": RELEASE}
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("VENUE01B_DECISION=" + report["decision"])
    print("VENUE01B_COUNT=" + str(report.get("announcementCount")))
    return 0 if report["decision"] == "REVIEW_LIVE_OFFICIAL_SOURCE_SHAPE_ONLY" else 2

if __name__ == "__main__":
    raise SystemExit(main())
