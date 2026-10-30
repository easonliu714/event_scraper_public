#!/usr/bin/env python3
"""P30-L9-BO: distinguish two official Huashan cards sharing date and venue.

Source-observed index 2026-10-31: two separate reading-salon detail URLs
have distinct H1 and activity times, despite identical card date and venue.
This is a diagnostic only; neither source DOM nor ticket ID is Golden.
"""
import hashlib
from bs4 import BeautifulSoup
from p30_l9bl_huashan_source import norm
from p30_l9bn_huashan_card_identity import audit_card_identity, classify_href

HOLD = "HARD_HOLD_NO_PUBLICATION"

def audit_distinct_edges(index_html, details_by_href, hrefs):
    out = {"gate": "P30-L9-BO", "source": "HUASHAN_PLATFORM_13",
           "sourceRole": "OFFICIAL_PLATFORM_13", "cardEdges": 0,
           "sharedDateVenue": False, "distinctDetailPaths": 0,
           "distinctDetailH1": 0, "acceptedFields": 0,
           "goldenAccepted": 0, "published": False, "ticketEventId": None,
           "releaseState": HOLD}
    if len(hrefs) != 2 or len(details_by_href) != 2:
        return dict(out, decision="HOLD_EXACT_TWO_SOURCE_EDGES_REQUIRED")
    resolved = [classify_href(h)[1] for h in hrefs]
    if None in resolved or len(set(resolved)) != 2:
        return dict(out, decision="HOLD_UNSAFE_OR_COLLAPSED_SOURCE_ROUTES")
    soup = BeautifulSoup(index_html, "html.parser")
    titles, dates, venues = [], [], []
    for raw, url in zip(hrefs, resolved):
        if raw not in details_by_href:
            return dict(out, decision="HOLD_DETAIL_NOT_BOUND_TO_SOURCE_ROUTE")
        predecessor = audit_card_identity(index_html, details_by_href[raw], raw)
        if predecessor["decision"] != "REVIEW_SAME_ROUTE_CARD_TITLE_H1_NOT_FIELDS":
            return dict(out, decision="HOLD_PREDECESSOR_IDENTITY_" + predecessor["decision"])
        cards = [a for a in soup.find_all("a", href=True, limit=1200)
                 if classify_href(a["href"])[1] == url]
        if len(cards) != 1:
            return dict(out, decision="HOLD_CARD_ROUTE_AMBIGUITY")
        card = cards[0]
        t = [norm(x.get_text(" ", strip=True)) for x in card.find_all("time", limit=3)]
        v = [norm(x.get_text(" ", strip=True)) for x in card.find_all("span", limit=3)]
        h = [norm(x.get_text(" ", strip=True)) for x in card.find_all("h3", limit=3)]
        if len(t) != 1 or len(v) != 1 or len(h) != 1 or not all(t+v+h):
            return dict(out, decision="HOLD_CARD_DATE_VENUE_TITLE_UNBOUND")
        dates.append(t[0]); venues.append(v[0]); titles.append(h[0])
        out["cardEdges"] += 1
    out["distinctDetailPaths"] = len(set(resolved))
    out["distinctDetailH1"] = len(set(titles))
    out["sharedDateVenue"] = len(set(dates)) == len(set(venues)) == 1
    out["routeSHA256"] = sorted(hashlib.sha256(x.encode()).hexdigest() for x in resolved)
    if out["distinctDetailH1"] != 2:
        return dict(out, decision="HOLD_DIFFERENT_ROUTE_SAME_H1")
    return dict(out, decision="REVIEW_DISTINCT_SOURCE_ROUTE_H1_NO_SESSION_OR_TICKET_ID")
