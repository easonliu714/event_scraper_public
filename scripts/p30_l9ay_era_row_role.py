#!/usr/bin/env python3
"""P30-L9-AY: source-bound ERA session-table row ownership; NO PUBLISH."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from p30_l9av_era_source_role import DETAIL, TITLE, HOLD, norm, get_one

HEADS = ("h1", "h2", "h3", "h4", "h5", "h6")
DATE = re.compile(r"\b20\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b")

def review(detail, observed):
    out = dict(gate="P30-L9-AY", source="ERA_TICKET_PLATFORM_08",
               sourceURL=DETAIL, observed_at=observed, role="SESSION_TABLE_ROW_CANDIDATE",
               acceptedFields=0, goldenAccepted=0, published=False,
               ticketEventId=None, releaseState=HOLD,
               tableCount=0, rowCount=0, rowsWithDateHint=0)
    soup = BeautifulSoup(detail, "html.parser")
    h1 = [h for h in soup.find_all("h1") if norm(h.get_text(" ", strip=True)) == norm(TITLE)]
    if len(h1) != 1:
        return dict(out, decision="HOLD_DETAIL_H1_NOT_UNIQUE")
    headings = [h for h in soup.find_all(["h2", "h3", "h4", "h5"])
                if norm(h.get_text(" ", strip=True)) == "場次列表"]
    if len(headings) != 1:
        return dict(out, decision="HOLD_SESSION_HEADING_NOT_UNIQUE")
    heading = headings[0]
    parent = heading.parent
    tables = {}
    for depth in range(3):
        if parent is None or parent.name in ("body", "html", "[document]"):
            break
        children = parent.find_all(recursive=False)
        if len(children) > 80:
            return dict(out, decision="HOLD_SCOPE_CHILD_BOUND")
        index = next((i for i, c in enumerate(children)
                      if c is heading or heading in c.descendants), -1)
        if index < 0:
            break
        for child in children[index + 1:index + 9]:
            if child.name in HEADS or child.find(HEADS):
                break
            txt = norm(child.get_text(" ", strip=True))
            if "退票方式" in txt or len(txt) > 5000:
                break
            candidates = ([child] if child.name == "table" else []) + child.find_all("table", limit=3)
            for table in candidates:
                tables[id(table)] = table
        parent = parent.parent
    out["tableCount"] = len(tables)
    if len(tables) != 1:
        return dict(out, decision="HOLD_SESSION_TABLE_NOT_UNIQUE")
    table = next(iter(tables.values()))
    rows = table.find_all("tr", limit=41)
    out["rowCount"] = len(rows)
    if not rows or len(rows) > 40:
        return dict(out, decision="HOLD_TABLE_ROW_BOUND")
    date_rows = 0
    for row in rows:
        txt = norm(row.get_text(" ", strip=True))
        if len(txt) > 500 or "退票" in txt or "退款" in txt:
            return dict(out, decision="HOLD_REFUND_OR_OVERSIZE_ROW")
        tokens = DATE.findall(txt)
        if len(tokens) > 1:
            return dict(out, decision="HOLD_MULTIPLE_DATES_PER_ROW")
        date_rows += bool(tokens)
    out["rowsWithDateHint"] = date_rows
    if not date_rows:
        return dict(out, decision="HOLD_NO_ROW_LOCAL_DATE_HINT")
    out["provenance"] = dict(source=DETAIL, observed_at=observed,
                             role="SESSION_ROW_DATE_HINT_ONLY",
                             decision="REVIEW_NOT_ACCEPTED_NO_UNIQUE_SESSION_ID")
    return dict(out, decision="REVIEW_ONE_SESSION_TABLE_ROW_DATE_HINTS_NO_FIELDS")

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(gate="P30-L9-AY", observedAtUTC=observed,
               requestBudget=1, requestCount=1, acceptedFields=0,
               goldenAccepted=0, published=False, releaseState=HOLD)
    receipt, html = get_one(DETAIL)
    out["detailReceipt"] = receipt
    if html is None:
        return dict(out, decision="HOLD_OFFICIAL_DETAIL_UNAVAILABLE")
    out.update(review(html, observed))
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
