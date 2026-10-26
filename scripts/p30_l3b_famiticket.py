#!/usr/bin/env python3
"""P30-L3-B FamiTicket: bounded public-list URL candidate diagnosis.

One official /Home GET plus at most one same-site /Home/Activity/Info/ GET.
No bypass, credentials, hidden API, schedule, Pages writer or notifier.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.famiticket.com.tw/Home"
HOST = "www.famiticket.com.tw"
KIND = "EVENTRADAR_P30_L3B_FAMITICKET_LIST_CANDIDATE_ONLY"
MAX_BYTES = 1_500_000
MAX_LIST = 100
UA = "EventRadar-P30-readonly/1.0 (github.com/easonliu714/event_scraper_public)"
DETAIL_PATH_RE = re.compile(r"^/Home/Activity/Info/[A-Za-z0-9_-]{16,512}$", re.I)
IGNORE_TITLE = {"購票", "即將開賣", "活動探索", "活動詳情", "more", "立即購票", "查看更多"}


def allowlisted(url):
    """Restrict exact HTTPS origin and specific Home/info paths."""
    try:
        p = urlsplit(url)
        if (p.scheme != "https" or p.hostname != HOST or p.username is not None
                or p.password is not None or p.port not in (None, 443)
                or "\\" in p.path or ".." in p.path.split("/")):
            return False
        return p.path.rstrip("/") in ("/Home", "/Home/Index") or bool(DETAIL_PATH_RE.fullmatch(p.path))
    except ValueError:
        return False


def canonical_info(raw_href, source_url):
    if not isinstance(raw_href, str) or not raw_href or raw_href.startswith(("javascript:", "#")):
        return None
    final = urljoin(source_url, raw_href)
    if not allowlisted(final):
        return None
    p = urlsplit(final)
    if not DETAIL_PATH_RE.fullmatch(p.path):
        return None
    return urlunsplit(("https", HOST, p.path, "", ""))


def get_html(session, url, timeout=12):
    """At most 2 allowlisted redirects. Never retry blocked response."""
    first, trail = url, []
    for _ in range(3):
        if not allowlisted(url):
            return None, {"state": "URL_REJECTED", "requested_url": first, "trail": trail}
        try:
            with session.get(url, timeout=(6, timeout), stream=True,
                             allow_redirects=False, headers={"User-Agent": UA}) as res:
                status = res.status_code
                trail.append({"url": url, "http_status": status})
                if status in (301, 302, 303, 307, 308):
                    location = res.headers.get("location")
                    if not location:
                        return None, {"state": "REDIRECT_MISSING_LOCATION", "trail": trail}
                    url = urljoin(url, location)
                    continue
                ctype = res.headers.get("content-type", "")[:100]
                meta = {"state": "HTTP_OK" if status == 200 else "HTTP_ERROR",
                        "requested_url": first, "observed_url": url,
                        "http_status": status, "content_type": ctype, "trail": trail}
                if status != 200:
                    return None, meta
                if "text/html" not in ctype.lower():
                    meta["state"] = "NON_HTML"
                    return None, meta
                raw = bytearray()
                for chunk in res.iter_content(chunk_size=32768):
                    raw.extend(chunk)
                    if len(raw) > MAX_BYTES:
                        meta["state"] = "OVERSIZED_HTML"
                        return None, meta
                if not raw:
                    meta["state"] = "EMPTY_HTML"
                    return None, meta
                meta["bytes"] = len(raw)
                meta["html_sha256"] = hashlib.sha256(raw).hexdigest()
                return bytes(raw), meta
        except requests.RequestException as err:
            return None, {"state": "NETWORK_ERROR", "error_type": type(err).__name__,
                          "requested_url": first, "trail": trail}
    return None, {"state": "REDIRECT_LIMIT", "requested_url": first, "trail": trail}


def parse_list(page, source_url):
    """Only source-bound detail links. Category/date text is NOT event-date evidence."""
    soup = BeautifulSoup(page, "html.parser")
    found, seen, total = [], set(), 0
    for a in soup.find_all("a", href=True):
        total += 1
        link = canonical_info(a.get("href", ""), source_url)
        if not link or link in seen:
            continue
        label = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
        if not label:
            label = re.sub(r"\s+", " ", str(a.get("title") or "")).strip()
        if len(label) < 4 or label.casefold() in IGNORE_TITLE:
            continue
        # Treat listing tokens (often including dates and '購票') as raw, not verified fields.
        found.append({
            "platform": "FamiTicket", "title": label[:180], "official_url": link,
            "source_list_url": source_url, "list_label_raw": label[:300],
            "source_level": "LIST_ONLY", "detail_status": "NOT_CHECKED",
            "date": None, "location": None, "price": None, "description": None,
            "category": "待確認", "category_basis": "UNVERIFIED",
            "source_time_role": "UNVERIFIED_LIST_TEXT",
            "ticket_availability": "UNKNOWN", "golden_verified": False,
        })
        seen.add(link)
        if len(found) >= MAX_LIST:
            break
    return found, {"anchors_seen": total, "candidate_count": len(found)}


def run(session, interval=1.0, timeout=12):
    if interval < 0.6:
        raise ValueError("HOLD_RATE_LIMIT")
    html, network = get_html(session, BASE_URL, timeout)
    rows, parsed = parse_list(html, network.get("observed_url", BASE_URL)) if html else ([], None)
    detail = {"state": "NOT_ATTEMPTED"}
    if rows:
        time.sleep(interval)
        detail_html, detail_net = get_html(session, rows[0]["official_url"], timeout)
        detail = {"state": "DETAIL_HTTP_OK" if detail_html else "DETAIL_HTTP_HOLD",
                  "url": rows[0]["official_url"], "http": detail_net}
        rows[0]["detail_status"] = detail["state"]
        # HTTP200/Title presence is not enough to trust price/event-time/category.
    report = {
        "kind": KIND, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "list": {"source_url": BASE_URL, "http": network, "parse": parsed},
        "detail_sample": detail, "candidate_count": len(rows),
        "list_get_max": 1, "detail_get_max": 1, "retry_count": 0,
        "golden_accepted": False, "auto_hidden": 0, "app_data_published": False,
        "source_runtime": "DORMANT", "writer_executed": False,
        "notification_executed": False, "full_catalog_coverage_proven": False,
    }
    return rows, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args(argv)
    if not (4 <= args.timeout <= 25 and args.interval >= 0.6):
        ap.error("HOLD_UNSAFE_REQUEST_BUDGET")
    output = Path(args.out).resolve()
    docroot = Path("docs").resolve()
    if output == docroot or docroot in output.parents:
        ap.error("HOLD_PAGES_OUTPUT_FORBIDDEN")
    with requests.Session() as session:
        candidates, report = run(session, args.interval, args.timeout)
    output.mkdir(parents=True, exist_ok=True)
    (output / "candidate.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "diagnostics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("START P30_L3B_FAMITICKET_ONE_SHOT")
    print("HTTP", report["list"]["http"].get("http_status"),
          "LIST", len(candidates), "DETAIL", report["detail_sample"]["state"])
    print("PASS P30_L3B_LIST_CANDIDATES_OBSERVED_NOT_GOLDEN" if candidates
          else "HOLD P30_L3B_FAMITICKET_LIST_EMPTY_OR_BLOCKED")
    print("PASS P30_L3B_REPORT_ONLY_NO_DATA_PUBLISH")
    print("GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 APP_DATA_PUBLISHED=false SOURCE_RUNTIME=DORMANT")


if __name__ == "__main__":
    main()
