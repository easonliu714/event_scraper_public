#!/usr/bin/env python3
"""P30-L4-A: TWTC official-detail evidence for frozen 39 source candidates.

No list crawl, hidden API, cookies, retries, notifier, site-wide scans, or Pages write.
Accept date ONLY when matching same official event URL, page heading and raw MM/DD.
"""
import argparse
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests
from bs4 import BeautifulSoup
import p30_l3a_twtc as l3

KIND = "EVENTRADAR_P30_L4A_TWTC_DETAIL_DATE_EVIDENCE_NOT_GOLDEN"
INPUT_KIND = l3.KIND
EXPECTED_SOURCE_RUN = "40270383643"
EXPECTED_COUNT = 39
MAX_DETAIL_REQUESTS = 40
PER_REQUEST_DELAY = 1.5
BUDGET_SECONDS = 240


def canonical_key(url):
    """Bind a specific official exhibition detail ID; no external or fallback."""
    if not isinstance(url, str) or not l3.allowed(url):
        return None
    p = urlsplit(url)
    if p.path != "/exhibition_more.aspx":
        return None
    ids = parse_qs(p.query).get("id", [])
    if len(ids) != 1 or not re.fullmatch(r"\d{2,12}", ids[0]):
        return None
    return ids[0]


def normalize_title(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value))).casefold()


def raw_period_matches(raw, start, end):
    """Never infer a year from MM/DD; only cross-check a full official detail date."""
    if raw == "延期未定":
        return False
    if not isinstance(raw, str) or not l3.PERIOD_RE.fullmatch(raw):
        return False
    parts = re.split(r"\s*[~～-]\s*", raw)
    if len(parts) != 2:
        return False
    def md(value):
        month, day = value.split("/")
        return int(month), int(day)
    return md(parts[0]) == (start.month, start.day) and md(parts[1]) == (end.month, end.day)


def extract_verified_date(html, event, observed_url):
    """Require heading identity + exact official detail id + source period parity."""
    requested = event.get("detail_url")
    if canonical_key(requested) is None:
        return {"state": "MISSING_OFFICIAL_DETAIL_ID"}
    if canonical_key(observed_url) != canonical_key(requested):
        return {"state": "REDIRECT_EVENT_ID_MISMATCH"}
    soup = BeautifulSoup(html, "html.parser")
    title = event.get("title", "")
    title_norm = normalize_title(title)
    headings = [normalize_title(x.get_text(" ", strip=True))
                for x in soup.find_all(["h1", "h2", "h3"])]
    if title_norm not in headings:
        return {"state": "DETAIL_HEADING_MISMATCH"}
    parsed = l3.parse_detail_date(html, title)
    if parsed.get("state") != "DETAIL_DATE_CANDIDATE":
        return {"state": parsed.get("state", "DETAIL_DATE_UNKNOWN")}
    try:
        start, end = date.fromisoformat(parsed["start"]), date.fromisoformat(parsed["end"])
    except (TypeError, ValueError, KeyError):
        return {"state": "INVALID_OFFICIAL_DATE"}
    if start > end:
        return {"state": "INVERTED_OFFICIAL_DATE"}
    if not raw_period_matches(event.get("event_period_raw"), start, end):
        return {"state": "LIST_DETAIL_PERIOD_CONFLICT", "list_period_raw": event.get("event_period_raw")}
    return {"state": "DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE",
            "start": start.isoformat(), "end": end.isoformat(),
            "source_time_role": "OFFICIAL_EXHIBITION_DATE",
            "detail_url": requested, "event_id": canonical_key(requested)}


def validate_input(items, diagnostics):
    """Frozen source provenance prevents mixing one date with another event."""
    if not isinstance(diagnostics, dict) or diagnostics.get("kind") != INPUT_KIND:
        raise ValueError("HOLD_WRONG_L3A_SOURCE_KIND")
    for key in ("golden_accepted", "writer_executed",
                "notification_executed", "app_data_published"):
        if diagnostics.get(key) is not False:
            raise ValueError("HOLD_UNSAFE_SOURCE_" + key)
    if diagnostics.get("auto_hidden") != 0 or diagnostics.get("source_runtime") != "DORMANT":
        raise ValueError("HOLD_SOURCE_RUNTIME")
    if not isinstance(items, list) or len(items) != EXPECTED_COUNT:
        raise ValueError("HOLD_FROZEN_SOURCE_COUNT")
    if diagnostics.get("unique_candidates") != EXPECTED_COUNT:
        raise ValueError("HOLD_BASELINE_DIAGNOSTICS_COUNT")
    unique = set()
    for row in items:
        if not isinstance(row, dict) or row.get("platform") != "台北世貿":
            raise ValueError("HOLD_PLATFORM")
        if row.get("golden_verified") is not False or row.get("ticket_availability") != "UNKNOWN":
            raise ValueError("HOLD_INVALID_CANDIDATE_AUTHORITY")
        if not isinstance(row.get("title"), str) or len(row["title"].strip()) < 3:
            raise ValueError("HOLD_TITLE")
        url = row.get("detail_url")
        if url is not None and (canonical_key(url) is None or row.get("official_url") != url):
            raise ValueError("HOLD_DETAIL_URL")
        identity = (row["title"], row.get("official_url"), row.get("event_period_raw"))
        if identity in unique:
            raise ValueError("HOLD_DUPLICATE_SOURCE_ROWS")
        unique.add(identity)


