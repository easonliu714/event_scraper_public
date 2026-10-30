#!/usr/bin/env python3
"""P30-VENUE-02U: Fuzhong15 official screening index/detail identity; NO PUBLISH."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://www.fuzhong15.ntpc.gov.tw/xcmovie?XsmSId=0M361641875264878260"
HOST = "www.fuzhong15.ntpc.gov.tw"
HOLD = "HARD_HOLD_NO_PUBLICATION"
GENERIC = {"更多", "查看詳情", "MORE", "下一頁", "上一頁", "立即購票"}

def norm(s):
    return " ".join(str(s).split())

def safe_detail(href):
    if not href or href.strip().lower().startswith(("#", "//", "javascript:", "data:", "mailto:")):
        return None
    try:
        u = urljoin(HOME, href)
        p = urlsplit(u)
        q = parse_qs(p.query)
        if p.scheme != "https" or p.hostname != HOST or p.username or p.password or p.port not in (None, 443) or p.fragment:
            return None
        if p.path != "/xcmovie/cont" or len(q.get("sid", [])) != 1 or len(q.get("xsmsid", [])) != 1:
            return None
        if not q["sid"][0] or q["xsmsid"][0] != "0M361641875264878260":
            return None
        return u
    except ValueError:
        return None

def index_edges(html):
    soup = BeautifulSoup(html, "html.parser")
    candidates = {}
    for a in soup.find_all("a", href=True, limit=1000):
        u = safe_detail(a["href"])
        if not u:
            continue
        title = norm(a.get_text(" ", strip=True))
        if not 2 <= len(title) <= 160 or title.upper() in GENERIC:
            continue
        candidates.setdefault(u, set()).add(title)
    return [(u, next(iter(v))) for u, v in candidates.items() if len(v) == 1]

def inspect_detail(html, title):
    soup = BeautifulSoup(html, "html.parser")
    headings = [norm(h.get_text(" ", strip=True)) for h in soup.find_all(["h1", "h2", "h3", "h4"], limit=100)]
    exact = sum(h == title for h in headings)
    labels = [norm(s) for s in soup.find_all(string=re.compile("放映日期"), limit=20)]
    return {"headingCount": len(headings), "exactTitleMatches": exact,
            "screeningDateLabelCount": len(labels),
            "decision": "REVIEW_EXACT_SCREENING_TITLE_AND_DATE_ROLE_NO_FIELDS" if exact == 1 and len(labels) == 1 else "HOLD_TITLE_OR_DATE_ROLE_AMBIGUOUS",
            "acceptedFields": 0, "venueScreeningId": None, "ticketEventId": None}

def get_one(url):
    receipt = {"urlSHA256": hashlib.sha256(url.encode()).hexdigest(), "httpStatus": None, "bytes": 0, "bodySHA256": None}
    try:
        r = requests.get(url, timeout=15, allow_redirects=False, headers={"User-Agent": "EventRadarQualityAudit/1.0"})
        receipt.update(httpStatus=r.status_code, bytes=len(r.content), bodySHA256=hashlib.sha256(r.content).hexdigest())
        if r.status_code != 200 or len(r.content) > 2000000:
            return receipt, None
        return receipt, r.text
    except requests.RequestException as exc:
        receipt["failureType"] = type(exc).__name__
        return receipt, None

def live():
    out = {"gate": "P30-VENUE-02U", "source": "FUZHONG15_P0_NEW_TAIPEI",
           "observed_at": datetime.now(timezone.utc).isoformat(), "requestBudget": 2, "requestCount": 1,
           "acceptedFields": 0, "goldenAccepted": 0, "published": False, "releaseState": HOLD,
           "venueScreeningId": None, "ticketEventId": None}
    receipt, html = get_one(HOME)
    out["indexReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_INDEX_HTTP_OR_BODY")
    edges = index_edges(html)
    out["candidateScreeningTitleEdges"] = len(edges)
    if not edges:
        return dict(out, decision="HOLD_NO_SOURCE_DERIVED_SCREENING_DETAIL_EDGE")
    url, title = edges[-1]
    out["selectedDetailURLSHA256"] = hashlib.sha256(url.encode()).hexdigest()
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
