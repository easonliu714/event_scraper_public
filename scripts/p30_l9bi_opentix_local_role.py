#!/usr/bin/env python3
"""P30-L9-BI: bound OPENTIX ticket section label ownership, never infer field values."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from p30_l9bh_opentix_identity import HOME, HOLD, norm, get_one, index_edges, inspect_detail

ROLES = ("選擇場館", "選擇場次", "退票期限", "購票資訊")

def section_roles(html, title):
    soup = BeautifulSoup(html, "html.parser")
    headings = [norm(x.get_text(" ", strip=True)) for x in soup.find_all("h1", limit=50)]
    sections = [h for h in soup.find_all("h2", limit=80) if norm(h.get_text(" ", strip=True)) == "購票資訊"]
    result = {"exactTitleMatches": headings.count(title), "ticketSectionCount": len(sections),
              "boundedSiblingNodes": 0, "boundedSectionBytes": 0,
              "localVenueLabelCount": 0, "localSessionLabelCount": 0,
              "localRefundLabelCount": 0, "acceptedFields": 0, "sessionId": None,
              "ticketEventId": None}
    if result["exactTitleMatches"] != 1 or len(sections) != 1:
        result["decision"] = "HOLD_TITLE_OR_SECTION_IDENTITY"
        return result
    siblings = []
    for sibling in sections[0].next_siblings:
        if getattr(sibling, "name", None) in ("h1", "h2"):
            break
        if len(siblings) >= 24:
            result["decision"] = "HOLD_SECTION_SIBLING_CAP"
            return result
        siblings.append(sibling)
    text = norm(" ".join(x.get_text(" ", strip=True) if hasattr(x, "get_text") else str(x) for x in siblings))
    result["boundedSiblingNodes"] = len(siblings)
    result["boundedSectionBytes"] = len(text.encode("utf-8"))
    if len(text.encode("utf-8")) > 2400:
        result["decision"] = "HOLD_SECTION_TEXT_CAP"
        return result
    for key, field in (("選擇場館", "localVenueLabelCount"), ("選擇場次", "localSessionLabelCount"), ("退票期限", "localRefundLabelCount")):
        result[field] = sum(norm(v).rstrip("：:") == key for v in BeautifulSoup("".join(str(x) for x in siblings), "html.parser").find_all(string=True))
    if result["localSessionLabelCount"] > 1 or result["localVenueLabelCount"] > 1 or result["localRefundLabelCount"] > 1:
        result["decision"] = "HOLD_DUPLICATE_ROLE_LABELS"
    elif result["localSessionLabelCount"] == 0:
        result["decision"] = "HOLD_NO_SOURCE_LOCAL_SESSION_ROLE"
    else:
        result["decision"] = "REVIEW_LOCAL_SESSION_LABEL_NO_VALUE"
    return result

def live():
    audit = {"gate": "P30-L9-BI", "source": "OPENTIX_PLATFORM_05",
             "observed_at": datetime.now(timezone.utc).isoformat(),
             "requestBudget": 2, "requestCount": 1, "acceptedFields": 0,
             "goldenAccepted": 0, "published": False, "releaseState": HOLD}
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
    audit.update(section_roles(detail, title))
    return audit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-one", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.live_one:
        raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(live(), f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