def run(session, items, delay=PER_REQUEST_DELAY, timeout=12, clock=time.monotonic,
        sleeper=time.sleep):
    """One GET for each unique official detail ID, max 40, no retry, hard time budget."""
    if delay < 1.0 or not 4 <= timeout <= 20:
        raise ValueError("HOLD_REQUEST_BUDGET")
    records, fetched, begin = [], set(), clock()
    for row in items:
        url = row.get("detail_url")
        item = {"title": row["title"], "official_url": row.get("official_url"),
                "detail_url": url, "source_period_raw": row.get("event_period_raw"),
                "list_provenance_id": row.get("provenance_id"),
                "state": "NO_OFFICIAL_DETAIL_URL"}
        records.append(item)
        ident = canonical_key(url)
        if ident is None:
            continue
        if ident in fetched:
            item["state"] = "DUPLICATE_DETAIL_ID_HOLD"
            continue
        if len(fetched) >= MAX_DETAIL_REQUESTS or clock() - begin > BUDGET_SECONDS:
            item["state"] = "REQUEST_BUDGET_HOLD"
            continue
        if fetched:
            sleeper(delay)
        fetched.add(ident)
        html, meta = l3.get_html(session, url, timeout)
        item["http_status"] = meta.get("http_status")
        item["response_sha256"] = meta.get("sha256")
        item["observed_url"] = meta.get("url")
        item["http_state"] = meta.get("state")
        if html is None:
            item["state"] = "HTTP_DETAIL_HOLD"
            continue
        parsed = extract_verified_date(html, row, meta.get("url"))
        item.update(parsed)
    counts = Counter(item["state"] for item in records)
    return records, {"requests_attempted": len(fetched),
                     "date_verified": counts["DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE"],
                     "candidate_count": len(records),
                     "states": dict(sorted(counts.items())),
                     "remaining_unverified": len(records) - counts["DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--delay", type=float, default=PER_REQUEST_DELAY)
    ap.add_argument("--timeout", type=int, default=12)
    args = ap.parse_args(argv)
    out = Path(args.out).resolve()
    docs = Path("docs").resolve()
    if out == docs or docs in out.parents:
        ap.error("HOLD_PAGES_WRITE")
    root = Path(args.input_dir)
    a = (root / "candidate.json").read_bytes()
    b = (root / "diagnostics.json").read_bytes()
    items = json.loads(a.decode("utf-8"))
    diagnostics = json.loads(b.decode("utf-8"))
    validate_input(items, diagnostics)
    with requests.Session() as session:
        evidence, counts = run(session, items, args.delay, args.timeout)
    result = {
        "kind": KIND, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_id": EXPECTED_SOURCE_RUN,
        "source_file_sha256": {"candidate": hashlib.sha256(a).hexdigest(),
                               "diagnostics": hashlib.sha256(b).hexdigest()},
        "source_candidate_count": len(items), "counts": counts, "records": evidence,
        "source_runtime": "DORMANT", "golden_accepted": False, "auto_hidden": 0,
        "app_data_published": False, "writer_executed": False,
        "notification_executed": False, "full_catalog_coverage_proven": False,
        "accepted_fields": ["event_date_start", "event_date_end"],
        "identity_gate": "OFFICIAL_URL_ID+HEADING+RAW_PERIOD_PARITY",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "detail_date_evidence.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("START P30_L4A_TWTC_DETAIL_DATE_EVIDENCE")
    print("INPUT", len(items), "GET", counts["requests_attempted"],
          "DATE_VERIFIED", counts["date_verified"], "HOLD", counts["remaining_unverified"])
    for state, value in counts["states"].items():
        print("STATE", state, value)
    print("PASS P30_L4A_EVIDENCE_CREATED_CANDIDATE_NOT_GOLDEN")
    print("GOLDEN_ACCEPTED=0 APP_DATA_PUBLISHED=false AUTO_HIDDEN=0")


if __name__ == "__main__":
    main()
