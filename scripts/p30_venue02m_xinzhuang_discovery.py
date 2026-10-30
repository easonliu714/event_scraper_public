#!/usr/bin/env python3
"""P30-VENUE-02M: Xinzhuang Arts Center first-party event-index discovery; NO PUBLISH."""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://www.xzcac.ntpc.gov.tw/"
HOST = "www.xzcac.ntpc.gov.tw"
HOLD = "HARD_HOLD_NO_PUBLICATION"
CAP = 512000
POSITIVE = re.compile(r"活動資訊|活動一覽|藝文活動|展演活動|演出資訊|節目表|活動行事曆")
NEGATIVE = re.compile(r"場地租借|交通資訊|聯絡我們|會員|登入|最新消息|隱私")

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

def same_origin(href, base=HOME):
    url = urljoin(base, href)
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname != HOST or p.username or p.password
            or p.port not in (None, 443) or not p.path or p.path == "/"):
        return None
    return url

def inspect_home(html, observed):
    out = dict(gate="P30-VENUE-02M", source="XINZHUANG_ARTS_CENTER_VENUE",
               observed_at=observed, sourceURL=HOME, acceptedFields=0,
               goldenAccepted=0, published=False, ticketEventId=None,
               releaseState=HOLD, sameOriginLinks=0, candidateIndexLinks=0,
               candidateIndexURL=None, sourceQuality="DISCOVERY_ONLY")
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    candidate = set()
    for a in soup.find_all("a", href=True, limit=600):
        url = same_origin(a["href"])
        if url is None:
            continue
        seen.add(url)
        label = norm(a.get_text(" ", strip=True))
        if POSITIVE.search(label) and not NEGATIVE.search(label):
            candidate.add(url)
    out["sameOriginLinks"] = len(seen)
    out["candidateIndexLinks"] = len(candidate)
    if len(candidate) != 1:
        return dict(out, decision="HOLD_INDEX_DISCOVERY_ZERO_OR_AMBIGUOUS")
    out["candidateIndexURL"] = next(iter(candidate))
    return dict(out, decision="REVIEW_ONE_FIRST_PARTY_INDEX_LINK_NOT_LIST_PASS")

def inspect_index(html, observed):
    soup = BeautifulSoup(html, "html.parser")
    anchors = [a for a in soup.find_all("a", href=True, limit=600)
               if same_origin(a["href"]) and norm(a.get_text(" ", strip=True))]
    headings = [h for h in soup.find_all(["h1", "h2"], limit=100)
                if norm(h.get_text(" ", strip=True))]
    return dict(indexVisibleLinks=len(anchors), indexHeadings=len(headings),
                indexDecision="REVIEW_INDEX_STRUCTURE_ONLY_NO_EVENT_ID",
                indexProvenance=dict(source="OFFICIAL_SAME_ORIGIN_INDEX",
                                     observed_at=observed, role="INDEX_DISCOVERY",
                                     decision="REVIEW_NOT_INDIVIDUAL_EVENT"))

def get_one(url):
    try:
        with requests.get(url, timeout=12, allow_redirects=False,
                          headers={"User-Agent": "EventRadar-SourceQuality/1.0 (read-only)"},
                          stream=True) as r:
            if r.status_code != 200:
                return dict(status=r.status_code, bytes=0, sha256=None), None
            body = bytearray()
            for chunk in r.iter_content(16384):
                body.extend(chunk)
                if len(body) > CAP:
                    return dict(status=200, bytes=len(body), capExceeded=True), None
            raw = bytes(body)
            return dict(status=200, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()), raw.decode(r.encoding or "utf-8", errors="replace")
    except requests.RequestException as e:
        return dict(status="NETWORK_HOLD", errorType=type(e).__name__), None

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(gate="P30-VENUE-02M", observedAtUTC=observed,
               requestBudget=2, requestCount=1, acceptedFields=0,
               goldenAccepted=0, published=False, releaseState=HOLD)
    receipt, html = get_one(HOME)
    out["homeReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_HOME_HTTP_OR_BODY")
    out.update(inspect_home(html, observed))
    if out["decision"] != "REVIEW_ONE_FIRST_PARTY_INDEX_LINK_NOT_LIST_PASS":
        return out
    index_url = out["candidateIndexURL"]
    out["requestCount"] += 1
    receipt, index = get_one(index_url)
    out["indexReceipt"] = receipt
    if index is None:
        return dict(out, decision="HOLD_INDEX_HTTP_OR_BODY")
    out.update(inspect_index(index, observed))
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--live-one", action="store_true")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(live(), f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
