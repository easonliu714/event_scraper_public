#!/usr/bin/env python3
"""P30-L3-A TWTC: read-only exhibition table extraction and one detail sample.

No external organizer follow, no login, retries, writer, notification or publishing.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

LISTING = "https://twtc.com.tw/exhibition?p=home"
HOSTS = frozenset(("twtc.com.tw", "www.twtc.com.tw"))
MAX_BYTES = 1_500_000
MAX_RECORDS = 100
UA = "EventRadar-P30-readonly/1.0 (github.com/easonliu714/event_scraper_public)"
KIND = "EVENTRADAR_P30_L3A_TWTC_EXHIBITION_CANDIDATE_ONLY"
PERIOD_RE = re.compile(r"^\d{1,2}/\d{1,2}\s*[~～-]\s*\d{1,2}/\d{1,2}$")
DATE_RANGE = re.compile(
    r"展出日期\s*[:：]\s*(20\d{2}/\d{1,2}/\d{1,2})\s*[~～-]\s*(20\d{2}/\d{1,2}/\d{1,2})")


def allowed(url):
    try:
        u = urlsplit(url)
        return (u.scheme == "https" and u.hostname in HOSTS
                and u.username is None and u.password is None
                and u.port in (None, 443)
                and "\\" not in u.path and ".." not in u.path.split("/")
                and (u.path == "/exhibition" or u.path == "/exhibition_more.aspx"))
    except ValueError:
        return False


def get_html(session, url, timeout=12):
    start, trail = url, []
    for _ in range(3):
        if not allowed(url):
            return None, {"state": "URL_REJECTED", "trail": trail}
        try:
            with session.get(url, timeout=(6, timeout), allow_redirects=False,
                             stream=True, headers={"User-Agent": UA}) as resp:
                code = resp.status_code
                trail.append({"url": url, "http_status": code})
                if code in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("location")
                    if not loc:
                        return None, {"state": "REDIRECT_NO_LOCATION", "trail": trail}
                    url = urljoin(url, loc)
                    continue
                ct = resp.headers.get("content-type", "")[:100]
                meta = {"state": "HTTP_OK" if code == 200 else "HTTP_ERROR",
                        "url": url, "request_url": start, "http_status": code,
                        "content_type": ct, "trail": trail}
                if code != 200:
                    return None, meta
                if "text/html" not in ct.lower():
                    meta["state"] = "NON_HTML"
                    return None, meta
                body = bytearray()
                for chunk in resp.iter_content(chunk_size=32_768):
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        meta["state"] = "OVERSIZE"
                        return None, meta
                if not body:
                    meta["state"] = "EMPTY"
                    return None, meta
                meta["sha256"] = hashlib.sha256(body).hexdigest()
                meta["bytes"] = len(body)
                return bytes(body), meta
        except requests.RequestException as e:
            return None, {"state": "NETWORK_ERROR", "error_type": type(e).__name__,
                          "trail": trail, "request_url": start}
    return None, {"state": "REDIRECT_LIMIT", "trail": trail}


def detail_link(cell, base):
    for anchor in cell.find_all("a", href=True):
        absolute = urljoin(base, anchor.get("href", ""))
        if not allowed(absolute):
            continue
        u = urlsplit(absolute)
        if u.path != "/exhibition_more.aspx":
            continue
        ident = parse_qs(u.query).get("id", [])
        if len(ident) == 1 and re.fullmatch(r"\d{2,12}", ident[0]):
            return "https://twtc.com.tw/exhibition_more.aspx?id=" + ident[0] + "&p=home"
    return None


def parse_list(content, source=LISTING):
    soup = BeautifulSoup(content, "html.parser")
    records, seen = [], set()
    table_rows = 0
    for tr in soup.find_all("tr"):
        cols = tr.find_all("td", recursive=False)
        if len(cols) < 3:
            continue
        table_rows += 1
        period = " ".join(cols[0].stripped_strings)
        if not (PERIOD_RE.fullmatch(period) or period == "延期未定"):
            continue
        title = re.sub(r"\s+", " ", " ".join(
            s for s in cols[1].stripped_strings if s.strip().casefold() not in ("more", "詳情")))
        organizer = re.sub(r"\s+", " ", " ".join(cols[2].stripped_strings))[:200]
        venue = re.sub(r"\s+", " ", " ".join(cols[4].stripped_strings))[:100] if len(cols) >= 5 else None
        if len(title) < 4:
            continue
        url = detail_link(cols[1], source)
        key_data = (title.strip().casefold(), period, organizer.casefold())
        identity = url if url else "|".join(key_data)
        if identity in seen:
            continue
        seen.add(identity)
        records.append({
            "platform": "台北世貿", "title": title[:180],
            "official_url": url or source, "detail_url": url,
            "official_url_role": "TWTC_DETAIL" if url else "TWTC_LISTING_FALLBACK",
            "source_list_url": source, "event_period_raw": period,
            "source_time_role": "EXHIBITION_PERIOD_RAW_UNNORMALIZED",
            "event_date_start": None, "event_date_end": None,
            "date": None, "location": venue, "organizer": organizer,
            "price": None, "description": None, "ticket_availability": "UNKNOWN",
            "source_level": "LIST_TABLE_ONLY", "golden_verified": False,
            "provenance_id": hashlib.sha256("|".join(key_data).encode("utf-8")).hexdigest(),
            "status": "DATE_PENDING" if period != "延期未定" else "POSTPONED_UNCERTAIN",
        })
        if len(records) >= MAX_RECORDS:
            break
    return records, {"table_rows_seen": table_rows, "list_candidates": len(records)}


def parse_detail_date(data, expected_title):
    """Only bind a full-year exhibition date if the expected event name appears."""
    body = " ".join(BeautifulSoup(data, "html.parser").stripped_strings)
    if expected_title not in body:
        return {"state": "UNBOUND_DETAIL_TITLE"}
    matches = DATE_RANGE.findall(body)
    if len(matches) != 1:
        return {"state": "DATE_ABSENT_OR_AMBIGUOUS", "match_count": len(matches)}
    start, end = matches[0]
    try:
        sd, ed = date.fromisoformat(start.replace("/", "-")), date.fromisoformat(end.replace("/", "-"))
    except ValueError:
        return {"state": "INVALID_DATE"}
    if sd > ed:
        return {"state": "INVERTED_DATE"}
    return {"state": "DETAIL_DATE_CANDIDATE", "start": sd.isoformat(),
            "end": ed.isoformat(), "source_time_role": "OFFICIAL_EXHIBITION_DATE"}


def run(session, timeout=12, delay=1.0):
    if delay < 0.6:
        raise ValueError("HOLD_RATE_LIMIT")
    page, meta = get_html(session, LISTING, timeout)
    rows, parsed = parse_list(page, meta.get("url", LISTING)) if page else ([], None)
    sample = {"state": "NOT_ATTEMPTED"}
    target = next((r for r in rows if r["detail_url"]), None)
    if target:
        time.sleep(delay)
        html, detail_http = get_html(session, target["detail_url"], timeout)
        sample = {"target": target["detail_url"], "http": detail_http}
        if html is not None:
            fields = parse_detail_date(html, target["title"])
            sample.update(fields)
            if fields["state"] == "DETAIL_DATE_CANDIDATE":
                target["event_date_start"] = fields["start"]
                target["event_date_end"] = fields["end"]
                target["source_time_role"] = fields["source_time_role"]
                target["source_level"] = "DETAIL_DATE_CANDIDATE"
        else:
            sample["state"] = "DETAIL_HTTP_HOLD"
    return rows, {
        "kind": KIND, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "listing": {"source": LISTING, "http": meta, "parse": parsed},
        "sample_detail": sample, "unique_candidates": len(rows),
        "max_list_get": 1, "max_detail_get": 1, "retry_count": 0,
        "golden_accepted": False, "app_data_published": False, "auto_hidden": 0,
        "source_runtime": "DORMANT", "writer_executed": False, "notification_executed": False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    root = Path(args.out).resolve()
    if root == Path("docs").resolve() or Path("docs").resolve() in root.parents:
        ap.error("HOLD_PAGES_OUTPUT_FORBIDDEN")
    with requests.Session() as session:
        rows, report = run(session)
    root.mkdir(parents=True, exist_ok=True)
    (root / "candidate.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "diagnostics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("START P30_L3A_TWTC_OFFICIAL")
    print("LIST_HTTP", report["listing"]["http"].get("http_status"),
          "CANDIDATES", report["unique_candidates"])
    print("DETAIL_STATE", report["sample_detail"]["state"])
    print("PASS P30_L3A_LIST_ONLY_NOT_GOLDEN" if rows else "HOLD P30_L3A_LIST_EMPTY")
    print("PASS P30_L3A_REPORT_ONLY_NO_PUBLISH")
    print("GOLDEN_ACCEPTED=0 AUTO_HIDDEN=0 APP_DATA_PUBLISHED=false SOURCE_RUNTIME=DORMANT")


if __name__ == "__main__":
    main()
