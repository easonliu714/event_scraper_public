#!/usr/bin/env python3
"""P30-VENUE-02T: Cloud Gate New Taipei official index/detail role audit; NO PUBLISH."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://www.cloudgate.org.tw/cgt"
HOST = "www.cloudgate.org.tw"
HOLD = "HARD_HOLD_NO_PUBLICATION"
GENERIC = {"更多", "了解更多", "MORE", "立即購票", "詳細內容", "查看詳情"}
PATH_HINT = re.compile(r"/(performance|performances|program|programs|event|events|show|shows|production|productions)(/|$)", re.I)

def norm(s):
    return " ".join(str(s).split())

def safe_link(href):
    if not href or href.strip().startswith(("#", "//", "javascript:", "data:", "mailto:")):
        return None
    try:
        url = urljoin(HOME, href)
        p = urlsplit(url)
        if p.scheme != "https" or p.hostname != HOST or p.username or p.password or p.port not in (None, 443):
            return None
        return url
    except ValueError:
        return None

def index_edges(html):
    soup = BeautifulSoup(html, "html.parser")
    roles = {}
    candidates = {}
    for a in soup.find_all("a", href=True, limit=500):
        url = safe_link(a.get("href"))
        if url is None:
            continue
        path = urlsplit(url).path
        if not PATH_HINT.search(path):
            continue
        label = norm(a.get_text(" ", strip=True))
        roles[path.split("/")[1] if len(path.split("/")) > 1 else "root"] = roles.get(path.split("/")[1] if len(path.split("/")) > 1 else "root", 0) + 1
        if not 6 <= len(label) <= 150 or label.upper() in GENERIC:
            continue
        candidates.setdefault(url, set()).add(label)
    edges = [(url, next(iter(labels))) for url, labels in sorted(candidates.items()) if len(labels) == 1]
    return {"pathRoleCounts": roles, "candidateDetailEdges": len(edges)}, edges

def inspect_detail(html, label):
    soup = BeautifulSoup(html, "html.parser")
    heads = [norm(h.get_text(" ", strip=True)) for h in soup.find_all(["h1", "h2"], limit=80)]
    matches = sum(h == label for h in heads)
    return {
        "detailTitleMatches": matches,
        "decision": "REVIEW_EXACT_VENUE_INDEX_DETAIL_TITLE_NO_EVENT_ID" if matches == 1 else "HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY",
        "acceptedFields": 0, "venueEventId": None, "ticketEventId": None,
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
        "gate": "P30-VENUE-02T", "source": "CLOUD_GATE_THEATER_P0_NEW_TAIPEI",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "requestBudget": 2, "requestCount": 1, "acceptedFields": 0,
        "goldenAccepted": 0, "published": False, "releaseState": HOLD,
        "venueEventId": None, "ticketEventId": None,
    }
    receipt, html = get_one(HOME)
    out["indexReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_INDEX_HTTP_OR_BODY")
    roles, edges = index_edges(html)
    out.update(roles)
    if not edges:
        return dict(out, decision="HOLD_NO_SOURCE_DERIVED_DETAIL_EDGE")
    url, label = edges[0]
    out["selectedDetailURLSHA256"] = hashlib.sha256(url.encode()).hexdigest()
    out["selectedIndexTitleSHA256"] = hashlib.sha256(label.encode()).hexdigest()
    out["requestCount"] = 2
    receipt, html = get_one(url)
    out["detailReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(inspect_detail(html, label))
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
