#!/usr/bin/env python3
"""P30-VENUE-02O: one bounded official Xinzhuang submenu GET; candidate index role only."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from p30_venue02m_xinzhuang_discovery import HOLD, norm, same_origin, get_one

CANDIDATE_URL = "https://www.xzcac.ntpc.gov.tw/submenu?usein=2&psid=0G286667437547603307"
DETAIL_PATH = re.compile(r"/(?:xmdoc|news|activity|activities|event|program|content|detail)(?:/|$)", re.I)
DATE = re.compile(r"\b20\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b")
EVENT_WORD = re.compile(r"展演|活動|演出|節目|表演")
EXCLUDE = re.compile(r"首頁|隱私|交通|租借|聯絡|網站導覽|最新消息")

def inspect(html, observed):
    out = dict(gate="P30-VENUE-02O", source="XINZHUANG_ARTS_CENTER_VENUE",
               sourceURL=CANDIDATE_URL, observed_at=observed,
               role="CANDIDATE_SUBMENU_PAGE_ROLE", acceptedFields=0, goldenAccepted=0,
               published=False, ticketEventId=None, releaseState=HOLD,
               sourceQuality="OFFICIAL_SUBMENU_STRUCTURE_ONLY",
               pageHeadingCount=0, sameOriginLinks=0, detailPathHints=0,
               eventLabelHints=0, dateTokenHints=0, candidateExamples=[])
    soup = BeautifulSoup(html, "html.parser")
    headings = [norm(h.get_text(" ", strip=True))
                for h in soup.find_all(["h1", "h2", "h3"], limit=60)]
    if any(len(x) > 240 for x in headings):
        return dict(out, decision="HOLD_OVERSIZE_HEADING")
    out["pageHeadingCount"] = len([x for x in headings if x])
    out["pageHeadingEventLabels"] = sum(bool(EVENT_WORD.search(x)) for x in headings)
    seen = set()
    hints = {}
    for a in soup.find_all("a", href=True, limit=600):
        url = same_origin(a["href"], CANDIDATE_URL)
        if url is None:
            continue
        seen.add(url)
        label = norm(a.get_text(" ", strip=True))
        if len(label) > 240:
            return dict(out, decision="HOLD_OVERSIZE_LINK_LABEL")
        p = urlsplit(url)
        path_hint = bool(DETAIL_PATH.search(p.path))
        label_hint = bool(EVENT_WORD.search(label)) and not EXCLUDE.search(label)
        out["detailPathHints"] += bool(path_hint)
        out["eventLabelHints"] += bool(label_hint)
        if path_hint and label_hint and url != CANDIDATE_URL:
            hints[url] = dict(path=p.path, labelLength=len(label),
                              queryKeyNames=sorted({k.split("=")[0] for k in p.query.split("&") if k})[:15])
    out["sameOriginLinks"] = len(seen)
    out["dateTokenHints"] = len(DATE.findall(norm(soup.get_text(" ", strip=True))[:10000]))
    out["candidateExamples"] = list(hints.values())[:3]
    out["candidateDetailLinkHints"] = len(hints)
    if not out["pageHeadingCount"] and not hints:
        return dict(out, decision="HOLD_SUBMENU_NO_VISIBLE_EVENT_STRUCTURE")
    if len(hints) > 40:
        return dict(out, decision="HOLD_SUBMENU_DETAIL_LINK_BOUND")
    if not hints:
        return dict(out, decision="HOLD_SUBMENU_NO_UNIQUE_EVENT_DETAIL_LINK")
    return dict(out, decision="REVIEW_SUBMENU_DETAIL_LINK_HINTS_NO_LIST_PASS")

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(gate="P30-VENUE-02O", observedAtUTC=observed,
               requestBudget=1, requestCount=1, acceptedFields=0,
               goldenAccepted=0, published=False, releaseState=HOLD)
    receipt, html = get_one(CANDIDATE_URL)
    out["submenuReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_SUBMENU_HTTP_OR_BODY")
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
