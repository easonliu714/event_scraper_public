#!/usr/bin/env python3
"""P30-VENUE-02E: TPAC same-program session cancellation safety Gate.

Public TPAC program index -> one official /program/<id> detail was observed.
Official detail separates performances and explicitly marks canceled sessions.
This module never promotes those sessions, dates, prices, or ticket links.
"""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

SOURCE = "TPAC_OFFICIAL"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
MAX_HTML = 800_000
MAX_ROWS = 30
SESSION = re.compile(r"^20\d{2}-\d{2}-\d{2}\s*[（(][一二三四五六日天][）)]\s*\d{2}:\d{2}(?:\s*已取消(?:[，,].*)?)?$")

def hidden(node):
    """Reject display-hidden ancestors rather than trusting visible child text."""
    for parent in [node, *node.parents]:
        if getattr(parent, "attrs", None):
            style = re.sub(r"\s+", "", parent.get("style", "")).lower()
            if parent.has_attr("hidden") or parent.get("aria-hidden") == "true":
                return True
            if "display:none" in style or "visibility:hidden" in style:
                return True
    return False

def inspect_detail(html: bytes, official_url: str, list_title: str) -> dict:
    """Fail closed unless exact official URL/title and bounded local session UL."""
    result = dict(source=SOURCE, decision="HOLD_INPUT", listDetailIdentity="UNKNOWN",
                  sessionCount=0, canceledCount=0, activeCount=0,
                  acceptedFields=0, goldenAccepted=0, published=False,
                  ticketEventId=None, releaseState=RELEASE)
    if (not isinstance(html, bytes) or not html or len(html) > MAX_HTML
            or not isinstance(list_title, str) or not 2 <= len(list_title) <= 180
            or not isinstance(official_url, str)):
        return result
    try:
        url = urlsplit(official_url)
        if (url.scheme != "https" or url.hostname != "tpac.org.taipei"
                or url.username is not None or url.password is not None
                or url.port not in (None, 443) or url.query or url.fragment
                or not re.fullmatch(r"/program/[0-9]{1,12}", url.path)):
            return dict(result, decision="HOLD_SOURCE_URL")
        soup = BeautifulSoup(html.decode("utf-8-sig"), "html.parser")
    except (ValueError, UnicodeError):
        return dict(result, decision="HOLD_ENCODING_OR_URL")
    heads = [h for h in soup.find_all("h1")
             if not hidden(h) and " ".join(h.get_text(" ", strip=True).split()) == " ".join(list_title.split())]
    if len(heads) != 1:
        return dict(result, decision="HOLD_TITLE_IDENTITY")
    result["listDetailIdentity"] = "REVIEW_EXACT_OFFICIAL_TITLE"
    labels = [h for h in soup.find_all(["h2", "h3", "h4"])
              if not hidden(h) and "".join(h.get_text(" ", strip=True).split()) == "場次"]
    if len(labels) != 1:
        return dict(result, decision="HOLD_SESSION_LABEL_NOT_UNIQUE")
    section = labels[0].find_next_sibling("ul")
    if section is None or hidden(section):
        return dict(result, decision="HOLD_NO_LOCAL_SESSION_LIST")
    rows = section.find_all("li", recursive=False)
    if not rows or len(rows) > MAX_ROWS:
        return dict(result, decision="HOLD_SESSION_COUNT_CAP")
    canceled = 0
    for row in rows:
        if hidden(row):
            return dict(result, decision="HOLD_HIDDEN_SESSION_ROW")
        text = " ".join(row.get_text(" ", strip=True).split())
        if not SESSION.fullmatch(text):
            return dict(result, decision="HOLD_AMBIGUOUS_SESSION_TEXT")
        if "已取消" in text:
            canceled += 1
    return dict(result, decision="REVIEW_SESSION_CANCEL_SPLIT_NOT_ACCEPTED",
                sessionCount=len(rows), canceledCount=canceled,
                activeCount=len(rows) - canceled)

# List-card date range and detail-page date range can have different roles.
# Refuse conflicts instead of overwriting one with the other or calling either a show date.
RANGE = re.compile(r"^(20\d{2}-\d{2}-\d{2})\s*[-~～]\s*(20\d{2}-\d{2}-\d{2})$")

def compare_date_ranges(list_range: str, detail_range: str) -> dict:
    result = dict(decision="HOLD_UNLABELED_DATE_RANGE", rangeRole="UNKNOWN",
                  acceptedFields=0, goldenAccepted=0, published=False,
                  releaseState=RELEASE)
    if not isinstance(list_range, str) or not isinstance(detail_range, str):
        return result
    a, b = RANGE.fullmatch(list_range.strip()), RANGE.fullmatch(detail_range.strip())
    if a is None or b is None:
        return result
    if a.group(1) > a.group(2) or b.group(1) > b.group(2):
        return dict(result, decision="HOLD_INVALID_RANGE_ORDER")
    if a.groups() != b.groups():
        return dict(result, decision="HOLD_LIST_DETAIL_DATE_RANGE_CONFLICT")
    return dict(result, decision="REVIEW_RANGE_PARITY_NOT_FIELD_ACCEPTANCE")

if __name__ == "__main__":
    raise SystemExit("HOLD_NO_DIRECT_EXECUTION: import and test only; no official GET")
