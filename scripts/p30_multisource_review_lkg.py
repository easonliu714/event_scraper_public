"""Deterministic two-source REVIEW/LKG bridge; never a native GET or Publisher.

Ports independently developed TaiNEX #217 and FamiTicket #221 source-reader
contracts to the existing main candidate Core. Source-reader records are
historical, reconstructed observations, NOT independently reattested HTML.
No field is promoted to formal ACCEPTED; exhibition periods are not showtimes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from scripts import p30_venue02bo_tainex_exhibition as tainex
from scripts import p30_l9dc_famiticket_teca as famiticket
from scripts.p30_candidate_review_pipeline import build_candidate_dataset

HOLD = "HARD_HOLD_NO_PUBLICATION"
REGISTRY = {
    "tainex": {"module": tainex, "platform_id": "TAINEX",
               "platform": "台北南港展覽館", "gate": "P30-VENUE-02BO",
               "expected_decision": "REVIEW", "expected_fields": 6,
               "namespace": "event", "source_pr": 217},
    "famiticket": {"module": famiticket, "platform_id": "FAMITICKET",
                   "platform": "FamiTicket", "gate": "P30-L9-DC",
                   "expected_decision": "REVIEW_WITH_HOLD", "expected_fields": 9,
                   "namespace": "Home/Activity/Info", "source_pr": 221},
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
            or utc(row["scraped_at"]) > as_of):
        raise ValueError("PRIOR_LKG_SOURCE_BINDING_HOLD")


def plan(packets, *, previous=None, as_of):
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
    candidates, quality = build_candidate_dataset([r["candidate"] for r in receipts])
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
        "source_reader_qualified": len(candidates),
        "source_platforms": sorted({x["_candidate"]["platform_id"] for x in candidates}),
        "source_gates": sorted({r["gate"] for r in receipts}),
        "new_review": added, "changed_review": changed,
        "unchanged_review": unchanged, "retained_lkg": retained,
        "review_rows": rows, "rejected": rejected,
        "source_review_receipts": source_receipts,
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = plan(source["packets"], previous=source.get("previous", []),
                  as_of=utc(source["as_of"]))
    digest = write_isolated(result, args.output, Path.cwd())
    print(json.dumps({"decision": result["decision"],
                      "source_reader_qualified": result["source_reader_qualified"],
                      "independently_accepted_fields": 0,
                      "native_get": 0, "published_delta": 0,
                      "isolated_sha256": digest}, sort_keys=True))
    return 0 if result["source_reader_qualified"] else 49


if __name__ == "__main__":
    raise SystemExit(main())
