#!/usr/bin/env python3
"""P30-L9-AX: one bounded ERA detail GET to diagnose real session-heading DOM ancestry; NO PUBLISH."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from p30_l9av_era_source_role import DETAIL, TITLE, HOLD, norm, get_one

HEADS = ("h1", "h2", "h3", "h4", "h5", "h6")

def topology(detail, observed):
    out = dict(gate="P30-L9-AX", source="ERA_TICKET_PLATFORM_08",
               detailURL=DETAIL, observedAtUTC=observed, sourceQuality="DIAGNOSTIC_ONLY",
               acceptedFields=0, goldenAccepted=0, published=False, ticketEventId=None,
               releaseState=HOLD, scopes=[], sessionHeadingCount=0)
    soup = BeautifulSoup(detail, "html.parser")
    titles = [h for h in soup.find_all("h1") if norm(h.get_text(" ", strip=True)) == norm(TITLE)]
    if len(titles) != 1:
        return dict(out, decision="HOLD_DETAIL_H1_NOT_UNIQUE")
    headings = [h for h in soup.find_all(["h2", "h3", "h4", "h5"])
                if norm(h.get_text(" ", strip=True)) == "場次列表"]
    out["sessionHeadingCount"] = len(headings)
    if len(headings) != 1:
        return dict(out, decision="HOLD_SESSION_HEADING_NOT_UNIQUE")
    h = headings[0]
    parent = h.parent
    for depth in range(3):
        if parent is None or parent.name in ("body", "html", "[document]"):
            break
        children = parent.find_all(recursive=False)
        if len(children) > 80:
            out["scopes"].append(dict(depth=depth, parentTag=parent.name, decision="HOLD_CHILD_BOUND"))
            break
        index = next((i for i, c in enumerate(children) if c is h or h in c.descendants), -1)
        if index < 0:
            break
        after = children[index + 1:index + 9]
        stopped = False
        tables = 0
        dateTokens = 0
        tagNames = []
        for child in after:
            if child.name in HEADS or child.find(HEADS):
                stopped = True
                break
            txt = norm(child.get_text(" ", strip=True))
            if len(txt) > 5000 or "退票方式" in txt:
                stopped = True
                break
            tables += int(child.name == "table") + len(child.find_all("table", limit=3))
            dateTokens += txt.count("2026/") + txt.count("2026-")
            tagNames.append(child.name)
        out["scopes"].append(dict(depth=depth, parentTag=parent.name,
                                   immediateFollowingTags=tagNames[:8],
                                   boundedTables=tables, dateTokenHints=dateTokens,
                                   stoppedAtHeadingOrRefund=stopped))
        parent = parent.parent
    # A topology hint is never enough to bind a SESSION value to this event.
    if any(s.get("boundedTables", 0) for s in out["scopes"]):
        return dict(out, decision="REVIEW_TABLE_SCOPE_DIAGNOSTIC_NO_FIELDS")
    return dict(out, decision="HOLD_NO_BOUNDED_SESSION_TABLE_TOPOLOGY")

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(gate="P30-L9-AX", observedAtUTC=observed, requestBudget=1,
               requestCount=1, acceptedFields=0, goldenAccepted=0,
               published=False, releaseState=HOLD)
    receipt, detail = get_one(DETAIL)
    out["detailReceipt"] = receipt
    if detail is None:
        return dict(out, decision="HOLD_OFFICIAL_DETAIL_UNAVAILABLE")
    out.update(topology(detail, observed))
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
