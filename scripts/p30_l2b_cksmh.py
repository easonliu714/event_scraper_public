#!/usr/bin/env python3
"""P30-L2-B CKSMH: bounded official public HTML/list/detail probe, candidate only.

No credentials, bypass, retry, scheduler, DB/Pages writer or notification.
Only approved CKSMH paths on event.culture.tw. Live CLI is one-shot per CI push.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

HOST = "event.culture.tw"
LIST_URLS = (
    "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr",
    "https://event.culture.tw/CKSMH",
)
DETAIL_PREFIX = "/mocweb/reg/CKSMH/Detail.init.ctr"
PORTAL_DETAIL = "/CKSMH/portal/Registration/C0103MAction"
MAX_HTML = 1_500_000
MAX_EVENTS = 60
USER_AGENT = "EventRadar-P30-readonly/1.0 (github.com/easonliu714/event_scraper_public)"
EVIDENCE_KIND = "EVENTRADAR_P30_L2B_CKSMH_PROBE_NOT_GOLDEN"


def allowlisted(url):
    """Origin and CKSMH-path validation before each redirect and detail request."""
    try:
        p = urlsplit(url)
        path = p.path.lower()
        if (p.scheme != "https" or p.username or p.password
                or p.hostname != HOST or p.port not in (None, 443)
                or "\\" in p.path or any(x == ".." for x in p.path.split("/"))
                or not (path == "/cksmh" or path.startswith("/cksmh/")
                        or path.startswith("/mocweb/reg/cksmh/"))):
            return False
        return True
    except ValueError:
        return False


def get_html(session, url, timeout=12):
    """At most two redirects; no retry, no second origin, byte-bounded response."""
    initial = url
    trail = []
    for _ in range(3):
        if not allowlisted(url):
            return None, {"state": "URL_REJECTED", "requested_url": initial, "trail": trail}
        try:
            with session.get(url, allow_redirects=False, stream=True,
                             headers={"User-Agent": USER_AGENT},
                             timeout=(6, timeout)) as response:
                status = response.status_code
                trail.append({"url": url, "http_status": status})
                if status in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        return None, {"state": "REDIRECT_NO_LOCATION", "trail": trail}
                    url = urljoin(url, location)
                    continue
                ct = response.headers.get("content-type", "")[:100]
                meta = {"state": "HTTP_OK" if status == 200 else "HTTP_ERROR",
                        "requested_url": initial, "observed_url": url,
                        "http_status": status, "trail": trail, "content_type": ct}
                if status != 200:
                    return None, meta
                if "text/html" not in ct.lower():
                    meta["state"] = "NOT_HTML"
                    return None, meta
                body = bytearray()
                for part in response.iter_content(chunk_size=32_768):
                    body.extend(part)
                    if len(body) > MAX_HTML:
                        meta["state"] = "TOO_LARGE"
                        return None, meta
                if not body:
                    meta["state"] = "EMPTY_BODY"
                    return None, meta
                meta["bytes"] = len(body)
                meta["sha256"] = hashlib.sha256(body).hexdigest()
                return bytes(body), meta
        except requests.RequestException as ex:
            return None, {"state": "NETWORK_ERROR", "error_type": type(ex).__name__,
                          "requested_url": initial, "trail": trail}
    return None, {"state": "REDIRECT_LIMIT", "requested_url": initial, "trail": trail}


def canonical_detail(raw, listing_url):
    """Conservative actId-specific URL. Strip session ID and tracking parameters."""
    full = urljoin(listing_url, raw)
    if not allowlisted(full):
        return None
    p = urlsplit(full)
    path = p.path.split(";", 1)[0]
    if path not in (DETAIL_PREFIX, PORTAL_DETAIL):
        return None
    act = parse_qs(p.query).get("actId", [])
    if len(act) != 1 or not re.fullmatch(r"[0-9]{3,9}", act[0]):
        return None
    return urlunsplit(("https", HOST, path, "actId=" + act[0], ""))


def parse_list(data, source_url):
    """Link-backed, identity-bound event list; no title/date speculation."""
    soup = BeautifulSoup(data, "html.parser")
    events = []
    seen = set()
    anchors_seen = 0
    detail_like_anchors = 0
    for a in soup.find_all("a", href=True):
        anchors_seen += 1
        raw = (a.get("href") or "").strip()
        if "actId=" in raw or "Detail.init.ctr" in raw or "C0103MAction" in raw:
            detail_like_anchors += 1
        target = canonical_detail(raw, source_url)
        if not target or target in seen:
            continue
        title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
        if not title:
            title = (a.get("title") or "").strip()
        if len(title) < 3 or title in ("詳內容", "報名", "立即報名", "活動詳情", "詳細內容"):
            continue
        seen.add(target)
        events.append({
            "platform": "中正紀念堂", "title": title[:180],
            "official_url": target, "source_list_url": source_url,
            "source_level": "LIST_ONLY", "date": None, "location": None,
            "price": None, "description": None, "ticket_availability": "UNKNOWN",
            "category_basis": "UNVERIFIED", "golden_verified": False,
        })
        if len(events) >= MAX_EVENTS:
            break
    return events, {"anchors_seen": anchors_seen,
                    "detail_like_anchors": detail_like_anchors,
                    "list_candidates": len(events)}


def run(session, delay=1.0, timeout=12, fetch_detail=True):
    """One GET per entry (two total), optional single first detail; nothing more."""
    if delay < 0.6:
        raise ValueError("HOLD_RATE_LIMIT_TOO_SMALL")
    records = []
    seen = set()
    sources = []
    for idx, url in enumerate(LIST_URLS):
        if idx:
            time.sleep(delay)
        html, meta = get_html(session, url, timeout)
        evidence = {"source": url, "http": meta, "parse": None}
        sources.append(evidence)
        if html is None:
            continue
        rows, counts = parse_list(html, meta["observed_url"])
        evidence["parse"] = counts
        for row in rows:
            if row["official_url"] not in seen:
                seen.add(row["official_url"])
                records.append(row)
    detail = {"state": "NOT_ATTEMPTED"}
    if fetch_detail and records:
        time.sleep(delay)
        html, meta = get_html(session, records[0]["official_url"], timeout)
        detail = {"official_url": records[0]["official_url"], "http": meta,
                  "state": "DETAIL_HTTP_OK" if html is not None else "DETAIL_HOLD"}
        # A detail HTTP 200 is not confirmation of the event's dates or identity.
    report = {
        "kind": EVIDENCE_KIND,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": sources, "detail_sample": detail,
        "http_ok_entries": sum(x["http"]["state"] == "HTTP_OK" for x in sources),
        "list_nonempty_entries": sum(
            x["parse"] is not None and x["parse"]["list_candidates"] > 0
            for x in sources),
        "unique_list_candidates": len(records),
        "fetch_budget": {"list_entries": 2, "detail_max": 1, "no_retries": True},
        "source_runtime": "DORMANT", "writer_executed": False,
        "notification_executed": False, "golden_accepted": False,
        "app_data_published": False, "auto_hidden": 0,
    }
    return records, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args(argv)
    if not (4 <= args.timeout <= 20 and args.delay >= 0.6):
        ap.error("HOLD_UNSAFE_BUDGET")
    dest = Path(args.out).resolve()
    if dest == Path("docs").resolve() or Path("docs").resolve() in dest.parents:
        ap.error("HOLD_PAGES_OUTPUT_FORBIDDEN")
    with requests.Session() as session:
        items, evidence = run(session, args.delay, args.timeout)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "candidate.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "diagnostics.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("START P30_L2B_CKSMH_ONE_SHOT")
    for entry in evidence["sources"]:
        print("LIST", entry["source"], "STATE", entry["http"]["state"],
              "HTTP", entry["http"].get("http_status"),
              "CANDIDATES", (entry["parse"] or {}).get("list_candidates", 0))
    print("DETAIL_SAMPLE", evidence["detail_sample"]["state"])
    if evidence["unique_list_candidates"] > 0 and evidence["list_nonempty_entries"]:
        print("PASS P30_L2B_CKSMH_LIST_CANDIDATE_OBSERVED_NOT_GOLDEN")
    else:
        print("HOLD P30_L2B_CKSMH_LIVE_LIST_NOT_CONFIRMED")
    print("PASS P30_L2B_BOUNDED_REPORT_NO_WRITE")
    print("GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 APP_DATA_PUBLISHED=false SOURCE_RUNTIME=DORMANT")


if __name__ == "__main__":
    main()
