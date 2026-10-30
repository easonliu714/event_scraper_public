#!/usr/bin/env python3
"""P30-L9-BK: reuse canonical Songshan #14, bounded official list/detail identity; NO PUBLISH."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://www.songshanculturalpark.org/exhibition"
HOST = "www.songshanculturalpark.org"
HOLD = "HARD_HOLD_NO_PUBLICATION"
PATH = re.compile(r"^/exhibition/activity/[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
RANGE = re.compile(r"\s+20\d{2}-\d{2}-\d{2}\s*-\s*20\d{2}-\d{2}-\d{2}\s*$")
AGGREGATES = ("展演攻略", "活動攻略", "活動總覽")

def norm(value):
    return " ".join(str(value).split())

def safe_detail(raw):
    if not raw or raw.startswith("//"):
        return None
    url = urlsplit(urljoin(HOME, raw))
    if url.scheme != "https" or url.hostname != HOST or url.username or url.password or url.port or url.query or url.fragment or not PATH.fullmatch(url.path):
        return None
    return url.geturl()

def index_edges(html):
    soup = BeautifulSoup(html, "html.parser")
    edges = {}
    conflicts = 0
    for a in soup.find_all("a", href=True, limit=1200):
        url = safe_detail(a["href"])
        if not url:
            continue
        title = RANGE.sub("", norm(a.get_text(" ", strip=True)))
        if not 4 <= len(title) <= 180 or any(w in title for w in AGGREGATES):
            continue
        if url in edges and edges[url] != title:
            conflicts += 1
        edges.setdefault(url, title)
    return list(edges.items())[:60], conflicts

def inspect(index_html, detail_html):
    edges, conflicts = index_edges(index_html)
    result = {"sourceDerivedEdges":len(edges), "conflictingTitleEdges":conflicts,
              "exactTitleMatches":0, "detailDateRoleCount":0,
              "acceptedFields":0, "ticketEventId":None}
    if conflicts or not edges:
        return dict(result, decision="HOLD_LIST_TITLE_CONFLICT_OR_ZERO")
    url, title = edges[0]
    soup = BeautifulSoup(detail_html, "html.parser")
    heads = [norm(h.get_text(" ", strip=True)) for h in soup.find_all(["h1","h2","h3"], limit=80)]
    result["exactTitleMatches"] = heads.count(title)
    text = norm(soup.get_text(" ", strip=True))
    result["detailDateRoleCount"] = len(re.findall(r"活動日期\s*[：:]", text))
    if result["exactTitleMatches"] != 1:
        return dict(result, decision="HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    if result["detailDateRoleCount"] > 1:
        return dict(result, decision="HOLD_MULTIPLE_ACTIVITY_DATE_ROLES")
    return dict(result, decision="REVIEW_SAME_ACTIVITY_PATH_TITLE_NO_FIELDS")

def get_one(url):
    receipt = {"urlSHA256":hashlib.sha256(url.encode()).hexdigest(),"httpStatus":None,"bodyBytes":0}
    try:
        r = requests.get(url, timeout=15, allow_redirects=False, headers={"User-Agent":"EventRadar-SourceQuality/1.0"})
        receipt["httpStatus"] = r.status_code
        receipt["bodyBytes"] = len(r.content)
        if r.status_code != 200 or len(r.content) > 1500000 or "text/html" not in r.headers.get("Content-Type","").lower():
            return receipt, None
        return receipt, r.text
    except requests.RequestException as e:
        receipt["errorType"] = type(e).__name__
        return receipt, None

def live():
    audit = {"gate":"P30-L9-BK","source":"SONGSHAN_PLATFORM_14",
             "observed_at":datetime.now(timezone.utc).isoformat(),
             "requestBudget":2,"requestCount":1,"acceptedFields":0,
             "goldenAccepted":0,"published":False,"releaseState":HOLD}
    receipt, index = get_one(HOME)
    audit["indexReceipt"] = receipt
    if index is None:
        return dict(audit,decision="HOLD_INDEX_HTTP_OR_BODY")
    edges, conflicts = index_edges(index)
    audit["sourceDerivedEdges"] = len(edges)
    audit["conflictingTitleEdges"] = conflicts
    if conflicts or not edges:
        return dict(audit,decision="HOLD_LIST_TITLE_CONFLICT_OR_ZERO")
    url, title = edges[0]
    audit["selectedURLSHA256"] = hashlib.sha256(url.encode()).hexdigest()
    audit["requestCount"] = 2
    receipt, detail = get_one(url)
    audit["detailReceipt"] = receipt
    if detail is None:
        return dict(audit,decision="HOLD_DETAIL_HTTP_OR_BODY")
    audit.update(inspect(index,detail))
    return audit

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    args = p.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
