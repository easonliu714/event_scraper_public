#!/usr/bin/env python3
"""P30-L9-BA: one official ERA detail, bounded row-anchor role/identity evidence; NO PUBLISH."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, parse_qsl
from bs4 import BeautifulSoup
from p30_l9az_era_cell_ownership import review as prior_review, DATE, TIME
from p30_l9av_era_source_role import DETAIL, HOLD, norm, get_one

PRODUCT_ID = "P1GFK34F"
SESSION_KEY = re.compile(r"session|performance|showtime|show_id|session_id", re.I)
OTHER_PRODUCT = re.compile(r"P[0-9][A-Z0-9]{5,}", re.I)

def inspect(detail, observed):
    prior = prior_review(detail, observed)
    out = dict(gate="P30-L9-BA", source="ERA_TICKET_PLATFORM_08",
               sourceURL=DETAIL, observed_at=observed, role="ROW_ANCHOR_IDENTITY_DIAGNOSTIC",
               predecessorDecision=prior["decision"], acceptedFields=0, goldenAccepted=0,
               published=False, ticketEventId=None, sessionId=None, releaseState=HOLD,
               candidateRowCount=0, rowAnchorCount=0, anchorRole="UNKNOWN",
               sourceQuality="ONE_ROW_ANCHOR_ROLE_ONLY")
    if not prior["decision"].startswith("REVIEW_"):
        return dict(out, decision="HOLD_PREDECESSOR_CELL_SCOPE")
    soup = BeautifulSoup(detail, "html.parser")
    headings = [h for h in soup.find_all(["h2", "h3", "h4", "h5"])
                if norm(h.get_text(" ", strip=True)) == "場次列表"]
    if len(headings) != 1:
        return dict(out, decision="HOLD_SESSION_HEADING_NOT_UNIQUE")
    heading = headings[0]
    parent = heading.parent
    tables = {}
    for _ in range(3):
        if parent is None or parent.name in ("body", "html", "[document]"):
            break
        children = parent.find_all(recursive=False)
        if len(children) > 80:
            return dict(out, decision="HOLD_SCOPE_CHILD_BOUND")
        pos = next((i for i, c in enumerate(children) if c is heading or heading in c.descendants), -1)
        if pos < 0:
            break
        for child in children[pos + 1:pos + 9]:
            if child.name in ("h1", "h2", "h3", "h4", "h5", "h6") or child.find(["h1", "h2", "h3", "h4", "h5", "h6"]):
                break
            txt = norm(child.get_text(" ", strip=True))
            if "退票方式" in txt or len(txt) > 5000:
                break
            for table in ([child] if child.name == "table" else []) + child.find_all("table", limit=3):
                tables[id(table)] = table
        parent = parent.parent
    if len(tables) != 1:
        return dict(out, decision="HOLD_TABLE_NOT_UNIQUE")
    rows = tables[next(iter(tables))].find_all("tr", limit=41)
    candidates = [row for row in rows
                  if DATE.search(norm(row.get_text(" ", strip=True)))
                  and TIME.search(norm(row.get_text(" ", strip=True)))]
    out["candidateRowCount"] = len(candidates)
    if len(candidates) != 1:
        return dict(out, decision="HOLD_ROW_DATE_TIME_NOT_UNIQUE")
    row = candidates[0]
    anchors = row.find_all("a", href=True, limit=3)
    out["rowAnchorCount"] = len(anchors)
    if len(anchors) != 1:
        return dict(out, decision="HOLD_ROW_ANCHOR_NOT_UNIQUE")
    href = anchors[0]["href"].strip()
    if not href or href.startswith(("#", "javascript:", "data:", "mailto:")):
        return dict(out, decision="HOLD_NON_NAVIGABLE_ANCHOR")
    url = urljoin(DETAIL, href)
    p = urlsplit(url)
    if p.scheme != "https" or p.username or p.password or p.port not in (None, 443):
        return dict(out, decision="HOLD_UNSAFE_ANCHOR_URL")
    if p.hostname != urlsplit(DETAIL).hostname:
        return dict(out, anchorHost=p.hostname, anchorRole="EXTERNAL",
                    decision="HOLD_EXTERNAL_ANCHOR_NOT_TICKET_SESSION")
    ids = set(OTHER_PRODUCT.findall(url))
    if ids and ids != {PRODUCT_ID}:
        return dict(out, anchorRole="PRODUCT_MISMATCH", decision="HOLD_ROW_ANCHOR_PRODUCT_MISMATCH")
    keys = sorted({key.lower() for key, _ in parse_qsl(p.query, keep_blank_values=True)})[:20]
    out.update(anchorHost=p.hostname, anchorPath=p.path, queryKeyNames=keys,
               sameProductToken=PRODUCT_ID in url,
               sessionParameterKeyHints=sum(bool(SESSION_KEY.search(k)) for k in keys))
    if PRODUCT_ID not in url:
        return dict(out, anchorRole="UNVERIFIED_PRODUCT",
                    decision="HOLD_ROW_ANCHOR_NO_SAME_PRODUCT_ID")
    out["anchorRole"] = "SAME_PRODUCT_LINK_ONLY"
    out["provenance"] = dict(source=DETAIL, observed_at=observed,
                              role="ROW_LOCAL_LINK_IDENTITY_HINT",
                              decision="REVIEW_NO_VERIFIED_SESSION_ID")
    return dict(out, decision="REVIEW_SAME_PRODUCT_ANCHOR_NO_SESSION_ID_NO_FIELDS")

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(gate="P30-L9-BA", observedAtUTC=observed, requestBudget=1,
               requestCount=1, acceptedFields=0, goldenAccepted=0,
               published=False, releaseState=HOLD)
    receipt, html = get_one(DETAIL)
    out["detailReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_OFFICIAL_DETAIL_UNAVAILABLE")
    out.update(inspect(html, observed))
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
