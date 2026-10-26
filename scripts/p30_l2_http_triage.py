#!/usr/bin/env python3
"""P30-L2-A: classify immutable L1 diagnostics OFFLINE; never fetch activity sites.

Input is the existing diagnostic artifact, not current live activity inventory.
This module imports neither scraper.py nor show_news.py and has no network client.
"""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

KIND = "EVENTRADAR_P30_FRESH_DIAGNOSTIC_CANDIDATE"
BLOCKED = frozenset({
    "HTTP_ERROR", "NETWORK_ERROR", "URL_NOT_ALLOWLISTED", "REDIRECT_LIMIT",
    "REDIRECT_WITHOUT_LOCATION", "NON_HTML", "OVERSIZE_HTML", "EMPTY_RESPONSE",
    "BUDGET_EXHAUSTED",
})


def classify(entry):
    """Preserve the observed HTTP code; do not infer antibot, deletion or expiration."""
    platform = entry.get("platform")
    status = entry.get("stage1")
    if not isinstance(platform, str) or not platform.strip():
        raise ValueError("HOLD_PLATFORM_IDENTITY_MISSING")
    count = entry.get("list_candidates")
    if type(count) is not int or count < 0:
        raise ValueError("HOLD_INVALID_LIST_COUNT")
    net = entry.get("list_http") or {}
    if not isinstance(net, dict):
        raise ValueError("HOLD_HTTP_PROVENANCE_MALFORMED")
    code = net.get("http_status")
    if code is not None and (type(code) is not int or not 100 <= code <= 599):
        raise ValueError("HOLD_HTTP_CODE_INVALID")
    if status == "HTTP_OK":
        if code != 200:
            raise ValueError("HOLD_HTTP_OK_CODE_CONFLICT")
        tier = "L3_LIST_EMPTY_REVIEW" if count == 0 else "L4_DETAIL_SAMPLE_NEXT"
    elif status in BLOCKED:
        if count != 0:
            raise ValueError("HOLD_BLOCKED_WITH_LIST_COUNT")
        tier = "L2_HTTP_FAILURE_REVIEW"
    else:
        raise ValueError("HOLD_UNRECOGNIZED_HTTP_STAGE")
    return {
        "platform": platform,
        "source_listing_url": entry.get("listing_url"),
        "observed_final_url": net.get("url"),
        "http_status": code,
        "http_stage": status,
        "http_trail": net.get("trail", []),
        "content_type": net.get("content_type"),
        "response_sha256": net.get("html_sha256"),
        "list_candidates": count,
        "detail_checked": entry.get("detail_checked", 0),
        "detail_http_ok": entry.get("detail_http_ok", 0),
        "triage_tier": tier,
        "golden_verified": False,
        "source_gone_proven": False,
        "automatic_hide_permitted": False,
    }


def triage(diagnostic, input_sha256, run_id):
    """Require dormant, nonpublished source lineage and internally consistent counts."""
    if not isinstance(diagnostic, dict) or diagnostic.get("kind") != KIND:
        raise ValueError("HOLD_WRONG_DIAGNOSTIC_KIND")
    mandatory = {
        "writer_executed": False, "notification_executed": False,
        "golden_accepted": False, "app_data_published": False,
        "source_runtime": "DORMANT", "auto_hidden": 0,
    }
    for field, expected in mandatory.items():
        if diagnostic.get(field) != expected:
            raise ValueError(f"HOLD_UNSAFE_PROVENANCE_{field}")
    items = diagnostic.get("platforms")
    if not isinstance(items, list) or not items:
        raise ValueError("HOLD_NO_PLATFORM_EVIDENCE")
    entries = [classify(item) for item in items]
    names = [item["platform"] for item in entries]
    if len(names) != len(set(names)):
        raise ValueError("HOLD_DUPLICATE_PLATFORMS")
    counts = diagnostic.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("HOLD_MISSING_BASELINE_COUNTS")
    actual = {
        "platforms_checked": len(entries),
        "http_ok_platforms": sum(p["http_stage"] == "HTTP_OK" for p in entries),
        "list_nonempty_platforms": sum(p["list_candidates"] > 0 for p in entries),
        "total_list_candidates": sum(p["list_candidates"] for p in entries),
    }
    for key, value in actual.items():
        if counts.get(key) != value:
            raise ValueError(f"HOLD_BASELINE_COUNT_MISMATCH_{key}")
    tiers = Counter(p["triage_tier"] for p in entries)
    priority = {"L2_HTTP_FAILURE_REVIEW": 0, "L3_LIST_EMPTY_REVIEW": 1,
                "L4_DETAIL_SAMPLE_NEXT": 2}
    entries.sort(key=lambda e: (priority[e["triage_tier"]], e["platform"]))
    return {
        "kind": "EVENTRADAR_P30_L2A_OFFLINE_TRIAGE_ONLY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_run_id": str(run_id),
        "input_sha256": input_sha256,
        "source_generated_at_utc": diagnostic.get("generated_at_utc"),
        "source_main_sha_at_design": diagnostic.get("source_main_sha_at_design"),
        "detail_parser_pr_head_sha": diagnostic.get("detail_parser_pr_head_sha"),
        "counts": {**actual,
                   "l2_http_failure_review": tiers["L2_HTTP_FAILURE_REVIEW"],
                   "l3_empty_list_review": tiers["L3_LIST_EMPTY_REVIEW"],
                   "l4_detail_sample_next": tiers["L4_DETAIL_SAMPLE_NEXT"]},
        "platforms": entries,
        "no_new_http_requests": True,
        "golden_accepted": False,
        "auto_hidden": 0,
        "app_data_published": False,
        "source_runtime": "DORMANT",
        "writer_executed": False,
        "notification_executed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    src, dst = Path(args.input).resolve(), Path(args.out).resolve()
    if not src.is_file():
        parser.error("HOLD_DIAGNOSTIC_ARTIFACT_MISSING")
    if dst == src or Path("docs").resolve() in dst.parents or dst == Path("docs").resolve():
        parser.error("HOLD_FORMAL_PAGES_WRITE_FORBIDDEN")
    raw = src.read_bytes()
    diag = json.loads(raw.decode("utf-8"))
    result = triage(diag, hashlib.sha256(raw).hexdigest(), args.run_id)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("START P30_L2A_IMMUTABLE_OFFLINE_TRIAGE")
    print("EVIDENCE_RUN_ID", args.run_id)
    print("INPUT_SHA256", result["input_sha256"])
    print("COUNTS", json.dumps(result["counts"], ensure_ascii=False, sort_keys=True))
    print("PASS P30_L2A_OFFLINE_TRIAGE_NO_NEW_HTTP_NO_PUBLISH")
    print("GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 APP_DATA_PUBLISHED=false SOURCE_RUNTIME=DORMANT")


if __name__ == "__main__":
    main()
