#!/usr/bin/env python3
"""P30 one-shot, bounded, read-only live acquisition diagnostic.

Never import/execute scraper.py or show_news.py: both expose writers/notifiers.
Only HTTPS allowlisted public list/detail pages; no credentials, no scheduler,
no updates to docs/data.json and no notifications. Results are candidates only.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup, UnicodeDammit

# One public list entry per known platform; no search blasting or paging.
PLATFORMS = (
    ("KKTIX", "https://kktix.com/events?category_id=2", ("kktix.com", "kktix.cc"), r"/events/"),
    ("ACCUPASS", "https://www.accupass.com/search?q=%E9%9F%B3%E6%A8%82", ("accupass.com",), r"/event/"),
    ("拓元售票", "https://tixcraft.com/activity", ("tixcraft.com",), r"/activity/detail/"),
    ("寬宏", "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205", ("kham.com.tw",), r"UTK0201"),
    ("OPENTIX", "https://www.opentix.life/event", ("opentix.life",), r"/event/[0-9]"),
    ("UDN售票網", "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList", ("udnfunlife.com",), r"UTK0201"),
    ("FamiTicket", "https://www.famiticket.com.tw/Home/Activity/Search/242", ("famiticket.com.tw",), r"/Activity/Info"),
    ("年代售票", "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77", ("ticket.com.tw",), r"UTK0201"),
    ("TixFun售票網", "https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77", ("tixfun.com",), r"UTK0201"),
    ("Event Go", "https://eventgo.bnextmedia.com.tw/", ("bnextmedia.com.tw",), r"/event/detail"),
    ("BeClass", "https://www.beclass.com/default.php?name=ShowList&op=recent", ("beclass.com",), r"rid="),
    ("ibon", "https://ticket.ibon.com.tw/Activity/Index", ("ibon.com.tw",), r"/Activity/"),
    ("華山1914", "https://www.huashan1914.com/w/huashan1914/exhibition", ("huashan1914.com",), r"/exhibition/"),
    ("松山文創", "https://www.songshanculturalpark.org/", ("songshanculturalpark.org",), r"/exhibition/|/events?/"),
    ("KidsClub", "https://www.kidsclub.com.tw/", ("kidsclub.com.tw",), r"/courses/|/product/"),
    ("台北世貿", "https://www.twtc.com.tw/", ("twtc.com.tw",), r"/event/|/exhibition/"),
    ("中正紀念堂", "https://event.culture.tw/mocweb/reg/CKSMH/", ("culture.tw",), r"/Detail\.|actId="),
    ("iNDIEVOX", "https://www.indievox.com/activity/list", ("indievox.com",), r"/activity/detail"),
    ("StrollTimes", "https://strolltimes.com/", ("strolltimes.com",), r"/20[0-9]{2}/"),
)
USER_AGENT = "EventRadar-P30-audit/1.0 (one-shot public diagnostics; github.com/easonliu714/event_scraper_public)"
MAX_HTML_BYTES = 2_000_000
MAX_LIST_PER_PLATFORM = 120
IGNORE_EXACT = {"more", "read more", "立即購票", "購票", "活動詳情", "詳細內容", "了解更多", "查看更多", "下一頁", "首頁"}
CANONICAL_SOURCE = "fc4f963247d68eed29425808cc14e7250f312d05"
PURE_PARSER_SHA = "4c2c9ec93ae90410230a074e09b2aa853b7bfcf0"


def allowed(url, hosts):
    """Reject private IP, credentials, custom port, downgrade and foreign redirects."""
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower()
        return (p.scheme == "https" and p.username is None and p.password is None
                and p.port in (None, 443) and bool(host) and
                any(host == suffix or host.endswith("." + suffix) for suffix in hosts))
    except ValueError:
        return False


def get_html(session, url, hosts, timeout):
    """One GET + at most two allowlisted redirects. Never bypass HTTP blocks."""
    trail = []
    for _ in range(3):
        if not allowed(url, hosts):
            return None, {"status": "URL_NOT_ALLOWLISTED", "requested_url": url, "trail": trail}
        try:
            with session.get(url, timeout=(6, timeout), allow_redirects=False,
                             stream=True, headers={"User-Agent": USER_AGENT}) as response:
                status = response.status_code
                trail.append({"http_status": status, "url": url})
                if status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location", "")
                    if not location:
                        return None, {"status": "REDIRECT_WITHOUT_LOCATION", "trail": trail}
                    url = urljoin(url, location)
                    continue
                meta = {"status": "HTTP_OK" if status == 200 else "HTTP_ERROR",
                        "http_status": status, "url": url, "trail": trail,
                        "content_type": response.headers.get("content-type", "")[:100]}
                if status != 200:
                    return None, meta
                if "text/html" not in meta["content_type"].lower():
                    meta["status"] = "NON_HTML"
                    return None, meta
                content = bytearray()
                for chunk in response.iter_content(chunk_size=32768):
                    content.extend(chunk)
                    if len(content) > MAX_HTML_BYTES:
                        meta["status"] = "OVERSIZE_HTML"
                        return None, meta
                if not content:
                    meta["status"] = "EMPTY_RESPONSE"
                    return None, meta
                meta["bytes"] = len(content)
                meta["html_sha256"] = hashlib.sha256(content).hexdigest()
                decoded = UnicodeDammit(bytes(content), is_html=True).unicode_markup
                return (decoded or bytes(content).decode("utf-8", errors="replace")), meta
        except requests.RequestException as error:
            return None, {"status": "NETWORK_ERROR",
                          "error_type": type(error).__name__, "trail": trail}
    return None, {"status": "REDIRECT_LIMIT", "trail": trail}


def parse_list(html, platform, base_url, hosts, href_pattern):
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    rows = []
    anchors = soup.find_all("a", href=True)
    for el in anchors:
        href = el.get("href") or ""
        full = urljoin(base_url, href).split("#")[0]
        if not allowed(full, hosts) or not re.search(href_pattern, full, re.I):
            continue
        if full in seen:
            continue
        label = (el.get("title") or "").strip()
        if not label:
            inner = el.find(["h2", "h3", "h4", "h5", "img"])
            label = (inner.get("alt", "") if inner and inner.name == "img" else
                     inner.get_text(" ", strip=True) if inner else "")
        if not label:
            label = el.get_text(" ", strip=True)
        label = re.sub(r"\s+", " ", label).strip()[:180]
        if len(label) < 3 or label.casefold() in IGNORE_EXACT:
            continue
        seen.add(full)
        rows.append({"url": full, "title": label, "platform": platform,
                     "date": None, "location": None, "price": None, "description": None,
                     "type": "其他", "category_basis": "UNVERIFIED",
                     "ticket_availability": "UNKNOWN", "source_level": "LIST_ONLY",
                     "detail_status": "NOT_CHECKED", "official_url": full})
        if len(rows) >= MAX_LIST_PER_PLATFORM:
            break
    return rows, len(anchors)


def load_pure_parser(file_path):
    if not file_path:
        return None
    path = Path(file_path)
    if not path.is_file():
        raise RuntimeError("HOLD_P30_PINNED_PARSER_MISSING")
    spec = importlib.util.spec_from_file_location("p30_pinned_pure_detail", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "parse_detail", None)):
        raise RuntimeError("HOLD_P30_PINNED_PARSER_UNAVAILABLE")
    return module.parse_detail


def merge_detail(row, evidence):
    """Never upgrade unbound date to Golden or assert ticket availability."""
    updated = dict(row)
    if not isinstance(evidence, dict):
        return updated
    for key in ("date", "location", "price", "description", "img_url"):
        value = evidence.get(key)
        if isinstance(value, str) and value.strip():
            updated[key] = value.strip()[:1200]
    updated["source_page_type"] = evidence.get("source_page_type", "UNKNOWN")
    updated["source_identity_status"] = evidence.get("source_identity_status", "UNKNOWN")
    updated["source_time_role"] = evidence.get("source_time_role", "UNKNOWN")
    if "event_session_candidate_count" in evidence:
        updated["event_session_candidate_count"] = evidence["event_session_candidate_count"]
    updated["source_level"] = "DETAIL_PARSED" if any(
        updated.get(k) for k in ("date", "location", "price", "description")) else "DETAIL_SCANNED_NO_FIELDS"
    return updated


def run(args, session=None, parser=None, sleeper=time.sleep):
    created = datetime.now(timezone.utc).isoformat()
    owned_session = session is None
    if session is None:
        session = requests.Session()
    session.headers.update({"Accept": "text/html,application/xhtml+xml;q=0.9"})
    parser = parser if parser is not None else load_pure_parser(args.parser_file)
    if parser is None:
        raise RuntimeError("HOLD_NO_PINNED_DETAIL_PARSER")
    all_rows, results, seen_urls = [], [], set()
    begin = time.monotonic()
    try:
        for platform, listing_url, hosts, pattern in PLATFORMS[:args.platform_limit]:
            item = {"platform": platform, "listing_url": listing_url,
                    "stage1": "NOT_STARTED", "stage2": "NOT_STARTED",
                    "stage3": "NOT_STARTED", "stage4": "NOT_STARTED",
                    "list_candidates": 0, "detail_checked": 0, "detail_http_ok": 0,
                    "detail_fields": {"date": 0, "location": 0, "price": 0, "description": 0}}
            results.append(item)
            if time.monotonic() - begin > args.max_seconds:
                item["stage1"] = "BUDGET_EXHAUSTED"
                continue
            html, net = get_html(session, listing_url, hosts, args.timeout)
            item["list_http"] = net
            item["stage1"] = net["status"]
            if html is None:
                item["stage2"] = "BLOCKED_BY_STAGE1"
                continue
            rows, anchors = parse_list(html, platform, net["url"], hosts, pattern)
            item["anchors_seen"] = anchors
            item["list_candidates"] = len(rows)
            item["stage2"] = "LIST_CANDIDATES" if rows else "LIST_EMPTY_OR_JS_RENDERED"
            for row in rows:
                if row["url"] in seen_urls:
                    continue
                seen_urls.add(row["url"])
                all_rows.append(row)
            # Detail samples only: do not fetch every listed activity.
            detail_rows = rows[:args.detail_per_platform]
            for row in detail_rows:
                if time.monotonic() - begin > args.max_seconds:
                    item["stage3"] = "BUDGET_EXHAUSTED"
                    break
                sleeper(args.min_interval)
                detail_html, detail_net = get_html(session, row["url"], hosts, args.timeout)
                item["detail_checked"] += 1
                row["detail_http_status"] = detail_net.get("http_status")
                row["detail_status"] = detail_net["status"]
                if detail_html is None:
                    continue
                item["detail_http_ok"] += 1
                try:
                    parsed = parser(detail_html, expected_url=detail_net["url"])
                    row.update(merge_detail(row, parsed))
                    row["detail_status"] = "PARSED"
                    for field in item["detail_fields"]:
                        if row.get(field):
                            item["detail_fields"][field] += 1
                except Exception as error:
                    row["detail_status"] = "PARSER_EXCEPTION"
                    row["parser_error"] = type(error).__name__
            item["stage3"] = ("DETAIL_OK" if item["detail_http_ok"] else
                              "DETAIL_NOT_REACHED" if not item["detail_checked"] else "DETAIL_HTTP_FAILED")
            item["stage4"] = ("FIELD_CANDIDATES" if sum(item["detail_fields"].values()) else
                              "NO_VERIFIED_FIELD_CANDIDATES")
            sleeper(args.min_interval)
    finally:
        if owned_session:
            session.close()
    counts = {"platforms_checked": len(results),
              "http_ok_platforms": sum(x["stage1"] == "HTTP_OK" for x in results),
              "list_nonempty_platforms": sum(x["list_candidates"] > 0 for x in results),
              "total_list_candidates": len(all_rows),
              "detail_attempts": sum(x["detail_checked"] for x in results),
              "detail_http_ok": sum(x["detail_http_ok"] for x in results),
              "detail_parsed_records": sum(
                  x["detail_status"] == "PARSED" for x in all_rows)}
    report = {"kind": "EVENTRADAR_P30_FRESH_DIAGNOSTIC_CANDIDATE",
              "generated_at_utc": created,
              "source_main_sha_at_design": CANONICAL_SOURCE,
              "detail_parser_pr_head_sha": PURE_PARSER_SHA,
              "golden_accepted": False, "app_data_published": False,
              "source_runtime": "DORMANT", "auto_hidden": 0,
              "writer_executed": False, "notification_executed": False,
              "full_catalog_coverage_proven": False, "counts": counts, "platforms": results}
    return all_rows, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="p30-artifacts")
    ap.add_argument("--parser-file", required=True)
    ap.add_argument("--platform-limit", type=int, default=len(PLATFORMS))
    ap.add_argument("--detail-per-platform", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--min-interval", type=float, default=1)
    ap.add_argument("--max-seconds", type=int, default=1000)
    args = ap.parse_args(argv)
    if not 1 <= args.platform_limit <= len(PLATFORMS):
        ap.error("invalid platform limit")
    if not 0 <= args.detail_per_platform <= 2:
        ap.error("detail-per-platform must be 0..2")
    if not 4 <= args.timeout <= 30 or args.min_interval < 0.6:
        ap.error("unsafe timeout/interval")
    output = Path(args.out)
    if output.resolve().is_relative_to(Path("docs").resolve()):
        ap.error("writing to docs/ is forbidden")
    output.mkdir(parents=True, exist_ok=True)
    records, report = run(args)
    (output / "candidate.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "diagnostics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("START P30_LIVE_DIAGNOSTIC")
    for p in report["platforms"]:
        print("PLATFORM", p["platform"], "HTTP", p["stage1"], "LIST", p["list_candidates"],
              "DETAIL", p["detail_http_ok"], "/", p["detail_checked"],
              "FIELDS", sum(p["detail_fields"].values()))
    print("PASS P30_DIAGNOSTIC_ARTIFACTS_CREATED_NOT_GOLDEN")
    print("SOURCE_RUNTIME=DORMANT GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 APP_DATA_PUBLISHED=false")


if __name__ == "__main__":
    main()
