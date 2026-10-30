#!/usr/bin/env python3
"""L9-BN: source-observed Huashan card-title versus H1 identity, REVIEW only.

Observed public index card contains date/title/venue while its linked detail H1
contains title alone. Never infer identity from whole-card text or URL alone.
"""
import hashlib
from bs4 import BeautifulSoup
from p30_l9bm_huashan_route_diagnostic import classify_href
from p30_l9bl_huashan_source import norm

HOLD = "HARD_HOLD_NO_PUBLICATION"

def audit_card_identity(index_html, detail_html, selected_href):
    kind, selected = classify_href(selected_href)
    out = {"gate": "P30-L9-BN", "source": "HUASHAN_PLATFORM_13",
           "routeKind": kind, "selectedURLSHA256": hashlib.sha256(
               (selected or "").encode()).hexdigest(),
           "matchedCards": 0, "titleNodes": 0, "exactH1Matches": 0,
           "wholeCardTextIsTitle": False, "acceptedFields": 0,
           "goldenAccepted": 0, "published": False, "releaseState": HOLD}
    if selected is None:
        return dict(out, decision="HOLD_UNSAFE_OR_NON_DETAIL_ROUTE")
    index = BeautifulSoup(index_html, "html.parser")
    cards = []
    for a in index.find_all("a", href=True, limit=1200):
        _, candidate = classify_href(a["href"])
        if candidate != selected:
            continue
        cards.append(a)
    out["matchedCards"] = len(cards)
    if len(cards) != 1:
        return dict(out, decision="HOLD_CARD_MISSING_OR_DUPLICATED")
    card = cards[0]
    titles = [norm(x.get_text(" ", strip=True)) for x in
              card.find_all(["h2", "h3", "h4"], limit=8)]
    titles = [x for x in titles if x]
    out["titleNodes"] = len(titles)
    if len(titles) != 1 or not 4 <= len(titles[0]) <= 180:
        return dict(out, decision="HOLD_CARD_TITLE_NOT_STRUCTURALLY_BOUND")
    title = titles[0]
    out["wholeCardTextIsTitle"] = norm(card.get_text(" ", strip=True)) == title
    detail = BeautifulSoup(detail_html, "html.parser")
    h1s = [norm(x.get_text(" ", strip=True)) for x in detail.find_all("h1", limit=12)]
    out["exactH1Matches"] = h1s.count(title)
    out["titleSHA256"] = hashlib.sha256(title.encode()).hexdigest()
    if len(h1s) != 1 or out["exactH1Matches"] != 1:
        return dict(out, decision="HOLD_H1_TITLE_MISMATCH_OR_AMBIGUITY")
    return dict(out, decision="REVIEW_SAME_ROUTE_CARD_TITLE_H1_NOT_FIELDS")
