#!/usr/bin/env python3
"""P30-L9-BU: source-observed FamiTicket list/detail iframe identity boundary.

The index exposes an opaque /Home/Activity/Info path, but the public
detail reader renders only an iframe. Do not infer a same-ID event heading,
date role, sale role, price, or canonical ticket event identity.
"""
import hashlib
import re
from urllib.parse import urlsplit

SOURCE = "FamiTicket#07"
INDEX_URL = "https://www.famiticket.com.tw/Home"
HOLD = "HARD_HOLD_NO_PUBLICATION"
STAMP = re.compile(r"^20\d\d-\d\d-\d\d$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{24,512}$")

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def safe_detail(url):
    if not isinstance(url, str):
        return False
    try:
        p = urlsplit(url)
    except ValueError:
        return False
    prefix = "/Home/Activity/Info/"
    return (p.scheme == "https" and p.netloc == "www.famiticket.com.tw"
            and not p.username and not p.password and not p.query
            and not p.fragment and p.path.startswith(prefix)
            and bool(TOKEN.fullmatch(p.path[len(prefix):])))

def inspect(row, detail):
    out = {"gate": "P30-L9-BU", "canonicalPlatform": SOURCE,
           "officialGETinCI": 0, "sourceQualityStage": "LIST_TO_IFRAME_DETAIL",
           "candidateProvenance": [], "acceptedFields": 0,
           "goldenAccepted": 0, "published": False,
           "releaseState": HOLD, "ticketEventId": None}
    if not isinstance(row, dict) or not isinstance(detail, dict):
        return dict(out, decision="HOLD_UNSTRUCTURED_SOURCE_EVIDENCE")
    if (row.get("index_url") != INDEX_URL
            or not safe_detail(row.get("detail_url"))
            or detail.get("url") != row.get("detail_url")):
        return dict(out, decision="HOLD_SOURCE_URL_OR_OPAQUE_IDENTITY")
    title = row.get("title")
    date_label = row.get("list_date")
    category = row.get("category")
    stamp = row.get("observed_at")
    if (not isinstance(title, str) or not 8 <= len(title) <= 160
            or title != title.strip() or not isinstance(date_label, str)
            or not 5 <= len(date_label) <= 40
            or not isinstance(category, str)
            or not STAMP.fullmatch(stamp or "")):
        return dict(out, decision="HOLD_LIST_ROLE_OR_PROVENANCE")
    for role, value in (("LIST_TITLE_UNVERIFIED", title),
                        ("LIST_DATE_ROLE_UNKNOWN", date_label),
                        ("LIST_CATEGORY_UNVERIFIED", category)):
        out["candidateProvenance"].append({
            "source": SOURCE, "source_url": INDEX_URL, "observed_at": stamp,
            "role": role, "valueSHA256": digest(value),
            "decision": "REVIEW_NOT_ACCEPTED"})
    if category in ("交換票", "餐券", "景點門票", "住宿", "交通"):
        return dict(out, decision="HOLD_VOUCHER_OR_NON_EVENT_CATEGORY")
    if category not in ("演唱會", "音樂會", "展覽", "展覽 演唱會"):
        return dict(out, decision="HOLD_UNRECOGNIZED_CATEGORY")
    if detail.get("iframe_only") is not True or detail.get("heading") is not None:
        return dict(out, decision="HOLD_DETAIL_VIEW_NOT_INDEPENDENTLY_VERIFIED")
    out["detailHeadingVerified"] = False
    out["sameIdTitleVerified"] = False
    out["dateRoleVerified"] = False
    if category == "展覽 演唱會":
        return dict(out, decision="HOLD_MIXED_LIST_CATEGORY_AND_IFRAME_IDENTITY")
    return dict(out, decision="HOLD_IFRAME_ONLY_NO_SAME_ID_DETAIL_TITLE")

if __name__ == "__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
