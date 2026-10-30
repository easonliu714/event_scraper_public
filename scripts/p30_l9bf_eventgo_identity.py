#!/usr/bin/env python3
"""P30-L9-BF: Event Go #10 bounded official list/detail title-edge diagnostic; NO PUBLISH."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://eventgo.bnextmedia.com.tw/"
HOST = "eventgo.bnextmedia.com.tw"
HOLD = "HARD_HOLD_NO_PUBLICATION"
GENERIC = {"詳細內容", "活動詳情", "立即報名", "立即購票", "更多", "MORE", "查看詳情"}

def normalize(value):
    return " ".join(str(value).split())

def safe_detail(href):
    if not href or href.strip().startswith(("#", "javascript:", "data:", "mailto:", "//")):
        return None
    try:
        url = urljoin(HOME, href)
        p = urlsplit(url)
        if p.scheme != "https" or p.hostname != HOST or p.username or p.password or p.port not in (None, 443):
            return None
        if not p.path.startswith("/event/detail"):
            return None
        return url
    except ValueError:
        return None

def list_candidates(html):
    soup = BeautifulSoup(html, "html.parser")
    edges = {}
    for a in soup.find_all("a", href=True, limit=500):
        url = safe_detail(a.get("href"))
        if not url:
            continue
        label = normalize(a.get_text(" ", strip=True))
        if not 6 <= len(label) <= 160 or label.upper() in GENERIC:
            continue
        edges.setdefault(url, set()).add(label)
    return [(url, next(iter(labels))) for url, labels in sorted(edges.items()) if len(labels) == 1]

def inspect_detail(html, expected_title):
    soup = BeautifulSoup(html, "html.parser")
    headings = [normalize(h.get_text(" ", strip=True)) for h in soup.find_all(["h1", "h2"], limit=80)]
    matches = sum(h == expected_title for h in headings)
    return {
        "detailTitleMatches": matches,
        "headingCount": len(headings),
        "decision": "REVIEW_SAME_URL_EXACT_TITLE_NO_FIELDS" if matches == 1 else "HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY",
        "acceptedFields": 0,
        "eventId": None,
        "sessionId": None,
    }

def get_one(url):
    receipt = {"urlSHA256": hashlib.sha256(url.encode()).hexdigest(), "httpStatus": None, "bytes": 0, "bodySHA256": None}
    try:
        r = requests.get(url, timeout=15, allow_redirects=False, headers={"User-Agent": "EventRadarQualityAudit/1.0"})
        receipt["httpStatus"] = r.status_code
        receipt["bytes"] = len(r.content)
        receipt["bodySHA256"] = hashlib.sha256(r.content).hexdigest()
        if r.status_code != 200 or len(r.content) > 2_000_000:
            return receipt, None
        return receipt, r.text
    except requests.RequestException as exc:
        receipt["failureType"] = type(exc).__name__
        return receipt, None

def live():
    out = {
        "gate": "P30-L9-BF", "source": "EVENTGO_PLATFORM_10",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "requestBudget": 2, "requestCount": 1,
        "acceptedFields": 0, "goldenAccepted": 0, "published": False,
        "releaseState": HOLD, "eventId": None, "sessionId": None,
    }
    receipt, html = get_one(HOME)
    out["indexReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_INDEX_HTTP_OR_BODY")
    candidates = list_candidates(html)
    out["candidateExactLinkTitleEdges"] = len(candidates)
    if not candidates:
        return dict(out, decision="HOLD_NO_UNAMBIGUOUS_EVENT_DETAIL_EDGE")
    url, title = candidates[0]
    out["selectedURLSHA256"] = hashlib.sha256(url.encode()).hexdigest()
    out["selectedIndexTitleSHA256"] = hashlib.sha256(title.encode()).hexdigest()
    out["requestCount"] = 2
    receipt, detail = get_one(url)
    out["detailReceipt"] = receipt
    if detail is None:
        return dict(out, decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(inspect_detail(detail, title))
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-one", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(live(), f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
