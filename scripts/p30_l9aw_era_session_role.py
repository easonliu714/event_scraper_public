#!/usr/bin/env python3
"""P30-L9-AW: ERA #08 section-local session rows versus refund cutoff; review only."""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from p30_l9av_era_source_role import HOME, DETAIL, HOLD, CAP, norm, get_one, inspect as prior_inspect

# Unicode Chinese label immediately before a digit is a word character; use digit guards, not \b.\nDATE = re.compile(r"(?<!\d)20\d{2}[/.-]\d{1,2}[/.-]\d{1,2}(?!\d)")
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

def after_heading(heading, target, max_siblings=4):
    """Read only bounded immediate following siblings; never search global dates."""
    for index, sibling in enumerate(heading.next_siblings):
        if index >= max_siblings:
            break
        if not getattr(sibling, "name", None):
            continue
        if sibling.name in HEADINGS or sibling.find(HEADINGS):
            break
        candidates = ([sibling] if sibling.name == target else sibling.find_all(target))
        if candidates:
            return candidates[0]
    return None

def inspect(home, detail, observed):
    old = prior_inspect(home, detail, observed)
    out = dict(old, gate="P30-L9-AW", sourceQuality="REVIEW_ONLY",
               sessionRowsReview=0, sessionDateTokensReview=0,
               refundDateTokensReview=0, roleProvenance={})
    if old["decision"] != "REVIEW_SAME_PRODUCT_LIST_DETAIL_ROLE_BOUNDARY_NO_FIELDS":
        return dict(out, decision="HOLD_PRIOR_EXACT_PRODUCT_IDENTITY", priorDecision=old["decision"])
    soup = BeautifulSoup(detail, "html.parser")
    session = [h for h in soup.find_all(["h2","h3","h4","h5"])
               if norm(h.get_text(" ", strip=True)) == "場次列表"]
    refund = [h for h in soup.find_all(["h2","h3","h4","h5"])
              if norm(h.get_text(" ", strip=True)) == "退票方式"]
    if len(session) != 1:
        return dict(out, decision="HOLD_SESSION_HEADING_NOT_UNIQUE")
    table = after_heading(session[0], "table")
    if table is None:
        return dict(out, decision="HOLD_NO_SESSION_LOCAL_TABLE")
    rows = table.find_all("tr")
    if not 1 <= len(rows) <= 48:
        return dict(out, decision="HOLD_SESSION_ROW_BOUNDS")
    table_text = norm(table.get_text(" ", strip=True))
    if len(table_text) > 5000 or "退票" in table_text or "退款" in table_text:
        return dict(out, decision="HOLD_SESSION_TABLE_MIXED_REFUND")
    session_dates = DATE.findall(table_text)
    out["sessionRowsReview"] = len(rows)
    out["sessionDateTokensReview"] = len(session_dates)
    if not session_dates:
        return dict(out, decision="HOLD_NO_LOCAL_SESSION_DATE_TOKEN")
    if len(refund) != 1:
        return dict(out, decision="HOLD_REFUND_HEADING_NOT_UNIQUE")
    refund_node = after_heading(refund[0], "p")
    if refund_node is None:
        return dict(out, decision="HOLD_NO_LOCAL_REFUND_NODE")
    refund_text = norm(refund_node.get_text(" ", strip=True))
    if len(refund_text) > 800:
        return dict(out, decision="HOLD_REFUND_SCOPE_CAP")
    out["refundDateTokensReview"] = len(DATE.findall(refund_text))
    out["roleProvenance"] = {
        "SESSION": dict(source=DETAIL, observed_at=observed, role="SESSION_TABLE_DATE_CANDIDATE",
                        decision="REVIEW_LOCAL_TABLE_NOT_ACCEPTED_SESSION"),
        "REFUND": dict(source=DETAIL, observed_at=observed, role="REFUND_DEADLINE",
                       decision="REFUSE_AS_EVENT_OR_SALE_DATE"),
        "PRODUCT_ID": dict(source=DETAIL, observed_at=observed, role="SOURCE_LOCAL_PRODUCT_ID",
                           decision="REVIEW_NOT_GLOBAL_TICKET_EVENT_ID")
    }
    return dict(out, decision="REVIEW_SESSION_TABLE_REFUND_SEPARATED_NO_FIELD_PROMOTION")

def live():
    observed = datetime.now(timezone.utc).isoformat()
    out = dict(observedAtUTC=observed, requestBudget=2, requestCount=0,
               acceptedFields=0, goldenAccepted=0, published=False, releaseState=HOLD)
    r, home = get_one(HOME)
    out["requestCount"] += 1
    out["listReceipt"] = r
    if home is None:
        return dict(out, decision="HOLD_LIST_HTTP_OR_BODY")
    r, detail = get_one(DETAIL)
    out["requestCount"] += 1
    out["detailReceipt"] = r
    if detail is None:
        return dict(out, decision="HOLD_DETAIL_HTTP_OR_BODY")
    out.update(inspect(home, detail, observed))
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
