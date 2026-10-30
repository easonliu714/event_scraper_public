#!/usr/bin/env python3
"""P30-L9-BJ: OPENTIX bounded role-to-value topology; fail closed, no publication."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup, Tag
from p30_l9bh_opentix_identity import HOME, HOLD, get_one, index_edges, norm
from p30_l9bi_opentix_local_role import section_roles

DATETIME = re.compile(r"20\d{2}/(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])\s+(?:[01]\d|2[0-3]):[0-5]\d")
OTHER_ROLES = ("開賣", "退票", "截止", "選擇場館", "報名", "優惠", "票價")

def inspect_value_topology(html, title):
    prior = section_roles(html, title)
    result = dict(prior, adjacentValueCandidateCount=0, adjacentControlCount=0,
                  acceptedFields=0, sessionId=None, ticketEventId=None,
                  sessionDateTime=None, sourceRole="SESSION_CHOOSER_LABEL")
    if prior["decision"] != "REVIEW_LOCAL_SESSION_LABEL_NO_VALUE":
        return result
    soup = BeautifulSoup(html, "html.parser")
    sections = [h for h in soup.find_all("h2", limit=80)
                if norm(h.get_text(" ", strip=True)) == "購票資訊"]
    if len(sections) != 1:
        result["decision"] = "HOLD_TICKET_SECTION_AMBIGUOUS"
        return result
    scope = []
    for sibling in sections[0].next_siblings:
        if isinstance(sibling, Tag) and sibling.name in ("h1", "h2"):
            break
        if len(scope) >= 24:
            result["decision"] = "HOLD_SECTION_SIBLING_CAP"
            return result
        scope.append(sibling)
    root = BeautifulSoup("".join(str(x) for x in scope), "html.parser")
    labels = [n for n in root.find_all(string=True)
              if norm(n).rstrip("：:") == "選擇場次"]
    if len(labels) != 1:
        result["decision"] = "HOLD_LOCAL_LABEL_AMBIGUOUS"
        return result
    label_parent = labels[0].parent
    if not isinstance(label_parent, Tag) or norm(label_parent.get_text(" ", strip=True)).rstrip("：:") != "選擇場次":
        result["decision"] = "HOLD_LABEL_CONTAINER_MIXED"
        return result
    adjacent = [n for n in label_parent.next_siblings
                if (isinstance(n, Tag) or norm(n))]
    if not adjacent:
        result["decision"] = "HOLD_JS_OR_UNBOUND_SESSION_VALUE"
        return result
    candidate = adjacent[0]
    if not isinstance(candidate, Tag):
        result["decision"] = "HOLD_UNSTRUCTURED_ADJACENCY"
        return result
    controls = candidate.find_all(["input", "select", "button", "option"], limit=30)
    if candidate.name in ("input", "select", "button") or controls or candidate.get("role") in ("combobox", "listbox"):
        result["adjacentControlCount"] = len(controls) + int(candidate.name in ("input", "select", "button"))
        result["decision"] = "HOLD_INTERACTIVE_OR_JS_ONLY_VALUE"
        return result
    value = norm(candidate.get_text(" ", strip=True))
    if len(value.encode("utf-8")) > 240 or any(role in value for role in OTHER_ROLES):
        result["decision"] = "HOLD_MIXED_ROLE_OR_VALUE_CAP"
        return result
    matches = DATETIME.findall(value)
    result["adjacentValueCandidateCount"] = len(matches)
    if len(matches) != 1 or value != matches[0]:
        result["decision"] = "HOLD_ZERO_MULTI_OR_NONLOCAL_VALUE"
        return result
    try:
        datetime.strptime(matches[0], "%Y/%m/%d %H:%M")
    except ValueError:
        result["decision"] = "HOLD_INVALID_CALENDAR_DATETIME"
        return result
    result["decision"] = "REVIEW_ADJACENT_DATETIME_NO_TZ_NO_SESSION_ID"
    return result

def live():
    audit = {"gate":"P30-L9-BJ","source":"OPENTIX_PLATFORM_05",
             "observed_at":datetime.now(timezone.utc).isoformat(),
             "requestBudget":2,"requestCount":1,"acceptedFields":0,
             "goldenAccepted":0,"published":False,"releaseState":HOLD}
    receipt, index = get_one(HOME)
    audit["indexReceipt"] = receipt
    if index is None:
        return dict(audit, decision="HOLD_INDEX_HTTP_OR_BODY")
    edges = index_edges(index)
    audit["uniqueSourceEventEdges"] = len(edges)
    if not edges:
        return dict(audit, decision="HOLD_NO_UNIQUE_EVENT_EDGE")
    url, title = edges[0]
    audit["selectedEventURLSHA256"] = hashlib.sha256(url.encode()).hexdigest()
    audit["requestCount"] = 2
    receipt, detail = get_one(url)
    audit["detailReceipt"] = receipt
    if detail is None:
        return dict(audit, decision="HOLD_DETAIL_HTTP_OR_BODY")
    audit.update(inspect_value_topology(detail, title))
    return audit

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
