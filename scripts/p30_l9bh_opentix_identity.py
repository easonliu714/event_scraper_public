#!/usr/bin/env python3
"""P30-L9-BH: OPENTIX #05 source-derived event title and section-role proof; NO PUBLISH."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

HOME = "https://www.opentix.life/"
HOST = "www.opentix.life"
HOLD = "HARD_HOLD_NO_PUBLICATION"
CATEGORIES = {"戲劇", "音樂", "舞蹈", "電影", "親子", "其他", "活動/學習", "展覽", "講座", "傳統戲曲"}
GENERIC = {"看全部", "更多", "連結", "立即購票", "詳細資訊"}

def norm(value):
    return " ".join(str(value).split())

def safe_event(href):
    if not href or href.strip().lower().startswith(("#", "//", "javascript:", "data:", "mailto:")):
        return None
    try:
        url = urljoin(HOME, href)
        parts = urlsplit(url)
        if (parts.scheme != "https" or parts.hostname != HOST or parts.username or
                parts.password or parts.port not in (None, 443) or parts.query or parts.fragment):
            return None
        segments = parts.path.strip("/").split("/")
        if len(segments) != 2 or segments[0] != "event" or not segments[1].isdigit():
            return None
        return url
    except ValueError:
        return None

def label_title(label):
    text = norm(label)
    for category in sorted(CATEGORIES, key=len, reverse=True):
        if text.startswith(category + " "):
            text = text[len(category) + 1:]
            break
    if not 4 <= len(text) <= 180 or text.upper() in GENERIC:
        return None
    return text

def index_edges(html):
    soup = BeautifulSoup(html, "html.parser")
    candidates = {}
    for anchor in soup.find_all("a", href=True, limit=1200):
        url = safe_event(anchor["href"])
        title = label_title(anchor.get_text(" ", strip=True)) if url else None
        if url and title:
            candidates.setdefault(url, set()).add(title)
    return [(url, next(iter(titles))) for url, titles in sorted(candidates.items()) if len(titles) == 1]

def inspect_detail(html, title):
    soup = BeautifulSoup(html, "html.parser")
    h1 = [norm(h.get_text(" ", strip=True)) for h in soup.find_all("h1", limit=50)]
    exact = sum(h == title for h in h1)
    h2 = [norm(h.get_text(" ", strip=True)) for h in soup.find_all("h2", limit=80)]
    visible = [norm(t) for t in soup.find_all(string=True, limit=6000) if norm(t)]
    ticket_sections = h2.count("購票資訊")
    session_labels = visible.count("選擇場次")
    venue_labels = visible.count("選擇場館")
    refund_labels = visible.count("退票期限：") + visible.count("退票期限")
    if exact != 1:
        decision = "HOLD_EVENT_TITLE_MISMATCH_OR_AMBIGUITY"
    elif ticket_sections != 1:
        decision = "HOLD_TICKET_SECTION_MISSING_OR_DUPLICATED"
    else:
        decision = "REVIEW_EXACT_EVENT_TITLE_TICKET_SECTION_NO_FIELDS"
    return {"h1Count": len(h1), "exactTitleMatches": exact,
            "ticketInfoSectionCount": ticket_sections, "sessionChooserLabelCount": session_labels,
            "venueChooserLabelCount": venue_labels, "refundLabelCount": refund_labels,
            "decision": decision, "acceptedFields": 0, "eventId": None, "sessionId": None}

def get_one(url):
    receipt = {"urlSHA256": hashlib.sha256(url.encode()).hexdigest(),
               "httpStatus": None, "bytes": 0, "bodySHA256": None}
    try:
        response = requests.get(url, timeout=15, allow_redirects=False,
                                headers={"User-Agent": "EventRadarQualityAudit/1.0"})
        receipt.update(httpStatus=response.status_code, bytes=len(response.content),
                       bodySHA256=hashlib.sha256(response.content).hexdigest())
        if response.status_code != 200 or not response.content or len(response.content) > 2000000:
            return receipt, None
        return receipt, response.text
    except requests.RequestException as exc:
        receipt["failureType"] = type(exc).__name__
        return receipt, None

def live():
    audit = {"gate": "P30-L9-BH", "source": "OPENTIX_PLATFORM_05",
             "observed_at": datetime.now(timezone.utc).isoformat(), "requestBudget": 2,
             "requestCount": 1, "acceptedFields": 0, "goldenAccepted": 0,
             "published": False, "releaseState": HOLD, "eventId": None, "sessionId": None}
    receipt, html = get_one(HOME)
    audit["indexReceipt"] = receipt
    if html is None:
        return dict(audit, decision="HOLD_INDEX_HTTP_OR_BODY")
    edges = index_edges(html)
    audit["sourceDerivedUniqueEventEdges"] = len(edges)
    if not edges:
        return dict(audit, decision="HOLD_NO_SOURCE_DERIVED_EVENT_EDGE")
    url, title = edges[0]
    audit["selectedEventURLSHA256"] = hashlib.sha256(url.encode()).hexdigest()
    audit["selectedIndexTitleSHA256"] = hashlib.sha256(title.encode()).hexdigest()
    audit["requestCount"] = 2
    receipt, detail = get_one(url)
    audit["detailReceipt"] = receipt
    if detail is None:
        return dict(audit, decision="HOLD_DETAIL_HTTP_OR_BODY")
    audit.update(inspect_detail(detail, title))
    return audit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-one", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(live(), handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
