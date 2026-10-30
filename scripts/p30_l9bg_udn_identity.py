#!/usr/bin/env python3
"""P30-L9-BG: bounded UDN #06 official same-product title identity, NO PUBLISH."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://tickets.udnfunlife.com/application/UTK01/UTK0101_03.aspx?Category=231&kdid=cateList"
HOST = "tickets.udnfunlife.com"
HOLD = "HARD_HOLD_NO_PUBLICATION"
GENERIC = {"立即購票", "立即訂票", "詳細資訊", "更多", "MORE", "訂購", "查看詳情"}

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
        if not p.path.startswith("/application/") or "UTK0201_" not in p.path:
            return None
        if len(q.get("PRODUCT_ID", [])) != 1 or not q["PRODUCT_ID"][0].strip():
            return None
        return u
    except ValueError:
        return None

def index_edges(html):
    soup = BeautifulSoup(html, "html.parser")
    candidates = {}
    for a in soup.find_all("a", href=True, limit=600):
        url = safe_detail(a["href"])
        if not url:
            continue
        title = norm(a.get_text(" ", strip=True).split("NT$")[0])
        if not 5 <= len(title) <= 160 or title.upper() in GENERIC:
            continue
        candidates.setdefault(url, set()).add(title)
    edges = [(u, next(iter(v))) for u, v in sorted(candidates.items()) if len(v) == 1]
    return edges

def inspect_detail(html, title):
    soup = BeautifulSoup(html, "html.parser")
    headings = [norm(h.get_text(" ", strip=True)) for h in soup.find_all(["h1", "h2", "h3"], limit=100)]
    exact = sum(x == title for x in headings)
    return {"headingCount": len(headings), "exactTitleMatches": exact,
            "decision": "REVIEW_SAME_PRODUCT_EXACT_TITLE_NO_FIELDS" if exact == 1 else "HOLD_TITLE_MISMATCH_OR_AMBIGUITY",
            "acceptedFields": 0, "eventId": None, "sessionId": None}

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
    out = {"gate": "P30-L9-BG", "source": "UDN_PLATFORM_06",
           "observed_at": datetime.now(timezone.utc).isoformat(), "requestBudget": 2, "requestCount": 1,
           "acceptedFields": 0, "goldenAccepted": 0, "published": False, "releaseState": HOLD,
           "eventId": None, "sessionId": None}
    receipt, html = get_one(HOME)
    out["indexReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_INDEX_HTTP_OR_BODY")
    edges = index_edges(html)
    out["candidateExactLinkTitleEdges"] = len(edges)
    if not edges:
        return dict(out, decision="HOLD_NO_UNAMBIGUOUS_SOURCE_DETAIL_EDGE")
    url, title = edges[0]
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
