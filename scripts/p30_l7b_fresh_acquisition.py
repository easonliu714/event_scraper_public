#!/usr/bin/env python3
"""P30-L7-B: bounded real HTTP -> list -> identity-bound detail -> review-only evidence.

One-shot and isolated: no imports from scraper.py, no schedule, Writer, DB, notifier,
browser impersonation, anti-bot bypass, or production JSON/PWA mutation.
A successful HTTP GET is NOT equivalent to an event list or verified field.
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
from bs4 import BeautifulSoup, UnicodeDammit

KIND = "EVENTRADAR_P30_L7B_FRESH_BOUNDED_CANDIDATES_V1"
VERSION = "1.0.0"
SOURCE_MAIN = "fc4f963247d68eed29425808cc14e7250f312d05"
SOURCE_PARENT = "17d189c5615cdd58db3ea0e7e1ea9472a5ab1cc8"
UA = "EventRadar-P30-L7B/1.0 (bounded public-source quality audit; GitHub easonliu714/event_scraper_public)"
MAX_BYTES = 1200000
MAX_CANDIDATES = 40
MAX_REDIRECTS = 2
MAX_FIELD_EVIDENCE = 12
NOISE = {"read more", "more", "詳細內容", "活動詳情", "立即購票", "購票", "了解更多", "下一頁", "查看更多", "更多", "首頁"}
# Platform endpoints pinned from previously audited isolated P30 source code, NOT cached HTTP.
# P30-L3A TWTC official exhibition table; L4B CKSMH Query.list; L3BA Fami Home;
# L3BB ibon entertainment shell. 403/empty/JS remain HOLD with no bypass.
PLATFORMS = (
    ("KKTIX", "https://kktix.com/events?category_id=2", ("kktix.com", "kktix.cc"), r"/events/"),
    ("ACCUPASS", "https://www.accupass.com/search?q=%E9%9F%B3%E6%A8%82", ("accupass.com",), r"/event/"),
    ("拓元售票", "https://tixcraft.com/activity", ("tixcraft.com",), r"/activity/detail/"),
    ("寬宏", "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205", ("kham.com.tw",), r"UTK0201"),
    ("OPENTIX", "https://www.opentix.life/event", ("opentix.life",), r"/event/[0-9]"),
    ("UDN售票網", "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList", ("udnfunlife.com",), r"UTK0201"),
    ("FamiTicket", "https://www.famiticket.com.tw/Home", ("famiticket.com.tw",), r"/Activity/Info"),
    ("年代售票", "https://ticket.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=77", ("ticket.com.tw",), r"UTK0201"),
    ("TixFun售票網", "https://tixfun.com/UTK0101_?TYPE=1&CATEGORY=77", ("tixfun.com",), r"UTK0201"),
    ("Event Go", "https://eventgo.bnextmedia.com.tw/", ("bnextmedia.com.tw",), r"/event/detail"),
    ("BeClass", "https://www.beclass.com/default.php?name=ShowList&op=recent", ("beclass.com",), r"rid="),
    ("ibon", "https://ticket.ibon.com.tw/Index/entertainment", ("ibon.com.tw",), r"/(?:Web/|WebV3/)?ActivityInfo/Details/"),
    ("華山1914", "https://www.huashan1914.com/w/huashan1914/exhibition", ("huashan1914.com",), r"/exhibition/"),
    ("松山文創", "https://www.songshanculturalpark.org/", ("songshanculturalpark.org",), r"/exhibition/|/events?/"),
    ("KidsClub", "https://www.kidsclub.com.tw/", ("kidsclub.com.tw",), r"/courses/|/product/"),
    ("台北世貿", "https://twtc.com.tw/exhibition?p=home", ("twtc.com.tw",), r"exhibition_more\.aspx\?id="),
    ("中正紀念堂", "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr", ("culture.tw",), r"/Detail\.init\.ctr\?actId="),
    ("iNDIEVOX", "https://www.indievox.com/activity/list", ("indievox.com",), r"/activity/detail"),
    ("StrollTimes", "https://strolltimes.com/", ("strolltimes.com",), r"/events/"),
)
LABEL_ROLES = (
    ("EVENT_PERIOD", r"(?:活動日期|活動期間|展覽日期|展覽期間|展期|演出日期|開演時間)"),
    ("ADMISSION_TIME", r"(?:入場時間|開放入場|入場日期)"),
    ("REGISTRATION_PERIOD", r"(?:報名期間|報名時間|報名截止|報名開始)"),
    ("SALE_PERIOD", r"(?:售票期間|售票時間|開賣時間|預售期間|購票期間)"),
    ("VOUCHER_VALIDITY", r"(?:票券有效期間|使用期限|有效期限|兌換期間)"),
    ("VENUE", r"(?:活動地點|展覽地點|演出地點|演出場地|活動場地|地點|場館)"),
    ("PRICE", r"(?:票價|門票價格|購票價格|售價)"),
)
DATE_SIGNAL = re.compile(r"(?:20\d{2}\s*[-/年.]\s*\d{1,2}|\d{1,2}\s*[/月]\s*\d{1,2}|\d{1,2}:\d{2})")
JS_SIGNAL = re.compile(r"(?:__NEXT_DATA__|id=['\"]__next|ng-version|__NUXT__|enable javascript)", re.I)
WAF_SIGNAL = re.compile(r"(?:captcha|cloudflare|access denied|request blocked|verify you are human)", re.I)


def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def allow_url(url, hosts):
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower().rstrip(".")
        return (p.scheme == "https" and not p.username and not p.password
                and p.port in (None, 443) and bool(host)
                and not re.search(r"[\x00-\x20]", url)
                and any(host == h or host.endswith("." + h) for h in hosts))
    except ValueError:
        return False


def canonical_url(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path or "/", p.query, ""))


def classify_http(code):
    if code == 200:
        return "HTTP_OK"
    return {403: "HTTP_403_BLOCKED", 404: "HTTP_404_NOT_FOUND",
            429: "HTTP_429_RATE_LIMIT"}.get(code, "HTTP_ERROR")


def get_page(session, url, hosts, timeout, counts):
    """Count each actually attempted GET, no retry, allowlist each redirect hop."""
    trail = []
    for step in range(MAX_REDIRECTS + 1):
        if not allow_url(url, hosts):
            return None, {"state": "HOLD_URL_NOT_ALLOWLISTED", "trail": trail}
        try:
            counts["requests"] += 1
            with session.get(url, timeout=(5, timeout), allow_redirects=False, stream=True,
                             headers={"User-Agent": UA, "Accept": "text/html"}) as r:
                code = r.status_code
                trail.append({"url": url, "httpStatus": code})
                if code in (301, 302, 303, 307, 308):
                    loc = r.headers.get("Location", "")
                    if not loc:
                        return None, {"state": "HOLD_REDIRECT_NO_LOCATION", "trail": trail}
                    url = urljoin(url, loc)
                    continue
                meta = {"state": classify_http(code), "httpStatus": code,
                        "requestedUrl": url, "redirectTrail": trail,
                        "contentType": r.headers.get("content-type", "")[:100]}
                if code != 200:
                    return None, meta
                if "text/html" not in meta["contentType"].lower():
                    meta["state"] = "HOLD_NOT_HTML"
                    return None, meta
                raw = bytearray()
                for chunk in r.iter_content(chunk_size=32768):
                    raw.extend(chunk)
                    if len(raw) > MAX_BYTES:
                        meta["state"] = "HOLD_SIZE_LIMIT"
                        return None, meta
                if not raw:
                    meta["state"] = "HOLD_EMPTY_BODY"
                    return None, meta
                meta["bodySHA256"] = digest(bytes(raw))
                meta["bodyBytes"] = len(raw)
                html = UnicodeDammit(bytes(raw), is_html=True).unicode_markup
                return html or bytes(raw).decode("utf-8", errors="replace"), meta
        except requests.RequestException as exc:
            return None, {"state": "HOLD_NETWORK_ERROR", "exception": type(exc).__name__,
                          "redirectTrail": trail}
    return None, {"state": "HOLD_REDIRECT_LIMIT", "redirectTrail": trail}


def document_title(soup):
    og = soup.find("meta", attrs={"property": "og:title"})
    candidates = [og.get("content", "") if og else ""]
    for name in ("h1", "title"):
        tag = soup.find(name)
        candidates.append(tag.get_text(" ", strip=True) if tag else "")
    for c in candidates:
        clean = re.sub(r"\s+", " ", str(c)).strip()
        if len(clean) >= 3:
            return clean[:250]
    return None


def parse_list(html, platform, base, hosts, pattern):
    soup = BeautifulSoup(html, "html.parser")
    out, seen = [], set()
    anchors = soup.select("a[href]")
    for a in anchors:
        url = canonical_url(urljoin(base, a.get("href", "")))
        if not allow_url(url, hosts) or not re.search(pattern, url, re.I):
            continue
        title = a.get("title", "").strip() if isinstance(a.get("title"), str) else ""
        if not title:
            candidate = a.find(["h2", "h3", "h4", "h5", "img"])
            title = (candidate.get("alt", "") if candidate and candidate.name == "img"
                     else candidate.get_text(" ", strip=True) if candidate
                     else a.get_text(" ", strip=True))
        title = re.sub(r"\s+", " ", str(title)).strip()[:220]
        if len(title) < 3 or title.casefold() in NOISE or url in seen:
            continue
        seen.add(url)
        key = digest((platform + "\n" + url).encode())[:24]
        out.append({"candidateId": "er7b_" + key, "sourcePlatform": platform,
                    "sourceRole": ("THIRD_PARTY_AGGREGATOR_ARTICLE" if platform == "StrollTimes"
                                   else "PLATFORM_LISTED_EVENT_UNVERIFIED"),
                    "sourceUrl": url, "title": title, "listEvidence": {
                        "listUrl": base, "anchorText": title, "provenance": "FRESH_HTML_ANCHOR"},
                    "detailStatus": "NOT_SAMPLED", "detailTitle": None,
                    "detailIdentityVerified": False, "fieldEvidence": [],
                    "dateStart": None, "dateEnd": None, "eventTimeZone": None,
                    "venue": None, "price": None, "ticketStatus": "UNKNOWN",
                    "registrationPeriod": None, "saleWindow": None, "voucherValidity": None,
                    "category": "待分類", "mergeAllowed": False, "goldenVerified": False,
                    "published": False})
        if len(out) == MAX_CANDIDATES:
            break
    return out, {"anchorCount": len(anchors), "candidateLimitReached": len(out) == MAX_CANDIDATES,
                 "jsRenderingHint": bool(JS_SIGNAL.search(html[:100000])),
                 "wafHint": bool(WAF_SIGNAL.search(html[:100000]))}


def title_parity(list_title, detail_title):
    if not detail_title:
        return False
    norm = lambda s: re.sub(r"[\W_]+", "", s, flags=re.UNICODE).casefold()
    a, b = norm(list_title), norm(detail_title)
    return len(a) >= 6 and (a == b or a in b or (len(b) >= 6 and b in a))


def extract_fields(html, detail_url):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)[:150000]
    evidence = []
    for role, label in LABEL_ROLES:
        pat = re.compile(r"(?:^|\n)\s*(" + label + r")\s*[:：]?\s*(?:\n\s*)?([^\n]{2,110})", re.I)
        for match in pat.finditer(text):
            value = re.sub(r"\s+", " ", match.group(2)).strip()
            if not value or (role not in ("VENUE", "PRICE") and not DATE_SIGNAL.search(value)):
                continue
            evidence.append({"role": role, "label": match.group(1),
                             "observedValue": value[:110], "sourceUrl": detail_url,
                             "verification": "FRESH_LABEL_OBSERVED_REVIEW_REQUIRED"})
            if len(evidence) >= MAX_FIELD_EVIDENCE:
                return evidence
    return evidence


def safe_out(path):
    root = Path.cwd().resolve()
    dest = Path(path).resolve()
    if not dest.is_relative_to(root) or dest == root or any(
        dest == root / folder or dest.is_relative_to(root / folder)
        for folder in ("docs", ".git", "schemas", "scripts", "tests", ".github")
    ):
        raise ValueError("HOLD_ISOLATED_OUTPUT_PATH_REQUIRED")
    return dest


def audit(platforms, detail_per_platform=1, timeout=10, interval=0.7,
          max_seconds=450, session=None, sleeper=time.sleep):
    is_live = session is None
    session = session or requests.Session()
    session.headers.update({"Accept": "text/html"})
    started = iso_now()
    start_mono = time.monotonic()
    request_counter = {"requests": 0}
    diagnostics, candidates = [], []
    try:
        for name, entry, hosts, pattern in platforms:
            p = {"platform": name, "entryUrl": entry, "http": None,
                 "listState": "NOT_ATTEMPTED", "listCandidateCount": 0,
                 "detailAttempted": 0, "detailHttpOK": 0,
                 "detailIdentityVerified": 0, "fieldEvidenceObserved": 0}
            diagnostics.append(p)
            if time.monotonic() - start_mono > max_seconds:
                p["listState"] = "HOLD_TIME_BUDGET"
                continue
            body, p["http"] = get_page(session, entry, hosts, timeout, request_counter)
            if body is None:
                p["listState"] = "HOLD_HTTP"
                continue
            rows, extras = parse_list(body, name, p["http"]["requestedUrl"], hosts, pattern)
            p.update(extras)
            p["listCandidateCount"] = len(rows)
            p["listState"] = "LIST_CANDIDATES" if rows else "HOLD_NO_LIST_OR_JS_RENDERED"
            for row in rows[:detail_per_platform]:
                if time.monotonic() - start_mono > max_seconds:
                    row["detailStatus"] = "HOLD_TIME_BUDGET"
                    continue
                sleeper(interval)
                detail, meta = get_page(session, row["sourceUrl"], hosts, timeout, request_counter)
                p["detailAttempted"] += 1
                row["detailHttp"] = meta
                row["detailStatus"] = meta["state"]
                if detail is None:
                    continue
                p["detailHttpOK"] += 1
                detail_title = document_title(BeautifulSoup(detail, "html.parser"))
                row["detailTitle"] = detail_title
                row["detailIdentityVerified"] = title_parity(row["title"], detail_title)
                row["detailStatus"] = ("DETAIL_TITLE_PARITY_PASS" if row["detailIdentityVerified"]
                                       else "HOLD_DETAIL_TITLE_PARITY")
                if row["detailIdentityVerified"]:
                    p["detailIdentityVerified"] += 1
                    row["fieldEvidence"] = extract_fields(detail, meta["requestedUrl"])
                    p["fieldEvidenceObserved"] += len(row["fieldEvidence"])
            candidates.extend(rows)
            sleeper(interval)
    finally:
        if is_live:
            session.close()
    counts = {"platformsChecked": len(diagnostics),
              "httpOK": sum(x["http"].get("state") == "HTTP_OK" for x in diagnostics if x["http"]),
              "listPositive": sum(x["listCandidateCount"] > 0 for x in diagnostics),
              "listCandidates": len(candidates),
              "detailAttempts": sum(x["detailAttempted"] for x in diagnostics),
              "detailHttpOK": sum(x["detailHttpOK"] for x in diagnostics),
              "detailIdentityVerified": sum(x["detailIdentityVerified"] for x in diagnostics),
              "labelEvidenceObserved": sum(x["fieldEvidenceObserved"] for x in diagnostics)}
    actual = request_counter["requests"] if is_live else 0
    source_seal = digest(json.dumps([{"platform": p["platform"],
                                      "listBody": p["http"].get("bodySHA256"),
                                      "details": [x["detailHttp"].get("bodySHA256")
                                                  for x in candidates if x["sourcePlatform"] == p["platform"]
                                                  and "detailHttp" in x]} for p in diagnostics],
                                    ensure_ascii=False, sort_keys=True).encode())
    run_id = "P30-L7B-FRESH-" + started.replace("-", "").replace(":", "").replace("T", "-").replace("Z", "") + "-" + source_seal[:12]
    report = {"kind": "EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1",
              "runId": run_id, "collectedAtUTC": started, "candidateOrigin":
              ("L7B_ACTUAL_NEW_PUBLIC_HTTP" if is_live else "L7B_SYNTHETIC_TEST_INJECTION_NOT_FRESH"),
              "actualFreshHTTPRequests": actual, "observedTestRequests": (0 if is_live else request_counter["requests"]),
              "all19PlatformsAttempted": len(platforms) == 19,
              "fullPlatformCoverageVerified": False, "counts": counts, "platforms": diagnostics,
              "qualityGate": {
                  "http": "PASS" if counts["httpOK"] else "HOLD",
                  "list": "PASS" if counts["listPositive"] else "HOLD",
                  "detail": "PASS" if counts["detailIdentityVerified"] else "HOLD",
                  "fields": "REVIEW_ONLY" if counts["labelEvidenceObserved"] else "HOLD",
              }, "published": False, "goldenAccepted": 0, "writerExecuted": False,
              "notifierExecuted": False, "schedulerExecuted": False,
              "automaticMergeCount": 0, "automaticHideCount": 0, "deletedCount": 0,
              "historicalAndroid44Preserved": True, "sourceRuntime": "DORMANT"}
    output = {"kind": KIND, "schemaVersion": VERSION, "runId": run_id,
              "candidateOrigin": report["candidateOrigin"], "collectedAtUTC": started,
              "actualFreshHTTPRequests": actual, "fullPlatformCoverageVerified": False,
              "candidateCount": len(candidates), "candidateEventRecords": candidates,
              "goldenAccepted": 0, "published": False, "mergeAllowed": False,
              "formalFieldPromotionCount": 0}
    return output, report


def emit(output, report, root):
    dest = safe_out(root)
    dest.mkdir(parents=True, exist_ok=True)
    paths = {"fresh_candidate.json": output, "platform_diagnostics.json": report}
    manifest_files = {}
    for filename, obj in paths.items():
        payload = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
        (dest / filename).write_bytes(payload)
        manifest_files[filename] = digest(payload)
    manifest = {"kind": "EVENTRADAR_P30_L7B_ISOLATED_SHA_MANIFEST",
                "runId": report["runId"], "sourceMainSHA": SOURCE_MAIN,
                "sourceParentSHA": SOURCE_PARENT, "filesSHA256": manifest_files,
                "actualFreshHTTPRequests": report["actualFreshHTTPRequests"],
                "published": False, "goldenAccepted": 0}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="p30-l7b-evidence")
    ap.add_argument("--platform-limit", type=int, default=19)
    ap.add_argument("--detail-per-platform", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--min-interval", type=float, default=0.7)
    ap.add_argument("--max-seconds", type=int, default=450)
    args = ap.parse_args()
    if not 1 <= args.platform_limit <= 19 or not 0 <= args.detail_per_platform <= 2:
        ap.error("HOLD_INVALID_BOUNDED_SAMPLE")
    if not 4 <= args.timeout <= 20 or not 0.6 <= args.min_interval <= 5:
        ap.error("HOLD_RATE_LIMIT_OR_TIMEOUT")
    if not 30 <= args.max_seconds <= 600:
        ap.error("HOLD_TIME_BUDGET")
    safe_out(args.out)
    output, report = audit(PLATFORMS[:args.platform_limit], args.detail_per_platform,
                           args.timeout, args.min_interval, args.max_seconds)
    manifest = emit(output, report, args.out)
    for p in report["platforms"]:
        print("SOURCE", p["platform"], "HTTP", p["http"]["state"] if p["http"] else "HOLD",
              "LIST", p["listCandidateCount"], "DETAIL", p["detailIdentityVerified"],
              "LABELS", p["fieldEvidenceObserved"])
    print("RUN_ID", report["runId"], "FRESH_HTTP", report["actualFreshHTTPRequests"])
    print("COUNTS", json.dumps(report["counts"], ensure_ascii=False))
    print("QUALITY_GATE", json.dumps(report["qualityGate"], ensure_ascii=False))
    print("PASS L7B_ISOLATED_FILES_SEALED", len(manifest["filesSHA256"]))
    print("HOLD L7B_FORMAL_DATE_PRICE_TICKET_AND_GOLDEN_NOT_PROMOTED")


if __name__ == "__main__":
    main()
