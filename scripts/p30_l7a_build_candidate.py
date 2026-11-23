#!/usr/bin/env python3
"""P30-L7-A immutable two-artifact -> Android smoke-candidate JSON, no publisher.

Two bounded independent source samples, NOT the full event inventory.
No network module, no DB, no Pages writer, no notification, no auto hide.
"""
import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

KIND_CKSMH = "EVENTRADAR_P30_L2B_CKSMH_PROBE_NOT_GOLDEN"
KIND_TWTC = "EVENTRADAR_P30_L3A_TWTC_EXHIBITION_CANDIDATE_ONLY"
KIND_OUTPUT = "EVENTRADAR_P30_ANDROID_SMOKE_CANDIDATE_NOT_GOLDEN"
INPUT_SPECS = (
    ("CKSMH", "中正紀念堂", "event.culture.tw", KIND_CKSMH, 5, "40269917573"),
    ("TWTC", "台北世貿", "twtc.com.tw", KIND_TWTC, 39, "40270383643"),
)


def file_json(path):
    raw = Path(path).read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def is_official(url, host):
    if not isinstance(url, str) or len(url) > 2048:
        return False
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname == host
                and p.username is None and p.password is None
                and p.port in (None, 443) and bool(p.path)
                and not any(x == ".." for x in p.path.split("/")))
    except ValueError:
        return False


def verify_diagnostic(report, name, kind, expected):
    if not isinstance(report, dict) or report.get("kind") != kind:
        raise ValueError("HOLD_WRONG_DIAGNOSTIC_" + name)
    for flag in ("writer_executed", "notification_executed",
                 "app_data_published", "golden_accepted"):
        if report.get(flag) is not False:
            raise ValueError("HOLD_UNSAFE_" + flag)
    if report.get("source_runtime") != "DORMANT" or report.get("auto_hidden") != 0:
        raise ValueError("HOLD_UNSAFE_RUNTIME")
    if name == "CKSMH":
        count = report.get("unique_list_candidates")
    else:
        count = report.get("unique_candidates")
    if count != expected:
        raise ValueError("HOLD_SOURCE_COUNT_DRIFT_" + name)


def build_event(row, platform, host, run_id):
    if not isinstance(row, dict) or row.get("platform") != platform:
        raise ValueError("HOLD_PLATFORM_MISMATCH")
    title = row.get("title")
    official = row.get("official_url")
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 180:
        raise ValueError("HOLD_INVALID_TITLE")
    if not is_official(official, host):
        raise ValueError("HOLD_UNBOUND_ORIGIN")
    if row.get("golden_verified") is not False or row.get("ticket_availability") != "UNKNOWN":
        raise ValueError("HOLD_FALSE_GOLDEN_OR_TICKET_STATUS")
    start, end = row.get("event_date_start"), row.get("event_date_end")
    if start is not None or end is not None:
        if (platform != "台北世貿" or not isinstance(start, str) or not isinstance(end, str)
                or row.get("source_time_role") != "OFFICIAL_EXHIBITION_DATE"
                or row.get("source_level") != "DETAIL_DATE_CANDIDATE"):
            raise ValueError("HOLD_UNBOUND_DATE_ROLE")
        try:
            if date.fromisoformat(start) > date.fromisoformat(end):
                raise ValueError("reversed")
        except ValueError:
            raise ValueError("HOLD_INVALID_DETAIL_DATE")
    legacy_date = row.get("date")
    if legacy_date is not None:
        raise ValueError("HOLD_UNEXPECTED_LIST_DATE")
    venue = row.get("location") if isinstance(row.get("location"), str) else None
    identity = "|".join((platform, title.strip(), official,
                         str(row.get("event_period_raw") or "")))
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    summary = row.get("description") if isinstance(row.get("description"), str) else None
    return {
        "id": key, "title": title.strip(), "platform": platform,
        "category": "展覽" if platform == "台北世貿" else "待確認",
        "categoryEvidence": "OFFICIAL_EXHIBITION_TIMETABLE" if platform == "台北世貿"
                            else "NOT_CLASSIFIED",
        "officialUrl": official, "officialLinkRole": row.get("official_url_role", "EVENT_DETAIL"),
        "sourceListUrl": row.get("source_list_url"),
        "sourceRunId": run_id, "sourceLevel": row.get("source_level"),
        "dateStart": start, "dateEnd": end,
        "rawPeriod": row.get("event_period_raw"),
        "timeRole": row.get("source_time_role", "UNKNOWN"),
        "venue": venue[:120] if venue else None,
        "price": None, "summary": summary[:300] if summary else None,
        "ticketStatus": "UNKNOWN", "validity": "UNCERTAIN",
        "goldenVerified": False,
    }


def build(ck_items, ck_diag, tw_items, tw_diag):
    if not isinstance(ck_items, list) or not isinstance(tw_items, list):
        raise ValueError("HOLD_INVALID_ARRAYS")
    all_rows = []
    sources = []
    for label, platform, host, kind, expected, run_id in INPUT_SPECS:
        rows = ck_items if label == "CKSMH" else tw_items
        report = ck_diag if label == "CKSMH" else tw_diag
        verify_diagnostic(report, label, kind, expected)
        if len(rows) != expected:
            raise ValueError("HOLD_SOURCE_EVENT_COUNT_" + label)
        all_rows.extend(build_event(row, platform, host, run_id) for row in rows)
        sources.append({"platform": platform, "runId": run_id,
                        "candidateCount": len(rows), "goldenAccepted": False})
    keys = [r["id"] for r in all_rows]
    if len(keys) != len(set(keys)):
        raise ValueError("HOLD_DUPLICATE_IDENTITIES")
    all_rows.sort(key=lambda v: (v["platform"], v["title"]))
    return {
        "kind": KIND_OUTPUT, "schemaVersion": "P30-CANDIDATE-1",
        "generatedAtUTC": datetime.now(timezone.utc).isoformat(),
        "count": len(all_rows), "sources": sources, "items": all_rows,
        "sourceRuntime": "DORMANT", "goldenAccepted": False,
        "autoHidden": 0, "published": False, "writerExecuted": False,
        "notificationExecuted": False, "fullPlatformCoverageProven": False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cksmh-dir", required=True)
    ap.add_argument("--twtc-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    dest = Path(args.out).resolve()
    if dest == Path("docs").resolve() or Path("docs").resolve() in dest.parents:
        ap.error("HOLD_PAGES_OUTPUT")
    ck_root, tw_root = Path(args.cksmh_dir), Path(args.twtc_dir)
    ck_items, ck_hash = file_json(ck_root / "candidate.json")
    ck_diag, ck_dhash = file_json(ck_root / "diagnostics.json")
    tw_items, tw_hash = file_json(tw_root / "candidate.json")
    tw_diag, tw_dhash = file_json(tw_root / "diagnostics.json")
    output = build(ck_items, ck_diag, tw_items, tw_diag)
    output["sourceFileSHA256"] = {
        "cksmhCandidate": ck_hash, "cksmhDiagnostics": ck_dhash,
        "twtcCandidate": tw_hash, "twtcDiagnostics": tw_dhash,
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("START P30_L7A_CANDIDATE_BRIDGE")
    print("CANDIDATES", output["count"], "SOURCES", len(output["sources"]))
    print("PASS P30_L7A_ISOLATED_CANDIDATE_JSON_NOT_GOLDEN")
    print("SOURCE_RUNTIME=DORMANT AUTO_HIDDEN=0 PUBLISHED=false")


if __name__ == "__main__":
    main()
