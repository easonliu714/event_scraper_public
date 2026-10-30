#!/usr/bin/env python3
"""P30-VENUE-02K: Zepp New Taipei source-local OPEN/START and external ticket role, review only."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from p30_venue02j_zepp_newtaipei import LIST, DETAIL, HOLD, CAP, norm, get_one, inspect as prior_inspect

TIME = re.compile(r"(?<!\d)([01]?\d|2[0-3]):[0-5]\d(?!\d)")

def local_markers(soup, label):
    hits = []
    pattern = re.compile(r"(?<![A-Z])(?:\[" + label + r"\]|" + label + r")(?![A-Z])", re.I)
    for tag in soup.find_all(["p", "li", "dd", "span"]):
        text = norm(tag.get_text(" ", strip=True))
        if len(text) > 180 or not pattern.search(text):
            continue
        if any(child.name in ("p", "li", "dd", "span") and
               pattern.search(norm(child.get_text(" ", strip=True)))
               for child in tag.find_all(True)):
            continue
        hits.append(text)
    return hits

def inspect(listing, detail, observed):
    old = prior_inspect(listing, detail, observed)
    out = dict(old, gate="P30-VENUE-02K", openLocalMarkers=0,
               startLocalMarkers=0, externalTicketLinksReview=0, roleProvenance={})
    if old["decision"] != "REVIEW_ZEPP_SAME_RID_LIST_DETAIL_NO_FIELDS":
        return dict(out, decision="HOLD_PRIOR_SAME_RID_IDENTITY", priorDecision=old["decision"])
    soup = BeautifulSoup(detail, "html.parser")
    starts = local_markers(soup, "START")
    opens = local_markers(soup, "OPEN")
    out["startLocalMarkers"] = len(starts)
    out["openLocalMarkers"] = len(opens)
    if len(starts) != 1 or len(TIME.findall(starts[0])) != 1:
        return dict(out, decision="HOLD_START_LOCAL_TIME_AMBIGUOUS")
    if len(opens) != 1 or len(TIME.findall(opens[0])) != 1:
        return dict(out, decision="HOLD_OPEN_LOCAL_TIME_AMBIGUOUS")
    if starts[0] == opens[0]:
        return dict(out, decision="HOLD_OPEN_START_SAME_UNSCOPED_NODE")
    links = []
    for a in soup.find_all("a", href=True):
        u = urljoin(DETAIL, a["href"])
        p = urlsplit(u)
        host = (p.hostname or "").lower()
        if p.scheme == "https" and (host == "kktix.com" or host.endswith(".kktix.com")):
            links.append(u)
    out["externalTicketLinksReview"] = len(links)
    if len(links) > 1:
        return dict(out, decision="HOLD_MULTIPLE_EXTERNAL_TICKET_LINKS")
    out["roleProvenance"] = {
        "OPEN": dict(source=DETAIL, observed_at=observed, role="VENUE_DOOR_OPEN_CANDIDATE",
                     decision="REVIEW_NOT_EVENT_START_OR_SALE"),
        "START": dict(source=DETAIL, observed_at=observed, role="VENUE_SHOW_START_CANDIDATE",
                      decision="REVIEW_NOT_TICKET_SALE"),
        "TICKET": dict(source=DETAIL, observed_at=observed, role="VENUE_CLAIMED_PLATFORM",
                       decision="REVIEW_EXTERNAL_LINK_NOT_VERIFIED_TICKET_EVENT_ID" if links else
                       "HOLD_PLATFORM_NAME_WITHOUT_VERIFIED_TICKET_URL")
    }
    return dict(out, decision="REVIEW_ZEPP_LOCAL_OPEN_START_TICKET_BOUNDARY_NO_FIELDS")

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(observedAtUTC=observed, requestBudget=2, requestCount=0,
               acceptedFields=0, goldenAccepted=0, published=False, releaseState=HOLD)
    r, listing = get_one(LIST)
    out["requestCount"] += 1
    out["listReceipt"] = r
    if listing is None:
        return dict(out, decision="HOLD_LIST_HTTP_OR_BODY")
    r, detail = get_one(DETAIL)
    out["requestCount"] += 1
    out["detailReceipt"] = r
    if detail is None:
        return dict(out, decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(inspect(listing, detail, observed))
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--live-one", action="store_true")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    if not a.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(live(), f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
