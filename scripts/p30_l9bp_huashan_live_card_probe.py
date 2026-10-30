#!/usr/bin/env python3
"""P30-L9-BP: one normal Huashan index GET; record actual card DOM topology.

Diagnostic only. Never treat a card, HTTP200 or CI SUCCESS as an accepted
EVENT/SESSION/PRICE/ticket field. No raw HTML is written to evidence.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
from p30_l9bl_huashan_source import norm
from p30_l9bn_huashan_card_identity import classify_href

INDEX = "https://www.huashan1914.com/exhibition"
ROUTE = "/exhibition/%E6%9C%97%E8%AE%80%E6%B2%99%E9%BE%8D-%E9%80%99%E6%A8%A3%E5%95%8A%EF%BC%81%E9%82%A3%E4%BA%9B%E7%86%9F%E6%82%89%E5%8F%88%E9%99%8C%E7%94%9F%E7%9A%84%E6%97%A5%E5%B8%B8"
HOLD = "HARD_HOLD_NO_PUBLICATION"

def inspect_index(html, selected_href=ROUTE):
    out = {"gate":"P30-L9-BP","source":"HUASHAN_PLATFORM_13",
           "sourceRole":"OFFICIAL_PLATFORM_13","matchedCardAnchors":0,
           "headingNodesInsideAnchor":0,"dateTextInAnchor":False,
           "venueTextInAnchor":False,"acceptedFields":0,"goldenAccepted":0,
           "published":False,"ticketEventId":None,"releaseState":HOLD}
    kind, selected = classify_href(selected_href)
    if selected is None:
        return dict(out,decision="HOLD_UNSAFE_SELECTED_ROUTE")
    soup = BeautifulSoup(html, "html.parser")
    cards = [a for a in soup.find_all("a",href=True,limit=1800)
             if classify_href(a.get("href",""))[1] == selected]
    out["matchedCardAnchors"] = len(cards)
    if len(cards) != 1:
        return dict(out,decision="HOLD_CARD_MISSING_OR_DUPLICATE")
    card = cards[0]
    headings = [norm(h.get_text(" ",strip=True)) for h in card.find_all(["h2","h3","h4"],limit=10)]
    headings = [h for h in headings if h]
    out["headingNodesInsideAnchor"] = len(headings)
    out["headingTags"] = [h.name for h in card.find_all(["h2","h3","h4"],limit=10)]
    text = norm(card.get_text(" ",strip=True))
    out["cardTextSHA256"] = hashlib.sha256(text.encode()).hexdigest()
    out["dateTextInAnchor"] = bool(re.search(r"2026[./]10[./]31",text))
    out["venueTextInAnchor"] = "中3A館" in text and "2樓拱廳" in text
    if len(headings) != 1:
        return dict(out,decision="HOLD_CARD_HEADING_OUTSIDE_OR_AMBIGUOUS")
    out["headingSHA256"] = hashlib.sha256(headings[0].encode()).hexdigest()
    if not out["dateTextInAnchor"] or not out["venueTextInAnchor"]:
        return dict(out,decision="HOLD_DATE_OR_VENUE_NOT_CARD_LOCAL")
    return dict(out,decision="REVIEW_CARD_LOCAL_TOPOLOGY_NO_FIELD_ACCEPTANCE")

def live_one():
    out = {"gate":"P30-L9-BP","mode":"ONE_NORMAL_OFFICIAL_INDEX_GET",
           "source":"HUASHAN_PLATFORM_13","requestBudget":1,"requestCount":1,
           "observedAtUTC":datetime.now(timezone.utc).isoformat(),
           "officialGET":1,"sourceQualityFromLive":False,"acceptedFields":0,
           "goldenAccepted":0,"published":False,"releaseState":HOLD}
    try:
        import requests
        with requests.get(INDEX,headers={"User-Agent":"EventRadarSourceAudit/1.0 (+https://github.com/easonliu714/event_scraper_public)",
             "Accept":"text/html"},timeout=(5,12),allow_redirects=False,stream=True) as response:
            out["httpStatus"] = response.status_code
            if response.status_code != 200:
                return dict(out,decision="HOLD_HTTP_NOT_200")
            if "html" not in response.headers.get("Content-Type","").lower():
                return dict(out,decision="HOLD_NON_HTML_RESPONSE")
            chunks, size = [], 0
            for part in response.iter_content(chunk_size=16384):
                size += len(part)
                if size > 1500000:
                    return dict(out,decision="HOLD_BODY_SIZE_LIMIT")
                chunks.append(part)
            body = b"".join(chunks)
        out["bodyByteCount"] = len(body)
        out["bodySHA256"] = hashlib.sha256(body).hexdigest()
        out["sourceQualityFromLive"] = True
        return dict(out,**inspect_index(body.decode("utf-8",errors="replace")))
    except Exception as exc:
        out["errorType"] = type(exc).__name__
        return dict(out,decision="HOLD_SAFE_HTTP_OR_PARSE_FAILURE")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    if not a.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(live_one(),sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
