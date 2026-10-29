#!/usr/bin/env python3
"""P30-L9-AS: one bounded public FamiTicket HTML/DOM identity observation.

Read-only; no iframe navigation, login, checkout, hidden content acceptance,
event field promotion or raw HTML persistence. HTTP200 alone never passes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
import p30_l3b_a_famiticket as frozen

URL = "https://www.famiticket.com.tw/Home/Activity/Info/RQA3AHUAbwBwAEgANwBzAFIAQQA1AGEAbABEADgAcABqAGMAbwBaAC8ARgBGAEcAVwBWAEUAdQBXAFEAeQBUAFcAcgAyADUARgBFADUAbgBWADQAdwA9AA2"
TITLE = "CC同人創作展"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_HTML_BYTES = 220000

def norm(s):
    return " ".join(str(s).split())

def hidden(tag):
    """Refuse headings/markers in hidden or inert ancestors."""
    while getattr(tag, "attrs", None) is not None:
        attrs = tag.attrs
        style = re.sub(r"\s+", "", str(attrs.get("style", "")).lower())
        if (tag.name in ("script", "style", "template", "noscript")
                or attrs.get("hidden") is not None
                or str(attrs.get("aria-hidden", "")).lower() == "true"
                or "display:none" in style or "visibility:hidden" in style):
            return True
        tag = tag.parent
    return False

def inspect_html(html, detail_url, expected_title):
    base = dict(source="FAMITICKET_07", decision="HOLD_INPUT",
                identity="UNKNOWN", headingMatches=0, infoMarkers=0,
                iframeCount=0, acceptedFields=0, goldenAccepted=0,
                published=False, releaseState=RELEASE,
                ticketEventId=None, eventDateAccepted=False)
    if (not isinstance(html, str) or not html
            or len(html.encode("utf-8")) > MAX_HTML_BYTES
            or not isinstance(expected_title, str) or not 2 <= len(expected_title) <= 180
            or not isinstance(detail_url, str) or not frozen.allowed(detail_url, detail=True)
            or urlsplit(detail_url).query or urlsplit(detail_url).fragment):
        return base
    soup = BeautifulSoup(html, "html.parser")
    base["iframeCount"] = len(soup.find_all("iframe"))
    headings = [t for t in soup.find_all(["h1", "h2", "h3", "h4"])
                if norm(t.get_text(" ", strip=True)) == norm(expected_title)]
    visible = [t for t in headings if not hidden(t)]
    base["headingMatches"] = len(visible)
    if not visible:
        return dict(base, decision="HOLD_HIDDEN_TITLE" if headings else
                    ("HOLD_IFRAME_ONLY_NO_TITLE" if base["iframeCount"] else "HOLD_NO_EXACT_TITLE"))
    if len(visible) != 1:
        return dict(base, decision="HOLD_DUPLICATE_EXACT_TITLE")
    base["identity"] = "REVIEW_SAME_URL_EXACT_VISIBLE_HEADING"
    markers = []
    for t in soup.find_all(string=True):
        if norm(t) == "《活動資訊》" and t.parent is not None and not hidden(t.parent):
            markers.append(t.parent)
    for img in soup.find_all("img"):
        if norm(img.get("alt", "")) == "《活動資訊》" and not hidden(img):
            markers.append(img)
    base["infoMarkers"] = len(markers)
    if not markers:
        return dict(base, decision="HOLD_NO_VISIBLE_INFO_MARKER")
    if len(markers) != 1:
        return dict(base, decision="HOLD_AMBIGUOUS_INFO_MARKERS")
    return dict(base, decision="REVIEW_LIVE_HTML_TITLE_AND_INFO_MARKER_NO_FIELD_ACCEPTANCE")

def fetch_one():
    """Exactly one normal GET; fail closed on redirects, timeout and body cap."""
    audit = dict(source="FAMITICKET_07", observedAtUTC=datetime.now(timezone.utc).isoformat(),
                 requestCount=1, httpStatus=None, bodySHA256=None, bodyBytes=0,
                 contentType="UNKNOWN", sourceQualityThisCI="HOLD_NETWORK",
                 acceptedFields=0, goldenAccepted=0, published=False,
                 releaseState=RELEASE, decision="HOLD_NETWORK")
    try:
        import requests
        with requests.get(URL, headers={"User-Agent":"EventRadar-SourceQuality-ReadOnly/1.0"},
                          timeout=(6, 12), allow_redirects=False, stream=True) as response:
            audit["httpStatus"] = response.status_code
            audit["contentType"] = response.headers.get("Content-Type", "").split(";")[0].lower()
            if response.status_code != 200:
                audit["decision"] = "HOLD_HTTP_NOT_200"
                audit["sourceQualityThisCI"] = "HOLD_HTTP"
                return audit
            if audit["contentType"] not in ("text/html", "application/xhtml+xml"):
                audit["decision"] = "HOLD_CONTENT_TYPE"
                return audit
            parts = []
            total = 0
            for chunk in response.iter_content(chunk_size=32768):
                total += len(chunk)
                if total > MAX_HTML_BYTES:
                    audit["decision"] = "HOLD_HTML_BYTE_CAP"
                    audit["bodyBytes"] = total
                    return audit
                parts.append(chunk)
            raw = b"".join(parts)
            audit["bodyBytes"] = len(raw)
            audit["bodySHA256"] = hashlib.sha256(raw).hexdigest()
            result = inspect_html(raw.decode(response.encoding or "utf-8", errors="replace"), URL, TITLE)
            audit.update(result)
            audit["sourceQualityThisCI"] = ("REVIEW_ONE_LIVE_HTML_DOM"
                 if result["decision"].startswith("REVIEW_") else "HOLD_LIVE_HTML_DOM")
    except Exception as exc:
        audit["networkErrorClass"] = type(exc).__name__
        audit["decision"] = "HOLD_NETWORK"
    return audit

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live-one", action="store_true")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    if not a.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(fetch_one(), f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")

if __name__ == "__main__":
    main()
