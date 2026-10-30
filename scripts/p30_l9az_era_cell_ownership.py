#!/usr/bin/env python3
"""P30-L9-AZ: bounded official ERA table cell/header/session-identity diagnostics; no publish."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from p30_l9ay_era_row_role import review as predecessor_review, DATE
from p30_l9av_era_source_role import DETAIL, HOLD, norm, get_one

TIME = re.compile(r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)")
DATE_ROLE = re.compile(r"^(?:演出日期|日期|活動日期|場次日期)$")
TIME_ROLE = re.compile(r"^(?:演出時間|時間|開演時間|場次時間)$")
REFUND = re.compile(r"退票|退款|退費|取消|截止")

def review(detail, observed):
    base = predecessor_review(detail, observed)
    out = dict(gate="P30-L9-AZ", source="ERA_TICKET_PLATFORM_08",
               sourceURL=DETAIL, observed_at=observed, role="SESSION_CELL_DIAGNOSTIC",
               acceptedFields=0, goldenAccepted=0, published=False,
               ticketEventId=None, releaseState=HOLD, predecessorDecision=base["decision"],
               rowShapes=[], headerDateRoleCount=0, headerTimeRoleCount=0,
               rowSessionAttributeHints=0, candidateRowsWithDateAndTime=0,
               sourceQuality="DETAIL_TABLE_CELL_TOPOLOGY")
    if not base["decision"].startswith("REVIEW_"):
        return dict(out, decision="HOLD_PREDECESSOR_TABLE_IDENTITY")
    soup = BeautifulSoup(detail, "html.parser")
    headings = [h for h in soup.find_all(["h2","h3","h4","h5"])
                if norm(h.get_text(" ", strip=True)) == "場次列表"]
    if len(headings) != 1:
        return dict(out, decision="HOLD_SESSION_HEADING_NOT_UNIQUE")
    heading = headings[0]
    parent = heading.parent
    tables = {}
    for _ in range(3):
        if parent is None or parent.name in ("body","html","[document]"):
            break
        children = parent.find_all(recursive=False)
        if len(children) > 80:
            return dict(out, decision="HOLD_SCOPE_CHILD_BOUND")
        pos = next((i for i,c in enumerate(children) if c is heading or heading in c.descendants), -1)
        if pos < 0:
            break
        for child in children[pos+1:pos+9]:
            if child.name in ("h1","h2","h3","h4","h5","h6") or child.find(["h1","h2","h3","h4","h5","h6"]):
                break
            txt = norm(child.get_text(" ", strip=True))
            if "退票方式" in txt or len(txt) > 5000:
                break
            for table in ([child] if child.name == "table" else []) + child.find_all("table",limit=3):
                tables[id(table)] = table
        parent = parent.parent
    if len(tables) != 1:
        return dict(out, decision="HOLD_SESSION_TABLE_NOT_UNIQUE")
    table = next(iter(tables.values()))
    rows = table.find_all("tr",limit=41)
    if not rows or len(rows)>40:
        return dict(out, decision="HOLD_ROW_BOUND")
    seen_date = 0
    for i,row in enumerate(rows):
        cells = row.find_all(["td","th"],recursive=False)
        if len(cells)>12:
            return dict(out, decision="HOLD_CELL_BOUND")
        labels = [norm(c.get_text(" ",strip=True)) for c in cells]
        if any(len(s)>500 or REFUND.search(s) for s in labels):
            return dict(out, decision="HOLD_REFUND_OR_OVERSIZE_CELL")
        date_count = sum(len(DATE.findall(s)) for s in labels)
        time_count = sum(len(TIME.findall(s)) for s in labels)
        if date_count>1:
            return dict(out, decision="HOLD_MULTIPLE_ROW_DATES")
        attrs = sum(bool(c.get("data-session-id")) for c in [row]+cells)
        if attrs>1:
            return dict(out, decision="HOLD_MULTIPLE_SESSION_ATTRIBUTES")
        date_roles = sum(bool(DATE_ROLE.fullmatch(s)) for s in labels)
        time_roles = sum(bool(TIME_ROLE.fullmatch(s)) for s in labels)
        out["headerDateRoleCount"] += date_roles
        out["headerTimeRoleCount"] += time_roles
        out["rowSessionAttributeHints"] += attrs
        out["candidateRowsWithDateAndTime"] += bool(date_count and time_count)
        seen_date += bool(date_count)
        out["rowShapes"].append(dict(index=i,cellCount=len(cells),
                                      headerCellCount=sum(c.name=="th" for c in cells),
                                      dateTokenCount=date_count,timeTokenCount=time_count,
                                      dateLabelCount=date_roles,timeLabelCount=time_roles,
                                      sessionAttributeHints=attrs,anchorCount=len(row.find_all("a",limit=20))))
    if not seen_date:
        return dict(out,decision="HOLD_NO_ROW_LOCAL_DATE")
    if out["rowSessionAttributeHints"]>1:
        return dict(out,decision="HOLD_NONUNIQUE_SESSION_ATTRIBUTES")
    out["provenance"] = dict(source=DETAIL, observed_at=observed,
                             role="ROW_CELL_SHAPE_ONLY",
                             decision="REVIEW_NOT_ACCEPTED_NO_VERIFIED_SESSION_ID")
    return dict(out,decision="REVIEW_ROW_CELL_TOPOLOGY_NO_ACCEPTED_FIELDS")

def live():
    observed=datetime.now(timezone.utc).isoformat()
    out=dict(gate="P30-L9-AZ",observedAtUTC=observed,requestBudget=1,requestCount=1,
             acceptedFields=0,goldenAccepted=0,published=False,releaseState=HOLD)
    receipt,html=get_one(DETAIL)
    out["detailReceipt"]=receipt
    if html is None:
        return dict(out,decision="HOLD_OFFICIAL_DETAIL_UNAVAILABLE")
    out.update(review(html,observed))
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--live-one",action="store_true")
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
