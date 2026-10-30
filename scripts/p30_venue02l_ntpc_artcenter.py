#!/usr/bin/env python3
"""P30-VENUE-02L: New Taipei Arts Center official monthly announcement identity; NO PUBLISH."""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

LIST = "https://www.culture.ntpc.gov.tw/artcenter_chi/sitesearch"
SID = "0Q152372523738311866"
DETAIL = "https://www.culture.ntpc.gov.tw/artcenter_chi/xmdoc/cont?sid=" + SID + "&sq=&xsmsid=0G269629106251547168"
TITLE = "〖演出預告〗115年11月演出節目"
HOLD = "HARD_HOLD_NO_PUBLICATION"
CAP = 512000

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

def sid_of(url):
    p = urlsplit(url)
    if p.scheme != "https" or p.hostname != "www.culture.ntpc.gov.tw" or p.path != "/artcenter_chi/xmdoc/cont":
        return None
    sid = parse_qs(p.query).get("sid", [])
    return sid[0] if len(sid) == 1 and re.fullmatch(r"[0-9A-Z]{20}", sid[0]) else None

def inspect(listing, detail, observed):
    out = dict(gate="P30-VENUE-02L", venueSource="NTPC_ARTCENTER_VENUE",
               sourceRole="VENUE_MONTHLY_ANNOUNCEMENT", sourceLocalSid=SID,
               ticketEventId=None, acceptedFields=0, goldenAccepted=0,
               published=False, releaseState=HOLD, listSidLinks=0,
               detailHeadingMatches=0, roleProvenance={})
    ls, ds = BeautifulSoup(listing, "html.parser"), BeautifulSoup(detail, "html.parser")
    anchors = [a for a in ls.find_all("a", href=True)
               if sid_of(urljoin(LIST, a["href"])) == SID and norm(a.get_text(" ", strip=True)) == TITLE]
    out["listSidLinks"] = len(anchors)
    if len(anchors) != 1:
        return dict(out, decision="HOLD_LIST_SID_TITLE_NOT_UNIQUE")
    heads = [h for h in ds.find_all(["h1", "h2", "h3", "h4"])
             if norm(h.get_text(" ", strip=True)) == TITLE]
    out["detailHeadingMatches"] = len(heads)
    if len(heads) != 1:
        return dict(out, decision="HOLD_DETAIL_HEADING_NOT_UNIQUE")
    out["roleProvenance"] = {
        "ANNOUNCEMENT": dict(source=DETAIL, observed_at=observed,
                             role="VENUE_MONTHLY_PROGRAM_BULLETIN",
                             decision="REVIEW_SID_AND_TITLE_NOT_INDIVIDUAL_EVENT"),
        "SESSION": dict(source=DETAIL, observed_at=observed,
                        role="UNSCOPED_MULTIPLE_PERFORMANCES",
                        decision="HOLD_NO_INDIVIDUAL_SESSION_IDENTITY"),
        "TICKET": dict(source=DETAIL, observed_at=observed,
                       role="VENUE_CLAIMED_TICKET_PLATFORMS",
                       decision="HOLD_NO_INDEPENDENT_TICKET_EVENT_ID")
    }
    return dict(out, decision="REVIEW_SAME_SID_MONTHLY_ANNOUNCEMENT_NO_FIELDS")

def get_one(url):
    try:
        r = requests.get(url, timeout=12, allow_redirects=False,
                         headers={"User-Agent": "EventRadar-SourceQuality/1.0 (read-only)"}, stream=True)
        if r.status_code != 200:
            return dict(status=r.status_code, bytes=0, sha256=None), None
        body = bytearray()
        for chunk in r.iter_content(16384):
            body.extend(chunk)
            if len(body) > CAP:
                return dict(status=200, bytes=len(body), capExceeded=True, sha256=None), None
        raw = bytes(body)
        return dict(status=200, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()), raw.decode(r.encoding or "utf-8", errors="replace")
    except requests.RequestException as e:
        return dict(status="NETWORK_HOLD", errorType=type(e).__name__), None

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(gate="P30-VENUE-02L", observedAtUTC=observed, requestBudget=2,
               requestCount=0, acceptedFields=0, goldenAccepted=0,
               published=False, releaseState=HOLD)
    receipt, listing = get_one(LIST)
    out["requestCount"] += 1
    out["listReceipt"] = receipt
    if listing is None:
        return dict(out, decision="HOLD_LIST_HTTP_OR_BODY")
    receipt, detail = get_one(DETAIL)
    out["requestCount"] += 1
    out["detailReceipt"] = receipt
    if detail is None:
        return dict(out, decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(inspect(listing, detail, observed))
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
